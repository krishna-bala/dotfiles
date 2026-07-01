"""Tests for hardware state data types."""

import unittest
from dataclasses import FrozenInstanceError

from lib.state.hardware import (
    BspwmDesktop,
    BspwmMonitor,
    BspwmSettings,
    HardwareState,
    XrandrOutput,
)


class TestHardwareState(unittest.TestCase):
    def test_default_state_is_empty(self):
        state = HardwareState()
        self.assertEqual(state.outputs, ())
        self.assertEqual(state.bspwm_monitors, ())
        self.assertEqual(state.bspwm_settings, BspwmSettings())
        self.assertEqual(state.polybar_pids, ())

    def test_state_is_frozen(self):
        state = HardwareState()
        with self.assertRaises(FrozenInstanceError):
            state.outputs = (XrandrOutput(name="eDP-1", connected=True),)  # type: ignore[misc]

    def test_state_equality(self):
        a = HardwareState(outputs=(XrandrOutput(name="eDP-1", connected=True),))
        b = HardwareState(outputs=(XrandrOutput(name="eDP-1", connected=True),))
        self.assertEqual(a, b)

    def test_full_state_construction(self):
        state = HardwareState(
            outputs=(
                XrandrOutput(
                    name="eDP-1",
                    connected=True,
                    active_mode="1920x1200",
                    position=(0, 0),
                    primary=True,
                ),
                XrandrOutput(name="DP-2", connected=False),
            ),
            bspwm_monitors=(
                BspwmMonitor(
                    id="0xA",
                    name="eDP-1",
                    desktops=(
                        BspwmDesktop(id="0xA1", name="1", window_ids=("w1", "w2")),
                        BspwmDesktop(id="0xA2", name="2"),
                    ),
                ),
            ),
            bspwm_settings=BspwmSettings(border_width=10),
            polybar_pids=(1234, 5678),
        )
        self.assertEqual(len(state.outputs), 2)
        self.assertEqual(state.outputs[0].name, "eDP-1")
        self.assertTrue(state.outputs[0].primary)
        self.assertFalse(state.outputs[1].connected)
        self.assertEqual(state.bspwm_monitors[0].desktops[0].window_ids, ("w1", "w2"))
        self.assertEqual(state.bspwm_settings.border_width, 10)
        self.assertEqual(state.polybar_pids, (1234, 5678))


class TestXrandrOutput(unittest.TestCase):
    def test_minimal_construction(self):
        o = XrandrOutput(name="eDP-1", connected=True)
        self.assertIsNone(o.active_mode)
        self.assertIsNone(o.position)
        self.assertEqual(o.rotation, "normal")
        self.assertEqual(o.scale, (1.0, 1.0))
        self.assertFalse(o.primary)

    def test_is_hashable(self):
        # Frozen dataclasses with hashable fields should be hashable
        outputs = {
            XrandrOutput(name="eDP-1", connected=True),
            XrandrOutput(name="DP-2", connected=False),
            XrandrOutput(name="eDP-1", connected=True),
        }
        self.assertEqual(len(outputs), 2)


class TestBspwmDesktop(unittest.TestCase):
    def test_default_window_ids_empty(self):
        d = BspwmDesktop(id="0xA", name="1")
        self.assertEqual(d.window_ids, ())

    def test_distinct_ids_with_same_name(self):
        # Critical invariant: two desktops can share a name across monitors
        # but their ids are distinct. The reconciler treats id as the key.
        a = BspwmDesktop(id="0xA1", name="1")
        b = BspwmDesktop(id="0xB1", name="1")
        self.assertNotEqual(a, b)


class TestBspwmSettings(unittest.TestCase):
    def test_defaults_match_bspwmrc_baseline(self):
        # If these defaults drift from bspwmrc lines 87-93, profiles will
        # disagree about what "default" means. Pin them.
        s = BspwmSettings()
        self.assertEqual(s.border_width, 7)
        self.assertEqual(s.window_gap, 15)
        self.assertEqual(s.focused_border_color, "#629dc8")
        self.assertEqual(s.normal_border_color, "#1f2339")


if __name__ == "__main__":
    unittest.main()
