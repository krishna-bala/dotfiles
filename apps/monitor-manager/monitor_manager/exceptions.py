"""Custom exceptions for monitor manager."""

from pathlib import Path
from typing import List, Optional


class MonitorManagerError(Exception):
    """Base exception for all monitor manager errors."""

    pass


class HardwareDetectionError(MonitorManagerError):
    """Failed to detect hardware."""

    def __init__(self, message: str, xrandr_output: Optional[str] = None):
        """Initialize hardware detection error.

        Args:
            message: Error description
            xrandr_output: Raw xrandr output for debugging
        """
        super().__init__(message)
        self.xrandr_output = xrandr_output


class ProfileError(MonitorManagerError):
    """Base exception for profile-related errors."""

    pass


class ProfileNotFoundError(ProfileError):
    """Profile file doesn't exist."""

    def __init__(self, profile_name: str, searched_path: Path):
        """Initialize profile not found error.

        Args:
            profile_name: Name of profile that wasn't found
            searched_path: Path where profile was searched
        """
        super().__init__(f"Profile '{profile_name}' not found at {searched_path}")
        self.profile_name = profile_name
        self.searched_path = searched_path


class ProfileValidationError(ProfileError):
    """Profile schema validation failed."""

    def __init__(self, profile_name: str, errors: List[str]):
        """Initialize profile validation error.

        Args:
            profile_name: Name of profile that failed validation
            errors: List of validation error messages
        """
        error_list = "\n  - ".join(errors)
        super().__init__(f"Profile '{profile_name}' validation failed:\n  - {error_list}")
        self.profile_name = profile_name
        self.errors = errors


class ConfigurationError(MonitorManagerError):
    """Base exception for configuration application failures."""

    pass


class DisplayConfigurationError(ConfigurationError):
    """xrandr command failed."""

    def __init__(
        self,
        message: str,
        command: Optional[List[str]] = None,
        stderr: Optional[str] = None,
        rollback_file: Optional[Path] = None,
    ):
        """Initialize display configuration error.

        Args:
            message: Error description
            command: xrandr command that failed
            stderr: Standard error output from command
            rollback_file: Path to rollback configuration file
        """
        super().__init__(message)
        self.command = command
        self.stderr = stderr
        self.rollback_file = rollback_file


class WindowManagerConfigurationError(ConfigurationError):
    """BSPWM configuration failed."""

    def __init__(
        self,
        message: str,
        bspc_command: Optional[List[str]] = None,
        stderr: Optional[str] = None,
    ):
        """Initialize window manager configuration error.

        Args:
            message: Error description
            bspc_command: bspc command that failed
            stderr: Standard error output from command
        """
        super().__init__(message)
        self.bspc_command = bspc_command
        self.stderr = stderr
