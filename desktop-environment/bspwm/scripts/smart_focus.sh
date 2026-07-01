#!/bin/bash

direction=$1
[ -z "$direction" ] && exit 1

if bspc query -N -n "$direction"; then
  cmd="node -f $direction"
else
  cmd="monitor -f $direction"
fi

# Execute without quotes to split arguments
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/bspwm"
mkdir -p "$LOG_DIR"
bspc $cmd || echo "Failed: $cmd" >>"$LOG_DIR/smart_focus.log"
