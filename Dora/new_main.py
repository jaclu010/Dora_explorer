# -*- coding: utf-8 -*-
from __future__ import print_function
import serial
from bluetooth import *
import sys
import time
import math
import threading

#Debug variables
speed = 0.5
robot_rot_speed = math.pi / 40

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
        if (self.typee == 1): serial_loop(self.threadID)
        if (self.typee == 2): serial_loop_2(self.threadID)
        #print("Starting thread" + str(self.threadID))
        #print_time(self.threadID)
        #print("Exiting thread" + str(self.threadID))


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


#sets the block in 2D-list d_list to val at x,y
def set_block(d_list, val, x, y):
    if (x >= 0 and y >= 0 and x < map_size and y < map_size):
        d_list[y][x] = val 


#Translates the position of robot 
def move_in_dir(pos, speed, rotation, forward):
    newx = 0
    newy = 0
    p1 = pos
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
laser_value = []
last_laser_value = laser_value
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
movement_dir = "stop"

auto_mode = False

if (auto_mode): req = False

BAUDRATE = 115200
serUSB0 = None
#serUSB0 = serial.Serial("/dev/ttyUSB0")
try:
    serUSB0 = serial.Serial("/dev/ttyUSB0")
    serUSB0.baudrate = BAUDRATE
except serial.serialutil.SerialException:
    print("USB0 IT NO WORK, Johan did fuck up!")

serUSB1 = None
try:
    serUSB1 = serial.Serial("/dev/ttyUSB0")
    serUSB1.baudrate = BAUDRATE
except serial.serialutil.SerialException:
    print("USB1 IT NO WORK, Fixa saken Gomba")
    
    
running = True


"""
Send commands to styr-module

"""

def serial_loop_2(tid):
    prev_movement = "none"
    print("Thread" + str(tid) + "main loop initialized")
    
    global serUSB1
    if (serUSB1 != None):
        serUSB1.write("a".encode())
        serUSB1.write("a".encode())
        serUSB1.write("a".encode())
        serUSB1.write("a".encode())

    while running:
        if (serUSB1 != None):
            try:
                if (serUSB1.isOpen()):
                    if movement_dir == "forward" and prev_movement != "forward":
                        serUSB1.write("f".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(200))
                        prev_movement = "forward"
                        print(prev_movement)
                    elif movement_dir == "backward" and prev_movement != "backward":
                        serUSB1.write("b".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(200))
                        prev_movement = "backward"
                        print(prev_movement)
                    elif movement_dir == "left" and prev_movement != "left":
                        serUSB1.write("l".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(200))
                        prev_movement = "left"
                        print(prev_movement)
                    elif movement_dir == "right" and prev_movement != "right":
                        serUSB1.write("r".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(200))
                        prev_movement = "right"
                        print(prev_movement)
                    elif movement_dir == "stop" and prev_movement != "stop":
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(0))
                        prev_movement = "stop"
                        print(prev_movement)
                    """
                    if (forward_down and not backward_down):
                        serUSB1.write("f".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(200))                    
                        #print("we go f")
                    elif (not forward_down and backward_down):
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(200))                    
                        serUSB1.write("b".encode())
                        #print("b")
                    if (left_down):
                        serUSB1.write("l".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(200))
                        #print("left")
                    elif (right_down):
                        serUSB1.write("r".encode())
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(200))                    
                        #print("r")
                    if (not forward_down and not backward_down and not left_down and not right_down):
                        serUSB1.write("s".encode())
                        serUSB1.write(chr(0))
                        #print("stop")
                    """
                    #a = chr(240)
                    #serUSB1.write("s".encode())
                    #serUSB1.write(chr(240))
                    #time.sleep(5)
                    #serUSB1.write("b".encode())
                    #x
                    #print("serusb1 connected")
            except serial.serialutil.SerialException:
                print("Something really wierd happened to the serial connection USB1")



max_value = 0

                
def serial_loop(tid):
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
    global max_value
    while running:
        #sensor_value = ["0"]
        if (serUSB0 != None):
            try:
                if (serUSB0.isOpen()):
                    #If we are waiting for serial data
                    last_read = None
                    if (serial_state == 0):
                        byte = serUSB0.read(1)
                        byteORD = ord(byte)
                        if (byteORD == ir_id): serial_state = 1
                        if (byteORD == laser_id):
                            serial_state = 2
                            b1_1 = serUSB0.read(1)
                            b1_2 = ord(b1_1)

                            b2_1 = serUSB0.read(1)
                            b2_2 = ord(b2_1)

                            num_laser_reads = int(b1_2) * 256 + int(b2_2) 
                            #print(num_laser_reads)
                        if (byteORD == gyro_id): serial_state = 3
                    if (serial_state == 1):
                        #ir_state
                        #print("ir")
                        for i in range(0,num_sensors):
                            byte = serUSB0.read(1)
                            byteORD = ord(byte)
                            sensor_value[i] = str(byteORD) 
                        serial_state = 0
                    elif (serial_state == 2):
                        #laser_state
                        #print("laser")
                        val1 = None
                        val2 = None
                        brake_state = False
                        laser_value = []
                        for i in range(0, num_laser_reads):
                            for l in range(0,2):
                                byte = serUSB0.read(1)
                                byteORD = ord(byte)
                                if(l == 0):
                                    val1 = byteORD
                                else:
                                    val2 = byteORD
                            laser_value.append(int(val1) * 256 + int(val2))
                        last_laser_value = laser_value
                        serial_state = 0
                    elif (serial_state == 3):
                        #gyro_state
                        #print("gyro")
                        byte = serUSB0.read(1)
                        byteORD = ord(byte)
                        byte2 = serUSB0.read(1)
                        byteORD2 = ord(byte2)
                        gyro_value2 = byteORD * 256 + byteORD2
                        #print(gyro_value)
                        
                        bias = 2500
                        
                        gyro_value = (((25.0/12) * gyro_value2) + 400 - bias)/6.67
                        
                        elap = (time.time() - last_gyro_time)
                        last_gyro_value = gyro_value * elap

                        if (math.fabs(math.radians(last_gyro_value)) >= 0.005):
                            robot_rot += math.radians(last_gyro_value)
                        last_gyro_time = time.time()
                        serial_state = 0
                    else:
                        serial_state = 0
            except serial.serialutil.SerialException:
                print("Something really wierd happened with serial connection")
        
        
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
    global robot_pos
    global robot_rot
    global sensor_value
    global movement_dir
    
    while running:
        time.sleep(.5)
        
        #print(last_gyro_value)
        #print("max" + str(max_value))

        print("rob_rot" + str(math.degrees(robot_rot)))
        #print(robot_rot)
        #If bluetooth connection is established, send data
        print("Gyro_Value: " + str(gyro_value))
        print("sensor" + str(sensor_value))
        print("Laser: " + str(last_laser_value))
        #print("")
        #if (gyro_value):
        #    print(gyro_value)
        #print(gyro_value)
        
        if (bluetooth_online):
            map_string = str(map)
            map_string = map_string.translate(None, " ")
            map_string = map_string.translate(None, "[")
            map_string = map_string.translate(None, "]")
            map_string = "[" + map_string + "]"
            #print("BT_ONLINE" + str(bluetooth_online))
            #Every other iteration of main loop, send request to laptop for instructions.
            if (req):
                req = False
                #if(True):
                sock.send("!req#")
                data2 = sock.recv(1024)
                if (len(data2) == 0): break
                if (data2 != b"none"):
                    print(data2)
                    movement_dir = str(data2)
                    print("Movement: " + movement_dir)
                    """
                    if (data2 == b"forward" and not forward_down):
                        forward_down = True
                    if (data2 == b"backward" and not backward_down):
                        backward_down = True
                    if (data2 == b"left" and not left_down):
                        left_down = True
                    if (data2 == b"right" and not right_down):
                        right_down = True
                    if (data2 == b"stop"):
                        forward_down = False
                        backward_down = False
                        left_down = False
                        right_down = False
                    """
                            
            else:
                if (not auto_mode): req = True
                
                temp_data = "[sens]";
                temp_data += str(sensor_value)
                temp_data += "#"
                sock.send(temp_data)

                temp_data = "[laser]"
                temp_data += str(last_laser_value)
                temp_data += "#"
                sock.send(temp_data)

                temp_data = "[gyro]"
                temp_data += str(gyro_value)
                temp_data += "#"
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
            #print("we go forward")
        if (backward_down):
            robot_pos = move_in_dir(robot_pos, speed, robot_rot, False)
        if (left_down):
            robot_rot -= robot_rot_speed
        if (right_down):
            robot_rot += robot_rot_speed
        
    if (bluetooth_online): sock.close()

t1.start()
t2.start()
t3.start()
