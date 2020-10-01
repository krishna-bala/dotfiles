#!/usr/bin/env sh

## Add this to your wm startup file.

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

# Launch bar1 and bar2
m=$(xrandr | grep " connected " | wc -l);
sleep 0.25
lid=$(cat /proc/acpi/button/lid/LID/state | grep "state:    " | awk '{ print $2 }')


if [ "$m" -eq "1" ]; then
	polybar -c ~/.config/polybar/config.ini laptop &
#elif [ "$m" -eq "2" ]; then
#	polybar -c ~/.config/polybar/config.ini laptop &
#	polybar -c ~/.config/polybar/config.ini monitor1 &
elif [ "$m" -eq "3" ]; then
	if [ "$lid" = "closed" ]; then
		polybar -c ~/.config/polybar/config.ini monitor1 &
		polybar -c ~/.config/polybar/config.ini monitor2 &
	else
		polybar -c ~/.config/polybar/config.ini laptop &
		polybar -c ~/.config/polybar/config.ini monitor1 &
		polybar -c ~/.config/polybar/config.ini monitor2 &
	fi
fi


