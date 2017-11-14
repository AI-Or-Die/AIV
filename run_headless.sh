#!/bin/sh
lsusb | grep "Logitech" >> camera1.txt
echo "\n" >> camera1.txt
date >> camera1.txt
DIR=`dirname $0`
cd ${DIR}
tmux new-session -d -s aiv
tmux split-window -t aiv ./apriltags/build/bin/aiv_apriltag_detector -N 1 -n config.txt -d
sleep 2
tmux split-window -t aiv ./apriltags/build/bin/aiv_apriltag_detector  -N 2 -n config.txt -d
sleep 2
tmux split-window -t aiv 'python3 ai.py front.txt back.txt heading.txt'
sleep 2
tmux select-layout -t aiv main-horizontal
tmux select-pane -U -t aiv
tmux attach -t aiv
