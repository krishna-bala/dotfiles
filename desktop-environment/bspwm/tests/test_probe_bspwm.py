"""Tests for bspwm probe."""

import json
import unittest
from pathlib import Path

from lib.probe.bspwm import BspwmProbe, _id_to_hex

FIXTURES = Path(__file__).parent / "fixtures" / "bspc"


class TestIdFormat(unittest.TestCase):
    def test_hex_format(self):
        self.assertEqual(_id_to_hex(2097158), "0x00200006")
        self.assertEqual(_id_to_hex(0xA1), "0x000000A1")


class TestParseDumpFromFixture(unittest.TestCase):
    """Real `bspc wm -d` output from the laptop in personal-solo state."""

    def setUp(self):
        text = (FIXTURES / "personal-solo-dump.json").read_text()
        self.monitors = BspwmProbe.parse_dump(text)

    def test_one_monitor_named_edp1(self):
        self.assertEqual(len(self.monitors), 1)
        self.assertEqual(self.monitors[0].name, "eDP-1")

    def test_monitor_id_is_hex(self):
        self.assertTrue(self.monitors[0].id.startswith("0x"))
        # Same id we observed when capturing the fixture
        self.assertEqual(self.monitors[0].id, "0x00200006")

    def test_ten_desktops_named_1_to_10(self):
        names = [d.name for d in self.monitors[0].desktops]
        self.assertEqual(names, ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])

    def test_each_desktop_has_distinct_hex_id(self):
        ids = [d.id for d in self.monitors[0].desktops]
        self.assertEqual(len(set(ids)), len(ids))
        for did in ids:
            self.assertTrue(did.startswith("0x"))

    def test_window_ids_collected_from_node_tree(self):
        # The fixture has windows on the first three desktops.
        ws_with_windows = [
            d for d in self.monitors[0].desktops if len(d.window_ids) > 0
        ]
        self.assertGreater(len(ws_with_windows), 0)
        # All window ids should be hex strings
        for d in ws_with_windows:
            for wid in d.window_ids:
                self.assertTrue(wid.startswith("0x"), f"{wid} is not hex")


class TestParseDumpSynthetic(unittest.TestCase):
    def test_two_monitors_with_distinct_ids(self):
        dump = json.dumps(
            {
                "monitors": [
                    {
                        "id": 0xA0,
                        "name": "DP-2",
                        "desktops": [
                            {"id": 0xA1, "name": "11", "root": None},
                            {"id": 0xA2, "name": "12", "root": None},
                        ],
                    },
                    {
                        "id": 0xB0,
                        "name": "DP-3",
                        "desktops": [
                            {"id": 0xB1, "name": "1", "root": None},
                        ],
                    },
                ]
            }
        )
        monitors = BspwmProbe.parse_dump(dump)
        self.assertEqual(len(monitors), 2)
        self.assertEqual([m.name for m in monitors], ["DP-2", "DP-3"])
        self.assertEqual(monitors[0].id, "0x000000A0")
        self.assertEqual(monitors[1].desktops[0].name, "1")

    def test_window_ids_walk_recursive_tree(self):
        # Tree: root has two children, each with a client. Plus a deeper grandchild.
        leaf = {
            "id": 0x10,
            "client": {"className": "kitty"},
            "firstChild": None,
            "secondChild": None,
        }
        deep_leaf = {
            "id": 0x20,
            "client": {"className": "firefox"},
            "firstChild": None,
            "secondChild": None,
        }
        right = {
            "id": 0x30,
            "client": None,
            "firstChild": deep_leaf,
            "secondChild": None,
        }
        root = {"id": 0x40, "client": None, "firstChild": leaf, "secondChild": right}
        dump = json.dumps(
            {
                "monitors": [
                    {
                        "id": 0x100,
                        "name": "eDP-1",
                        "desktops": [{"id": 0x101, "name": "1", "root": root}],
                    }
                ]
            }
        )
        monitors = BspwmProbe.parse_dump(dump)
        wids = monitors[0].desktops[0].window_ids
        # The two leafs with non-null client should be collected.
        # Internal nodes (root, right) have client=None and contribute nothing.
        self.assertEqual(set(wids), {"0x00000010", "0x00000020"})

    def test_empty_dump(self):
        self.assertEqual(BspwmProbe.parse_dump('{"monitors": []}'), ())

    def test_desktop_with_null_root_has_empty_window_ids(self):
        dump = json.dumps(
            {
                "monitors": [
                    {
                        "id": 1,
                        "name": "eDP-1",
                        "desktops": [{"id": 2, "name": "1", "root": None}],
                    }
                ]
            }
        )
        monitors = BspwmProbe.parse_dump(dump)
        self.assertEqual(monitors[0].desktops[0].window_ids, ())


class TestReadSettings(unittest.TestCase):
    def test_reads_each_setting_from_runner(self):
        class FakeRunner:
            def __init__(self):
                self.values = {
                    "border_width": "10",
                    "window_gap": "20",
                    "focused_border_color": "#abcdef",
                    "normal_border_color": "#123456",
                    "split_ratio": "0.6",
                    "borderless_monocle": "true",
                    "gapless_monocle": "false",
                }

            def dump_state(self):
                return '{"monitors": []}'

            def get_config(self, key):
                return self.values[key]

        s = BspwmProbe(runner=FakeRunner()).read_settings()
        self.assertEqual(s.border_width, 10)
        self.assertEqual(s.window_gap, 20)
        self.assertEqual(s.focused_border_color, "#abcdef")
        self.assertEqual(s.normal_border_color, "#123456")
        self.assertEqual(s.split_ratio, 0.6)
        self.assertTrue(s.borderless_monocle)
        self.assertFalse(s.gapless_monocle)

    def test_unknown_key_falls_back_to_default(self):
        class FailingRunner:
            def dump_state(self):
                return '{"monitors": []}'

            def get_config(self, key):
                raise RuntimeError("bspc: unknown setting")

        s = BspwmProbe(runner=FailingRunner()).read_settings()
        # Fallback to BspwmSettings() defaults
        self.assertEqual(s.border_width, 7)
        self.assertEqual(s.window_gap, 15)


if __name__ == "__main__":
    unittest.main()
