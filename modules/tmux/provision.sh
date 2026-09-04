#!/usr/bin/env bash
#
# tmux/provision.sh - the distro tmux; tmux.conf needs nothing newer.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root

log "tmux"
pkg_ensure tmux
