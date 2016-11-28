# -*- coding: utf-8 -*-
from __future__ import print_function
import serial
from bluetooth import *
import sys
import time
import math
import threading

speed = 0.5
robot_rot_speed = math.pi / 40

class Thread(threading.Thread):
    def __init__(self, threadID, typee):
        threading.Thread.__init__(self)
        self.threadID = threadID
        #typee == 0: bluetooth, typee 1 = serial
        self.typee = typee

    def run(self):
        if (self.typee == 0): bluetooth_loop(self.threadID)
        if (self.typee == 1): serial_loop(self.threadID)

        #print("Starting thread" + str(self.threadID))
        #print_time(self.threadID)
        #print("Exiting thread" + str(self.threadID))

def print_time(id):
    c = 5
    d = 2
    if (id == 0):
        c = 10
        d = 1
    while c:
        time.sleep(d)
        print ("thread" + str(id) + " : " + str(time.ctime(time.time()))) 
        c -= 1

t1 = Thread(1, 0)
t2 = Thread(2, 1)

        
def gen_empty_map():
    a = []
    for y in range (0,21):
        
        b = []
        for x in range (0,21):
            b += ["1"]
        a += [b]
    return a


def set_block(d_list, val, x, y):
    if (x >= 0 and y >= 0 and x < 21 and y < 21):
        d_list[y][x] = val 

def move_in_dir(pos, speed, rotation, forward):
    newx = 0
    newy = 0
    p1 = pos
    #print(forward)
    if (forward):
        newx = p1[0] - speed*math.cos(rotation)
        newy = p1[1] - speed*math.sin(rotation)
    else:
        newx = p1[0] + speed*math.cos(rotation)
        newy = p1[0] + speed*math.sin(rotation)
    #print (str(newx) + ", " + str(newy) )
        
    return (newx, newy)
        
map = gen_empty_map()

set_block(map,"2",0,0)
for y in range (0, 21):
    for x in range (0,21):
        if (x == 0 or y == 0 or x == 20 or y == 20):
            set_block(map, "2", x, y)
        if (x <= 5 and y <= 5): 
            set_block(map, "2", x, y)
        if (x <= 4 and y <= 4):
            set_block(map, "0", x ,y)
map_string = ""

robot_pos = (0,0)
robot_rot = math.pi


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
sensor_value = [0]
init_sensor_value =["1233321","666","188784","123123"]

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

BAUDRATE = 115200

serUSB0 = serial.Serial("/dev/ttyUSB0")
serUSB0.baudrate = BAUDRATE

running = True


def serial_loop(tid):
    print("Thread" + str(tid) + " main loop initialized")
    global sensor_value
    global serUSB0    
    while running:
        if (serUSB0.isOpen()):
            try:
                a = serUSB0.read(1)
                b = ord(a)
                if (b != 252 and b != 246):
                    sensor_value[0] = str(b)
            except serial.serialutil.SerialException:
                print("Something really wierd happened with serial connection")
def bluetooth_loop(tid):
    print("Thread" + str(tid) + " main loop initialized")
    global running
    global sock
    global req
    global forward_down
    global backward_down
    global left_down
    global right_down
    
    while running:
        #print("printing from global thread: hihihihi: " + str(sensor_value))
        time.sleep(0.1)
        print(sensor_value)


t1.start()
t2.start()






#Main loop
while True:
    break
    #Map serial data
    sensor_value = []
    if (serUSB0.isOpen() and False):
        try:
            #if (serUSB0.inWaiting() > 0):
            a = serUSB0.read(1)
            b = ord(a)
            if (b !=252):
                if(b != 246):
                    print(str(b), end ="")
                else:
                    print("_______")
            else:
                print(",", end ="")
                #print(b)
        except serial.serialutil.SerialException:
            print("Some wierd shit is going on")
            
    #Slam magic
            
    #If bluetooth connection is established, send data
    if (bluetooth_online):
        map_string = str(map)
        map_string = map_string.translate(None, " ")
        map_string = map_string.translate(None, "[")
        map_string = map_string.translate(None, "]")
        map_string = "[" + map_string + "]"

        #Every other iteration of main loop, send request to laptop for instructions.
        if (req):
            req = False
            #if(True):
            sock.send("!req#")
            data2 = sock.recv(1024)
            if (len(data2) == 0): break
            if (data2 != b"none"):
                
                if (data2 == b"forward" and not forward_down):
                    forward_down = True
                if (data2 == b"backward" and not backward_down):
                    backward_down = True
                if (data2 == b"left" and not left_down):
                    left_down = True
                if (data2 == b"right" and not right_down):
                    right_down = True
                if (data2 == b"stop"):
                    forward_down = backward_down = left_down = right_down = False
        else:
            if (not auto_mode): req = True
            sensor_value = []
            temp_data = "[sens][";

            for i in range(0,len(sensor_value)-1):
                temp_data += str(sensor_value[i])
                if (i < len(sensor_value)-2):
                    temp_data += ","
            temp_data += "]#"
            sock.send(temp_data)
        
            temp_data = "[rob]["
            temp_data += str(robot_pos[0]) + ","
            temp_data += str(robot_pos[1]) + ","
            temp_data += str(robot_rot) + "]"
            temp_data += "#"
            #print(temp_data)
            sock.send(temp_data)
        
            temp_data = "[map]"
            temp_data += map_string
            temp_data += "#"
            #print(temp_data)
            sock.send(temp_data)
        
    if (forward_down):
       robot_pos = move_in_dir(robot_pos, speed, robot_rot, True)
    if (backward_down):
        robot_pos = move_in_dir(robot_pos, speed, robot_rot, False)
    if (left_down):
        robot_rot -= robot_rot_speed
    if (right_down):
        robot_rot += robot_rot_speed
        
if (bluetooth_online): sock.close()
serUSB0.close
