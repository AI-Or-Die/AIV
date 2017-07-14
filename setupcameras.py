import cv2
import glob
import sys, os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='Process arguments for video camera setup')
    parser.add_argument('--save', action='store', default=None)
    args = parser.parse_args()
    print(args.save)
    available_video_mount_points = glob.glob('/dev/video[0-9]*')
    video_numbers = [int(mount_point.replace('/dev/video', '')) for mount_point in available_video_mount_points]
    print(video_numbers)
    
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

    if args.save:
        with open(args.save, 'w') as file:
            file.write('Front ' + str(front_camera_number) + '\nBack ' + str(back_camera_number) + '\n')

if __name__ == '__main__':
    main()
