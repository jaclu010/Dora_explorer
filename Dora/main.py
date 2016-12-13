
# -*- coding: utf-8 -*-
from __future__ import print_function
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
import copy
#import doramapper
from path import *
from position import *
import submap as sm
import slam_submapper2 as slammer 
from multiprocessing import Process, Value, Array
from multiprocessing.queues import SimpleQueue


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

auto_mode = False
state = MANUAL

wheel_distance = 0

left_count = 0
right_count = 0

x_gain = 0
y_gain = 0
test_pos = [15.5, 15.5]

pid = control.PID(10, 10, 0, 5)
pid.set_output_limits(-st.speeds[st.DEFAULT], st.speeds[st.DEFAULT])


def stop_tower(num_hall_reads):
    st.set_speed(AUTO_MODE, 30, "tower")
    while num_hall_reads.value < 1:
        pass

    while num_hall_reads.value > 0:
        pass
    while num_hall_reads.value < 1:
        pass

    st.set_speed(AUTO_MODE, 0, "tower")

def go_tiles_simple(tiles):
    global wheel_distance
    st.forward()
    st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
    start_pos = copy.deepcopy(robot_pos)
    start_dist = wheel_distance
    
    while wheel_distance - start_dist < 40 * tiles:
        get_distance()

    st.set_speed(AUTO_MODE, 0)
    

def go_tiles(tiles, ir_values, shared_pos, enable_pid=True):
    global robot_pos, robot_dir, wheel_distance, test_pos
    prev_pos = int_robot_pos(robot_pos)
    #start_time = time.time()
    st.set_speed(AUTO_MODE, 0)
    st.forward()
    

    compare_axis = None
    sign = 0
    if robot_dir == NORTH:
        compare_axis = 1
        sign = -1
    elif robot_dir == EAST:
        compare_axis = 0
        sign = 1
    elif robot_dir == SOUTH:
        compare_axis = 1
        sign = 1
    elif robot_dir == WEST:
        compare_axis = 0
        sign = -1

    start = robot_pos[compare_axis]
    dest = 0

    if sign == 1:
        dest = round(robot_pos[compare_axis]) + (sign * 0.5)
    elif sign == -1:
        dest = int(round(robot_pos[compare_axis],1)) + (sign * 0.5)

    
    to_drive = abs(round(dest - start, 1)) + (tiles - 1)
    #start_dist = wheel_distance
    wheel_distance = 0
    #print('POS: %s %s ' % (test_pos, robot_pos))
    #print('Attempting to move %f from pos %s %f' % (to_drive, str(robot_pos), dest))
    



    # Move until correct number of tiles are traversed
    #print('START DIST: %f  TO DRIVE: %f' % (abs(dest - robot_pos[compare_axis]), to_drive*40))
    st.steering_port.flushInput()
    st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
    while wheel_distance < to_drive * 40:
    #while abs(round(dest - robot_pos[compare_axis], 1)) > 0:
        #print(dest - robot_pos[compare_axis])
    #Current_distance = wheel_distance
    #while wheel_distance - current_distance < 40 * tiles:
    
        update_path(robot_pos, shared_pos)
        if ir_values[IR_ID[FORWARD]] < 5:  # Wall detected
            st.set_speed(AUTO_MODE, 0)
            print('STOP')
            break
        
        pid_side = detect_walls(ir_values)
        
        if enable_pid and pid_side != None:
            # We have detected a wall for the PID to follow
            if pid_side == LEFT:
                pid.reversed = True
            elif pid_side == RIGHT:
                pid.reversed = False
            
            pid.enabled = True
            turn_factor = pid.compute(ir_values)
            
            if st.speeds[st.LEFT] != abs(int(st.speeds[st.DEFAULT] - turn_factor)):
                st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] - turn_factor), "left")
            if st.speeds[st.RIGHT] != abs(int(st.speeds[st.DEFAULT] + turn_factor)):
                st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] + turn_factor), "right")
        elif st.speeds[st.LEFT] != st.speeds[st.DEFAULT] or st.speeds[st.RIGHT] != st.speeds[st.DEFAULT]:
            # PID not enabled, go straight ahead
            st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
        
        get_distance()
        
    """
    # Attempt at corner position fix
    if tiles < 1:
        if robot_dir == NORTH:
            robot_pos = [prev_pos[0], prev_pos[1] - 0.5]
        elif robot_dir == EAST:
            robot_pos = [prev_pos[0] + 0.5, prev_pos[1]]
        elif robot_dir == SOUTH:
            robot_pos = [prev_pos[0], prev_pos[1] + 0.5]
        elif robot_dir == WEST:
            robot_pos = [prev_pos[0] - 0.5, prev_pos[1]]
    """
    
    print('Position after go %s' % str(robot_pos))
        
    st.set_speed(AUTO_MODE, 0)
 
    
    
def turn(turn_deg, side, ir_values):
    print('BUFFER', st.steering_port.inWaiting())
    global robot_dir, robot_pos, state, verified_grids, need_new_time, wheel_distance, x_gain, y_gain

    if side == 'left' or side == LEFT:
        st.left()
        robot_dir = (robot_dir - (turn_deg//90)) % 4
    elif side == 'right' or side == RIGHT:
        st.right()
        robot_dir = (robot_dir + (turn_deg//90)) % 4
    else:
        return
    
    st.set_speed(AUTO_MODE, 170)
    start_angle = gyro_value.value
    while abs(gyro_value.value - start_angle) < turn_deg-15:
        pass

        
    st.set_speed(AUTO_MODE, 0)
    st.forward()
    st.steering_port.flushInput()
    time.sleep(0.1)
    
    need_new_time = True
    verified_grids = 0
    wheel_distance = 0

    irs = []
    with ir_values.get_lock():
        irs = [ir_values[i] for i in range(len(ir_values))]
    """
    print(irs)

    if((15 > irs[4] > 5 and 15 > irs[5] > 5) or (15 > irs[2] > 5 and 15 > irs[3] > 5)):
    """
    int_x = int(robot_pos[0])
    int_y = int(robot_pos[1])

    robot_pos[0] = int_x + 0.5
    robot_pos[1] = int_y + 0.5
    

    print('DISTANCE: %f %f' % (x_gain, y_gain))
    x_gain = 0
    y_gain = 0
    
    #go_tiles(1)
    if travel_commands:
        state = TRAVEL
    else:
        state = WALL

def get_distance(turning=None):
    # Get driven distance. Reset after each turn
    global robot_pos, robot_dir, wheel_distance, left_count, right_count, x_gain, y_gain, test_pos
    wheel_steps = st.steering_port.inWaiting()
    if wheel_steps >= 1:
        for step in range(wheel_steps):
            rec = ord(st.steering_port.read(1))
            if rec == WHEEL_ID: 
                wheel_distance += 4
                robot_pos = update_robot_pos(robot_pos, robot_dir, 0.1)
                left_count += 1
                
                #  print('NEW POS: %s %i' % (str(robot_pos), wheel_distance))
            else:
                right_count +=1

    if left_count >= 1 and right_count >= 1:
        gain = update_wheel_position(left_count*4, right_count*4)
        x_gain += (gain[0] + gain[2]) / 2
        y_gain += (gain[1] + gain[3]) / 2
        t_x = (gain[0] + gain[2]) / 2
        t_y = (gain[1] + gain[3]) / 2
        tile_gain_x = (t_x / 40)
        tile_gain_y = (t_y / 40)
        left_count = 0
        right_count = 0
        if robot_dir == NORTH:
            test_pos[0] += tile_gain_x
            test_pos[1] -= tile_gain_y
        elif robot_dir == EAST:
            test_pos[0] += tile_gain_y
            test_pos[1] += tile_gain_x
        elif robot_dir == SOUTH:
            test_pos[0] -= tile_gain_x
            test_pos[1] += tile_gain_y
        elif robot_dir == WEST:
            test_pos[0] -= tile_gain_y
            test_pos[1] -= tile_gain_x
        #print('POS: %s %s' % (test_pos, robot_pos))

def check_centered():
    global robot_pos, robot_dir
    is_horizontal = robot_dir % 2
    position = int_robot_pos(robot_pos)

    centered_vertical = not is_horizontal and (position[1] + 0.4) <= robot_pos[1] <= (position[1] + 0.6)
    centered_horizontal = is_horizontal and (position[0] + 0.4) <= robot_pos[0] <= (position[0] + 0.6)

    return centered_vertical or centered_horizontal
                
def update_path(prev, shared_pos):
    global robot_pos, driven_path
    temp_path = copy_list(robot_pos)
    temp_path = [int(temp_path[0]), int(temp_path[1])]  # pos, x pos y, counter
    if not driven_path or temp_path != driven_path[-1]:
        driven_path.append(temp_path)
        shared_pos[0] = temp_path[0]
        shared_pos[1] = temp_path[1]
        

def check_pos_change(prev_pos):
    global robot_pos
    return robot_pos != prev_pos


def slam(ir_values, laser_values, mode, steering_cmd_man, pid_cons, gyro_value, num_laser_values, num_hall_reads, grid, shared_pos):
    global pid, state, robot_pos, robot_dir, travel_commands, need_new_time, verified_grids, wheel_distance, driven_path
    st.open_port()
    st.steering_port.flushInput()
    st.forward()
    
    pid_side = RIGHT
    start_driving_time = 0
    current_grid_walls = [[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]]
    verified_pos = []
    driven_path = []

    control.forward_sensor = IR_ID[FORWARD_RIGHT]
    control.backward_sensor = IR_ID[BACKWARD_RIGHT]

    adjusted_laser = []
    last_laser_list = []

    tile_wall_count = {}

    search_mode = LASER
    stop_tower(num_hall_reads)
    mapping_time = time.time()
    start_pos = [pos for pos in robot_pos]
    laser_counter = 0
    num_reads = 0

    #mapper = doramapper.Mapping()
    #generated = False

    mapper = sm.Mapping()
    
    
    while True:
        get_distance()
        update_path(robot_pos, shared_pos)
                    
                
        
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
        """
        if int(robot_pos[0]) == int(start_pos[0]) and int(robot_pos[1]) == int(start_pos[1]) and wheel_distance > 30:
            st.set_speed(AUTO_MODE, 0)
            state = MANUAL
            continue
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
            
            #go_tilesgo_tiles(1)
            #driven_grids += 1
            # Enter WALL to exit the starting cell
            state = WALL
                
        elif state == WALL:
            #print("WALL")

            if check_centered():
                map_ir_neighbors(grid, robot_pos, robot_dir, ir_values, tile_wall_count)


            if search_mode == LASER and not [ir_values[i] for i in range(NUM_SENSORS) if ir_values[i] != EMPTY_CHECK]:  # TODO: Lock ir_values?
                # All ir values == 25 (no walls detected), should switch to slam?
                state = SLAM
                st.set_speed(AUTO_MODE, 0)
                st.set_speed(AUTO_MODE, 50, 'tower')
                continue

            # Wall ahead
            if ir_values[IR_ID[FORWARD]] <= FORWARD_CHECK:
                #print("Wall forwards detected")
                if ir_values[IR_ID[FORWARD_RIGHT]] <= RIGHT_CHECK and ir_values[IR_ID[FORWARD_LEFT]] <= LEFT_CHECK:
                    print("Wall sides detected, turning back")
                    # Dead end, start driving backwards
                    state = DEAD_END
                elif ir_values[IR_ID[FORWARD_RIGHT]] <= RIGHT_CHECK:
                    print("Wall right  detected, turning left")
                    # wall to the right, turn left
                    state = TURN_LEFT
                                            
                elif ir_values[IR_ID[FORWARD_LEFT]] <= LEFT_CHECK:
                    # wall to the left, turn right
                    print("Wall left detected, turning right")
                    state = TURN_RIGHT
                continue

            if ir_values[IR_ID[FORWARD_LEFT]] == EMPTY_CHECK and ir_values[IR_ID[BACKWARD_LEFT]] <= LEFT_CHECK:
                #print(ir_values[4], ir_values[5])
                # We have detected an opening in the wall, turning left around corner
                print('TURN LEFT AROUND CORNER')
                #print([ir_values[i] for i in range(NUM_SENSORS)])
                st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
                go_tiles(1, ir_values, shared_pos)
                if search_mode == LASER:
                    continue
                turn(90,'left', ir_values)
                reset_neighbors(robot_pos, tile_wall_count)
                map_ir_neighbors(grid, robot_pos, robot_dir, ir_values, tile_wall_count)
                go_tiles(1, ir_values, shared_pos)
                continue

            if ir_values[IR_ID[FORWARD_RIGHT]] == EMPTY_CHECK and ir_values[IR_ID[BACKWARD_RIGHT]] <= RIGHT_CHECK:
                # Wall ending on the right side
                if ir_values[IR_ID[FORWARD_LEFT]] <= LEFT_CHECK and ir_values[IR_ID[BACKWARD_LEFT]] <= LEFT_CHECK:
                    # Wall continues on the left side: Follow it
                    pid_side = LEFT
                    continue
                print('TURN RIGHT AROUND CORNER')
                st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
                go_tiles(1, ir_values, shared_pos)
                if search_mode == LASER:
                    continue
                turn(90,'right', ir_values)
                reset_neighbors(robot_pos, tile_wall_count)
                map_ir_neighbors(grid, robot_pos, robot_dir, ir_values, tile_wall_count)
                go_tiles(1, ir_values, shared_pos)
                continue


            pid_side = detect_walls(ir_values)

            if pid_side == LEFT:
                pid.reversed = True
            elif pid_side == RIGHT:
                pid.reversed = False

            pid.enabled = True
            turn_factor = pid.compute(ir_values)

            if st.speeds[st.LEFT] != abs(int(st.speeds[st.DEFAULT] - turn_factor)):
                st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] - turn_factor), "left")
            if st.speeds[st.RIGHT] != abs(int(st.speeds[st.DEFAULT] + turn_factor)):
                st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] + turn_factor), "right")

        elif state == TRAVEL:
            print("TRAVEL")
            if not travel_commands:
                p = path.find_closest_unexplored(grid, robot_pos)
                travel_commands = path.follow_path(p, robot_dir)
            
            if travel_commands:
                c = travel_commands.pop(0)
                parts = c.split('_')
                if parts[0] == "go":
                    tiles = int(parts[2])
                    go_tiles(tiles, ir_values, shared_pos)
                    print("Travelling 2 tiles")
                elif parts[0] == "turn":
                    turn_deg = int(parts[2])
                    print("Turning " + str(turn_deg))
                    turn(turn_deg, parts[1], ir_values)
            else:
                
                state = WALL
            
        elif state == TURN_LEFT:
            print('TURN LEFT')
            turn(90, 'left', ir_values)
            reset_neighbors(robot_pos, tile_wall_count)
            state = WALL
            need_new_time = True
            
        elif state == TURN_RIGHT:
            print('TURN_RIGHT')
            turn(90, 'right', ir_values)
            reset_neighbors(robot_pos, tile_wall_count)
            state = WALL
            need_new_time = True
            
        elif state == DEAD_END:
            turn(180, 'left', ir_values)
            reset_neighbors(robot_pos, tile_Wall_count)
            state = WALL
            need_new_time = True

        elif state == SLAM:
            pid.enabled = False
            """
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
                        if value > 2:
                            newvalue = 2
                            print('value', newvalue)
                            set_grid_value(j, i, newvalue, grid)
            """
            if num_laser_values.value > 0 and laser_counter < mapper.maxiter:
                laser_list = []
                with laser_values.get_lock():
                    #print('laser values', num_laser_values.value)
                    if num_laser_values.value > 520:
                        with num_laser_values.get_lock():
                            num_laser_values.value = 0
                        continue
                    laser_list = [laser_values[i] for i in range(num_laser_values.value)]
                if laser_list:
                    print('here')
                    laser_counter += 1
                    #print('before')
                    generated_map = slammer.mapper(laser_list)
                    print('here end')
                    #print(laser_list)
                    for i in range(len(generated_map[0])):
                        print(generated_map[0][i])

                    print('-------------------')
                    if laser_counter >= mapper.maxiter:
                        mapper.remove_bad_values()
                    
                    mapper.add_submap(generated_map[0], generated_map[1], (int(robot_pos[0]), int(robot_pos[1])))
                    mapper.generate_map()

                    
                    
                    #print('after')
                    #slam_tobefixed2.test_print(generated_map)
                    #print(generated_map)

                    for i in range(31):
                        for j in range(31):
                            newvalue = 0
                            
                            value = mapper.finalmap[i][j]
                            if value >= 1.5:
                                newvalue = 2
                                #print('value', newvalue)
                            #if(laser_counter >= mapper.maxiter / 2):    
                            if laser_counter >= mapper.maxiter / 2:
                                set_grid_value(j, i, newvalue, grid)
            elif laser_counter >= mapper.maxiter:
                #go_tiles(2, ir_values, shared_pos)
                laser_counter = 0
                #num_reads = 1
                
                    
                
            #state = WALL
                    
        elif state == MANUAL:
            print("MANUAL")
            #travel_path = reverse(drive_path)
            #travel_path = [node for node in driven_path.reverse()]
            if mode.value == 1:
                need_new_time = True
                verified_grids = 0
                state = START
                continue

            pid.enabled = False
            st.steering_serial(steering_cmd_man, mode, ir_values)
            #state = TRAVEL
            st.forward()
            print('Exiting manual mode')


if __name__ == "__main__":  
    ir_values = Array('i', 6)
    laser_values = Array('i', 520)
    num_laser_values = Value('i', 0)
    num_hall_reads = Value('i', 0)
    gyro_value = Value('d', 0)
    mode = Value('i', 0)  # auto = 1
    pid_cons = Array('d', 2)
    pid_cons[0] = -1  # make sure to not read pid values from array on boot
    grid = Array('i', MAP_SIZE**2)
    shared_pos = Array('i',2)
    steering_cmd_man = SimpleQueue()
    
    sensor_process = Process(target=sensor.sensor_serial, args=(ir_values, laser_values, gyro_value, num_laser_values, num_hall_reads))
    slam_process = Process(target=slam, args=(ir_values, laser_values, mode, steering_cmd_man, pid_cons, gyro_value, num_laser_values, num_hall_reads, grid, shared_pos))
    bluetooth_process = Process(target=blueztooth.bluetooth_loop, args=(ir_values, laser_values, steering_cmd_man, mode, pid_cons, num_laser_values, grid, shared_pos))

    sensor_process.start()
    slam_process.start()
    bluetooth_process.start()

    prev_laser = []

    sensor_process.join()
    slam_process.join()
    bluetooth_process.join()
