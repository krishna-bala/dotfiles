#!/usr/bin/env bash
# Re-detect topology and apply the best-matching profile via the
# reconciliation pipeline. Bound to super+alt+r in sxhkdrc.
#
# Logs to $XDG_STATE_HOME/bspwm/apply-auto.log. Notifies via notify-send
# only on failure — success is silent (the user sees the visual result).

set -uo pipefail

LOG="${XDG_STATE_HOME:-$HOME/.local/state}/bspwm/apply-auto.log"
mkdir -p "$(dirname "$LOG")"

# Keep the log bounded (it grows on every invocation)
if [ -f "$LOG" ]; then
    tail -n 2000 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_MANAGER="$(command -v monitor-manager || echo "$HOME/.local/bin/monitor-manager")"

# Keep polybar's network module on the interface carrying the default route;
# docking can move it, and the bars are relaunched below either way.
# shellcheck source=network-env.sh
. "$SCRIPT_DIR/network-env.sh"
network_env

{
    echo "=== apply-auto run at $(date) ==="
    "$MONITOR_MANAGER" apply-all --force
} >>"$LOG" 2>&1

if [ $? -ne 0 ]; then
    notify-send -u critical "monitor-manager" "apply-auto failed — see $LOG"
    exit 1
fi

# Re-register Blueman with Polybar after the tray is recreated.
if pgrep -x blueman-applet >/dev/null; then
    pkill -x blueman-applet
    sleep 1
fi
setsid -f blueman-applet
