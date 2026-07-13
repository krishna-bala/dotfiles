#!/usr/bin/env bash
#
# provision.sh - runs both provisioning scripts in this repo: the shell/
# terminal/dev tooling (provision-shell.sh) and the X11/WM stack
# (desktop-environment/provision.sh). Pass --no-desktop to provision only
# the shell half (e.g. on remote machines with no desktop). Each script is
# independently idempotent and safe to re-run; run either one directly to
# provision just that half.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DESKTOP=true
for arg in "$@"; do
  case "$arg" in
    --no-desktop) DESKTOP=false ;;
    *)
      echo "usage: $0 [--no-desktop]" >&2
      exit 2
      ;;
  esac
done

"$SCRIPT_DIR/provision-shell.sh"
if "$DESKTOP"; then
  "$SCRIPT_DIR/desktop-environment/provision.sh"
fi
