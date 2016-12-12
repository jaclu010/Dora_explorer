import os
from multiprocessing import Array
from global_vars import *
import control
from path import *


def find_usb(port_id):
    port = ""
    for file in os.listdir("/dev/serial/by-id"):
        if port_id in file:
            symlink = os.path.join("/dev/serial/by-id/", file)
            port = str(os.path.realpath(symlink))
    return port


def set_grid_value(col, row, value, grid):
    with grid.get_lock():
        grid[(row*MAP_SIZE)+col] = value

        
def reset_neighbors(robot_pos, tile_wall_count):
    int_pos = tuple(int_robot_pos(robot_pos))
    current_node = Node(int_pos[0], int_pos[1])
    for node in current_node.neighbors():
        neighbour_pos = (node.x, node.y)
        tile_wall_count[neighbour_pos] = [0,0,0]


def map_ir_neighbors(grid, robot_pos, robot_dir, ir_values, tile_wall_count):
    int_pos = tuple(int_robot_pos(robot_pos))
    current_node = Node(int_pos[0], int_pos[1])
    neighbours = []
    for node in current_node.neighbors():
        neighbour_pos = (node.x, node.y)
        neighbours.append(neighbour_pos)
        if neighbour_pos not in tile_wall_count.keys():
            tile_wall_count[neighbour_pos] = [0,0,0]

    current_ir_values = []
    with ir_values.get_lock():
        current_ir_values = [ir_values[i] for i in range(NUM_SENSORS)]
            
        
    for i in range(NUM_SENSORS):
        index = i
        if i == 2 or i == 3:
            index = 2
        elif i == 4 or i == 5:
            index = 3
            
        _x, _y = GRID_INDEX_VALUES[robot_dir][index]
        temp_pos = (int_pos[0] + _x, int_pos[1] + _y)
        if temp_pos in tile_wall_count.keys() and tile_wall_count[temp_pos][0] < 10:
            tile_wall_count[temp_pos][0] += 1
            if current_ir_values[i] == 25:
                tile_wall_count[temp_pos][2] += 1
            else:
                tile_wall_count[temp_pos][1] += 1

    for n in neighbours:
        if tile_wall_count[n][0] == 10:
            tile_wall_count[n][0] += 1
            if tile_wall_count[n][1] == tile_wall_count[n][2]:
                tile_wall_count[n] = [0, 0, 0] # reset counter
            elif tile_wall_count[n][1] < tile_wall_count[n][2]:
                set_grid_value(n[0], n[1], EMPTY_TILE, grid)
            else:
                set_grid_value(n[0], n[1], WALL_TILE, grid)

    set_grid_value(int_pos[0], int_pos[1], EMPTY_TILE, grid)

        
def calc_distance(time_driven):
    #return 43.79*time_driven-3.185
    return 51.5*time_driven-3.185


def update_robot_pos(robot_pos, robot_dir, num_tiles):
    # Update robot position
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


def detect_walls(ir_values):
    reverse_pid = None
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
    return reverse_pid

def int_robot_pos(robot_pos):
    return [int(robot_pos[0]), int(robot_pos[1])]

"""
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
"""


if __name__ == '__main__':
    # Test set_grid_value
    grid = Array('i', 10)
    set_grid_value(1,0,2,grid)
    print([grid[i] for i in range(len(grid))])
