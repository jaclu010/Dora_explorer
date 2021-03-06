#####
#
# blueztooth.py
# Updated: 12/14 2016
# Authors: Fredrik Iselius, Martin Lundberg, Johan Nilsson, Niklas Nilsson
#
#####

from common import *
from bluetooth import *
import sys
import time


# Mac adress to server, per default 7C:7A:91:4A:21:D9 (martins dator)
FIXED_PC = True
MARTIN = "7C:7A:91:4A:21:D9" 
NIKLAS = "74:2F:68:69:99:60"
JONATHAN = "60:02:92:95:26:22"

adrs = [JONATHAN, MARTIN, NIKLAS]


def blue_connect():

    """
    Tries to establish connection to the laptop program
    Iterates through several possible mac addresses
    """
    
    # Unique id, should be the same as servers
    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

    service_matches = find_service(uuid=uuid, address=adrs[0])

    i = 0
    # Loop until match found
    while len(service_matches) == 0:
        print("Server could not be found on adr " + adrs[i])
        time.sleep(0.2)
        i = (i + 1)%3
        service_matches = find_service(uuid=uuid, address=adrs[i])

    sock = None
    
    # Connect when match found
    for match in service_matches:
        port = match["port"]
        name = match["name"]
        host = match["host"]
        
        print("connecting to \"%s\" on %s" % (name, host))
        
        # Create the client socket
        sock = BluetoothSocket(RFCOMM)
        sock.connect((host, port))
        print("Dora connected to " + name)
    
    return sock


def bluetooth_loop(ir_values, laser_values, steering_cmd_man, mode, pid, num_laser_values, grid, shared_pos, move_cmd):

    """
    Sends formated map, ir and laser data if the variable req is set to false
    Rquests and receives data over bluetooth if req is set to true
    """

    sock = blue_connect()
    bluetooth_online = False

    if sock:
        bluetooth_online = True

    req = True

    # Previous values
    prev_ir = []
    prev_laser = []
    prev_map_string = ""
    prev_pos = []
    move_cmd_string = ""
    
    forward_down, backward_down, left_down, right_down = (False,) * 4
        
    while True:
        try:
            if bluetooth_online:
                # Every other iteration of main loop, send request to laptop for instructions.
                if req:
                    req = False
                    sock.send("!req#")
                    rec_data = str(sock.recv(1024))

                    if len(rec_data) == 0:
                        break

                    # If data is received
                    if rec_data != "none":
                        # Drives dora forward
                        if rec_data == "forward" and not forward_down:
                            forward_down = True
                            steering_cmd_man.put(rec_data)
                            steering_cmd_man.put("speed_left")
                            steering_cmd_man.put("speed_right")
                    
                        # Drives dora forward and left
                        elif rec_data == "forward_left":
                            steering_cmd_man.put(rec_data)
                    
                        # Drives dora forward and right
                        elif rec_data == "forward_right":
                            steering_cmd_man.put(rec_data)

                        # Drives dora backward
                        elif rec_data == "backward" and not backward_down:
                            backward_down = True
                            steering_cmd_man.put(rec_data)
                            steering_cmd_man.put("speed_left")
                            steering_cmd_man.put("speed_right")
                    
                        # Turns dora to the left
                        elif rec_data == "turn_left" and not left_down:
                            left_down = True
                            steering_cmd_man.put(rec_data)
                            steering_cmd_man.put("speed_left")
                            steering_cmd_man.put("speed_right")

                        # Turns dora to the right
                        elif rec_data == "turn_right" and not right_down:
                            right_down = True
                            steering_cmd_man.put(rec_data)
                            steering_cmd_man.put("speed_left")
                            steering_cmd_man.put("speed_right")

                        # Stops dora
                        elif rec_data == "stop":
                            forward_down, backward_down, left_down, right_down = (False,) * 4
                            steering_cmd_man.put(rec_data)
                    
                        # Switches between manual and auto mode
                        elif rec_data == 'manual':
                            if mode.value == 0:
                                steering_cmd_man.put(rec_data)
                            elif mode.value == 1:
                                mode.value = 0

                        # Changes pid values
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

                        # Changes speed
                        elif "speed" in rec_data:
                            steering_cmd_man.put(rec_data)

                else:
                    req = True

                    # Converts the internal grid to a string
                    map_string = ""
                    with grid.get_lock():
                        map_string = str([grid[i] for i in range(len(grid))])

                
                    current_ir = [ir_values[i] for i in range(len(ir_values))]

                    # Formats and sends IR values
                    if not prev_ir or prev_ir != current_ir:
                        prev_ir = current_ir
                        sock.send("[sens]%s#" % str(current_ir))

                    # Formats and sends Laser reads
                    if num_laser_values.value <= 520:  # Max number of laser reads
                        current_laser = [laser_values[i] for i in range(num_laser_values.value)]
                        if not prev_laser or prev_laser != current_laser:
                            prev_laser = current_laser
                            sock.send("[laser]%s#" % str(current_laser))

                    # Formats and sends the map
                    if prev_map_string != map_string:
                        sock.send("[map]%s#" % map_string)
                        prev_map_string = map_string

                    # Formats and sends current robot position
                    curr_pos = [shared_pos[i] for i in range(len(shared_pos))]
                    if prev_pos != curr_pos:
                        sock.send('[rob]%s#' % str(curr_pos))
                        prev_pos = [curr_pos[i] for i in range(2)]

                    with move_cmd.get_lock():
                        for c in move_cmd.value:
                            move_cmd_string += c
                
                    if move_cmd_string != "":
                        sock.send('[move]%s#' % move_cmd_string)
                        move_cmd_string = ""
                        move_cmd.value = ""
        except:
            sock = blue_connect()

    if bluetooth_online:
        sock.close()
