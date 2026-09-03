"""Display detection and xrandr control service."""

import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Protocol

from .edid import hash_edid
from .exceptions import DisplayConfigurationError, HardwareDetectionError


@dataclass
class Monitor:
    """Represents a physical monitor detected by xrandr."""

    output: str  # "eDP-1", "DP-0.1", etc.
    edid: str  # Truncated hash of the full EDID (match key, not the raw bytes)
    manufacturer: str  # "Dell", "Acer", etc.
    model: str  # "G3223D", etc.
    resolution: str  # "2560x1440"
    connected: bool


class XrandrExecutor(Protocol):
    """Protocol for executing xrandr commands."""

    def get_props_output(self) -> str:
        """Get output from xrandr --props command.

        Returns:
            Raw xrandr --props output as string
        """
        ...

    def execute_command(self, command: List[str]) -> None:
        """Execute an xrandr command.

        Args:
            command: List of command arguments (e.g., ["xrandr", "--output", "eDP-1", "--auto"])
        """
        ...


class SubprocessXrandrExecutor:
    """Real implementation that executes xrandr via subprocess."""

    def get_props_output(self) -> str:
        """Get output from xrandr --props command.

        Raises:
            HardwareDetectionError: If xrandr command fails
        """
        try:
            result = subprocess.run(
                ["xrandr", "--props"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise HardwareDetectionError(
                f"Failed to run xrandr --props: {e.stderr}",
                xrandr_output=e.stdout,
            ) from e
        except FileNotFoundError as e:
            raise HardwareDetectionError(
                "xrandr command not found - ensure xorg-xrandr is installed"
            ) from e

    def execute_command(self, command: List[str]) -> None:
        """Execute an xrandr command.

        Raises:
            DisplayConfigurationError: If xrandr command fails
        """
        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise DisplayConfigurationError(
                f"xrandr command failed: {e.stderr}",
                command=command,
                stderr=e.stderr,
            ) from e


class DisplayService:
    """Service for display detection and xrandr configuration."""

    def __init__(self, executor: Optional[XrandrExecutor] = None, dry_run: bool = False):
        """Initialize display service.

        Args:
            executor: XrandrExecutor implementation (defaults to SubprocessXrandrExecutor)
            dry_run: If True, print commands instead of executing them
        """
        self.executor = executor or SubprocessXrandrExecutor()
        self.dry_run = dry_run

    def detect_monitors(self) -> List[Monitor]:
        """Detect connected monitors via xrandr.

        Returns:
            List of Monitor objects for all detected displays
        """
        output = self.executor.get_props_output()
        return self._parse_xrandr_output(output)

    def _parse_xrandr_output(self, xrandr_output: str) -> List[Monitor]:
        """Parse xrandr --props output to extract monitor information.

        Args:
            xrandr_output: Raw output from xrandr --props

        Returns:
            List of Monitor objects
        """
        monitors = []
        lines = xrandr_output.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Look for output lines (e.g., "eDP-1 connected primary 1920x1080+0+0")
            output_match = re.match(r"^(\S+)\s+(connected|disconnected)", line)

            if output_match:
                output_name = output_match.group(1)
                connected = output_match.group(2) == "connected"

                # Extract resolution if connected
                resolution = "unknown"
                if connected:
                    res_match = re.search(r"(\d+x\d+)\+\d+\+\d+", line)
                    if res_match:
                        resolution = res_match.group(1)

                # Look ahead for EDID in next lines
                edid = ""
                manufacturer = "Unknown"
                model = "Unknown"

                j = i + 1
                while j < len(lines) and lines[j].startswith("\t"):
                    # Check for EDID section
                    if lines[j].strip() == "EDID:":
                        # Collect EDID hex lines
                        edid_lines = []
                        k = j + 1
                        while k < len(lines) and re.match(r"^\t\t[0-9a-f]{32}", lines[k]):
                            edid_lines.append(lines[k].strip())
                            k += 1
                        edid = "".join(edid_lines)

                        # Parse manufacturer and model from the raw EDID, then
                        # collapse it to its match key -- the raw bytes (and
                        # the per-unit serial they carry) never leave this scope.
                        if edid:
                            manufacturer, model = self._parse_edid_info(edid)
                            edid = hash_edid(edid)

                        j = k - 1  # Adjust index
                    j += 1

                # Create Monitor object
                monitor = Monitor(
                    output=output_name,
                    edid=edid,
                    manufacturer=manufacturer,
                    model=model,
                    resolution=resolution,
                    connected=connected,
                )
                monitors.append(monitor)

            i += 1

        return monitors

    def _parse_edid_info(self, edid: str) -> tuple[str, str]:
        """Extract manufacturer and model from EDID hex string.

        EDID format (simplified):
        - Bytes 8-9: Manufacturer ID (3 letters compressed into 2 bytes)
        - Bytes 54-71: Descriptor blocks (may contain model name)

        Args:
            edid: EDID hex string (concatenated, no spaces)

        Returns:
            Tuple of (manufacturer, model) strings
        """
        if len(edid) < 256:  # EDID should be 128 or 256 bytes (256 or 512 hex chars)
            return ("Unknown", "Unknown")

        try:
            # Extract manufacturer ID from bytes 8-9 (chars 16-19)
            mfg_bytes = edid[16:20]
            mfg_id = int(mfg_bytes, 16)

            # Decode 3 letters from compressed format
            # Format: 0CCCCCBBBBBAAAAA (5 bits each, A=1 is 'A')
            letter1 = chr(((mfg_id >> 10) & 0x1F) + 64)
            letter2 = chr(((mfg_id >> 5) & 0x1F) + 64)
            letter3 = chr((mfg_id & 0x1F) + 64)
            manufacturer = f"{letter1}{letter2}{letter3}"

            # Model name extraction is complex and optional
            # For now, use a placeholder
            model = "Generic"

            return (manufacturer, model)

        except (ValueError, IndexError):
            return ("Unknown", "Unknown")

    def get_monitor_by_output(self, output: str, monitors: List[Monitor]) -> Optional[Monitor]:
        """Get monitor from detected list by output name.

        Args:
            output: Output name (e.g., "eDP-1")
            monitors: List of detected monitors

        Returns:
            Monitor object or None if not found
        """
        for monitor in monitors:
            if monitor.output == output:
                return monitor
        return None

