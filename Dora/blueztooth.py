from bluetooth import *
import sys

#mac adress to server, per default 7C:7A:91:4A:21:D9 (martins dator)
FIXED_PC = True
FIXED_ADDR = "7C:7A:91:4A:21:D9"


def blue_connect(addr=FIXED_ADDR):
    #Unique id, should be the same as servers
    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
    bluetooth_online = True
    if addr != FIXED_ADDR:
        #Otherwise get mac-addres from argument
        if len (sys.argv) < 2:
            print("no device spec. go search")
            print("the DoraServer service")
        else:
            adr = sys.argv[1]
            print ("Searching for sServer on %s" % addr)
            
    service_matches = find_service( uuid = uuid, address = addr )
    print("services")
    if len(service_matches) == 0:
        print("Server could not be found")
        bluetooth_online = False
        #sys.exit(0)

    sock = None
    #If the bluetooth is online, create a connection to server
    if (bluetooth_online):
        first_match = service_matches[0]
        port = first_match["port"]
        name = first_match["name"]
        host = first_match["host"]

        print("connecting to \"%s\" on %s" % (name, host))
    
        # Create the client socket
        sock=BluetoothSocket( RFCOMM )
        sock.connect((host, port))
        print("connected")
        print("Pi connected to " + name)
    return sock

sensor_value_prev = None
last_laser_value_prev = None


def bluetooth_loop(ir_values, laser_values, gyro_value, steering_cmd_man, mode, pid, num_laser_values):
    sock = blue_connect()
    bluetooth_online = False
    auto_mode = False
    prev_ir = []
    prev_laser = []
    if sock != None:
        bluetooth_online = True
    req = True
    
    forward_down, backward_down, left_down, right_down = False, False, False, False
    global robot_pos#, robot_rot
    #global sensor_value
    global last_laser_value_prev, sensor_value_prev, robot_pos_prev, robot_rot_prev
    global map_prev, map

    speed = {"right": "100", "left": "100", "laser": "100"}
    
    inter = 0
    printDebug = False
    #Sensor value, 1 = topSens, 2 = botSens, vTop = 3, Vbot =4, hTop = 5, hBot = 0
    while True:
        #map = set_block(map, inter+1, 0,0)
        #print(equal2D(map, map_prev))
        if (printDebug):
            print("rob_rot" + str(math.degrees(gv.robot_rot)))
            print("Gyro_Value: " + str(gv.gyro_value))
            print("sensor" + str(gv.sensor_value))
            print("Laser CURRENT curr : " + str(gv.last_laser_value))
            print("laser size : " + str(len(gv.last_laser_value)))
        #print (gv.sensor_value)
        """
        if (forward_down):
            robot_pos = move_in_dir(robot_pos, speed, gv.robot_rot)            
        if (backward_down):
            robot_pos = move_in_dir(robot_pos, -speed, gv.robot_rot)
        if (left_down):
            gv.robot_rot -= gv.robot_rot_speed
        if (right_down):
            gv.robot_rot += gv.robot_rot_speed
        """

        #print(gv.sensor_value)
            
        if (bluetooth_online):
            map_string = str(map)
            map_string = map_string.translate(None, " ")
            map_string = map_string.translate(None, "[")
            map_string = map_string.translate(None, "]")
            map_string = "[" + map_string + "]"
            #Every other iteration of main loop, send request to laptop for instructions.
            if (req):
                req = False
                sock.send("!req#")
                rec_data = str(sock.recv(1024))

                if (len(rec_data) == 0):
                    break
                
                if (rec_data != "none"):
                    if (rec_data == "forward" and not forward_down):
                        forward_down = True
                        steering_cmd_man.put(rec_data)
                        steering_cmd_man.put("speed_left")
                        steering_cmd_man.put("speed_right")
                    elif (rec_data == "backward" and not backward_down):
                        backward_down = True
                        steering_cmd_man.put(rec_data)
                        steering_cmd_man.put("speed_left")
                        steering_cmd_man.put("speed_right")
                    elif (rec_data == "turn_left" and not left_down):
                        left_down = True
                        steering_cmd_man.put(rec_data)
                        steering_cmd_man.put("speed_left")
                        steering_cmd_man.put("speed_right")
                    elif (rec_data == "turn_right" and not right_down):
                        right_down = True
                        steering_cmd_man.put(rec_data)
                        steering_cmd_man.put("speed_left")
                        steering_cmd_man.put("speed_right")
                    elif (rec_data == "stop"):
                        forward_down = False
                        backward_down = False
                        left_down = False
                        right_down = False
                        steering_cmd_man.put(rec_data)
                    elif rec_data == 'manual':
                        if mode.value == 0: mode.value = 1
                        elif mode.value == 1: mode.value = 0
                    elif "pid" in rec_data:
                        parts = rec_data.split("_")
                        with pid.get_lock():
                            if parts[1] == "p":
                                pid[0] = 0
                                pid[1] = float(parts[2])
                            elif parts[1] == "i":
                                pid[0] = 1
                                pid[1] = float(parts[2])
                            elif parts[1] == "d":
                                pid[0] = 2
                                pid[1] = float(parts[2])
                    elif "speed" in rec_data:
                        steering_cmd_man.put(rec_data)
                        parts = rec_data.split("_")
                        if parts[1] == "both":
                            speed["left"] = parts[2]
                            speed["right"] = parts[2]
                        else:
                            speed[parts[1]] = parts[2]
                        
            else:
                if (not auto_mode): req = True

                current_ir = [ir_values[i] for i in range(len(ir_values))]
                                
                if not prev_ir or prev_ir != current_ir:
                    prev_ir = current_ir
                    sock.send("[sens]%s#" % str(current_ir))

                #print(num_laser_values.value)
                if num_laser_values.value <= 520:  # Max number of laser reads
                    current_laser = [laser_values[i] for i in range(num_laser_values.value)]
                    #print(current_laser)
                    if not prev_laser or prev_laser != current_laser:
                        prev_laser = current_laser
                        sock.send("[laser]%s#" % str(current_laser))
                
                """
                #if (last_laser_value_prev != gv.last_laser_value):
                temp_data = "[laser]"
                temp_data += str(gv.last_laser_value)
                temp_data += "#"
                sock.send(temp_data)
                    
                temp_data = "[gyro]"
                temp_data += str(gv.gyro_value)
                temp_data += "#"
                sock.send(temp_data)

                #if not (robot_pos_prev == robot_pos and robot_rot_prev == gv.robot_rot):
                temp_data = "[rob]["
                temp_data += str(robot_pos[0]) + ","
                temp_data += str(robot_pos[1]) + ","
                temp_data += str(gv.robot_rot) + "]"
                temp_data += "#"
                sock.send(temp_data)

                if (map_prev != map):
                    temp_data = "[map]"
                    temp_data += map_string
                    temp_data += "#"
                    sock.send(temp_data)
                """
        #print(equal2D(map, map_prev))
        """last_laser_value_prev = copy.deepcopy(gv.last_laser_value)
        sensor_value_prev = copy.deepcopy(gv.sensor_value)
        robot_pos_prev = robot_pos
        robot_rot_prev = gv.robot_rot
        map_prev = copy.deepcopy(map)"""
    if (bluetooth_online): sock.close()


if __name__ == "__main__":
    bluetooth_loop()
    
