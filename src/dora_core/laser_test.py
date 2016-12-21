from __future__ import print_function
import math
from common import *
from global_vars import *

robot_pos = [5,5]
robot_dir = NORTH
current_grid_pos = [0,0]
grid = [0 for i in range(MAP_SIZE**2)]

def get_grid_pos(laser_values):
    global current_grid_pos
    num_values = len(laser_values)
    if num_values == 0:
        return
    step = math.radians(360.0) / num_values
    temp_x = []
    temp_y = []
    for i in range(num_values):

        x = laser_values[i] * math.cos((math.radians(270) + step * i))
        y = laser_values[i] * math.sin((math.radians(270) + step * 1))

        if i == 2:
            current_grid_pos[1] = round(abs(y) % TILE_SIZE)
        elif i == ((num_values // 4) * 3)+2:
            current_grid_pos[0] = round(abs(x) % TILE_SIZE)

    if len(temp_x) > 0:
        current_grid_pos[0] = sum(temp_x) / len(temp_x)
    if len(temp_y) > 0:
        current_grid_pos[1] = sum(temp_y) / len(temp_y)


def get_grid_id(x,y):
    _grid = [0,0]
    if x >= 0:
        _grid[0] = (current_grid_pos[0] + x) // 40
    else:
        _grid[0] = -1 * ((current_grid_pos[0] + abs(x)) // 40)

    if y >= 0:
        _grid[1] = (current_grid_pos[1] + y) // 40
    else:
        _grid[1] = -1 * ((current_grid_pos[1] + abs(y)) // 40)

    return _grid


def simple_laser(laser_val):
    start_angle = START_ANGLES[robot_dir]
    step = 2*math.pi / len(laser_val)
    get_grid_pos(laser_val)
    for i in range(len(laser_val)):
        x = math.cos(start_angle+step*i)*laser_val[i]
        y = math.sin(start_angle+step*i)*laser_val[i]
        x_id, y_id = get_grid_id(x,y)
        grid[((robot_pos[1] + int(y_id))*MAP_SIZE)+(robot_pos[0] + int(x_id))] = WALL_TILE


if __name__ == '__main__':
    with open('laser_log.log', 'r') as laser_file:
        reads = laser_file.readlines()[0].split('#')
        for read in reads:
            read = eval(read[len('[laser]'):])
            simple_laser(read)
            counter = 0
            for value in grid:
                if counter == 30:
                    print(value)
                    counter = 0
                else:
                    if value == 2:
                        print('\033[93m' +str(value)+'\033[0m', end="")
                    else:
                        print(value, end="")
                    counter +=1
            raw_input()
            grid = [0 for i in range(MAP_SIZE**2)]
            
    
    
    
    
