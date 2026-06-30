"""State management for default profile preference."""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class State:
    """Application state."""

    default_profile: Optional[str] = None


class StateService:
    """Service for managing application state (default profile preference)."""

    DEFAULT_STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "bspwm-monitor-manager"
    DEFAULT_STATE_FILE = DEFAULT_STATE_DIR / "state.json"

    def __init__(self, state_file: Optional[Path] = None):
        """Initialize state service.

        Args:
            state_file: Path to state file (default: /tmp/bspwm-monitor-manager/state.json)
        """
        self.state_file = state_file or self.DEFAULT_STATE_FILE
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def get_default(self) -> Optional[str]:
        """Get the default profile preference.

        Returns:
            Profile name if set, None otherwise
        """
        state = self._load_state()
        return state.default_profile

    def set_default(self, profile_name: str) -> None:
        """Set the default profile preference.

        Args:
            profile_name: Name of profile to set as default
        """
        state = State(default_profile=profile_name)
        self._save_state(state)
        logger.info(f"Set default profile to: {profile_name}")

    def clear_default(self) -> None:
        """Clear the default profile preference."""
        state = State(default_profile=None)
        self._save_state(state)
        logger.info("Cleared default profile")

    def _load_state(self) -> State:
        """Load state from file.

        Returns:
            State object (with defaults if file doesn't exist or is invalid)
        """
        if not self.state_file.exists():
            return State()

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
            return State(default_profile=data.get('default_profile'))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load state file: {e}. Using defaults.")
            return State()

    def _save_state(self, state: State) -> None:
        """Save state to file.

        Args:
            state: State object to save
        """
        try:
            data = {
                'default_profile': state.default_profile
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.error(f"Failed to save state file: {e}")
            raise
