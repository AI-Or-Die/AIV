import cv2
import glob
import sys, os
import subprocess
import argparse
import re

# Maybe make these settable in the future, depending on how configurable we want this to be
front_camera_height = 360
front_camera_width = 640
front_camera_outfile = 'front.txt'
front_camera_fov = 89.0

back_camera_height = 360
back_camera_width = 640
back_camera_outfile = 'back.txt'
back_camera_fov = 89.0

save_file = 'config.txt'

def main():
    available_video_mount_points = glob.glob('/dev/video[0-9]*')
    video_numbers = [int(mount_point.replace('/dev/video', '')) for mount_point in available_video_mount_points]
    
    front_camera_number = None
    back_camera_number = None

    for video_number in sorted(video_numbers):
        cap = cv2.VideoCapture(video_number)
        if not cap.isOpened():
            break
        while(True):
            # Capture frame-by-frame
            ret, frame = cap.read()
            if not ret:
                print('Not returned')
                break

            frame_height = len(frame)

            font = cv2.FONT_HERSHEY_DUPLEX
            font_scale = 1
            font_color = (255, 255, 255) 
            font_thickness = 2
            font_height = cv2.getTextSize('Testing', fontFace=font, fontScale=font_scale, thickness=font_thickness)[0][1]
            font_position = (0, font_height)

            text='Camera ' + str(video_number)
            if front_camera_number is None:
                text += '\nIf this is the front camera, press f'
            if back_camera_number is None:
                text += '\nIf this is the back camera, press b'

            for line in text.split('\n'):
    
                cv2.putText(frame,
                            text=line,
                            org=font_position, 
                            fontFace=cv2.FONT_HERSHEY_DUPLEX,
                            fontScale=font_scale,
                            color=font_color,
                            thickness=font_thickness)

                font_position = (0, font_position[1] + font_height + 10)
            # Display the resulting frame
            cv2.imshow('frame',frame)

            guiPressedKey = cv2.waitKey(1) & 0xFF
            if guiPressedKey == ord('b'):
                back_camera_number = video_number
                break
            if guiPressedKey == ord('f'):
                front_camera_number = video_number
                break

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
    cv2.destroyAllWindows()
    
    usb_path_finder_command_front = "udevadm info --name video" + str(front_camera_number) + " -q path"
    usb_path_finder_command_back = "udevadm info --name video" + str(back_camera_number) + " -q path"
    
    path_finder_process_front = subprocess.Popen(usb_path_finder_command_front.split(), stdout=subprocess.PIPE)
    path_finder_process_back = subprocess.Popen(usb_path_finder_command_back.split(), stdout=subprocess.PIPE)

    path_finder_process_output_front = path_finder_process_front.stdout.read().decode('ascii')
    path_finder_process_output_back = path_finder_process_back.stdout.read().decode('ascii')

    print(path_finder_process_output_front)
    print(path_finder_process_output_back)

    # Make sure we got the output we wanted
    usb_path_front = path_finder_process_output_front.split('/')[-3] + '/'
    usb_path_back = path_finder_process_output_back.split('/')[-3] + '/'


    with open(save_file, 'w') as file:
        file.write('Front ' + usb_path_front + ' ' + 
                   front_camera_outfile + ' ' + 
                   str(front_camera_width) + ' ' + 
                   str(front_camera_height) + ' ' +
                   str(front_camera_fov) + '\n')

        file.write('Back ' + usb_path_back + ' ' +
                   back_camera_outfile + ' ' + 
                   str(front_camera_width) + ' ' +
                   str(front_camera_height) + ' ' +
                   str(front_camera_fov) + '\n')


if __name__ == '__main__':
    main()
