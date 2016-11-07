from tkinter import *
import math
from time import gmtime, strftime
from bluetooth import *
import threading


class ConnectThread(threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        connectBluetooth()


class BluetoothThread(threading.Thread):
    def __init__(self, threadID, app):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.app = app

    def run(self):
        blue(self.app)


messagesLock = threading.Lock()
newMessageQueue = []

# Bluetooth connection
server_sock = BluetoothSocket(RFCOMM)
server_sock.bind(("", PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]
uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
advertise_service(server_sock, "SampleServer",
                  service_id=uuid,
                  service_classes=[uuid, SERIAL_PORT_CLASS],
                  profiles=[SERIAL_PORT_PROFILE],
                  #                  protocols = [ OBEX_UUID ]
                  )

print("Waiting for connection on RFCOMM channel %d" % port)

client_sock = None
client_info = None

# Queue with commands to send to Dora
commandQueue = []

root = Tk()
root.geometry("1280x720")


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.frame = Frame
        self.canvasWidth = 780
        self.canvasHeight = 720
        self.mapArray = []
        self.up = False
        self.mapSize = 32
        self.mapRotation = 0
        self.robRotation = math.pi
        self.robotPos = (1, 6)
        self.robotSpeed = 0.5
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
        # All canvasobjects are kept in this list
        self.canvasList = []

        self.canvasOffX = self.mapSize;
        self.canvasOffY = self.mapSize;

        self.textBox = self.initText()
        self.initButtons()
        self.cbSensor, self.cbMovement = self.initCheckboxes()

        self.canvUpdate()

    def debugInitMapArray(self):
        # mapArray will always have an equal height and width
        # 0 == undefined block, #1 == empty block, #2 == wall
        self.canvasList = []
        for y in range(0, 21):
            a = []
            for x in range(0, 21):
                val = "1"
                if ((x == 0 or y == 0) or (x == 20 or y == 20)): val = "2"
                if (x >= 0 and x < 4 and y >= 0 and y < 4): val = "0"
                if (x == 4 and y <= 4) or (y == 4 and x < 4): val = "2"
                if (x == 10 and y == 10): val = "2"
                if (x >= 6 and x < 12 and y >= 17): val = "2"
                if (x > 6 and x < 11 and y >= 18): val = "0"
                if (x > 8 and x < 14 and y < 4): val = "0"
                if (x == 8 and y < 4): val = "2"
                if (x >= 8 and x < 14 and y == 4): val = "2"
                if (x == 14 and y < 4): val = "2"
                if (x >= 10 and x <= 12 and y >= 10 and y <= 12): val = "2"
                a.append(val)
            self.mapArray.append(a)

    def initCheckboxes(self):
        self.cbSensorVar = IntVar()
        cbSensor = Checkbutton(self, text="Show sensor data", variable=self.cbSensorVar,
                               command=self.cbSensorToggle)
        # cbSensor.deselect()
        cbSensor.place(x=0, y=460)
        self.cbMovementVar = IntVar()
        cbMovement = Checkbutton(self, text="Show movement data", variable=self.cbMovementVar,
                                 command=self.cbMovementToggle)
        # cbMovement.deselect()
        cbMovement.place(x=130, y=460)
        return cbSensor, cbMovement

    def initCanvas(self):
        mapCanvas = Canvas(self, bg="white", width=str(self.canvasWidth), height=str(self.canvasHeight))
        mapCanvas.place(x=500, y=0)
        self.debugInitMapArray()
        return mapCanvas

    def initText(self):
        dataTextBox = Text(self, state=DISABLED, bg="gray62", width="62", height="30")
        dataTextBox.place(x=0, y=0)
        # button = Button(dataTextBox, text="Click")
        # dataTextBox.window_create(INSERT, window=button)
        return dataTextBox

    def initButtons(self):
        buttonHeight = 5
        buttonWidth = 10
        buttonColor = "gray42"
        buttonActiveColor = "gray58"

        buttonRight = Button(self, command=self.moveRight, bg=buttonColor, activebackground=buttonActiveColor,
                             text="Right", width=buttonWidth, height=buttonHeight)
        buttonLeft = Button(self, command=self.moveLeft, bg=buttonColor, activebackground=buttonActiveColor,
                            text="Left", width=buttonWidth, height=buttonHeight)
        buttonForward = Button(self, command=self.moveForward, bg=buttonColor, activebackground=buttonActiveColor,
                               text="Forward", width=buttonWidth, height=buttonHeight)
        buttonBack = Button(self, command=self.moveBackward, bg=buttonColor, activebackground=buttonActiveColor,
                            text="Down", width=buttonWidth, height=buttonHeight)

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
        # self.robotPos = self.addTuple(self.robotPos, t2)
        self.robRotation += math.pi / 10

    def moveLeft(self):
        self.addToMessages("MOVE", "Left")
        global commandQueue
        commandQueue += ["left"]
        # self.robotPos = self.addTuple(self.robotPos, t2)
        self.robRotation -= math.pi / 10

    def moveForward(self):
        self.addToMessages("MOVE", "Forward")
        global commandQueue
        commandQueue += ["forward"]

        self.robotPos = (self.robotPos[0] - self.robotSpeed * math.cos(self.robRotation), self.robotPos[1])
        self.robotPos = (self.robotPos[0], self.robotPos[1] - self.robotSpeed * math.sin(self.robRotation))

        # self.robotPos = self.addTuple(self.robotPos, t2)

    def moveBackward(self):
        self.addToMessages("MOVE", "Backward")
        global commandQueue
        commandQueue += ["backward"]

        self.robotPos = (self.robotPos[0] + self.robotSpeed * math.cos(self.robRotation), self.robotPos[1])
        self.robotPos = (self.robotPos[0], self.robotPos[1] + self.robotSpeed * math.sin(self.robRotation))

    def printToLog(self):
        self.textBox.config(state=NORMAL)

        with open('robotLog.txt', 'a') as file:
            file.write(self.messages[-1][0] + "\t" + self.messages[-1][1])

        if (self.messages[-1][0] == "MOVE" and self.cbMovement.getvar(str(self.cbMovementVar)) == "1"):
            self.textBox.insert("0.0", self.messages[-1][1])
        elif (self.messages[-1][0] == "SENS" and self.cbSensor.getvar(str(self.cbSensorVar)) == "1"):
            self.textBox.insert("0.0", self.messages[-1][1])

        self.textBox.config(state=DISABLED)

    def addToMessages(self, type, message):
        self.messages.append((type, strftime("%H:%M:%S", gmtime()) + "\t" + message + "\n"))
        self.printToLog()

    def canvUpdate(self):
        self.mapRotation -= math.pi / 200
        # self.mapRotation = math.pi / 4
        self.draw2DMap()
        self.mapCanvas.after(10, self.canvUpdate)

    def draw2DMap(self):
        self.clearCanvas()
        xOffset = self.canvasOffX
        yOffset = self.canvasOffY
        boxWidth = boxHeight = self.mapSize
        ezDraw = False
        # rotation in rad, rotate around map center
        rotation = self.mapRotation

        if ezDraw:
            for y in range(0, 21):
                for x in range(0, 21):
                    if (self.getMapValue(x, y) == "2"):
                        self.drawBox(x * boxWidth + xOffset, y * boxHeight + yOffset, boxWidth, boxHeight, True)
        else:
            # Now draw with lines
            for y in range(0, 21):
                for x in range(0, 21):
                    curVal = self.getMapValue(x, y)
                    upVal = self.getMapValue(x, y - 1)
                    downVal = self.getMapValue(x, y + 1)
                    rightVal = self.getMapValue(x + 1, y)
                    leftVal = self.getMapValue(x - 1, y)

                    # Tuples with cords to box cornor
                    leftUp = (x * boxWidth + xOffset, y * boxHeight + yOffset)
                    rightUp = (x * boxWidth + xOffset + boxWidth, y * boxHeight + yOffset)
                    leftDown = (x * boxWidth + xOffset, y * boxHeight + yOffset + boxHeight)
                    rightDown = (x * boxWidth + xOffset + boxWidth, y * boxHeight + yOffset + boxHeight)
                    offset3d = (0, -self.mapSize)
                    center = (self.canvasWidth / 2 + xOffset, self.canvasHeight / 2 + yOffset)

                    if (rotation != 0):
                        leftUp = self.rotatePoint(leftUp, center, rotation)
                        rightUp = self.rotatePoint(rightUp, center, rotation)
                        leftDown = self.rotatePoint(leftDown, center, rotation)
                        rightDown = self.rotatePoint(rightDown, center, rotation)

                    ##Current glitch _|

                    if curVal == "2":
                        # Now we should draw shit
                        if rightVal == "1":
                            self.draw3d(rightUp, rightDown, offset3d)
                        if upVal == "1":
                            self.draw3d(leftUp, rightUp, offset3d)
                        if leftVal == "1":
                            self.draw3d(leftDown, leftUp, offset3d)
                        if downVal == "1":
                            self.draw3d(rightDown, leftDown, offset3d)
            self.drawRobot()

    def addTuple(self, t1, t2):
        return (t1[0] + t2[0], t1[1] + t2[1])

    def drawRobot(self):
        robotCenter = (self.robotPos[0] * self.mapSize + self.mapSize / 2 + self.canvasOffX,
                       self.robotPos[1] * self.mapSize + self.mapSize / 2 + self.canvasOffY)
        robotWidth = self.mapSize
        robotHeight = self.mapSize / 2
        robotOffset = (0, -self.mapSize / 1.5)
        rOff2 = (0, -self.mapSize / 3)
        xOffset = 0
        yOffset = 0
        robotRotation = self.mapRotation
        center = (self.canvasWidth / 2 + self.canvasOffX, self.canvasHeight / 2 + self.canvasOffY)
        rLeftUp = (robotCenter[0] - robotWidth / 2 + xOffset, robotCenter[1] - robotHeight / 2 + yOffset)
        rRightUp = (robotCenter[0] + robotWidth / 2 + xOffset, robotCenter[1] - robotHeight / 2 + yOffset)
        rLeftDown = (robotCenter[0] - robotWidth / 2 + xOffset, robotCenter[1] + robotHeight / 2 + yOffset)
        rRightDown = (robotCenter[0] + robotWidth / 2 + xOffset, robotCenter[1] + robotHeight / 2 + yOffset)
        rLeftUpUp = (
        robotCenter[0] - robotWidth / 2 + xOffset - self.mapSize / 3, robotCenter[1] + robotHeight / 2 + yOffset)
        rRightUpUp = (
        robotCenter[0] - robotWidth / 2 + xOffset - self.mapSize / 3, robotCenter[1] - robotHeight / 2 + yOffset)

        if (robotRotation != 0):
            rLeftUp = self.rotatePoint(rLeftUp, center, robotRotation)
            rRightUp = self.rotatePoint(rRightUp, center, robotRotation)
            rLeftDown = self.rotatePoint(rLeftDown, center, robotRotation)
            rRightDown = self.rotatePoint(rRightDown, center, robotRotation)
            rLeftUpUp = self.rotatePoint(rLeftUpUp, center, robotRotation)
            rRightUpUp = self.rotatePoint(rRightUpUp, center, robotRotation)
            robotCenter = self.rotatePoint(robotCenter, center, robotRotation)
        if (self.robRotation != 0):
            rLeftUp = self.rotatePoint(rLeftUp, robotCenter, self.robRotation)
            rRightUp = self.rotatePoint(rRightUp, robotCenter, self.robRotation)
            rLeftDown = self.rotatePoint(rLeftDown, robotCenter, self.robRotation)
            rRightDown = self.rotatePoint(rRightDown, robotCenter, self.robRotation)
            rRightUpUp = self.rotatePoint(rRightUpUp, robotCenter, self.robRotation)
            rLeftUpUp = self.rotatePoint(rLeftUpUp, robotCenter, self.robRotation)
            robotCenter = self.rotatePoint(robotCenter, robotCenter, self.robRotation)

        self.drawLine(robotCenter[0], robotCenter[1], robotCenter[0] + 2, robotCenter[1] + 2, False)
        self.draw3d(rLeftUp, rRightUp, robotOffset)
        self.draw3d(rRightUp, rRightDown, robotOffset)
        self.draw3d(rRightDown, rLeftDown, robotOffset)
        self.draw3d(rLeftDown, rLeftUp, robotOffset)
        self.draw3d(rLeftDown, rLeftUpUp, rOff2)
        self.draw3d(rLeftUpUp, rRightUpUp, rOff2)
        self.draw3d(rRightUpUp, rLeftUp, rOff2)
        self.draw3d(rLeftUp, rLeftDown, rOff2)

    def draw3d(self, p1, p2, offset):
        # self.drawLine(p1[0], p1[1], p1[0] + offset[0], p1[1] - offset[1], False)

        self.drawLine(p1[0], p1[1], p2[0], p2[1], False)

        self.drawLine(p1[0], p1[1], p1[0] + offset[0], p1[1] + offset[1], False)
        self.drawLine(p1[0] + offset[0], p1[1] + offset[1], p2[0] + offset[0], p2[1] + offset[1], False)

    def rotatePoint(self, p1, p2, angle):
        # rotate p1 around p2
        newX = p2[0] + (p1[0] - p2[0]) * math.cos(angle) - (p1[1] - p2[1]) * math.sin(angle)
        newY = p2[1] + (p1[0] - p2[0]) * math.sin(angle) + (p1[1] - p2[1]) * math.cos(angle)

        ans = (newX, newY)
        return ans

    def getMapValue(self, x, y):
        if (x >= 0 and x < 21 and y >= 0 and y < 21): return self.mapArray[y][x]
        return None

    def drawLine(self, x1, y1, x2, y2, thick):
        line = self.mapCanvas.create_line(x1, y1, x2, y2)
        self.canvasList.append(line)

        if (thick):
            line1 = self.mapCanvas.create_line(x1 - 1, y1 - 1, x2 - 1, y2 - 1)
            self.canvasList.append(line1)
            line2 = self.mapCanvas.create_line(x1 + 1, y1 + 1, x2 + 1, y2 + 1)
            self.canvasList.append(line2)

    def drawBox(self, x, y, w, h, f):
        # draws a box at x,y with height h and width w. f = boolean. fill if true
        if not f:
            self.drawLine(x, y, x + w, y, False)
            self.drawLine(x + w, y, x + w, y + h, False)
            self.drawLine(x + w, y + h, x, y + h, False)
            self.drawLine(x, y + h, x, y, False)
        else:
            self.mapCanvas.create_rectangle(x, y, x + w, y + h, fill="blue")

    def clearCanvas(self):
        self.mapCanvas.delete(ALL)
        self.canvasList = []


def clearRobotLog():
    open('robotLog.txt', 'w').close()


def connectBluetooth():
    global client_sock
    global client_info
    client_sock, client_info = server_sock.accept()
    print("Accepted connection on RFCOM channel %d" % port)


def blue(app):
    global newMessageQueue
    mapString = ""
    receivingMap = False
    isReq = False
    try:
        while True:
            data = client_sock.recv(4096)

            if len(data) > 0 and data != b'!req':
                messagesLock.acquire()
                if data[1:5] == b'sens':
                    newMessageQueue += [("SENS", str(data))]
                elif data[1:5] == b'move':
                    newMessageQueue += [("MOVE", str(data))]
                elif data[1:4] == b'map':
                    mapString += str(data)
                    receivingMap = True
                if receivingMap:
                    mapString += str(data)
                    if b'[map_end]' in data:
                        receivingMap = False
                        newMessageQueue += [("MAP", mapString)]
                        mapString = ""

                        if data[-9:] != b'[map_end]':
                            isReq = True

                messagesLock.release()
                print("received [%s]" % data)
                root.event_generate("<<AddMessage>>")

            if data == b'!req' or isReq:
                isReq = False
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

    def handleMessageQueue(self):
        messagesLock.acquire()
        print("Queue: " + str(newMessageQueue))
        if newMessageQueue:
            app.addToMessages(newMessageQueue[0][0], newMessageQueue[0][1])
            newMessageQueue.pop(0)
        messagesLock.release()

    root.bind('<<AddMessage>>', handleMessageQueue)

    connectThread = ConnectThread(1)
    connectThread.start()
    connectThread.join()

    blueThread = BluetoothThread(2, app)
    blueThread.start()

    root.mainloop()
    blueThread.join()


if __name__ == '__main__':
    main()
