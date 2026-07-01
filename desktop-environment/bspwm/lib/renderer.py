"""Plain-text rendering of Plans.

The same Plan that the executor runs is what the renderer prints, so preview
and execution can never disagree about what's about to happen.
"""

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


class Renderer:
    """Renders a Plan as human-readable text."""

    def render(self, plan: Plan) -> str:
        if plan.is_noop():
            return (
                f"Profile: {plan.profile_name}\n"
                "  (no changes — already in desired state)\n"
            )

        lines = [
            f"Profile: {plan.profile_name}",
            f"Ops: {len(plan.ops)}",
            "",
        ]
        for i, op in enumerate(plan.ops, 1):
            lines.append(f"  [{i:>3}] {self.render_op(op)}")
        return "\n".join(lines) + "\n"

    def render_op(self, op: Op) -> str:
        if isinstance(op, XrandrApply):
            primary = " primary" if op.primary else ""
            scale = (
                "" if op.scale == (1.0, 1.0) else f" scale={op.scale[0]}x{op.scale[1]}"
            )
            rotation = "" if op.rotation == "normal" else f" rotate={op.rotation}"
            return (
                f"xrandr apply  {op.output} {op.mode} @ "
                f"{op.position[0]},{op.position[1]}{rotation}{scale}{primary}"
            )
        if isinstance(op, XrandrOff):
            return f"xrandr off    {op.output}"
        if isinstance(op, XrandrApplyLayout):
            fb = "" if op.fb is None else f" fb={op.fb[0]}x{op.fb[1]}"
            parts = [f"xrandr layout{fb} (one invocation)"]
            parts.extend(f"  + {self.render_op(a)}" for a in op.applies)
            parts.extend(f"  + {self.render_op(o)}" for o in op.offs)
            return "\n        ".join(parts)
        if isinstance(op, WaitForBspwmMonitor):
            return (
                f"wait          {op.output} appears in bspwm "
                f"(<={op.timeout_seconds}s)"
            )
        if isinstance(op, BspcDesktopAdd):
            return f"desktop add   {op.desktop_name!r} on monitor {op.monitor_id}"
        if isinstance(op, BspcDesktopRename):
            return f"desktop rename {op.desktop_id} -> {op.new_name!r}"
        if isinstance(op, BspcDesktopRemove):
            return f"desktop remove {op.desktop_id} (must be empty)"
        if isinstance(op, BspcWindowMoveToDesktop):
            return f"window move   {op.window_id} -> desktop {op.target_desktop_id}"
        if isinstance(op, BspcMonitorRemove):
            return f"monitor remove {op.monitor_id}"
        if isinstance(op, BspcConfig):
            return f"config        {op.key} = {op.value}"
        if isinstance(op, PolybarKillAll):
            return "polybar kill  (all)"
        if isinstance(op, WallpaperRestore):
            return "wallpaper     nitrogen --restore"
        if isinstance(op, PolybarLaunch):
            env = " " + " ".join(f"{k}={v}" for k, v in op.env) if op.env else ""
            return f"polybar launch {op.output} bar={op.bar_definition}{env}"
        return f"<unknown op: {op!r}>"
