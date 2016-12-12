import os
from multiprocessing import Array
from global_vars import *

FORWARD = 0
BACKWARD = 1
BACKWARD_RIGHT = 2
FORWARD_RIGHT = 3
BACKWARD_LEFT = 4
FORWARD_LEFT = 5

FORWARD_SENSOR_MAPPING = {FORWARD: 0, BACKWARD: 1, BACKWARD_RIGHT: 2,
                          FORWARD_RIGHT: 3, BACKWARD_LEFT: 4, FORWARD_LEFT: 5}
BACKWARD_SENSOR_MAPPING = {FORWARD: 1, BACKWARD: 0, BACKWARD_RIGHT: 5,
                           FORWARD_RIGHT: 4, BACKWARD_LEFT: 3, FORWARD_LEFT: 2}


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

def convert_array_to_2d(grid):
        grid_2d = []
        for row in range(MAP_SIZE):
                grid_2d.append([])
                for col in range(MAP_SIZE):
                        grid_2d[row].append(grid[row*MAP_SIZE+col])
        return grid_2d


if __name__ == '__main__':
        # Test set_grid_value
        grid = Array('i', 10)
        set_grid_value(1,0,2,grid)
        print([grid[i] for i in range(len(grid))])
        
