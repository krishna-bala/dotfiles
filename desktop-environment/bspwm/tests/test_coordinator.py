"""Tests for coordinator service."""

import unittest
from pathlib import Path

from lib.coordinator import MonitorManagerCoordinator, ResolvedProfile, PlanResult
from lib.display import DisplayService, Monitor
from lib.profile import ProfileService
from lib.exceptions import ProfileNotFoundError, ProfileValidationError


class MockXrandrExecutor:
    """Mock xrandr executor for testing."""

    def __init__(self, props_output: str):
        self.props_output = props_output
        self.executed_commands = []

    def get_props_output(self) -> str:
        return self.props_output

    def execute_command(self, command: list[str]) -> None:
        self.executed_commands.append(command)


class TestCoordinator(unittest.TestCase):
    """Test MonitorManagerCoordinator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Load fixture for personal-solo
        fixtures_dir = Path(__file__).parent / "fixtures/xrandr"
        with open(fixtures_dir / "personal-solo-props.txt") as f:
            self.personal_solo_props = f.read()

        # Create services with mocked xrandr
        mock_executor = MockXrandrExecutor(self.personal_solo_props)
        display_service = DisplayService(executor=mock_executor)
        profile_service = ProfileService(Path(__file__).parent / "fixtures" / "profiles")

        self.coordinator = MonitorManagerCoordinator(
            display_service=display_service,
            profile_service=profile_service,
        )

    def test_resolve_profile_personal_solo(self):
        """Test resolving personal-solo profile."""
        resolved = self.coordinator.resolve_profile("personal-solo")

        # Check types
        self.assertIsInstance(resolved, ResolvedProfile)
        self.assertIsInstance(resolved.monitors, list)
        self.assertIsInstance(resolved.alias_to_output, dict)
        self.assertIsInstance(resolved.display_configs, list)

        # Check laptop was resolved
        self.assertIn("laptop", resolved.alias_to_output)
        self.assertEqual(resolved.alias_to_output["laptop"], "eDP-1")

        # Check display config was created
        self.assertEqual(len(resolved.display_configs), 1)
        self.assertEqual(resolved.display_configs[0].output, "eDP-1")

    def test_resolve_laptop_by_edid_when_output_name_differs(self):
        """Laptop alias resolves via EDID when the panel name differs across
        machines (eDP-1 vs eDP-1-1), matching profile selection behavior.
        Renaming the output breaks the name fallback, so resolution can only
        succeed through the EDID map."""
        props = self.personal_solo_props.replace("eDP-1", "eDP-1-1")
        display_service = DisplayService(executor=MockXrandrExecutor(props))
        profile_service = ProfileService(Path(__file__).parent / "fixtures" / "profiles")

        # Guard the invariant this test depends on: the fixture profile's
        # laptop pin must equal the hash of the xrandr fixture's synthetic
        # EDID. If this fires, someone changed one fixture without the other.
        fixture_edid = next(
            m.edid for m in display_service.detect_monitors() if m.output == "eDP-1-1"
        )
        self.assertEqual(
            profile_service.load_profile("personal-solo").laptop.edid,
            fixture_edid,
            "fixtures/profiles/personal-solo.yaml laptop edid must equal the "
            "hash of the EDID in fixtures/xrandr/personal-solo-props.txt",
        )

        coordinator = MonitorManagerCoordinator(
            display_service=display_service,
            profile_service=profile_service,
        )

        resolved = coordinator.resolve_profile("personal-solo")

        self.assertEqual(resolved.alias_to_output["laptop"], "eDP-1-1")

    def test_resolve_nonexistent_profile(self):
        """Test resolving a profile that doesn't exist."""
        with self.assertRaises(ProfileNotFoundError):
            self.coordinator.resolve_profile("nonexistent")

    def test_plan_personal_solo(self):
        """Test planning personal-solo profile."""
        plan = self.coordinator.plan("personal-solo")

        # Check types
        self.assertIsInstance(plan, PlanResult)
        self.assertIsInstance(plan.resolved, ResolvedProfile)

        # Check validation passed
        self.assertTrue(plan.validation.is_valid)

        # Check profile was resolved
        self.assertIn("laptop", plan.resolved.alias_to_output)

    def test_resolve_profile_with_missing_monitors(self):
        """Test resolving a profile when required monitors are missing."""
        # Create a temporary profile that requires external monitors
        # This will fail because personal-solo fixture only has laptop
        # We would need a dual-monitor profile to test this properly
        # For now, this is a placeholder showing the pattern
        pass


if __name__ == "__main__":
    unittest.main()
