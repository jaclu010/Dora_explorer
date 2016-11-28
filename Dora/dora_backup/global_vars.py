import threading
import time
import math

STEERING_PORT = "FT94TI48"
SENSOR_PORT = "FT94S3XQ"

BAUDRATE_STEERING = 115200
BAUDRATE_SENSOR = 230400

running = True
condition = threading.Condition()

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
