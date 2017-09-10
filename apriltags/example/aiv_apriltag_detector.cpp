/**
 * @file april_tags.cpp
 * @brief Example application for April tags library
 * @author: Michael Kaess
 *
 * Opens the first available camera (typically a built in camera in a
 * laptop) and continuously detects April tags in the incoming
 * images. Detections are both visualized in the live image and shown
 * in the text console. Optionally allows selecting of a specific
 * camera in case multiple ones are present and specifying image
 * resolution as long as supported by the camera.
 */

using namespace std;

#include <iostream>
#include <cstring>
#include <vector>
#include <list>
#include <sys/time.h>
#include <fstream>
#include <csignal>
#include <string>
#include <regex>
#include <cmath>
#include <thread>
#include <memory>
#include <atomic>
#include <mutex>

const string usage = "\n"
  "Usage:\n"
  "  apriltags_demo [OPTION...] [IMG1 [IMG2...]]\n"
  "\n"
  "Options:\n"
  "  -h  -?          Show help options\n"
  "  -d              Disable graphics\n"
  "  -t              Timing of tag extraction\n"
  "  -C <bbxhh>      Tag family (default 36h11)\n"
  "  -D <id>         Video device ID (if multiple cameras present). Not needed if -n is set\n"
  "  -F <fx>         Focal length in pixels\n"
  "  -W <width>      Image width (default 640, availability depends on camera)\n"
  "  -H <height>     Image height (default 480, availability depends on camera)\n"
  "  -S <size>       Tag size (square black frame) in meters\n"
  "  -E <exposure>   Manually set camera exposure (default auto; range 0-10000)\n"
  "  -G <gain>       Manually set camera gain (default auto; range 0-255)\n"
  "  -B <brightness> Manually set the camera brightness (default 128; range 0-255)\n"
  "  -N <camera number> Set camera number (1 for front, 2 for back)\n"
  "  -n <config file> Read in camera config from given config file. Must come after -N"
  "\n";

#ifndef __APPLE__
#define EXPOSURE_CONTROL // only works in Linux
#endif

#ifdef EXPOSURE_CONTROL
#include <libv4l2.h>
#include <linux/videodev2.h>
#include <fcntl.h>
#include <errno.h>
#endif

// OpenCV library for easy access to USB camera and drawing of images
// on screen
#include "opencv2/opencv.hpp"

// April tags detector and various families that can be selected by command line option
#include "AprilTags/TagDetector.h"
#include "AprilTags/Tag16h5.h"
#include "AprilTags/Tag25h7.h"
#include "AprilTags/Tag25h9.h"
#include "AprilTags/Tag36h9.h"
#include "AprilTags/Tag36h11.h"


// Needed for getopt / command line options processing
#include <unistd.h>
extern int optind;
extern char *optarg;

const char* windowName = "apriltags_demo";

cv::VideoCapture *capture_device;

// utility function to provide current system time (used below in
// determining frame rate at which images are being processed)
double tic() {
  struct timeval t;
  gettimeofday(&t, NULL);
  return ((double)t.tv_sec + ((double)t.tv_usec)/1000000.);
}


#ifndef PI
const double PI = 3.14159265358979323846;
#endif
const double TWOPI = 2.0*PI;

/**
 * Normalize angle to be within the interval [-pi,pi].
 */
inline double standardRad(double t) {
  if (t >= 0.) {
    t = fmod(t+PI, TWOPI) - PI;
  } else {
    t = fmod(t-PI, -TWOPI) + PI;
  }
  return t;
}

/**
 * Convert rotation matrix to Euler angles
 */
void wRo_to_euler(const Eigen::Matrix3d& wRo, double& yaw, double& pitch, double& roll) {
    yaw = standardRad(atan2(wRo(1,0), wRo(0,0)));
    double c = cos(yaw);
    double s = sin(yaw);
    pitch = standardRad(atan2(-wRo(2,0), wRo(0,0)*c + wRo(1,0)*s));
    roll  = standardRad(atan2(wRo(0,2)*s - wRo(1,2)*c, -wRo(0,1)*s + wRo(1,1)*c));
}

bool break_camera_loop = false;

class CameraUpdater {
  private:
  cv::VideoCapture m_cap;
  int camera_number;
  cv::Mat latest_picture;
  thread updater_thread;
  atomic<bool> thread_is_running;
  mutex picture_lock;

  public:
  CameraUpdater(int camera_number) : camera_number(camera_number), m_cap(camera_number), thread_is_running(false) {
    thread_is_running = true;
    if (!m_cap.isOpened()) {
      cerr << "Capture device not opened" << endl;
      exit(1);
    }
  }

  CameraUpdater(int camera_number, int width, int height) : CameraUpdater(camera_number) {
    m_cap.set(CV_CAP_PROP_FRAME_WIDTH, width);
    m_cap.set(CV_CAP_PROP_FRAME_HEIGHT, height);
  }

  ~CameraUpdater() {
    thread_is_running = false;
    updater_thread.join();
    m_cap.release();
  }

  void update_camera() {
    while (thread_is_running) {
      cv::Mat picture;
      bool read_picture = m_cap.read(picture);
      if (!read_picture) {
        cerr << "Could not read picture" << endl;
        continue;
      }
      picture_lock.lock();
      latest_picture = picture;
      picture_lock.unlock();
    }
  }
  
  void start() {
    thread_is_running = true;
    picture_lock.lock();
    bool picture_grabbed = m_cap.read(latest_picture);
    if (!picture_grabbed) {
      cerr << "Could not grab picture" << endl;
      exit(1);
    }
    picture_lock.unlock();
    updater_thread = thread([this] { this->update_camera(); });
  }
  
  cv::Mat get_picture() {
    picture_lock.lock();
    cv::Mat picture = latest_picture;
    picture_lock.unlock();
    return picture;
  }
};


class Demo {

  AprilTags::TagDetector* m_tagDetector;
  AprilTags::TagCodes m_tagCodes;

  bool m_draw; // draw image and April tag detections?
  bool m_timing; // print timing information for each tag extraction call

  int m_width; // image size in pixels
  int m_height;
  double m_tagSize; // April tag side length in meters of square black frame
  double m_fx; // camera focal length in pixels
  double m_fy;
  double m_px; // camera principal point
  double m_py;
  double m_fov; // Camera diagonal field of fiew

  int m_deviceId; // camera id (in case of multiple cameras)

  int m_exposure;
  int m_gain;
  int m_brightness;
  int m_camera_number; //1 for back, 2 for front
  cv::String m_camera_name; //Null if not set, otherwise Front or Back

  cv::Mat m_camera_matrix;
  cv::Mat m_dist_coeffs;

  string m_output_filename;

  CameraUpdater *m_camera_updater;

public:

  // default constructor
  Demo() :
    // default settings, most can be modified through command line options (see below)
    m_tagDetector(NULL),
    m_tagCodes(AprilTags::tagCodes36h11),

    m_draw(true),
    m_timing(false),

    m_width(640),
    m_height(480),
    m_tagSize(0.166),
    m_fx(600),
    m_fy(600),
    m_px(m_width/2),
    m_py(m_height/2),
    m_fov(78.0),

    m_exposure(-1),
    m_gain(-1),
    m_brightness(-1),

    m_deviceId(0),
    m_camera_number(0),
    m_camera_name(""),
    m_camera_updater(nullptr)

  {
    m_camera_matrix = (cv::Mat_<double>(3, 3) << 462.63107599, 0.,           326.21297766,
                                             0.,           462.21461581, 176.90908288,
                                             0.,           0.,           1.);
    m_dist_coeffs = (cv::Mat_<double>(1, 5) << 0.09591939, -0.19559665, 0.00127468, 0.00103905, 0.09594666);
  }

  ~Demo() {

    capture_device = NULL;
    delete m_camera_updater;
  }


  // changing the tag family
  void setTagCodes(string s) {
    if (s=="16h5") {
      m_tagCodes = AprilTags::tagCodes16h5;
    } else if (s=="25h7") {
      m_tagCodes = AprilTags::tagCodes25h7;
    } else if (s=="25h9") {
      m_tagCodes = AprilTags::tagCodes25h9;
    } else if (s=="36h9") {
      m_tagCodes = AprilTags::tagCodes36h9;
    } else if (s=="36h11") {
      m_tagCodes = AprilTags::tagCodes36h11;
    } else {
      cout << "Invalid tag family specified" << endl;
      exit(1);
    }
  }

  // parse command line options to change default behavior
  void parseOptions(int argc, char* argv[]) {
    int c;
    while ((c = getopt(argc, argv, ":h?dtn:N:C:F:H:S:W:E:G:B:D:")) != -1) {
      // Each option character has to be in the string in getopt();
      // the first colon changes the error character from '?' to ':';
      // a colon after an option means that there is an extra
      // parameter to this option; 'W' is a reserved character
      switch (c) {
      case 'h':
      case '?':
        cout << usage;
        exit(0);
        break;
      case 'd':
        m_draw = false;
        break;
      case 't':
        m_timing = true;
        break;
      case 'C':
        setTagCodes(optarg);
        break;
      case 'F':
        m_fx = atof(optarg);
        m_fy = m_fx;
        break;
      case 'H':
        m_height = atoi(optarg);
        m_py = m_height/2;
         break;
      case 'S':
        m_tagSize = atof(optarg);
        break;
      case 'W':
        m_width = atoi(optarg);
        m_px = m_width/2;
        break;
      case 'E':
#ifndef EXPOSURE_CONTROL
        cout << "Error: Exposure option (-E) not available" << endl;
        exit(1);
#endif
        m_exposure = atoi(optarg);
        break;
      case 'G':
#ifndef EXPOSURE_CONTROL
        cout << "Error: Gain option (-G) not available" << endl;
        exit(1);
#endif
        m_gain = atoi(optarg);
        break;
      case 'B':
#ifndef EXPOSURE_CONTROL
        cout << "Error: Brightness option (-B) not available" << endl;
        exit(1);
#endif
        m_brightness = atoi(optarg);
        break;
      case 'D':
        m_deviceId = atoi(optarg);
        break;
      case 'n':
        if (!m_camera_number) {
            cout << "-n option must always come after -N" << endl;
            exit(1);
        }
        readConfig(optarg);
        break;
      case 'N':
        m_camera_number = atoi(optarg);
        if(m_camera_number > 2 || m_camera_number < 1) {
            cout << "Error: camera number must be 1 (front) or 2 (back)";
            exit(1);
        }
        m_camera_name = (m_camera_number == 1) ? "Front" : "Back";
        break;
      case ':': // unknown option, from getopt
        cout << usage;
        exit(1);
        break;
      }
    }
  }

  void setup() {
    m_tagDetector = new AprilTags::TagDetector(m_tagCodes);

    // prepare window for drawing the camera images
    if (m_draw) {
      cv::String windowName = (m_camera_number == 1) ? "Front" : "Back";
      cv::namedWindow(windowName, 1);
    }
  }

  // Read in config directions. If our camera is the back camera, we want the second line, otherwise we want the first
  void readConfig(const char* file) {
    // Open file
    ifstream configFile(file);
    string line;
    // Read in line 1 for front, line 2 for back
    getline(configFile, line);
    if (m_camera_number == 2) getline(configFile, line);
    // Read in values one at a time
    stringstream linestream(line);
    string camera_name; // Front or Back
    string usb_location; //USB Hub where the camera is located

    linestream >> camera_name;
    linestream >> usb_location;
    linestream >> m_output_filename;
    linestream >> m_width;
    linestream >> m_height;
    linestream >> m_fov;

    m_camera_name = camera_name; // Convert from std::string to cv::String

    // Figure out which camera number is associated with this USB hub
    FILE *in;
    const string find_videonum_command = "find /sys/bus/usb/devices/" + usb_location + " | grep video[0-9]*$";
    string command_out;

    if(!(in = popen(find_videonum_command.c_str(), "r"))) {
      std:cout << "Could not open video command";
    }

    try {
      char buf[512];
      while (!feof(in)) {
        if (fgets(buf, 512, in) != NULL) command_out += buf;
      }
    } catch (...) {
      pclose(in);
      throw;
    }
    pclose(in);

    regex videonum_regex("video([0-9]+)\n?$"); // Gets the video number at the end of output
    smatch match_results;
    bool found_videonum = regex_search(command_out, match_results, videonum_regex);
    if (!found_videonum) {
      cout << "Did not find video number, check USB location in config file" << endl;
      exit(1);
    }

    m_deviceId = stoi(match_results[1].str());
    }

  void setupVideo() {

#ifdef EXPOSURE_CONTROL
    // manually setting camera exposure settings; OpenCV/v4l1 doesn't
    // support exposure control; so here we manually use v4l2 before
    // opening the device via OpenCV; confirmed to work with Logitech
    // C270; try exposure=20, gain=100, brightness=150

    stringstream video_str_builder;
    video_str_builder << "/dev/video";
    video_str_builder << m_deviceId;
    string video_str = video_str_builder.str();
    int device = v4l2_open(video_str.c_str(), O_RDWR | O_NONBLOCK);

    if (m_exposure >= 0) {
      // not sure why, but v4l2_set_control() does not work for
      // V4L2_CID_EXPOSURE_AUTO...
      struct v4l2_control c;
      c.id = V4L2_CID_EXPOSURE_AUTO;
      c.value = 1; // 1=manual, 3=auto; V4L2_EXPOSURE_AUTO fails...
      if (v4l2_ioctl(device, VIDIOC_S_CTRL, &c) != 0) {
        cout << "Failed to set... " << strerror(errno) << endl;
      }
      cout << "exposure: " << m_exposure << endl;
      v4l2_set_control(device, V4L2_CID_EXPOSURE_ABSOLUTE, m_exposure*6);
    }
    if (m_gain >= 0) {
      cout << "gain: " << m_gain << endl;
      v4l2_set_control(device, V4L2_CID_GAIN, m_gain*256);
    }
    if (m_brightness >= 0) {
      cout << "brightness: " << m_brightness << endl;
      v4l2_set_control(device, V4L2_CID_BRIGHTNESS, m_brightness*256);
    }
    v4l2_close(device);
#endif
	    m_camera_updater = new CameraUpdater(m_deviceId, m_width, m_height);

	    // find and open a USB camera (built in laptop camera, web cam etc)
	    //cout << "Camera successfully opened (ignore error messages above...)" << endl;
    //cout << "Actual resolution: "
    // TODO: Set height and width of camera
  }

  // Prints a set of detections to the given file.
  // Format: "<degrees horizontal> <Tag id>"
  void print_detections_to_file(const vector<AprilTags::TagDetection> &detections, const string &filename) {
    ofstream output_file;

    output_file.open(filename.c_str());
    //Set up field of view
    const double h_fov = atan(tan((m_fov/180) * M_PI) * cos(atan2(m_width, m_height))) / M_PI * 180;
    const double v_fov = atan(tan((m_fov/180) * M_PI) * sin(atan2(m_width, m_height))) / M_PI * 180;

    const double h_degrees_per_pixel = h_fov / m_width;
    const double v_degrees_per_pixel = v_fov / m_height;

    for (int i = 0; i < detections.size(); i++) {
        double detection_horizontal_degrees = (detections[i].cxy.first - (m_width/2)) * h_degrees_per_pixel;
        int detection_id = detections[i].id;
        output_file << detection_horizontal_degrees << " " << detection_id << endl;
    }

    output_file.close();
  }

  void print_detection(AprilTags::TagDetection& detection) const {
    cout << "  Id: " << detection.id
         << " (Hamming: " << detection.hammingDistance << ")";

    // recovering the relative pose of a tag:

    // NOTE: for this to be accurate, it is necessary to use the
    // actual camera parameters here as well as the actual tag size
    // (m_fx, m_fy, m_px, m_py, m_tagSize)

    Eigen::Vector3d translation;
    Eigen::Matrix3d rotation;
    detection.getRelativeTranslationRotation(m_tagSize, m_fx, m_fy, m_px, m_py,
                                             translation, rotation);
    Eigen::Matrix3d F;
    F <<
      1, 0,  0,
      0,  -1,  0,
      0,  0,  1;
    Eigen::Matrix3d fixed_rot = F*rotation;
    double yaw, pitch, roll;
    wRo_to_euler(fixed_rot, yaw, pitch, roll);

    cout << "  distance=" << translation.norm()
         << "m, x=" << translation(0)
         << ", y=" << translation(1)
         << ", z=" << translation(2)
         << ", yaw=" << yaw
         << ", pitch=" << pitch
         << ", roll=" << roll
         << endl;

    // Also note that for SLAM/multi-view application it is better to
    // use reprojection error of corner points, because the noise in
    // this relative pose is very non-Gaussian; see iSAM source code
    // for suitable factors.
  }

  void processImage(cv::Mat& image, cv::Mat& image_gray) {
    // alternative way is to grab, then retrieve; allows for
    // multiple grab when processing below frame rate - v4l keeps a
    // number of frames buffered, which can lead to significant lag
    //      m_cap.grab();
    //      m_cap.retrieve(image);

    // detect April tags (requires a gray scale image)
    cv::cvtColor(image, image_gray, CV_BGR2GRAY);

    cv::undistort(image_gray, image_gray.clone(), m_camera_matrix, m_dist_coeffs);

    double t0;
    if (m_timing) {
      t0 = tic();
    }

    vector<AprilTags::TagDetection> detections = m_tagDetector->extractTags(image_gray);
    if (m_timing) {
      double dt = tic()-t0;
      cout << "Extracting tags took " << dt << " seconds." << endl;
    }

    // print out each detection
    cout << detections.size() << " tags detected on " << m_camera_name << ':' << endl;
    for (int i=0; i<detections.size(); i++) {
      print_detection(detections[i]);
    }
    print_detections_to_file(detections, m_output_filename);

    // show the current image including any detections
    if (m_draw) {
      cv::Mat image_undis;
      cv::undistort(image, image_undis, m_camera_matrix, m_dist_coeffs);
      image = image_undis;
      for (int i=0; i<detections.size(); i++) {
        // also highlight in the image
        detections[i].draw(image);
      }

      //Set up text drawing for "Front" and "Back"
      int fontFace = cv::FONT_HERSHEY_DUPLEX;
      double fontScale = 2.0;
      cv::Scalar fontColor(255, 255, 255);
      int fontThickness = 2;

      cv::Size textSize = getTextSize(m_camera_name, fontFace, fontScale, fontThickness, NULL);
      int textHeight = textSize.height;
      int imageHeight = image.rows;

      cv::Point pt(0, imageHeight);
      putText(image, m_camera_name, pt, fontFace, fontScale, fontColor, fontThickness);
      imshow(m_camera_name, image); // OpenCV call
    }
  }

  // Contunially process video
  void loop() {
    if (m_camera_updater == nullptr) {
        cerr << "Camera updater not initialized" << endl;
        exit(1);
    }
    cerr << "Starting updater" << endl;
    m_camera_updater->start();
    cout << "Started updater" << endl;

    cv::Mat image;
    cv::Mat image_gray;

    int frame = 0;
    double last_t = tic();

    while (!break_camera_loop) {

      // capture frame
      image = m_camera_updater->get_picture();
      cerr << "Got image" << endl;

      processImage(image, image_gray);
      cerr << "Processed image" << endl;

      // print out the frame rate at which image frames are being processed
      frame++;
      if (frame % 10 == 0) {
        double t = tic();
        cout << "  " << 10./(t-last_t) << " fps" << endl;
        last_t = t;
      }

      // exit if any key is pressed
      if (cv::waitKey(1) == 'q') break;
    }

  }

}; // Demo

// Breaks out of the camera loop gently on ctrl+c.
void signalHandler (int signum) {
  break_camera_loop = true;
}

int main(int argc, char* argv[]) {

  // Break out of the camera loop gently on ctrl+c or SIGTERM
  signal(SIGTERM, signalHandler);
  signal(SIGINT, signalHandler);
  Demo demo;

  // process command line options
  cout << "Parsing options" << endl;
  demo.parseOptions(argc, argv);


  cout << "Setting up" << endl;
  demo.setup();

  cout << "Processing video" << endl;
  // setup image source, window for drawing...
  demo.setupVideo();

  // the actual processing loop where tags are detected and visualized
  demo.loop();

  return 0;
}
