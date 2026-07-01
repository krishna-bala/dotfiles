"""Tests for xrandr probe."""

import unittest
from pathlib import Path

from lib.edid import hash_edid
from lib.probe.xrandr import XrandrProbe

FIXTURES = Path(__file__).parent / "fixtures" / "xrandr"


class TestXrandrParseFromFixture(unittest.TestCase):
    def setUp(self):
        self.outputs = XrandrProbe.parse(
            (FIXTURES / "personal-solo-props.txt").read_text()
        )
        self.by_name = {o.name: o for o in self.outputs}

    def test_all_six_outputs_seen(self):
        self.assertEqual(
            set(self.by_name.keys()),
            {"eDP-1", "DP-1", "HDMI-1", "DP-2", "DP-3", "DP-4"},
        )

    def test_edp_active_and_primary(self):
        edp = self.by_name["eDP-1"]
        self.assertTrue(edp.connected)
        self.assertTrue(edp.primary)
        self.assertEqual(edp.active_mode, "1920x1080")
        self.assertEqual(edp.position, (0, 0))
        self.assertEqual(edp.rotation, "normal")

    def test_disconnected_outputs_have_no_geom(self):
        for name in ("DP-1", "HDMI-1", "DP-2", "DP-3", "DP-4"):
            o = self.by_name[name]
            self.assertFalse(o.connected, f"{name} should be disconnected")
            self.assertIsNone(o.active_mode, f"{name} should have no active_mode")
            self.assertIsNone(o.position, f"{name} should have no position")

    def test_edid_extracted_for_connected(self):
        edp = self.by_name["eDP-1"]
        self.assertIsNotNone(edp.edid)
        # edid is the truncated EDID hash (match key), not the raw bytes
        self.assertEqual(len(edp.edid), 16)
        int(edp.edid, 16)  # valid hex


class TestXrandrParseSynthetic(unittest.TestCase):
    def test_dual_monitor_with_rotation_and_offset(self):
        dp2_raw = "00ffffffffffff00aabbccddeeff00112233445566778899"
        dp3_raw = "00ffffffffffff00f1e2d3c4b5a69788776655443322110099"
        text = (
            "Screen 0: minimum 320 x 200, current 5760 x 2160, maximum 16384 x 16384\n"
            "eDP-1-1 disconnected (normal left inverted right x axis y axis)\n"
            "DP-2 connected 3840x2160+0+0 left "
            "(normal left inverted right x axis y axis) 600mm x 340mm\n"
            "\tEDID:\n"
            f"\t\t{dp2_raw}\n"
            "DP-3 connected primary 2560x1440+1296+432 "
            "(normal left inverted right x axis y axis) 600mm x 340mm\n"
            "\tEDID:\n"
            f"\t\t{dp3_raw}\n"
        )
        outputs = XrandrProbe.parse(text)
        by_name = {o.name: o for o in outputs}

        self.assertFalse(by_name["eDP-1-1"].connected)

        dp2 = by_name["DP-2"]
        self.assertTrue(dp2.connected)
        self.assertFalse(dp2.primary)
        self.assertEqual(dp2.rotation, "left")
        self.assertEqual(dp2.active_mode, "3840x2160")
        self.assertEqual(dp2.position, (0, 0))
        self.assertEqual(dp2.edid, hash_edid(dp2_raw))

        dp3 = by_name["DP-3"]
        self.assertTrue(dp3.primary)
        self.assertEqual(dp3.active_mode, "2560x1440")
        self.assertEqual(dp3.position, (1296, 432))
        self.assertEqual(dp3.edid, hash_edid(dp3_raw))
        self.assertNotEqual(dp2.edid, dp3.edid)
        self.assertEqual(dp3.rotation, "normal")

    def test_disconnected_with_stale_primary_word(self):
        # The actual rollback file showed "DP-3 disconnected primary"
        text = "DP-3 disconnected primary (normal left inverted right x axis y axis)\n"
        outputs = XrandrProbe.parse(text)
        self.assertEqual(len(outputs), 1)
        self.assertFalse(outputs[0].connected)
        self.assertTrue(outputs[0].primary)
        self.assertIsNone(outputs[0].active_mode)

    def test_empty_input(self):
        self.assertEqual(XrandrProbe.parse(""), ())

    def test_screen_line_is_ignored(self):
        outputs = XrandrProbe.parse(
            "Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 16384 x 16384\n"
        )
        self.assertEqual(outputs, ())


class TestXrandrProbeWithRunner(unittest.TestCase):
    def test_calls_runner_then_parses(self):
        class FakeRunner:
            def get_props(self):
                return (
                    "eDP-1 connected primary 1920x1200+0+0 "
                    "(normal left inverted right x axis y axis) 336mm x 210mm\n"
                )

        outputs = XrandrProbe(runner=FakeRunner()).read()
        self.assertEqual(outputs[0].name, "eDP-1")
        self.assertEqual(outputs[0].active_mode, "1920x1200")


if __name__ == "__main__":
    unittest.main()
