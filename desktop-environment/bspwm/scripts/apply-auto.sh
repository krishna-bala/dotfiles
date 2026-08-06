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
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT" || {
    notify-send -u critical "monitor-manager" "apply-auto: cannot cd to $PROJECT_ROOT"
    exit 1
}

# Keep Polybar's network module on the interface carrying the default route.
NETWORK_INTERFACE="$(ip route show default 2>/dev/null | awk 'NR == 1 {print $5}')"
export NETWORK_INTERFACE="${NETWORK_INTERFACE:-wlp9s0}"

{
    echo "=== apply-auto run at $(date) ==="
    "$HOME/.local/bin/uv" run python monitor-manager.py apply-all --force
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
