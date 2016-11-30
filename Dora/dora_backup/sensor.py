import common
import global_vars as gv
import serial
import time

IR_ID = 92
LASER_ID = 93
GYRO_ID = 94
STOP_ID = 255

serUSB0 = None

try:
    serUSB0 = serial.Serial(common.find_usb(gv.SENSOR_PORT))
    serUSB0.baudrate = gv.BAUDRATE_SENSOR
except serial.serialutil.SerialException, exc:
    print("USB0 IT NO WORK, Johan did fuck up! %s" % exc)
    
                
def sensor_serial(tid):
    print("Thread" + str(tid) + " main loop initialized")
    #global sensor_value
    global serUSB0
    serial_state = 0
    cur_laser_index = 0
    #global laser_value, last_laser_value
    #global gyro_value
    #global num_laser_reads
    #global last_gyro_time, last_gyro_value
    #global robot_rot
    
    while gv.running:
        if (serUSB0 != None):
            try:
                if (serUSB0.isOpen()):
                    #If we are waiting for serial data
                    last_read = None
                    if (serial_state == 0):
                        byte = serUSB0.read(1)
                        byteORD = ord(byte)
                        if (byteORD == IR_ID): serial_state = 1
                        if (byteORD == LASER_ID): serial_state = 2
                        if (byteORD == GYRO_ID): serial_state = 3
                    if (serial_state == 1):
                        #ir_state
                        for i in range(0, gv.num_sensors):
                            byte = serUSB0.read(1)
                            byteORD = ord(byte)
                            gv.sensor_value[i] = str(byteORD) 
                        serial_state = 0
                    elif (serial_state == 2):
                        #laser_state
                        val1 = None
                        val2 = None
                        brake_state = False

                        b1 = serUSB0.read(1)
                        b1ORD = ord(b1)

                        if (b1ORD == STOP_ID):
                            gv.last_laser_value = gv.laser_value
                            gv.laser_value = []
                            a = serUSB0.read(1)
                            aORD = ord(a)
                            b = serUSB0.read(1)
                            bORD = ord(b)
                            c = serUSB0.read(1)
                            cORD = ord(c)
                            value = int(bORD) * 256 + int(cORD)
                            print("Len : " + str(len(gv.last_laser_value)) + ", sent Len : " + str(value) + ", laserDIFF : " + str(aORD))
                        else:
                            b2 = serUSB0.read(1)
                            b2ORD = ord(b2)
                            val1 = b1ORD
                            val2 = b2ORD
                            gv.laser_value.append(int(val1) * 256 + int(val2))
                        serial_state = 0
                    elif (serial_state == 3):
                        #sensor_state
                        byte = serUSB0.read(1)
                        byteORD = ord(byte)
                        byte2 = serUSB0.read(1)
                        byteORD2 = ord(byte2)
                        gyro_value2 = byteORD * 256 + byteORD2
                        
                        bias = 2500
                        
                        gv.gyro_value = (((25.0/12) * gyro_value2) + 400 - bias)/6.67
                        elap = (time.time() - gv.last_gyro_time)
                        gv.last_gyro_value = gv.gyro_value * elap

                        #if (math.fabs(math.radians(gv.last_gyro_value)) >= 0.005):
                        #    robot_rot += math.radians(gv.last_gyro_value)
                        gv.last_gyro_time = time.time()
                        serial_state = 0
                    else:
                        serial_state = 0
            except serial.serialutil.SerialException, exc:
                print("An error occured with the serial connection on the sensor port: %s" % exc)
        
    serUSB0.close()
