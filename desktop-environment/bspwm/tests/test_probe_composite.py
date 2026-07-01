"""Tests for the composite state probe."""

import unittest

from lib.probe.bspwm import BspwmProbe
from lib.probe.composite import CompositeStateProbe
from lib.probe.polybar import PolybarProbe
from lib.probe.xrandr import XrandrProbe
from lib.state.hardware import BspwmSettings


class _FakeXrandrRunner:
    def get_props(self):
        return (
            "eDP-1 connected primary 1920x1200+0+0 "
            "(normal left inverted right x axis y axis) 336mm x 210mm\n"
        )


class _FakeBspcRunner:
    def __init__(self):
        self._settings = {
            "border_width": "7",
            "window_gap": "15",
            "focused_border_color": "#629dc8",
            "normal_border_color": "#1f2339",
            "split_ratio": "0.5",
            "borderless_monocle": "false",
            "gapless_monocle": "false",
        }

    def dump_state(self):
        return (
            '{"monitors": [{"id": 1, "name": "eDP-1", "desktops": ['
            '{"id": 11, "name": "1", "root": null},'
            '{"id": 12, "name": "2", "root": null}'
            "]}]}"
        )

    def get_config(self, key):
        return self._settings[key]


class _FakePgrepRunner:
    def list_polybar_pids(self):
        return (4321,)


class TestCompositeStateProbe(unittest.TestCase):
    def test_assembles_full_state(self):
        probe = CompositeStateProbe(
            xrandr=XrandrProbe(runner=_FakeXrandrRunner()),
            bspwm=BspwmProbe(runner=_FakeBspcRunner()),
            polybar=PolybarProbe(runner=_FakePgrepRunner()),
        )
        state = probe.read()

        self.assertEqual(len(state.outputs), 1)
        self.assertEqual(state.outputs[0].name, "eDP-1")
        self.assertTrue(state.outputs[0].primary)

        self.assertEqual(len(state.bspwm_monitors), 1)
        self.assertEqual(state.bspwm_monitors[0].name, "eDP-1")
        self.assertEqual(len(state.bspwm_monitors[0].desktops), 2)

        self.assertEqual(state.bspwm_settings, BspwmSettings())
        self.assertEqual(state.polybar_pids, (4321,))


if __name__ == "__main__":
    unittest.main()
