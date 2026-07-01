"""Tests for plan rendering."""

import unittest

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
from lib.renderer import Renderer


class TestRenderer(unittest.TestCase):
    def setUp(self):
        self.r = Renderer()

    def test_empty_plan_says_no_changes(self):
        out = self.r.render(Plan(profile_name="personal-solo"))
        self.assertIn("personal-solo", out)
        self.assertIn("no changes", out)

    def test_plan_summary_includes_op_count(self):
        plan = Plan(
            profile_name="personal-solo",
            ops=(XrandrOff("DP-2"), XrandrOff("DP-3")),
        )
        out = self.r.render(plan)
        self.assertIn("Ops: 2", out)

    def test_full_plan_renders_each_op_type(self):
        plan = Plan(
            profile_name="personal-solo",
            ops=(
                XrandrApply("eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True),
                XrandrOff("DP-2"),
                WaitForBspwmMonitor("eDP-1", 7.5),
                BspcDesktopRename("0xA1", "1"),
                BspcDesktopAdd("0xA", "2"),
                BspcWindowMoveToDesktop("w1", "0xB1"),
                BspcDesktopRemove("0xC1"),
                BspcMonitorRemove("0xC"),
                BspcConfig("border_width", "7"),
                PolybarKillAll(),
                PolybarLaunch("eDP-1", "main", env=(("MONITOR", "eDP-1"),)),
            ),
        )
        out = self.r.render(plan)
        # Each line should be referenced by something distinctive
        for needle in [
            "personal-solo",
            "Ops: 11",
            "xrandr apply",
            "1920x1200",
            "primary",
            "xrandr off",
            "DP-2",
            "wait",
            "desktop rename",
            "desktop add",
            "window move",
            "desktop remove",
            "monitor remove",
            "border_width = 7",
            "polybar kill",
            "polybar launch",
            "MONITOR=eDP-1",
        ]:
            self.assertIn(needle, out, f"missing {needle!r} in renderer output")

    def test_xrandr_apply_with_rotation_and_scale(self):
        op = XrandrApply("DP-2", "3840x2160", (0, 0), "left", (0.6, 0.6), False)
        line = self.r.render_op(op)
        self.assertIn("rotate=left", line)
        self.assertIn("scale=0.6x0.6", line)
        self.assertNotIn("primary", line)

    def test_xrandr_apply_omits_normal_rotation_and_unit_scale(self):
        op = XrandrApply("eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True)
        line = self.r.render_op(op)
        self.assertNotIn("rotate", line)
        self.assertNotIn("scale", line)
        self.assertIn("primary", line)

    def test_render_op_returns_nonempty_string_for_each_op_type(self):
        ops = [
            XrandrApply("eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True),
            XrandrOff("DP-2"),
            WaitForBspwmMonitor("eDP-1"),
            BspcDesktopAdd("m1", "1"),
            BspcDesktopRename("d1", "1"),
            BspcDesktopRemove("d1"),
            BspcWindowMoveToDesktop("w1", "d1"),
            BspcMonitorRemove("m1"),
            BspcConfig("border_width", "7"),
            PolybarKillAll(),
            PolybarLaunch("eDP-1", "main"),
        ]
        for op in ops:
            line = self.r.render_op(op)
            self.assertIsInstance(line, str)
            self.assertTrue(line.strip(), f"empty rendering for {op!r}")


if __name__ == "__main__":
    unittest.main()
