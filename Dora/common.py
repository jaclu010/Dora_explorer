import os

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
