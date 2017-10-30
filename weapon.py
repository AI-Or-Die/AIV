import serial
import signal
import sys
import os
import time
import random
from pyax12.connection import Connection

class WeaponArm:
    MAX_UP = 1400
    MAX_DOWN = 2100
    MAX_LEFT=1023
    MAX_RIGHT=3*1023
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

    def goToRange(self,up=0,left=1):
        try:
            self.serial_connection.goto(1, int(self.MAX_UP*up+self.MAX_DOWN*(1-up)), speed=64)
            self.serial_connection.goto(4, int(self.MAX_LEFT*left+self.MAX_RIGHT*(1-left)), speed=64)
        except Exception as e:
            with open('main.log','a') as f:
                f.write(str(e)+"\n")

        print('', end='')

    def goUpDown(self):
        try:
            self.goToRange(up=1)
            time.sleep(2)
            self.goToRange(up=0)
            time.sleep(2)
            self.goToRange(up=1)
            time.sleep(2)
            self.goToRange(up=0)
            time.sleep(2)
        except Exception as e:
            with open('main.log','a') as f:
                f.write(str(e)+"\n")

        print('', end='')

    def goCrazy(self):
        try:
            self.goToRange(up=random.random(),left=random.random())
            time.sleep(1.5)
            self.goToRange(up=random.random(),left=random.random())
            time.sleep(1.5)
            self.goToRange(up=random.random(),left=random.random())
            time.sleep(1.5)
            self.goToRange(up=random.random(),left=random.random())
            time.sleep(1.5)
        except Exception as e:
            with open('main.log','a') as f:
                f.write(str(e)+"\n")

        print('', end='')

    def goToHomePosition(self):
        try:
            self.serial_connection.goto(1, 1900, speed=64)
            self.serial_connection.goto(4, 1023, speed=64)
        except Exception as e:
            with open('main.log','a') as f:
                f.write(str(e))
        # If we don't have this, the server motors sometimes don't start up
        # TODO: find a real fix for this
        print('', end='')

    def goToAttackPosition(self):
        try:
            self.serial_connection.goto(1, 2100, speed=64)
            self.serial_connection.goto(4, 1023, speed=64)
            print('', end='')
        except Exception as e:
            with open('main.log','a') as f:
                f.write(str(e))
