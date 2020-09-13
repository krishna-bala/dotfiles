#!/usr/bin/env sh

## Add this to your wm startup file.

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

# Launch bar1 and bar2
m=$(xrandr --listmonitors | wc -l);
if [ "$m" -eq "2" ]
then
	polybar -c ~/.config/polybar/config.ini laptop &
elif [ "$m" -eq "3" ]
then
	polybar -c ~/.config/polybar/config.ini laptop &
	polybar -c ~/.config/polybar/config.ini monitor1 &
else
	polybar -c ~/.config/polybar/config.ini laptop &
fi


