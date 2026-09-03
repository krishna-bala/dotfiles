#!/usr/bin/env bash
#
# wacom/provision.sh - the X input driver wacominit's xsetwacom talks to.

set -euo pipefail

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/provision-lib.sh
. "$MODULE_DIR/../../lib/provision-lib.sh"

require_not_root

log "wacom driver"
pkg_ensure xserver-xorg-input-wacom
