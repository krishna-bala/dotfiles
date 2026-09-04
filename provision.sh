#!/usr/bin/env bash
#
# provision.sh - installs the tools the selected modules' configs assume,
# by running each module's provision.sh in role order.
#
#   ./provision.sh --roles desktop     # first run on a machine of that kind
#   ./provision.sh                     # re-apply the saved selection
#
# Every module script is independently runnable and idempotent: pins are
# floors (lib/provision-lib.sh), every download is sha256-verified, and any
# failure aborts loudly. Run ./install afterwards to link the configs.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/provision-lib.sh
. "$REPO_ROOT/lib/provision-lib.sh"
# shellcheck source=lib/roles.sh
. "$REPO_ROOT/lib/roles.sh"

usage() {
  cat <<EOF
usage: $0 [--roles <role>[,<role>...]] [--modules <module>[,<module>...]]

Installs the tools the selected modules' configs assume, running each
module's provision.sh in role order. With no selection, the one saved by
the last run ($ROLES_FILE) is re-applied.

  --roles r[,r]      roles to provision (available: $(list_roles | paste -sd' '))
  --modules m[,m]    extra modules, or a selection with no role
  -h, --help         show this help

Run ./install afterwards to link the configs.
EOF
}

require_not_root
PARSE_TARGETS_STRICT=1 parse_targets "$@"
mapfile -t MODULES < <(resolve_modules "${TARGETS[@]}")
check_requires "${MODULES[@]}"

init_provision_log "$REPO_ROOT/provision.log"
require_supported_platform
mkdir -p "$HOME/.local/bin" "$HOME/.local/share"

log "Provisioning started: ${MODULES[*]}"
for m in "${MODULES[@]}"; do
  script="$REPO_ROOT/modules/$m/provision.sh"
  [ -x "$script" ] || continue
  log "module $m"
  "$script"
done

save_targets "${TARGETS[@]}"
log "Provisioning complete. Run ./install to link the configs."
