# Proton VPN in the Polybar tray

Polybar's `internal/tray` uses XEmbed. Proton VPN GTK4 publishes a
StatusNotifierItem (SNI), so bspwm starts a compatible bridge before Proton.

`bspwm/scripts/start-proton-tray.sh` starts
`~/.local/bin/snixembed-proton`, waits for its D-Bus watcher, then launches
Proton with `--start-minimized`. It avoids duplicate processes, leaves an
already-running Proton alone, and falls back to a visible window if the
bridge is unavailable. Right-click the Proton tray icon for Show/Hide and
connection controls. Closing the window hides it; choosing Quit exits it.

## Installation

The desktop provisioner calls `provision-tray.sh`. It can also be run alone:

```sh
bash modules/x11/provision-tray.sh
```

The build pins upstream snixembed to commit
`6339bafee3c766be3525f20f9766b04e5860536f` and applies
`patches/snixembed-optional-properties.patch`. The installed version includes
the patch hash, so repeat runs skip the build and patch changes rebuild it.
The unmanaged `/usr/bin/snixembed` and Proton's package files are untouched.

## Compatibility fix

On Ubuntu 24.04.5 with Proton VPN 4.18.2, the old bridge aborts in
`status_notifier_item_dbus_proxy_get_icon_pixmap`. Proton omits IconPixmap
and ToolTip from GetAll and returns a string for unknown Get requests.
Vala's generated getters attempt to decode that string as an array/struct,
causing a GLib assertion. The patch checks the cached D-Bus types before
using those getters and falls back to the title for the tooltip.

Verification on September 18, 2026: reproduced the old crash with Proton's
actual TrayIcon class without connecting another VPN client; the patched
bridge survived the same icon and its menu decoded successfully.
The user confirmed the real tray worked after Proton was relaunched.
Shell syntax and ShellCheck passed; a second provisioning run was a no-op.
A full logout/login has not been tested.

## Portability

The source patch has no machine-specific assumptions. It is verified on
this Ubuntu 24.04.5 X11/bspwm/Polybar desktop with Proton 4.18.2. The same
setup on other 24.04 machines is expected to work. Ubuntu 22.04 has the
build dependencies, but its build and full Proton integration remain
untested; the existing server-role CI does not exercise this tray code.
Run the installer on each target to build against its own libraries,
rather than copying the 24.04 binary to 22.04. A desktop with a working
native SNI host generally does not need this bridge.

Logs: `~/.local/state/bspwm/proton-tray.log`. Nonfatal GTK/GIO warnings may
remain for omitted properties; these no longer abort the bridge. Review
the patch when upstream handles these properties, or when Proton changes
its tray implementation.
