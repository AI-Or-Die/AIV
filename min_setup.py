import cv2
import glob
import subprocess

available_video_mount_points = glob.glob('/dev/video[0-9]*')
video_numbers = [int(mount_point.replace('/dev/video', '')) for mount_point in available_video_mount_points]

cams = []
for video_number in sorted(video_numbers):
	cap = cv2.VideoCapture(video_number)
	if not cap.isOpened():
		break
	else:
		cams.append(video_number)

print("available cams",cams)

usb_path_finder_command_a = "udevadm info --name video" + str(cams[0]) + " -q path"
usb_path_finder_command_b = "udevadm info --name video" + str(cams[1]) + " -q path"

path_finder_process_a = subprocess.Popen(usb_path_finder_command_a.split(), stdout=subprocess.PIPE)
path_finder_process_b = subprocess.Popen(usb_path_finder_command_b.split(), stdout=subprocess.PIPE)

path_finder_process_output_a = path_finder_process_a.stdout.read().decode('ascii')
path_finder_process_output_b = path_finder_process_b.stdout.read().decode('ascii')

print("process output a: ", path_finder_process_output_a)
print("process output b: ", path_finder_process_output_b)

usb_path_a = path_finder_process_output_a.split('/')[-3] + '/'
usb_path_b = path_finder_process_output_b.split('/')[-3] + '/'

print("usb_path_a: ", usb_path_a)
print("usb_path_b: ", usb_path_b)
