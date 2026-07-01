#!/usr/bin/env bash
#
# provision.sh - runs both provisioning scripts in this repo: the shell/
# terminal/dev tooling (provision-shell.sh) and the X11/WM stack
# (desktop-environment/provision.sh). Each is independently idempotent and
# safe to re-run; run either one directly to provision just that half.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/provision-shell.sh"
"$SCRIPT_DIR/desktop-environment/provision.sh"
