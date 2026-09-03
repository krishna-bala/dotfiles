"""Hardware state — what xrandr and bspwm currently report.

Probe layer reads into HardwareState. Reconciler diffs it against DesiredState.
Executor mutates the system. Nothing here calls subprocess.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True)
class XrandrOutput:
    """One row from `xrandr --props`."""

    name: str
    connected: bool
    edid: Optional[str] = None  # Truncated hash of the full EDID, not raw bytes
    active_mode: Optional[str] = None
    position: Optional[Tuple[int, int]] = None
    rotation: str = "normal"
    scale: Tuple[float, float] = (1.0, 1.0)
    primary: bool = False


@dataclass(frozen=True)
class BspwmDesktop:
    """A bspwm desktop. `id` is the hex id from `bspc query -D`; names can collide."""

    id: str
    name: str
    window_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class BspwmMonitor:
    """A bspwm monitor. Hex id sidesteps the dot-as-modifier hazard for `DP-0.1`."""

    id: str
    name: str
    desktops: Tuple[BspwmDesktop, ...] = ()


@dataclass(frozen=True)
class BspwmSettings:
    """The subset of `bspc config` values profiles set."""

    border_width: int = 7
    window_gap: int = 15
    focused_border_color: str = "#629dc8"
    normal_border_color: str = "#1f2339"
    split_ratio: float = 0.5
    borderless_monocle: bool = False
    gapless_monocle: bool = False


@dataclass(frozen=True)
class HardwareState:
    """Snapshot of the world at one moment."""

    outputs: Tuple[XrandrOutput, ...] = ()
    bspwm_monitors: Tuple[BspwmMonitor, ...] = ()
    bspwm_settings: BspwmSettings = field(default_factory=BspwmSettings)
    polybar_pids: Tuple[int, ...] = ()
