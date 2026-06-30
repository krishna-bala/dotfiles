"""Window-merge policies for topology shrinks.

When a stale monitor's desktops can't all map onto a surviving monitor's desktop
list (going from 20 desktops to 10, say), a policy decides where each window
goes. Policies are pure: they get a window id, the source desktop's name, and
the candidate target desktop names — they return one target name.

Default is PreserveByName: workspace 5 stays workspace 5 across topology
changes; overflow falls to the first desktop. Swap policies to change that
behaviour without touching the reconciler.
"""

from typing import Protocol, Tuple


class MergePolicy(Protocol):
    """Decide where a window goes when its source desktop won't survive."""

    def assign(
        self,
        window_id: str,
        source_desktop_name: str,
        target_desktop_names: Tuple[str, ...],
    ) -> str:
        ...


def _require_targets(target_desktop_names: Tuple[str, ...]) -> None:
    if not target_desktop_names:
        raise ValueError("merge policy needs at least one candidate target desktop")


class PreserveByName:
    """Same name on the target → there. Otherwise → first target.

    Matches the user's mental model that "workspace N is workspace N" across
    topology changes. Names that don't survive the shrink pile onto the first
    target — a deliberate choice, not random.
    """

    def assign(
        self,
        window_id: str,
        source_desktop_name: str,
        target_desktop_names: Tuple[str, ...],
    ) -> str:
        _require_targets(target_desktop_names)
        if source_desktop_name in target_desktop_names:
            return source_desktop_name
        return target_desktop_names[0]


class SquashToFirst:
    """All windows pile onto the first target desktop."""

    def assign(
        self,
        window_id: str,
        source_desktop_name: str,
        target_desktop_names: Tuple[str, ...],
    ) -> str:
        _require_targets(target_desktop_names)
        return target_desktop_names[0]


class SpilloverModulo:
    """Distribute by parsing the source name as int, mod len(targets)."""

    def assign(
        self,
        window_id: str,
        source_desktop_name: str,
        target_desktop_names: Tuple[str, ...],
    ) -> str:
        _require_targets(target_desktop_names)
        try:
            n = int(source_desktop_name)
        except ValueError:
            return target_desktop_names[0]
        return target_desktop_names[n % len(target_desktop_names)]
