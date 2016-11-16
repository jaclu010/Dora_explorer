# -*- coding: utf-8 -*-
from __future__ import print_function
import serial
from bluetooth import *
import sys
import time
import math
import threading
import copy
import os

from global_vars import *
from steering import *

#Debug variables
speed = 0.5
robot_rot_speed = math.pi / 40
map_size = 21

# Bluetooth condition
# condition = threading.Condition()
global steering_serial
global movement_dir



#class for threading
class Thread(threading.Thread):
    def __init__(self, threadID, typee):
        threading.Thread.__init__(self)
        self.threadID = threadID
        #typee == 0: bluetooth, typee 1 = serial
        self.typee = typee
    def run(self):
        
        if (self.typee == 0): bluetooth_loop(self.threadID)
        if (self.typee == 1): sensor_serial(self.threadID)
        if (self.typee == 2): steering_serial(self.threadID)
t1 = Thread(1, 0)
t2 = Thread(2, 1)
t3 = Thread(3, 2)

#generates an empty map
def gen_empty_map():
    a = []
    for y in range (0,21):        
        b = []
        for x in range (0,21):
            b += ["1"]
        a += [b]
    return a


def equal2D(l1, l2):
    t = True
    if (l1 == None or l2 == None): return False
    for i in range(len(l1)):
        if (l1[i] != l2[i]):
            t = False
            break
    return t

#sets the block in 2D-list d_list to val at x,y
def set_block(d_list, val, x, y):
    if (x >= 0 and y >= 0 and x < map_size and y < map_size):
        d_list[y][x] = val
    return d_list


#Translates the position of robot 
def move_in_dir(pos, speed, rotation):
    newx = 0
    newy = 0
    p1 = pos
    newx = p1[0] - speed*math.cos(rotation)
    newy = p1[1] - speed*math.sin(rotation)
    return (newx, newy)    
map = gen_empty_map()

#set_block(map,"2",0,0)
for y in range (0, 21):
    for x in range (0,21):
        if (x == 0 or y == 0 or x == 20 or y == 20):
            map = set_block(map, "2", x, y)
        if (x <= 5 and y <= 5): 
            map = set_block(map, "2", x, y)
        if (x <= 4 and y <= 4):
            map = set_block(map, "0", x ,y)
map_string = ""

map_prev = None



robot_pos = (0,0)
robot_rot = math.pi
robot_pos_prev = None
robot_pos_rot = None

#if python version not 3
if sys.version < '3':
    input  = raw_input

#mac adress to server, per default 7C:7A:91:4A:21:D9 (martins dator)
ismartincomp = True

addr = None
if (ismartincomp):
    addr = "7C:7A:91:4A:21:D9"
else:
    #Otherwise get mac-addres from argument
    if len (sys.argv) < 2:
        print("no device spec. go search")
        print("the samleServer service")
    else:
        adr = sys.argv[1]
        print ("Searching for sServer on %s" % addr)
#Unique id, should be the same as servers
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

service_matches = find_service( uuid = uuid, address = addr )

bluetooth_online = True

if len(service_matches) == 0:
    print("Server could not be found")
    bluetooth_online = False
    #sys.exit(0)

#If the bluetooth is online, create a connection to server
if (bluetooth_online):
    first_match = service_matches[0]
    port = first_match["port"]
    name = first_match["name"]
    host = first_match["host"]

    print("connecting to \"%s\" on %s" % (name, host))
    
    # Create the client socket
    sock=BluetoothSocket( RFCOMM )
    sock.connect((host, port))

    print("Pi connected to " + name)

sens = False

num_readings = 360
num_sensors = 6
ir_id = 92
laser_id = 93
gyro_id = 94
stop_id = 255

# state0 = waiting, state1 = reading ir-data, state2 = reading laser-data, state3 = reading gyro_data
serial_state = 0

# if the laser-data stopped during runtime, this variable is used to find out which index we should start adding data when continuing
cur_laser_index = 0

last_gyro_time = time.time()
last_gyro_value = 0
gyro_value = 0
sensor_value = [0 for x in range(num_sensors)]
sensor_value_prev = None
laser_value = []
last_laser_value = []
last_laser_value_prev = None
for i in range(300):
    last_laser_value.append(math.sin(i) * ((i+50) % 310) )
#last_laser_value[0] = 1000
#init_sensor_value =["1233321","666","188784","123123"]
num_laser_reads = 0

debug_data = []

req = False
a = 5

delay = 1

forward_down = False
backward_down = False
left_down = False
right_down = False
#movement_dir = "stop"

auto_mode = False

if (auto_mode): req = False

serUSB0 = None
#serUSB0 = serial.Serial("/dev/ttyUSB0")



def find_usb(port_id):
	port = ""
        for file in os.listdir("/dev/serial/by-id"):
		if port_id in file:
			symlink = os.path.join("/dev/serial/by-id/", file)
			port = str(os.path.realpath(symlink))
	return port



try:
    serUSB0 = serial.Serial(find_usb(SENSOR_PORT))
    serUSB0.baudrate = BAUDRATE2
except serial.serialutil.SerialException, exc:
    print("USB0 IT NO WORK, Johan did fuck up! %s" % exc)

"""
serUSB1 = None
try:
    print("Open port plx")
    serUSB1 = serial.Serial(find_usb(STEERING_PORT), writeTimeout=0)
    serUSB1.baudrate = BAUDRATE
except serial.serialutil.SerialException, exc:
    print("USB1 IT NO WORK, Fixa saken Gomba %s" % exc)
"""
    
#running = True

"""
def steering_serial(tid):
    print("Thread" + str(tid) + "main loop initialized")

    global serUSB1
    prev_movement = "none"
    
    while running:
        if (serUSB1 != None):
            try:
                if (serUSB1.isOpen()):
                    condition.acquire()
                    while True:
                        temp_move = movement_dir
                        if movement_dir != "none":
                            break
                        condition.wait()
                    condition.release()
                    if temp_move == "forward" and prev_movement != "forward":
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
"""
                
def sensor_serial(tid):
    print("Thread" + str(tid) + " main loop initialized")
    global sensor_value
    global serUSB0
    global serial_state
    global cur_laser_index
    global laser_value
    global last_laser_value
    global gyro_value
    global num_laser_reads
    global last_gyro_time
    global last_gyro_value
    global robot_rot
    while running:
       # print("SENSOR")
       # old = time.time()
        #sensor_value = ["0"]
        if (serUSB0 != None):
            try:
                print("yebanjo")
                if (serUSB0.isOpen()):
                    #If we are waiting for serial data
                    last_read = None
                    if (serial_state == 0):
                        byte = serUSB0.read(1)
                        byteORD = ord(byte)
                        if (byteORD == ir_id): serial_state = 1
                        if (byteORD == laser_id): serial_state = 2
                        if (byteORD == gyro_id): serial_state = 3
                    if (serial_state == 1):
                        #ir_state
                        for i in range(0,num_sensors):
                            byte = serUSB0.read(1)
                            byteORD = ord(byte)
                            sensor_value[i] = str(byteORD) 
                        serial_state = 0
                    elif (serial_state == 2):
                        #laser_state
                        val1 = None
                        val2 = None
                        brake_state = False

                        b1 = serUSB0.read(1)
                        b1ORD = ord(b1)

                        if (b1ORD == stop_id):
                            last_laser_value = laser_value
                            laser_value = []
                            a = serUSB0.read(1)
                            aORD = ord(a)
                            b = serUSB0.read(1)
                            bORD = ord(b)
                            c = serUSB0.read(1)
                            cORD = ord(c)
                            value = int(bORD) * 256 + int(cORD)
                            #print("Len : " + str(len(last_laser_value)) + ", sent Len : " + str(value) + ", laserDIFF : " + str(aORD))
                        else:
                            b2 = serUSB0.read(1)
                            b2ORD = ord(b2)
                            val1 = b1ORD
                            val2 = b2ORD
                            laser_value.append(int(val1) * 256 + int(val2))
                        serial_state = 0
                    elif (serial_state == 3):
                        #gyro_state
                        byte = serUSB0.read(1)
                        byteORD = ord(byte)
                        byte2 = serUSB0.read(1)
                        byteORD2 = ord(byte2)
                        gyro_value2 = byteORD * 256 + byteORD2
                        
                        bias = 2500
                        
                        gyro_value = (((25.0/12) * gyro_value2) + 400 - bias)/6.67
                        #print(gyro_value)
                        elap = (time.time() - last_gyro_time)
                        last_gyro_value = gyro_value * elap

                        #if (math.fabs(math.radians(last_gyro_value)) >= 0.005):
                        #    robot_rot += math.radians(last_gyro_value)
                        last_gyro_time = time.time()
                        serial_state = 0
                    else:
                        serial_state = 0
            except serial.serialutil.SerialException, exc:
                print("An error occured with the serial connection on the sensor port: %s" % exc)
        
    serUSB0.close()

    
def bluetooth_loop(tid):
    print("Thread" + str(tid) + " main loop initialized")
    global running
    global sock
    global req
    global forward_down
    global backward_down
    global left_down
    global right_down
    global movement_dir
    global robot_pos
    global robot_rot
    global sensor_value
    global last_laser_value_prev
    global sensor_value_prev
    global robot_pos_prev
    global robot_rot_prev
    global map_prev
    global map
    global condition
    inter = 0
    printDebug = False
    while running:
        #print("BLUETOOTH")
        #old = time.time() # time.time.time.time.time
        #time.now()
        #time.sleep(.001)
        #inter += 1
        #inter = inter % 2
        #map = set_block(map, inter+1, 0,0)
        #print(equal2D(map, map_prev))
        if (printDebug):
            print("rob_rot" + str(math.degrees(robot_rot)))
            print("Gyro_Value: " + str(gyro_value))
            print("sensor" + str(sensor_value))
            print("Laser CURRENT curr : " + str(last_laser_value))
            print("laser size : " + str(len(last_laser_value)))

        if (forward_down):
            robot_pos = move_in_dir(robot_pos, speed, robot_rot)            
        if (backward_down):
            robot_pos = move_in_dir(robot_pos, -speed, robot_rot)
        if (left_down):
            robot_rot -= robot_rot_speed
        if (right_down):
            robot_rot += robot_rot_speed


            

        if (bluetooth_online):
            map_string = str(map)
            map_string = map_string.translate(None, " ")
            map_string = map_string.translate(None, "[")
            map_string = map_string.translate(None, "]")
            map_string = "[" + map_string + "]"
            #Every other iteration of main loop, send request to laptop for instructions.
            if (req):
                print("REQUESTING")
                req = False
                #if(True):
                sock.send("!req#")
                data2 = sock.recv(1024)
                if (len(data2) == 0): break
                condition.acquire()
                if (data2 != b"none"):
                    if (data2 == b"forward" and not forward_down):
                        forward_down = True
                        movement_dir = "forward"
                    elif (data2 == b"backward" and not backward_down):
                        backward_down = True
                        movement_dir = "backward"
                    elif (data2 == b"left" and not left_down):
                        left_down = True
                        movement_dir = "left"
                    elif (data2 == b"right" and not right_down):
                        right_down = True
                        movement_dir = "right"
                    elif (data2 == b"stop"):
                        forward_down = False
                        backward_down = False
                        left_down = False
                        right_down = False
                        movement_dir = "stop"
                else:
                    movement_dir = "none"
                #print(movement_dir)
                condition.notify()
                condition.release()
                    
                                                
            else:
                if (not auto_mode): req = True

                if (sensor_value_prev != sensor_value):
                    temp_data = "[sens]";
                    temp_data += str(sensor_value)
                    temp_data += "#"
                    sock.send(temp_data)

                #if (last_laser_value_prev != last_laser_value):
                temp_data = "[laser]"
                temp_data += str(last_laser_value)
                temp_data += "#"
                sock.send(temp_data)
                    
                temp_data = "[gyro]"
                temp_data += str(gyro_value)
                temp_data += "#"
                sock.send(temp_data)

                #if not (robot_pos_prev == robot_pos and robot_rot_prev == robot_rot):
                temp_data = "[rob]["
                temp_data += str(robot_pos[0]) + ","
                temp_data += str(robot_pos[1]) + ","
                temp_data += str(robot_rot) + "]"
                temp_data += "#"
                sock.send(temp_data)

                if (map_prev != map):
                    #print("fuck FIDDE")
                    temp_data = "[map]"
                    temp_data += map_string
                    temp_data += "#"
                    #print(map_string)
                    sock.send(temp_data)

        #print(equal2D(map, map_prev))
        last_laser_value_prev = copy.deepcopy(last_laser_value)
        sensor_value_prev = copy.deepcopy(sensor_value)
        robot_pos_prev = robot_pos
        robot_rot_prev = robot_rot
        #print(map_prev == map)
        map_prev = copy.deepcopy(map)
       # print("BT: ", time.time()-old)
    if (bluetooth_online): sock.close()

t1.start()
#t2.start()
t3.start()
