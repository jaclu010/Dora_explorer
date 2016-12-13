import threading
import time
import math


# UART
STEERING_PORT_NAME = "FT94IDR4"
SENSOR_PORT_NAME = "FT94NXIE"

BAUDRATE_STEERING = 115200
BAUDRATE_SENSOR = 230400

# MODES
MANUAL_MODE = 0
AUTO_MODE = 1
running = True
condition = threading.Condition()

# TILES
UNKNOWN_TILE = 0
EMPTY_TILE = 1
WALL_TILE = 2
TILE_SIZE = 40

# DIRECTIONS
NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

# TURNING
TURN_TIME = {90: 0.63, 180: 1.1}
LEFT = 0
RIGHT = 1


# MAPPING
MAP_SIZE = 31
GRID_INDEX_VALUES = [[[0,-1],[1,0],[0,1],[-1,0]],
                     [[0,1],[-1,0],[0,-1],[1,0]],
                     [[1,0],[0,1],[-1,0],[0,-1]],
                     [[-1,0],[0,-1],[1,0],[0,1]]]

# IR CHECK VALUES
FORWARD_CHECK = 16
BACKWARD_CHECK = 16
LEFT_CHECK = 15
RIGHT_CHECK = 15
EMPTY_CHECK = 25

#SEARCH_MODE
IR = 0
LASER = 1

START_ANGLES = [math.radians(270), math.pi, math.pi/2, 0]


movement_dir = "none"

num_sensors = 6

sensor_value = [0 for x in range(num_sensors)]
laser_value = []
last_laser_value = []
gyro_value = 0
#num_laser_reads = 0
last_gyro_time = time.time()
last_gyro_value = 0
robot_rot = math.pi
robot_rot_speed = math.pi / 40

# States
MANUAL, SLAM, WALL, TURN_LEFT, TURN_RIGHT, DEAD_END, START, TRAVEL = range(8)
