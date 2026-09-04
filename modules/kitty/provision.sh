#!/usr/bin/env bash
#
# kitty/provision.sh - the terminal emulator (upstream binary bundle ->
# ~/.local/kitty.app, kitty/kitten symlinked into ~/.local/bin) and the font
# kitty.conf names. Pinned rather than apt: 22.04's kitty (0.21) is too old
# for this repo's kitty.conf and kittens, and the X11 module's sxhkd
# bindings and monitor-switch.sh hard-depend on the binary.
#
# This is a client-side module: it belongs on machines someone sits at, not
# on servers reached over ssh (the ssh kitten ships its own remote helper).

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root
mkdir -p "$HOME/.local/bin"

# kitty publishes no checksum file (it signs with GPG); this sha256 was
# computed from the downloaded release artifact when the pin was set.
KITTY_VERSION="0.47.4"
KITTY_SHA256="bc230142b2bd27f2a4bf1b1b67575f3d397a4ea2cc83f4ac2b912c306a939693"

# fontconfig: fc-cache for the Nerd Font below. fonts-symbola: covers
# Miscellaneous Technical symbols that neither the Nerd Fonts nor Noto Color
# Emoji carry. U+23F5 in particular is excluded from the RGI emoji set, so
# nothing else on a clean install provides it and Claude Code's
# permission-mode indicators render as tofu in the terminal.
log "Font packages"
pkg_ensure fontconfig fonts-symbola

log "kitty $KITTY_VERSION"
if ! pin_satisfied kitty "$KITTY_VERSION"; then
  install_release_bundle \
    "https://github.com/kovidgoyal/kitty/releases/download/v$KITTY_VERSION/kitty-$KITTY_VERSION-x86_64.txz" \
    "$KITTY_SHA256" kitty.app 0 kitty kitten
  # Desktop integration, per kitty's install docs: launcher entries with
  # absolute Exec/Icon paths (the bundle's .desktop files assume kitty is on
  # the system PATH), and xdg-terminal-exec registration. These embed $HOME,
  # so they're generated here rather than symlinked by dotbot.
  mkdir -p "$HOME/.local/share/applications" "$HOME/.config"
  cp "$HOME/.local/kitty.app/share/applications/kitty.desktop" \
    "$HOME/.local/kitty.app/share/applications/kitty-open.desktop" \
    "$HOME/.local/share/applications/"
  sed -i \
    -e "s|Icon=kitty|Icon=$HOME/.local/kitty.app/share/icons/hicolor/256x256/apps/kitty.png|g" \
    -e "s|Exec=kitty|Exec=$HOME/.local/kitty.app/bin/kitty|g" \
    "$HOME/.local/share/applications/kitty.desktop" \
    "$HOME/.local/share/applications/kitty-open.desktop"
  echo 'kitty.desktop' >"$HOME/.config/xdg-terminals.list"
fi

# kitty.conf's font_family is "JetBrainsMono Nerd Font Mono"
install_nerd_font JetBrainsMono "$NERD_FONT_JETBRAINSMONO_SHA256"

report_stale_copies kitty "$HOME/.local/bin/kitty" || true
