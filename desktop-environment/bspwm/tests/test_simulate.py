"""Tests for the pure simulate(state, op) transition function."""

import unittest

from lib.ops import (
    BspcConfig,
    BspcDesktopAdd,
    BspcDesktopRemove,
    BspcDesktopRename,
    BspcMonitorRemove,
    BspcWindowMoveToDesktop,
    PolybarKillAll,
    PolybarLaunch,
    WaitForBspwmMonitor,
    XrandrApply,
    XrandrOff,
)
from lib.simulate import default_mint, simulate
from lib.state.hardware import (
    BspwmDesktop,
    BspwmMonitor,
    BspwmSettings,
    HardwareState,
    XrandrOutput,
)


def _state_with_two_outputs():
    return HardwareState(
        outputs=(
            XrandrOutput(name="eDP-1", connected=True),
            XrandrOutput(
                name="DP-2",
                connected=True,
                active_mode="3840x2160",
                position=(0, 0),
                primary=True,
            ),
        )
    )


class TestSimulateXrandr(unittest.TestCase):
    def test_apply_activates_inactive_output(self):
        state = _state_with_two_outputs()
        op = XrandrApply("eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True)
        new_state = simulate(state, op, default_mint())
        edp = next(o for o in new_state.outputs if o.name == "eDP-1")
        self.assertEqual(edp.active_mode, "1920x1200")
        self.assertEqual(edp.position, (0, 0))
        self.assertTrue(edp.primary)

    def test_apply_primary_clears_other_primaries(self):
        state = _state_with_two_outputs()
        op = XrandrApply("eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True)
        new_state = simulate(state, op, default_mint())
        dp2 = next(o for o in new_state.outputs if o.name == "DP-2")
        self.assertFalse(dp2.primary)

    def test_apply_creates_unknown_output(self):
        state = HardwareState()
        op = XrandrApply("eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True)
        new_state = simulate(state, op, default_mint())
        self.assertEqual(len(new_state.outputs), 1)
        self.assertEqual(new_state.outputs[0].name, "eDP-1")
        self.assertTrue(new_state.outputs[0].connected)

    def test_off_clears_active_state(self):
        state = _state_with_two_outputs()
        new_state = simulate(state, XrandrOff("DP-2"), default_mint())
        dp2 = next(o for o in new_state.outputs if o.name == "DP-2")
        self.assertIsNone(dp2.active_mode)
        self.assertIsNone(dp2.position)
        self.assertFalse(dp2.primary)


class TestSimulateBspwm(unittest.TestCase):
    def test_wait_adds_bare_monitor(self):
        state = HardwareState()
        new_state = simulate(state, WaitForBspwmMonitor("eDP-1"), default_mint())
        self.assertEqual(len(new_state.bspwm_monitors), 1)
        m = new_state.bspwm_monitors[0]
        self.assertEqual(m.name, "eDP-1")
        # Predicts no default desktops — executor handles real bspwm's defaults.
        self.assertEqual(m.desktops, ())
        self.assertTrue(m.id.startswith("$M_"))

    def test_wait_idempotent_when_monitor_exists(self):
        state = HardwareState(
            bspwm_monitors=(BspwmMonitor(id="0xA", name="eDP-1"),)
        )
        new_state = simulate(state, WaitForBspwmMonitor("eDP-1"), default_mint())
        self.assertEqual(state, new_state)

    def test_desktop_add_appends_to_target_monitor(self):
        state = HardwareState(
            bspwm_monitors=(
                BspwmMonitor(id="0xA", name="eDP-1", desktops=()),
                BspwmMonitor(id="0xB", name="DP-2", desktops=()),
            )
        )
        new_state = simulate(
            state, BspcDesktopAdd(monitor_id="0xA", desktop_name="1"), default_mint()
        )
        self.assertEqual(len(new_state.bspwm_monitors[0].desktops), 1)
        self.assertEqual(new_state.bspwm_monitors[0].desktops[0].name, "1")
        self.assertEqual(len(new_state.bspwm_monitors[1].desktops), 0)

    def test_desktop_rename(self):
        state = HardwareState(
            bspwm_monitors=(
                BspwmMonitor(
                    id="0xA",
                    name="eDP-1",
                    desktops=(BspwmDesktop(id="0xA1", name="Desktop"),),
                ),
            )
        )
        new_state = simulate(
            state, BspcDesktopRename(desktop_id="0xA1", new_name="1"), default_mint()
        )
        self.assertEqual(new_state.bspwm_monitors[0].desktops[0].name, "1")
        # Id is preserved
        self.assertEqual(new_state.bspwm_monitors[0].desktops[0].id, "0xA1")

    def test_desktop_remove(self):
        state = HardwareState(
            bspwm_monitors=(
                BspwmMonitor(
                    id="0xA",
                    name="eDP-1",
                    desktops=(
                        BspwmDesktop(id="0xA1", name="1"),
                        BspwmDesktop(id="0xA2", name="2"),
                    ),
                ),
            )
        )
        new_state = simulate(
            state, BspcDesktopRemove(desktop_id="0xA1"), default_mint()
        )
        names = [d.name for d in new_state.bspwm_monitors[0].desktops]
        self.assertEqual(names, ["2"])

    def test_window_move(self):
        state = HardwareState(
            bspwm_monitors=(
                BspwmMonitor(
                    id="0xA",
                    name="eDP-1",
                    desktops=(
                        BspwmDesktop(id="0xA1", name="1", window_ids=("w1", "w2")),
                        BspwmDesktop(id="0xA2", name="2", window_ids=()),
                    ),
                ),
            )
        )
        new_state = simulate(
            state,
            BspcWindowMoveToDesktop(window_id="w1", target_desktop_id="0xA2"),
            default_mint(),
        )
        d1, d2 = new_state.bspwm_monitors[0].desktops
        self.assertEqual(d1.window_ids, ("w2",))
        self.assertEqual(d2.window_ids, ("w1",))

    def test_window_move_across_monitors(self):
        state = HardwareState(
            bspwm_monitors=(
                BspwmMonitor(
                    id="0xA",
                    name="DP-2",
                    desktops=(BspwmDesktop(id="0xA1", name="11", window_ids=("w1",)),),
                ),
                BspwmMonitor(
                    id="0xB",
                    name="eDP-1",
                    desktops=(BspwmDesktop(id="0xB1", name="1", window_ids=()),),
                ),
            )
        )
        new_state = simulate(
            state,
            BspcWindowMoveToDesktop(window_id="w1", target_desktop_id="0xB1"),
            default_mint(),
        )
        self.assertEqual(new_state.bspwm_monitors[0].desktops[0].window_ids, ())
        self.assertEqual(new_state.bspwm_monitors[1].desktops[0].window_ids, ("w1",))

    def test_monitor_remove(self):
        state = HardwareState(
            bspwm_monitors=(
                BspwmMonitor(id="0xA", name="DP-2"),
                BspwmMonitor(id="0xB", name="eDP-1"),
            )
        )
        new_state = simulate(
            state, BspcMonitorRemove(monitor_id="0xA"), default_mint()
        )
        names = [m.name for m in new_state.bspwm_monitors]
        self.assertEqual(names, ["eDP-1"])


class TestSimulateConfig(unittest.TestCase):
    def test_border_width_int(self):
        state = HardwareState(bspwm_settings=BspwmSettings(border_width=7))
        new_state = simulate(
            state, BspcConfig(key="border_width", value="10"), default_mint()
        )
        self.assertEqual(new_state.bspwm_settings.border_width, 10)

    def test_split_ratio_float(self):
        state = HardwareState()
        new_state = simulate(
            state, BspcConfig(key="split_ratio", value="0.65"), default_mint()
        )
        self.assertEqual(new_state.bspwm_settings.split_ratio, 0.65)

    def test_borderless_monocle_bool(self):
        state = HardwareState()
        new_state = simulate(
            state, BspcConfig(key="borderless_monocle", value="true"), default_mint()
        )
        self.assertTrue(new_state.bspwm_settings.borderless_monocle)

    def test_color_string(self):
        state = HardwareState()
        new_state = simulate(
            state,
            BspcConfig(key="focused_border_color", value="#abcdef"),
            default_mint(),
        )
        self.assertEqual(new_state.bspwm_settings.focused_border_color, "#abcdef")

    def test_unknown_key_is_noop(self):
        state = HardwareState()
        new_state = simulate(
            state, BspcConfig(key="unknown_setting", value="x"), default_mint()
        )
        self.assertEqual(new_state, state)


class TestSimulatePolybar(unittest.TestCase):
    def test_kill_all_clears_pids(self):
        state = HardwareState(polybar_pids=(1234, 5678))
        new_state = simulate(state, PolybarKillAll(), default_mint())
        self.assertEqual(new_state.polybar_pids, ())

    def test_launch_appends_synthetic_pid(self):
        state = HardwareState()
        new_state = simulate(
            state, PolybarLaunch(output="eDP-1", bar_definition="main"), default_mint()
        )
        self.assertEqual(len(new_state.polybar_pids), 1)


class TestSimulateImmutability(unittest.TestCase):
    def test_input_state_is_not_mutated(self):
        original = HardwareState(
            outputs=(XrandrOutput(name="eDP-1", connected=True),)
        )
        simulate(
            original,
            XrandrApply("eDP-1", "1920x1200", (0, 0), "normal", (1.0, 1.0), True),
            default_mint(),
        )
        # Original is unchanged
        self.assertIsNone(original.outputs[0].active_mode)


class TestSimulateUnknownOp(unittest.TestCase):
    def test_unknown_op_raises(self):
        with self.assertRaises(ValueError):
            simulate(HardwareState(), object(), default_mint())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
