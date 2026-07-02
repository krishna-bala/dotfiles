"""Tests for desired state compilation from profile."""

import unittest
from pathlib import Path

from lib.profile import ProfileService
from lib.state.desired import compile_desired


class TestCompilePersonalSolo(unittest.TestCase):
    def setUp(self):
        self.profiles_dir = Path(__file__).parent / "fixtures" / "profiles"
        self.service = ProfileService(self.profiles_dir)
        self.profile = self.service.load_profile("personal-solo")
        self.desired = compile_desired(self.profile, alias_to_output={"laptop": "eDP-1"})

    def test_profile_name_preserved(self):
        self.assertEqual(self.desired.profile_name, "personal-solo")

    def test_single_output(self):
        self.assertEqual(len(self.desired.outputs), 1)
        out = self.desired.outputs[0]
        self.assertEqual(out.name, "eDP-1")
        self.assertTrue(out.enabled)
        self.assertEqual(out.mode, "1920x1200")
        self.assertEqual(out.position, (0, 0))
        self.assertTrue(out.primary)
        self.assertEqual(out.scale, (1.0, 1.0))
        self.assertEqual(out.rotation, "normal")

    def test_monitor_order(self):
        self.assertEqual(self.desired.monitor_order, ("eDP-1",))

    def test_workspaces(self):
        self.assertEqual(len(self.desired.workspaces), 1)
        ws = self.desired.workspaces[0]
        self.assertEqual(ws.output, "eDP-1")
        self.assertEqual(
            ws.desktop_names,
            ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"),
        )

    def test_bar(self):
        self.assertEqual(len(self.desired.bars), 1)
        bar = self.desired.bars[0]
        self.assertEqual(bar.output, "eDP-1")
        self.assertEqual(bar.orientation, "landscape")
        self.assertEqual(bar.font_size, 16)
        self.assertIn("workspaces", bar.modules_left)
        self.assertIn("date", bar.modules_center)


class TestCompilePersonalHome(unittest.TestCase):
    """Dual-monitor profile with the laptop disabled — exercises the harder
    paths: rotation, sub-1.0 scale, multiple workspaces, multiple bars."""

    def setUp(self):
        self.profiles_dir = Path(__file__).parent / "fixtures" / "profiles"
        self.service = ProfileService(self.profiles_dir)
        self.profile = self.service.load_profile("personal-home")
        self.desired = compile_desired(
            self.profile,
            alias_to_output={"laptop": "eDP-1", "vertical": "DP-2", "main": "DP-3"},
        )

    def _outputs_by_name(self):
        return {o.name: o for o in self.desired.outputs}

    def test_laptop_disabled_externals_enabled(self):
        out = self._outputs_by_name()
        self.assertFalse(out["eDP-1"].enabled)
        self.assertTrue(out["DP-2"].enabled)
        self.assertTrue(out["DP-3"].enabled)

    def test_main_is_primary(self):
        out = self._outputs_by_name()
        self.assertTrue(out["DP-3"].primary)
        self.assertFalse(out["DP-2"].primary)

    def test_vertical_rotation_and_scale(self):
        out = self._outputs_by_name()
        self.assertEqual(out["DP-2"].rotation, "left")
        self.assertEqual(out["DP-2"].scale, (0.6, 0.6))
        self.assertEqual(out["DP-2"].mode, "3840x2160")

    def test_main_position_and_mode(self):
        out = self._outputs_by_name()
        self.assertEqual(out["DP-3"].mode, "2560x1440")
        self.assertEqual(out["DP-3"].position, (1296, 432))

    def test_monitor_order_resolved(self):
        # Profile order is [main, vertical] → [DP-3, DP-2]
        self.assertEqual(self.desired.monitor_order, ("DP-3", "DP-2"))

    def test_workspaces_split(self):
        ws = {w.output: w.desktop_names for w in self.desired.workspaces}
        self.assertEqual(ws["DP-3"], ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10"))
        self.assertEqual(
            ws["DP-2"],
            ("11", "12", "13", "14", "15", "16", "17", "18", "19", "20"),
        )

    def test_two_bars(self):
        self.assertEqual(len(self.desired.bars), 2)
        bars_by_output = {b.output: b for b in self.desired.bars}
        self.assertEqual(bars_by_output["DP-3"].orientation, "landscape")
        self.assertEqual(bars_by_output["DP-2"].orientation, "portrait")


class TestCompileDropsUnmappedAliases(unittest.TestCase):
    """If alias_to_output is missing an alias, that alias's outputs/bars/
    workspaces drop silently — same forgiveness the existing coordinator has."""

    def setUp(self):
        self.profiles_dir = Path(__file__).parent / "fixtures" / "profiles"
        self.service = ProfileService(self.profiles_dir)

    def test_missing_alias_drops_output(self):
        profile = self.service.load_profile("personal-home")
        # Only resolve "main" — the others should drop
        desired = compile_desired(profile, alias_to_output={"main": "DP-3"})
        names = {o.name for o in desired.outputs}
        self.assertEqual(names, {"DP-3"})
        self.assertEqual(desired.monitor_order, ("DP-3",))
        self.assertEqual(len(desired.bars), 1)


class TestCompileSettings(unittest.TestCase):
    def test_profile_settings_override_defaults(self):
        profile = ProfileService(
            Path(__file__).parent / "fixtures" / "profiles"
        ).load_profile("personal-solo")
        desired = compile_desired(profile, alias_to_output={"laptop": "eDP-1"})
        # personal-solo sets border_width=7, window_gap=15 — same as defaults,
        # but the values should round-trip through compilation.
        self.assertEqual(desired.bspwm_settings.border_width, 7)
        self.assertEqual(desired.bspwm_settings.window_gap, 15)
        self.assertEqual(desired.bspwm_settings.focused_border_color, "#629dc8")


if __name__ == "__main__":
    unittest.main()
