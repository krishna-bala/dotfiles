#!/usr/bin/env bash
#
# provision.sh - idempotent provisioning for the X11/WM stack in this repo.
#
# Installs the system packages this repo's configs and scripts depend on,
# plus uv (pinned) to build the monitor-manager's venv. Every step is guarded
# by an existence/version check, so re-running is always safe. Run ./install
# afterwards to symlink the configs themselves.

set -uo pipefail

if [ "$(id -u)" -eq 0 ]; then
  echo "ERROR: do not run provision.sh as root. It uses sudo where needed." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/provision.log"

if [ -f "$LOG_FILE" ]; then
  tail -n 2000 "$LOG_FILE" >"$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
fi
exec > >(tee -a "$LOG_FILE") 2>&1

log() { printf '\n==> [%s] %s\n' "$(date '+%F %T')" "$*"; }
skip() { printf '    [skip] %s\n' "$*"; }

mkdir -p "$HOME/.local/bin"

# ----------------------------------------------------------------------------
# Pinned versions - bump deliberately, review upstream changes, then re-run.
# ----------------------------------------------------------------------------
UV_VERSION="0.11.20"

installed_version() {
  local bin
  bin="$(command -v "$1" || true)"
  [ -z "$bin" ] && [ -x "$HOME/.local/bin/$1" ] && bin="$HOME/.local/bin/$1"
  [ -z "$bin" ] && return 0
  "$bin" --version 2>/dev/null | grep -oEm1 '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -n1
}

meets_pin() {
  local cur pin="${2#v}"
  cur="$(installed_version "$1")"
  [ -n "$cur" ] || return 1
  [ "$(printf '%s\n' "$pin" "$cur" | sort -V | head -n1)" = "$pin" ]
}

install_release_binary() {
  local url="$1" member="$2" dest="$3" strip="${4:-0}"
  local tmp
  tmp="$(mktemp -d)"
  if curl -fsSL -o "$tmp/archive.tar.gz" "$url" &&
    tar -xzf "$tmp/archive.tar.gz" -C "$tmp" --strip-components="$strip" "$member"; then
    install -m 0755 "$tmp/$(basename "$member")" "$HOME/.local/bin/$dest"
  else
    echo "    [error] failed to download/extract $url"
  fi
  rm -rf "$tmp"
}

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
# uv (python package/venv manager) - needed for `uv sync` below
# ----------------------------------------------------------------------------
log "uv $UV_VERSION"
if meets_pin uv "$UV_VERSION"; then
  skip "uv $(installed_version uv) already installed (>= $UV_VERSION)"
else
  install_release_binary \
    "https://github.com/astral-sh/uv/releases/download/$UV_VERSION/uv-x86_64-unknown-linux-gnu.tar.gz" \
    "uv-x86_64-unknown-linux-gnu/uv" uv 1
  [ -x "$HOME/.local/bin/uv" ] || echo "    [error] uv install failed"
fi

# ----------------------------------------------------------------------------
# bspwm monitor-manager venv (bspwmrc runs .venv/bin/python directly at
# login, so the venv must exist before the first graphical session)
# ----------------------------------------------------------------------------
log "bspwm monitor-manager venv"
UV_BIN="$(command -v uv || echo "$HOME/.local/bin/uv")"
if [ -x "$UV_BIN" ]; then
  if (cd "$SCRIPT_DIR/bspwm" && "$UV_BIN" sync -q); then
    skip "bspwm .venv in sync"
  else
    echo "    [error] uv sync failed in bspwm/"
  fi
else
  echo "    [error] uv not found; cannot create bspwm .venv"
fi

log "Provisioning complete. Run ./install to symlink configs."
