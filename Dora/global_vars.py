import threading

STEERING_PORT = "FT94TI48"
SENSOR_PORT = "FT94S3XQ"

BAUDRATE_STEERING = 115200
BAUDRATE2 = 230400 #BAUDRATE_SENSOR

serUSB1 = None
running = True
condition = threading.Condition()

movement_dir = None
