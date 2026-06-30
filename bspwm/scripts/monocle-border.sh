#!/bin/bash
# Per-desktop border_width: thick for nodes on monocle desktops, thin elsewhere.
# bspwm's global border_width leaks across monitors, so apply per-node instead.

MONOCLE=7
OTHER=3

apply_borders() {
    local desktop layout node
    while read -r desktop; do
        layout=$(bspc query -T -d "$desktop" | jq -r '.layout')
        if [ "$layout" = "monocle" ]; then
            width=$MONOCLE
        else
            width=$OTHER
        fi
        while read -r node; do
            [ -n "$node" ] && bspc config -n "$node" border_width "$width"
        done < <(bspc query -N -d "$desktop" -n .window)
    done < <(bspc query -D)
}

apply_borders
bspc subscribe desktop_layout node_add node_transfer | while read -r _; do
    apply_borders
done
