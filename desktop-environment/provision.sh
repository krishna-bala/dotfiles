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
# WM/X11 stack (apt). Everything bspwmrc, sxhkd, dunst, and the systemd user
# units invoke:
#   nitrogen             - wallpaper restore at bspwm startup
#   network-manager-gnome, blueman - nm-applet / blueman-applet tray apps
#   x11-xkb-utils        - setxkbmap (swapescape.service ExecStart)
#   xdg-utils            - xdg-open (dunstrc browser)
#   i3lock, libnotify-bin - bin/lockscreen and startup-failure notifications
# protonvpn-app is deliberately NOT here: it comes from Proton's own repo
# and bspwmrc pgrep-guards it, so its absence is harmless.
# kitty (sxhkd's terminal, monitor-switch.sh) is provisioned by
# provision-shell.sh as a pinned upstream bundle.
# ----------------------------------------------------------------------------
log "WM/X11 packages (apt)"
sudo apt-get update -qq
sudo apt-get install -y -qq \
  bspwm sxhkd polybar rofi picom dunst nitrogen \
  redshift brightnessctl pulseaudio-utils scrot xclip \
  x11-xserver-utils x11-xkb-utils xserver-xorg-input-wacom \
  network-manager-gnome blueman xdg-utils \
  i3lock libnotify-bin fontconfig xz-utils

# ----------------------------------------------------------------------------
# Nerd Fonts (pinned via provision-lib.sh): polybar's bars use
# FantasqueSansM/Iosevka, dunst and the rofi themes use JetBrainsMono.
# ----------------------------------------------------------------------------
install_nerd_font JetBrainsMono "$NERD_FONT_JETBRAINSMONO_SHA256"
install_nerd_font Iosevka "$NERD_FONT_IOSEVKA_SHA256"
install_nerd_font FantasqueSansMono "$NERD_FONT_FANTASQUESANSMONO_SHA256"

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
