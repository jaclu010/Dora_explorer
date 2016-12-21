#####
#
# common.py
# Updated: 14/12 2016
# Authors: Fredrik Iselius, Martin Lundberg, Niklas Nilsson
#
#####
from __future__ import print_function
import os
from multiprocessing import Array
from global_vars import *
import control
from path import *


def find_usb(port_id):
    """
    Returns the full path to the serial port that contains 'port_id' in its name
    """
    port = ""
    for file in os.listdir("/dev/serial/by-id"):
        if port_id in file:
            symlink = os.path.join("/dev/serial/by-id/", file)
            port = str(os.path.realpath(symlink))
    return port


def set_grid_value(col, row, value, grid):
    with grid.get_lock():
        grid[(row*MAP_SIZE)+col] = value

def get_grid_value(col, row, grid):
    with grid.get_lock():
       return grid[(row*MAP_SIZE+col)]

def set_grid_value_2d(col, row, value, grid):
    grid[row][col] = value

def get_grid_value_2d(col, row, grid):
    return grid[row][col]

def reset_neighbors(robot_pos, tile_wall_count):
    """
    Resets the counter value for all neighbours of the current tile
    if they exist in the 'tile_wall_count' dictionary
    """
    int_pos = tuple(int_robot_pos(robot_pos))
    current_node = Node(int_pos[0], int_pos[1])
    for node in current_node.neighbors():
        neighbour_pos = (node.x, node.y)
        if neighbour_pos in tile_wall_count.keys():
            tile_wall_count[neighbour_pos][0] = 0
"""
def add_walls(grid, int_pos, tile_wall_count, neighbours):
    # Check if the neighbour tile should be drawn as a wall or empty tile
    for n in neighbours:
        
"""

def set_wall(grid, pos, tile_wall_count):
    if tile_wall_count[pos][1] == tile_wall_count[pos][2]:
        tile_wall_count[pos] = [0, 0, 0] # reset counter
    elif tile_wall_count[pos][1] < tile_wall_count[pos][2]:
        set_grid_value_2d(pos[0], pos[1], EMPTY_TILE, grid)
    else:
        set_grid_value_2d(pos[0], pos[1], WALL_TILE, grid)

    
def map_ir_neighbors(grid, robot_pos, robot_dir, current_ir_values, tile_wall_count, has_new_ir):
    """
    Updates the map on the current tile and all its neighbours.
    """
    int_pos = tuple(int_robot_pos(robot_pos))
    current_node = Node(int_pos[0], int_pos[1])
    neighbours = []

    tile_wall_count[int_pos] = [11,0,0]  # Fix current tile as checked
    
    # Get all neighbours of the current tile and add them to tile_wall_count
    for node in current_node.neighbors():
        neighbour_pos = (node.x, node.y)
        neighbours.append(neighbour_pos)
        if neighbour_pos not in tile_wall_count.keys():
            tile_wall_count[neighbour_pos] = [0,0,0]    
            
    # Add the number of times a tile was identified as a wall/empty tile
    # to the tile_wall_count dict
    for i in range(NUM_SENSORS):
        if i == 1 or i == 2 or i == 4:
            continue
        index = i
        if i == 2 or i == 3:
            index = 2
        elif i == 4 or i == 5:
            index = 3
            
        _x, _y = GRID_INDEX_VALUES[robot_dir][index]
        temp_pos = (int_pos[0] + _x, int_pos[1] + _y)
        if temp_pos in tile_wall_count.keys():
            if tile_wall_count[temp_pos][0] < 3:
                tile_wall_count[temp_pos][0] += 1
                if current_ir_values[i] == 25:
                    tile_wall_count[temp_pos][2] += 1
                else:
                    tile_wall_count[temp_pos][1] += 1
            else:
                set_wall(grid, temp_pos, tile_wall_count)

    set_grid_value_2d(int_pos[0], int_pos[1], EMPTY_TILE, grid)
   
        
def calc_distance(time_driven):
    """
    ---Deprecated---
    Function to calculate driven distance
    """
    return 51.5*time_driven-3.185


def update_robot_pos(robot_pos, robot_dir, num_tiles):
    """
    Updates the robot position with num_file in direction robot_dir
    """
    
    if robot_dir % 4 == NORTH:
        robot_pos[1] -= num_tiles
    elif robot_dir % 4 == EAST:
        robot_pos[0] += num_tiles
    elif robot_dir % 4 == SOUTH:
        robot_pos[1] += num_tiles
    elif robot_dir % 4 == WEST:
        robot_pos[0] -= num_tiles
    return robot_pos


def convert_array_to_2d(grid):
    """
    Converts an array with size MAP_SIZE**2
    to a 2d array of the same size
    """
    grid_2d = []
    for row in range(MAP_SIZE):
        grid_2d.append([])
        for col in range(MAP_SIZE):
            grid_2d[row].append(grid[row*MAP_SIZE+col])
    return grid_2d


def copy_list(o_list):
    n_list = []
    for elem in o_list:
        n_list.append(elem)
    return n_list


def detect_walls(ir_values, prev_pid_side=None):
    """
    Used to determine which side to use for the PID.
    Returns None if there are no walls in range
    """
    ir = ir_values
    reverse_pid = None

    if prev_pid_side == LEFT or prev_pid_side == None:
        if ir_values[IR_ID[FORWARD_LEFT]] < EMPTY_CHECK and ir_values[IR_ID[BACKWARD_LEFT]] < EMPTY_CHECK:
            # Wall detected on left side
            reverse_pid = LEFT
            control.forward_sensor = IR_ID[FORWARD_LEFT]
            control.backward_sensor = IR_ID[BACKWARD_LEFT]
        elif ir_values[IR_ID[FORWARD_RIGHT]] < EMPTY_CHECK and ir_values[IR_ID[BACKWARD_RIGHT]] < EMPTY_CHECK:
            # Wall detected on right side
            reverse_pid = RIGHT
            control.forward_sensor = IR_ID[FORWARD_RIGHT]
            control.backward_sensor = IR_ID[BACKWARD_RIGHT]
    elif prev_pid_side == RIGHT:
        if ir_values[IR_ID[FORWARD_RIGHT]] < EMPTY_CHECK and ir_values[IR_ID[BACKWARD_RIGHT]] < EMPTY_CHECK:
            # Wall detected on right side
            reverse_pid = RIGHT
            control.forward_sensor = IR_ID[FORWARD_RIGHT]
            control.backward_sensor = IR_ID[BACKWARD_RIGHT]
        elif ir_values[IR_ID[FORWARD_LEFT]] < EMPTY_CHECK and ir_values[IR_ID[BACKWARD_LEFT]] < EMPTY_CHECK:
            # Wall detected on left side
            reverse_pid = LEFT
            control.forward_sensor = IR_ID[FORWARD_LEFT]
            control.backward_sensor = IR_ID[BACKWARD_LEFT]
    return reverse_pid

def int_robot_pos(robot_pos):
    return [int(robot_pos[0]), int(robot_pos[1])]

def print_submap(submap):
    green = '\033[92m'
    blue = '\033[94m'
    endc = '\033[0m'

    for y in submap:
        for x in y:
            if int(x) == 1:
                print(blue + str(x) + endc, end='')
            elif int(x) == 2:
                print(green + str(x) + endc, end='')
            else:
                print(str(x), end='')
            print('')
