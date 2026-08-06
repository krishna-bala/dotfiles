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

# Picom is built from a pinned upstream commit below because Ubuntu 22.04's
# package is v9, whose rounded-corner antialiasing is visibly uneven.
PICOM_VERSION="13"
PICOM_COMMIT="d87a5ba3af7a9ee3c4e040ee29b2dea7e9e46317"
# Polybar likewise: 22.04 packages 3.5.7, but modules.ini's [module/tray] needs
# the internal/tray module added in 3.7.0. Unlike picom's, this artifact is an
# asset upstream uploads rather than one GitHub generates on demand, so its
# bytes are fixed for good - and it is the only source that ships polybar's
# vendored submodules, which a git-tag archive omits. The sha256 is the one
# Debian records for polybar_3.7.2.orig.tar.gz.
POLYBAR_VERSION="3.7.2"
POLYBAR_SHA256="e2feacbd02e7c94baed7f50b13bcbf307d95df0325c3ecae443289ba5b56af29"

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
  bspwm sxhkd rofi dunst nitrogen \
  redshift brightnessctl pulseaudio-utils scrot xclip simplescreenrecorder \
  x11-xserver-utils x11-xkb-utils xserver-xorg-input-wacom \
  network-manager-gnome blueman xdg-utils \
  i3lock libnotify-bin fontconfig xz-utils \
  build-essential cmake curl git meson ninja-build pkg-config \
  libconfig-dev libdbus-1-dev libegl-dev libev-dev libgl-dev libepoxy-dev \
  libpcre2-dev libpixman-1-dev libx11-xcb-dev libxcb1-dev \
  libxcb-composite0-dev libxcb-damage0-dev libxcb-glx0-dev \
  libxcb-image0-dev libxcb-present-dev libxcb-randr0-dev \
  libxcb-render0-dev libxcb-render-util0-dev libxcb-shape0-dev \
  libxcb-util-dev libxcb-xfixes0-dev uthash-dev \
  libcairo2-dev libuv1-dev libnl-genl-3-dev libpulse-dev \
  libxcb-cursor-dev libxcb-ewmh-dev libxcb-icccm4-dev libxcb-sync-dev \
  libxcb-xkb-dev libxcb-xrm-dev python3-xcbgen xcb-proto

# ----------------------------------------------------------------------------
# Picom (pinned source build). Ubuntu 22.04 only packages v9. Upstream uploads
# no release assets, and the alternative - a sha256 over GitHub's tag archive -
# pins bytes GitHub generates on demand and has changed before, which fails the
# hash through no fault of the tag. So this pins the commit instead: git's own
# object hashing makes it the content hash, and a re-pointed tag is caught by
# the check below rather than silently building something else. Meson's bundled
# libconfig fallback is itself pinned and handles 22.04's pre-1.7 libconfig.
# ----------------------------------------------------------------------------
log "picom v$PICOM_VERSION (source build)"
PICOM_BIN="$HOME/.local/bin/picom"
if [ -x "$PICOM_BIN" ] && [ "$("$PICOM_BIN" --version 2>/dev/null)" = "v$PICOM_VERSION" ]; then
  skip "picom $("$PICOM_BIN" --version) already at pin"
else
  tmp="$(mktemp -d)"
  git -c advice.detachedHead=false clone --quiet --depth 1 \
    --branch "v$PICOM_VERSION" https://github.com/yshui/picom "$tmp/src" ||
    die "clone failed: picom v$PICOM_VERSION"
  picom_head="$(git -C "$tmp/src" rev-parse HEAD)"
  [ "$picom_head" = "$PICOM_COMMIT" ] ||
    die "picom tag v$PICOM_VERSION is $picom_head, expected $PICOM_COMMIT - refusing to build"
  # picom's meson.build stamps `git rev-parse` output into the version string
  # when it builds inside a repository, so the binary would report "v13
  # (revision d87a5ba)" and never match the pin check above - rebuilding on
  # every run. Drop the metadata now that the commit is verified.
  rm -rf "$tmp/src/.git"
  meson setup --buildtype=release "$tmp/src/build" "$tmp/src" ||
    die "picom v$PICOM_VERSION configure failed"
  ninja -C "$tmp/src/build" src/picom ||
    die "picom v$PICOM_VERSION build failed"
  install -m 0755 "$tmp/src/build/src/picom" "$PICOM_BIN" ||
    die "picom v$PICOM_VERSION install failed"
  rm -rf "$tmp"
fi

# ----------------------------------------------------------------------------
# Polybar (pinned source build). 22.04 packages 3.5.7, which predates the
# internal/tray module modules.ini uses, so on that release the tray silently
# never appears. Built with the feature set this config actually references:
# internal/pulseaudio ([module/alsa]) and internal/network need libpulse and
# libnl, while i3/mpd/curl/alsa modules are unused and their backends are
# switched off rather than pulled in. Docs need sphinx and are skipped.
# Installs under ~/.local, ahead of any apt polybar on PATH.
# ----------------------------------------------------------------------------
log "polybar $POLYBAR_VERSION (source build)"
if at_pinned_version polybar "$POLYBAR_VERSION"; then
  skip "polybar $(installed_version polybar) already at pin"
else
  tmp="$(mktemp -d)"
  fetch_url \
    "https://github.com/polybar/polybar/releases/download/$POLYBAR_VERSION/polybar-$POLYBAR_VERSION.tar.gz" \
    "$tmp/polybar.tar.gz" ||
    die "download failed: polybar $POLYBAR_VERSION"
  verify_sha256 "$tmp/polybar.tar.gz" "$POLYBAR_SHA256"
  mkdir -p "$tmp/src"
  tar -xzf "$tmp/polybar.tar.gz" -C "$tmp/src" --strip-components=1 ||
    die "extract failed: polybar $POLYBAR_VERSION"
  cmake -S "$tmp/src" -B "$tmp/src/build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$HOME/.local" \
    -DBUILD_DOC=OFF \
    -DENABLE_I3=OFF -DENABLE_MPD=OFF -DENABLE_CURL=OFF -DENABLE_ALSA=OFF ||
    die "polybar $POLYBAR_VERSION configure failed"
  cmake --build "$tmp/src/build" || die "polybar $POLYBAR_VERSION build failed"
  cmake --install "$tmp/src/build" || die "polybar $POLYBAR_VERSION install failed"
  rm -rf "$tmp"
fi

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
