"""Tests for the Reconciler.

Includes the regression test for the personal-home → personal-solo unplug
bug — the case where bspwm holds zombie monitors with windows on them and
the existing reset-desktops path scrambled the result.
"""

import unittest
from pathlib import Path

from lib.ops import (
    BspcMonitorRemove,
    BspcWindowMoveToDesktop,
    PolybarLaunch,
    XrandrApply,
    XrandrApplyLayout,
    XrandrOff,
)


def _layouts(plan):
    return [op for op in plan.ops if isinstance(op, XrandrApplyLayout)]


def _applies(plan):
    return [a for op in _layouts(plan) for a in op.applies]


def _offs(plan):
    return [o for op in _layouts(plan) for o in op.offs]
from lib.plan import SquashToFirst
from lib.profile import ProfileService
from lib.reconciler import Reconciler
from lib.simulate import default_mint, simulate
from lib.state.desired import compile_desired
from lib.state.hardware import (
    BspwmDesktop,
    BspwmMonitor,
    BspwmSettings,
    HardwareState,
    XrandrOutput,
)

PROFILES_DIR = Path(__file__).parent.parent / "profiles"


def _personal_solo():
    return compile_desired(
        ProfileService(PROFILES_DIR).load_profile("personal-solo"),
        alias_to_output={"laptop": "eDP-1"},
    )


def _replay(state: HardwareState, plan):
    """Apply each op of `plan` to `state` and return the final state."""
    mint = default_mint()
    for op in plan.ops:
        state = simulate(state, op, mint)
    return state


class TestReconcileNoChange(unittest.TestCase):
    """Already-in-state should produce a no-op-ish plan (only polybar restart)."""

    def test_personal_solo_already_applied(self):
        # Hardware state matches personal-solo exactly
        state = HardwareState(
            outputs=(
                XrandrOutput(
                    name="eDP-1",
                    connected=True,
                    active_mode="1920x1200",
                    position=(0, 0),
                    primary=True,
                ),
            ),
            bspwm_monitors=(
                BspwmMonitor(
                    id="0xA",
                    name="eDP-1",
                    desktops=tuple(
                        BspwmDesktop(id=f"0xA{i}", name=str(i)) for i in range(1, 11)
                    ),
                ),
            ),
            bspwm_settings=BspwmSettings(),
            polybar_pids=(),  # no polybar yet — first launch
        )
        plan = Reconciler().plan(state, _personal_solo())
        kinds = {type(op).__name__ for op in plan.ops}
        self.assertNotIn("XrandrApplyLayout", kinds)
        self.assertNotIn("BspcDesktopAdd", kinds)
        self.assertNotIn("BspcDesktopRename", kinds)
        self.assertNotIn("BspcMonitorRemove", kinds)
        # Only polybar is left
        self.assertEqual(kinds, {"PolybarLaunch"})


class TestReconcileColdStart(unittest.TestCase):
    """eDP-1 connected but inactive, bspwm empty — typical first-boot state."""

    def test_personal_solo_from_cold_state(self):
        state = HardwareState(
            outputs=(XrandrOutput(name="eDP-1", connected=True),),
        )
        plan = Reconciler().plan(state, _personal_solo())
        kinds = [type(op).__name__ for op in plan.ops]

        # Order: xrandr → wait → reconcile desktops → settings → polybar
        self.assertEqual(kinds.index("XrandrApplyLayout"), 0)
        self.assertIn("WaitForBspwmMonitor", kinds)
        self.assertEqual(kinds.count("WaitForBspwmMonitor"), 1)
        # Simulator predicts no default desktops — 10 adds, no renames.
        self.assertEqual(kinds.count("BspcDesktopRename"), 0)
        self.assertEqual(kinds.count("BspcDesktopAdd"), 10)
        # No moves, no removes, no monitor cleanup
        self.assertEqual(kinds.count("BspcWindowMoveToDesktop"), 0)
        self.assertEqual(kinds.count("BspcMonitorRemove"), 0)


class TestReconcileUnplugRegression(unittest.TestCase):
    """The bug. bspwm holds DP-2 + DP-3 with 20 windows; xrandr shows only
    eDP-1 connected (inactive). Trigger personal-solo. The fix: every window
    moves to a real eDP-1 desktop, all stale state is cleaned up, no
    reset-desktops anywhere."""

    def setUp(self):
        # 10 windows on DP-2 desktops 11..20 (one each), 10 on DP-3 desktops 1..10
        dp2_desktops = tuple(
            BspwmDesktop(
                id=f"0xA{i:X}", name=str(10 + i), window_ids=(f"w{10 + i}",)
            )
            for i in range(1, 11)
        )
        dp3_desktops = tuple(
            BspwmDesktop(id=f"0xB{i:X}", name=str(i), window_ids=(f"v{i}",))
            for i in range(1, 11)
        )
        self.current = HardwareState(
            outputs=(
                XrandrOutput(name="eDP-1", connected=True),  # connected, inactive
                XrandrOutput(name="DP-2", connected=False),
                XrandrOutput(name="DP-3", connected=False),
            ),
            bspwm_monitors=(
                BspwmMonitor(id="0xA0", name="DP-2", desktops=dp2_desktops),
                BspwmMonitor(id="0xB0", name="DP-3", desktops=dp3_desktops),
            ),
        )
        self.desired = _personal_solo()
        self.plan = Reconciler().plan(self.current, self.desired)

    def test_xrandr_enables_edp_first(self):
        first = self.plan.ops[0]
        self.assertIsInstance(first, XrandrApplyLayout)
        apply = first.applies[0]
        self.assertEqual(apply.output, "eDP-1")
        self.assertEqual(apply.mode, "1920x1200")
        self.assertTrue(apply.primary)

    def test_no_reset_desktops_op_exists_in_vocabulary(self):
        # Sanity: the destructive op type isn't in our Op union by construction.
        # If someone adds it later, this test fails before the bug returns.
        from lib import ops as ops_module

        self.assertFalse(hasattr(ops_module, "BspcDesktopReset"))

    def test_every_window_appears_in_exactly_one_move(self):
        moves = [
            op for op in self.plan.ops if isinstance(op, BspcWindowMoveToDesktop)
        ]
        moved_ids = [op.window_id for op in moves]
        expected = {f"w{i}" for i in range(11, 21)} | {f"v{i}" for i in range(1, 11)}
        self.assertEqual(set(moved_ids), expected)
        # Each window moves exactly once
        self.assertEqual(len(moved_ids), len(set(moved_ids)))

    def test_dp3_windows_route_to_same_named_edp_desktop(self):
        """PreserveByName: DP-3:5 (named '5') → eDP-1:5 (named '5')."""
        # We don't know eDP-1's desktop ids upfront, but we can replay the plan
        # and check final placement.
        final = _replay(self.current, self.plan)
        # eDP-1 is the only surviving monitor
        self.assertEqual(len(final.bspwm_monitors), 1)
        edp = final.bspwm_monitors[0]
        # Desktops named exactly 1..10
        names = [d.name for d in edp.desktops]
        self.assertEqual(names, ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        # Each v_i should be on desktop named str(i)
        windows_by_desktop_name = {d.name: set(d.window_ids) for d in edp.desktops}
        for i in range(1, 11):
            self.assertIn(
                f"v{i}",
                windows_by_desktop_name[str(i)],
                f"v{i} should be on desktop '{i}' but was on "
                f"{[name for name, w in windows_by_desktop_name.items() if f'v{i}' in w]}",
            )

    def test_dp2_overflow_lands_on_first_target_under_preserve_by_name(self):
        """PreserveByName falls back to first target when name doesn't match.
        DP-2 had desktops 11..20, none of which exist on eDP-1 (1..10), so all
        their windows land on '1'."""
        final = _replay(self.current, self.plan)
        edp = final.bspwm_monitors[0]
        d1 = next(d for d in edp.desktops if d.name == "1")
        for i in range(11, 21):
            self.assertIn(f"w{i}", d1.window_ids)

    def test_dp2_and_dp3_monitors_are_removed(self):
        removes = [op for op in self.plan.ops if isinstance(op, BspcMonitorRemove)]
        self.assertEqual(len(removes), 2)

    def test_no_monitor_remove_for_surviving_edp(self):
        for op in self.plan.ops:
            if isinstance(op, BspcMonitorRemove):
                # All the original ids that get removed must be the stale ones
                self.assertIn(op.monitor_id, {"0xA0", "0xB0"})

    def test_xrandr_off_emitted_for_active_outputs_not_in_profile(self):
        # In this scenario DP-2 and DP-3 aren't active in xrandr (already
        # disconnected), so we expect zero XrandrOff ops.
        self.assertEqual(_offs(self.plan), [])

    def test_polybar_is_relaunched(self):
        kinds = [type(op).__name__ for op in self.plan.ops]
        self.assertEqual(kinds.count("PolybarLaunch"), 1)
        launches = [op for op in self.plan.ops if isinstance(op, PolybarLaunch)]
        self.assertEqual(launches[0].output, "eDP-1")

    def test_final_state_matches_desired_topology(self):
        """High-level: replay the plan, the final state must look like
        personal-solo."""
        final = _replay(self.current, self.plan)
        # Only eDP-1 in bspwm
        self.assertEqual([m.name for m in final.bspwm_monitors], ["eDP-1"])
        # Desktops 1..10
        edp = final.bspwm_monitors[0]
        self.assertEqual(
            [d.name for d in edp.desktops],
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        )
        # All 20 original windows ended up on eDP-1
        all_windows = {w for d in edp.desktops for w in d.window_ids}
        expected = {f"w{i}" for i in range(11, 21)} | {f"v{i}" for i in range(1, 11)}
        self.assertEqual(all_windows, expected)


class TestReconcileWithExplicitXrandrOff(unittest.TestCase):
    """Currently-active output that the profile doesn't enable → XrandrOff."""

    def test_explicitly_disables_unwanted_active_output(self):
        current = HardwareState(
            outputs=(
                XrandrOutput(name="eDP-1", connected=True),
                XrandrOutput(
                    name="DP-2",
                    connected=True,
                    active_mode="3840x2160",
                    position=(0, 0),
                ),
            ),
        )
        plan = Reconciler().plan(current, _personal_solo())
        self.assertEqual([op.output for op in _offs(plan)], ["DP-2"])


class TestReconcileWithSquashPolicy(unittest.TestCase):
    """Same scenario as the regression but with SquashToFirst — verifies the
    policy actually swaps cleanly without reconciler changes."""

    def test_all_windows_pile_on_first_target(self):
        dp3_desktops = tuple(
            BspwmDesktop(id=f"0xB{i:X}", name=str(i), window_ids=(f"v{i}",))
            for i in range(1, 11)
        )
        current = HardwareState(
            outputs=(XrandrOutput(name="eDP-1", connected=True),),
            bspwm_monitors=(
                BspwmMonitor(id="0xB0", name="DP-3", desktops=dp3_desktops),
            ),
        )
        plan = Reconciler().plan(
            current, _personal_solo(), merge_policy=SquashToFirst()
        )
        final = _replay(current, plan)
        edp = final.bspwm_monitors[0]
        d1 = next(d for d in edp.desktops if d.name == "1")
        # All v_i squashed onto desktop "1"
        for i in range(1, 11):
            self.assertIn(f"v{i}", d1.window_ids)


class TestReconcileSettings(unittest.TestCase):
    def test_no_op_when_settings_match(self):
        current = HardwareState(
            outputs=(
                XrandrOutput(
                    name="eDP-1",
                    connected=True,
                    active_mode="1920x1200",
                    position=(0, 0),
                    primary=True,
                ),
            ),
            bspwm_monitors=(
                BspwmMonitor(
                    id="0xA",
                    name="eDP-1",
                    desktops=tuple(
                        BspwmDesktop(id=f"0xA{i}", name=str(i)) for i in range(1, 11)
                    ),
                ),
            ),
            bspwm_settings=BspwmSettings(),  # matches profile defaults
        )
        plan = Reconciler().plan(current, _personal_solo())
        configs = [op for op in plan.ops if type(op).__name__ == "BspcConfig"]
        self.assertEqual(configs, [])

    def test_emits_diff_when_settings_differ(self):
        current = HardwareState(
            outputs=(
                XrandrOutput(
                    name="eDP-1",
                    connected=True,
                    active_mode="1920x1200",
                    position=(0, 0),
                    primary=True,
                ),
            ),
            bspwm_monitors=(
                BspwmMonitor(
                    id="0xA",
                    name="eDP-1",
                    desktops=tuple(
                        BspwmDesktop(id=f"0xA{i}", name=str(i)) for i in range(1, 11)
                    ),
                ),
            ),
            bspwm_settings=BspwmSettings(
                border_width=1, window_gap=1, focused_border_color="#000000"
            ),
        )
        plan = Reconciler().plan(current, _personal_solo())
        config_keys = {
            op.key for op in plan.ops if type(op).__name__ == "BspcConfig"
        }
        self.assertEqual(
            config_keys,
            {"border_width", "window_gap", "focused_border_color"},
        )


class TestReconcileMergePolicyDefault(unittest.TestCase):
    def test_default_policy_is_preserve_by_name(self):
        # Verifying via behaviour: a window on a stale desktop named "5"
        # routes to a desktop named "5" on the surviving monitor when both
        # exist, even without specifying a policy.
        current = HardwareState(
            outputs=(XrandrOutput(name="eDP-1", connected=True),),
            bspwm_monitors=(
                BspwmMonitor(
                    id="0xA",
                    name="DP-2",
                    desktops=(
                        BspwmDesktop(id="0xA1", name="5", window_ids=("w1",)),
                    ),
                ),
            ),
        )
        plan = Reconciler().plan(current, _personal_solo())
        final = _replay(current, plan)
        d5 = next(
            d for d in final.bspwm_monitors[0].desktops if d.name == "5"
        )
        self.assertIn("w1", d5.window_ids)


if __name__ == "__main__":
    unittest.main()


class TestReconcileFramebuffer(unittest.TestCase):
    """All xrandr changes must land in ONE XrandrApplyLayout op carrying the
    final layout's --fb. Sequential per-output calls wedge the modesetting
    driver: a screen resize fails with RRSetScreenSize BadMatch once any CRTC
    has a scale transform active (regression: personal-home dock, 2026-06-11).
    """

    def _personal_home(self):
        return compile_desired(
            ProfileService(PROFILES_DIR).load_profile("personal-home"),
            alias_to_output={"laptop": "eDP-1", "vertical": "DP-2", "main": "DP-3"},
        )

    def test_dock_emits_single_layout_op_with_final_fb(self):
        # Laptop-only reality, docking into personal-home (DP-2 rotated+scaled
        # 4K at 0,0 → 1296x2304; DP-3 2560x1440 at 1296,432 → 3856x1872).
        state = HardwareState(
            outputs=(
                XrandrOutput(
                    name="eDP-1",
                    connected=True,
                    active_mode="1920x1200",
                    position=(0, 0),
                    primary=True,
                ),
                XrandrOutput(name="DP-2", connected=True),
                XrandrOutput(name="DP-3", connected=True),
            ),
            bspwm_monitors=(
                BspwmMonitor(
                    id="0x00200002",
                    name="eDP-1",
                    desktops=tuple(
                        BspwmDesktop(id=f"0x0020000{i}", name=str(i))
                        for i in range(1, 6)
                    ),
                ),
            ),
        )
        plan = Reconciler().plan(state, self._personal_home())

        layouts = _layouts(plan)
        self.assertEqual(len(layouts), 1)
        layout = layouts[0]
        self.assertEqual(len(layout.applies), 2)
        self.assertEqual([o.output for o in layout.offs], ["eDP-1"])
        # Final layout extent: max(1296x2304, 3856x1872)
        self.assertEqual(layout.fb, (3856, 2304))
        # The layout op leads the plan, before any wait/bspc op
        self.assertIs(plan.ops[0], layout)

    def test_undock_emits_single_layout_op_with_shrunk_fb(self):
        # Docked reality (wide layout), going to laptop-only personal-solo:
        # one invocation turns DP-3 off, applies eDP-1, and shrinks --fb to
        # the laptop-only extent.
        state = HardwareState(
            outputs=(
                XrandrOutput(
                    name="eDP-1",
                    connected=True,
                    active_mode="1920x1200",
                    position=(0, 0),
                ),
                XrandrOutput(
                    name="DP-3",
                    connected=False,
                    active_mode="2560x1440",
                    position=(1296, 432),
                    primary=True,
                ),
            ),
            bspwm_monitors=(
                BspwmMonitor(
                    id="0x00200002",
                    name="eDP-1",
                    desktops=tuple(
                        BspwmDesktop(id=f"0x0020000{i}", name=str(i))
                        for i in range(1, 11)
                    ),
                ),
            ),
        )
        plan = Reconciler().plan(state, _personal_solo())

        layouts = _layouts(plan)
        self.assertEqual(len(layouts), 1)
        layout = layouts[0]
        self.assertEqual([a.output for a in layout.applies], ["eDP-1"])
        self.assertEqual([o.output for o in layout.offs], ["DP-3"])
        self.assertEqual(layout.fb, (1920, 1200))

    def test_no_layout_op_when_xrandr_already_matches(self):
        state = HardwareState(
            outputs=(
                XrandrOutput(
                    name="eDP-1",
                    connected=True,
                    active_mode="1920x1200",
                    position=(0, 0),
                    primary=True,
                ),
            ),
            bspwm_monitors=(
                BspwmMonitor(
                    id="0x00200002",
                    name="eDP-1",
                    desktops=tuple(
                        BspwmDesktop(id=f"0x0020000{i:X}", name=str(i))
                        for i in range(1, 11)
                    ),
                ),
            ),
        )
        plan = Reconciler().plan(state, _personal_solo())
        self.assertEqual(_layouts(plan), [])
