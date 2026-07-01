"""Pure data types for current and desired system state.

`hardware.HardwareState` is what the system *is* — read by probes from xrandr,
bspwm, and polybar.

`desired.DesiredState` is what a profile *wants* — produced by `compile_desired`
from a Profile plus an alias-to-output mapping.

Neither type touches the system. Both are frozen dataclasses with tuple-typed
collections so they can be safely held, compared, and used as inputs to a pure
reconciler.
"""
