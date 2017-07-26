#!/bin/sh
./apriltags/build/bin/front_back_camera_demo -N 1 -n config.txt & 
apr1=$!
./apriltags/build/bin/front_back_camera_demo -N 2 -n config.txt & 
apr2=$!
python3 ai.py front.txt back.txt heading.txt &
ai=$!
trap 'kill -TERM $apr1; kill -TERM $apr2; kill -TERM $ai' INT
wait
