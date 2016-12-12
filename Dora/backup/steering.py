import serial
import threading
from global_vars import *
import os
from common import *
import logging
import time

LEFT = 0
RIGHT = 1
TOWER = 2
DEFAULT = 3
speeds = {LEFT: 0, RIGHT: 0, TOWER: 100, DEFAULT: 125}
man_speeds = {LEFT: 125, RIGHT: 125, TOWER: 80, DEFAULT: 125}
steering_port = None

TURN_TIMES = {150: 0.63, 175: 0.52, 200: 0.445, 225: 0.39, 250: 0.355}

def turn(forward_dir, side):
    """
    Pick the correct turn function based on the current
    forward direction
    """
    if forward_dir == FORWARD:
        if side == "left":
            left()
        elif side == "right":
            right()
    elif forward_dir == BACKWARD:
        if side == "left":
            right()
        elif side == "right":
            left()

def set_driving_dir(forward_dir):
    """
    Sets the driving direction
    """
    if forward_dir == FORWARD:
        forward()
    elif forward_dir == RIGHT:
        backward()
        

def set_speed(mode, spd = 0, side = "both"):
    """
    spd must be an integer value 0-255
    """
    global speeds, man_speeds

    temp = {}
    if mode:
        temp =  speeds
    else:
        temp = man_speeds
        
    spd = int(spd)
    if spd > 255:
        spd = 255
    elif spd < 0:
        spd = 0

    
    if side == "both":
        temp[RIGHT] = spd
        temp[LEFT] = spd
        steering_port.write("s".encode())
        
    elif side == "left":
        temp[LEFT] = spd
        steering_port.write("v".encode())
        
    elif side == "right":
        temp[RIGHT] = spd
        steering_port.write("h".encode())
        
    elif side == "tower":
        temp[TOWER] = spd
        steering_port.write("t".encode())

    steering_port.write(chr(spd))

def forward():
    steering_port.write("f".encode())
   
def backward():
    steering_port.write("b".encode())

def left():
    steering_port.write("l".encode())

def right():
    steering_port.write("r".encode())

    

def open_port():
    global steering_port

    try:
        steering_port = serial.Serial(find_usb(STEERING_PORT_NAME), writeTimeout=0)
        steering_port.baudrate = BAUDRATE_STEERING
    except serial.serialutil.SerialException, exc:
        print("Failed to open steering port: %s" % exc)
    
    
    
def steering_serial(steering_cmd_man, mode, ir):
    """
    Send commands to the steering module
    """
    prev_command = ""
    print("Manual mode")
    while mode.value == 0:
        try:
            command = steering_cmd_man.get()
            if command != prev_command:
                if command == "forward":
                    forward()
                elif command == "backward":
                    backward()
                elif command == "turn_left":
                    left()
                elif command == "turn_right":
                    right()
                elif command == "forward_left":
                    forward()
                    set_speed(1, man_speeds[LEFT]//3, "left")
                    set_speed(1, man_speeds[RIGHT], 'right')
                elif command == "forward_right":
                    forward()
                    set_speed(1, man_speeds[RIGHT]//3, "right")
                    set_speed(1, man_speeds[LEFT], 'left')
                elif command == "stop":
                    set_speed(1, 0)
                elif "speed" in command:
                    parts = command.split("_")  # format: "speed" "side" integer speed
                    if len(parts) == 2:
                        if parts[1] == "left":
                            set_speed(1, man_speeds[LEFT], parts[1])
                        else:
                            set_speed(1, man_speeds[RIGHT], parts[1])
                    else:
                        set_speed(mode.value, int(parts[2]), parts[1])
                elif command == "manual":
                    mode.value = 1
                prev_command = command
        except serial.serialutil.SerialException, exc:
            print("An error occured with the serial connection on the steering port: %s" % exc)
            raise serial.serialutil.SerialException
