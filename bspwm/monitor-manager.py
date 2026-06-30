#!/usr/bin/env python3
"""BSPWM Monitor Manager - Profile-based monitor configuration."""

import argparse
import sys
from pathlib import Path

# Add lib directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from lib.coordinator import MonitorManagerCoordinator
from lib.display import DisplayService
from lib.exceptions import (
    HardwareDetectionError,
    ProfileNotFoundError,
    ProfileValidationError,
)
from lib.executor import Executor
from lib.interactive import run_interactive_menu
from lib.preferences import StateService
from lib.probe.composite import CompositeStateProbe
from lib.profile import ProfileService
from lib.reconciler import Reconciler
from lib.renderer import Renderer
from lib.safety import SafetyService
from lib.state.desired import compile_desired


def get_coordinator() -> MonitorManagerCoordinator:
    """Get coordinator instance with services.

    Returns:
        MonitorManagerCoordinator instance
    """
    return MonitorManagerCoordinator(
        display_service=DisplayService(),
        profile_service=ProfileService(),
    )


def cmd_detect(args):
    """Detect connected monitors and display information."""
    service = DisplayService()

    try:
        monitors = service.detect_monitors()
    except HardwareDetectionError as e:
        print(f"Error detecting monitors: {e}", file=sys.stderr)
        return 1

    if not monitors:
        print("No monitors detected")
        return 0

    # Display results
    print("Detected monitors:\n")

    connected = [m for m in monitors if m.connected]
    disconnected = [m for m in monitors if not m.connected]

    # Show connected monitors first
    if connected:
        print("Connected:")
        for monitor in connected:
            print(f"  {monitor.output}")
            print(f"    Resolution: {monitor.resolution}")
            print(f"    Manufacturer: {monitor.manufacturer}")
            print(f"    Model: {monitor.model}")
            if monitor.edid:
                # Show first 32 chars of EDID with ellipsis
                edid_preview = monitor.edid[:32] + "..." if len(monitor.edid) > 32 else monitor.edid
                print(f"    EDID: {edid_preview}")
            print()

    # Show disconnected monitors
    if disconnected and args.show_disconnected:
        print("Disconnected:")
        for monitor in disconnected:
            print(f"  {monitor.output}")
        print()

    return 0


def cmd_validate(args):
    """Validate a profile against schema and optionally current hardware."""
    profile_service = ProfileService()

    try:
        # Load profile
        profile = profile_service.load_profile(args.profile)
        print(f"✓ Profile '{args.profile}' loaded successfully\n")

        # Validate schema
        validation = profile_service.validate_profile(profile)

        if validation.is_valid:
            print(f"✓ Profile '{profile.name}' is valid")
            print(f"  Description: {profile.description}")
            print(f"  Monitors required: {len(profile.monitors)}")
            if profile.laptop:
                print(f"  Laptop display: {profile.laptop.output}")

            # Show warnings if any
            if validation.warnings:
                print("\nWarnings:")
                for warning in validation.warnings:
                    print(f"  ⚠ {warning}")
            return 0
        else:
            print(f"✗ Profile '{profile.name}' has validation errors:\n")
            for error in validation.errors:
                print(f"  - {error}")
            return 1

    except (ProfileNotFoundError, ProfileValidationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_list(args):
    """List all available profiles."""
    profile_service = ProfileService()
    profiles = profile_service.list_profiles()

    if not profiles:
        print("No profiles found")
        return 0

    print("Available profiles:\n")
    for profile_name in profiles:
        try:
            profile = profile_service.load_profile(profile_name)
            print(f"  {profile.name}")
            print(f"    {profile.description}")
        except Exception as e:
            print(f"  {profile_name} (error loading: {e})")
        print()

    return 0


def cmd_match(args):
    """Match detected monitors to available profiles and show scores."""
    display_service = DisplayService()
    profile_service = ProfileService()
    state_service = StateService()

    try:
        # Detect monitors
        monitors = display_service.detect_monitors()
    except HardwareDetectionError as e:
        print(f"Error detecting monitors: {e}", file=sys.stderr)
        return 1

    if not monitors:
        print("No monitors detected")
        return 0

    # Check for default preference first
    default_profile = state_service.get_default()
    selected_profile = None
    selection_reason = None

    if default_profile:
        # Check if default is valid for current monitors
        try:
            matches = profile_service.match_profiles(monitors)
            # See if default is in the matches
            default_match = next((m for m in matches if m[0] == default_profile), None)
            if default_match:
                selected_profile = default_profile
                selection_reason = "using default"
        except Exception:
            pass  # Fall through to auto-detection

    # If no valid default, use auto-detection
    if not selected_profile:
        try:
            matches = profile_service.match_profiles(monitors)
        except Exception as e:
            print(f"Error matching profiles: {e}", file=sys.stderr)
            return 1

        if not matches:
            print("No matching profiles found", file=sys.stderr)
            print("\nTip: Create a profile that matches your current hardware configuration", file=sys.stderr)
            return 1

        selected_profile = matches[0][0]  # Best match
        selection_reason = "auto-detected"

    # --best flag: just output profile name for scripting
    if hasattr(args, 'best') and args.best:
        print(selected_profile)
        return 0

    # Regular output
    connected = [m for m in monitors if m.connected]

    print("Detected monitors:\n")
    for monitor in connected:
        print(f"  {monitor.output} - {monitor.manufacturer} {monitor.model} ({monitor.resolution})")
        if args.verbose and monitor.edid:
            print(f"    EDID: {monitor.edid[:32]}...")
    print()

    # Match profiles
    try:
        matches = profile_service.match_profiles(monitors)
    except Exception as e:
        print(f"Error matching profiles: {e}", file=sys.stderr)
        return 1

    # Display matches
    print(f"Matched profiles ({len(matches)}):\n")

    for profile_name, score, profile in matches:
        prefix = "  "
        if profile_name == selected_profile:
            prefix = "→ "

        print(f"{prefix}{profile_name} (score: {score:.0f})")
        print(f"    {profile.description}")

        if args.verbose:
            # Show requirements
            print(f"    Required monitors: {len(profile.monitors)}")
            if profile.laptop:
                print(f"    Laptop display: {profile.laptop.output}")
            print(f"    Displays configured: {len(profile.displays)}")
            print(
                f"    Workspaces: {sum(len(ws) for ws in profile.window_manager.workspaces.values())}"
            )

        print()

    # Highlight selected profile
    print(f"Best match: {selected_profile} ({selection_reason})")

    return 0


def cmd_set_default(args):
    """Set the default profile preference."""
    profile_service = ProfileService()
    state_service = StateService()

    # Validate profile exists
    try:
        profile_service.load_profile(args.profile)
    except ProfileNotFoundError:
        print(f"Error: Profile '{args.profile}' not found", file=sys.stderr)
        print("\nAvailable profiles:", file=sys.stderr)
        for name in profile_service.list_profiles():
            print(f"  {name}", file=sys.stderr)
        return 1
    except ProfileValidationError as e:
        print(f"Error: Profile '{args.profile}' is invalid: {e}", file=sys.stderr)
        return 1

    # Set default
    state_service.set_default(args.profile)
    print(f"✓ Set default profile to: {args.profile}")
    return 0


def cmd_clear_default(args):
    """Clear the default profile preference."""
    state_service = StateService()
    state_service.clear_default()
    print("✓ Cleared default profile preference")
    print("Will use auto-detection on next match")
    return 0


def cmd_plan(args):
    """Show the Plan that would be executed for a profile (dry-run).

    Probes current state, compiles the profile into a DesiredState,
    reconciles, and prints the resulting Op sequence. The same Plan that
    `apply-all` would run.
    """
    coordinator = get_coordinator()

    try:
        resolved = coordinator.resolve_profile(args.profile)
    except (ProfileNotFoundError, ProfileValidationError, HardwareDetectionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    current = CompositeStateProbe().read()
    desired = compile_desired(resolved.profile, resolved.alias_to_output)
    plan = Reconciler().plan(current, desired)

    print(f"Description: {resolved.profile.description}\n")
    print(Renderer().render(plan))

    if args.verbose:
        print("Alias Mapping:")
        for alias, output in resolved.alias_to_output.items():
            print(f"  {alias} → {output}")
        print()

    return 0


def _auto_detect_profile_name():
    """Pick the profile to apply when none was given.

    Same selection as `match --best`: the default preference wins if it
    matches current hardware, otherwise the highest-scoring match. Returns
    None (with a message on stderr) when detection fails or nothing matches.
    """
    try:
        monitors = DisplayService().detect_monitors()
    except HardwareDetectionError as e:
        print(f"Error detecting monitors: {e}", file=sys.stderr)
        return None
    if not monitors:
        print("No monitors detected", file=sys.stderr)
        return None

    try:
        matches = ProfileService().match_profiles(monitors)
    except Exception as e:
        print(f"Error matching profiles: {e}", file=sys.stderr)
        return None
    if not matches:
        print("No matching profiles found", file=sys.stderr)
        return None

    default_profile = StateService().get_default()
    if default_profile and any(m[0] == default_profile for m in matches):
        return default_profile
    return matches[0][0]


def apply_profile(profile_name=None, force=False):
    """Apply a profile via the reconciliation pipeline.

    Probe current state → compile desired → reconcile → render → execute.
    The reconciler emits an explicit Plan of ops (xrandr layout in one
    invocation, bspc desktop add/rename/remove, window moves, monitor
    remove, polybar kill/launch, wallpaper restore); the executor runs them
    in order with symbolic refs resolved to real ids at run time.

    If profile_name is None, auto-detects the best-matching profile (default
    preference if it matches current hardware, otherwise highest-scoring).
    Used by the super+alt+r keybind: re-detect topology and apply, no manual
    profile name needed.
    """
    coordinator = get_coordinator()

    profile_name = profile_name or _auto_detect_profile_name()
    if profile_name is None:
        return 1

    try:
        resolved = coordinator.resolve_profile(profile_name)
    except (ProfileNotFoundError, ProfileValidationError, HardwareDetectionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    current = CompositeStateProbe().read()
    desired = compile_desired(resolved.profile, resolved.alias_to_output)
    plan = Reconciler().plan(current, desired)

    print(f"Description: {resolved.profile.description}\n")
    print(Renderer().render(plan))

    if plan.is_noop():
        print("Already in desired state — nothing to do.")
        return 0

    if not force:
        print("Apply this plan? [y/N]: ", end="", flush=True)
        if input().strip().lower() not in ("y", "yes"):
            print("Cancelled")
            return 0

    # Snapshot for rollback. Still uses the existing text-format snapshot;
    # PR 5 will migrate this to a serialised Plan.
    safety_service = SafetyService()
    rollback_file = None
    try:
        snapshot = safety_service.create_snapshot()
        rollback_file = safety_service.save_rollback_text(snapshot)
        print(f"\nRollback snapshot saved: {rollback_file}")
    except Exception as e:
        print(f"Warning: failed to save rollback snapshot: {e}", file=sys.stderr)

    print("\nExecuting plan...")
    result = Executor().execute(plan)

    if result.succeeded():
        print(f"\n{'=' * 60}")
        print(f"✓ Applied {len(result.completed)} ops successfully")
        print(f"{'=' * 60}")
        return 0

    failed_op, failed_exc = result.failed
    print(f"\n✗ Plan failed at op {len(result.completed) + 1}/{len(plan.ops)}", file=sys.stderr)
    print(f"  Op:    {Renderer().render_op(failed_op)}", file=sys.stderr)
    print(f"  Error: {type(failed_exc).__name__}: {failed_exc}", file=sys.stderr)
    print(f"  Skipped: {len(result.skipped)} subsequent ops", file=sys.stderr)
    if rollback_file:
        print(f"  Rollback snapshot at: {rollback_file}", file=sys.stderr)
    return 1


def cmd_apply_all(args):
    """CLI wrapper around apply_profile."""
    return apply_profile(args.profile, args.force)


def cmd_interactive(args):
    """Run interactive TUI for profile selection.

    This provides a user-friendly menu for:
    - Viewing detected monitors
    - Seeing matched profiles
    - Selecting a profile
    - Choosing to plan or apply
    """
    coordinator = get_coordinator()
    profile_service = ProfileService()
    display_service = DisplayService()

    try:
        # Run interactive menu
        choice = run_interactive_menu(coordinator, profile_service, display_service)

        # Handle user's choice
        if choice.action == "cancel":
            return 0

        # User selected plan or apply
        profile_name = choice.profile_name

        if choice.action == "plan":
            # Same Plan that apply would run, rendered the same way
            print("\n" + "=" * 60)
            print("CONFIGURATION PLAN")
            print("=" * 60)

            try:
                resolved = coordinator.resolve_profile(profile_name)
            except (ProfileNotFoundError, ProfileValidationError, HardwareDetectionError) as e:
                print(f"Error: {e}", file=sys.stderr)
                return 1

            current = CompositeStateProbe().read()
            desired = compile_desired(resolved.profile, resolved.alias_to_output)
            plan = Reconciler().plan(current, desired)

            print(f"\nProfile: {resolved.profile.name}")
            print(f"Description: {resolved.profile.description}\n")
            print(Renderer().render(plan))
            return 0

        elif choice.action == "apply":
            # Confirmation already happened in the interactive menu
            return apply_profile(profile_name, force=True)

    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Install simple-term-menu with: uv add simple-term-menu", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BSPWM Monitor Manager - Profile-based monitor configuration"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # detect command
    detect_parser = subparsers.add_parser(
        "detect",
        help="Detect connected monitors (read-only)",
    )
    detect_parser.add_argument(
        "--show-disconnected",
        action="store_true",
        help="Show disconnected monitors",
    )
    detect_parser.set_defaults(func=cmd_detect)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a profile (read-only)",
    )
    validate_parser.add_argument(
        "--profile",
        required=True,
        help="Profile name to validate",
    )
    validate_parser.set_defaults(func=cmd_validate)

    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List all available profiles (read-only)",
    )
    list_parser.set_defaults(func=cmd_list)

    # match command
    match_parser = subparsers.add_parser(
        "match",
        help="Match detected monitors to profiles and show scores (read-only)",
    )
    match_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed information about matched profiles",
    )
    match_parser.add_argument(
        "--best",
        action="store_true",
        help="Output only the profile name (for scripting)",
    )
    match_parser.set_defaults(func=cmd_match)

    # set-default command
    set_default_parser = subparsers.add_parser(
        "set-default",
        help="Set default profile preference (persists across reboots)",
    )
    set_default_parser.add_argument(
        "--profile",
        required=True,
        help="Profile name to set as default",
    )
    set_default_parser.set_defaults(func=cmd_set_default)

    # clear-default command
    clear_default_parser = subparsers.add_parser(
        "clear-default",
        help="Clear default profile preference (use auto-detection)",
    )
    clear_default_parser.set_defaults(func=cmd_clear_default)

    # plan command
    plan_parser = subparsers.add_parser(
        "plan",
        help="Show what configuration would be applied (dry-run)",
    )
    plan_parser.add_argument(
        "--profile",
        required=True,
        help="Profile name to plan",
    )
    plan_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed information including alias mappings",
    )
    plan_parser.set_defaults(func=cmd_plan)

    # apply-all command
    apply_all_parser = subparsers.add_parser(
        "apply-all",
        help="Apply a profile via the reconciliation pipeline",
    )
    apply_all_parser.add_argument(
        "--profile",
        default=None,
        help="Profile name to apply (default: auto-detect best match)",
    )
    apply_all_parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )
    apply_all_parser.set_defaults(func=cmd_apply_all)

    # interactive command
    interactive_parser = subparsers.add_parser(
        "interactive",
        help="Interactive TUI for profile selection and application",
    )
    interactive_parser.set_defaults(func=cmd_interactive)

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
