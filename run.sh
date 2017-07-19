#!/bin/sh
./apriltags/build/bin/front_back_camera_demo -N 1 -n config.txt & 
apr1=$!
./apriltags/build/bin/front_back_camera_demo -N 2 -n config.txt & 
apr2=$!
trap 'kill -TERM $apr1; kill -TERM $apr2' INT
./apriltags/build/bin/get_heading front.txt back.txt heading.txt
