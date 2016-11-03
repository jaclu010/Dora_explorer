from tkinter import *
from time import gmtime, strftime
from bluetooth import *
import threading

class ConnectThread (threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
    def run(self):
        connectBluetooth()

class BluetoothThread (threading.Thread):
    def __init__(self, threadID, app):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.app = app
    def run(self):
        blue(self.app)

#Bluetooth connection
server_sock = BluetoothSocket(RFCOMM)
server_sock.bind(("", PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

advertise_service(  server_sock, "SampleServer",
                    service_id=uuid,
                    service_classes=[uuid, SERIAL_PORT_CLASS],
                    profiles=[SERIAL_PORT_PROFILE],
                    #				  protocols = [ OBEX_UUID ]
                    )

print("Waiting for connection on RFCOMM channel %d" % port)

client_sock = None
client_info = None

# Queue with commands to send to Dora
commandQueue = []

root = Tk()
root.geometry("1280x720")

class Window(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.master = master
        self.master.title("Dora The Explorer")
        self.pack(fill=BOTH, expand=1)
        self.messages = []

        menu = Menu(self.master)
        self.master.config(menu=menu)

        file = Menu(menu)
        file.add_command(label="Clear robotLog.txt", command=clearRobotLog)
        file.add_command(label="Exit", command=self.close)
        menu.add_cascade(label="File", menu=file)

        self.mapCanvas = self.initCanvas()
        self.textBox = self.initText()
        self.initButtons()
        self.cbSensor, self.cbMovement = self.initCheckboxes()

    def initCheckboxes(self):
        self.cbSensorVar = IntVar()
        cbSensor = Checkbutton(self, text="Show sensor data", variable=self.cbSensorVar,
                               command=self.cbSensorToggle)
        #cbSensor.deselect()
        cbSensor.place(x=0, y=460)

        self.cbMovementVar = IntVar()
        cbMovement = Checkbutton(self, text="Show movement data", variable=self.cbMovementVar,
                                 command=self.cbMovementToggle)
        #cbMovement.deselect()
        cbMovement.place(x=130, y=460)
        return cbSensor, cbMovement

    def initCanvas(self):
        mapCanvas = Canvas(self, bg="red", width="780", height="720")
        mapCanvas.place(x=500, y=0)
        return mapCanvas

    def initText(self):
        dataTextBox = Text(self, state=DISABLED, bg="gray62", width="62", height="30")
        dataTextBox.place(x=0, y=0)

        #button = Button(dataTextBox, text="Click")
        #dataTextBox.window_create(INSERT, window=button)

        return dataTextBox

    def initButtons(self):
        buttonHeight = 5
        buttonWidth = 10
        buttonColor = "gray42"
        buttonActiveColor = "gray58"

        buttonRight = Button(self, command=self.moveRight, bg=buttonColor, activebackground = buttonActiveColor, text="Right", width=buttonWidth, height=buttonHeight)
        buttonLeft = Button(self, command=self.moveLeft, bg=buttonColor, activebackground = buttonActiveColor, text="Left", width=buttonWidth, height=buttonHeight)
        buttonForward = Button(self, command=self.moveForward, bg=buttonColor, activebackground = buttonActiveColor, text="Forward", width=buttonWidth, height=buttonHeight)
        buttonBack = Button(self, command=self.moveBackward, bg=buttonColor, activebackground = buttonActiveColor, text="Down", width=buttonWidth, height=buttonHeight)

        buttonY = 600

        buttonRight.place(x=285, y=buttonY)
        buttonLeft.place(x=115, y=buttonY)
        buttonForward.place(x=200, y=510)
        buttonBack.place(x=200, y=buttonY)

    def addText(self, text):
        self.textBox.insert(END, text)

    def cbSensorToggle(self):
        if self.cbSensor.getvar(str(self.cbSensorVar)) == "1":
            print("Sensor Value is 1")
        elif self.cbSensor.getvar(str(self.cbSensorVar)) == "0":
            print("Sensor Value is 0")

    def cbMovementToggle(self):
        if self.cbMovement.getvar(str(self.cbMovementVar)) == "1":
            print("Movement Value is 1")
        elif self.cbMovement.getvar(str(self.cbMovementVar)) == "0":
            self.textBox.config(state=NORMAL)
            self.textBox.delete("0.0", END)
            self.textBox.config(state=DISABLED)
            print("Movement Value is 0")



    def close(self):
        root.withdraw()
        sys.exit()

    root.bind('<Escape>', close)

    def moveRight(self):
        self.addToMessages("MOVE", "Right")
        global commandQueue
        commandQueue += ["right"]

    def moveLeft(self):
        self.addToMessages("MOVE", "Left")
        global commandQueue
        commandQueue += ["left"]

    def moveForward(self):
        self.addToMessages("MOVE", "Forward")
        global commandQueue
        commandQueue += ["forward"]

    def moveBackward(self):
        self.addToMessages("MOVE", "Backward")
        global commandQueue
        commandQueue += ["backward"]

    def printToLog(self):
        self.textBox.config(state=NORMAL)

        with open('robotLog.txt', 'a') as file:
            file.write(self.messages[-1][0] + "\t" + self.messages[-1][1])

        if (self.messages[-1][0] == "MOVE" and  self.cbMovement.getvar(str(self.cbMovementVar)) == "1"):
            self.textBox.insert("0.0", self.messages[-1][1])
        elif (self.messages[-1][0] == "SENS"):
            print()
        self.textBox.config(state=DISABLED)

    def addToMessages(self, type, message):
        self.messages.append((type, strftime("%H:%M:%S", gmtime()) + "\t" + message + "\n"))
        self.printToLog()

def clearRobotLog():
    open('robotLog.txt', 'w').close()

def connectBluetooth():
    global client_sock
    global client_info
    client_sock, client_info = server_sock.accept()
    print("Accepted connection on RFCOM channel %d" % port)


def blue(app):
    try:
        while True:
            data = client_sock.recv(1024)

            if len(data) > 0:
                app.printToLog(str(data))
                print("received [%s]" % data)

            if data == b'!req':
                if commandQueue:
                    client_sock.send(commandQueue.pop(0))
                else:
                    client_sock.send("none")


    except IOError:
        pass

    print("disconnected")

    client_sock.close()
    server_sock.close()
    print("all done")


def main():
    app = Window(root)

    connectThread = ConnectThread(1)
    connectThread.start()
    connectThread.join()

    blueThread = BluetoothThread(2, app)
    blueThread.start()


    root.mainloop()
    blueThread.join()

if __name__ == '__main__':
    main()