#!/bin/bash

# Toggle polybar visibility on the focused monitor only

FOCUSED_MONITOR=$(bspc query -M -m focused --names)
if [ -z "$FOCUSED_MONITOR" ]; then
  echo "Error: Could not determine focused monitor"
  exit 1
fi

# Find the polybar PID running on the focused monitor
POLYBAR_PID=""
for pid in $(pgrep -x polybar); do
  # Read the MONITOR env var from the process environment
  mon=$(tr '\0' '\n' < /proc/"$pid"/environ 2>/dev/null | grep -m1 '^MONITOR=' | cut -d= -f2)
  if [ "$mon" = "$FOCUSED_MONITOR" ]; then
    POLYBAR_PID="$pid"
    break
  fi
done

if [ -z "$POLYBAR_PID" ]; then
  echo "Error: No polybar instance found for monitor $FOCUSED_MONITOR"
  exit 1
fi

# Use current padding to determine visibility state. The padding value is
# profile-dependent (bar height varies), so save it on hide and restore the
# saved value on show instead of hardcoding one number.
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/bspwm"
mkdir -p "$STATE_DIR"
PAD_FILE="$STATE_DIR/top_padding.$FOCUSED_MONITOR"
CURRENT_PADDING=$(bspc config -m "$FOCUSED_MONITOR" top_padding)

if [ "$CURRENT_PADDING" -gt 0 ]; then
  echo "$CURRENT_PADDING" >"$PAD_FILE"
  polybar-msg -p "$POLYBAR_PID" cmd hide
  bspc config -m "$FOCUSED_MONITOR" top_padding 0
else
  SAVED_PADDING=$(cat "$PAD_FILE" 2>/dev/null)
  case "$SAVED_PADDING" in
  '' | *[!0-9]*) SAVED_PADDING=60 ;;
  esac
  polybar-msg -p "$POLYBAR_PID" cmd show
  bspc config -m "$FOCUSED_MONITOR" top_padding "$SAVED_PADDING"
fi

