"""Tests for safety service."""

import unittest
import json
from pathlib import Path
from datetime import datetime

from lib.safety import SafetyService, StateSnapshot


class TestStateSnapshot(unittest.TestCase):
    """Test StateSnapshot class."""

    def test_to_dict(self):
        """Test converting snapshot to dictionary."""
        snapshot = StateSnapshot(
            timestamp="2025-01-01T12:00:00",
            xrandr_state="Screen 0: minimum 8 x 8, current 1920 x 1080",
            bspwm_monitors="eDP-1\n",
            bspwm_desktops="1\n2\n3\n4\n5\n",
        )

        data = snapshot.to_dict()

        self.assertEqual(data["timestamp"], "2025-01-01T12:00:00")
        self.assertEqual(data["xrandr_state"], "Screen 0: minimum 8 x 8, current 1920 x 1080")
        self.assertEqual(data["bspwm_monitors"], "eDP-1\n")
        self.assertEqual(data["bspwm_desktops"], "1\n2\n3\n4\n5\n")


class TestSafetyService(unittest.TestCase):
    """Test SafetyService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use temp directory for snapshots
        import tempfile

        self.temp_dir = Path(tempfile.mkdtemp())
        self.service = SafetyService(snapshot_dir=self.temp_dir)

    def tearDown(self):
        """Clean up temp directory."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_snapshot_dir_created(self):
        """Test that snapshot directory is created."""
        self.assertTrue(self.service.snapshot_dir.exists())
        self.assertTrue(self.service.snapshot_dir.is_dir())

    def test_save_snapshot(self):
        """Test saving a snapshot to disk."""
        snapshot = StateSnapshot(
            timestamp=datetime.now().isoformat(),
            xrandr_state="test xrandr output",
        )

        filepath = self.service.save_snapshot(snapshot)

        # Check file was created
        self.assertTrue(filepath.exists())
        self.assertTrue(filepath.name.startswith("snapshot_"))
        self.assertTrue(filepath.name.endswith(".json"))

        # Check content
        with open(filepath) as f:
            data = json.load(f)

        self.assertEqual(data["xrandr_state"], "test xrandr output")

    def test_save_rollback_text(self):
        """Test saving rollback text file."""
        snapshot = StateSnapshot(
            timestamp=datetime.now().isoformat(),
            xrandr_state="test xrandr output for rollback",
        )

        filepath = self.service.save_rollback_text(snapshot)

        # Check file was created
        self.assertTrue(filepath.exists())
        self.assertTrue(filepath.name.startswith("rollback_"))
        self.assertTrue(filepath.name.endswith(".txt"))

        # Check content contains xrandr state
        with open(filepath) as f:
            content = f.read()

        self.assertIn("test xrandr output for rollback", content)
        self.assertIn("# Display Configuration (xrandr)", content)

    def test_save_rollback_text_with_bspwm(self):
        """Test saving rollback text file with BSPWM state."""
        snapshot = StateSnapshot(
            timestamp=datetime.now().isoformat(),
            xrandr_state="test xrandr output",
            bspwm_monitors="eDP-1\n",
            bspwm_desktops="1\n2\n3\n4\n5\n",
        )

        filepath = self.service.save_rollback_text(snapshot)

        # Check file was created
        self.assertTrue(filepath.exists())

        # Check content includes BSPWM restoration command
        with open(filepath) as f:
            content = f.read()

        self.assertIn("test xrandr output", content)
        self.assertIn("# Window Manager Configuration (BSPWM)", content)
        self.assertIn("bspc monitor eDP-1 -d 1 2 3 4 5", content)

    def test_rollback_multi_monitor_restoration(self):
        """Per-monitor desktop capture yields a restore line for every monitor."""
        from datetime import datetime

        snapshot = StateSnapshot(
            timestamp=datetime.now().isoformat(),
            xrandr_state="test xrandr output",
            bspwm_monitors="DP-0\nDP-3\n",
            bspwm_desktops="1\n2\n3\n4\n",
            desktops_by_monitor={"DP-0": ["1", "2"], "DP-3": ["3", "4"]},
        )

        filepath = self.service.save_rollback_text(snapshot)
        with open(filepath) as f:
            content = f.read()

        self.assertIn("bspc monitor DP-0 -d 1 2", content)
        self.assertIn("bspc monitor DP-3 -d 3 4", content)

    def test_prune_keeps_newest_snapshots(self):
        """The snapshot directory is bounded to KEEP files per kind."""
        for i in range(25):
            (self.service.snapshot_dir / f"snapshot_20260101_{i:06d}.json").touch()
            (self.service.snapshot_dir / f"rollback_20260101_{i:06d}.txt").touch()

        self.service._prune()

        snapshots = sorted(self.service.snapshot_dir.glob("snapshot_*.json"))
        rollbacks = sorted(self.service.snapshot_dir.glob("rollback_*.txt"))
        self.assertEqual(len(snapshots), SafetyService.KEEP)
        self.assertEqual(len(rollbacks), SafetyService.KEEP)
        # Oldest were removed, newest kept
        self.assertEqual(snapshots[-1].name, "snapshot_20260101_000024.json")
        self.assertEqual(snapshots[0].name, "snapshot_20260101_000005.json")


if __name__ == "__main__":
    unittest.main()
