#####
#
# sensor.py
# Updated: 14/12 2016
# Authors: Fredrik Iselius, Martin Lundberg, Johan Nilsson, Niklas Nilsson
#
#####

import common
import serial
import time
from global_vars import *

# ID bytes
IR_ID = 92
LASER_ID = 93
GYRO_ID = 94
STOP_ID = 255

STATES = {IR_ID: 1, LASER_ID: 2, GYRO_ID: 3}

def open_port():
    """
    Open UART port to sensor module
    Catches error and prints if port can't be opened
    """
    sensor_port = None
    try:
        sensor_port = serial.Serial(common.find_usb(SENSOR_PORT_NAME))
        sensor_port.baudrate = BAUDRATE_SENSOR
    except serial.serialutil.SerialException as exc:
        print("Failes to open sensor port: %s" % exc)
    return sensor_port
    
# Reads various sensor values sent from sensor module via UART                
def sensor_serial(ir_values, laser_values, gyro_value, num_laser_values, num_hall_reads, has_new_ir):
    """
    Reads IR, Laser & Gyro values received over UART
    Adds values to shared memory
    """

    print("Starting sensor process")
    sensor_port = open_port()

    if not sensor_port:
        print("Could not find/open sensor port")
        return
    
    serial_state = 0
    laser_buffer = []
    prev_gyro = 0
    prev_gyro_time = time.time()
    
    while True:
        try:
            if sensor_port.isOpen():
                # If we are waiting for serial data
                if serial_state == 0:
                    byte_ord = ord(sensor_port.read(1))
                    if byte_ord in STATES.keys():
                        serial_state = STATES[byte_ord]
                        
                # IR start byte received    
                if serial_state == STATES[IR_ID]:
                    with has_new_ir.get_lock():
                        has_new_ir.value = 1
                    for i in range(NUM_SENSORS):
                        byte_ord = ord(sensor_port.read(1))
                        with ir_values.get_lock():
                            ir_values[i] = byte_ord
                            
                # Laser start byte received    
                elif serial_state == STATES[LASER_ID]:
                    first_byte = ord(sensor_port.read(1))

                    # Stop ID received
                    if first_byte == STOP_ID:
                        
                        if len(laser_buffer) <= len(laser_values): # Moves laser readings from buffer to shared memory
                            with laser_values.get_lock():
                                for i in range(len(laser_buffer)):
                                    laser_values[i] = laser_buffer[i]

                        with num_hall_reads.get_lock():
                            num_hall_reads.value = 0

                        diff = int(ord(sensor_port.read(1)))
                        num_laser_values.value = int(ord(sensor_port.read(1)))*256+int(ord(sensor_port.read(1)))
                        laser_buffer = []
                    else:
                        # Count number of laser readings at hall sensor
                        if 100 < first_byte < 255: # Remove Hall byte from laser reading
                            first_byte -= 240
                            with num_hall_reads.get_lock():
                                num_hall_reads.value += 1

                        # Add laser reading to buffer
                        laser_buffer.append(int(first_byte) * 256 + int(ord(sensor_port.read(1))))

                # Gyro start byte received
                elif serial_state == STATES[GYRO_ID]:
                    gyro_adc = ord(sensor_port.read(1)) * 256 + ord(sensor_port.read(1))
                    bias = 2477.8
                    angular_rate = (((25.0/12) * gyro_adc) + 400 - bias)/6.67 # Converts gyro reading to angular rate

                    with gyro_value.get_lock():
                        gyro_value.value += angular_rate * (time.time() - prev_gyro_time)
                        prev_gyro_time = time.time()
                    
                serial_state = 0

        except serial.serialutil.SerialException as exc:
            print("An error occured with the serial connection on the sensor port: %s" % exc)
        
    sensor_port.close()
