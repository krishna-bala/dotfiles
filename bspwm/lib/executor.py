"""Executor — runs a Plan against the real system.

The reconciler emits ops referencing simulator-issued placeholder ids
($M_n, $D_n) for objects that don't exist yet at planning time. The executor
mints symbols in lockstep with the simulator (same prefix, same counter
order) so it knows which symbol each id-creating op produced. After running
each id-creating op, the executor binds its symbol to the real hex id that
bspwm reports.

Subsequent ops with symbolic refs in their fields are resolved against the
binding table just before dispatch.

If an op fails, execute() returns immediately with the failed op and the
remaining (skipped) ops. No rollback is attempted at this layer — that's
SafetyService's job once snapshot/rollback are themselves Plans.
"""

import os
import subprocess
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple

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


@dataclass(frozen=True)
class ExecutionResult:
    """Outcome of running a Plan."""

    completed: Tuple[Op, ...] = ()
    failed: Optional[Tuple[Op, Exception]] = None
    skipped: Tuple[Op, ...] = ()

    def succeeded(self) -> bool:
        return self.failed is None


class XrandrCommandRunner(Protocol):
    def apply_layout(self, op: XrandrApplyLayout) -> None:
        ...


class WallpaperRunner(Protocol):
    def restore(self) -> None:
        ...


class BspcCommandRunner(Protocol):
    def wait_for_monitor(self, output_name: str, timeout: float) -> str:
        """Block until bspwm registers a monitor named `output_name`. Return its hex id."""
        ...

    def query_desktop_ids(
        self, monitor_id: str
    ) -> Tuple[Tuple[str, str], ...]:
        """Return (desktop_id, desktop_name) pairs in monitor order."""
        ...

    def add_desktop(self, monitor_id: str, name: str) -> str:
        """Append a desktop and return its new hex id."""
        ...

    def rename_desktop(self, desktop_id: str, new_name: str) -> None:
        ...

    def remove_desktop(self, desktop_id: str) -> None:
        ...

    def remove_monitor(self, monitor_id: str) -> None:
        ...

    def move_window(self, window_id: str, target_desktop_id: str) -> None:
        ...

    def set_config(self, key: str, value: str) -> None:
        ...


class PolybarLauncher(Protocol):
    def kill_all(self) -> None:
        ...

    def launch(self, output: str, bar_definition: str, env: Dict[str, str]) -> int:
        ...


class Executor:
    """Runs a Plan against the system."""

    def __init__(
        self,
        xrandr: Optional[XrandrCommandRunner] = None,
        bspc: Optional[BspcCommandRunner] = None,
        polybar: Optional[PolybarLauncher] = None,
        wallpaper: Optional[WallpaperRunner] = None,
    ):
        self._xrandr = xrandr or SubprocessXrandrCommandRunner()
        self._bspc = bspc or SubprocessBspcCommandRunner()
        self._polybar = polybar or SubprocessPolybarLauncher()
        self._wallpaper = wallpaper or SubprocessWallpaperRunner()

    def execute(self, plan: Plan) -> ExecutionResult:
        bindings: Dict[str, str] = {}
        counter = [0]

        def mint(prefix: str) -> str:
            counter[0] += 1
            return f"${prefix}_{counter[0]}"

        completed: List[Op] = []
        for i, op in enumerate(plan.ops):
            try:
                resolved = self._resolve_refs(op, bindings)
                self._dispatch(resolved, bindings, mint)
                completed.append(op)
            except Exception as e:
                return ExecutionResult(
                    completed=tuple(completed),
                    failed=(op, e),
                    skipped=tuple(plan.ops[i + 1 :]),
                )
        return ExecutionResult(completed=tuple(completed))

    @staticmethod
    def _resolve(ref: str, bindings: Dict[str, str]) -> str:
        if not ref.startswith("$"):
            return ref
        if ref not in bindings:
            raise KeyError(f"unbound symbol {ref!r} (planner/executor mint mismatch)")
        return bindings[ref]

    def _resolve_refs(self, op: Op, bindings: Dict[str, str]) -> Op:
        """Replace any symbolic refs in op fields with their bound real ids."""
        if isinstance(op, BspcDesktopAdd):
            return replace(op, monitor_id=self._resolve(op.monitor_id, bindings))
        if isinstance(op, BspcDesktopRename):
            return replace(op, desktop_id=self._resolve(op.desktop_id, bindings))
        if isinstance(op, BspcDesktopRemove):
            return replace(op, desktop_id=self._resolve(op.desktop_id, bindings))
        if isinstance(op, BspcWindowMoveToDesktop):
            return replace(
                op,
                window_id=self._resolve(op.window_id, bindings),
                target_desktop_id=self._resolve(op.target_desktop_id, bindings),
            )
        if isinstance(op, BspcMonitorRemove):
            return replace(op, monitor_id=self._resolve(op.monitor_id, bindings))
        return op

    def _dispatch(self, op: Op, bindings: Dict[str, str], mint) -> None:
        if isinstance(op, XrandrApplyLayout):
            self._xrandr.apply_layout(op)
        elif isinstance(op, WaitForBspwmMonitor):
            new_monitor_id = self._bspc.wait_for_monitor(op.output, op.timeout_seconds)
            bindings[mint("M")] = new_monitor_id
            # Simulator predicts the monitor has zero desktops. Real bspwm may
            # have created defaults — drain them so reality matches the model.
            for desktop_id, _name in self._bspc.query_desktop_ids(new_monitor_id):
                self._bspc.remove_desktop(desktop_id)
        elif isinstance(op, BspcDesktopAdd):
            new_desktop_id = self._bspc.add_desktop(op.monitor_id, op.desktop_name)
            bindings[mint("D")] = new_desktop_id
        elif isinstance(op, BspcDesktopRename):
            self._bspc.rename_desktop(op.desktop_id, op.new_name)
        elif isinstance(op, BspcDesktopRemove):
            self._bspc.remove_desktop(op.desktop_id)
        elif isinstance(op, BspcWindowMoveToDesktop):
            self._bspc.move_window(op.window_id, op.target_desktop_id)
        elif isinstance(op, BspcMonitorRemove):
            self._bspc.remove_monitor(op.monitor_id)
        elif isinstance(op, BspcConfig):
            self._bspc.set_config(op.key, op.value)
        elif isinstance(op, PolybarKillAll):
            self._polybar.kill_all()
        elif isinstance(op, PolybarLaunch):
            self._polybar.launch(op.output, op.bar_definition, dict(op.env))
        elif isinstance(op, WallpaperRestore):
            self._wallpaper.restore()
        else:
            raise ValueError(f"unknown op type: {type(op).__name__}")


# ----- Subprocess-backed runners -----


class SubprocessXrandrCommandRunner:
    def apply_layout(self, op: XrandrApplyLayout) -> None:
        cmd = ["xrandr"]
        if op.fb is not None:
            cmd.extend(["--fb", f"{op.fb[0]}x{op.fb[1]}"])
        for a in op.applies:
            cmd.extend(
                [
                    "--output",
                    a.output,
                    "--mode",
                    a.mode,
                    "--pos",
                    f"{a.position[0]}x{a.position[1]}",
                ]
            )
            if a.rotation != "normal":
                cmd.extend(["--rotate", a.rotation])
            if a.scale != (1.0, 1.0):
                cmd.extend(["--scale", f"{a.scale[0]}x{a.scale[1]}"])
            if a.primary:
                cmd.append("--primary")
        for off in op.offs:
            cmd.extend(["--output", off.output, "--off"])
        subprocess.run(cmd, check=True, capture_output=True, text=True)


class SubprocessWallpaperRunner:
    def restore(self) -> None:
        # check=False: wallpaper is cosmetic; a missing nitrogen or a failed
        # repaint must not fail an otherwise-applied plan.
        subprocess.run(
            ["nitrogen", "--restore"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


class SubprocessBspcCommandRunner:
    """Wraps `bspc` invocations. Hex-id-only — names are unsafe selectors."""

    def wait_for_monitor(self, output_name: str, timeout: float) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                mid = self._monitor_id_by_name(output_name)
                # Brief settle so bspwm's default-desktop creation finishes
                # before we drain it.
                time.sleep(0.1)
                return mid
            except _MonitorNotFoundError:
                time.sleep(0.2)
        raise TimeoutError(
            f"bspwm did not register monitor {output_name!r} within {timeout}s"
        )

    def _monitor_id_by_name(self, name: str) -> str:
        ids_result = subprocess.run(
            ["bspc", "query", "-M"],
            check=True,
            capture_output=True,
            text=True,
        )
        for mid in ids_result.stdout.split():
            name_result = subprocess.run(
                ["bspc", "query", "-M", "-m", mid, "--names"],
                check=True,
                capture_output=True,
                text=True,
            )
            if name_result.stdout.strip() == name:
                return mid.strip()
        raise _MonitorNotFoundError(name)

    def query_desktop_ids(self, monitor_id: str) -> Tuple[Tuple[str, str], ...]:
        ids_result = subprocess.run(
            ["bspc", "query", "-D", "-m", monitor_id],
            check=True,
            capture_output=True,
            text=True,
        )
        out: List[Tuple[str, str]] = []
        for did in ids_result.stdout.split():
            name_result = subprocess.run(
                ["bspc", "query", "-D", "-d", did, "--names"],
                check=True,
                capture_output=True,
                text=True,
            )
            out.append((did.strip(), name_result.stdout.strip()))
        return tuple(out)

    def add_desktop(self, monitor_id: str, name: str) -> str:
        before = self._desktop_ids(monitor_id)
        subprocess.run(
            ["bspc", "monitor", monitor_id, "-a", name],
            check=True,
            capture_output=True,
            text=True,
        )
        after = self._desktop_ids(monitor_id)
        new = [d for d in after if d not in before]
        if not new:
            raise RuntimeError(
                f"bspc monitor {monitor_id} -a {name} did not produce a new desktop"
            )
        # bspc -a appends, so the new id is the last one. If multiple appeared
        # (shouldn't), take the last.
        return new[-1]

    def _desktop_ids(self, monitor_id: str) -> List[str]:
        result = subprocess.run(
            ["bspc", "query", "-D", "-m", monitor_id],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.split()

    def rename_desktop(self, desktop_id: str, new_name: str) -> None:
        subprocess.run(
            ["bspc", "desktop", desktop_id, "-n", new_name],
            check=True,
            capture_output=True,
            text=True,
        )

    def remove_desktop(self, desktop_id: str) -> None:
        subprocess.run(
            ["bspc", "desktop", desktop_id, "-r"],
            check=True,
            capture_output=True,
            text=True,
        )

    def remove_monitor(self, monitor_id: str) -> None:
        subprocess.run(
            ["bspc", "monitor", monitor_id, "-r"],
            check=True,
            capture_output=True,
            text=True,
        )

    def move_window(self, window_id: str, target_desktop_id: str) -> None:
        subprocess.run(
            ["bspc", "node", window_id, "-d", target_desktop_id],
            check=True,
            capture_output=True,
            text=True,
        )

    def set_config(self, key: str, value: str) -> None:
        subprocess.run(
            ["bspc", "config", key, value],
            check=True,
            capture_output=True,
            text=True,
        )


class _MonitorNotFoundError(Exception):
    pass


class SubprocessPolybarLauncher:
    DEFAULT_CONFIG = Path.home() / ".config/polybar/shades/config.ini"

    def __init__(self, config_file: Optional[Path] = None):
        self._config_file = Path(config_file) if config_file else self.DEFAULT_CONFIG

    def kill_all(self) -> None:
        subprocess.run(
            ["pkill", "-f", "polybar"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # bspwm/polybar are async — give a moment for processes to terminate
        time.sleep(0.3)

    def launch(self, output: str, bar_definition: str, env: Dict[str, str]) -> int:
        proc = subprocess.Popen(
            ["polybar", "-q", bar_definition, "-c", str(self._config_file)],
            env={**os.environ, **env},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return proc.pid


__all__ = [
    "BspcCommandRunner",
    "ExecutionResult",
    "Executor",
    "PolybarLauncher",
    "SubprocessBspcCommandRunner",
    "SubprocessPolybarLauncher",
    "SubprocessXrandrCommandRunner",
    "XrandrCommandRunner",
]
