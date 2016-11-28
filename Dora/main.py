
# -*- coding: utf-8 -*-
from __future__ import print_function
import serial
import sys
import time
import math
import copy
import os
from common import *
import global_vars as gv
import steering as st
import sensor
import control
import blueztooth
from multiprocessing import Process, Value, Array
from multiprocessing.queues import SimpleQueue

forward_dir = FORWARD
ir_id = FORWARD_SENSOR_MAPPING

#Debug variables
speed = 0.5

#generates an empty map
map_size = 21
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



#def main_slam():

 #   while gv.running:
        #gv.condition.acquire()
        #print(gv.sensor_value)
  #      print()
        #gv.movement_dir 
        #gv.condition.notify()
        #gv.condition.release()

#t1.start()
#t2.start()
#t3.start()

def slam(ir_values, laser_values, mode, steering_cmd_man, pid_cons):
    st.open_port()

    pid = control.PID(10, 9, 9, 2.24)
    print("PID: " + str(pid.Kp) + " " + str(pid.Ki) + " " + str(pid.Kd)) 
    #pid.inverse = True
    pid.set_output_limits(-150, 150)
    
    control.forward_sensor = ir_id[FORWARD_RIGHT]
    control.backward_sensor = ir_id[BACKWARD_RIGHT]

    st.forward()
    
    while True:
        """
        if ir_id[FORWARD] <= 15 or ir_id[BACKWARD] <= 15:
            st.set_speed(0,0)
        """

        with pid_cons.get_lock():
            if pid_cons[0] != -1:
                if pid_cons[0] == 0:
                    pid.Kp = pid_cons[1]
                elif pid_cons[0] == 1:
                    pid.Ki = pid_cons[1]
                elif pid_cons[0] == 2:
                    pid.Kd = pid_cons[1]
                pid_cons[0] = -1
                print("PID: " + str(pid.Kp) + " " + str(pid.Ki) + " " + str(pid.Kd)) 

        if mode.value: # Auto mode
            pid.enabled = True
            turn = pid.compute(ir_values)

            #print("res: " + str(turn) + "   " + str(st.speeds[st.LEFT]) + "   " + str(st.speeds[st.RIGHT]))

            if st.speeds[st.LEFT] != abs(int(st.speeds[st.DEFAULT] - turn)):
                st.set_speed(mode.value, abs(st.speeds[st.DEFAULT] - turn), "left")
            if st.speeds[st.RIGHT] != abs(int(st.speeds[st.DEFAULT] + turn)):
                st.set_speed(mode.value, abs(st.speeds[st.DEFAULT] + turn), "right")
            
            
            
            """
            if res > 0:
                if st.speeds[st.LEFT] != st.speeds[st.DEFAULT]:
                    st.set_speed(mode.value, st.speeds[st.DEFAULT], "left")
                if st.speeds[st.RIGHT] != int(res):
                    st.set_speed(mode.value, res, "right")
                
            elif res < 0:
                if st.speeds[st.LEFT] != int(abs(res)):
                    st.set_speed(mode.value, abs(res), "left")
                if st.speeds[st.RIGHT] != st.speeds[st.DEFAULT]:
                    st.set_speed(mode.value, st.speeds[st.DEFAULT], "right")
            else:
                if st.speeds[st.RIGHT] != st.speeds[st.DEFAULT]:
                    st.set_speed(mode.value, st.speeds[st.DEFAULT], "right")
                if st.speeds[st.LEFT] != st.speeds[st.DEFAULT]:
                    st.set_speed(mode.value, st.speeds[st.DEFAULT], "left")
            """
        else:  # Manual mode
            pid.enabled = False
            st.steering_serial(steering_cmd_man, mode, ir_values)
        
   


if __name__ == "__main__":  
    ir_values = Array('i', 6)
    laser_values = Array('i', 520)
    num_laser_values = Value('i', 0)
    gyro_value = Value('d', 0)
    mode = Value('i', 0) # auto = 1
    pid = Array('i', 2)
    pid[0] = -1  # make sure to not read pid values from array on boot
    
    steering_cmd_man = SimpleQueue()
    
    sensor_process = Process(target=sensor.sensor_serial, args=(ir_values, laser_values, gyro_value, num_laser_values))
    slam_process = Process(target=slam, args=(ir_values, laser_values, mode, steering_cmd_man, pid))
    bluetooth_process = Process(target=blueztooth.bluetooth_loop, args=(ir_values, laser_values, gyro_value, steering_cmd_man, mode, pid, num_laser_values))

    sensor_process.start()
    slam_process.start()
    bluetooth_process.start()
    #steering_process.start()

    

    """
    # Test turning
    time.sleep(2)
    st.open_port()
    st.forward()
    st.set_speed(0,150)
    print(ir_values[0])
    for i in range(len(ir_values)):
        print(i, ir_values[i])

    print(num_laser_values.value)
        
    while True:
        if ir_values[sensor.FORWARD] <= 20:
            st.set_speed(0,0)
            time.sleep(0.1)
            st.set_speed(0,150)
            st.left()
            time.sleep(float(0.63))
            st.set_speed(0,0)
            temp = raw_input()
    """
    """
    # Test speeds
    time.sleep(2)
    st.open_port()
    st.set_speed(0,0)
    st.forward()
    while True:
        st.forward()
        speed = raw_input("Speed: ")
        dur = raw_input("Time: ")
        st.set_speed(0, int(speed))
        time.sleep(float(dur))
        st.set_speed(0,0)
        raw_input("Go back")
        st.backward()
        st.set_speed(0, int(speed))
        time.sleep(float(dur))
        st.set_speed(0,0)
    """
    sensor_process.join()
    #slam_process.join()
