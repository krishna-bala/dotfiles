"""Reconciler — pure function that diffs current vs desired into a Plan.

The planner emits ops in execution-relevant order, maintaining a shadow state
via `simulate` so later ops can reference objects created by earlier ops. The
output Plan is what the executor runs and the renderer displays — same value,
no parallel paths.

Order of phases (each emits ops):
    1. xrandr: enable/update desired outputs, disable any active output not in
       the profile.
    2. wait: emit a wait op for every desired-enabled output not yet in bspwm,
       so the simulator records it before later phases reference it.
    3. surviving desktops: rename or add desktops on monitors the profile
       keeps, so windows have the right targets to land on.
    4. window migration: move windows off stale (profile-removed) monitors
       using the merge policy.
    5. cleanup: remove now-empty stale desktops, then stale monitors.
    6. settings: emit BspcConfig only for keys that differ from current.
    7. polybar: kill all + launch one per desired bar.
"""

from typing import List, Optional, Tuple

from .ops import (
    BspcConfig,
    BspcDesktopAdd,
    BspcDesktopRemove,
    BspcDesktopRename,
    BspcMonitorRemove,
    BspcWindowMoveToDesktop,
    Op,
    Plan,
    PolybarKillAll,
    PolybarLaunch,
    WaitForBspwmMonitor,
    WallpaperRestore,
    XrandrApply,
    XrandrApplyLayout,
    XrandrOff,
)
from .plan import MergePolicy, PreserveByName
from .simulate import simulate
from .state.desired import DesiredState
from .state.hardware import BspwmMonitor, HardwareState


def _output_extent(
    mode: Optional[str],
    position: Optional[Tuple[int, int]],
    rotation: str,
    scale: Tuple[float, float],
) -> Tuple[int, int]:
    """Bottom-right corner of an output after scale and rotation."""
    if not mode or position is None:
        return (0, 0)
    try:
        w_str, h_str = mode.split("x")
        w, h = int(w_str), int(h_str)
    except ValueError:
        return (0, 0)
    w = int(round(w * scale[0]))
    h = int(round(h * scale[1]))
    if rotation in ("left", "right"):
        w, h = h, w
    return (position[0] + w, position[1] + h)


def _effective_mode(
    mode: Optional[str], rotation: str, scale: Tuple[float, float]
) -> Optional[str]:
    """Desired geometry in the probe's space.

    The probe reads xrandr's summary line, which reports the post-transform
    geometry (mode scaled, then rotated: a 4K output at scale 0.6 rotated
    left reads back as 1296x2304) and exposes no scale at all. Comparing the
    profile's raw (mode, scale, rotation) against that never converges, so
    the desired side is projected into the same space first."""
    ex = _output_extent(mode, (0, 0), rotation, scale)
    return None if ex == (0, 0) else f"{ex[0]}x{ex[1]}"


class _PlanBuilder:
    """Accumulates ops while keeping a shadow HardwareState in sync."""

    def __init__(self, initial: HardwareState):
        self.state = initial
        self.ops: List[Op] = []
        self._counter = 0

    def _mint(self, prefix: str) -> str:
        self._counter += 1
        return f"${prefix}_{self._counter}"

    def emit(self, op: Op) -> None:
        self.ops.append(op)
        self.state = simulate(self.state, op, self._mint)


class Reconciler:
    """Builds a Plan from a (HardwareState, DesiredState) pair."""

    def plan(
        self,
        current: HardwareState,
        desired: DesiredState,
        merge_policy: Optional[MergePolicy] = None,
    ) -> Plan:
        merge_policy = merge_policy or PreserveByName()
        b = _PlanBuilder(current)
        self._reconcile_xrandr(b, desired)
        self._wait_for_new_bspwm_monitors(b, desired)
        self._reconcile_surviving_desktop_lists(b, desired)
        self._migrate_windows_off_stale(b, desired, merge_policy)
        self._cleanup_stale(b, desired)
        self._reconcile_settings(b, desired)
        self._reconcile_polybar(b, desired)
        # Last and failure-tolerant by position: a geometry change leaves the
        # root pixmap stale, so repaint the wallpaper for the new layout.
        if any(isinstance(op, XrandrApplyLayout) for op in b.ops):
            b.emit(WallpaperRestore())
        return Plan(profile_name=desired.profile_name, ops=tuple(b.ops))

    def _reconcile_xrandr(self, b: _PlanBuilder, desired: DesiredState) -> None:
        """Collect an apply for every desired-enabled output that differs from
        current and an off for every currently-active output the profile does
        not enable, then emit them as ONE XrandrApplyLayout op (see the op's
        docstring for why a single invocation is required)."""
        current_by_name = {o.name: o for o in b.state.outputs}
        desired_enabled_names = {d.name for d in desired.outputs if d.enabled}

        applies: List[XrandrApply] = []
        for d in desired.outputs:
            if not d.enabled:
                continue
            cur = current_by_name.get(d.name)
            if (
                cur
                and cur.active_mode is not None
                and cur.active_mode == _effective_mode(d.mode, d.rotation, d.scale)
                and cur.position == d.position
                and cur.rotation == d.rotation
                and cur.primary == d.primary
            ):
                continue
            applies.append(
                XrandrApply(
                    output=d.name,
                    mode=d.mode or "",
                    position=d.position or (0, 0),
                    rotation=d.rotation,
                    scale=d.scale,
                    primary=d.primary,
                )
            )

        offs: List[XrandrOff] = []
        for o in b.state.outputs:
            if o.active_mode is None:
                continue
            if o.name in desired_enabled_names:
                continue
            offs.append(XrandrOff(output=o.name))

        if not applies and not offs:
            return

        # --fb of the final layout; xrandr sequences the resize correctly
        # within the single invocation.
        final_fb = (0, 0)
        for d in desired.outputs:
            if not d.enabled:
                continue
            ex = _output_extent(d.mode, d.position, d.rotation, d.scale)
            final_fb = (max(final_fb[0], ex[0]), max(final_fb[1], ex[1]))

        b.emit(
            XrandrApplyLayout(
                applies=tuple(applies),
                offs=tuple(offs),
                fb=final_fb if final_fb != (0, 0) else None,
            )
        )

    def _wait_for_new_bspwm_monitors(
        self, b: _PlanBuilder, desired: DesiredState
    ) -> None:
        bspwm_names = {m.name for m in b.state.bspwm_monitors}
        for d in desired.outputs:
            if not d.enabled:
                continue
            if d.name not in bspwm_names:
                b.emit(WaitForBspwmMonitor(output=d.name))

    def _reconcile_surviving_desktop_lists(
        self, b: _PlanBuilder, desired: DesiredState
    ) -> None:
        """For each monitor the profile keeps, rename its first N existing
        desktops to the desired names by position, then add any that are
        missing. Surplus existing desktops past the desired length are left
        for the migration phase to drain and the cleanup phase to remove."""
        workspaces_by_output = {w.output: w.desktop_names for w in desired.workspaces}
        for monitor in b.state.bspwm_monitors:
            desired_names = workspaces_by_output.get(monitor.name)
            if desired_names is None:
                continue  # stale; cleanup phase handles it

            existing = list(monitor.desktops)
            n_min = min(len(existing), len(desired_names))
            for i in range(n_min):
                if existing[i].name != desired_names[i]:
                    b.emit(
                        BspcDesktopRename(
                            desktop_id=existing[i].id, new_name=desired_names[i]
                        )
                    )
            for i in range(len(existing), len(desired_names)):
                b.emit(
                    BspcDesktopAdd(monitor_id=monitor.id, desktop_name=desired_names[i])
                )

    def _migrate_windows_off_stale(
        self,
        b: _PlanBuilder,
        desired: DesiredState,
        merge_policy: MergePolicy,
    ) -> None:
        """Move every window on a stale monitor to a desktop on a surviving
        monitor, picking the target via merge_policy."""
        workspaces_by_output = {w.output: w.desktop_names for w in desired.workspaces}
        target_monitor = self._pick_target_monitor(b.state, workspaces_by_output)
        if target_monitor is None:
            return  # no surviving monitor to migrate to (caller error)

        target_names = tuple(d.name for d in target_monitor.desktops)
        if not target_names:
            return  # nothing to land on

        target_id_by_name = {d.name: d.id for d in target_monitor.desktops}

        stale_monitors = [
            m for m in b.state.bspwm_monitors if m.name not in workspaces_by_output
        ]
        for sm in stale_monitors:
            # Snapshot windows before mutating; the builder's state will shift
            # under us as we emit.
            for sd in sm.desktops:
                for window_id in sd.window_ids:
                    target_name = merge_policy.assign(
                        window_id=window_id,
                        source_desktop_name=sd.name,
                        target_desktop_names=target_names,
                    )
                    target_id = target_id_by_name[target_name]
                    b.emit(
                        BspcWindowMoveToDesktop(
                            window_id=window_id, target_desktop_id=target_id
                        )
                    )

    def _pick_target_monitor(
        self, state: HardwareState, workspaces_by_output: dict
    ) -> Optional[BspwmMonitor]:
        """First monitor in bspwm order that the profile keeps and that has at
        least one desktop. None if no monitor qualifies."""
        for m in state.bspwm_monitors:
            if m.name in workspaces_by_output and len(m.desktops) > 0:
                return m
        return None

    def _cleanup_stale(self, b: _PlanBuilder, desired: DesiredState) -> None:
        """Remove now-empty stale desktops, then the stale monitors. Reads the
        post-migration shadow state, not the original."""
        workspaces_by_output = {w.output: w.desktop_names for w in desired.workspaces}
        stale_monitors = [
            m for m in b.state.bspwm_monitors if m.name not in workspaces_by_output
        ]
        for sm in stale_monitors:
            current = next(
                (m for m in b.state.bspwm_monitors if m.id == sm.id), None
            )
            if current is None:
                continue
            # Migration may not have drained every desktop — skip non-empty
            # ones; bspwm would refuse the remove anyway. Surface as a
            # non-empty stale desktop so the caller notices.
            removable = [d for d in current.desktops if not d.window_ids]
            # bspwm also refuses to remove a monitor's LAST desktop, but
            # `monitor -r` takes the monitor down together with a remaining
            # empty desktop — so when the monitor would be left bare, keep
            # one desktop for the monitor remove to absorb.
            if removable and len(removable) == len(current.desktops):
                removable = removable[:-1]
            for d in removable:
                b.emit(BspcDesktopRemove(desktop_id=d.id))
            b.emit(BspcMonitorRemove(monitor_id=sm.id))

    def _reconcile_settings(self, b: _PlanBuilder, desired: DesiredState) -> None:
        """Emit BspcConfig only for keys that differ from current."""
        cur = b.state.bspwm_settings
        des = desired.bspwm_settings
        if cur.border_width != des.border_width:
            b.emit(BspcConfig(key="border_width", value=str(des.border_width)))
        if cur.window_gap != des.window_gap:
            b.emit(BspcConfig(key="window_gap", value=str(des.window_gap)))
        if cur.focused_border_color != des.focused_border_color:
            b.emit(
                BspcConfig(
                    key="focused_border_color", value=des.focused_border_color
                )
            )
        if cur.normal_border_color != des.normal_border_color:
            b.emit(
                BspcConfig(key="normal_border_color", value=des.normal_border_color)
            )
        if cur.split_ratio != des.split_ratio:
            b.emit(BspcConfig(key="split_ratio", value=str(des.split_ratio)))
        if cur.borderless_monocle != des.borderless_monocle:
            b.emit(
                BspcConfig(
                    key="borderless_monocle",
                    value="true" if des.borderless_monocle else "false",
                )
            )
        if cur.gapless_monocle != des.gapless_monocle:
            b.emit(
                BspcConfig(
                    key="gapless_monocle",
                    value="true" if des.gapless_monocle else "false",
                )
            )

    def _reconcile_polybar(self, b: _PlanBuilder, desired: DesiredState) -> None:
        """Always restart polybar on profile change. Matches existing behaviour
        and avoids stale per-bar state when monitor topology shifts. Env vars
        match the polybar config's expectations: MONITOR + FONT_0/FONT_1 nerd-
        font strings + MODULES_LEFT/CENTER/RIGHT."""
        if b.state.polybar_pids:
            b.emit(PolybarKillAll())
        for bar in desired.bars:
            env: Tuple[Tuple[str, str], ...] = (
                ("MONITOR", bar.output),
                (
                    "FONT_0",
                    f"JetBrainsMono Nerd Font:pixelsize={bar.font_size};3",
                ),
                (
                    "FONT_1",
                    f"JetBrainsMono Nerd Font:pixelsize={bar.font_size + 2};3",
                ),
                ("MODULES_LEFT", bar.modules_left),
                ("MODULES_CENTER", bar.modules_center),
                ("MODULES_RIGHT", bar.modules_right),
            )
            b.emit(
                PolybarLaunch(output=bar.output, bar_definition="main", env=env)
            )


__all__ = ["Reconciler"]
