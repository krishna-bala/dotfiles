"""Unit tests for display detection service."""

import unittest
from unittest.mock import patch, Mock
from pathlib import Path

from lib.display import DisplayService, Monitor, XrandrExecutor


class MockXrandrExecutor:
    """Mock executor for testing."""

    def __init__(self, props_output: str):
        self.props_output = props_output
        self.executed_commands = []

    def get_props_output(self) -> str:
        return self.props_output

    def execute_command(self, command: list) -> None:
        self.executed_commands.append(command)


class TestDisplayService(unittest.TestCase):
    """Test cases for DisplayService."""

    def setUp(self):
        """Load test fixtures."""
        fixture_path = Path(__file__).parent / "fixtures" / "xrandr" / "personal-solo-props.txt"
        with open(fixture_path) as f:
            self.xrandr_props = f.read()

        self.mock_executor = MockXrandrExecutor(self.xrandr_props)
        self.service = DisplayService(executor=self.mock_executor)

    def test_parse_xrandr_output_personal_solo(self):
        """Test parsing xrandr output for personal-solo configuration."""
        monitors = self.service._parse_xrandr_output(self.xrandr_props)

        # Should detect all outputs (connected + disconnected)
        self.assertGreaterEqual(len(monitors), 1)

        # Find connected monitor
        connected = [m for m in monitors if m.connected]
        self.assertEqual(len(connected), 1)

        # Verify eDP-1 details
        edp = next(m for m in monitors if m.output == "eDP-1")
        self.assertTrue(edp.connected)
        self.assertEqual(edp.resolution, "1920x1080")
        self.assertIsNotNone(edp.edid)
        self.assertEqual(len(edp.edid), 16)

    def test_parse_edid_extraction(self):
        """Test that EDID is correctly reduced to its truncated hash."""
        monitors = self.service._parse_xrandr_output(self.xrandr_props)
        edp = next(m for m in monitors if m.output == "eDP-1")

        # edid is the truncated EDID hash (match key), not the raw bytes
        self.assertIsNotNone(edp.edid)
        self.assertEqual(len(edp.edid), 16)
        # Should be valid hex
        int(edp.edid, 16)

    def test_parse_disconnected_monitors(self):
        """Test that disconnected monitors are correctly identified."""
        monitors = self.service._parse_xrandr_output(self.xrandr_props)

        disconnected = [m for m in monitors if not m.connected]
        self.assertGreater(len(disconnected), 0)

        # Check that disconnected monitors have output names
        for monitor in disconnected:
            self.assertIsNotNone(monitor.output)
            self.assertTrue(len(monitor.output) > 0)

    def test_detect_monitors_calls_xrandr(self):
        """Test that detect_monitors uses executor to get output."""
        monitors = self.service.detect_monitors()

        # Verify monitors were parsed from executor output
        self.assertGreater(len(monitors), 0)

    def test_get_monitor_by_output(self):
        """Test getting monitor by output name."""
        monitors = self.service.detect_monitors()

        monitor = self.service.get_monitor_by_output("eDP-1", monitors)

        self.assertIsNotNone(monitor)
        self.assertEqual(monitor.output, "eDP-1")
        self.assertEqual(len(monitor.edid), 16)

    def test_get_monitor_by_output_nonexistent(self):
        """Test that get_monitor_by_output returns None for non-existent output."""
        monitors = self.service.detect_monitors()

        monitor = self.service.get_monitor_by_output("NONEXISTENT-OUTPUT", monitors)

        self.assertIsNone(monitor)

    def test_parse_edid_info(self):
        """Test manufacturer extraction from EDID."""
        # Synthetic EDID header (not derived from any real hardware)
        edid = "00ffffffffffff00aabbccdd00000000"

        manufacturer, model = self.service._parse_edid_info(edid * 8)  # Make it long enough

        # Manufacturer should be extracted (3 letters)
        self.assertEqual(len(manufacturer), 3)
        self.assertTrue(manufacturer.isupper())

    def test_dry_run_mode(self):
        """Test that dry_run flag is stored."""
        service = DisplayService(executor=self.mock_executor, dry_run=True)
        self.assertTrue(service.dry_run)

        service = DisplayService(executor=self.mock_executor, dry_run=False)
        self.assertFalse(service.dry_run)



if __name__ == "__main__":
    unittest.main()
