#!/usr/bin/env bash
#
# provision.sh - idempotent provisioning for the X11/WM stack in this repo.
#
# Installs the system packages this repo's configs and scripts depend on,
# plus uv (exact pin + sha256, via ../provision-lib.sh) to build the
# monitor-manager's venv. Steps already satisfied are skipped, so re-running
# is safe; any failure aborts loudly with a nonzero exit. Run ./install
# afterwards to symlink the configs themselves.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../provision-lib.sh
. "$SCRIPT_DIR/../provision-lib.sh"

require_not_root
init_provision_log "$SCRIPT_DIR/provision.log"

mkdir -p "$HOME/.local/bin"

log "Provisioning started"

# ----------------------------------------------------------------------------
# WM/X11 stack (apt). i3lock and libnotify-bin aren't in the upstream
# package list this slice was cut from, but bin/lockscreen and bspwmrc's
# startup-failure notifications hard-depend on them, so they're added here.
# ----------------------------------------------------------------------------
log "WM/X11 packages (apt)"
sudo apt-get update -qq
sudo apt-get install -y -qq \
  bspwm sxhkd polybar rofi picom dunst feh \
  redshift brightnessctl pulseaudio-utils scrot xclip \
  x11-xserver-utils xserver-xorg-input-wacom \
  i3lock libnotify-bin

# ----------------------------------------------------------------------------
# uv (python package/venv manager) - needed for `uv sync` below; pin and
# installer are shared with provision-shell.sh via provision-lib.sh
# ----------------------------------------------------------------------------
install_uv

# ----------------------------------------------------------------------------
# bspwm monitor-manager venv (bspwmrc runs .venv/bin/python directly at
# login, so the venv must exist before the first graphical session).
# --locked: install exactly what uv.lock records, and fail loudly if
# pyproject.toml and uv.lock have drifted apart.
# ----------------------------------------------------------------------------
log "bspwm monitor-manager venv"
UV_BIN="$(command -v uv || echo "$HOME/.local/bin/uv")"
[ -x "$UV_BIN" ] || die "uv not found; cannot create bspwm .venv"
(cd "$SCRIPT_DIR/bspwm" && "$UV_BIN" sync --locked -q) ||
  die "uv sync --locked failed in bspwm/"
skip "bspwm .venv in sync"

log "Provisioning complete. Run ./install to symlink configs."
