#!/bin/bash
# capture-fixture.sh - Capture current monitor and BSPWM state as test fixture
# Usage: ./scripts/capture-fixture.sh <config-name>
#
# Example: ./scripts/capture-fixture.sh personal-solo

set -e

if [ -z "$1" ]; then
	echo "Usage: $0 <config-name>"
	echo "Example: $0 personal-solo"
	exit 1
fi

NAME=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BSPWM_DIR="$(dirname "$SCRIPT_DIR")"
FIXTURES_DIR="$BSPWM_DIR/tests/fixtures"

echo "Capturing fixture: $NAME"
echo "======================================"

# Capture xrandr state
echo "Capturing xrandr output..."
xrandr --query >"$FIXTURES_DIR/xrandr/${NAME}.txt"
echo "  → $FIXTURES_DIR/xrandr/${NAME}.txt"

echo "Capturing xrandr properties (EDID redacted before it touches disk)..."
xrandr --props | python3 "$SCRIPT_DIR/redact-edid.py" >"$FIXTURES_DIR/xrandr/${NAME}-props.txt"
echo "  → $FIXTURES_DIR/xrandr/${NAME}-props.txt"
echo "  EDID match keys above (paste into the profile's detection: block) ^^^"

# Capture BSPWM state
echo "Capturing BSPWM monitor list..."
bspc query -M --names >"$FIXTURES_DIR/bspc/${NAME}-monitors.txt"
echo "  → $FIXTURES_DIR/bspc/${NAME}-monitors.txt"

echo "Capturing BSPWM desktop list..."
bspc query -D --names >"$FIXTURES_DIR/bspc/${NAME}-desktops.txt"
echo "  → $FIXTURES_DIR/bspc/${NAME}-desktops.txt"

echo "Capturing per-monitor desktop assignments..."
bspc query -M | while read -r monitor; do
	monitor_name=$(bspc query -M -m "$monitor" --names)
	bspc query -D -m "$monitor" --names >"$FIXTURES_DIR/bspc/${NAME}-${monitor_name}-desktops.txt"
	echo "  → $FIXTURES_DIR/bspc/${NAME}-${monitor_name}-desktops.txt"
done

echo ""
echo "======================================"
echo "Fixture captured successfully: $NAME"
echo ""
echo "Files created:"
echo "  - xrandr/${NAME}.txt"
echo "  - xrandr/${NAME}-props.txt"
echo "  - bspc/${NAME}-monitors.txt"
echo "  - bspc/${NAME}-desktops.txt"
echo "  - bspc/${NAME}-<monitor>-desktops.txt (per monitor)"
