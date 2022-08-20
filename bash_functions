#!/bin/bash

##################################
### VIS SERVER / LOG FUNCTIONS ###
##################################


# Launch vis server (before vis_log)
# vis_server(){
#   cd $HOME/foxbots; bazel run vis:vis_server &
#   cd $HOME/foxbots/vis/frontend/; npm run start;
# }
# 
# vis_log(){
# 
# 	# Configure for wherever you download log folders
# 	LOG_FOLDER=$HOME/data/logs
# 
# 	# Set path with first arg
# 	LOG_PATH=$LOG_FOLDER/$1
# 
# 	cd $HOME/foxbots/; 
# 	./bazel-bin/apps/point_to_point_playback \
# 		$LOG_PATH\
#  		--start_time $2\
# 		--interactive=1\
# 		--vis\
#  		--component=planning\
# 		--v=2\
# 		 --vmodule=pick_planner=2\
#  		# --show\
#  		# --show_d435\
#  		# --reprocess=1\
#  		# --vis-leaning-loads\
#  		# --detect-semantic-depth-info\
#  		# --vis-semantic-depth\
#  		# --detect_leaning_loads\
#  		$@;
# }
# 
##################################

tmat() {
  if [ "$#" -eq 1 ] 
  then
    tmux a -t $1
  else
    echo "Usage: tmat <session-name>"
  fi
}

tmns() {
  if [ "$#" -eq 1 ]
  then
    tmux new -s $1
  else
    echo "Usage: tmns <session-name>"
  fi
}

tmks() {
  if [ "$#" -eq 1 ]
  then
    tmux kill-session -t $1
  else
    tmux kill-server
  fi
}

tmkss() {
  if [ "$#" -eq 1 ]
  then
    tmux kill-session -t $1
  else
    echo "Usage: tmkss <session-name>"
  fi
}

tmls () {
  tmux ls
}

dev() {
  tmux new-session -c $HOME/foxbots -s dev
}

swap() {
  nohup setxkbmap -option caps:swapescape &
}

rshift() {
  redshift -l 30.26:-97.72 -t 5700:3600 -m randr -v &
}

bba() {
  bazel build //...
}

bta() {
  bazel test //... --disk_cache=~/.bazel_cache
}

grom() {
  git rebase origin/master
}

gdom() {
  git difftool origin/master
}

gco() {
  if [ "$#" -eq 1 ] 
  then
    git checkout $1
  else
    echo "Usage: gco <branch-name>"
  fi
}

record() {
  simplescreenrecorder &
}

viz() {
  tmux new -s viz "cd $HOME/foxbots && ./bazel-bin/vis/vis_server &\
    cd $HOME/foxbots/vis/frontend && npm run start;"
}

jup() {
  tmux new -s jup "cd $HOME/foxbots && pyenv activate jupyter"

}

opss() {
  openvpn3 session-start --config default
}

opsl() {
  openvpn3 sessions-list
}

opsd() { 
  TEMP=$(openvpn3 sessions-list | grep Path | awk -F ": " '{print $2}'); 
  openvpn3 session-manage --path $TEMP --disconnect
}

bazecor() {
  nohup $HOME/Downloads/Bazecor-0.3.3.AppImage &
}

