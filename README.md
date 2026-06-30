# desktop-environment

A bspwm + polybar + sxhkd X11 desktop, including a Python monitor-manager
that auto-detects connected displays (by a hashed EDID fingerprint, never
the raw bytes) and applies a matching profile. This is the tightly-coupled
X11 stack: everything here changes and is tested together.

## What's in here

- `bspwm/` — `bspwmrc`, window-manager scripts, and `monitor-manager.py`
  (the EDID-based profile system: `lib/`, `profiles/*.yaml`, `tests/`).
  The monitor-manager lives inside this repo rather than as its own package
  because it's runtime-coupled to bspwm: `bspwmrc` execs its venv's
  `python` directly at login.
- `sxhkd/`, `polybar/` — hotkeys and status bar.
- `picom.conf`, `dunstrc`, `redshift.conf`, `Xresources` — compositor,
  notifications, color temperature, X resource defaults.
- `systemd/` — user units (e.g. swapescape).
- `bin/` — `wacominit` (Wacom tablet mapping), `lockscreen` (i3lock
  wrapper), `clipimg` (pull an image from a remote kitty session's
  clipboard).
- `docs/` — the desktop-environment PRD and AirPods-on-Linux notes.

## Install

Standalone, on any machine:

```bash
git clone --recurse-submodules https://github.com/krishna-bala/desktop-environment
cd desktop-environment
./provision.sh   # system packages + uv sync for the monitor-manager venv
./install        # symlink configs via dotbot
```

`./install` runs `git submodule update --init --recursive` itself, so a
plain (non-recursive) clone also works.

`provision.sh` is idempotent — re-run it any time; every step is guarded by
an existence/version check.

## Monitor manager

See `bspwm/CLAUDE.md` for the full architecture. In short:
`monitor-manager.py` reads `xrandr`, matches connected displays against
`bspwm/profiles/*.yaml` by a truncated SHA-256 hash of each display's EDID
(`bspwm/lib/edid.py`), and reconciles bspwm/polybar to the matching
profile's layout. Capture a new profile's fixtures and match keys with
`bspwm/scripts/capture-fixture.sh`, which redacts raw EDID bytes before
anything touches disk.

## Composition

This repo is also consumed as a git submodule by a private meta-repo that
adds a company-specific overlay and orchestrates installation across
several public dotfiles repos (this one, a shell/terminal repo, and a
neovim repo). It stays independently installable on its own — the meta-repo
just runs this repo's `install.conf.yaml` as one step among several, with
`force: true` overlay links applied last.
