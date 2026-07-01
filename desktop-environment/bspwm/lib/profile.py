"""Profile management - loading, validation, and matching."""

import logging
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from .exceptions import ProfileNotFoundError, ProfileValidationError

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of profile validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class MonitorDetection:
    """Monitor detection specification for profile matching."""

    edid: str  # Truncated hash of the full EDID (match key, not raw bytes)
    alias: str  # Logical name used in config (e.g., "primary", "secondary")
    manufacturer: Optional[str] = None  # Human-readable manufacturer
    model: Optional[str] = None  # Human-readable model


@dataclass
class LaptopDetection:
    """Laptop display detection specification."""

    output: str  # Output name pattern (e.g., "eDP-1", "eDP-1-1")
    alias: str = "laptop"  # Logical name (default: "laptop")
    edid: Optional[str] = None  # Truncated EDID hash for precise matching


@dataclass
class DisplayConfig:
    """Physical display configuration for xrandr."""

    output: str  # Monitor output name or alias
    enabled: bool = True
    resolution: Optional[str] = None  # "2560x1440"
    position: Optional[str] = None  # "0x0", "1920x0"
    rotation: str = "normal"  # "normal", "left", "right", "inverted"
    scale: str = "1x1"  # Scaling factor
    primary: bool = False


@dataclass
class WindowManagerConfig:
    """BSPWM window manager configuration."""

    monitor_order: List[str]  # Monitor aliases in physical order
    workspaces: Dict[str, List[int]]  # Workspace numbers per monitor alias
    settings: Optional[Dict[str, Any]] = None  # Optional BSPWM settings override


@dataclass
class PolybarConfig:
    """Polybar configuration for a single monitor."""

    monitor: str  # Monitor alias
    orientation: str = "landscape"  # "landscape" or "portrait"
    font_size: Optional[int] = None
    modules: Optional[Dict[str, str]] = None  # left, center, right modules


@dataclass
class UIConfig:
    """UI layer configuration (polybar)."""

    bars: List[PolybarConfig] = field(default_factory=list)


@dataclass
class Profile:
    """Complete monitor configuration profile."""

    name: str
    description: str
    monitors: List[MonitorDetection]  # Required external monitors
    laptop: Optional[LaptopDetection]  # Laptop display spec
    displays: Dict[str, DisplayConfig]  # Display configs by alias
    window_manager: WindowManagerConfig
    ui: UIConfig


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge `override` onto `base` recursively. Dicts merge; everything
    else (including lists) is replaced by the override value."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class ProfileService:
    """Service for profile loading, validation, and matching."""

    DEFAULT_PROFILES_DIR = Path.home() / ".dotfiles/bspwm/profiles"

    # Shared defaults merged under every profile at load time; profiles
    # only specify what differs. Not a profile itself.
    DEFAULTS_FILE = "defaults.yaml"

    def __init__(self, profiles_dir: Optional[Path] = None):
        """Initialize profile service.

        Args:
            profiles_dir: Directory containing YAML profiles (default: ~/.dotfiles/bspwm/profiles)
        """
        self.profiles_dir = Path(profiles_dir or self.DEFAULT_PROFILES_DIR)
        self._defaults: Optional[dict] = None

    def _load_defaults(self) -> dict:
        """Load profiles/defaults.yaml once; missing file means no defaults."""
        if self._defaults is None:
            defaults_path = self.profiles_dir / self.DEFAULTS_FILE
            if defaults_path.exists():
                with open(defaults_path) as f:
                    self._defaults = yaml.safe_load(f) or {}
            else:
                self._defaults = {}
        return self._defaults

    def load_profile(self, profile_name: str) -> Profile:
        """Load a profile from YAML file.

        Args:
            profile_name: Profile name (without .yaml extension)

        Returns:
            Profile object

        Raises:
            ProfileNotFoundError: If profile doesn't exist
            ProfileValidationError: If YAML is invalid or missing required fields
        """
        profile_path = self.profiles_dir / f"{profile_name}.yaml"

        if not profile_path.exists():
            raise ProfileNotFoundError(profile_name, profile_path)

        try:
            with open(profile_path) as f:
                data = yaml.safe_load(f)

            data = _deep_merge(self._load_defaults(), data)
            return self._parse_profile_dict(data)
        except (KeyError, TypeError, ValueError) as e:
            raise ProfileValidationError(profile_name, [str(e)]) from e

    def _parse_profile_dict(self, data: dict) -> Profile:
        """Parse profile dictionary into Profile object.

        Args:
            data: Profile data from YAML

        Returns:
            Profile object

        Raises:
            ValueError: If required fields are missing or invalid (will be caught and re-raised as ProfileValidationError)
        """
        # Validate top-level required fields
        required_fields = ["name", "description", "detection", "display", "window_manager", "ui"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Parse detection section
        detection = data["detection"]
        monitors = []
        for mon_data in detection.get("monitors", []):
            monitors.append(
                MonitorDetection(
                    edid=mon_data["edid"],
                    alias=mon_data["alias"],
                    manufacturer=mon_data.get("manufacturer"),
                    model=mon_data.get("model"),
                )
            )

        laptop = None
        if "laptop" in detection:
            laptop_data = detection["laptop"]
            laptop = LaptopDetection(
                output=laptop_data["output"],
                alias=laptop_data.get("alias", "laptop"),
                edid=laptop_data.get("edid"),
            )

        # Parse display section
        displays = {}
        for alias, disp_data in data["display"].items():
            displays[alias] = DisplayConfig(
                output=alias,  # Will be resolved later
                enabled=disp_data.get("enabled", True),
                resolution=disp_data.get("resolution"),
                position=disp_data.get("position"),
                rotation=disp_data.get("rotation", "normal"),
                scale=disp_data.get("scale", "1x1"),
                primary=disp_data.get("primary", False),
            )

        # Parse window_manager section
        wm_data = data["window_manager"]
        window_manager = WindowManagerConfig(
            monitor_order=wm_data["monitor_order"],
            workspaces=wm_data["workspaces"],
            settings=wm_data.get("settings"),
        )

        # Parse ui section. Bars without an explicit font_size inherit
        # ui.font_size (typically supplied by profiles/defaults.yaml).
        ui_data = data["ui"]
        default_font_size = ui_data.get("font_size")
        bars = []
        for bar_data in ui_data.get("bars", []):
            bars.append(
                PolybarConfig(
                    monitor=bar_data["monitor"],
                    orientation=bar_data.get("orientation", "landscape"),
                    font_size=bar_data.get("font_size", default_font_size),
                    modules=bar_data.get("modules"),
                )
            )
        ui = UIConfig(bars=bars)

        return Profile(
            name=data["name"],
            description=data["description"],
            monitors=monitors,
            laptop=laptop,
            displays=displays,
            window_manager=window_manager,
            ui=ui,
        )

    def validate_profile(self, profile: Profile) -> ValidationResult:
        """Validate profile for consistency and completeness.

        Args:
            profile: Profile to validate

        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Check name is not empty
        if not profile.name:
            result.errors.append("Profile name cannot be empty")

        # Check at least one monitor or laptop is specified
        if not profile.monitors and not profile.laptop:
            result.errors.append("Profile must specify at least one monitor or laptop display")

        # Collect all monitor aliases
        all_aliases = {m.alias for m in profile.monitors}
        if profile.laptop:
            all_aliases.add(profile.laptop.alias)

        # Check display configs reference valid aliases
        for alias in profile.displays.keys():
            if alias not in all_aliases:
                result.errors.append(f"Display config '{alias}' doesn't match any monitor alias")

        # Check enabled displays have required fields
        for alias, disp in profile.displays.items():
            if disp.enabled:
                if not disp.resolution:
                    result.errors.append(f"Display '{alias}': resolution required when enabled")
                if not disp.position:
                    result.errors.append(f"Display '{alias}': position required when enabled")

        # Check rotation is valid
        valid_rotations = {"normal", "left", "right", "inverted"}
        for alias, disp in profile.displays.items():
            if disp.rotation not in valid_rotations:
                result.errors.append(
                    f"Display '{alias}': invalid rotation '{disp.rotation}' "
                    f"(must be one of {valid_rotations})"
                )

        # Check at most one primary display
        primary_displays = [alias for alias, disp in profile.displays.items() if disp.primary]
        if len(primary_displays) > 1:
            result.errors.append(
                f"Multiple primary displays specified: {', '.join(primary_displays)}"
            )

        # Check window_manager.monitor_order references valid aliases
        for alias in profile.window_manager.monitor_order:
            if alias not in all_aliases:
                result.errors.append(
                    f"Window manager monitor_order references unknown alias '{alias}'"
                )

        # Check window_manager.workspaces keys match aliases
        for alias in profile.window_manager.workspaces.keys():
            if alias not in all_aliases:
                result.errors.append(
                    f"Window manager workspaces references unknown alias '{alias}'"
                )

        # Check workspace numbers are unique
        all_workspaces = []
        for workspaces in profile.window_manager.workspaces.values():
            all_workspaces.extend(workspaces)
        duplicates = [ws for ws in set(all_workspaces) if all_workspaces.count(ws) > 1]
        if duplicates:
            result.errors.append(f"Duplicate workspace numbers: {duplicates}")

        # Check UI bars reference valid aliases
        for bar in profile.ui.bars:
            if bar.monitor not in all_aliases:
                result.errors.append(f"UI bar references unknown monitor alias '{bar.monitor}'")

        # Check UI bar orientation is valid
        valid_orientations = {"landscape", "portrait"}
        for bar in profile.ui.bars:
            if bar.orientation not in valid_orientations:
                result.errors.append(
                    f"UI bar for '{bar.monitor}': invalid orientation '{bar.orientation}' "
                    f"(must be one of {valid_orientations})"
                )

        result.is_valid = len(result.errors) == 0
        return result

    def list_profiles(self) -> List[str]:
        """List all available profiles.

        Returns:
            List of profile names (without .yaml extension)
        """
        if not self.profiles_dir.exists():
            return []

        return sorted(
            p.stem for p in self.profiles_dir.glob("*.yaml") if p.stem != "defaults"
        )

    def match_profiles(self, detected_monitors: List) -> List[Tuple[str, float, Profile]]:
        """Match detected monitors to available profiles with scoring.

        Scoring algorithm:
        - Each required monitor EDID match: +100 points
        - Laptop EDID match (if specified): +100 points
        - Extra detected monitors not in profile: -10 points per monitor
        - Missing required monitors: Profile not included in results

        Args:
            detected_monitors: List of Monitor objects from DisplayService.detect_monitors()

        Returns:
            List of tuples (profile_name, score, profile) sorted by score (highest first)
            Only includes profiles where all required monitors are detected
        """
        # Extract EDIDs from detected monitors
        detected_edids = {m.edid for m in detected_monitors if m.connected and m.edid}

        # Build laptop EDID set from eDP-* outputs
        laptop_edids = {
            m.edid for m in detected_monitors
            if m.connected and m.edid and m.output.startswith("eDP-")
        }

        matched_profiles = []

        # Load and score each profile
        for profile_name in self.list_profiles():
            try:
                profile = self.load_profile(profile_name)
            except (ProfileNotFoundError, ProfileValidationError) as e:
                logger.warning(f"Skipping invalid profile {profile_name}: {e}")
                continue  # Skip invalid profiles

            # Collect required EDIDs from profile
            required_edids = {m.edid for m in profile.monitors}

            # Check if laptop is required
            laptop_required = profile.laptop is not None

            # Check if all required external monitors are detected
            if not required_edids.issubset(detected_edids):
                continue  # Missing required monitors, skip this profile

            # Check laptop matching
            laptop_matched = False
            matched_laptop_edid = None

            if laptop_required:
                if profile.laptop.edid:
                    # Profile specifies laptop EDID - match by EDID
                    if profile.laptop.edid in laptop_edids:
                        laptop_matched = True
                        matched_laptop_edid = profile.laptop.edid
                    else:
                        logger.debug(
                            f"Profile {profile_name}: laptop EDID not detected"
                        )
                        continue  # Laptop EDID not found, skip
                else:
                    # Profile has no laptop EDID - warn and skip
                    logger.warning(
                        f"Profile {profile_name}: laptop detection missing EDID, skipping. "
                        f"Add EDID to detection.laptop for reliable matching."
                    )
                    continue

            # Calculate score
            score = 0.0

            # Points for each matched external monitor
            score += len(required_edids) * 100

            # Points for laptop match
            if laptop_matched:
                score += 100

            # Penalty for extra monitors not used in profile
            profile_edids = required_edids.copy()
            if matched_laptop_edid:
                profile_edids.add(matched_laptop_edid)

            extra_monitors = detected_edids - profile_edids
            score -= len(extra_monitors) * 10

            matched_profiles.append((profile_name, score, profile))

        # Sort by score (highest first)
        matched_profiles.sort(key=lambda x: x[1], reverse=True)

        return matched_profiles
