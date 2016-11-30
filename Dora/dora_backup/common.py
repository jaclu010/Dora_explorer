import os

def find_usb(port_id):
	port = ""
        for file in os.listdir("/dev/serial/by-id"):
		if port_id in file:
			symlink = os.path.join("/dev/serial/by-id/", file)
			port = str(os.path.realpath(symlink))
	return port
