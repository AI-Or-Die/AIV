# Installs the AIV dependencies
sudo apt-get update

# Apriltags dependencies
sudo apt-get install subversion cmake libopencv-dev libeigen3-dev libv4l-dev

# Run dependencies
sudo apt-get install tmux python3 python3-pip
pip3 install pyserial
touch front.txt back.txt

# OpenCV
# The following was taken from https://github.com/milq/milq/blob/master/scripts/bash/install-opencv.sh
# and modified for the latest OpenCV version

# 1. KEEP UBUNTU OR DEBIAN UP TO DATE

sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y dist-upgrade
sudo apt-get -y autoremove


# 2. INSTALL THE DEPENDENCIES

# Build tools:
sudo apt-get install -y build-essential cmake

# GUI (if you want to use GTK instead of Qt, replace 'qt5-default' with 'libgtkglext1-dev' and remove '-DWITH_QT=ON' option in CMake):
sudo apt-get install -y libgtkglext1-dev libvtk6-dev

# Media I/O:
sudo apt-get install -y zlib1g-dev libjpeg-dev libwebp-dev libpng-dev libtiff5-dev libjasper-dev libopenexr-dev libgdal-dev

# Video I/O:
sudo apt-get install -y libdc1394-22-dev libavcodec-dev libavformat-dev libswscale-dev libtheora-dev libvorbis-dev libxvidcore-dev libx264-dev yasm libopencore-amrnb-dev libopencore-amrwb-dev libv4l-dev libxine2-dev

# Parallelism and linear algebra libraries:
sudo apt-get install -y libtbb-dev libeigen3-dev

# Python:
sudo apt-get install -y python-dev python-tk python-numpy python3-dev python3-tk python3-numpy

# Java:
sudo apt-get install -y ant default-jdk

# Documentation:
sudo apt-get install -y doxygen


# 3. INSTALL THE LIBRARY (YOU CAN CHANGE '3.2.0' FOR THE LAST STABLE VERSION)

sudo apt-get install -y unzip wget
wget https://github.com/opencv/opencv/archive/3.3.0.zip
unzip 3.3.0.zip
rm 3.3.0.zip
mv opencv-3.3.0 OpenCV
cd OpenCV
mkdir build
cd build
cmake -DWITH_OPENGL-ES=ON -DWITH_OPENGL=OFF -DFORCE_VTK=ON -DWITH_TBB=ON -DWITH_GDAL=ON -DWITH_XINE=ON -DBUILD_EXAMPLES=ON -DENABLE_PRECOMPILED_HEADERS=OFF ..
make -j4
sudo make install
sudo ldconfig
rm -rf OpenCV opencv-3.3.0
