#!/usr/bin/env python3
"""Strip raw EDID bytes out of `xrandr --props` output.

Each EDID block is replaced in place with a fixed dummy block (same shape,
no real bytes), so a captured fixture stays parseable by the probe/display
code without ever carrying a per-unit hardware serial to disk. The real
match key for each output -- the value to paste into a profile's
`detection:` block -- is printed to stderr instead.

Usage: xrandr --props | redact-edid.py > sanitized.txt
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.edid import hash_edid  # noqa: E402

_OUTPUT_LINE_RE = re.compile(r"^(?P<name>\S+)\s+(connected|disconnected)")
_EDID_HEX_LINE_RE = re.compile(r"^\t\t[0-9a-f]{32}")

# Fixed, non-identifying stand-in for a real EDID block. Same shape (8 lines
# of 32 hex chars) as a real 128-byte EDID so parsing still exercises the
# real code path; the content carries no hardware fingerprint.
_DUMMY_EDID_LINES = ["\t\t" + ("00" * 16) for _ in range(8)]


def redact(xrandr_props: str) -> str:
    lines = xrandr_props.split("\n")
    out: list[str] = []
    current_output = None
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _OUTPUT_LINE_RE.match(line)
        if m:
            current_output = m.group("name")
        if line.strip() == "EDID:":
            out.append(line)
            j = i + 1
            chunks = []
            while j < len(lines) and _EDID_HEX_LINE_RE.match(lines[j]):
                chunks.append(lines[j].strip())
                j += 1
            if chunks:
                print(f"{current_output}: {hash_edid(''.join(chunks))}", file=sys.stderr)
                out.extend(_DUMMY_EDID_LINES)
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


if __name__ == "__main__":
    sys.stdout.write(redact(sys.stdin.read()))
