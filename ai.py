import serial
import sys
import os
import time
from pyax12.connection import Connection

h_fov = 78.0  # TODO: Read this in from config.txt and calculate real horizontal angle

def main():
    # Take in 3 arguments: usually front.txt, back.txt, heading.txt
    if len(sys.argv) != 4:
        print("This requires 3 arguments: the front input file, the back input file, and the output file")
        exit(1)
    front_camera_filename = sys.argv[1]
    back_camera_filename = sys.argv[2]
    heading_filename = sys.argv[3]

    weapon_arm = WeaponArm()
    weapon_arm.goToHomePosition()

    start_following_tags(front_camera_filename, back_camera_filename)

def start_following_tags(front_camera_filename, back_camera_filename):
    while True:
        front_heading = 0
        back_heading = 0
        front_id = 0
        back_id = 0
 
        start_time = time.time()
        with open(front_camera_filename, 'r') as front_file, open(back_camera_filename, 'r') as back_file:
            # For now, we just take the last measurement in the file.
            # TODO: Be smarter about this.
            for line in front_file:
                  front_heading, front_id = (float(number) for number in line.split())
            for line in back_file:
                  back_heading, back_id = (float(number) for number in line.split())

            if front_heading:
                print("Front heading", front_heading, "Front id", front_id)
            elif back_heading:
                print("Back heading", back_heading, "Back id", back_id)

        # If front_id is not None, take front_id, else take back id
        tag_id = front_id or back_id
        chosen_heading = front_heading or back_heading

        if tag_id % 2 == 0:
            chosen_heading = 0

        heading_string = degreesToMotorDirections(chosen_heading)
        print(heading_string)
        displayTTYSend(heading_string)
   

def degreesToMotorDirections(angle):
    """Turns angle into AA/aa/ZZ/zz directions"""

    # Get speed between 0 and 25
    normalized_angle = angle / (h_fov / 2)
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
    """Sends a string to the motor controller.
    """
    port = serial.Serial("/dev/ttyUSB0", 9600, timeout = 2)
    port.write(('<' + str1 + '>' + '\n').encode('ascii'))
    port.close()

class WeaponArm:
    def __init__(self):
        # Wait for arm to be available
        while not os.path.exists('/dev/ttyACM0'):
            time.sleep(.1)
    
        # Set up actuators
        serial_connection_successful = False
        while not serial_connection_successful:
            serial_connection_successful=True
            try:
                self.serial_connection = Connection(port='/dev/ttyACM0',
                                               baudrate=1000000,
                                               timeout=.1)
            except serial.serialutil.SerialException:
                serial_connection_successful = False

    def goToHomePosition(self):
        self.serial_connection.goto(1, 1900, speed=64)
        self.serial_connection.goto(4, 1023, speed=64)

        # If we don't have this, the server motors sometimes don't start up
        # TODO: find a real fix for this
        print(end='')
        

if __name__ == '__main__':
    main()
