import serial
from global_vars import *
from common import *


speeds = {LEFT: 0, RIGHT: 0, TOWER: 80, DEFAULT: 75}
man_speeds = {LEFT: 125, RIGHT: 125, TOWER: 80, DEFAULT: 125}
steering_port = None


def set_speed(mode, spd = 0, side = "both"):
    """
    spd must be an integer value 0-255
    """
    #  print('NEW SPEED: %i %s' % (int(spd), side))
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
    global steering_port

    try:
        steering_port = serial.Serial(find_usb(STEERING_PORT_NAME), writeTimeout=0)
        steering_port.baudrate = BAUDRATE_STEERING
    except serial.serialutil.SerialException as exc:
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
        except serial.serialutil.SerialException as exc:
            print("An error occured with the serial connection on the steering port: %s" % exc)
