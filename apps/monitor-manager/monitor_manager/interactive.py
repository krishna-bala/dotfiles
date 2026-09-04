"""Interactive TUI for monitor profile selection.

This module provides a terminal user interface for selecting and applying
monitor profiles interactively using simple-term-menu.
"""

from pathlib import Path
from typing import Optional, List, Tuple
from dataclasses import dataclass

try:
    from simple_term_menu import TerminalMenu
except ImportError:
    TerminalMenu = None  # Allow module to load even if simple-term-menu not installed

from .display import DisplayService, Monitor
from .profile import ProfileService, Profile
from .coordinator import MonitorManagerCoordinator, ResolvedProfile


@dataclass
class MenuChoice:
    """Result of an interactive menu choice."""

    profile_name: Optional[str]
    action: str  # "apply", "plan", "cancel"


class InteractiveMenu:
    """Interactive TUI for profile selection and application."""

    def __init__(
        self,
        coordinator: MonitorManagerCoordinator,
        profile_service: ProfileService,
        display_service: DisplayService,
    ):
        """Initialize interactive menu.

        Args:
            coordinator: Coordinator service for profile resolution
            profile_service: Profile service for loading profiles
            display_service: Display service for monitor detection
        """
        if TerminalMenu is None:
            raise ImportError(
                "simple-term-menu is required for interactive mode. "
                "Install with: uv add simple-term-menu"
            )

        self.coordinator = coordinator
        self.profile_service = profile_service
        self.display_service = display_service

    def show_detected_monitors(self) -> List[Monitor]:
        """Show detected monitors in a formatted display.

        Returns:
            List of detected monitors
        """
        print("\n" + "=" * 60)
        print("DETECTED MONITORS")
        print("=" * 60)

        monitors = self.display_service.detect_monitors()

        if not monitors:
            print("⚠ No monitors detected")
            return []

        for i, monitor in enumerate(monitors, 1):
            print(f"\n{i}. {monitor.output}")
            print(f"   Manufacturer: {monitor.manufacturer}")
            print(f"   Model: {monitor.model}")
            print(f"   Resolution: {monitor.resolution}")
            print(f"   EDID: {monitor.edid[:32]}...")
            print(f"   Connected: {'Yes' if monitor.connected else 'No'}")

        return monitors

    def show_matched_profiles(self, monitors: List[Monitor]) -> List[Tuple[str, float, Profile]]:
        """Show profiles matched to current hardware.

        Args:
            monitors: List of detected monitors

        Returns:
            List of (profile_name, score, profile) tuples
        """
        print("\n" + "=" * 60)
        print("MATCHING PROFILES")
        print("=" * 60)

        matches = self.profile_service.match_profiles(monitors)

        if not matches:
            print("⚠ No matching profiles found")
            return []

        for i, (profile_name, score, profile) in enumerate(matches, 1):
            print(f"\n{i}. {profile.name} (score: {score})")
            print(f"   {profile.description}")
            print(f"   External monitors: {len(profile.monitors)}")
            if profile.laptop:
                print(f"   Laptop display: Yes")

        return matches

    def select_profile(self, matches: List[Tuple[str, float, Profile]]) -> Optional[str]:
        """Show profile selection menu.

        Args:
            matches: List of (profile_name, score, profile) tuples

        Returns:
            Selected profile name, or None if cancelled
        """
        if not matches:
            return None

        # Build menu options
        menu_items = []
        for profile_name, score, profile in matches:
            menu_items.append(f"{profile.name} - {profile.description} (score: {score})")

        menu_items.append("Cancel")

        # Show menu
        print("\n" + "=" * 60)
        print("SELECT PROFILE")
        print("=" * 60)
        print("Use arrow keys to navigate, Enter to select:\n")

        terminal_menu = TerminalMenu(
            menu_items,
            title="Available Profiles:",
            menu_cursor="→ ",
            menu_cursor_style=("fg_cyan", "bold"),
            menu_highlight_style=("bg_cyan", "fg_black"),
        )

        choice_index = terminal_menu.show()

        if choice_index is None or choice_index == len(menu_items) - 1:
            # User cancelled or selected "Cancel"
            return None

        profile_name, _, _ = matches[choice_index]
        return profile_name

    def select_action(self) -> str:
        """Show action selection menu.

        Returns:
            Action choice: "plan", "apply", or "cancel"
        """
        menu_items = [
            "Show plan (dry-run preview)",
            "Apply configuration",
            "Cancel",
        ]

        print("\n" + "=" * 60)
        print("SELECT ACTION")
        print("=" * 60)
        print("Use arrow keys to navigate, Enter to select:\n")

        terminal_menu = TerminalMenu(
            menu_items,
            title="What would you like to do?",
            menu_cursor="→ ",
            menu_cursor_style=("fg_cyan", "bold"),
            menu_highlight_style=("bg_cyan", "fg_black"),
        )

        choice_index = terminal_menu.show()

        if choice_index is None or choice_index == 2:
            return "cancel"
        elif choice_index == 0:
            return "plan"
        else:
            return "apply"

    def confirm_application(self, profile_name: str) -> bool:
        """Confirm profile application.

        Args:
            profile_name: Name of profile to apply

        Returns:
            True if confirmed, False otherwise
        """
        menu_items = [
            f"Yes, apply {profile_name}",
            "No, cancel",
        ]

        print("\n" + "=" * 60)
        print("CONFIRM APPLICATION")
        print("=" * 60)
        print("Use arrow keys to navigate, Enter to select:\n")

        terminal_menu = TerminalMenu(
            menu_items,
            title=f"Apply profile '{profile_name}'?",
            menu_cursor="→ ",
            menu_cursor_style=("fg_yellow", "bold"),
            menu_highlight_style=("bg_yellow", "fg_black"),
        )

        choice_index = terminal_menu.show()

        return choice_index == 0

    def run(self) -> MenuChoice:
        """Run interactive menu workflow.

        Returns:
            MenuChoice with selected profile and action
        """
        # Step 1: Detect monitors
        monitors = self.show_detected_monitors()
        if not monitors:
            print("\n⚠ Cannot continue without detected monitors")
            return MenuChoice(profile_name=None, action="cancel")

        input("\nPress Enter to continue...")

        # Step 2: Show matched profiles
        matches = self.show_matched_profiles(monitors)
        if not matches:
            print("\n⚠ No profiles match current hardware")
            return MenuChoice(profile_name=None, action="cancel")

        input("\nPress Enter to continue...")

        # Step 3: Select profile
        profile_name = self.select_profile(matches)
        if profile_name is None:
            print("\n✓ Cancelled")
            return MenuChoice(profile_name=None, action="cancel")

        # Step 4: Select action
        action = self.select_action()
        if action == "cancel":
            print("\n✓ Cancelled")
            return MenuChoice(profile_name=None, action="cancel")

        # Step 5: If applying, confirm
        if action == "apply":
            if not self.confirm_application(profile_name):
                print("\n✓ Cancelled")
                return MenuChoice(profile_name=None, action="cancel")

        return MenuChoice(profile_name=profile_name, action=action)


def run_interactive_menu(
    coordinator: MonitorManagerCoordinator,
    profile_service: ProfileService,
    display_service: DisplayService,
) -> MenuChoice:
    """Convenience function to run interactive menu.

    Args:
        coordinator: Coordinator service
        profile_service: Profile service
        display_service: Display service

    Returns:
        MenuChoice with selected profile and action
    """
    menu = InteractiveMenu(coordinator, profile_service, display_service)
    return menu.run()
