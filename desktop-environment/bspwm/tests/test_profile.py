"""Tests for profile loading and validation."""

import unittest
from pathlib import Path
import tempfile
import yaml

from lib.profile import (
    ProfileService,
    Profile,
    MonitorDetection,
    LaptopDetection,
    DisplayConfig,
    WindowManagerConfig,
    UIConfig,
    PolybarConfig,
    ValidationResult,
)
from lib.display import Monitor
from lib.exceptions import ProfileNotFoundError, ProfileValidationError


class TestProfileService(unittest.TestCase):
    """Test ProfileService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use actual profiles directory for integration tests
        self.profiles_dir = Path(__file__).parent.parent / "profiles"
        self.service = ProfileService(self.profiles_dir)

    def test_load_personal_solo_profile(self):
        """Test loading personal-solo profile."""
        profile = self.service.load_profile("personal-solo")

        self.assertEqual(profile.name, "personal-solo")
        self.assertEqual(profile.description, "Personal laptop with built-in display only")
        self.assertIsNotNone(profile.laptop)
        self.assertEqual(profile.laptop.output, "eDP-1")
        self.assertEqual(profile.laptop.alias, "laptop")
        self.assertEqual(len(profile.monitors), 0)

    def test_load_nonexistent_profile(self):
        """Test loading a profile that doesn't exist."""
        with self.assertRaises(ProfileNotFoundError):
            self.service.load_profile("nonexistent-profile")

    def test_validate_valid_profile(self):
        """Test validation of a valid profile."""
        profile = self.service.load_profile("personal-solo")
        result = self.service.validate_profile(profile)

        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_validate_missing_name(self):
        """Test validation fails with missing name."""
        profile = Profile(
            name="",
            description="Test",
            monitors=[],
            laptop=LaptopDetection(output="eDP-1", alias="laptop"),
            displays={"laptop": DisplayConfig(output="laptop")},
            window_manager=WindowManagerConfig(
                monitor_order=["laptop"],
                workspaces={"laptop": [1, 2, 3]},
            ),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertIn("Profile name cannot be empty", result.errors)

    def test_validate_no_monitors(self):
        """Test validation fails with no monitors or laptop."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[],
            laptop=None,
            displays={},
            window_manager=WindowManagerConfig(monitor_order=[], workspaces={}),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(
            any("must specify at least one monitor or laptop display" in e for e in result.errors)
        )

    def test_validate_invalid_display_alias(self):
        """Test validation fails when display references unknown alias."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[],
            laptop=LaptopDetection(output="eDP-1", alias="laptop"),
            displays={
                "laptop": DisplayConfig(
                    output="laptop", enabled=True, resolution="1920x1080", position="0x0"
                ),
                "unknown": DisplayConfig(
                    output="unknown", enabled=True, resolution="1920x1080", position="0x0"
                ),
            },
            window_manager=WindowManagerConfig(
                monitor_order=["laptop"],
                workspaces={"laptop": [1, 2, 3]},
            ),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("doesn't match any monitor alias" in e for e in result.errors))

    def test_validate_enabled_display_missing_resolution(self):
        """Test validation fails when enabled display missing resolution."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[],
            laptop=LaptopDetection(output="eDP-1", alias="laptop"),
            displays={
                "laptop": DisplayConfig(
                    output="laptop",
                    enabled=True,
                    resolution=None,  # Missing!
                    position="0x0",
                )
            },
            window_manager=WindowManagerConfig(
                monitor_order=["laptop"],
                workspaces={"laptop": [1, 2, 3]},
            ),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("resolution required when enabled" in e for e in result.errors))

    def test_validate_enabled_display_missing_position(self):
        """Test validation fails when enabled display missing position."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[],
            laptop=LaptopDetection(output="eDP-1", alias="laptop"),
            displays={
                "laptop": DisplayConfig(
                    output="laptop",
                    enabled=True,
                    resolution="1920x1080",
                    position=None,  # Missing!
                )
            },
            window_manager=WindowManagerConfig(
                monitor_order=["laptop"],
                workspaces={"laptop": [1, 2, 3]},
            ),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("position required when enabled" in e for e in result.errors))

    def test_validate_invalid_rotation(self):
        """Test validation fails with invalid rotation."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[],
            laptop=LaptopDetection(output="eDP-1", alias="laptop"),
            displays={
                "laptop": DisplayConfig(
                    output="laptop",
                    enabled=True,
                    resolution="1920x1080",
                    position="0x0",
                    rotation="invalid",
                )
            },
            window_manager=WindowManagerConfig(
                monitor_order=["laptop"],
                workspaces={"laptop": [1, 2, 3]},
            ),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("invalid rotation" in e for e in result.errors))

    def test_validate_multiple_primary_displays(self):
        """Test validation fails with multiple primary displays."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[
                MonitorDetection(edid="abc123", alias="primary"),
                MonitorDetection(edid="def456", alias="secondary"),
            ],
            laptop=None,
            displays={
                "primary": DisplayConfig(
                    output="primary",
                    enabled=True,
                    resolution="1920x1080",
                    position="0x0",
                    primary=True,
                ),
                "secondary": DisplayConfig(
                    output="secondary",
                    enabled=True,
                    resolution="1920x1080",
                    position="1920x0",
                    primary=True,  # Duplicate!
                ),
            },
            window_manager=WindowManagerConfig(
                monitor_order=["primary", "secondary"],
                workspaces={"primary": [1, 2], "secondary": [3, 4]},
            ),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Multiple primary displays" in e for e in result.errors))

    def test_validate_invalid_monitor_order_alias(self):
        """Test validation fails when monitor_order references unknown alias."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[],
            laptop=LaptopDetection(output="eDP-1", alias="laptop"),
            displays={
                "laptop": DisplayConfig(
                    output="laptop",
                    enabled=True,
                    resolution="1920x1080",
                    position="0x0",
                )
            },
            window_manager=WindowManagerConfig(
                monitor_order=["laptop", "unknown"],  # Invalid reference
                workspaces={"laptop": [1, 2, 3]},
            ),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("monitor_order references unknown alias" in e for e in result.errors))

    def test_validate_invalid_workspaces_alias(self):
        """Test validation fails when workspaces references unknown alias."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[],
            laptop=LaptopDetection(output="eDP-1", alias="laptop"),
            displays={
                "laptop": DisplayConfig(
                    output="laptop",
                    enabled=True,
                    resolution="1920x1080",
                    position="0x0",
                )
            },
            window_manager=WindowManagerConfig(
                monitor_order=["laptop"],
                workspaces={
                    "laptop": [1, 2, 3],
                    "unknown": [4, 5, 6],  # Invalid reference
                },
            ),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("workspaces references unknown alias" in e for e in result.errors))

    def test_validate_duplicate_workspace_numbers(self):
        """Test validation fails with duplicate workspace numbers."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[
                MonitorDetection(edid="abc123", alias="primary"),
                MonitorDetection(edid="def456", alias="secondary"),
            ],
            laptop=None,
            displays={
                "primary": DisplayConfig(
                    output="primary",
                    enabled=True,
                    resolution="1920x1080",
                    position="0x0",
                ),
                "secondary": DisplayConfig(
                    output="secondary",
                    enabled=True,
                    resolution="1920x1080",
                    position="1920x0",
                ),
            },
            window_manager=WindowManagerConfig(
                monitor_order=["primary", "secondary"],
                workspaces={
                    "primary": [1, 2, 3],
                    "secondary": [3, 4, 5],  # 3 is duplicate
                },
            ),
            ui=UIConfig(),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Duplicate workspace numbers" in e for e in result.errors))

    def test_validate_invalid_ui_bar_alias(self):
        """Test validation fails when UI bar references unknown alias."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[],
            laptop=LaptopDetection(output="eDP-1", alias="laptop"),
            displays={
                "laptop": DisplayConfig(
                    output="laptop",
                    enabled=True,
                    resolution="1920x1080",
                    position="0x0",
                )
            },
            window_manager=WindowManagerConfig(
                monitor_order=["laptop"],
                workspaces={"laptop": [1, 2, 3]},
            ),
            ui=UIConfig(
                bars=[
                    PolybarConfig(monitor="unknown")  # Invalid reference
                ]
            ),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("UI bar references unknown monitor alias" in e for e in result.errors))

    def test_validate_invalid_ui_bar_orientation(self):
        """Test validation fails with invalid UI bar orientation."""
        profile = Profile(
            name="test",
            description="Test",
            monitors=[],
            laptop=LaptopDetection(output="eDP-1", alias="laptop"),
            displays={
                "laptop": DisplayConfig(
                    output="laptop",
                    enabled=True,
                    resolution="1920x1080",
                    position="0x0",
                )
            },
            window_manager=WindowManagerConfig(
                monitor_order=["laptop"],
                workspaces={"laptop": [1, 2, 3]},
            ),
            ui=UIConfig(bars=[PolybarConfig(monitor="laptop", orientation="invalid")]),
        )

        result = self.service.validate_profile(profile)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("invalid orientation" in e for e in result.errors))

    def test_list_profiles(self):
        """Test listing available profiles."""
        profiles = self.service.list_profiles()
        self.assertIn("personal-solo", profiles)
        self.assertIsInstance(profiles, list)


class TestProfileMatching(unittest.TestCase):
    """Test profile matching functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test profiles
        self.temp_dir = tempfile.mkdtemp()
        self.profiles_dir = Path(self.temp_dir)
        self.service = ProfileService(self.profiles_dir)

        # Create test profiles
        self._create_laptop_only_profile()
        self._create_dual_monitor_profile()
        self._create_triple_monitor_profile()

    def tearDown(self):
        """Clean up temporary directory."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def _create_laptop_only_profile(self):
        """Create laptop-only profile for testing."""
        profile_data = {
            "name": "laptop-only",
            "description": "Laptop display only",
            "detection": {
                "laptop": {"output": "eDP-1", "alias": "laptop", "edid": "laptop_edid_abc"},
                "monitors": [],
            },
            "display": {
                "laptop": {
                    "enabled": True,
                    "resolution": "1920x1080",
                    "position": "0x0",
                    "primary": True,
                }
            },
            "window_manager": {
                "monitor_order": ["laptop"],
                "workspaces": {"laptop": [1, 2, 3]},
            },
            "ui": {"bars": [{"monitor": "laptop"}]},
        }

        with open(self.profiles_dir / "laptop-only.yaml", "w") as f:
            yaml.dump(profile_data, f)

    def _create_dual_monitor_profile(self):
        """Create dual monitor profile for testing."""
        profile_data = {
            "name": "dual-monitor",
            "description": "Laptop + External monitor",
            "detection": {
                "laptop": {"output": "eDP-1", "alias": "laptop", "edid": "laptop_edid_abc"},
                "monitors": [
                    {
                        "edid": "external_monitor_edid_123",
                        "alias": "primary",
                        "manufacturer": "Dell",
                    }
                ],
            },
            "display": {
                "laptop": {"enabled": False},
                "primary": {
                    "enabled": True,
                    "resolution": "2560x1440",
                    "position": "0x0",
                    "primary": True,
                },
            },
            "window_manager": {
                "monitor_order": ["primary"],
                "workspaces": {"primary": [1, 2, 3]},
            },
            "ui": {"bars": [{"monitor": "primary"}]},
        }

        with open(self.profiles_dir / "dual-monitor.yaml", "w") as f:
            yaml.dump(profile_data, f)

    def _create_triple_monitor_profile(self):
        """Create triple monitor profile for testing."""
        profile_data = {
            "name": "triple-monitor",
            "description": "Laptop + Two external monitors",
            "detection": {
                "laptop": {"output": "eDP-1", "alias": "laptop", "edid": "laptop_edid_abc"},
                "monitors": [
                    {
                        "edid": "external_monitor_edid_123",
                        "alias": "primary",
                        "manufacturer": "Dell",
                    },
                    {
                        "edid": "external_monitor_edid_456",
                        "alias": "secondary",
                        "manufacturer": "Acer",
                    },
                ],
            },
            "display": {
                "laptop": {"enabled": False},
                "primary": {
                    "enabled": True,
                    "resolution": "2560x1440",
                    "position": "0x0",
                    "primary": True,
                },
                "secondary": {
                    "enabled": True,
                    "resolution": "3840x2160",
                    "position": "2560x0",
                    "rotation": "left",
                },
            },
            "window_manager": {
                "monitor_order": ["primary", "secondary"],
                "workspaces": {"primary": [1, 2, 3], "secondary": [4, 5, 6]},
            },
            "ui": {
                "bars": [
                    {"monitor": "primary"},
                    {"monitor": "secondary", "orientation": "portrait"},
                ]
            },
        }

        with open(self.profiles_dir / "triple-monitor.yaml", "w") as f:
            yaml.dump(profile_data, f)

    def test_match_laptop_only(self):
        """Test matching with only laptop detected."""
        detected = [
            Monitor(
                output="eDP-1",
                edid="laptop_edid_abc",
                manufacturer="LGD",
                model="Generic",
                resolution="1920x1080",
                connected=True,
            )
        ]

        matches = self.service.match_profiles(detected)

        # Should match laptop-only profile
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "laptop-only")
        self.assertEqual(matches[0][1], 100.0)  # Score: laptop match

    def test_match_dual_monitor(self):
        """Test matching with laptop + one external monitor."""
        detected = [
            Monitor(
                output="eDP-1",
                edid="laptop_edid_abc",
                manufacturer="LGD",
                model="Generic",
                resolution="1920x1080",
                connected=True,
            ),
            Monitor(
                output="DP-1",
                edid="external_monitor_edid_123",
                manufacturer="Dell",
                model="Generic",
                resolution="2560x1440",
                connected=True,
            ),
        ]

        matches = self.service.match_profiles(detected)

        # Should match both laptop-only and dual-monitor profiles
        # dual-monitor should score higher
        self.assertGreaterEqual(len(matches), 1)

        profile_names = [m[0] for m in matches]
        self.assertIn("dual-monitor", profile_names)

        # dual-monitor should be first (highest score)
        self.assertEqual(matches[0][0], "dual-monitor")
        self.assertEqual(matches[0][1], 200.0)  # Score: 100 (external) + 100 (laptop)

    def test_match_triple_monitor(self):
        """Test matching with laptop + two external monitors."""
        detected = [
            Monitor(
                output="eDP-1",
                edid="laptop_edid_abc",
                manufacturer="LGD",
                model="Generic",
                resolution="1920x1080",
                connected=True,
            ),
            Monitor(
                output="DP-1",
                edid="external_monitor_edid_123",
                manufacturer="Dell",
                model="Generic",
                resolution="2560x1440",
                connected=True,
            ),
            Monitor(
                output="DP-2",
                edid="external_monitor_edid_456",
                manufacturer="Acer",
                model="Generic",
                resolution="3840x2160",
                connected=True,
            ),
        ]

        matches = self.service.match_profiles(detected)

        # All three profiles could match
        profile_names = [m[0] for m in matches]
        self.assertIn("triple-monitor", profile_names)

        # triple-monitor should be first (highest score)
        self.assertEqual(matches[0][0], "triple-monitor")
        self.assertEqual(matches[0][1], 300.0)  # Score: 100 (ext1) + 100 (ext2) + 100 (laptop)

    def test_match_missing_required_monitor(self):
        """Test no match when required monitor is missing."""
        detected = [
            Monitor(
                output="eDP-1",
                edid="laptop_edid_abc",
                manufacturer="LGD",
                model="Generic",
                resolution="1920x1080",
                connected=True,
            )
        ]

        matches = self.service.match_profiles(detected)

        # Should only match laptop-only, not dual or triple
        profile_names = [m[0] for m in matches]
        self.assertNotIn("dual-monitor", profile_names)
        self.assertNotIn("triple-monitor", profile_names)

    def test_match_extra_monitors_penalty(self):
        """Test penalty for extra monitors not in profile."""
        detected = [
            Monitor(
                output="eDP-1",
                edid="laptop_edid_abc",
                manufacturer="LGD",
                model="Generic",
                resolution="1920x1080",
                connected=True,
            ),
            Monitor(
                output="DP-1",
                edid="external_monitor_edid_123",
                manufacturer="Dell",
                model="Generic",
                resolution="2560x1440",
                connected=True,
            ),
            Monitor(
                output="DP-2",
                edid="extra_monitor_not_in_profile",
                manufacturer="Samsung",
                model="Generic",
                resolution="1920x1080",
                connected=True,
            ),
        ]

        matches = self.service.match_profiles(detected)

        # Find dual-monitor in matches
        dual_match = next((m for m in matches if m[0] == "dual-monitor"), None)
        self.assertIsNotNone(dual_match)

        # Score should be: 100 (external) + 100 (laptop) - 10 (extra)
        self.assertEqual(dual_match[1], 190.0)

    def test_match_no_detected_monitors(self):
        """Test matching with no detected monitors."""
        detected = []

        matches = self.service.match_profiles(detected)

        # No profiles should match
        self.assertEqual(len(matches), 0)

    def test_match_disconnected_monitors_ignored(self):
        """Test that disconnected monitors are ignored."""
        detected = [
            Monitor(
                output="eDP-1",
                edid="laptop_edid_abc",
                manufacturer="LGD",
                model="Generic",
                resolution="1920x1080",
                connected=True,
            ),
            Monitor(
                output="DP-1",
                edid="external_monitor_edid_123",
                manufacturer="Dell",
                model="Generic",
                resolution="2560x1440",
                connected=False,  # Not connected
            ),
        ]

        matches = self.service.match_profiles(detected)

        # Should only match laptop-only
        profile_names = [m[0] for m in matches]
        self.assertIn("laptop-only", profile_names)
        self.assertNotIn("dual-monitor", profile_names)

    def test_match_monitors_without_edid_ignored(self):
        """Test that monitors without EDID are ignored."""
        detected = [
            Monitor(
                output="eDP-1",
                edid="laptop_edid_abc",
                manufacturer="LGD",
                model="Generic",
                resolution="1920x1080",
                connected=True,
            ),
            Monitor(
                output="DP-1",
                edid="",  # No EDID
                manufacturer="Unknown",
                model="Unknown",
                resolution="unknown",
                connected=True,
            ),
        ]

        matches = self.service.match_profiles(detected)

        # Should only match laptop-only
        profile_names = [m[0] for m in matches]
        self.assertIn("laptop-only", profile_names)
        self.assertNotIn("dual-monitor", profile_names)


if __name__ == "__main__":
    unittest.main()
