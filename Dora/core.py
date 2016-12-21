# -*- coding: utf-8 -*-

#####
#
# main.py
# Updated: 20/12 2016
# Authors: Fredrik Iselius, Niklas Nilsson, Johan Nilsson, Jacob Lundberg, Martin Lundberg, Jonathan Johansson 
#
#####

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
from path import *
from position import *
import slam_merger as sm
import slam_submapper as slammer 
from multiprocessing import Process, Value, Array
from multiprocessing.queues import SimpleQueue


#if python version not 3
if sys.version < '3':
    input  = raw_input


# GLOBAL VARS
robot_pos = [15.5, 15.5]
robot_dir = NORTH

update_ir_map = False
first_laser_read = False
ir_enabled = True

current_tile_pos = [0, 0]
verified_grids = 0
ir_grid = [[UNKNOWN_TILE for j in range(MAP_SIZE)] for i in range(MAP_SIZE)]  # Generate empty ir grid

travel_commands = []
tile_wall_count = {}

state = MANUAL

wheel_distance = 0

left_count = 0
right_count = 0

x_gain = 0
y_gain = 0
test_pos = [15.5, 15.5]

# Init pid regulator for keeping a distance from walls
pid = control.PID(10, 10, 0, 5)
pid.set_output_limits(-st.speeds[st.DEFAULT], st.speeds[st.DEFAULT])


def adjust_to_walls(ir_values):
    wall_side = detect_walls(ir_values)
    if wall_side == LEFT:
        while ir_values[IR_ID[FORWARD_LEFT]] - ir_values[IR_ID[BACKWARD_LEFT]] > 0:
            st.left()
            st.set_speed(AUTO_MODE, 80)
            time.sleep(0.03)
            st.set_speed(AUTO_MODE, 0)
            while has_new_ir.value == 0:
                time.sleep(0.01)
            has_new_ir.value = 0
            
        st.set_speed(AUTO_MODE, 0)
        while ir_values[IR_ID[FORWARD_LEFT]] - ir_values[IR_ID[BACKWARD_LEFT]] < 0:
            st.right()
            st.set_speed(AUTO_MODE, 80)
            time.sleep(0.03)
            st.set_speed(AUTO_MODE, 0)
            while has_new_ir.value == 0:
                time.sleep(0.01)
            has_new_ir.value = 0

        st.set_speed(AUTO_MODE, 0)
        st.forward()
        
    elif wall_side == RIGHT:
        while ir_values[IR_ID[FORWARD_RIGHT]] - ir_values[IR_ID[BACKWARD_RIGHT]] > 0:
            st.right()
            st.set_speed(AUTO_MODE, 80)
            time.sleep(0.03)
            st.set_speed(AUTO_MODE, 0)
            while has_new_ir.value == 0:
                time.sleep(0.01)
            has_new_ir.value = 0

        st.set_speed(AUTO_MODE, 0)
        while ir_values[IR_ID[FORWARD_RIGHT]] - ir_values[IR_ID[BACKWARD_RIGHT]] < 0:
            st.left()
            st.set_speed(AUTO_MODE, 80)
            time.sleep(0.03)
            st.set_speed(AUTO_MODE, 0)
            while has_new_ir.value == 0:
                time.sleep(0.01)
            has_new_ir.value = 0

        st.set_speed(AUTO_MODE, 0)
        st.forward()
        time.sleep(0.1)


def stop_tower(num_hall_reads):
    """
    Stops the rotating tower when it points backwards
    """
    
    st.set_speed(AUTO_MODE, 0)
    st.set_speed(AUTO_MODE, 25, "tower")

    while num_hall_reads.value < 1:
        pass

    while num_hall_reads.value > 0:
        pass
    while num_hall_reads.value < 1:
        pass

    print('TOWER STOPPED')
    st.set_speed(AUTO_MODE, 0, "tower")

def go_tiles_simple(tiles):
    """
    Drives the robot n tiles forward
    """
    global wheel_distance
    st.forward()
    st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
    start_dist = wheel_distance
    
    while wheel_distance - start_dist < 40 * tiles:
        get_distance()

    st.set_speed(AUTO_MODE, 0)
    

def go_tiles(tiles, ir_values, shared_pos, ir_grid, enable_pid=True):
    """
    Drives the robot n tiles forward.
    It uses two pid regulators. One for controlling the speed
    when there are no walls around and one for keeping a distance from walls.
    """
    global robot_pos, robot_dir, wheel_distance, test_pos, tile_wall_count, update_ir_map, first_laser_read, ir_enabled
    prev_pos = int_robot_pos(robot_pos)
    st.set_speed(AUTO_MODE, 0)
    st.forward()

    adjust_to_walls(ir_values)

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
        dest = math.ceil(robot_pos[compare_axis]) + (sign * 0.5)
    elif sign == -1:
        dest = int(round(robot_pos[compare_axis],1)) + (sign * 0.5)

    
    to_drive = abs(round(dest - start, 1)) + (tiles - 1)  # Distance to drive in tiles
    wheel_distance = 0
    speed_pid = control.PID(to_drive * 40, 0.6, 0, 0)
    speed_pid.set_output_limits(st.speeds[st.DEFAULT], 125)
    print('Attempting to move %f from pos %s %f' % (to_drive, str(robot_pos), dest))

    pid_side = None
    current_ir_values = [25 for i in range(6)]
    prev_ir_values = [25 for i in range(6)]

    # Clear distance inputs and set default speed
    st.steering_port.flushInput()
    st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
    
    # Move until correct number of tiles are traversed
    while wheel_distance < to_drive * 40:
        get_distance()
        # Update map when centered
        if has_new_ir.value == 1:
            with ir_values.get_lock():
                current_ir_values = [ir for ir in ir_values]
            with has_new_ir.get_lock():
                has_new_ir.value = 0
        else:
            continue
        
        if check_centered() and ir_enabled:
            map_ir_neighbors(ir_grid, robot_pos, robot_dir, current_ir_values, tile_wall_count, has_new_ir)
            update_ir_map = True
            update_final_ir(grid, ir_grid)
        update_path(robot_pos, shared_pos)
        
        # Break if the robot is about to drive into a wall
        if current_ir_values[IR_ID[FORWARD]] < 8:
            st.set_speed(AUTO_MODE, 0)
            _x, _y = GRID_INDEX_VALUES[robot_dir][0]
            set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, WALL_TILE, ir_grid)
            tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,100,0]

            st.backward()
            while has_new_ir.value == 0:
                time.sleep(0.1)
            # Back
            while ir_values[IR_ID[FORWARD]] < 5:
                st.set_speed(AUTO_MODE, 60)
                time.sleep(0.03)
                st.set_speed(AUTO_MODE, 0)
                while has_new_ir.value == 0:
                    time.sleep(0.01)
                has_new_ir.value = 0
                
            st.set_speed(AUTO_MODE, 0)
            st.steering_port.flushInput()
            st.forward()
            break

        # Enable pid if the robot is driving close to a wall
        pid_side = detect_walls(current_ir_values, pid_side)
        
        if enable_pid and pid_side != None:
            #st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
            if pid_side == LEFT:
                pid.reversed = True
                if abs(current_ir_values[IR_ID[FORWARD_LEFT]] - prev_ir_values[IR_ID[FORWARD_LEFT]]) > 4:
                    prev_ir_values = [ir for ir in current_ir_values]
                    continue
            elif pid_side == RIGHT:
                pid.reversed = False
                if abs(current_ir_values[IR_ID[FORWARD_RIGHT]] - prev_ir_values[IR_ID[FORWARD_RIGHT]]) > 4:
                    prev_ir_values = [ir for ir in current_ir_values]
                    continue

                
            pid.enabled = True
            turn_factor = pid.compute(current_ir_values)
            
            if st.speeds[st.LEFT] != abs(int(st.speeds[st.DEFAULT] - turn_factor)):
                st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] - turn_factor), "left")
            if st.speeds[st.RIGHT] != abs(int(st.speeds[st.DEFAULT] + turn_factor)):
                st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] + turn_factor), "right")

        # No walls nearby. Use pid to determine forward speed
        else:
            pid.enabled = False
            speed = speed_pid.compute(float(wheel_distance))
            st.set_speed(AUTO_MODE, speed)

        # Update driven distance
        get_distance()
        prev_ir_values = [ir for ir in current_ir_values]

    pid.enabled = False
    
    if ir_values[IR_ID[FORWARD]] < EMPTY_CHECK and ir_values[IR_ID[FORWARD]] > 12:
        st.set_speed(AUTO_MODE, 80)
        _x, _y = GRID_INDEX_VALUES[robot_dir][0]
        set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, WALL_TILE, ir_grid)
        tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,100,0]
        while ir_values[IR_ID[FORWARD]] > 12:
            pass

    # The robot has reached its target, set speed to 0
    st.set_speed(AUTO_MODE, 0)
 
    
    
def turn(turn_deg, side, ir_values):
    global robot_dir, robot_pos, state, verified_grids, wheel_distance, x_gain, y_gain, ir_grid, ir_enabled
    st.set_speed(AUTO_MODE, 0)

    adjust_to_walls(ir_values)

    if ir_enabled:
        for i in range(4):
            while has_new_ir.value == 0:
                pass
            map_ir_neighbors(ir_grid, robot_pos, robot_dir, ir_values, tile_wall_count, has_new_ir)
    
    # Set turn direction
    if side == 'left' or side == LEFT:
        st.left()
        robot_dir = (robot_dir - (turn_deg//90)) % 4
    elif side == 'right' or side == RIGHT:
        st.right()
        robot_dir = (robot_dir + (turn_deg//90)) % 4
    else:
        return

    # Init turn regulator
    turn_pid = control.PID(turn_deg, 0.6, 0, 0)
    turn_pid.set_output_limits(70, 180)
    start_angle = gyro_value.value

    # Keep turning until the robot has reached 'turn_deg' angle
    while abs(gyro_value.value - start_angle) < turn_deg:
        turn_speed = turn_pid.compute(float(abs(gyro_value.value - start_angle)))
        st.set_speed(AUTO_MODE, turn_speed)

    # Break reset speed and driving direction
    st.set_speed(AUTO_MODE, 0)
    st.forward()
    st.steering_port.flushInput()
    time.sleep(0.1)
    wheel_distance = 0
   
    if travel_commands:
        state = TRAVEL
    else:
        state = WALL

def get_distance(turning=None):
    """
    Get distance updates from uart and update driven distance.
    """
    global robot_pos, robot_dir, wheel_distance, left_count, right_count, x_gain, y_gain, test_pos
    wheel_steps = st.steering_port.inWaiting()
    if wheel_steps >= 1:
        for step in range(wheel_steps):
            rec = ord(st.steering_port.read(1))
            if rec == 96:
                # The robot has driven 4 cm
                wheel_distance += 4
                robot_pos = update_robot_pos(robot_pos, robot_dir, 0.1)
                left_count += 1
            else:
                pass


def check_centered():
    """
    Check if the robot is somewhat centered inside the current tile
    """
    global robot_pos, robot_dir
    is_horizontal = robot_dir % 2
    position = int_robot_pos(robot_pos)

    centered_vertical = not is_horizontal and (position[1] + 0.5) <= robot_pos[1] <= (position[1] + 0.8)
    centered_horizontal = is_horizontal and (position[0] + 0.5) <= robot_pos[0] <= (position[0] + 0.8)

    return centered_vertical or centered_horizontal


def update_path(prev, shared_pos):
    """
    Update the driven path
    """
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

def update_final_ir(grid, ir_grid):
    global robot_pos, first_laser_read, update_ir_map
    
    if first_laser_read and update_ir_map:
        
        current_map = [[0 for x in range(MAP_SIZE)] for y in range(MAP_SIZE)]
        
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                current_map[y][x] = get_grid_value(x,y,grid)
                    
        subp = sm.slice_submap(ir_grid, (int(robot_pos[0]), int(robot_pos[1])))

        r_map = sm.returnFinal(current_map, subp[0], subp[1], (int(robot_pos[0]), int(robot_pos[1])))

        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                set_grid_value(x,y, r_map[y][x], grid)
        update_ir_map = False
    



def slam(ir_values, laser_values, mode, steering_cmd_man, pid_cons, gyro_value, num_laser_values, num_hall_reads, grid, shared_pos, move_cmd, has_new_ir):
    """
    Main loop for driving the robot.
    """
    global pid, state, robot_pos, robot_dir, travel_commands, verified_grids, wheel_distance, driven_path, tile_wall_count, update_ir_map, first_laser_read, ir_grid, ir_enabled

    # Open and clear the uart port to the steering module
    st.open_port()
    st.steering_port.flushInput()
    st.set_speed(AUTO_MODE, 0)
    st.forward()

    # PID vars
    pid_side = RIGHT
    control.forward_sensor = IR_ID[FORWARD_RIGHT]
    control.backward_sensor = IR_ID[BACKWARD_RIGHT]
    full_turn_start = time.time()

    # Laser vars
    adjusted_laser = []
    last_laser_list = []

    # Position vars
    start_pos = [pos for pos in robot_pos]
    driven_path = []
    prev_state = MANUAL

    # SLAM vars
    laser_counter = 0
    mapper = sm.Mapping()

    # Other
    search_mode = LASER
    debug_print = True
    

    laser_floor = [[0 for x in range(31)] for y in range(31)]
    
    
    while True:
        get_distance()
        update_path(robot_pos, shared_pos)

        #Updates final map with ir values
        update_final_ir(grid, ir_grid)

        
        if not mode.value:
            state = MANUAL
        
        if state != prev_state and debug_print:
            print('---------------')
            print('CURRENT STATE: ' + STATES[state])
            print('CURRENT DIRECTION: ' + DIRECTIONS[robot_dir])
            print('CURRENT POSITION: ' + str(robot_pos))
            print('PID SIDE: ' + str(pid_side))
            

        # Update pid values from the laptop program
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

        # Initial state. Should not enter here again        
        if state == START:
            prev_state = START

            # Assign values to surrounding tiles from START position
            set_grid_value_2d(15, 14, EMPTY_TILE, ir_grid)
            set_grid_value_2d(15, 15, EMPTY_TILE, ir_grid)
            set_grid_value_2d(15, 16, WALL_TILE, ir_grid)
            set_grid_value_2d(14, 15, WALL_TILE, ir_grid)
            set_grid_value_2d(16, 15, WALL_TILE, ir_grid)
            # Enter WALL to exit the starting cell
            state = WALL
            continue

        # Main state when following walls
        elif state == WALL:
            prev_state = WALL

            # If the room is closed, go home
            if path.closed_room(grid, robot_pos):
                state = TRAVEL
                ir_enabled = False
                continue
            
            # Update map
            if has_new_ir.value == 1 and check_centered() and ir_enabled:
                update_ir_map = True
                map_ir_neighbors(ir_grid, robot_pos, robot_dir, ir_values, tile_wall_count, has_new_ir)
            # Enters SLAM state if there arent any walls around
            if search_mode == LASER and not [ir_values[i] for i in range(NUM_SENSORS) if ir_values[i] != EMPTY_CHECK and i != 1]:
                state = SLAM
                # Break and start the laser tower
                st.set_speed(AUTO_MODE, 0, 'both')
                continue

            # Check for a wall in front of the robot
            if ir_values[IR_ID[FORWARD]] <= FORWARD_CHECK:
                #set front as wall
                _x, _y = GRID_INDEX_VALUES[robot_dir][0]
                set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, WALL_TILE, ir_grid)
                tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,100,0]
                # Switch to dead end state if there are walls on both sides of the robot
                if ir_values[IR_ID[FORWARD_RIGHT]] < EMPTY_CHECK and ir_values[IR_ID[FORWARD_LEFT]] < EMPTY_CHECK:
                    state = DEAD_END

                # Switch to turn left state if there is a wall on the right
                elif ir_values[IR_ID[FORWARD_RIGHT]] < EMPTY_CHECK:
                    state = TURN_LEFT

                # Switch to turn right state if there is a wall on the left
                elif ir_values[IR_ID[FORWARD_LEFT]] < EMPTY_CHECK:
                    state = TURN_RIGHT

                # Find closest unexplored if there are no walls on the sides
                else:
                    #map_ir_neighbors(ir_grid, robot_pos, robot_dir, ir_values, tile_wall_count)
                    _x, _y = GRID_INDEX_VALUES[robot_dir][2]
                    set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, EMPTY_TILE, ir_grid)
                    tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,0,100]
                    _x, _y = GRID_INDEX_VALUES[robot_dir][3]
                    set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, EMPTY_TILE, ir_grid)
                    tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,0,100]
                    update_ir_map = True
                    state = TRAVEL
                continue

            # Check if the wall ends on the left side
            if ir_values[IR_ID[FORWARD_LEFT]] == EMPTY_CHECK and ir_values[IR_ID[BACKWARD_LEFT]] < EMPTY_CHECK:
                num_closed_walls = 0  # Number of closed walls in turn
                st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
                # Drive out past walls and stop
                while ir_values[IR_ID[BACKWARD_LEFT]] != EMPTY_CHECK:
                    get_distance()

                # Check forward distance
                if ir_values[IR_ID[FORWARD]] < EMPTY_CHECK and ir_values[IR_ID[FORWARD]] > 12:
                    _x, _y = GRID_INDEX_VALUES[robot_dir][0]
                    set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, WALL_TILE, ir_grid)
                    tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,100,0]
                    print('FRONT WALL DETECTED')
                    num_closed_walls += 1
                    while ir_values[IR_ID[FORWARD]] > 12:
                        pass
                else:
                    go_tiles_simple(0.3)

                st.set_speed(AUTO_MODE, 0)
                    
                if ir_values[IR_ID[FORWARD_RIGHT]] < EMPTY_CHECK and ir_values[IR_ID[BACKWARD_RIGHT]] < EMPTY_CHECK:
                    print('RIGHT WALL DETECTED')
                    num_closed_walls += 1

                st.set_speed(AUTO_MODE, 0)

                # Update the map
                #for i in range(100):
                print('Waiting for new ir')
                if ir_enabled:
                    while has_new_ir.value == 0:
                        pass
                        map_ir_neighbors(ir_grid, robot_pos, robot_dir, ir_values, tile_wall_count, has_new_ir)
                        update_ir_map = True
                    
                # Stay here if the robot is using the laser
                if search_mode == LASER and num_closed_walls < 2: 
                    print('LASER SEARCH ACTIVE, SKIPPING REST AND ENTER SLAM')
                    state = SLAM
                    continue

                # Wall continues on the right side: Follow it
                else:
                    print('WALL CONTINUES ON THE RIGHT SIDE, FOLLOW IT')
                    pid_side = RIGHT
                    continue
                """
                # Wall continues on the right side: Follow it
                if ir_values[IR_ID[FORWARD_RIGHT]] <= RIGHT_CHECK and ir_values[IR_ID[BACKWARD_RIGHT]] <= RIGHT_CHECK:
                    print('WALL CONTINUES ON THE RIGHT SIDE, FOLLOW IT')
                    pid_side = RIGHT
                    continue
                
                # The robot is either standing in a t-turn or a four-turn
                else:
                    print('T OR 4 TURN')
                    state = TRAVEL
                    continue
                """
                continue

            # Check if the wall ends on the right side
            if ir_values[IR_ID[FORWARD_RIGHT]] == EMPTY_CHECK and ir_values[IR_ID[BACKWARD_RIGHT]] < EMPTY_CHECK:
                num_closed_walls = 0  # Number of closed walls in turn
                st.set_speed(AUTO_MODE, st.speeds[st.DEFAULT])
                # Drive out past walls and stop
                while ir_values[IR_ID[BACKWARD_RIGHT]] != EMPTY_CHECK:
                    get_distance()

                # Check forward distance
                if ir_values[IR_ID[FORWARD]] < EMPTY_CHECK and ir_values[IR_ID[FORWARD]] > 12:
                    _x, _y = GRID_INDEX_VALUES[robot_dir][0]
                    set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, WALL_TILE, ir_grid)
                    tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,100,0]
                    num_closed_walls += 1
                    while ir_values[IR_ID[FORWARD]] > 12:
                        pass
                else:
                    go_tiles_simple(0.3) 

                st.set_speed(AUTO_MODE, 0)

                if ir_values[IR_ID[FORWARD_LEFT]] < EMPTY_CHECK and ir_values[IR_ID[BACKWARD_LEFT]] < EMPTY_CHECK:
                    print('LEFT WALL DETECTED')
                    num_closed_walls += 1

                # Update the map
                if ir_enabled:
                    while has_new_ir.value == 0:
                        pass
                        map_ir_neighbors(ir_grid, robot_pos, robot_dir, ir_values, tile_wall_count, has_new_ir)
                        update_ir_map = True
                # Stay here if the robot is using the laser
                if search_mode == LASER and num_closed_walls < 2:
                    print('LASER SEARCH ACTIVE, SKIPPING REST AND ENTER SLAM')
                    state = SLAM
                    continue
                
                # Wall continues on the left side: Follow it
                else:
                    print('WALL CONTINUES ON THE LEFT SIDE, FOLLOW IT')
                    pid_side = LEFT
                    continue
                """
                
                if ir_values[IR_ID[FORWARD_LEFT]] <= LEFT_CHECK and ir_values[IR_ID[BACKWARD_LEFT]] <= LEFT_CHECK:
                    print('WALL CONTINUES ON THE LEFT SIDE, FOLLOW IT')
                    pid_side = LEFT
                    continue

                
                # The robot is either standing in a t-turn or a four-turn
                else:
                    print('T OR 4 TURN')
                    state = TRAVEL
                    continue
                """
                continue


            # Use pid to follow the wall
            pid_side = detect_walls(ir_values)
            if pid_side == LEFT:
                pid.reversed = True
            elif pid_side == RIGHT:
                pid.reversed = False

            if pid_side != None:
                pid.enabled = True
                turn_factor = pid.compute(ir_values)

                if st.speeds[st.LEFT] != abs(int(st.speeds[st.DEFAULT] - turn_factor)):
                    st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] - turn_factor), "left")
                if st.speeds[st.RIGHT] != abs(int(st.speeds[st.DEFAULT] + turn_factor)):
                    st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT] + turn_factor), "right")
            else:
                pid.enabled = False
                if st.speeds[st.LEFT] != abs(int(st.speeds[st.DEFAULT])):
                    st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT]), "left")
                if st.speeds[st.RIGHT] != abs(int(st.speeds[st.DEFAULT])):
                    st.set_speed(AUTO_MODE, abs(st.speeds[st.DEFAULT]), "right")

            continue

        elif state == TRAVEL:
            prev_state = TRAVEL
            
            # Generate robot commands which, when executed,
            # will drive the robot to the nearest unexplored tile
            if not travel_commands:
                if path.closed_room(grid, robot_pos):
                    p = path.a_star(grid, robot_pos, [15, 15])
                    ir_enabled = False
                else:
                    p = path.find_closest_unexplored(grid, robot_pos)
                travel_commands = path.follow_path(p, robot_dir)
                print('GENERATED COMMANDS: ' + str(travel_commands))

            # Excute travel commands
            if travel_commands:
                c = travel_commands.pop(0)
                move_cmd.value = c
                
                parts = c.split('_')
                if parts[0] == "go":
                    tiles = int(parts[2])
                    go_tiles(tiles, ir_values, shared_pos, ir_grid)
                elif parts[0] == "turn":
                    turn_deg = int(parts[2])
                    turn(turn_deg, parts[1], ir_values)
                time.sleep(0.2)

                # Check if home
                print('CHECKING IF HOME', str(robot_pos))
                if not travel_commands and int_robot_pos(robot_pos) == int_robot_pos(start_pos):
                    st.set_speed(AUTO_MODE, 0)
                    mode.value = 0
                    state = MANUAL
                    continue

                elif not travel_commands:
                    if ir_values[IR_ID[FORWARD_LEFT]] < EMPTY_CHECK and ir_values[IR_ID[FORWARD_RIGHT]] < EMPTY_CHECK:
                        state = WALL
                    elif (ir_values[IR_ID[FORWARD_LEFT]] < EMPTY_CHECK and ir_values[IR_ID[FORWARD]] < EMPTY_CHECK) or \
                       (ir_values[IR_ID[FORWARD_RIGHT]] < EMPTY_CHECK and ir_values[IR_ID[FORWARD]] < EMPTY_CHECK):
                        for i in range(4):
                            while has_new_ir.value == 0:
                                pass
                            current_ir_values = [ir for ir in ir_values]
                            map_ir_neighbors(ir_grid, robot_pos, robot_dir, current_ir_values, tile_wall_count, has_new_ir)
                            update_ir_map = True
                            update_final_ir(grid, ir_grid)
                        state = TRAVEL
                    else:
                        state = SLAM
                    continue
                    
            else:
                state = WALL
            continue

        elif state == TURN_LEFT:
            prev_state = TURN_LEFT
            turn(90, 'left', ir_values)
            # Reset verify counter on neighbour tiles so they are verified again after the turn
            reset_neighbors(robot_pos, tile_wall_count)
            
            # Force a new position after a turn to keep the robot aligned with the grid
            
            int_x = int(robot_pos[0])
            int_y = int(robot_pos[1])

            robot_pos[0] = int_x + 0.5
            robot_pos[1] = int_y + 0.5
            
            state = WALL
            continue
            
        elif state == TURN_RIGHT:
            prev_state = TURN_RIGHT
            turn(90, 'right', ir_values)
            # Reset verify counter on neighbour tiles so they are verified again after the turn
            reset_neighbors(robot_pos, tile_wall_count)

            # Force a new position after a turn to keep the robot aligned with the grid
            int_x = int(robot_pos[0])
            int_y = int(robot_pos[1])

            robot_pos[0] = int_x + 0.5
            robot_pos[1] = int_y + 0.5
            
            state = WALL
            continue
            
        elif state == DEAD_END:
            prev_state = DEAD_END
            #front
            _x, _y = GRID_INDEX_VALUES[robot_dir][0]
            set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, WALL_TILE, ir_grid)
            tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,100,0]
            #right
            _x, _y = GRID_INDEX_VALUES[robot_dir][2]
            set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, WALL_TILE, ir_grid)
            tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,100,0]
            #left
            _x, _y = GRID_INDEX_VALUES[robot_dir][3]
            set_grid_value_2d(int(robot_pos[0])+_x, int(robot_pos[1])+_y, WALL_TILE, ir_grid)
            tile_wall_count[(int(robot_pos[0]) + _x, int(robot_pos[1]) + _y)] = [100,100,0]
            turn(180, 'left', ir_values)
            state = WALL
            continue

        elif state == SLAM:
            prev_state = SLAM
            pid.enabled = False

            if not laser_counter:
                for i in range(4):
                    while has_new_ir.value == 0:
                        pass
                    current_ir_values = [ir for ir in ir_values]
                    map_ir_neighbors(ir_grid, robot_pos, robot_dir, current_ir_values, tile_wall_count, has_new_ir)
                update_ir_map = True
                update_final_ir(grid, ir_grid)
            if not first_laser_read:
                for y in range(MAP_SIZE):
                    for x in range(MAP_SIZE):
                        set_grid_value(x,y, ir_grid[y][x], grid)

            

            
            #print('\nIN SLAM STATE, SET SPEED 0')
            st.set_speed(AUTO_MODE, 0)
            time.sleep(0.5)
            if path.closed_room(grid, robot_pos):
                # Find closest path home
                print('ROOM IS CLOSED, GO HOME')
                stop_tower(num_hall_reads)
                path_home = path.a_star(grid, robot_pos, [15.5, 15.5])
                travel_commands = path.follow_path(path_home, robot_dir)
                print("Path home: " + str(travel_commands))
                state = TRAVEL
                ir_enabled = False
                continue
            else:
                # Check if closest unexplored tile is too far away, if so then go there
                unexplored_tiles = path.bfs(grid, robot_pos, find_unidentified=True)
                if unexplored_tiles and len(path.a_star(grid, robot_pos, unexplored_tiles[0])) > 7:
                    state = TRAVEL
                    continue
                    
                st.set_speed(AUTO_MODE, 50, 'tower')
            
            #  Wait for new laser values
            while 0 < num_laser_values.value < 520 and num_hall_reads.value == 0:
                pass

            
            if laser_counter < mapper.maxiter:
                #print('NOT ENOUGH READS, UPDATING MAP')
                # Copy laser sensor reads from shared array if there are less then 520 reads
                laser_list = []

                with laser_values.get_lock():
                    if num_laser_values.value > 520:
                        with num_laser_values.get_lock():
                            num_laser_values.value = 0
                        continue
                    laser_list = [laser_values[i] for i in range(num_laser_values.value)]

                # Update map based on the new sensor values
                if laser_list:
                    laser_counter += 1
                    
                    # Generate submap
                    generated_map = slammer.mapper(laser_list)

                    # Add the submap to the 'final' one
                    mapper.add_submap(generated_map[0], generated_map[1], (int(robot_pos[0]), int(robot_pos[1])), robot_dir)

                    fingrid = [[UNKNOWN_TILE for x in range(MAP_SIZE)] for y in range(MAP_SIZE)]
                    for y in range(MAP_SIZE):
                        for x in range(MAP_SIZE):
                            fingrid[y][x] = get_grid_value(x,y,grid)
                    
                    mapper.generate_map(fingrid)
                    
                    
                   
            elif laser_counter >= mapper.maxiter:


                if (not first_laser_read):
                    first_laser_read = True
                
                print('\nENOUGH LASER READS, STOPPING TOWER', laser_counter)
                laser_counter = 0
                stop_tower(num_hall_reads)

                raycast_map = [[0 for i in range(MAP_SIZE)] for j in range(MAP_SIZE)]
                for y in range(31):
                    for x in range(31):
                        value = 0
                        if (mapper.submaps):
                            value = float(mapper.finalmap[y][x]) / len(mapper.submaps)
                        tile_value = UNKNOWN_TILE
                        if (value >= 0.5):
                            tile_value = WALL_TILE
                        raycast_map[y][x] = tile_value
                

                subp = sm.slice_submap(ir_grid, (int(robot_pos[0]), int(robot_pos[1])))

                raycast_map = sm.returnFinal(raycast_map, subp[0], subp[1], (int(robot_pos[0]), int(robot_pos[1])))
                ray_floor = sm.raycast_floor(raycast_map,(int(robot_pos[0]), int(robot_pos[1])))
                
                for y in range(31):
                    for x in range(31):
                        ray_val = raycast_map[y][x]
                        #las_val = laser_floor[y][x]
                        rayflorval = ray_floor[y][x]
                        if (rayflorval == 1):
                            laser_floor[y][x] = rayflorval
                        las_val = laser_floor[y][x]
                        if (las_val == 1):
                            if (ray_val < 2):
                                raycast_map[y][x] = 1

                
                for i in range(31):
                    for j in range(31):                            
                        value = raycast_map[i][j]
                        if (value >= 2):
                            value = 2
                        set_grid_value(j, i, value, grid)

                mapper.remove_bad_values()

                        
                if path.closed_room(grid, robot_pos):
                    # Find closest path home
                    print('ROOM IS CLOSED, GO HOME')
                    path_home = path.a_star(grid, robot_pos, [15.5, 15.5])
                    travel_commands = path.follow_path(path_home, robot_dir)
                    print("Path home: " + str(travel_commands))
                    state = TRAVEL
                    ir_enabled = False
                else:
                    print('ROOM IS NOT CLOSED, ENTER TRAVEL')
                    state = TRAVEL
                
            #state = WALL
            continue

        # Executes commands sent from the laptop
        elif state == MANUAL:
            st.set_speed(AUTO_MODE, 0)
            prev_state = MANUAL
            stop_tower(num_hall_reads)
            time.sleep(1)
            
            # Enter autonomous mode
            if mode.value == 1:
                state = START
                continue

            # Disable pid and start recieving commands
            pid.enabled = False
            st.steering_serial(steering_cmd_man, mode, ir_values)  # Blocks
            
            st.steering_port.flushInput()
            st.forward()
            continue


if __name__ == "__main__":
    # Variables shared between processes
    ir_values = Array('i', 6)
    laser_values = Array('i', 520)
    num_laser_values = Value('i', 0)
    num_hall_reads = Value('i', 0)
    gyro_value = Value('d', 0)
    has_new_ir = Value('i', 0)
    mode = Value('i', 0)  # Manual, Atonomous = 0, 1
    pid_cons = Array('d', 2)
    pid_cons[0] = -1  # Make sure to not read pid values from array on boot
    grid = Array('i', MAP_SIZE**2)
    shared_pos = Array('i',2)
    move_cmd = Array('c', 50)
    steering_cmd_man = SimpleQueue()

    # Init ir array to avoid errors in the beginning
    with ir_values.get_lock():
        ir_values[0] = EMPTY_TILE 
    
    # Setup and start processes
    # sensor_process:    Handles communication with the sensor module
    # slam_process:      Decision logic. Uses data recieved from both the sensor and bluetooth processes.
    #                    The slam process also takes care of communication with the steering module.
    # bluetooth_process: Handles communication with the bluetooth connected laptop
    sensor_process = Process(target=sensor.sensor_serial, args=(ir_values, laser_values, gyro_value, num_laser_values, num_hall_reads, has_new_ir))
    slam_process = Process(target=slam, args=(ir_values, laser_values, mode, steering_cmd_man, pid_cons, gyro_value, num_laser_values, num_hall_reads, grid, shared_pos, move_cmd, has_new_ir))
    bluetooth_process = Process(target=blueztooth.bluetooth_loop, args=(ir_values, laser_values, steering_cmd_man, mode, pid_cons, num_laser_values, grid, shared_pos, move_cmd))

    sensor_process.start()
    slam_process.start()
    bluetooth_process.start()

    prev_laser = []

    sensor_process.join()
    slam_process.join()
    bluetooth_process.join()
