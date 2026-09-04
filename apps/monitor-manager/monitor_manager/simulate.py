"""Pure transition function: apply one Op to a HardwareState.

The reconciler uses this to maintain a shadow state while emitting ops, so
later ops can reference objects created by earlier ops (e.g., desktops that
will exist on a monitor after BspcDesktopAdd runs). The executor mirrors
this logic against the real system — for any op O and state S,
`probe_after_running(O on real system from state S)` should equal
`simulate(S, O, ...)`.

Newly-created bspwm objects (monitors that appear on RandR events,
desktops that BspcDesktopAdd creates) get placeholder ids minted via the
caller-supplied `mint_id` callable. The executor binds those placeholders
to real hex ids at run time.
"""

from dataclasses import replace
from typing import Callable, List

from .ops import (
    BspcConfig,
    BspcDesktopAdd,
    BspcDesktopRemove,
    BspcDesktopRename,
    BspcMonitorRemove,
    BspcWindowMoveToDesktop,
    Op,
    PolybarKillAll,
    PolybarLaunch,
    WaitForBspwmMonitor,
    WallpaperRestore,
    XrandrApply,
    XrandrApplyLayout,
    XrandrOff,
)
from .state.hardware import (
    BspwmDesktop,
    BspwmMonitor,
    BspwmSettings,
    HardwareState,
    XrandrOutput,
)

MintIdFn = Callable[[str], str]


def simulate(state: HardwareState, op: Op, mint_id: MintIdFn) -> HardwareState:
    """Return the state that would result from running `op` against `state`.

    `mint_id(prefix)` produces a fresh placeholder id like "$D_5" for newly
    created bspwm objects. The reconciler shares one mint function across
    a planning pass so ids are unique within a Plan.
    """
    if isinstance(op, XrandrApply):
        return _simulate_xrandr_apply(state, op)
    if isinstance(op, XrandrOff):
        return _simulate_xrandr_off(state, op)
    if isinstance(op, XrandrApplyLayout):
        for a in op.applies:
            state = _simulate_xrandr_apply(state, a)
        for off in op.offs:
            state = _simulate_xrandr_off(state, off)
        return state  # framebuffer size itself is not modeled
    if isinstance(op, WaitForBspwmMonitor):
        return _simulate_wait_for_bspwm_monitor(state, op, mint_id)
    if isinstance(op, BspcDesktopAdd):
        return _simulate_desktop_add(state, op, mint_id)
    if isinstance(op, BspcDesktopRename):
        return _simulate_desktop_rename(state, op)
    if isinstance(op, BspcDesktopRemove):
        return _simulate_desktop_remove(state, op)
    if isinstance(op, BspcWindowMoveToDesktop):
        return _simulate_window_move(state, op)
    if isinstance(op, BspcMonitorRemove):
        return _simulate_monitor_remove(state, op)
    if isinstance(op, BspcConfig):
        return _simulate_config(state, op)
    if isinstance(op, PolybarKillAll):
        return replace(state, polybar_pids=())
    if isinstance(op, PolybarLaunch):
        return _simulate_polybar_launch(state, op)
    if isinstance(op, WallpaperRestore):
        return state  # wallpaper is not modeled
    raise ValueError(f"unknown op type: {type(op).__name__}")


def _simulate_xrandr_apply(state: HardwareState, op: XrandrApply) -> HardwareState:
    new_outputs: List[XrandrOutput] = []
    seen = False
    for o in state.outputs:
        if o.name == op.output:
            seen = True
            new_outputs.append(
                replace(
                    o,
                    connected=True,
                    active_mode=op.mode,
                    position=op.position,
                    rotation=op.rotation,
                    scale=op.scale,
                    primary=op.primary,
                )
            )
        elif op.primary and o.primary:
            new_outputs.append(replace(o, primary=False))
        else:
            new_outputs.append(o)
    if not seen:
        new_outputs.append(
            XrandrOutput(
                name=op.output,
                connected=True,
                active_mode=op.mode,
                position=op.position,
                rotation=op.rotation,
                scale=op.scale,
                primary=op.primary,
            )
        )
    return replace(state, outputs=tuple(new_outputs))


def _simulate_xrandr_off(state: HardwareState, op: XrandrOff) -> HardwareState:
    new_outputs = tuple(
        replace(o, active_mode=None, position=None, primary=False)
        if o.name == op.output
        else o
        for o in state.outputs
    )
    return replace(state, outputs=new_outputs)


def _simulate_wait_for_bspwm_monitor(
    state: HardwareState, op: WaitForBspwmMonitor, mint_id: MintIdFn
) -> HardwareState:
    if any(m.name == op.output for m in state.bspwm_monitors):
        return state
    # Predict a bare monitor with no desktops. Real bspwm may create one or
    # more default desktops on monitor-appear; the executor reconciles those
    # away so reality matches this prediction. Keeping the simulator's model
    # minimal means the planner only emits BspcDesktopAdd for what's wanted —
    # never a rename of an unpredictable default name.
    new_monitor = BspwmMonitor(id=mint_id("M"), name=op.output, desktops=())
    return replace(state, bspwm_monitors=state.bspwm_monitors + (new_monitor,))


def _simulate_desktop_add(
    state: HardwareState, op: BspcDesktopAdd, mint_id: MintIdFn
) -> HardwareState:
    new_desktop = BspwmDesktop(id=mint_id("D"), name=op.desktop_name, window_ids=())
    monitors = tuple(
        replace(m, desktops=m.desktops + (new_desktop,))
        if m.id == op.monitor_id
        else m
        for m in state.bspwm_monitors
    )
    return replace(state, bspwm_monitors=monitors)


def _simulate_desktop_rename(
    state: HardwareState, op: BspcDesktopRename
) -> HardwareState:
    monitors = tuple(_rename_in(m, op.desktop_id, op.new_name) for m in state.bspwm_monitors)
    return replace(state, bspwm_monitors=monitors)


def _rename_in(m: BspwmMonitor, desktop_id: str, new_name: str) -> BspwmMonitor:
    return replace(
        m,
        desktops=tuple(
            replace(d, name=new_name) if d.id == desktop_id else d for d in m.desktops
        ),
    )


def _simulate_desktop_remove(
    state: HardwareState, op: BspcDesktopRemove
) -> HardwareState:
    monitors = tuple(
        replace(m, desktops=tuple(d for d in m.desktops if d.id != op.desktop_id))
        for m in state.bspwm_monitors
    )
    return replace(state, bspwm_monitors=monitors)


def _simulate_window_move(
    state: HardwareState, op: BspcWindowMoveToDesktop
) -> HardwareState:
    new_monitors: List[BspwmMonitor] = []
    for m in state.bspwm_monitors:
        new_desktops: List[BspwmDesktop] = []
        for d in m.desktops:
            if op.window_id in d.window_ids:
                new_desktops.append(
                    replace(
                        d,
                        window_ids=tuple(w for w in d.window_ids if w != op.window_id),
                    )
                )
            elif d.id == op.target_desktop_id:
                new_desktops.append(
                    replace(d, window_ids=d.window_ids + (op.window_id,))
                )
            else:
                new_desktops.append(d)
        new_monitors.append(replace(m, desktops=tuple(new_desktops)))
    return replace(state, bspwm_monitors=tuple(new_monitors))


def _simulate_monitor_remove(
    state: HardwareState, op: BspcMonitorRemove
) -> HardwareState:
    monitors = tuple(m for m in state.bspwm_monitors if m.id != op.monitor_id)
    return replace(state, bspwm_monitors=monitors)


def _simulate_config(state: HardwareState, op: BspcConfig) -> HardwareState:
    s = state.bspwm_settings
    new_settings = _apply_setting(s, op.key, op.value)
    return replace(state, bspwm_settings=new_settings)


def _apply_setting(s: BspwmSettings, key: str, value: str) -> BspwmSettings:
    if key == "border_width":
        return replace(s, border_width=int(value))
    if key == "window_gap":
        return replace(s, window_gap=int(value))
    if key == "focused_border_color":
        return replace(s, focused_border_color=value)
    if key == "normal_border_color":
        return replace(s, normal_border_color=value)
    if key == "split_ratio":
        return replace(s, split_ratio=float(value))
    if key == "borderless_monocle":
        return replace(s, borderless_monocle=value.strip().lower() == "true")
    if key == "gapless_monocle":
        return replace(s, gapless_monocle=value.strip().lower() == "true")
    return s


def _simulate_polybar_launch(state: HardwareState, op: PolybarLaunch) -> HardwareState:
    # Synthetic PID. Stable per launch index so tests can assert.
    new_pid = 90000 + len(state.polybar_pids)
    return replace(state, polybar_pids=state.polybar_pids + (new_pid,))


def default_mint() -> MintIdFn:
    """A counter-backed `mint_id` for callers that want one off the shelf."""
    counter: List[int] = [0]

    def _mint(prefix: str) -> str:
        counter[0] += 1
        return f"${prefix}_{counter[0]}"

    return _mint


__all__ = ["simulate", "default_mint", "MintIdFn"]
