#!/usr/bin/env bash
#
# provision-shell.sh - idempotent provisioning for the shell/terminal/dev
# tools this repo's configs assume are present.
#
# Every downloaded tool is pinned to an exact version and verified against a
# recorded sha256 (helpers in provision-lib.sh). A tool already at its pin is
# skipped, so re-running is safe; any other outcome - download failure, hash
# mismatch, failed install - aborts loudly with a nonzero exit. Run ./install
# afterwards to symlink the dotfiles themselves.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=provision-lib.sh
. "$SCRIPT_DIR/provision-lib.sh"

require_not_root
init_provision_log "$SCRIPT_DIR/provision.log"

mkdir -p "$HOME/.local/bin" "$HOME/.local/share"

# ----------------------------------------------------------------------------
# Pinned versions + sha256s of the exact artifacts downloaded below. Bumping
# a pin is a deliberate, reviewed change: update the version AND its sha256
# (from the upstream release's published checksums), review the upstream
# diff, then re-run. (supply chain policy: no fetch-latest, see CLAUDE.md)
# UV_VERSION/UV_SHA256 live in provision-lib.sh, shared with the desktop half.
# ----------------------------------------------------------------------------
NVM_VERSION="v0.40.3"
NVM_INSTALL_SHA256="2d8359a64a3cb07c02389ad88ceecd43f2fa469c06104f92f98df5b6f315275f"
GLAB_VERSION="v1.102.0"
GLAB_SHA256="2e06f278bb1762126e9b695f67baf5e3210df431b2039c76c1991252bf9c0868"
LAZYGIT_VERSION="v0.62.2"
LAZYGIT_SHA256="8b9a4c2d0969cbea92b45c956dd2a44e1ba76900c9df49f1c60984045ce77984"
STARSHIP_VERSION="v1.25.1"
STARSHIP_SHA256="4488c11ca632327d1f1f16fb2f102c0646094c35479cd5435991385da43c61ac"
FZF_VERSION="v0.73.1" # bashrc's `fzf --bash` integration needs >= 0.48.0
FZF_SHA256="f3252c2c366bc1700d3c85781ec8c9695998927ac127870eb049ceea2d540f8a"
LSD_VERSION="v1.2.0" # not in 22.04's apt, so pinned like the other release tools
LSD_SHA256="57d3b5859254adcfb8374ce98159cca97a14959997d2ae1176d2cff59556d829"
# kitty and neovim publish no checksum files (kitty signs with GPG); these
# sha256s were computed from the downloaded release artifacts when the pins
# were set, so every machine gets byte-identical copies of what was reviewed.
KITTY_VERSION="0.47.4"
KITTY_SHA256="bc230142b2bd27f2a4bf1b1b67575f3d397a4ea2cc83f4ac2b912c306a939693"
NVIM_VERSION="v0.12.3"
NVIM_SHA256="c441b547142860bf01bcce39e36cbed185c41112813e15443b16e5237750724d"
# rustup-init sha256 is upstream's published checksum for this archive version
RUSTUP_VERSION="1.29.0"
RUSTUP_INIT_SHA256="4acc9acc76d5079515b46346a485974457b5a79893cfb01112423c89aeb5aa10"
RUST_TOOLCHAIN="1.96.1"
TREE_SITTER_VERSION="0.26.10"

log "Provisioning started"

# ----------------------------------------------------------------------------
# apt packages (git-core PPA for a current git). These follow the distro's
# versions; only the release-tarball tools below are content-pinned.
# ----------------------------------------------------------------------------
log "System packages (apt)"
if ! command -v add-apt-repository >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq software-properties-common
fi
if ! grep -rq "git-core/ppa" /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null; then
  sudo add-apt-repository -y ppa:git-core/ppa
fi
sudo apt-get update -qq
# libclang-dev: the tree-sitter CLI source build below pulls in rquickjs-sys,
# whose bindgen build step needs libclang.so at compile time.
sudo apt-get install -y -qq \
  git curl wget unzip xz-utils \
  build-essential pkg-config libclang-dev \
  tmux jq xclip \
  bash-completion fontconfig

# ----------------------------------------------------------------------------
# nvm + node LTS
# ----------------------------------------------------------------------------
# Must match bashrc's NVM_DIR logic exactly, or provisioning installs node
# somewhere the shell never looks.
if [[ -z "${XDG_CONFIG_HOME-}" ]]; then
  export NVM_DIR="$HOME/.nvm"
else
  export NVM_DIR="$XDG_CONFIG_HOME/nvm"
fi
log "nvm $NVM_VERSION + node LTS (NVM_DIR=$NVM_DIR)"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  mkdir -p "$NVM_DIR"
  # PROFILE=/dev/null: bashrc already has its own nvm block; never let the
  # installer append one to the repo-symlinked ~/.bashrc.
  PROFILE=/dev/null run_verified_installer \
    "https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh" \
    "$NVM_INSTALL_SHA256"
else
  skip "nvm already installed"
fi
# shellcheck disable=SC1091
. "$NVM_DIR/nvm.sh" || die "failed to load $NVM_DIR/nvm.sh"
if ! nvm ls --no-colors lts/* >/dev/null 2>&1; then
  NVM_SYMLINK_CURRENT=true nvm install --lts || die "nvm install --lts failed"
else
  skip "node LTS already installed"
fi

# ----------------------------------------------------------------------------
# uv (python package/venv manager; pin shared with the desktop half)
# ----------------------------------------------------------------------------
install_uv

# ----------------------------------------------------------------------------
# glab (GitLab CLI)
# ----------------------------------------------------------------------------
log "glab $GLAB_VERSION"
if at_pinned_version glab "$GLAB_VERSION"; then
  skip "glab $(installed_version glab) already at pin"
else
  install_release_binary \
    "https://gitlab.com/gitlab-org/cli/-/releases/$GLAB_VERSION/downloads/glab_${GLAB_VERSION#v}_linux_amd64.tar.gz" \
    "$GLAB_SHA256" "bin/glab" glab 1
fi

# ----------------------------------------------------------------------------
# apt-managed CLI tools: fd, ripgrep (distro versions, presence-checked)
# ----------------------------------------------------------------------------
log "fd"
if have fd; then
  skip "fd already installed"
else
  sudo apt-get install -y -qq fd-find
  ln -sf "$(command -v fdfind)" "$HOME/.local/bin/fd"
fi

log "ripgrep"
if have rg; then skip "ripgrep already installed"; else
  sudo apt-get install -y -qq ripgrep
fi

# ----------------------------------------------------------------------------
# Release-tarball tools: lsd, lazygit, starship, fzf (exact pin + sha256)
# ----------------------------------------------------------------------------
log "lsd $LSD_VERSION"
if at_pinned_version lsd "$LSD_VERSION"; then
  skip "lsd $(installed_version lsd) already at pin"
else
  install_release_binary \
    "https://github.com/lsd-rs/lsd/releases/download/$LSD_VERSION/lsd-$LSD_VERSION-x86_64-unknown-linux-gnu.tar.gz" \
    "$LSD_SHA256" "lsd-$LSD_VERSION-x86_64-unknown-linux-gnu/lsd" lsd 1
fi

log "lazygit $LAZYGIT_VERSION"
if at_pinned_version lazygit "$LAZYGIT_VERSION"; then
  skip "lazygit $(installed_version lazygit) already at pin"
else
  install_release_binary \
    "https://github.com/jesseduffield/lazygit/releases/download/$LAZYGIT_VERSION/lazygit_${LAZYGIT_VERSION#v}_Linux_x86_64.tar.gz" \
    "$LAZYGIT_SHA256" "lazygit" lazygit
fi

log "starship $STARSHIP_VERSION"
if at_pinned_version starship "$STARSHIP_VERSION"; then
  skip "starship $(installed_version starship) already at pin"
else
  install_release_binary \
    "https://github.com/starship/starship/releases/download/$STARSHIP_VERSION/starship-x86_64-unknown-linux-gnu.tar.gz" \
    "$STARSHIP_SHA256" "starship" starship
fi

log "fzf $FZF_VERSION"
if at_pinned_version fzf "$FZF_VERSION"; then
  skip "fzf $(installed_version fzf) already at pin"
else
  install_release_binary \
    "https://github.com/junegunn/fzf/releases/download/$FZF_VERSION/fzf-${FZF_VERSION#v}-linux_amd64.tar.gz" \
    "$FZF_SHA256" "fzf" fzf
fi

# ----------------------------------------------------------------------------
# kitty (upstream binary bundle -> ~/.local/kitty.app, kitty/kitten symlinked
# into ~/.local/bin). Pinned rather than apt: 22.04's kitty (0.21) is too old
# for this repo's kitty.conf and kittens, and the desktop half's sxhkd
# bindings and monitor-switch.sh hard-depend on the binary.
# ----------------------------------------------------------------------------
log "kitty $KITTY_VERSION"
if at_pinned_version kitty "$KITTY_VERSION"; then
  skip "kitty $(installed_version kitty) already at pin"
else
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

# ----------------------------------------------------------------------------
# neovim (upstream bundle -> ~/.local/nvim.app). bashrc's EDITOR, gitconfig's
# editor/difftool/mergetool, and lazygit's edit command all assume nvim;
# 22.04's apt neovim (0.6) is far too old for a current config.
# ----------------------------------------------------------------------------
log "neovim $NVIM_VERSION"
if at_pinned_version nvim "$NVIM_VERSION"; then
  skip "nvim $(installed_version nvim) already at pin"
else
  install_release_bundle \
    "https://github.com/neovim/neovim/releases/download/$NVIM_VERSION/nvim-linux-x86_64.tar.gz" \
    "$NVIM_SHA256" nvim.app 1 nvim
fi

# ----------------------------------------------------------------------------
# rust toolchain (rustup, pinned) - nvim's tooling assumes cargo (bashrc
# sources ~/.cargo/env, mason builds native extensions), and the tree-sitter
# CLI below is built from source with it.
# ----------------------------------------------------------------------------
log "rust $RUST_TOOLCHAIN (rustup $RUSTUP_VERSION)"
export CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}"
if [ -x "$CARGO_HOME/bin/rustup" ]; then
  skip "rustup already installed"
else
  tmp="$(mktemp -d)"
  fetch_url \
    "https://static.rust-lang.org/rustup/archive/$RUSTUP_VERSION/x86_64-unknown-linux-gnu/rustup-init" \
    "$tmp/rustup-init" ||
    die "download failed: rustup-init $RUSTUP_VERSION"
  verify_sha256 "$tmp/rustup-init" "$RUSTUP_INIT_SHA256"
  chmod +x "$tmp/rustup-init"
  # --no-modify-path: bashrc already sources ~/.cargo/env; never let the
  # installer edit the repo-symlinked shell files.
  "$tmp/rustup-init" -y -q --no-modify-path --profile minimal \
    --default-toolchain "$RUST_TOOLCHAIN" || die "rustup-init failed"
  rm -rf "$tmp"
fi
# shellcheck disable=SC1091
. "$CARGO_HOME/env" || die "failed to load $CARGO_HOME/env"
if rustup toolchain list | grep -q "^$RUST_TOOLCHAIN"; then
  skip "rust $RUST_TOOLCHAIN toolchain present"
else
  rustup toolchain install "$RUST_TOOLCHAIN" --profile minimal ||
    die "rust $RUST_TOOLCHAIN toolchain install failed"
fi

# ----------------------------------------------------------------------------
# tree-sitter CLI (nvim-treesitter needs >= 0.26.1). Built from source at a
# pinned version: upstream prebuilts are compiled against glibc 2.39 (Ubuntu
# 24.04) and die with "GLIBC_2.39 not found" on 22.04. cargo verifies every
# crate against the crates.io registry checksums; --locked uses the crate's
# committed Cargo.lock. Installs to ~/.cargo/bin (on PATH via ~/.cargo/env).
# ----------------------------------------------------------------------------
log "tree-sitter CLI $TREE_SITTER_VERSION (source build)"
if at_pinned_version tree-sitter "$TREE_SITTER_VERSION"; then
  skip "tree-sitter $(installed_version tree-sitter) already at pin"
else
  cargo "+$RUST_TOOLCHAIN" install tree-sitter-cli \
    --version "$TREE_SITTER_VERSION" --locked --force ||
    die "tree-sitter-cli $TREE_SITTER_VERSION build failed"
fi

# ----------------------------------------------------------------------------
# Stale duplicate binaries: tools this script manages in ~/.local/bin can also
# exist elsewhere on PATH (old manual installs in /usr/local/bin, cargo, apt).
# Flag every duplicate and say how to remove it. A duplicate that comes first
# on PATH is worse than clutter: it silently wins over the pinned copy.
# ----------------------------------------------------------------------------
log "Checking for stale duplicate binaries"
stale_found=0
for tool in uv glab lazygit starship fzf lsd kitty nvim; do
  [ -x "$HOME/.local/bin/$tool" ] || continue
  while IFS= read -r path; do
    [ "$path" = "$HOME/.local/bin/$tool" ] && continue
    stale_found=1
    # dpkg-owned copies (e.g. an old apt lsd/kitty) must go through apt,
    # since deleting the file by hand leaves dpkg in an inconsistent state
    rm_hint="sudo rm $path"
    case "$path" in "$HOME"/*) rm_hint="rm $path" ;; esac
    if pkg="$(dpkg -S "$path" 2>/dev/null | head -n1 | cut -d: -f1)" && [ -n "$pkg" ]; then
      rm_hint="sudo apt-get remove $pkg"
    fi
    if [ "$(command -v "$tool")" = "$HOME/.local/bin/$tool" ]; then
      printf '    [note] stale %s at %s (shadowed; clean up with: %s)\n' \
        "$tool" "$path" "$rm_hint"
    else
      printf '    [WARN] %s on PATH resolves to %s, which shadows the pinned ~/.local/bin/%s; remove it with: %s\n' \
        "$tool" "$path" "$tool" "$rm_hint"
    fi
  done < <(type -aP "$tool" 2>/dev/null | awk '!seen[$0]++')
done
if [ "$stale_found" -eq 0 ]; then
  skip "no stale copies found"
fi

log "Provisioning complete. Run ./install to symlink dotfiles."
