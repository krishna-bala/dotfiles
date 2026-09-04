#!/usr/bin/env bash
#
# nvim/provision.sh - neovim and what its config (a separate repo) builds
# with: a pinned rust toolchain (mason builds native extensions with cargo)
# and the tree-sitter CLI, source-built at a pinned version. bashrc's
# EDITOR, gitconfig's difftool/mergetool, and lazygit's edit command all
# assume nvim.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root
mkdir -p "$HOME/.local/bin"

# neovim publishes no checksum file; this sha256 was computed from the
# downloaded release artifact when the pin was set, so every machine gets a
# byte-identical copy of what was reviewed.
NVIM_VERSION="v0.12.3"
NVIM_SHA256="c441b547142860bf01bcce39e36cbed185c41112813e15443b16e5237750724d"
# rustup-init sha256 is upstream's published checksum for this archive version
RUSTUP_VERSION="1.29.0"
RUSTUP_INIT_SHA256="4acc9acc76d5079515b46346a485974457b5a79893cfb01112423c89aeb5aa10"
RUST_TOOLCHAIN="1.96.1"
TREE_SITTER_VERSION="0.26.10"

# libclang-dev: the tree-sitter CLI source build pulls in rquickjs-sys, whose
# bindgen build step needs libclang.so at compile time.
log "Build packages"
pkg_ensure build-essential pkg-config libclang-dev

# ----------------------------------------------------------------------------
# neovim (upstream bundle -> ~/.local/nvim.app). 22.04's apt neovim (0.6) is
# far too old for a current config.
# ----------------------------------------------------------------------------
log "neovim $NVIM_VERSION"
if ! pin_satisfied nvim "$NVIM_VERSION"; then
  install_release_bundle \
    "https://github.com/neovim/neovim/releases/download/$NVIM_VERSION/nvim-linux-x86_64.tar.gz" \
    "$NVIM_SHA256" nvim.app 1 nvim
fi

# ----------------------------------------------------------------------------
# rust toolchain (rustup, pinned)
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
if ! pin_satisfied tree-sitter "$TREE_SITTER_VERSION"; then
  cargo "+$RUST_TOOLCHAIN" install tree-sitter-cli \
    --version "$TREE_SITTER_VERSION" --locked --force ||
    die "tree-sitter-cli $TREE_SITTER_VERSION build failed"
fi

report_stale_copies nvim "$HOME/.local/bin/nvim" || true
