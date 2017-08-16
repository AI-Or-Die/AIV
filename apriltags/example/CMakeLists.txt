cmake_minimum_required (VERSION 2.6)

link_libraries(apriltags)

add_executable(apriltags_demo apriltags_demo.cpp Serial.cpp)
pods_install_executables(apriltags_demo)

add_executable(imu imu.cpp Serial.cpp)
pods_install_executables(imu)

add_executable(aiv_apriltag_detector aiv_apriltag_detector.cpp Serial.cpp)
pods_install_executables(aiv_apriltag_detector)
