import common
import serial
import time

IR_ID = 92
LASER_ID = 93
GYRO_ID = 94
STOP_ID = 255

BAUDRATE = 230400
PORT_NAME = "FT94S3XQ"

# Reading states
IR = 1
LASER = 2
GYRO = 3


STATES = {IR_ID: 1, LASER_ID: 2, GYRO_ID: 3}

def open_port():
    sensor_port = None
    try:
        sensor_port = serial.Serial(common.find_usb(PORT_NAME))
        sensor_port.baudrate = BAUDRATE
    except serial.serialutil.SerialException, exc:
        print("Failes to open sensor port: %s" % exc)
    return sensor_port
    
                
def sensor_serial(ir_values, laser_values, gyro_value, num_laser_values):
    print("Starting sensor process")
    sensor_port = open_port()
    if sensor_port == None:
        return
    
    serial_state = 0
    cur_laser_index = 0
    laser_buffer = []
    
    while True:
        try:
            if (sensor_port.isOpen()):
                #If we are waiting for serial data
                last_read = None
                if (serial_state == 0):
                    byteORD = ord(sensor_port.read(1))
                    if byteORD in STATES.keys():
                        serial_state = STATES[byteORD]                    
                    
                if (serial_state == IR):
                    for i in range(len(ir_values)):
                        byteORD = ord(sensor_port.read(1))
                        with ir_values.get_lock():
                            ir_values[i] = byteORD
                    serial_state = 0
                    
                elif (serial_state == LASER):
                    first_byte = ord(sensor_port.read(1))
                    if (first_byte == STOP_ID):
                        if len(laser_buffer) <= len(laser_values):
                            with laser_values.get_lock():
                                for i in range(len(laser_buffer)):
                                    laser_values[i] = laser_buffer[i]
                            
                        
                        diff = int(ord(sensor_port.read(1)))
                        num_laser_values.value = int(ord(sensor_port.read(1)))*256+int(ord(sensor_port.read(1)))
                        laser_buffer = []
                    else:
                        # Append laser value
                        laser_buffer.append(int(first_byte) * 256 + int(ord(sensor_port.read(1))))
                    serial_state = 0
                    
                elif (serial_state == GYRO):
                    gyro_adc = ord(sensor_port.read(1)) * 256 + ord(sensor_port.read(1))
                    bias = 2500

                    
                    #gv.gyro_value = (((25.0/12) * gyro_value2) + 400 - bias)/6.67
                    with gyro_value.get_lock():
                        gyro_value.value = (((25.0/12) * gyro_adc) + 400 - bias)/6.67

                    """
                    elap = (time.time() - gv.last_gyro_time)
                    gv.last_gyro_value = gv.gyro_value * elap
                    
                    #if (math.fabs(math.radians(gv.last_gyro_value)) >= 0.005):
                    #    robot_rot += math.radians(gv.last_gyro_value)
                    gv.last_gyro_time = time.time()
                    """
                    serial_state = 0
                else:
                    serial_state = 0
        except serial.serialutil.SerialException, exc:
            print("An error occured with the serial connection on the sensor port: %s" % exc)
        
    sensor_port.close()
