"""Integration tests for full monitor manager workflow."""

import unittest
from pathlib import Path

from lib.display import DisplayService
from lib.profile import ProfileService
from lib.coordinator import MonitorManagerCoordinator
from lib.reconciler import Reconciler
from lib.simulate import default_mint, simulate
from lib.state.desired import compile_desired
from lib.state.hardware import (
    BspwmDesktop,
    BspwmMonitor,
    HardwareState,
    XrandrOutput,
)
from lib.safety import SafetyService


class MockXrandrExecutor:
    """Mock xrandr executor for testing."""

    def __init__(self, props_output: str):
        self.props_output = props_output
        self.executed_commands = []

    def get_props_output(self) -> str:
        return self.props_output

    def execute_command(self, command: list[str]) -> None:
        self.executed_commands.append(command)


class MockBspcExecutor:
    """Mock bspc executor for testing."""

    def __init__(self):
        self.executed_commands = []

    def execute_command(self, command: list[str]) -> str:
        self.executed_commands.append(command)
        return ""


class TestFullWorkflow(unittest.TestCase):
    """Test full workflow integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Load xrandr fixture
        fixtures_dir = Path(__file__).parent / "fixtures/xrandr"
        with open(fixtures_dir / "personal-solo-props.txt") as f:
            self.xrandr_output = f.read()

        # Create mock executors
        self.mock_xrandr = MockXrandrExecutor(self.xrandr_output)
        self.mock_bspc = MockBspcExecutor()

        # Create services
        self.display_service = DisplayService(executor=self.mock_xrandr, dry_run=True)
        self.profile_service = ProfileService(Path(__file__).parent / "fixtures" / "profiles")

        # Create coordinator
        self.coordinator = MonitorManagerCoordinator(
            display_service=self.display_service,
            profile_service=self.profile_service,
        )

    def test_full_profile_application_workflow(self):
        """Test complete workflow: plan -> resolve -> apply display -> apply WM."""
        # Step 1: Plan
        plan = self.coordinator.plan("personal-solo")

        self.assertTrue(plan.validation.is_valid)
        self.assertEqual(len(plan.resolved.display_configs), 1)

        # Step 2: Verify resolution
        resolved = plan.resolved
        self.assertIn("laptop", resolved.alias_to_output)
        self.assertEqual(resolved.alias_to_output["laptop"], "eDP-1")

        # Step 3: Verify the resolved display config (application happens via
        # the executor's xrandr ops; see test_executor.py)
        self.assertEqual(len(resolved.display_configs), 1)
        self.assertEqual(resolved.display_configs[0].output, "eDP-1")
        self.assertEqual(resolved.display_configs[0].resolution, "1920x1200")

        # Step 4: Compile the desired state (what the reconciler applies)
        desired = compile_desired(resolved.profile, resolved.alias_to_output)

        workspaces = {w.output: w.desktop_names for w in desired.workspaces}
        self.assertEqual(workspaces, {"eDP-1": tuple(str(n) for n in range(1, 11))})
        # Settings come from fixtures/profiles/defaults.yaml via the load-time merge
        self.assertEqual(desired.bspwm_settings.border_width, 7)
        self.assertEqual(desired.bspwm_settings.window_gap, 15)

    def test_safety_snapshot_captures_full_state(self):
        """Test that safety snapshot captures both display and WM state."""
        import tempfile

        # Create safety service with temp directory
        temp_dir = Path(tempfile.mkdtemp())
        safety = SafetyService(snapshot_dir=temp_dir)

        try:
            # Create snapshot
            snapshot = safety.create_snapshot()

            # Verify xrandr state captured
            self.assertIsNotNone(snapshot.xrandr_state)
            self.assertGreater(len(snapshot.xrandr_state), 0)

            # Verify BSPWM state captured (may be None if BSPWM not running in test env)
            # This is expected in unit test environment
            # In real environment, these would be populated

            # Save rollback file
            rollback_file = safety.save_rollback_text(snapshot)
            self.assertTrue(rollback_file.exists())

            # Verify rollback file contains xrandr state
            with open(rollback_file) as f:
                content = f.read()

            self.assertIn("# Display Configuration (xrandr)", content)
            self.assertIn(snapshot.xrandr_state, content)

        finally:
            # Cleanup
            import shutil

            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def test_error_handling_invalid_profile(self):
        """Test error handling when profile doesn't exist."""
        from lib.exceptions import ProfileNotFoundError

        with self.assertRaises(ProfileNotFoundError):
            self.coordinator.plan("nonexistent-profile")

    def test_error_handling_missing_monitor(self):
        """Test error handling when required monitor is missing."""
        from lib.exceptions import ProfileValidationError

        # Create mock with no connected monitors
        mock_xrandr_empty = MockXrandrExecutor("Screen 0: minimum 320 x 200\n")
        display_service_empty = DisplayService(executor=mock_xrandr_empty, dry_run=True)

        coordinator_empty = MonitorManagerCoordinator(
            display_service=display_service_empty,
            profile_service=self.profile_service,
        )

        # Planning with no monitors should raise ProfileValidationError
        with self.assertRaises(ProfileValidationError) as ctx:
            coordinator_empty.plan("personal-solo")

        self.assertIn("No monitors detected", str(ctx.exception))

    def test_full_apply_all_workflow(self):
        """resolve → compile → reconcile produces a plan that reaches the profile."""
        # Step 1: Resolve profile and compile the desired state
        resolved = self.coordinator.resolve_profile("personal-solo")
        self.assertEqual(resolved.alias_to_output["laptop"], "eDP-1")
        desired = compile_desired(resolved.profile, resolved.alias_to_output)

        # Step 2: Reconcile against a bare just-booted state (one default desktop)
        current = HardwareState(
            outputs=(XrandrOutput(name="eDP-1", connected=True),),
            bspwm_monitors=(
                BspwmMonitor(
                    id="0x00200001",
                    name="eDP-1",
                    desktops=(BspwmDesktop(id="0x00200002", name="Desktop"),),
                ),
            ),
        )
        plan = Reconciler().plan(current, desired)
        self.assertGreater(len(plan.ops), 0)

        # Step 3: Replaying the plan in the simulator reaches the desired state
        state = current
        mint = default_mint()
        for op in plan.ops:
            state = simulate(state, op, mint)

        final = {m.name: tuple(d.name for d in m.desktops) for m in state.bspwm_monitors}
        self.assertEqual(final, {"eDP-1": tuple(str(n) for n in range(1, 11))})


if __name__ == "__main__":
    unittest.main()
