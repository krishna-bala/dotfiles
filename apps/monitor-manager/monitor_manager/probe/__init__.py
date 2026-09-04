"""Probes that read system state into HardwareState.

Each probe owns one source: xrandr, bspwm, or polybar. They are read-only —
the executor mutates, probes only observe. CompositeStateProbe assembles the
parts into a single HardwareState.

Probes accept Protocol-typed runners so tests substitute in fakes without
touching subprocess.
"""
