"""Integration tests for CLI commands."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.display import DisplayService, Monitor
from lib.profile import ProfileService


class TestPlanCommand(unittest.TestCase):
    """Tests for the plan command."""

    def setUp(self):
        """Set up test fixtures."""
        # Load fixture
        fixture_path = Path(__file__).parent / "fixtures/xrandr/personal-solo-props.txt"
        with open(fixture_path) as f:
            self.xrandr_output = f.read()

        # Expected monitor from fixture (edid is the truncated EDID hash)
        self.expected_monitor = Monitor(
            output="eDP-1",
            edid="7f43020e9adaddcd",
            manufacturer="SYN",
            model="Generic",
            resolution="1920x1080",
            connected=True,
        )

        # Profile service pointing to test profiles
        self.profile_dir = Path(__file__).parent.parent / "profiles"
        self.profile_service = ProfileService(self.profile_dir)

    def test_plan_shows_display_configuration(self):
        """Test that plan command shows display configuration details."""
        # Mock xrandr executor
        mock_executor = MagicMock()
        mock_executor.get_props_output.return_value = self.xrandr_output

        # Create display service with mock
        display_service = DisplayService(executor=mock_executor, dry_run=True)

        # Detect monitors
        monitors = display_service.detect_monitors()
        connected_monitors = [m for m in monitors if m.connected]
        self.assertEqual(len(connected_monitors), 1)
        self.assertEqual(connected_monitors[0].output, "eDP-1")

        # Load profile
        profile = self.profile_service.load_profile("personal-solo")

        # Build alias to output mapping (mimics cmd_plan logic)
        alias_to_output = {}

        # Map laptop
        if profile.laptop:
            laptop_monitor = display_service.get_monitor_by_output(profile.laptop.output, monitors)
            if laptop_monitor:
                alias_to_output[profile.laptop.alias] = laptop_monitor.output

        # Verify mapping
        self.assertEqual(alias_to_output["laptop"], "eDP-1")

        # Verify display configs exist
        self.assertIn("laptop", profile.displays)
        laptop_config = profile.displays["laptop"]
        self.assertTrue(laptop_config.enabled)
        self.assertEqual(laptop_config.resolution, "1920x1200")

    def test_plan_detects_missing_monitors(self):
        """Test that plan command detects when required monitors are missing."""
        # Mock xrandr executor with empty output
        mock_executor = MagicMock()
        mock_executor.get_props_output.return_value = (
            "Screen 0: minimum 8 x 8, current 1920 x 1080\n"
        )

        # Create display service
        display_service = DisplayService(executor=mock_executor, dry_run=True)

        # Detect monitors (should be empty)
        monitors = display_service.detect_monitors()
        self.assertEqual(len(monitors), 0)

    def test_plan_resolves_aliases_to_outputs(self):
        """Test that plan command correctly resolves aliases to output names."""
        # Mock xrandr executor
        mock_executor = MagicMock()
        mock_executor.get_props_output.return_value = self.xrandr_output

        display_service = DisplayService(executor=mock_executor, dry_run=True)
        monitors = display_service.detect_monitors()

        # Load profile
        profile = self.profile_service.load_profile("personal-solo")

        # Build EDID to output mapping
        edid_to_output = {}
        for monitor in monitors:
            if monitor.connected and monitor.edid:
                edid_to_output[monitor.edid] = monitor.output

        # Build alias to output mapping
        alias_to_output = {}

        # Map external monitors by EDID
        for monitor_spec in profile.monitors:
            if monitor_spec.edid in edid_to_output:
                alias_to_output[monitor_spec.alias] = edid_to_output[monitor_spec.edid]

        # Map laptop by output pattern
        if profile.laptop:
            laptop_monitor = display_service.get_monitor_by_output(profile.laptop.output, monitors)
            if laptop_monitor:
                alias_to_output[profile.laptop.alias] = laptop_monitor.output

        # Verify laptop is mapped
        self.assertIn("laptop", alias_to_output)
        self.assertEqual(alias_to_output["laptop"], "eDP-1")


    def test_plan_validates_profile_before_execution(self):
        """Test that plan command validates profile before showing plan."""
        # Load profile
        profile = self.profile_service.load_profile("personal-solo")

        # Validate
        validation = self.profile_service.validate_profile(profile)

        # Should be valid
        self.assertTrue(validation.is_valid)
        self.assertEqual(len(validation.errors), 0)


if __name__ == "__main__":
    unittest.main()
