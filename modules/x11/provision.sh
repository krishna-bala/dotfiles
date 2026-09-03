#!/usr/bin/env bash
#
# x11/provision.sh - idempotent provisioning for the bspwm/X11 stack.
#
# Installs the system packages bspwmrc, sxhkd, dunst, and the systemd user
# unit invoke; polybar and picom from the distro where its package is new
# enough and from pinned source where it is not; the fonts rofi names; and
# the monitor-manager (apps/monitor-manager) as a uv tool. Steps already
# satisfied are skipped, so re-running is safe; any failure aborts loudly.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$MODULE_DIR/../.." && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root
mkdir -p "$HOME/.local/bin"

# Picom is built from a pinned upstream commit where the distro package is
# older than v13: 22.04 ships v9, whose rounded-corner antialiasing is
# visibly uneven, and whether the releases between fixed it has not been
# checked, so the floor is the version that was reviewed.
PICOM_VERSION="13"
PICOM_COMMIT="d87a5ba3af7a9ee3c4e040ee29b2dea7e9e46317"
# Polybar likewise: 22.04 packages 3.5.7, but modules.ini's [module/tray]
# needs the internal/tray module added in 3.7.0, so that is the floor for
# taking the distro package. Unlike picom's, this artifact is an asset
# upstream uploads rather than one GitHub generates on demand, so its bytes
# are fixed for good - and it is the only source that ships polybar's
# vendored submodules, which a git-tag archive omits. The sha256 is the one
# Debian records for polybar_3.7.2.orig.tar.gz.
POLYBAR_VERSION="3.7.2"
POLYBAR_MIN_DISTRO_VERSION="3.7.0"
POLYBAR_SHA256="e2feacbd02e7c94baed7f50b13bcbf307d95df0325c3ecae443289ba5b56af29"

# ----------------------------------------------------------------------------
# WM/X11 stack (apt). Everything bspwmrc, sxhkd, dunst, and the systemd user
# units invoke:
#   nitrogen             - wallpaper restore at bspwm startup
#   network-manager-gnome, blueman - nm-applet / blueman-applet tray apps
#   x11-xkb-utils        - setxkbmap (swapescape.service ExecStart)
#   xdg-utils            - xdg-open (dunstrc browser)
#   i3lock, libnotify-bin - bin/lockscreen and startup-failure notifications
#   xclip                - clipboard from sxhkd's screenshot bindings
# protonvpn-app is deliberately NOT here: it comes from Proton's own repo
# and bspwmrc pgrep-guards it, so its absence is harmless.
# kitty (sxhkd's terminal, monitor-switch.sh) is the kitty module's.
# ----------------------------------------------------------------------------
log "WM/X11 packages"
pkg_ensure \
  bspwm sxhkd rofi dunst nitrogen \
  redshift brightnessctl pulseaudio-utils scrot xclip simplescreenrecorder \
  x11-xserver-utils x11-xkb-utils \
  network-manager-gnome blueman xdg-utils \
  i3lock libnotify-bin fontconfig xz-utils

# ----------------------------------------------------------------------------
# Picom. Distro package when it is at least the pinned major; otherwise a
# pinned source build. Upstream uploads no release assets, and the
# alternative - a sha256 over GitHub's tag archive - pins bytes GitHub
# generates on demand and has changed before, which fails the hash through
# no fault of the tag. So this pins the commit instead: git's own object
# hashing makes it the content hash, and a re-pointed tag is caught by the
# check below rather than silently building something else. Meson's bundled
# libconfig fallback is itself pinned and handles 22.04's pre-1.7 libconfig.
# ----------------------------------------------------------------------------
log "picom v$PICOM_VERSION"
PICOM_BIN="$HOME/.local/bin/picom"
picom_candidate="$(pkg_candidate_version picom)"
if [ -x "$PICOM_BIN" ] && [ "$("$PICOM_BIN" --version 2>/dev/null)" = "v$PICOM_VERSION" ]; then
  skip "picom $("$PICOM_BIN" --version) already at pin (source build)"
elif [ -n "$picom_candidate" ] && version_ge "${picom_candidate%%-*}" "$PICOM_VERSION"; then
  pkg_ensure picom
  note "picom from the distro ($picom_candidate) satisfies the v$PICOM_VERSION floor; not building"
else
  pkg_ensure \
    build-essential git meson ninja-build pkg-config \
    libconfig-dev libdbus-1-dev libegl-dev libev-dev libgl-dev libepoxy-dev \
    libpcre2-dev libpixman-1-dev libx11-xcb-dev libxcb1-dev \
    libxcb-composite0-dev libxcb-damage0-dev libxcb-glx0-dev \
    libxcb-image0-dev libxcb-present-dev libxcb-randr0-dev \
    libxcb-render0-dev libxcb-render-util0-dev libxcb-shape0-dev \
    libxcb-util-dev libxcb-xfixes0-dev uthash-dev
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
# Polybar. Distro package when it has internal/tray (>= 3.7.0); otherwise a
# pinned source build with the feature set this config actually references:
# internal/pulseaudio ([module/alsa]) and internal/network need libpulse and
# libnl, while i3/mpd/curl/alsa modules are unused and their backends are
# switched off rather than pulled in. Docs need sphinx and are skipped.
# Installs under ~/.local, ahead of any apt polybar on PATH.
# ----------------------------------------------------------------------------
log "polybar $POLYBAR_VERSION"
polybar_candidate="$(pkg_candidate_version polybar)"
if at_pinned_version polybar "$POLYBAR_VERSION"; then
  skip "polybar $(installed_version polybar) already at pin"
elif [ -n "$polybar_candidate" ] && version_ge "${polybar_candidate%%-*}" "$POLYBAR_MIN_DISTRO_VERSION"; then
  pkg_ensure polybar
  note "polybar from the distro ($polybar_candidate) has internal/tray; not building"
else
  pkg_ensure \
    build-essential cmake git pkg-config python3-xcbgen xcb-proto \
    libcairo2-dev libuv1-dev libnl-genl-3-dev libpulse-dev \
    libxcb1-dev libxcb-composite0-dev libxcb-cursor-dev libxcb-ewmh-dev \
    libxcb-icccm4-dev libxcb-image0-dev libxcb-randr0-dev libxcb-sync-dev \
    libxcb-util-dev libxcb-xkb-dev libxcb-xrm-dev
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
# Nerd Fonts (pinned via provision-lib.sh): the rofi themes use Iosevka and
# FantasqueSansMono; JetBrainsMono (polybar's bars, dunst) is the kitty
# module's, which this module requires.
# ----------------------------------------------------------------------------
install_nerd_font Iosevka "$NERD_FONT_IOSEVKA_SHA256"
install_nerd_font FantasqueSansMono "$NERD_FONT_FANTASQUESANSMONO_SHA256"

# ----------------------------------------------------------------------------
# monitor-manager: the EDID-based profile applier bspwmrc runs at login and
# the sxhkd bindings invoke. It is an application (apps/monitor-manager),
# installed as a uv tool into its own venv with a `monitor-manager` entry
# point on PATH. --editable: the venv imports the checkout, so pulling the
# repo updates the tool without re-provisioning; the lockfile pins its
# dependencies exactly and a drifted lock fails loudly.
# ----------------------------------------------------------------------------
install_uv
log "monitor-manager (uv tool)"
UV_BIN="$(command -v uv || echo "$HOME/.local/bin/uv")"
[ -x "$UV_BIN" ] || die "uv not found; cannot install monitor-manager"
# `uv tool install` resolves afresh, so the lockfile is turned into a
# constraints file first: the tool venv gets exactly the versions uv.lock
# records, and --locked makes a lock that has drifted from pyproject.toml
# fail here rather than install something unreviewed.
tmp="$(mktemp -d)"
(cd "$REPO_ROOT/apps/monitor-manager" &&
  "$UV_BIN" export --locked --no-dev --no-hashes --no-emit-project -q -o "$tmp/constraints.txt" &&
  "$UV_BIN" tool install --editable --reinstall -q -c "$tmp/constraints.txt" .) ||
  die "uv tool install failed for apps/monitor-manager"
rm -rf "$tmp"
[ -x "$HOME/.local/bin/monitor-manager" ] || die "uv tool install put no monitor-manager on ~/.local/bin"
skip "monitor-manager installed ($("$HOME/.local/bin/monitor-manager" --help 2>/dev/null | head -n1))"
