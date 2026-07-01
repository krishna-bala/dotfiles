#!/bin/bash

direction=$1
[ -z "$direction" ] && exit 1

expand_cmd() {
  case $1 in
  west) echo "left -20 0" ;;
  south) echo "bottom 0 20" ;;
  north) echo "top 0 -20" ;;
  east) echo "right 20 0" ;;
  esac
}

contract_cmd() {
  case $1 in
  west) echo "right -20 0" ;;
  south) echo "top 0 20" ;;
  north) echo "bottom 0 -20" ;;
  east) echo "left 20 0" ;;
  esac
}

if bspc query -N -n "$direction.local"; then
  cmd=$(expand_cmd "$direction")
else
  cmd=$(contract_cmd "$direction")
fi

# Execute without quotes to split arguments
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/bspwm"
mkdir -p "$LOG_DIR"
bspc node -z $cmd || echo "Failed: $cmd" >>"$LOG_DIR/smart_resize.log"
