#!/bin/sh
lsusb | grep "Logitech" >> camera2.txt
echo "\n" >> camera2.txt
date >> camera2.txt
DIR=`dirname $0`
cd ${DIR}
tmux new-session -d -s aiv
tmux split-window -t aiv ./apriltags/build/bin/aiv_apriltag_detector -N 1 -n config.txt
tmux split-window -t aiv ./apriltags/build/bin/aiv_apriltag_detector  -N 2 -n config.txt
tmux split-window -t aiv 'python3 ai.py front.txt back.txt heading.txt' 
tmux select-layout -t aiv main-horizontal
tmux select-pane -U -t aiv
tmux attach -t aiv
