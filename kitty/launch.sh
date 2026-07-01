#!/bin/bash

SOCKET_PATH="/tmp/kitty-$USER"
font_size="12.0"

# --home flag forces local home directory (avoids inheriting kitten ssh sessions)
CWD="current"
if [ "$1" = "--home" ]; then
  CWD="$HOME"
  shift
fi

# If socket exists and is alive, use remote control to create a new OS window
if [ -S "$SOCKET_PATH" ] && kitty @ --to "unix:$SOCKET_PATH" ls &>/dev/null; then
  # Note: Cannot override font_size with remote control, uses existing instance settings
  exec kitty @ --to "unix:$SOCKET_PATH" launch --type=os-window --cwd="$CWD" "$@"
else
  rm -f "$SOCKET_PATH"
  exec kitty --listen-on "unix:$SOCKET_PATH" --override "font_size=$font_size" --directory="$HOME" "$@"
fi
