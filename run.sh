#!/bin/sh
export DISPLAY=:0 # Show on the main display, not on ssh
./apriltags/build/bin/aiv_apriltag_detector -N 1 -n config.txt & 
apr1=$!
./apriltags/build/bin/aiv_apriltag_detector -N 2 -n config.txt & 
apr2=$!
python3 ai.py front.txt back.txt heading.txt &
ai=$!
trap 'kill -TERM $apr1; kill -TERM $apr2; kill -TERM $ai' INT
wait
