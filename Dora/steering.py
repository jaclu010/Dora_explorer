import serial
import threading
from global_vars import *
import os
#from main import find_usb


serUSB1 = None
global movement_dir
def find_usb(port_id):
	port = ""
        for file in os.listdir("/dev/serial/by-id"):
		if port_id in file:
			symlink = os.path.join("/dev/serial/by-id/", file)
			port = str(os.path.realpath(symlink))
	return port

try:
    print("Open port plx")
    serUSB1 = serial.Serial(find_usb(STEERING_PORT), writeTimeout=0)
    serUSB1.baudrate = BAUDRATE_STEERING
except serial.serialutil.SerialException, exc:
    print("USB1 IT NO WORK, Fixa saken Gomba %s" % exc)

    
def steering_serial(tid):
    """
    Send commands to the steering module
    """
    print("Thread" + str(tid) + "main loop initialized")

    global serUSB1, running, condition
    global movement_dir
    prev_movement = "none"
    print(serUSB1.isOpen())
    while running:
        print(movement_dir)
        if (serUSB1 != None):
            try:
                if (serUSB1.isOpen()):
                    condition.acquire()
                    while True:
                        temp_move = movement_dir
                        if movement_dir != "none":
                            #print(movement_dir)    
                            break
                        condition.wait()
                    condition.release()
                    #print(movement_dir)
                    if temp_move == "forward" and prev_movement != "forward":
                        print("here")
                        serUSB1.write("f".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(100))
                        prev_movement = "forward"
                    elif movement_dir == "backward" and prev_movement != "backward":
                        serUSB1.write("b".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(100))
                        prev_movement = "backward"

                    elif movement_dir == "left" and prev_movement != "left":
                        serUSB1.write("l".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(100))
                        prev_movement = "left"

                    elif movement_dir == "right" and prev_movement != "right":
                        serUSB1.write("l".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(100))
                        prev_movement = "right"
                            
                    elif movement_dir == "stop" and prev_movement != "stop":
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(0))
                        prev_movement = "stop"

            except serial.serialutil.SerialException, exc:
                print("An error occured with the serial connection on the steering port: %s" % exc)
