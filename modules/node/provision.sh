#!/usr/bin/env bash
#
# node/provision.sh - nvm (pinned installer + sha256) and the current node
# LTS. bashrc loads nvm from the same NVM_DIR this script installs to.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root

NVM_VERSION="v0.40.3"
NVM_INSTALL_SHA256="2d8359a64a3cb07c02389ad88ceecd43f2fa469c06104f92f98df5b6f315275f"

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
