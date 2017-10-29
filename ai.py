import serial
import signal
import sys
import os
import time
from pyax12.connection import Connection

h_fov = 78.0  # TODO: Read this in from config.txt and calculate real horizontal angle

latest_instruction = 'aa0'


def main():
    try:
        signal.signal(signal.SIGINT, exit_gracefully)
        # Take in 3 arguments: usually front.txt, back.txt, heading.txt
        if len(sys.argv) != 4:
            print("This requires 3 arguments: the front input file, the back input file, and the output file")
            exit(1)
        front_camera_filename = sys.argv[1]
        back_camera_filename = sys.argv[2]
        heading_filename = sys.argv[3]

        global weapon_arm
        weapon_arm = WeaponArm()
        weapon_arm.goToHomePosition()

        #spin_to_find_apriltags(front_camera_filename, back_camera_filename)
        move_toward_tag(front_camera_filename, back_camera_filename)
    except Exception as e:
        # odroid logging
        pass


def move_toward_tag(front_camera_filename, back_z_filename):
    while True:
        detections = detect_apriltags(front_camera_filename, back_camera_filename)
        # Find an apriltag, move toward it.

        if len(detections['front']) == 0 and len(detections['back']) == 0:
            sendMotorInstruction('AA')
            time.sleep(1/30)
            weapon_arm.goToHomePosition()
            sendWeaponInstruction('0')
            continue
        sendWeaponInstruction('1')
        if len(detections['front']) > 0:
           side = 'front'
           active_detection = detections['front'][0]
        else:
           side = 'back'
           active_detection = detections['back'][0]

        distance = active_detection[2]
        heading = active_detection[0]
        power = distance * 10
        power = int(min(power, 25))
        if side == 'back':
            power = -power
        if -11 < power < 11:
            weapon_arm.goToAttackPosition()
        else:
            weapon_arm.goToHomePosition()

        heading_char = degreesToMotorDirections(heading)
        left_adjustment, right_adjustment = (motorDirectionsToPower(letter) for letter in heading_char)
        if side == 'back':
            left_adjustment, right_adjustment = -left_adjustment, -right_adjustment
        leftPower = int(min(max(power + left_adjustment, -25), 25))
        rightPower = int(min(max(power + right_adjustment, -25), 25))
        print(leftPower, rightPower)
        motorInstruction = powerToMotorDirections(leftPower) + powerToMotorDirections(rightPower)
        sendMotorInstruction(motorInstruction)


def exit_gracefully(signal, frame):
    displayTTYSend('aa0')
    exit()


def apriltag_is_in_sight(front_camera_filename, back_camera_filename):
    detections = detect_apriltags(front_camera_filename, back_camera_filename)
    return len(detections['front']) > 0 or len(detections['back']) > 0

def start_spinning_incrementally(stop_condition=lambda: False):
    start_time = time.time()
    while not stop_condition():
        if ((time.time() - start_time)//.40) % 2 == 1:
            heading_string = degreesToMotorDirections(20.0)
            sendMotorInstruction(heading_string)
        else:
            heading_string = degreesToMotorDirections(0.0)
            sendMotorInstruction(heading_string)
        time.sleep(1/30)
    sendMotorInstruction('AA')
    return

def spin_to_find_apriltags(front_camera_filename, back_camera_filename):
    sees_apriltag = lambda: apriltag_is_in_sight(front_camera_filename, back_camera_filename)
    while True:
        start_spinning_incrementally(stop_condition=sees_apriltag)
        start_following_tags(front_camera_filename, back_camera_filename, stop_condition=lambda: not sees_apriltag())

def start_following_tags(front_camera_filename, back_camera_filename, stop_condition=lambda: False):
    while not stop_condition():

        detections = detect_apriltags(front_camera_filename, back_camera_filename)
        front_detections = detections['front']
        back_detections = detections['back']

        relevant_detections = front_detections or back_detections
        if relevant_detections:
            chosen_heading, tag_id, distance = relevant_detections[0]
        else:
            chosen_heading, tag_id, distance = 0, 0, 0

        # Only attack even numbered april tags
        if tag_id % 2 == 1:
            chosen_heading = 0

        heading_string = degreesToMotorDirections(chosen_heading)
        print(heading_string)
        sendMotorInstruction(heading_string)

def detect_apriltags(front_camera_filename, back_camera_filename):
    front_heading = 0
    back_heading = 0
    front_id = 0
    back_id = 0

    detections = {'front': [], 'back': []}

    with open(front_camera_filename, 'r') as front_file, open(back_camera_filename, 'r') as back_file:
        for line in front_file:
            detections['front'].append(tuple(float(number) for number in line.split()))
        for line in back_file:
            detections['back'].append(tuple(float(number) for number in line.split()))

    return detections

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

    if angle > 0:
        leftLetter = chr(ord('a') + letter_number)
        rightLetter = chr(ord('A') + letter_number)
    else:
        leftLetter = chr(ord('A') + letter_number)
        rightLetter = chr(ord('a') + letter_number)

    return leftLetter + rightLetter

def motorDirectionsToPower(letter):
    if 'a' <= letter <= 'z':
        return ord(letter) - ord('a')
    else:
        return -(ord(letter) - ord('A'))

def powerToMotorDirections(power):
    if power > 0:
        return chr(power + ord('a'))
    else:
        return chr(-power + ord('A'))

def sendMotorInstruction(str1):
    global latest_instruction
    assert len(str1) == 2
    latest_instruction = str1 + latest_instruction[2:]
    print(latest_instruction)
    displayTTYSend(latest_instruction)

def sendWeaponInstruction(str1):
    global latest_instruction
    assert str1 == '0' or str1 == '1'
    latest_instruction = latest_instruction[:2] + str1 + latest_instruction[3:]
    displayTTYSend(latest_instruction)

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
        try:
            self.serial_connection.goto(1, 1900, speed=64)
            self.serial_connection.goto(4, 1023, speed=64)

            # If we don't have this, the server motors sometimes don't start up
            # TODO: find a real fix for this
            print('', end='')
        except exception as e:
            # odroid logging
            pass

    def goToAttackPosition(self):
        try:
            self.serial_connection.goto(1, 2100, speed=64)
            self.serial_connection.goto(4, 1023, speed=64)
            print('', end='')
        except exception as e:
            # odroid logging
            pass


if __name__ == '__main__':
    main()
import serial
import sys
