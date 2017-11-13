### Camera Setup
```
python3 setupcameras.py
```
This will set up from and back cameras

### On Startup
```
./run_headless.sh
```
This runs automatically and sets up a tmux session for 
1. front camera tag detector
2. back camera tag detector
3. main AIV controller in ai.py 

### Other

The april tag detector source is in
* apriltags/example/aiv_apriltag_detector.cpp
* apriltags/example/apriltags_demo.cpp
