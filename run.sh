./apriltags/build/bin/front_back_camera_demo -N 1 -n config.txt -W 640 -H 360 -O front.txt &
./apriltags/build/bin/front_back_camera_demo -N 2 -n config.txt -W 640 -H 360 -O back.txt &
./apriltags/build/bin/get_heading front.txt back.txt heading.txt
wait
