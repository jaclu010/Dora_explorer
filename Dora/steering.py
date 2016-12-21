#####
#
# steering.py
# Updated: 14/12 2016
# Authors: Fredrik Iselius, Martin Lundberg
#
#####

import serial
from global_vars import *
from common import *


speeds = {LEFT: 0, RIGHT: 0, TOWER: 80, DEFAULT: 60}  # Speed dict for autonomous mode
man_speeds = {LEFT: 125, RIGHT: 125, TOWER: 80, DEFAULT: 125}  # Speed dict for manual mode
steering_port = None


def set_speed(mode, spd = 0, side = "both"):
    """
    Sends a command to the steering module which will set
    the wheek pair on side 'side' to speed 'spd'
    """
    global speeds, man_speeds
    
    temp = {}
    if mode:
        temp =  speeds
    else:
        temp = man_speeds

    # Make sure that spd is between 0-255
    spd = int(spd)
    if spd > 255:
        spd = 255
    elif spd < 0:
        spd = 0

    # Send command to the steering module
    if side == "both":
        if mode and spd == speeds[LEFT] and spd == speeds[LEFT]:
            return
        temp[RIGHT] = spd
        temp[LEFT] = spd
        steering_port.write("s".encode())
        
    elif side == "left":
        if mode and spd == speeds[LEFT]:
            return
        temp[LEFT] = spd
        steering_port.write("v".encode())
        
    elif side == "right":
        if mode and spd == speeds[RIGHT]:
            return
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
    """
    Opens the port returned from find_usb() for serial communication
    """
    global steering_port

    try:
        steering_port = serial.Serial(find_usb(STEERING_PORT_NAME), writeTimeout=0)
        steering_port.baudrate = BAUDRATE_STEERING
    except serial.serialutil.SerialException as exc:
        print("Failed to open steering port: %s" % exc)

    
def steering_serial(steering_cmd_man, mode, ir):
    """
    Fetches manual commands from a queue shared with the bluetooth process
    and executes them
    """
    
    prev_command = ""
    while mode.value == 0:
        try:
            # Execute only if there is a new command
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
        except serial.serialutil.SerialException as exc:
            print("An error occured with the serial connection on the steering port: %s" % exc)
