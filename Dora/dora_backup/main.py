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
import common
import global_vars as gv
import steering
import sensor

#Debug variables
speed = 0.5
map_size = 21


#class for threading
class Thread(threading.Thread):
    def __init__(self, threadID, typee):
        threading.Thread.__init__(self)
        self.threadID = threadID
        #typee == 0: bluetooth, typee 1 = serial
        self.typee = typee
    def run(self):
        
        if (self.typee == 0): bluetooth_loop(self.threadID)
        if (self.typee == 1): sensor.sensor_serial(self.threadID)
        if (self.typee == 2): steering.steering_serial(self.threadID)

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
#robot_rot = math.pi
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
        print("the DoraServer service")
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

# state0 = waiting, state1 = reading ir-data, state2 = reading laser-data, state3 = reading gyro_data
#serial_state = 0

# if the laser-data stopped during runtime, this variable is used to find out which index we should start adding data when continuing
#cur_laser_index = 0

#gv.last_gyro_time = time.time()
#last_gyro_value = 0
#gyro_value = 0
#gv.sensor_value = [0 for x in range(num_sensors)]
sensor_value_prev = None
#laser_value = []
#last_laser_value = []
last_laser_value_prev = None

for i in range(300):
    gv.last_laser_value.append(math.sin(i) * ((i+50) % 310) )
#num_laser_reads = 0

debug_data = []

req = False
a = 5

delay = 1

forward_down = False
backward_down = False
left_down = False
right_down = False

auto_mode = False

if (auto_mode): req = False


def bluetooth_loop(tid):
    print("Thread" + str(tid) + " main loop initialized")
    global sock, req
    global forward_down, backward_down, left_down, right_down
    global robot_pos#, robot_rot
    #global sensor_value
    global last_laser_value_prev, sensor_value_prev, robot_pos_prev, robot_rot_prev
    global map_prev, map
    
    inter = 0
    printDebug = False
    
    while gv.running:
        #map = set_block(map, inter+1, 0,0)
        #print(equal2D(map, map_prev))
        if (printDebug):
            print("rob_rot" + str(math.degrees(gv.robot_rot)))
            print("Gyro_Value: " + str(gv.gyro_value))
            print("sensor" + str(gv.sensor_value))
            print("Laser CURRENT curr : " + str(gv.last_laser_value))
            print("laser size : " + str(len(gv.last_laser_value)))

        if (forward_down):
            robot_pos = move_in_dir(robot_pos, speed, gv.robot_rot)            
        if (backward_down):
            robot_pos = move_in_dir(robot_pos, -speed, gv.robot_rot)
        if (left_down):
            gv.robot_rot -= gv.robot_rot_speed
        if (right_down):
            gv.robot_rot += gv.robot_rot_speed
            

        if (bluetooth_online):
            map_string = str(map)
            map_string = map_string.translate(None, " ")
            map_string = map_string.translate(None, "[")
            map_string = map_string.translate(None, "]")
            map_string = "[" + map_string + "]"
            #Every other iteration of main loop, send request to laptop for instructions.
            if (req):
                req = False
                sock.send("!req#")
                data2 = sock.recv(1024)

                if (len(data2) == 0):
                    break
                
                gv.condition.acquire()
                print(data2)
                if (data2 != b"none"):
                    if (data2 == b"forward" and not forward_down):
                        forward_down = True
                        gv.movement_dir = "forward"
                    elif (data2 == b"backward" and not backward_down):
                        backward_down = True
                        gv.movement_dir = "backward"
                    elif (data2 == b"left" and not left_down):
                        left_down = True
                        gv.movement_dir = "left"
                    elif (data2 == b"right" and not right_down):
                        right_down = True
                        gv.movement_dir = "right"
                    elif (data2 == b"stop"):
                        forward_down = False
                        backward_down = False
                        left_down = False
                        right_down = False
                        gv.movement_dir = "stop"
                else:
                    gv.movement_dir = "none"
                gv.condition.notify()
                gv.condition.release()
                    
                                                
            else:
                if (not auto_mode): req = True

                if (sensor_value_prev != gv.sensor_value):
                    temp_data = "[sens]";
                    temp_data += str(gv.sensor_value)
                    temp_data += "#"
                    sock.send(temp_data)

                #if (last_laser_value_prev != gv.last_laser_value):
                temp_data = "[laser]"
                temp_data += str(gv.last_laser_value)
                temp_data += "#"
                sock.send(temp_data)
                    
                temp_data = "[gyro]"
                temp_data += str(gv.gyro_value)
                temp_data += "#"
                sock.send(temp_data)

                #if not (robot_pos_prev == robot_pos and robot_rot_prev == gv.robot_rot):
                temp_data = "[rob]["
                temp_data += str(robot_pos[0]) + ","
                temp_data += str(robot_pos[1]) + ","
                temp_data += str(gv.robot_rot) + "]"
                temp_data += "#"
                sock.send(temp_data)

                if (map_prev != map):
                    temp_data = "[map]"
                    temp_data += map_string
                    temp_data += "#"
                    sock.send(temp_data)

        #print(equal2D(map, map_prev))
        last_laser_value_prev = copy.deepcopy(gv.last_laser_value)
        sensor_value_prev = copy.deepcopy(gv.sensor_value)
        robot_pos_prev = robot_pos
        robot_rot_prev = gv.robot_rot
        map_prev = copy.deepcopy(map)
    if (bluetooth_online): sock.close()

    
t1.start()
t2.start()
t3.start()

