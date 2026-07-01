"""Tests for interactive TUI module."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lib.interactive import InteractiveMenu, MenuChoice, run_interactive_menu
from lib.display import Monitor
from lib.profile import Profile, DisplayConfig, WindowManagerConfig, UIConfig


class TestInteractiveMenu(unittest.TestCase):
    """Test interactive menu functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock services
        self.mock_coordinator = MagicMock()
        self.mock_profile_service = MagicMock()
        self.mock_display_service = MagicMock()

        # Create sample monitor
        self.sample_monitor = Monitor(
            output="eDP-1",
            edid="00ffffffffffff00" + "0" * 240,
            manufacturer="LGD",
            model="Unknown",
            resolution="1920x1200",
            connected=True,
        )

        # Create sample profile (use MagicMock since Profile has complex structure)
        self.sample_profile = MagicMock(spec=Profile)
        self.sample_profile.name = "personal-solo"
        self.sample_profile.description = "Personal laptop solo"
        self.sample_profile.monitors = []
        self.sample_profile.laptop = MagicMock()
        self.sample_profile.window_manager = MagicMock()
        self.sample_profile.ui = MagicMock()

    @patch("lib.interactive.TerminalMenu")
    def test_menu_initialization_requires_simple_term_menu(self, mock_term_menu):
        """Test that InteractiveMenu requires simple-term-menu."""
        # This should work when TerminalMenu is available
        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )
        self.assertIsNotNone(menu)

    @patch("lib.interactive.TerminalMenu", None)
    def test_menu_initialization_fails_without_simple_term_menu(self):
        """Test that InteractiveMenu raises ImportError without simple-term-menu."""
        with self.assertRaises(ImportError) as ctx:
            InteractiveMenu(
                self.mock_coordinator,
                self.mock_profile_service,
                self.mock_display_service,
            )

        self.assertIn("simple-term-menu", str(ctx.exception))

    @patch("lib.interactive.TerminalMenu")
    def test_show_detected_monitors_with_monitors(self, mock_term_menu):
        """Test showing detected monitors when monitors are present."""
        self.mock_display_service.detect_monitors.return_value = [self.sample_monitor]

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        monitors = menu.show_detected_monitors()

        self.assertEqual(len(monitors), 1)
        self.assertEqual(monitors[0].output, "eDP-1")
        self.mock_display_service.detect_monitors.assert_called_once()

    @patch("lib.interactive.TerminalMenu")
    def test_show_detected_monitors_without_monitors(self, mock_term_menu):
        """Test showing detected monitors when no monitors are present."""
        self.mock_display_service.detect_monitors.return_value = []

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        monitors = menu.show_detected_monitors()

        self.assertEqual(len(monitors), 0)

    @patch("lib.interactive.TerminalMenu")
    def test_show_matched_profiles_with_matches(self, mock_term_menu):
        """Test showing matched profiles when matches exist."""
        matches = [("personal-solo", 100, self.sample_profile)]
        self.mock_profile_service.match_profiles.return_value = matches

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.show_matched_profiles([self.sample_monitor])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "personal-solo")  # profile_name
        self.assertEqual(result[0][1], 100)  # score
        self.assertEqual(result[0][2].name, "personal-solo")  # profile

    @patch("lib.interactive.TerminalMenu")
    def test_show_matched_profiles_without_matches(self, mock_term_menu):
        """Test showing matched profiles when no matches exist."""
        self.mock_profile_service.match_profiles.return_value = []

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.show_matched_profiles([self.sample_monitor])

        self.assertEqual(len(result), 0)

    @patch("lib.interactive.TerminalMenu")
    def test_select_profile_returns_name(self, mock_term_menu_class):
        """Test selecting a profile returns profile name."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        mock_menu_instance.show.return_value = 0  # Select first item
        mock_term_menu_class.return_value = mock_menu_instance

        matches = [("personal-solo", 100, self.sample_profile)]

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.select_profile(matches)

        self.assertEqual(result, "personal-solo")
        mock_menu_instance.show.assert_called_once()

    @patch("lib.interactive.TerminalMenu")
    def test_select_profile_cancel(self, mock_term_menu_class):
        """Test canceling profile selection."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        mock_menu_instance.show.return_value = 1  # Select "Cancel" (second item)
        mock_term_menu_class.return_value = mock_menu_instance

        matches = [("personal-solo", 100, self.sample_profile)]

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.select_profile(matches)

        self.assertIsNone(result)

    @patch("lib.interactive.TerminalMenu")
    def test_select_action_plan(self, mock_term_menu_class):
        """Test selecting plan action."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        mock_menu_instance.show.return_value = 0  # Select "Show plan"
        mock_term_menu_class.return_value = mock_menu_instance

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.select_action()

        self.assertEqual(result, "plan")

    @patch("lib.interactive.TerminalMenu")
    def test_select_action_apply(self, mock_term_menu_class):
        """Test selecting apply action."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        mock_menu_instance.show.return_value = 1  # Select "Apply configuration"
        mock_term_menu_class.return_value = mock_menu_instance

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.select_action()

        self.assertEqual(result, "apply")

    @patch("lib.interactive.TerminalMenu")
    def test_select_action_cancel(self, mock_term_menu_class):
        """Test canceling action selection."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        mock_menu_instance.show.return_value = 2  # Select "Cancel"
        mock_term_menu_class.return_value = mock_menu_instance

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.select_action()

        self.assertEqual(result, "cancel")

    @patch("lib.interactive.TerminalMenu")
    def test_confirm_application_yes(self, mock_term_menu_class):
        """Test confirming application."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        mock_menu_instance.show.return_value = 0  # Select "Yes"
        mock_term_menu_class.return_value = mock_menu_instance

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.confirm_application("personal-solo")

        self.assertTrue(result)

    @patch("lib.interactive.TerminalMenu")
    def test_confirm_application_no(self, mock_term_menu_class):
        """Test declining application."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        mock_menu_instance.show.return_value = 1  # Select "No"
        mock_term_menu_class.return_value = mock_menu_instance

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.confirm_application("personal-solo")

        self.assertFalse(result)

    @patch("lib.interactive.TerminalMenu")
    @patch("builtins.input", return_value="")  # Mock input() for "Press Enter"
    def test_run_workflow_cancel_at_profile_selection(self, mock_input, mock_term_menu_class):
        """Test full workflow with cancellation at profile selection."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        # First call: profile selection (cancel)
        mock_menu_instance.show.return_value = 1  # Cancel
        mock_term_menu_class.return_value = mock_menu_instance

        # Setup mocks
        self.mock_display_service.detect_monitors.return_value = [self.sample_monitor]
        self.mock_profile_service.match_profiles.return_value = [
            ("personal-solo", 100, self.sample_profile)
        ]

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.run()

        self.assertIsNone(result.profile_name)
        self.assertEqual(result.action, "cancel")

    @patch("lib.interactive.TerminalMenu")
    @patch("builtins.input", return_value="")  # Mock input() for "Press Enter"
    def test_run_workflow_plan_action(self, mock_input, mock_term_menu_class):
        """Test full workflow with plan action."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        # Sequence of calls: profile selection, action selection
        mock_menu_instance.show.side_effect = [
            0,  # Select first profile
            0,  # Select "Show plan"
        ]
        mock_term_menu_class.return_value = mock_menu_instance

        # Setup mocks
        self.mock_display_service.detect_monitors.return_value = [self.sample_monitor]
        self.mock_profile_service.match_profiles.return_value = [
            ("personal-solo", 100, self.sample_profile)
        ]

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.run()

        self.assertEqual(result.profile_name, "personal-solo")
        self.assertEqual(result.action, "plan")

    @patch("lib.interactive.TerminalMenu")
    @patch("builtins.input", return_value="")  # Mock input() for "Press Enter"
    def test_run_workflow_apply_confirmed(self, mock_input, mock_term_menu_class):
        """Test full workflow with apply action confirmed."""
        # Mock TerminalMenu instance
        mock_menu_instance = MagicMock()
        # Sequence of calls: profile selection, action selection, confirmation
        mock_menu_instance.show.side_effect = [
            0,  # Select first profile
            1,  # Select "Apply configuration"
            0,  # Confirm "Yes"
        ]
        mock_term_menu_class.return_value = mock_menu_instance

        # Setup mocks
        self.mock_display_service.detect_monitors.return_value = [self.sample_monitor]
        self.mock_profile_service.match_profiles.return_value = [
            ("personal-solo", 100, self.sample_profile)
        ]

        menu = InteractiveMenu(
            self.mock_coordinator,
            self.mock_profile_service,
            self.mock_display_service,
        )

        result = menu.run()

        self.assertEqual(result.profile_name, "personal-solo")
        self.assertEqual(result.action, "apply")

    @patch("lib.interactive.TerminalMenu")
    def test_run_interactive_menu_convenience_function(self, mock_term_menu):
        """Test run_interactive_menu convenience function."""
        # This is a simple wrapper, just verify it creates menu and calls run()
        with patch.object(InteractiveMenu, "run") as mock_run:
            mock_run.return_value = MenuChoice(profile_name="test", action="plan")

            result = run_interactive_menu(
                self.mock_coordinator,
                self.mock_profile_service,
                self.mock_display_service,
            )

            self.assertEqual(result.profile_name, "test")
            self.assertEqual(result.action, "plan")
            mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
