#!/usr/bin/env bash
# A tray host must be ready before Proton decides whether close means hide.
set -u

command -v protonvpn-app >/dev/null || exit 0
tray_state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/bspwm"
mkdir -p "$tray_state_dir"
exec 9>"$tray_state_dir/proton-tray.lock"
flock -n 9 || exit 0
tray_log="$tray_state_dir/proton-tray.log"
if [ -f "$tray_log" ] && [ "$(stat -c%s "$tray_log")" -gt 262144 ]; then
  mv "$tray_log" "$tray_log.1"
fi

tray_ready() {
  gdbus call --session --timeout 2 --dest org.freedesktop.DBus \
    --object-path /org/freedesktop/DBus \
    --method org.freedesktop.DBus.NameHasOwner \
    org.kde.StatusNotifierWatcher 2>/dev/null | grep -q '(true,)'
}

bridge="$HOME/.local/bin/snixembed-proton"
if ! tray_ready && [ -x "$bridge" ]; then
  # --fork returns once the watcher owns its D-Bus name. Force X11 even if
  # the session has inherited a Wayland GDK preference. Close the lock fd
  # in background children so a later bspwm reload can run this helper.
  GDK_BACKEND=x11 timeout 5s "$bridge" --fork 9>&- </dev/null >>"$tray_log" 2>&1
fi

if pgrep -u "$(id -u)" -x protonvpn-app >/dev/null; then
  exit 0
fi
if tray_ready; then
  setsid -f protonvpn-app --start-minimized 9>&- </dev/null >>"$tray_log" 2>&1
else
  printf '%s Tray bridge unavailable; starting Proton visibly. Run modules/x11/provision-tray.sh.\n' \
    "$(date -Iseconds)" >>"$tray_log"
  setsid -f protonvpn-app 9>&- </dev/null >>"$tray_log" 2>&1
fi
