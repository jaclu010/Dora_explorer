import serial
import threading
import global_vars as gv
import os
import common


gv.serUSB1 = None

try:
    gv.serUSB1 = serial.Serial(common.find_usb(gv.STEERING_PORT), writeTimeout=0)
    gv.serUSB1.baudrate = gv.BAUDRATE_STEERING
except serial.serialutil.SerialException, exc:
    print("USB1 IT NO WORK, Fixa saken Gomba %s" % exc)
    
    
    
def steering_serial(tid):
    """
    Send commands to the steering module
    """
    print("Thread" + str(tid) + " main loop initialized")

    prev_movement = "none"
    print(gv.serUSB1.isOpen())
    while gv.running:
        if (gv.serUSB1 != None):
            try:
                if (gv.serUSB1.isOpen()):
                    gv.condition.acquire()
                    while True:
                        temp_move = gv.movement_dir
                        if gv.movement_dir != "none":
                            break
                        gv.condition.wait()
                    gv.condition.release()
                    #print(temp_move)
                    if temp_move == "forward" and prev_movement != "forward":
                        gv.serUSB1.write("f".encode())
                        gv.serUSB1.write("s".encode())
                        gv.serUSB1.write(chr(100))
                        prev_movement = "forward"
                        
                    elif temp_move == "backward" and prev_movement != "backward":
                        gv.serUSB1.write("b".encode())
                        gv.serUSB1.write("s".encode())
                        gv.serUSB1.write(chr(100))
                        prev_movement = "backward"
                        
                    elif temp_move == "left" and prev_movement != "left":
                        gv.serUSB1.write("l".encode())
                        gv.serUSB1.write("s".encode())
                        gv.serUSB1.write(chr(100))
                        prev_movement = "left"

                    elif temp_move == "right" and prev_movement != "right":
                        gv.serUSB1.write("r".encode())
                        gv.serUSB1.write("s".encode())
                        gv.serUSB1.write(chr(100))
                        prev_movement = "right"
                            
                    elif temp_move == "stop" and prev_movement != "stop":
                        gv.serUSB1.write("s".encode())
                        gv.serUSB1.write(chr(0))
                        prev_movement = "stop"

            except serial.serialutil.SerialException, exc:
                print("An error occured with the serial connection on the steering port: %s" % exc)
                raise serial.serialutil.SerialException
