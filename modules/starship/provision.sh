#!/usr/bin/env bash
#
# starship/provision.sh - the prompt binary, pinned (floor) + sha256.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root
mkdir -p "$HOME/.local/bin"

STARSHIP_VERSION="v1.25.1"
STARSHIP_SHA256="4488c11ca632327d1f1f16fb2f102c0646094c35479cd5435991385da43c61ac"

log "starship $STARSHIP_VERSION"
if ! pin_satisfied starship "$STARSHIP_VERSION"; then
  install_release_binary \
    "https://github.com/starship/starship/releases/download/$STARSHIP_VERSION/starship-x86_64-unknown-linux-gnu.tar.gz" \
    "$STARSHIP_SHA256" "starship" starship
fi
report_stale_copies starship "$HOME/.local/bin/starship" || true
