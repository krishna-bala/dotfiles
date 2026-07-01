"""Tests for profiles/defaults.yaml merging in ProfileService."""

import textwrap
from pathlib import Path

import pytest

from lib.profile import ProfileService, _deep_merge

MINIMAL_PROFILE = textwrap.dedent(
    """
    name: minimal
    description: minimal test profile
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
)

DEFAULTS = textwrap.dedent(
    """
    window_manager:
      settings:
        border_width: 7
        window_gap: 15
        focused_border_color: "#629dc8"
        normal_border_color: "#1f2339"
    ui:
      font_size: 16
    """
)


@pytest.fixture
def profiles_dir(tmp_path: Path) -> Path:
    (tmp_path / "defaults.yaml").write_text(DEFAULTS)
    (tmp_path / "minimal.yaml").write_text(MINIMAL_PROFILE)
    return tmp_path


def test_settings_inherited_from_defaults(profiles_dir: Path):
    profile = ProfileService(profiles_dir=profiles_dir).load_profile("minimal")
    assert profile.window_manager.settings == {
        "border_width": 7,
        "window_gap": 15,
        "focused_border_color": "#629dc8",
        "normal_border_color": "#1f2339",
    }


def test_profile_override_wins(profiles_dir: Path):
    override = MINIMAL_PROFILE.replace(
        "  workspaces:",
        "  settings:\n    window_gap: 30\n  workspaces:",
    )
    (profiles_dir / "minimal.yaml").write_text(override)
    profile = ProfileService(profiles_dir=profiles_dir).load_profile("minimal")
    assert profile.window_manager.settings["window_gap"] == 30
    # Untouched keys still come from defaults
    assert profile.window_manager.settings["border_width"] == 7


def test_bar_font_size_inherited_and_overridable(profiles_dir: Path):
    svc = ProfileService(profiles_dir=profiles_dir)
    assert svc.load_profile("minimal").ui.bars[0].font_size == 16

    override = MINIMAL_PROFILE.replace(
        "orientation: landscape", "orientation: landscape\n      font_size: 12"
    )
    (profiles_dir / "minimal.yaml").write_text(override)
    svc = ProfileService(profiles_dir=profiles_dir)
    assert svc.load_profile("minimal").ui.bars[0].font_size == 12


def test_list_profiles_excludes_defaults(profiles_dir: Path):
    assert ProfileService(profiles_dir=profiles_dir).list_profiles() == ["minimal"]


def test_missing_defaults_file_is_fine(tmp_path: Path):
    (tmp_path / "minimal.yaml").write_text(MINIMAL_PROFILE)
    profile = ProfileService(profiles_dir=tmp_path).load_profile("minimal")
    assert profile.window_manager.settings is None
    assert profile.ui.bars[0].font_size is None


def test_deep_merge_replaces_lists():
    base = {"a": {"b": 1, "c": [1, 2]}, "d": 4}
    override = {"a": {"c": [9]}}
    assert _deep_merge(base, override) == {"a": {"b": 1, "c": [9]}, "d": 4}
