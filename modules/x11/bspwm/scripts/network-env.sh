#!/usr/bin/env bash
# Resolve what polybar's network module should watch and call itself.
# Sourced (never executed) by bspwmrc at login and by apply-auto.sh on every
# profile apply, since docking can move the default route to another interface.
#
# NETWORK_INTERFACE - the interface carrying the default route, falling back to
#   the built-in wifi when nothing is up yet. network-label.sh reads it.
# NETWORK_LABEL - the NetworkManager connection name used by the Polybar
#   network-label custom module for wired links. It is unset for wireless,
#   whose current SSID is resolved directly so roaming needs no bar restart.

network_env() {
  local iface label
  iface="$(ip route show default 2>/dev/null | awk 'NR == 1 {print $5}')"
  # Fallback when no default route is up yet: the host's wifi interface
  # from host.env, exported by bspwmrc.
  iface="${iface:-${NETWORK_FALLBACK_IFACE:-wlan0}}"

  if [ -d "/sys/class/net/$iface/wireless" ]; then
    unset NETWORK_LABEL
  else
    label="$(nmcli -t -f NAME,DEVICE connection show --active 2>/dev/null |
      awk -F: -v dev="$iface" '$2 == dev { print $1; exit }')"
    # No NetworkManager, or an interface it does not manage: the interface
    # name is a poor label but an honest one.
    label="${label:-$iface}"
    export NETWORK_LABEL="$label"
  fi

  export NETWORK_INTERFACE="$iface"
}
