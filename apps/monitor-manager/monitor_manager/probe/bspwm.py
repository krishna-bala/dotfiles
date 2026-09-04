"""Probe bspwm state via `bspc wm -d` (one JSON dump) and `bspc config`."""

import json
import subprocess
from typing import List, Optional, Protocol, Tuple

from ..state.hardware import BspwmDesktop, BspwmMonitor, BspwmSettings


class BspcRunner(Protocol):
    """Source of bspc command output."""

    def dump_state(self) -> str:
        ...

    def get_config(self, key: str) -> str:
        ...


class SubprocessBspcRunner:
    def dump_state(self) -> str:
        result = subprocess.run(
            ["bspc", "wm", "-d"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def get_config(self, key: str) -> str:
        result = subprocess.run(
            ["bspc", "config", key],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()


def _id_to_hex(int_id: int) -> str:
    """Format bspwm integer ids as `0xNNNNNNNN` to match bspc's hex convention."""
    return f"0x{int_id:08X}"


def _walk_window_ids(node: Optional[dict]) -> List[str]:
    """Depth-first walk of a node tree, collecting ids of leaf nodes with a client."""
    if node is None:
        return []
    out: List[str] = []
    if node.get("client") is not None:
        out.append(_id_to_hex(node["id"]))
    out.extend(_walk_window_ids(node.get("firstChild")))
    out.extend(_walk_window_ids(node.get("secondChild")))
    return out


class BspwmProbe:
    """Reads bspwm state — topology via `bspc wm -d`, settings via `bspc config`."""

    def __init__(self, runner: Optional[BspcRunner] = None):
        self._runner = runner or SubprocessBspcRunner()

    def read_monitors(self) -> Tuple[BspwmMonitor, ...]:
        return self.parse_dump(self._runner.dump_state())

    def read_settings(self) -> BspwmSettings:
        defaults = BspwmSettings()

        def _safe(key: str, parse, default):
            try:
                return parse(self._runner.get_config(key))
            except Exception:
                return default

        return BspwmSettings(
            border_width=_safe("border_width", int, defaults.border_width),
            window_gap=_safe("window_gap", int, defaults.window_gap),
            focused_border_color=_safe(
                "focused_border_color", str, defaults.focused_border_color
            ),
            normal_border_color=_safe(
                "normal_border_color", str, defaults.normal_border_color
            ),
            split_ratio=_safe("split_ratio", float, defaults.split_ratio),
            borderless_monocle=_safe(
                "borderless_monocle",
                lambda v: v.strip().lower() == "true",
                defaults.borderless_monocle,
            ),
            gapless_monocle=_safe(
                "gapless_monocle",
                lambda v: v.strip().lower() == "true",
                defaults.gapless_monocle,
            ),
        )

    @staticmethod
    def parse_dump(dump_json: str) -> Tuple[BspwmMonitor, ...]:
        data = json.loads(dump_json)
        return tuple(_parse_monitor(m) for m in data.get("monitors", []))


def _parse_monitor(m: dict) -> BspwmMonitor:
    return BspwmMonitor(
        id=_id_to_hex(m["id"]),
        name=m["name"],
        desktops=tuple(_parse_desktop(d) for d in m.get("desktops", [])),
    )


def _parse_desktop(d: dict) -> BspwmDesktop:
    return BspwmDesktop(
        id=_id_to_hex(d["id"]),
        name=d["name"],
        window_ids=tuple(_walk_window_ids(d.get("root"))),
    )
