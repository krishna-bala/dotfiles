"""Operations the executor can perform on the system.

Each op is a frozen dataclass. Bspwm objects are referenced by id (hex strings
from `bspc query -*`), not name — names collide and `bspc` interprets dots as
selector modifiers, so name-based lookups are unsafe for outputs like `DP-0.1`.
Names live on probe inputs and renderer outputs only.

A `Plan` is an ordered tuple of ops. The reconciler builds it; the executor
runs it; the renderer pretty-prints it. The same Plan is the contract between
all three so preview and execution can never drift.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Union


@dataclass(frozen=True)
class XrandrApply:
    output: str
    mode: str
    position: Tuple[int, int]
    rotation: str
    scale: Tuple[float, float]
    primary: bool


@dataclass(frozen=True)
class XrandrOff:
    output: str


@dataclass(frozen=True)
class XrandrApplyLayout:
    """All xrandr changes for a plan, executed as ONE xrandr invocation.

    Sequential per-output calls cannot work here: the implicit screen
    resize fails with RRSetScreenSize BadMatch once any CRTC has a scale
    transform active (modesetting driver), and an explicit --fb on a later
    call hits the same wall. A single invocation lets xrandr sequence the
    server requests itself (disable, resize, then configure), which is the
    only ordering the driver accepts. `fb` is the framebuffer size of the
    final layout, passed as --fb.
    """

    applies: Tuple[XrandrApply, ...] = ()
    offs: Tuple[XrandrOff, ...] = ()
    fb: Optional[Tuple[int, int]] = None


@dataclass(frozen=True)
class WaitForBspwmMonitor:
    """Block until bspwm reports `output` as a monitor (or until timeout)."""

    output: str
    timeout_seconds: float = 7.5


@dataclass(frozen=True)
class BspcDesktopAdd:
    monitor_id: str
    desktop_name: str


@dataclass(frozen=True)
class BspcDesktopRename:
    desktop_id: str
    new_name: str


@dataclass(frozen=True)
class BspcDesktopRemove:
    """The reconciler only emits this for desktops it has modeled as empty."""

    desktop_id: str


@dataclass(frozen=True)
class BspcWindowMoveToDesktop:
    window_id: str
    target_desktop_id: str


@dataclass(frozen=True)
class BspcMonitorRemove:
    monitor_id: str


@dataclass(frozen=True)
class BspcConfig:
    key: str
    value: str


@dataclass(frozen=True)
class PolybarKillAll:
    pass


@dataclass(frozen=True)
class WallpaperRestore:
    """Repaint the wallpaper (nitrogen --restore) after geometry changes.

    The root pixmap is not regenerated when the screen is resized, so a
    layout change leaves smeared/stale wallpaper on resized regions."""

    pass


@dataclass(frozen=True)
class PolybarLaunch:
    output: str
    bar_definition: str
    env: Tuple[Tuple[str, str], ...] = ()


Op = Union[
    XrandrApply,
    XrandrOff,
    XrandrApplyLayout,
    WaitForBspwmMonitor,
    BspcDesktopAdd,
    BspcDesktopRename,
    BspcDesktopRemove,
    BspcWindowMoveToDesktop,
    BspcMonitorRemove,
    BspcConfig,
    PolybarKillAll,
    PolybarLaunch,
    WallpaperRestore,
]


@dataclass(frozen=True)
class Plan:
    profile_name: str
    ops: Tuple[Op, ...] = ()

    def is_noop(self) -> bool:
        return len(self.ops) == 0
