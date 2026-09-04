"""The profile search path: tracked profiles plus an overlay directory.

ProfileService reads from a list of directories. A later directory shadows
an earlier one on a name clash and contributes new names, and defaults.yaml
comes from the first directory that has one - so a private overlay can add
machine-specific profiles beside the public ones without editing the repo.
"""

from pathlib import Path

import pytest

from monitor_manager.profile import ProfileService

MINIMAL = """\
name: {name}
description: {desc}
detection:
  laptop:
    output: eDP-1
    alias: laptop
  monitors: []
display:
  laptop:
    enabled: true
    resolution: "1920x1080"
    position: "0x0"
    primary: true
window_manager:
  monitor_order: [laptop]
  workspaces:
    laptop: [1, 2, 3]
ui:
  bars:
    - monitor: laptop
      orientation: landscape
      modules:
        left: workspaces
"""

DEFAULTS = """\
window_manager:
  settings:
    border_width: 3
ui:
  font_size: 12
"""


@pytest.fixture
def dirs(tmp_path: Path):
    tracked = tmp_path / "profiles"
    overlay = tmp_path / "profiles.d"
    tracked.mkdir()
    overlay.mkdir()
    (tracked / "defaults.yaml").write_text(DEFAULTS)
    (tracked / "shared.yaml").write_text(MINIMAL.format(name="shared", desc="tracked copy"))
    (tracked / "public-only.yaml").write_text(MINIMAL.format(name="public-only", desc="tracked"))
    (overlay / "shared.yaml").write_text(MINIMAL.format(name="shared", desc="overlay copy"))
    (overlay / "work-only.yaml").write_text(MINIMAL.format(name="work-only", desc="overlay"))
    return tracked, overlay


def test_list_is_the_union(dirs):
    svc = ProfileService(list(dirs))
    assert svc.list_profiles() == ["public-only", "shared", "work-only"]


def test_later_directory_shadows_earlier(dirs):
    svc = ProfileService(list(dirs))
    assert svc.load_profile("shared").description == "overlay copy"
    assert svc.load_profile("public-only").description == "tracked"
    assert svc.load_profile("work-only").description == "overlay"


def test_defaults_come_from_first_directory_that_has_them(dirs):
    svc = ProfileService(list(dirs))
    # work-only lives in the overlay, which has no defaults.yaml; it still
    # inherits the tracked defaults
    assert svc.load_profile("work-only").window_manager.settings["border_width"] == 3


def test_missing_overlay_directory_is_fine(dirs):
    tracked, _ = dirs
    svc = ProfileService([tracked, tracked.parent / "does-not-exist"])
    assert svc.list_profiles() == ["public-only", "shared"]


def test_single_path_still_accepted(dirs):
    tracked, _ = dirs
    svc = ProfileService(tracked)
    assert svc.profiles_dir == tracked
    assert svc.list_profiles() == ["public-only", "shared"]


def test_default_search_path_follows_xdg(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert ProfileService.default_profiles_dirs() == [
        tmp_path / "bspwm" / "profiles",
        tmp_path / "bspwm" / "profiles.d",
    ]
