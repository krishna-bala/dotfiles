"""Desired state — what a profile asks for, with aliases resolved.

`compile_desired(profile, alias_to_output)` is a pure function: it does no
hardware probing. The caller (e.g. MonitorManagerCoordinator) supplies the
alias→output mapping that EDID matching produced.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ..profile import Profile
from .hardware import BspwmSettings


@dataclass(frozen=True)
class DesiredOutput:
    """xrandr config for one output, with the alias resolved to a real name."""

    name: str
    enabled: bool
    mode: Optional[str] = None
    position: Optional[Tuple[int, int]] = None
    rotation: str = "normal"
    scale: Tuple[float, float] = (1.0, 1.0)
    primary: bool = False


@dataclass(frozen=True)
class DesiredMonitorWorkspaces:
    """Desktops on one monitor, in order."""

    output: str
    desktop_names: Tuple[str, ...]


@dataclass(frozen=True)
class DesiredBar:
    """One polybar instance."""

    output: str
    orientation: str
    font_size: int
    modules_left: str = ""
    modules_center: str = ""
    modules_right: str = ""


@dataclass(frozen=True)
class DesiredState:
    """The system state a profile asks for."""

    profile_name: str
    outputs: Tuple[DesiredOutput, ...]
    monitor_order: Tuple[str, ...]
    workspaces: Tuple[DesiredMonitorWorkspaces, ...]
    bspwm_settings: BspwmSettings
    bars: Tuple[DesiredBar, ...]


def compile_desired(profile: Profile, alias_to_output: Dict[str, str]) -> DesiredState:
    """Resolve a profile's aliases against the supplied mapping.

    Aliases not present in `alias_to_output` are dropped silently — the same
    behaviour the existing coordinator has when an optional output isn't there.
    """
    outputs = tuple(
        _compile_output(alias_to_output[alias], disp)
        for alias, disp in profile.displays.items()
        if alias in alias_to_output
    )

    monitor_order = tuple(
        alias_to_output[a]
        for a in profile.window_manager.monitor_order
        if a in alias_to_output
    )

    workspaces = tuple(
        DesiredMonitorWorkspaces(
            output=alias_to_output[alias],
            desktop_names=tuple(str(n) for n in nums),
        )
        for alias, nums in profile.window_manager.workspaces.items()
        if alias in alias_to_output
    )

    bars = tuple(
        DesiredBar(
            output=alias_to_output[bar.monitor],
            orientation=bar.orientation,
            font_size=bar.font_size if bar.font_size is not None else 16,
            modules_left=(bar.modules or {}).get("left", ""),
            modules_center=(bar.modules or {}).get("center", ""),
            modules_right=(bar.modules or {}).get("right", ""),
        )
        for bar in profile.ui.bars
        if bar.monitor in alias_to_output
    )

    return DesiredState(
        profile_name=profile.name,
        outputs=outputs,
        monitor_order=monitor_order,
        workspaces=workspaces,
        bspwm_settings=_compile_settings(profile.window_manager.settings),
        bars=bars,
    )


def _compile_output(actual_name: str, disp) -> DesiredOutput:
    return DesiredOutput(
        name=actual_name,
        enabled=disp.enabled,
        mode=disp.resolution,
        position=_parse_position(disp.position),
        rotation=disp.rotation,
        scale=_parse_scale(disp.scale),
        primary=disp.primary,
    )


def _parse_position(text: Optional[str]) -> Optional[Tuple[int, int]]:
    if not text:
        return None
    try:
        x, y = text.split("x")
        return (int(x), int(y))
    except (ValueError, AttributeError):
        return None


def _parse_scale(text: Optional[str]) -> Tuple[float, float]:
    if not text:
        return (1.0, 1.0)
    try:
        x, y = text.split("x")
        return (float(x), float(y))
    except (ValueError, AttributeError):
        return (1.0, 1.0)


def _compile_settings(profile_settings: Optional[Dict[str, Any]]) -> BspwmSettings:
    """Merge profile overrides over the BspwmSettings defaults."""
    if not profile_settings:
        return BspwmSettings()
    defaults = BspwmSettings()
    return BspwmSettings(
        border_width=profile_settings.get("border_width", defaults.border_width),
        window_gap=profile_settings.get("window_gap", defaults.window_gap),
        focused_border_color=profile_settings.get(
            "focused_border_color", defaults.focused_border_color
        ),
        normal_border_color=profile_settings.get(
            "normal_border_color", defaults.normal_border_color
        ),
        split_ratio=profile_settings.get("split_ratio", defaults.split_ratio),
        borderless_monocle=profile_settings.get(
            "borderless_monocle", defaults.borderless_monocle
        ),
        gapless_monocle=profile_settings.get("gapless_monocle", defaults.gapless_monocle),
    )
