
# -*- coding: utf-8 -*-
from __future__ import print_function
from laser_test import *
import serial
import sys
import time
import math
import copy
import os
from common import *
from global_vars import *
import steering as st
import sensor
import control
import blueztooth
import path
import doramapper
from multiprocessing import Process, Value, Array
from multiprocessing.queues import SimpleQueue

forward_dir = FORWARD
ir_id = FORWARD_SENSOR_MAPPING

#Debug variables
speed = 0.5

#generates an empty map
def gen_empty_map():
    a = []
    for row in range (0,MAP_SIZE):
        b = []
        for col in range (0,MAP_SIZE):
            b += ["0"]
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



#if python version not 3
if sys.version < '3':
    input  = raw_input

# GLOBAL VARS
robot_pos = [15.5, 15.5]
robot_dir = NORTH

current_tile_pos = [0, 0]
verified_grids = 0

need_new_time = True

travel_commands = []

    
debug_data = []

req = False
a = 5

delay = 1

forward_down = False
backward_down = False
left_down = False
right_down = False

auto_mode = False
state = MANUAL

if (auto_mode): req = False

def stop_tower(num_hall_reads):
    st.set_speed(AUTO_MODE, 30, "tower")
    while num_hall_reads.value < 1:
        pass

    while num_hall_reads.value > 0:
        pass
    while num_hall_reads.value < 1:
        pass    
    #print("Stopping: " + str(num_hall_reads.value))
    st.set_speed(AUTO_MODE, 0, "tower")

def calc_distance(time_driven):
    #return 43.79*time_driven-3.185
    return 51.5*time_driven-3.185
    
def go_tiles(tiles):
    print('GO TILE')
    start_time = time.time()
    st.forward()
    st.set_speed(AUTO_MODE, 125)

    # Move until correct number of tiles are traversed
    while calc_distance(time.time() - start_time) < tiles * 40:
        #print(calc_distance(time.time() - start_time))
        pass
    if tiles >= 1:
        update_robot_pos(tiles)
    else:
        update_robot_pos(1)
    st.set_speed(AUTO_MODE, 0)

def update_robot_pos(num_tiles):
    global robot_pos
    # Update robot position
    if robot_dir % 4 == NORTH:
        robot_pos[1] -= num_tiles
    elif robot_dir % 4 == EAST:
        robot_pos[0] += num_tiles
    elif robot_dir % 4 == SOUTH:
        robot_pos[1] += num_tiles
    elif robot_dir % 4 == WEST:
        robot_pos[0] -= num_tiles
    print('Robot pos', robot_pos) 

def get_grid_pos(laser_values):
    global current_tile_pos
    num_values = len(laser_values)
    if num_values == 0:
        return
    step = math.radians(360.0) / num_values
    temp_x = []
    temp_y = []
    for i in range(num_values):

        #Laser read starts pointing backwards i.e 270 degrees
        x = laser_values[i] * math.cos((math.radians(270) + step * i))
        y = laser_values[i] * math.sin((math.radians(270) + step * 1))

        if i == 2:
            current_tile_pos[1] = round(abs(y) % TILE_SIZE)
        elif i == ((num_values // 4) * 3)+2:
            current_tile_pos[0] = round(abs(x) % TILE_SIZE)

    if len(temp_x) > 0:
        current_tile_pos[0] = sum(temp_x) / len(temp_x)
    if len(temp_y) > 0:
        current_tile_pos[1] = sum(temp_y) / len(temp_y)



def do_turn(turn_deg, side):
    global robot_dir, state, verified_grids, need_new_time
    #print("TURNING: " + str(TURN_TIME[turn_deg]) )
    if side == LEFT or side == 'left':
        #print("Turning left")
        st.left()
        robot_dir = (robot_dir - (turn_deg//90)) % 4
    elif side == RIGHT or side == 'right':
        #print("Turning right")
        st.right()
        robot_dir = (robot_dir + (turn_deg//90)) % 4
    else:
        return
    
    st.set_speed(AUTO_MODE, 150)
    start_angle = gyro_value.value
    while abs(gyro_value.value - start_angle) < turn_deg-10:
        pass
            
    st.set_speed(AUTO_MODE, 0)
    st.forward()
    time.sleep(0.1)
    
    need_new_time = True
    verified_grids = 0
    
    print('DIRECTION', robot_dir)
    #go_tiles(1)
    if travel_commands:
        state = TRAVEL
    else:
        state = WALL

        
def slam(ir_values, laser_values, mode, steering_cmd_man, pid_cons, gyro_value, num_laser_values, num_hall_reads, grid):
    global state, robot_pos, robot_dir, travel_commands, need_new_time, verified_grids
    st.open_port()
    
    #st.set_speed(AUTO_MODE,0,"tower")
    ir_id = FORWARD_SENSOR_MAPPING
    forward_dir = FORWARD
    driving_dir = 0
    RIGHT, LEFT = 0,1
    pid_side = RIGHT
    start_driving_time = 0
    current_grid_walls = [[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]

    driven_grids = 0
    debug = True
    
    last_robot_pos = [15.5, 15.5]
    prev_pos = []
    pid = control.PID(10, 10, 0, 5)
    pid.set_output_limits(-125, 125)
    
    control.forward_sensor = ir_id[FORWARD_RIGHT]
    control.backward_sensor = ir_id[BACKWARD_RIGHT]

    adjusted_laser = []
    last_laser_list = []

    search_mode = LASER
    stop_tower(num_hall_reads)
    mapping_time = time.time()
    start_pos = [pos for pos in robot_pos]

    mapper = doramapper.Mapping()
    generated = False
    
    st.forward()
    #st.set_speed(AUTO_MODE,0,"tower")
    while True:
        #print(robot_pos)

        """
        laser_list = []

        # Copy laser_values to list
        # with laser_values.get_lock()
        laser_list = [laser_values[i] for i in range(len(laser_values))]
        #for i in range(num_laser_values.value):
        #    laser_list[i] = laser_values[i]

        # Check if we have new laser values
        if laser_list != last_laser_list:
            adjusted_laser = []
            dist = math.sqrt((robot_pos[0] - last_robot_pos[0]) ** 2 + (robot_pos[1] - last_robot_pos[1]) ** 2)
        
            for i in range(num_laser_values.value):
                angle = (360 / num_laser_values.value) * i
                adjusted_laser += [laser_list[i] - (dist * math.cos(angle))]
                
                last_robot_pos = robot_pos
                last_laser_list = laser_list
        """
        
        if not mode.value:
            state = MANUAL
        
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

        if state == START:
            print("START")
            
            # Assign values to surrounding tiles from START position
            set_grid_value(15,15,EMPTY_TILE,grid)
            #set_grid_value(14,15,WALL_TILE,grid)
            set_grid_value(15,16,WALL_TILE,grid)
            #set_grid_value(15,14,EMPTY_TILE,grid)
            #set_grid_value(14,16,WALL_TILE,grid)
            #set_grid_value(16,16,WALL_TILE,grid)
            
            #go_tiles(1)
            #driven_grids += 1
            # Enter WALL to exit the starting cell
            state = WALL
                
        elif state == WALL:
            #print("WALL")
            """
            if time.time() - mapping_time > 10 and robot_pos == start_pos:
                print('MAPPING DONE', time.time() - mapping_time)
                st.set_speed(AUTO_MODE, 0)
                time.sleep(1)
                continue
            """

            # Save new time reference. Should be done after each turn
            if need_new_time:
                start_driving_time = time.time()
                need_new_time = False

            distance = calc_distance(time.time()-start_driving_time)
            
            if prev_pos != robot_pos and debug:
                #print("POS",robot_pos, distance)
                prev_pos = [robot_pos[0],robot_pos[1]]

            driven_grids = distance // 40

            # Count the number of times different walls are detected in the current grid
            if (distance - 5) - (driven_grids)*40 < 0:
                current_ir_values = []
                with ir_values.get_lock():
                    current_ir_values = [ir_values[i] for i in range(len(ir_values))]
                    
                for i in range(len(current_ir_values)):
                    if current_ir_values[i] < 25:
                        current_grid_walls[i][0] += 1
                    else:
                        current_grid_walls[i][1] += 1

            # Verify the grids around the current grid and update the map accordingly
            if driven_grids == verified_grids and distance > 5:
                # Don't update position when checking the first grid
                if driven_grids > 0:
                    is_inside_map = robot_pos[0] > 0 and robot_pos[0] < 30 and robot_pos[1] > 0 and robot_pos[1] < 30
                    if is_inside_map:
                        update_robot_pos(1)
                
                for i in range(len(current_grid_walls)):
                    # Map ir id to the correct index
                    index = i
                    if i == 2 or i == 3:
                        index = 2
                    elif i == 4 or i == 5:
                        index = 3
                    
                    check_tile = UNKNOWN_TILE
                    if current_grid_walls[i][0] > current_grid_walls[i][1]:  # Wall
                        check_tile = WALL_TILE
                    else:  # Empty
                        check_tile = EMPTY_TILE
                                          
                            
                    # Update map
                    if index != 1:
                        _x, _y = GRID_INDEX_VALUES[index][robot_dir]
                        #print("Updating map")
                        set_grid_value(int((robot_pos[0]+_x)),int((robot_pos[1]+_y)),check_tile,grid)
                
                current_grid_walls = [[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]
                verified_grids += 1

            if search_mode == LASER and not [ir_values[i] for i in range(len(ir_values)) if ir_values[i] != EMPTY_CHECK]:  # TODO: Lock ir_values?
                # All ir values == 25 (no walls detected), should switch to slam?
                state = SLAM
                st.set_speed(AUTO_MODE, 0)
                st.set_speed(AUTO_MODE, 80, 'tower')
                continue

            # Wall ahead
            if ir_values[ir_id[FORWARD]] <= FORWARD_CHECK:
                print("Wall forwards detected")
                if ir_values[ir_id[FORWARD_RIGHT]] <= RIGHT_CHECK and ir_values[ir_id[FORWARD_LEFT]] <= LEFT_CHECK:
                    print("Wall sides detected, turning back")
                    # Dead end, start driving backwards
                    state = DEAD_END
                elif ir_values[ir_id[FORWARD_RIGHT]] <= RIGHT_CHECK:
                    print("Wall right  detected, turning left")
                    # wall to the right, turn left
                    state = TURN_LEFT
                                            
                elif ir_values[ir_id[FORWARD_LEFT]] <= LEFT_CHECK:
                    # wall to the left, turn right
                    print("Wall left detected, turning right")
                    state = TURN_RIGHT
                print("LOOP forward wall")
                continue

            if ir_values[ir_id[FORWARD_LEFT]] == EMPTY_CHECK and ir_values[ir_id[BACKWARD_LEFT]] <= LEFT_CHECK:
                print(ir_values[4], ir_values[5])
                # We have detected an opening in the wall, turning left around corner
                #print("Turn left around corner")
                #print([ir_values[i] for i in range(len(ir_values))])
                st.set_speed(AUTO_MODE, 125)
                go_tiles(0.3)
                
                #do_turn(90,'left')
                #go_tiles(0.5)
                continue

            if ir_values[ir_id[FORWARD_RIGHT]] == EMPTY_CHECK and ir_values[ir_id[BACKWARD_RIGHT]] <= RIGHT_CHECK:
                # Opening in wall, turning right around corner
                #print("Turn right around corner")
                st.set_speed(AUTO_MODE, 125)
                time.sleep(0.2)
                state = TURN_RIGHT
                continue
                
            if ir_values[ir_id[FORWARD_LEFT]] < EMPTY_CHECK and ir_values[ir_id[BACKWARD_LEFT]] < EMPTY_CHECK:
                # Wall detected on left side
                if forward_dir == BACKWARD:
                    pid_side = RIGHT
                else:
                    pid_side = LEFT
                control.forward_sensor = ir_id[FORWARD_LEFT]
                control.backward_sensor = ir_id[BACKWARD_LEFT]
            elif ir_values[ir_id[FORWARD_RIGHT]] < EMPTY_CHECK and ir_values[ir_id[BACKWARD_RIGHT]] < EMPTY_CHECK:
                # Wall detected on right side
                if forward_dir == BACKWARD:
                    pid_side = LEFT
                else:
                    pid_side = RIGHT
                control.forward_sensor = ir_id[FORWARD_RIGHT]
                control.backward_sensor = ir_id[BACKWARD_RIGHT]


            if forward_dir == FORWARD:
                if pid_side == LEFT:
                    pid.reversed = True
                elif pid_side == RIGHT:
                    pid.reversed = False
            elif forward_dir == BACKWARD:
                if pid_side == LEFT:
                    pid.reversed = True
                elif pid_side == RIGHT:
                    pid.reversed = False

            pid.enabled = True
            turn = pid.compute(ir_values)

            if st.speeds[st.LEFT] != abs(int(st.speeds[st.DEFAULT] - turn)):
                st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] - turn), "left")
            if st.speeds[st.RIGHT] != abs(int(st.speeds[st.DEFAULT] + turn)):
                st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] + turn), "right")

        elif state == TRAVEL:
            print("TRAVEL")
            if not travel_commands:
            
                gr = [2,2,2,2,2,2,2,2,2,
                      2,2,2,1,2,2,2,2,2,
                      2,2,2,1,1,2,2,2,2,
                      2,2,2,1,1,2,2,2,2,
                      2,1,1,1,1,2,2,2,2,
                      2,1,1,1,1,2,2,2,2,
                      2,1,1,1,1,2,2,2,2,
                      2,1,1,1,1,2,2,2,2,
                      2,2,2,2,2,2,2,2,2]
                
                p = path.find_path(gr, [3, 1], [1, 7])
                travel_commands = path.follow_path(p, NORTH)
                
                print("cmd: " + str(travel_commands))
            
            while travel_commands:
                c = travel_commands.pop(0)
                parts = c.split('_')
                if parts[0] == "go":
                    tiles = int(parts[2])
                    go_tiles(tiles)
                    print("Travelling 2 tiles")
                elif parts[0] == "turn":
                    turn_deg = int(parts[2])
                    print("Turning " + str(turn_deg))
                    do_turn(turn_deg, parts[1])
            state = SLAM
            
        elif state == TURN_LEFT:
            do_turn(90, 'left')
            state = WALL
            need_new_time = True
            
        elif state == TURN_RIGHT:
            do_turn(90,'right')
            state = WALL
            need_new_time = True
            
        elif state == DEAD_END:
            do_turn(180, 'left')
            state = WALL
            need_new_time = True

        elif state == SLAM:
            #print("SLAM")
            
            
            pid.enabled = False
            if len(mapper.submaps) < 10 and num_laser_values.value > 0:
                print('first slam', num_laser_values.value)
                laser_list = []
                with laser_values.get_lock():
                    print('laser values', num_laser_values.value)
                    if num_laser_values.value > 520:
                        with num_laser_values.get_lock():
                            num_laser_values.value = 0
                        continue
                    laser_list = [laser_values[i] for i in range(num_laser_values.value)]
                mapper.laser.update_laser(laser_list)
                mapper.laser.draw_lines()
                mapper.fit_grid()
                print(len(mapper.submaps))
            elif not generated:
                print('generate')
                mapper.generate_map()
                generated = True
                for i in range(31):
                    for j in range(31):
                        value = mapper.finalmap[i][j]
                        newvalue = 0
                        if(value > 2):
                            newvalue = 2
                            print('value', newvalue)
                            set_grid_value(j, i, newvalue, grid)
            
            #state = WALL
                    
        elif state == MANUAL:
            print("MANUAL")
                                
            if mode.value == 1:
                need_new_time = True
                verified_grids = 0
                state = START
                continue
            
            pid.enabled = False
            st.steering_serial(steering_cmd_man, mode, ir_values)


if __name__ == "__main__":  
    ir_values = Array('i', 6)
    laser_values = Array('i', 520)
    num_laser_values = Value('i', 0)
    #curr_num_laser_values = Value('i',0)
    num_hall_reads = Value('i', 0)
    gyro_value = Value('d', 0)
    mode = Value('i', 0) # auto = 1
    pid = Array('d', 2)
    pid[0] = -1  # make sure to not read pid values from array on boot
    grid = Array('i', MAP_SIZE**2)
    
    steering_cmd_man = SimpleQueue()
    
    sensor_process = Process(target=sensor.sensor_serial, args=(ir_values, laser_values, gyro_value, num_laser_values, num_hall_reads))
    slam_process = Process(target=slam, args=(ir_values, laser_values, mode, steering_cmd_man, pid, gyro_value, num_laser_values, num_hall_reads, grid))
    bluetooth_process = Process(target=blueztooth.bluetooth_loop, args=(ir_values, laser_values, gyro_value, steering_cmd_man, mode, pid, num_laser_values, grid))

    sensor_process.start()
    slam_process.start()
    bluetooth_process.start()

    prev_laser = []
    """
    while True:
        lv = []
        if num_laser_values.value > 0:
            print(num_laser_values.value)
            with laser_values.get_lock():
                lv = [laser_values[i] for i in range(num_laser_values.value)]
            simple_laser(lv, grid)
        time.sleep(2)
    """
        
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
    slam_process.join()
    
