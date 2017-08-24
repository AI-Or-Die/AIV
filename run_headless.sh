#!/bin/sh
DIR=`dirname $0`
cd ${DIR}
tmux new-session -d -s aiv
tmux split-window -t aiv ./apriltags/build/bin/aiv_apriltag_detector -N 1 -n config.txt -d
#apr1=$!
tmux split-window -t aiv ./apriltags/build/bin/aiv_apriltag_detector -N 2 -n config.txt -d
#apr2=$!
tmux split-window -t aiv python3 ai.py front.txt back.txt heading.txt
tmux select-layout -t aiv main-horizontal
tmux select-pane -U -t aiv
#ai=$!
#trap 'kill -TERM $apr1; kill -TERM $apr2; kill -TERM $ai' INT
#wait
