"""Tests for op data types and Plan."""

import unittest
from dataclasses import FrozenInstanceError

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
    XrandrOff,
)


class TestPlan(unittest.TestCase):
    def test_empty_plan_is_noop(self):
        self.assertTrue(Plan(profile_name="x").is_noop())

    def test_nonempty_plan_is_not_noop(self):
        plan = Plan(profile_name="x", ops=(XrandrOff(output="DP-2"),))
        self.assertFalse(plan.is_noop())

    def test_plan_is_frozen(self):
        plan = Plan(profile_name="x")
        with self.assertRaises(FrozenInstanceError):
            plan.ops = (XrandrOff(output="DP-2"),)  # type: ignore[misc]

    def test_plan_equality(self):
        a = Plan(profile_name="x", ops=(XrandrOff(output="DP-2"),))
        b = Plan(profile_name="x", ops=(XrandrOff(output="DP-2"),))
        self.assertEqual(a, b)


class TestOps(unittest.TestCase):
    def test_xrandr_apply_fields(self):
        op = XrandrApply(
            output="eDP-1",
            mode="1920x1200",
            position=(0, 0),
            rotation="normal",
            scale=(1.0, 1.0),
            primary=True,
        )
        self.assertEqual(op.output, "eDP-1")
        self.assertEqual(op.position, (0, 0))
        self.assertTrue(op.primary)

    def test_wait_default_timeout(self):
        op = WaitForBspwmMonitor(output="eDP-1")
        self.assertEqual(op.timeout_seconds, 7.5)

    def test_polybar_launch_default_env_empty(self):
        op = PolybarLaunch(output="eDP-1", bar_definition="main")
        self.assertEqual(op.env, ())

    def test_ops_are_hashable(self):
        # Hashability lets ops live in sets — useful for "expected ops" tests
        ops = {
            XrandrOff(output="DP-2"),
            XrandrOff(output="DP-3"),
            BspcDesktopAdd(monitor_id="m1", desktop_name="1"),
        }
        self.assertEqual(len(ops), 3)

    def test_op_equality_by_value(self):
        a = XrandrOff(output="DP-2")
        b = XrandrOff(output="DP-2")
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_all_op_types_construct(self):
        # Smoke test: each op type can be built with reasonable args.
        ops = [
            XrandrApply("eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True),
            XrandrOff("DP-2"),
            WaitForBspwmMonitor("eDP-1", 7.5),
            BspcDesktopAdd("m1", "1"),
            BspcDesktopRename("d1", "1"),
            BspcDesktopRemove("d1"),
            BspcWindowMoveToDesktop("w1", "d1"),
            BspcMonitorRemove("m1"),
            BspcConfig("border_width", "7"),
            PolybarKillAll(),
            PolybarLaunch("eDP-1", "main", env=(("MONITOR", "eDP-1"),)),
        ]
        # Plan accepts any mix of them
        plan = Plan(profile_name="test", ops=tuple(ops))
        self.assertEqual(len(plan.ops), 11)


if __name__ == "__main__":
    unittest.main()
