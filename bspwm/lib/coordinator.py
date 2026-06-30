"""Coordinator service for orchestrating profile application."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .display import DisplayService, Monitor
from .profile import Profile, ProfileService, DisplayConfig, ValidationResult
from .exceptions import ProfileValidationError


@dataclass
class ResolvedProfile:
    """Profile with aliases resolved to actual hardware outputs."""

    profile: Profile
    monitors: List[Monitor]  # Detected monitors
    alias_to_output: Dict[str, str]  # Mapping of alias to actual output name
    display_configs: List[DisplayConfig]  # Display configs with resolved output names


@dataclass
class PlanResult:
    """Result of planning profile application."""

    resolved: ResolvedProfile
    validation: ValidationResult


class MonitorManagerCoordinator:
    """Orchestrates all services for profile application."""

    def __init__(
        self,
        display_service: Optional[DisplayService] = None,
        profile_service: Optional[ProfileService] = None,
    ):
        """Initialize coordinator.

        Args:
            display_service: DisplayService instance (creates default if None)
            profile_service: ProfileService instance (creates default if None)
        """
        self.display = display_service or DisplayService()
        self.profile = profile_service or ProfileService()

    def resolve_profile(self, profile_name: str) -> ResolvedProfile:
        """Resolve profile aliases to actual hardware outputs.

        Args:
            profile_name: Name of profile to resolve

        Returns:
            ResolvedProfile with all aliases mapped to actual outputs

        Raises:
            ProfileNotFoundError: If profile doesn't exist
            ProfileValidationError: If profile is invalid or required monitors missing
        """
        # Detect monitors
        monitors = self.display.detect_monitors()

        if not monitors:
            raise ProfileValidationError(profile_name, ["No monitors detected"])

        # Load profile
        profile = self.profile.load_profile(profile_name)

        # Validate profile
        validation = self.profile.validate_profile(profile)
        if not validation.is_valid:
            raise ProfileValidationError(profile_name, validation.errors)

        # Build EDID to output mapping from detected monitors
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

        # Map laptop by EDID, falling back to the recorded output name.
        # Panel names vary across machines (eDP-1 vs eDP-1-1), and profile
        # matching already accepts any eDP-* by EDID, so resolution must too.
        if profile.laptop:
            if profile.laptop.edid and profile.laptop.edid in edid_to_output:
                alias_to_output[profile.laptop.alias] = edid_to_output[profile.laptop.edid]
            else:
                laptop_monitor = self.display.get_monitor_by_output(profile.laptop.output, monitors)
                if laptop_monitor:
                    alias_to_output[profile.laptop.alias] = laptop_monitor.output

        # Check if all required monitors are available
        missing_monitors = []
        for monitor_spec in profile.monitors:
            if monitor_spec.alias not in alias_to_output:
                edid_preview = (
                    monitor_spec.edid[:16] + "..."
                    if len(monitor_spec.edid) > 16
                    else monitor_spec.edid
                )
                missing_monitors.append(f"{monitor_spec.alias} (EDID: {edid_preview})")

        if missing_monitors:
            error_msg = f"Required monitors not detected: {', '.join(missing_monitors)}"
            raise ProfileValidationError(profile_name, [error_msg])

        # Resolve display configs from aliases to actual output names
        resolved_configs = []

        for alias, config in profile.displays.items():
            if alias not in alias_to_output:
                # Skip displays with missing monitors (warning already logged during validation)
                continue

            # Create resolved config with actual output name
            resolved_config = DisplayConfig(
                output=alias_to_output[alias],
                enabled=config.enabled,
                resolution=config.resolution,
                position=config.position,
                rotation=config.rotation,
                scale=config.scale,
                primary=config.primary,
            )
            resolved_configs.append(resolved_config)

        return ResolvedProfile(
            profile=profile,
            monitors=monitors,
            alias_to_output=alias_to_output,
            display_configs=resolved_configs,
        )

    def plan(self, profile_name: str) -> PlanResult:
        """Generate execution plan without applying.

        Args:
            profile_name: Name of profile to plan

        Returns:
            PlanResult with resolved profile and validation

        Raises:
            ProfileNotFoundError: If profile doesn't exist
            ProfileValidationError: If profile is invalid or required monitors missing
        """
        resolved = self.resolve_profile(profile_name)

        # Re-validate to get warnings (resolve_profile only raises on errors)
        validation = self.profile.validate_profile(resolved.profile)

        return PlanResult(resolved=resolved, validation=validation)
