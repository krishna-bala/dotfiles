#!/bin/bash

SOCKET_PATH="/tmp/kitty-$USER"
KITTY="$HOME/.local/bin/kitty"
font_size="12.0"

if [ ! -x "$KITTY" ]; then
  printf 'kitty executable not found: %s\n' "$KITTY" >&2
  exit 1
fi

# --home flag forces local home directory (avoids inheriting kitten ssh sessions)
CWD="current"
if [ "$1" = "--home" ]; then
  CWD="$HOME"
  shift
fi

# If socket exists and is alive, use remote control to create a new OS window
if [ -S "$SOCKET_PATH" ] && "$KITTY" @ --to "unix:$SOCKET_PATH" ls &>/dev/null; then
  # Note: Cannot override font_size with remote control, uses existing instance settings
  exec "$KITTY" @ --to "unix:$SOCKET_PATH" launch --type=os-window --cwd="$CWD" "$@"
else
  rm -f "$SOCKET_PATH"
  exec "$KITTY" --listen-on "unix:$SOCKET_PATH" --override "font_size=$font_size" --directory="$HOME" "$@"
fi
