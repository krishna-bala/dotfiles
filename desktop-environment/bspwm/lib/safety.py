"""Safety service for state snapshots and rollback."""

import json
import os
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class StateSnapshot:
    """Captured system state for rollback."""

    timestamp: str  # ISO format timestamp
    xrandr_state: str  # Current xrandr output
    bspwm_monitors: Optional[str] = None  # Current BSPWM monitors
    bspwm_desktops: Optional[str] = None  # Current BSPWM desktops (flat)
    desktops_by_monitor: Optional[Dict[str, List[str]]] = None

    @classmethod
    def capture(cls) -> "StateSnapshot":
        """Capture current system state.

        Returns:
            StateSnapshot with current xrandr and BSPWM state

        Raises:
            subprocess.CalledProcessError: If state capture fails
        """
        # Capture xrandr state
        xrandr_result = subprocess.run(
            ["xrandr", "--current"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Capture BSPWM state (may not be running)
        bspwm_monitors = None
        bspwm_desktops = None
        desktops_by_monitor = None

        try:
            monitors_result = subprocess.run(
                ["bspc", "query", "--monitors", "--names"],
                capture_output=True,
                text=True,
                check=True,
            )
            bspwm_monitors = monitors_result.stdout

            desktops_result = subprocess.run(
                ["bspc", "query", "--desktops", "--names"],
                capture_output=True,
                text=True,
                check=True,
            )
            bspwm_desktops = desktops_result.stdout

            # Per-monitor desktop lists, so rollback can restore any topology
            desktops_by_monitor = {}
            for monitor in bspwm_monitors.strip().split("\n"):
                monitor = monitor.strip()
                if not monitor:
                    continue
                per_mon = subprocess.run(
                    ["bspc", "query", "--desktops", "--names", "--monitor", monitor],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                desktops_by_monitor[monitor] = [
                    d.strip() for d in per_mon.stdout.strip().split("\n") if d.strip()
                ]
        except (subprocess.CalledProcessError, FileNotFoundError):
            # BSPWM not running or bspc not available - skip BSPWM state
            pass

        return cls(
            timestamp=datetime.now().isoformat(),
            xrandr_state=xrandr_result.stdout,
            bspwm_monitors=bspwm_monitors,
            bspwm_desktops=bspwm_desktops,
            desktops_by_monitor=desktops_by_monitor,
        )

    def to_dict(self) -> dict:
        """Convert snapshot to dictionary for serialization.

        Returns:
            Dictionary representation of snapshot
        """
        return asdict(self)


class SafetyService:
    """Service for managing state snapshots and rollback."""

    def __init__(self, snapshot_dir: Optional[Path] = None):
        """Initialize safety service.

        Args:
            snapshot_dir: Directory to store snapshots (default: /tmp/monitor-manager-snapshots)
        """
        default_dir = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "bspwm-monitor-manager" / "snapshots"
        self.snapshot_dir = snapshot_dir or default_dir
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self) -> StateSnapshot:
        """Create a snapshot of current state.

        Returns:
            StateSnapshot object

        Raises:
            subprocess.CalledProcessError: If state capture fails
        """
        return StateSnapshot.capture()

    def save_snapshot(self, snapshot: StateSnapshot) -> Path:
        """Save snapshot to disk.

        Args:
            snapshot: Snapshot to save

        Returns:
            Path to saved snapshot file
        """
        # Create filename with timestamp
        timestamp = datetime.fromisoformat(snapshot.timestamp)
        filename = f"snapshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.snapshot_dir / filename

        # Save as JSON
        with open(filepath, "w") as f:
            json.dump(snapshot.to_dict(), f, indent=2)

        self._prune()
        return filepath

    def create_and_save_snapshot(self) -> tuple[StateSnapshot, Path]:
        """Create and save a snapshot in one operation.

        Returns:
            Tuple of (snapshot, filepath)

        Raises:
            subprocess.CalledProcessError: If state capture fails
        """
        snapshot = self.create_snapshot()
        filepath = self.save_snapshot(snapshot)
        return snapshot, filepath

    def save_rollback_text(self, snapshot: StateSnapshot) -> Path:
        """Save system state as plain text for manual rollback.

        Args:
            snapshot: Snapshot containing system state

        Returns:
            Path to text file
        """
        # Create filename with timestamp
        timestamp = datetime.fromisoformat(snapshot.timestamp)
        filename = f"rollback_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = self.snapshot_dir / filename

        # Save state as text with instructions
        with open(filepath, "w") as f:
            f.write(f"# System State Rollback Information\n")
            f.write(f"# Captured: {snapshot.timestamp}\n\n")

            # Xrandr state
            f.write("# Display Configuration (xrandr)\n")
            f.write("# Current xrandr output:\n")
            f.write(snapshot.xrandr_state)
            f.write("\n")

            # BSPWM state (if captured)
            if snapshot.bspwm_monitors and snapshot.bspwm_desktops:
                f.write("\n# Window Manager Configuration (BSPWM)\n")
                f.write("# Monitors:\n")
                for monitor in snapshot.bspwm_monitors.strip().split("\n"):
                    if monitor:
                        f.write(f"#   {monitor}\n")

                f.write("# Desktops:\n")
                for desktop in snapshot.bspwm_desktops.strip().split("\n"):
                    if desktop:
                        f.write(f"#   {desktop}\n")

                f.write("\n# To restore BSPWM configuration, run:\n")
                if snapshot.desktops_by_monitor:
                    for monitor, desktops in snapshot.desktops_by_monitor.items():
                        if desktops:
                            f.write(f"bspc monitor {monitor} -d {' '.join(desktops)}\n")
                else:
                    # Older snapshots only have the flat desktop list, which can
                    # be attributed to a monitor only in the single-monitor case
                    monitors = [
                        m.strip() for m in snapshot.bspwm_monitors.strip().split("\n") if m.strip()
                    ]
                    desktops = [
                        d.strip() for d in snapshot.bspwm_desktops.strip().split("\n") if d.strip()
                    ]
                    if len(monitors) == 1 and desktops:
                        f.write(f"bspc monitor {monitors[0]} -d {' '.join(desktops)}\n")

        self._prune()
        return filepath

    # Keep this many of each snapshot/rollback file; prune the rest oldest-first
    KEEP = 20

    def _prune(self) -> None:
        """Bound the snapshot directory: keep the newest KEEP files per kind."""
        for pattern in ("snapshot_*.json", "rollback_*.txt"):
            files = sorted(self.snapshot_dir.glob(pattern))
            for stale in files[: -self.KEEP]:
                try:
                    stale.unlink()
                except OSError:
                    pass
