#!/usr/bin/env bash
# Resolve what polybar's network module should watch and call itself.
# Sourced (never executed) by bspwmrc at login and by apply-auto.sh on every
# profile apply, since docking can move the default route to another interface.
#
# NETWORK_INTERFACE - the interface carrying the default route, falling back to
#   the built-in wifi when nothing is up yet. modules.ini reads it directly.
# NETWORK_LABEL - substituted into label-connected before polybar parses format
#   tokens, so a token survives as a token. Wi-Fi gets the literal "%essid%",
#   which polybar then keeps up to date as the machine roams between networks.
#   A wired link has no ESSID - polybar renders %essid% as junk on one - so its
#   NetworkManager connection name is resolved here and passed as plain text.

network_env() {
  local iface label
  iface="$(ip route show default 2>/dev/null | awk 'NR == 1 {print $5}')"
  iface="${iface:-wlp9s0}"

  if [ -d "/sys/class/net/$iface/wireless" ]; then
    label='%essid%'
  else
    label="$(nmcli -t -f NAME,DEVICE connection show --active 2>/dev/null |
      awk -F: -v dev="$iface" '$2 == dev { print $1; exit }')"
    # No NetworkManager, or an interface it does not manage: the interface
    # name is a poor label but an honest one.
    label="${label:-$iface}"
  fi

  export NETWORK_INTERFACE="$iface"
  export NETWORK_LABEL="$label"
}
