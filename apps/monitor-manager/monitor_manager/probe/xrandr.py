"""Probe xrandr state into XrandrOutput tuple."""

import re
import subprocess
from typing import List, Optional, Protocol, Tuple

from ..edid import hash_edid
from ..state.hardware import XrandrOutput


class XrandrRunner(Protocol):
    """Source of `xrandr --props` output."""

    def get_props(self) -> str:
        ...


class SubprocessXrandrRunner:
    def get_props(self) -> str:
        result = subprocess.run(
            ["xrandr", "--props"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout


# Output line shape (xrandr writes them in a fixed order):
#   <name> connected|disconnected [primary] [<W>x<H>+<X>+<Y>] [rotation] (rotations) [size]
_OUTPUT_LINE_RE = re.compile(
    r"^(?P<name>\S+)\s+(?P<status>connected|disconnected)"
    r"(?:\s+(?P<primary>primary))?"
    r"(?:\s+(?P<geom>\d+x\d+\+\d+\+\d+))?"
    r"(?:\s+(?P<rotation>left|right|inverted))?"
)
_EDID_HEX_LINE_RE = re.compile(r"^\t\t[0-9a-f]{32}")


class XrandrProbe:
    """Reads `xrandr --props` and parses it into XrandrOutputs."""

    def __init__(self, runner: Optional[XrandrRunner] = None):
        self._runner = runner or SubprocessXrandrRunner()

    def read(self) -> Tuple[XrandrOutput, ...]:
        return self.parse(self._runner.get_props())

    @staticmethod
    def parse(xrandr_output: str) -> Tuple[XrandrOutput, ...]:
        outputs: List[XrandrOutput] = []
        lines = xrandr_output.split("\n")
        for i, line in enumerate(lines):
            m = _OUTPUT_LINE_RE.match(line)
            if not m:
                continue

            geom = m.group("geom")
            active_mode: Optional[str] = None
            position: Optional[Tuple[int, int]] = None
            if geom:
                # geom like "1920x1200+0+0"
                mode_str, _, rest = geom.partition("+")
                px_str, _, py_str = rest.partition("+")
                active_mode = mode_str
                try:
                    position = (int(px_str), int(py_str))
                except ValueError:
                    position = None

            outputs.append(
                XrandrOutput(
                    name=m.group("name"),
                    connected=m.group("status") == "connected",
                    edid=_extract_edid(lines, i + 1),
                    active_mode=active_mode,
                    position=position,
                    rotation=m.group("rotation") or "normal",
                    primary=m.group("primary") is not None,
                )
            )
        return tuple(outputs)


def _extract_edid(lines: List[str], start: int) -> Optional[str]:
    """Find the EDID block in the indented section after an output line."""
    j = start
    while j < len(lines) and lines[j].startswith("\t"):
        if lines[j].strip() == "EDID:":
            edid_chunks: List[str] = []
            k = j + 1
            while k < len(lines) and _EDID_HEX_LINE_RE.match(lines[k]):
                edid_chunks.append(lines[k].strip())
                k += 1
            return hash_edid("".join(edid_chunks)) if edid_chunks else None
        j += 1
    return None
