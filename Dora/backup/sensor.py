import common
import serial
import time
from global_vars import *

IR_ID = 92
LASER_ID = 93
GYRO_ID = 94
STOP_ID = 255

# Reading states
IR = 1
LASER = 2
GYRO = 3


STATES = {IR_ID: 1, LASER_ID: 2, GYRO_ID: 3}

def open_port():
    sensor_port = None
    try:
        sensor_port = serial.Serial(common.find_usb(SENSOR_PORT_NAME))
        sensor_port.baudrate = BAUDRATE_SENSOR
    except serial.serialutil.SerialException, exc:
        print("Failes to open sensor port: %s" % exc)
    return sensor_port
    
                
def sensor_serial(ir_values, laser_values, gyro_value, num_laser_values, num_hall_reads):
    print("Starting sensor process")
    sensor_port = open_port()
    if sensor_port == None:
        print("Could not find/open sensor port")
        return
    
    serial_state = 0
    cur_laser_index = 0
    laser_buffer = []
    prev_gyro = 0
    prev_gyro_time =time.time()
    prev_ir = []
    
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
                    #if prev_ir != [ir_values[i] for i in range(len(ir_values))]:
                    #    prev_ir = [ir_values[i] for i in range(len(ir_values))]
                    #    print(prev_ir)
                    
                elif (serial_state == LASER):
                    first_byte = ord(sensor_port.read(1))
                    
                    if (first_byte == STOP_ID):

                        with num_hall_reads.get_lock():
                            num_hall_reads.values = 0
                        
                        if len(laser_buffer) <= len(laser_values):
                            with laser_values.get_lock():
                                for i in range(len(laser_buffer)):
                                    laser_values[i] = laser_buffer[i]
                        else: print("NUM LASER > MAX")
                            
                        
                        diff = int(ord(sensor_port.read(1)))
                        num_laser_values.value = int(ord(sensor_port.read(1)))*256+int(ord(sensor_port.read(1)))
                        #print("REC", num_laser_values.value)
                        #curr_num_laser_values.value = 0
                        #with open('laser_log.log', 'a') as log_file:
                        #    log_file.write('[laser]%s#' % str(laser_buffer))
                        laser_buffer = []
                    else:
                        # Append laser value
                        if (first_byte > 100 and first_byte < 255):
                            first_byte = first_byte - 240
                            with num_hall_reads.get_lock():
                                num_hall_reads.value += 1
                        else:
                            with num_hall_reads.get_lock():
                                num_hall_reads.value = 0
                        laser_buffer.append(int(first_byte) * 256 + int(ord(sensor_port.read(1))))
                        #if curr_num_laser_values.value > len(laser_values):
                        #    curr_num_laser_values.value = 0
                        # curr_num_laser_values.value += 1
                    serial_state = 0
                    
                elif (serial_state == GYRO):
                    gyro_adc = ord(sensor_port.read(1)) * 256 + ord(sensor_port.read(1))
                    bias = 2477.8


                    #gv.gyro_value = (((25.0/12) * gyro_value2) + 400 - bias)/6.67
                    with gyro_value.get_lock():
                        #gyro_value.value = (((25.0/12) * gyro_adc) + 400 - bias)/6.67
                        angular_rate = (((25.0/12) * gyro_adc) + 400 - bias)/6.67

                        #if abs(angular_rate) >= 8:
                        gyro_value.value += angular_rate * (time.time() - prev_gyro_time)
                        prev_gyro_time = time.time()
                    
                    serial_state = 0
                else:
                    serial_state = 0
        except serial.serialutil.SerialException, exc:
            print("An error occured with the serial connection on the sensor port: %s" % exc)
        
    sensor_port.close()
