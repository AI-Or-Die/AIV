cmake_minimum_required (VERSION 2.6)

link_libraries(apriltags)

add_executable(apriltags_demo apriltags_demo.cpp Serial.cpp)
pods_install_executables(apriltags_demo)

add_executable(imu imu.cpp Serial.cpp)
pods_install_executables(imu)

add_executable(front_back_camera_demo front_back_camera_demo.cpp Serial.cpp)
pods_install_executables(front_back_camera_demo)
