#!/usr/bin/env bash
# Render the selected connection with the appropriate wireless/wired icon.
set -u

interface="${NETWORK_INTERFACE:-}"
if [[ -z "$interface" ]]; then
    printf '󰈀 Offline\n'
    exit 0
fi

if [[ -d "/sys/class/net/$interface/wireless" ]]; then
    label="$(nmcli -t -g GENERAL.CONNECTION device show "$interface" 2>/dev/null |
        awk 'NR == 1 { print; exit }')"
    label="${label:-Offline}"

    signal_dbm=""
    if command -v iw >/dev/null 2>&1; then
        signal_dbm="$(iw dev "$interface" link 2>/dev/null |
            awk '$1 == "signal:" { print $2; exit }')"
    fi

    if [[ "$signal_dbm" =~ ^-?[0-9]+$ ]]; then
        if (( signal_dbm >= -50 )); then
            icon="󰤥"
        elif (( signal_dbm >= -60 )); then
            icon="󰤢"
        elif (( signal_dbm >= -70 )); then
            icon="󰤟"
        else
            icon="󰤯"
        fi
    else
        icon=""
    fi

    printf '%s %s\n' "$icon" "$label"
else
    label="${NETWORK_LABEL:-$interface}"
    printf '󰈀 %s\n' "$label"
fi
