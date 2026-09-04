#!/bin/bash

direction=$1
[ -z "$direction" ] && exit 1

if target_node=$(bspc query -N -n "$direction"); then
  current_monitor=$(bspc query -M -n)
  target_monitor=$(bspc query -M -n "$target_node")

  if [ "$current_monitor" = "$target_monitor" ]; then
    cmd="node -s $direction --follow"
  else
    cmd="node -m $direction --follow"
  fi
else
  cmd="node -m $direction --follow"
fi

# Execute the command
bspc $cmd || notify-send "Failed: bspc $cmd"
