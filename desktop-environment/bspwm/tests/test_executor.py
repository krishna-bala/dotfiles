"""Tests for the executor."""

import unittest
from typing import List, Tuple

from lib.executor import Executor
from lib.ops import (
    BspcConfig,
    BspcDesktopAdd,
    BspcDesktopRemove,
    BspcDesktopRename,
    BspcMonitorRemove,
    BspcWindowMoveToDesktop,
    Plan,
    PolybarKillAll,
    PolybarLaunch,
    WaitForBspwmMonitor,
    XrandrApply,
    XrandrApplyLayout,
    XrandrOff,
)

# ----- Fakes that record calls and let tests inject behavior -----


class _XrandrFake:
    def __init__(self):
        self.calls: List[Tuple[str, ...]] = []

    def apply_layout(self, op):
        for a in op.applies:
            self.calls.append(
                ("apply", a.output, a.mode, a.position, a.rotation, a.scale, a.primary)
            )
        for off in op.offs:
            self.calls.append(("off", off.output))
        self.calls.append(("fb", op.fb))


class _BspcFake:
    def __init__(self):
        self.calls: List[Tuple] = []
        # Each WaitForBspwmMonitor returns the next id; tests pre-load.
        self.next_monitor_id: List[str] = []
        # Each add_desktop returns the next id; tests pre-load.
        self.next_desktop_id: List[str] = []
        # query_desktop_ids returns whatever the test set.
        self.default_desktops: List[Tuple[str, str]] = []

    def wait_for_monitor(self, output_name, timeout):
        self.calls.append(("wait", output_name, timeout))
        return self.next_monitor_id.pop(0)

    def query_desktop_ids(self, monitor_id):
        self.calls.append(("query_desktops", monitor_id))
        return tuple(self.default_desktops)

    def add_desktop(self, monitor_id, name):
        self.calls.append(("add", monitor_id, name))
        return self.next_desktop_id.pop(0)

    def rename_desktop(self, desktop_id, new_name):
        self.calls.append(("rename", desktop_id, new_name))

    def remove_desktop(self, desktop_id):
        self.calls.append(("remove_desktop", desktop_id))

    def remove_monitor(self, monitor_id):
        self.calls.append(("remove_monitor", monitor_id))

    def move_window(self, window_id, target_desktop_id):
        self.calls.append(("move", window_id, target_desktop_id))

    def set_config(self, key, value):
        self.calls.append(("config", key, value))


class _PolybarFake:
    def __init__(self):
        self.calls: List[Tuple] = []
        self._next_pid = 50000

    def kill_all(self):
        self.calls.append(("kill",))

    def launch(self, output, bar_definition, env):
        self.calls.append(("launch", output, bar_definition, dict(env)))
        self._next_pid += 1
        return self._next_pid


class _WallpaperFake:
    def __init__(self):
        self.calls: List[Tuple] = []

    def restore(self):
        self.calls.append(("restore",))


def _executor_with_fakes():
    x = _XrandrFake()
    b = _BspcFake()
    p = _PolybarFake()
    return Executor(xrandr=x, bspc=b, polybar=p, wallpaper=_WallpaperFake()), x, b, p


# ----- Tests -----


class TestExecuteSimpleOps(unittest.TestCase):
    def test_xrandr_apply(self):
        e, x, _, _ = _executor_with_fakes()
        plan = Plan(
            profile_name="x",
            ops=(
                XrandrApplyLayout(
                    applies=(
                        XrandrApply(
                            "eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True
                        ),
                    ),
                    fb=(1920, 1200),
                ),
            ),
        )
        result = e.execute(plan)
        self.assertTrue(result.succeeded())
        self.assertEqual(
            x.calls,
            [
                ("apply", "eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True),
                ("fb", (1920, 1200)),
            ],
        )

    def test_xrandr_off(self):
        e, x, _, _ = _executor_with_fakes()
        e.execute(
            Plan(
                profile_name="x",
                ops=(XrandrApplyLayout(offs=(XrandrOff("DP-2"),)),),
            )
        )
        self.assertEqual(x.calls, [("off", "DP-2"), ("fb", None)])

    def test_bspc_simple_ops(self):
        e, _, b, _ = _executor_with_fakes()
        ops = (
            BspcDesktopRename("0xA1", "1"),
            BspcDesktopRemove("0xA2"),
            BspcMonitorRemove("0xA"),
            BspcWindowMoveToDesktop("0xW1", "0xA1"),
            BspcConfig("border_width", "7"),
        )
        e.execute(Plan(profile_name="x", ops=ops))
        self.assertEqual(
            b.calls,
            [
                ("rename", "0xA1", "1"),
                ("remove_desktop", "0xA2"),
                ("remove_monitor", "0xA"),
                ("move", "0xW1", "0xA1"),
                ("config", "border_width", "7"),
            ],
        )

    def test_polybar(self):
        e, _, _, p = _executor_with_fakes()
        ops = (
            PolybarKillAll(),
            PolybarLaunch("eDP-1", "main", env=(("MONITOR", "eDP-1"),)),
        )
        e.execute(Plan(profile_name="x", ops=ops))
        self.assertEqual(p.calls[0], ("kill",))
        self.assertEqual(p.calls[1][0], "launch")
        self.assertEqual(p.calls[1][1], "eDP-1")
        self.assertEqual(p.calls[1][3], {"MONITOR": "eDP-1"})


class TestSymbolBinding(unittest.TestCase):
    def test_wait_binds_monitor_symbol_then_drains_defaults(self):
        e, _, b, _ = _executor_with_fakes()
        b.next_monitor_id = ["0xREAL_M"]
        b.default_desktops = [("0xDEF1", "Desktop"), ("0xDEF2", "Other")]

        e.execute(Plan(profile_name="x", ops=(WaitForBspwmMonitor("eDP-1"),)))

        # Wait, then query, then remove each default.
        kinds = [c[0] for c in b.calls]
        self.assertEqual(
            kinds,
            ["wait", "query_desktops", "remove_desktop", "remove_desktop"],
        )
        # Defaults removed by id
        self.assertEqual(b.calls[2], ("remove_desktop", "0xDEF1"))
        self.assertEqual(b.calls[3], ("remove_desktop", "0xDEF2"))

    def test_add_binds_desktop_symbol_then_subsequent_op_resolves(self):
        e, _, b, _ = _executor_with_fakes()
        b.next_monitor_id = ["0xMREAL"]
        # First desktop add returns 0xD_REAL_1, second returns 0xD_REAL_2
        b.next_desktop_id = ["0xD_REAL_1", "0xD_REAL_2"]
        b.default_desktops = []

        # Plan emits the same shape the reconciler emits for a cold-start:
        # Wait → mints $M_1, AddDesktop on $M_1 → mints $D_2, AddDesktop on $M_1 → mints $D_3,
        # then a window move targeting $D_2, finally remove $D_3.
        plan = Plan(
            profile_name="x",
            ops=(
                WaitForBspwmMonitor("eDP-1"),
                BspcDesktopAdd(monitor_id="$M_1", desktop_name="1"),
                BspcDesktopAdd(monitor_id="$M_1", desktop_name="2"),
                BspcWindowMoveToDesktop(window_id="0xW", target_desktop_id="$D_2"),
                BspcDesktopRemove(desktop_id="$D_3"),
            ),
        )

        result = e.execute(plan)
        self.assertTrue(result.succeeded())

        # Each subsequent symbolic ref should have been resolved against bindings.
        # add: "$M_1" → "0xMREAL" (bound by the wait op)
        self.assertEqual(b.calls[2], ("add", "0xMREAL", "1"))
        self.assertEqual(b.calls[3], ("add", "0xMREAL", "2"))
        # move: target "$D_2" → "0xD_REAL_1" (bound by first add)
        self.assertEqual(b.calls[4], ("move", "0xW", "0xD_REAL_1"))
        # remove: "$D_3" → "0xD_REAL_2" (bound by second add)
        self.assertEqual(b.calls[5], ("remove_desktop", "0xD_REAL_2"))

    def test_unbound_symbol_raises(self):
        e, _, _, _ = _executor_with_fakes()
        # Reference $D_99 without any add to bind it.
        plan = Plan(
            profile_name="x",
            ops=(BspcDesktopRemove(desktop_id="$D_99"),),
        )
        result = e.execute(plan)
        self.assertFalse(result.succeeded())
        self.assertIsNotNone(result.failed)
        op, exc = result.failed
        self.assertIsInstance(op, BspcDesktopRemove)
        self.assertIsInstance(exc, KeyError)


class TestFailureHandling(unittest.TestCase):
    def test_failure_stops_execution_and_reports_skipped(self):
        class FailingBspc(_BspcFake):
            def rename_desktop(self, desktop_id, new_name):
                raise RuntimeError("bspc says no")

        e = Executor(xrandr=_XrandrFake(), bspc=FailingBspc(), polybar=_PolybarFake())
        ops = (
            BspcConfig("border_width", "7"),  # succeeds
            BspcDesktopRename("0xA", "1"),  # fails
            BspcConfig("window_gap", "15"),  # skipped
            BspcConfig("split_ratio", "0.5"),  # skipped
        )
        result = e.execute(Plan(profile_name="x", ops=ops))

        self.assertFalse(result.succeeded())
        self.assertEqual(len(result.completed), 1)
        self.assertIsInstance(result.completed[0], BspcConfig)
        self.assertIsNotNone(result.failed)
        self.assertIsInstance(result.failed[0], BspcDesktopRename)
        self.assertIsInstance(result.failed[1], RuntimeError)
        self.assertEqual(len(result.skipped), 2)


class TestPlannerExecutorRoundTrip(unittest.TestCase):
    """End-to-end: feed a real Reconciler-produced Plan through the Executor
    with fake runners, verify the bspc/xrandr call sequence is what the bug
    fix demands."""

    def test_unplug_regression_through_executor(self):
        from pathlib import Path

        from lib.plan import PreserveByName
        from lib.profile import ProfileService
        from lib.reconciler import Reconciler
        from lib.state.desired import compile_desired
        from lib.state.hardware import (
            BspwmDesktop,
            BspwmMonitor,
            HardwareState,
            XrandrOutput,
        )

        profiles_dir = Path(__file__).parent / "fixtures" / "profiles"

        # The exact unplug pre-state
        dp2 = BspwmMonitor(
            id="0xA0",
            name="DP-2",
            desktops=tuple(
                BspwmDesktop(
                    id=f"0xA{i:X}", name=str(10 + i), window_ids=(f"w{10 + i}",)
                )
                for i in range(1, 11)
            ),
        )
        dp3 = BspwmMonitor(
            id="0xB0",
            name="DP-3",
            desktops=tuple(
                BspwmDesktop(id=f"0xB{i:X}", name=str(i), window_ids=(f"v{i}",))
                for i in range(1, 11)
            ),
        )
        current = HardwareState(
            outputs=(
                XrandrOutput(name="eDP-1", connected=True),
                XrandrOutput(name="DP-2", connected=False),
                XrandrOutput(name="DP-3", connected=False),
            ),
            bspwm_monitors=(dp2, dp3),
        )

        profile = ProfileService(profiles_dir).load_profile("personal-solo")
        desired = compile_desired(profile, alias_to_output={"laptop": "eDP-1"})

        plan = Reconciler().plan(current, desired, merge_policy=PreserveByName())

        # Set up fakes to simulate real bspwm responses.
        e, x, b, p = _executor_with_fakes()
        # The Wait op gets a real monitor id back.
        b.next_monitor_id = ["0xEDP_REAL"]
        # bspwm gives us no default desktops on monitor add (best case).
        b.default_desktops = []
        # Each of the 10 BspcDesktopAdd ops returns a fresh real id.
        b.next_desktop_id = [f"0xEDP_D{i}" for i in range(1, 11)]

        result = e.execute(plan)
        self.assertTrue(result.succeeded(), msg=str(result.failed))

        # Check the call sequence:
        # 1. xrandr apply eDP-1
        self.assertEqual(x.calls[0][0], "apply")
        self.assertEqual(x.calls[0][1], "eDP-1")

        # 2. bspc: wait, query (drain default — none here), then 10 adds, etc.
        bspc_kinds = [c[0] for c in b.calls]
        self.assertEqual(bspc_kinds[0], "wait")
        self.assertEqual(bspc_kinds[1], "query_desktops")
        # 10 adds for desktops 1..10 on eDP-1
        add_calls = [c for c in b.calls if c[0] == "add"]
        self.assertEqual(len(add_calls), 10)
        for i, call in enumerate(add_calls, start=1):
            self.assertEqual(call, ("add", "0xEDP_REAL", str(i)))

        # 20 window moves
        moves = [c for c in b.calls if c[0] == "move"]
        self.assertEqual(len(moves), 20)
        # Each window's target is a real id (not a symbol)
        for _, _, target in moves:
            self.assertFalse(target.startswith("$"), f"unresolved symbol {target!r}")

        # 18 desktop removes: 9 per stale monitor — the last empty desktop
        # on each is left for `monitor -r` to absorb (bspwm refuses to
        # remove a monitor's last desktop directly)
        removes = [c for c in b.calls if c[0] == "remove_desktop"]
        self.assertEqual(len(removes), 18)

        # 2 monitor removes (DP-2, DP-3) by their original real ids
        monitor_removes = [c for c in b.calls if c[0] == "remove_monitor"]
        self.assertEqual(len(monitor_removes), 2)
        self.assertEqual(
            {c[1] for c in monitor_removes}, {"0xA0", "0xB0"}
        )

        # Polybar: 1 launch (we had no previous polybar pids in current)
        self.assertEqual([c[0] for c in p.calls], ["launch"])


if __name__ == "__main__":
    unittest.main()
