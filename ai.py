import serial
import sys

h_fov = 78.0  # TODO: Read this in from config.txt and calculate real horizontal angle

def main():
    if len(sys.argv) != 4:
        print("This requires 3 arguments: the front input file, the back input file, and the output file")
        exit(1)
    front_camera_filename = sys.argv[1]
    back_camera_filename = sys.argv[2]
    heading_filename = sys.argv[3]
    
    while True:
        front_heading = 0
        back_heading = 0
        with open(front_camera_filename, 'r') as front_file, open(back_camera_filename, 'r') as back_file:
            for line in front_file:
                  front_heading = float(line)
            for line in back_file:
                  back_heading = float(line)
            print(front_heading or back_heading) 
        heading_string = degreesToMotorDirections(front_heading or back_heading)
        print(heading_string)

def degreesToMotorDirections(angle):
    # Get speed between 0 and 25
    normalized_angle = angle / h_fov
    if normalized_angle < -1:
        normalized_angle = -1
    if normalized_angle > 1:
        normalized_angle = 1

    # Find alphanumeric letter
    letter_number = abs(int(normalized_angle * 25))
    
    if angle < 0:
        leftLetter = chr(ord('A') + letter_number)
        rightLetter = chr(ord('a') + letter_number)
    else:
        leftLetter = chr(ord('a') + letter_number)
        rightLetter = chr(ord('A') + letter_number)

    return leftLetter + rightLetter
    

def displayTTYSend(str1):
    port = serial.Serial("/dev/ttyUSB1", 9600, timeout = 2)
    port.write((str1 + '\n').encode('ascii'))
    port.close()

if __name__ == '__main__':
    main()    
