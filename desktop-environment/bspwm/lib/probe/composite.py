"""Assemble HardwareState from individual probes."""

from typing import Optional

from ..state.hardware import HardwareState
from .bspwm import BspwmProbe
from .polybar import PolybarProbe
from .xrandr import XrandrProbe


class CompositeStateProbe:
    """One call → full HardwareState. Each child probe is independently swappable."""

    def __init__(
        self,
        xrandr: Optional[XrandrProbe] = None,
        bspwm: Optional[BspwmProbe] = None,
        polybar: Optional[PolybarProbe] = None,
    ):
        self._xrandr = xrandr or XrandrProbe()
        self._bspwm = bspwm or BspwmProbe()
        self._polybar = polybar or PolybarProbe()

    def read(self) -> HardwareState:
        return HardwareState(
            outputs=self._xrandr.read(),
            bspwm_monitors=self._bspwm.read_monitors(),
            bspwm_settings=self._bspwm.read_settings(),
            polybar_pids=self._polybar.read(),
        )
