#!/usr/bin/env bash
#
# cli-tools/provision.sh - the CLI tools bashrc and bash_aliases assume:
# fzf, ripgrep, fd, lsd, lazygit, jq, uv, glab. Release-tarball tools are
# pinned (floor) + sha256; fd and ripgrep come from apt.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root
mkdir -p "$HOME/.local/bin"

# Pinned versions + sha256s of the exact artifacts downloaded below. Each pin
# is the minimum this repo's configs are known to work with, and what a fresh
# machine gets; running something newer is fine and provisioning says so
# instead of rolling it back. Raising a pin is a deliberate, reviewed change:
# update the version AND its sha256 (from the upstream release's published
# checksums), review the upstream diff, then re-run. Nothing here ever
# resolves "latest" at runtime (see CLAUDE.md). UV_VERSION lives in
# lib/provision-lib.sh, shared with the X11 module.
GLAB_VERSION="v1.112.0"
GLAB_SHA256="71eb77a13dd57f3add103e979b20dbd9f4730bcaf9501ae2e8ac14cb4585c707"
LAZYGIT_VERSION="v0.62.2"
LAZYGIT_SHA256="8b9a4c2d0969cbea92b45c956dd2a44e1ba76900c9df49f1c60984045ce77984"
FZF_VERSION="v0.73.1" # bashrc's `fzf --bash` integration needs >= 0.48.0
FZF_SHA256="f3252c2c366bc1700d3c85781ec8c9695998927ac127870eb049ceea2d540f8a"
LSD_VERSION="v1.2.0" # not in 22.04's apt, so pinned like the other release tools
LSD_SHA256="57d3b5859254adcfb8374ce98159cca97a14959997d2ae1176d2cff59556d829"

# Download and archive tooling the helpers in provision-lib.sh rely on, plus
# jq (agents/status-line.sh) and xz for .tar.xz release archives.
log "Base packages"
pkg_ensure curl wget unzip xz-utils jq

# ----------------------------------------------------------------------------
# apt-managed CLI tools: fd, ripgrep (distro versions, presence-checked)
# ----------------------------------------------------------------------------
log "fd"
if have fd; then
  skip "fd already installed"
else
  pkg_ensure fd-find
  ln -sf "$(command -v fdfind)" "$HOME/.local/bin/fd"
fi

log "ripgrep"
if have rg; then skip "ripgrep already installed"; else
  pkg_ensure ripgrep
fi

# ----------------------------------------------------------------------------
# uv (python package/venv manager; pin shared with the X11 module)
# ----------------------------------------------------------------------------
install_uv

# ----------------------------------------------------------------------------
# glab (GitLab CLI). Installed from upstream's .deb rather than the tarball so
# it lands in /usr/bin - the same place a hand-run `dpkg -i` from the releases
# page puts it. With one copy on PATH, a manual update actually replaces the
# provisioned one instead of being silently shadowed by ~/.local/bin/glab, and
# because the pin is a floor, the newer copy then survives re-provisioning.
# ----------------------------------------------------------------------------
log "glab $GLAB_VERSION"
# Migration off the old tarball layout: ~/.local/bin precedes /usr/bin on PATH,
# so a leftover copy there would shadow the .deb and make the pin check read
# the wrong binary. Remove it before checking the version.
if [ -e "$HOME/.local/bin/glab" ]; then
  rm -f "$HOME/.local/bin/glab"
  note "removed ~/.local/bin/glab left by the old tarball install"
fi
if ! pin_satisfied glab "$GLAB_VERSION"; then
  install_release_deb \
    "https://gitlab.com/gitlab-org/cli/-/releases/$GLAB_VERSION/downloads/glab_${GLAB_VERSION#v}_linux_amd64.deb" \
    "$GLAB_SHA256" glab
fi

# ----------------------------------------------------------------------------
# Release-tarball tools: lsd, lazygit, fzf (pinned floor + sha256)
# ----------------------------------------------------------------------------
log "lsd $LSD_VERSION"
if ! pin_satisfied lsd "$LSD_VERSION"; then
  install_release_binary \
    "https://github.com/lsd-rs/lsd/releases/download/$LSD_VERSION/lsd-$LSD_VERSION-x86_64-unknown-linux-gnu.tar.gz" \
    "$LSD_SHA256" "lsd-$LSD_VERSION-x86_64-unknown-linux-gnu/lsd" lsd 1
fi

log "lazygit $LAZYGIT_VERSION"
if ! pin_satisfied lazygit "$LAZYGIT_VERSION"; then
  install_release_binary \
    "https://github.com/jesseduffield/lazygit/releases/download/$LAZYGIT_VERSION/lazygit_${LAZYGIT_VERSION#v}_Linux_x86_64.tar.gz" \
    "$LAZYGIT_SHA256" "lazygit" lazygit
fi

log "fzf $FZF_VERSION"
if ! pin_satisfied fzf "$FZF_VERSION"; then
  install_release_binary \
    "https://github.com/junegunn/fzf/releases/download/$FZF_VERSION/fzf-${FZF_VERSION#v}-linux_amd64.tar.gz" \
    "$FZF_SHA256" "fzf" fzf
fi

log "Checking for stale duplicate binaries"
stale=0
for entry in \
  "uv:$HOME/.local/bin/uv" \
  "lazygit:$HOME/.local/bin/lazygit" \
  "fzf:$HOME/.local/bin/fzf" \
  "lsd:$HOME/.local/bin/lsd" \
  "glab:/usr/bin/glab"; do
  report_stale_copies "${entry%%:*}" "${entry#*:}" || stale=1
done
[ "$stale" -eq 1 ] || skip "no stale copies found"
