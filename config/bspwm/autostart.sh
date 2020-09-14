#!/bin/sh

#################
#### DISPLAY ####
#################

m=$(xrandr | grep " connected " | wc -l);
sleep .25;
#m=$(xrandr --listmonitors | wc -l);
if [ "$m" -eq "1" ]; then
 	xrandr --output eDP-1-1 --mode 1920x1080 --primary --dpi 161 &
elif [ "$m" -eq "2" ]; then
    xrandr --output eDP-1-1 --mode 1920x1080 --primary --output HDMI-1 --mode 1920x1080 --scale 1x1 --right-of eDP-1-1 &
else
 	xrandr --output eDP-1-1 --mode 1920x1080 --primary --dpi 161 &
fi

###################
#### AUTOSTART ####
###################

sxhkd &
nitrogen --restore &
picom --config $HOME/.config/picom/picom.ini &
xrdb $HOME/.Xresources &
$HOME/.config/polybar/launch.sh &
wmname LG3D &
udiskie &

####################
#### X settings ####
####################

xset r rate 200 75 &
xsetroot -cursor_name left_ptr &
exec ssh-agent 
