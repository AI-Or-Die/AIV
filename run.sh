./apriltags/build/bin/front_back_camera_demo -N 2 -n config.txt -W 640 -H 360 &
sleep 2
./apriltags/build/bin/front_back_camera_demo -N 1 -n config.txt -W 640 -H 360 &
wait
