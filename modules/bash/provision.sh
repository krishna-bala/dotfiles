#!/usr/bin/env bash
#
# bash/provision.sh - programmable completion, which bashrc loads when present.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root

log "bash-completion"
pkg_ensure bash-completion
