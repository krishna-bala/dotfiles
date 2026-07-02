"""Validation of the tracked profiles/ directory.

The tracked profiles are production config for real hardware (their EDID
pins are hashes of real monitors), so every other test runs against the
synthetic tests/fixtures/profiles instead. This file is the one deliberate
exception: it checks that the real profiles still parse, merge with
defaults.yaml, and pass validation, keeping the "my actual configs work"
guarantee the suite used to get implicitly.
"""

import unittest
from pathlib import Path

from lib.profile import ProfileService

TRACKED_PROFILES = Path(__file__).parent.parent / "profiles"


class TestTrackedProfiles(unittest.TestCase):
    def test_every_tracked_profile_loads_and_validates(self):
        service = ProfileService(TRACKED_PROFILES)
        names = service.list_profiles()
        self.assertTrue(names, f"no profiles found in {TRACKED_PROFILES}")

        for name in names:
            with self.subTest(profile=name):
                profile = service.load_profile(name)
                result = service.validate_profile(profile)
                self.assertTrue(
                    result.is_valid, f"profile {name} failed validation: {result.errors}"
                )

    def test_every_edid_pin_is_a_truncated_hash(self):
        """EDID pins must be 16 lowercase hex chars (lib/edid.py hash keys);
        anything else means a raw EDID or serial leaked into a public file."""
        service = ProfileService(TRACKED_PROFILES)
        for name in service.list_profiles():
            profile = service.load_profile(name)
            pins = [m.edid for m in profile.monitors]
            if profile.laptop and profile.laptop.edid:
                pins.append(profile.laptop.edid)
            for pin in pins:
                with self.subTest(profile=name, edid=pin):
                    self.assertRegex(pin, r"^[0-9a-f]{16}$")


if __name__ == "__main__":
    unittest.main()
