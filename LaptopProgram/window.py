from tkinter import *
from tkinter import simpledialog
import math
from time import gmtime, strftime
from bluetooth import *
import threading
import ast
import copy


class ConnectThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        if btConnected:
            connectBluetooth()


class BluetoothThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        if btConnected:
            blue()


connectThread = ConnectThread()
blueThread = BluetoothThread()

# Bluetooth concurrency
btConnected = False
connectedLock = threading.Lock()
messagesLock = threading.Lock()
newMessageQueue = []

# Bluetooth connection
server_sock = BluetoothSocket(RFCOMM)
try:
    server_sock.bind(("", PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]
    uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
    advertise_service(server_sock, "DoraServer",
                      service_id=uuid,
                      service_classes=[uuid, SERIAL_PORT_CLASS],
                      profiles=[SERIAL_PORT_PROFILE],
                      #                     protocols = [ OBEX_UUID ]
                      )
except:
    print("A Bluetooth connection could not be established")
else:
    print("Waiting for connection on RFCOMM channel %d" % port)
    btConnected = True

client_sock = None
client_info = None

# Queue with commands to send to Dora
commandQueue = []
moveState = "stop"

# Mouse button 1 states
m1Down = False
m1DownPos = (0, 0)
m1UpPos = m1DownPos

root = Tk()
root.geometry("1280x720")

# Lists with data from Dora
mapList = []
robList = []
laserList = []


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)

        self.frame = Frame
        self.canvasWidth = 780
        self.canvasHeight = 720
        self.mapArray = []

        self.mDown = False
        self.mPrevDown = m1Down

        self.up = False
        self.mapSize = 25
        self.mapRotation = math.pi / 4
        self.robRotation = math.pi
        self.robotPos = (10, 10)
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

        self.canvasOffX = self.mapSize
        self.canvasOffY = self.mapSize

        self.textBox = self.initText()
        self.initButtons()
        self.cbSensor, self.cbMovement, self.cb_sensor_overview = self.initCheckboxes()
        self.canvUpdate()

    def debugInitMapArray(self):
        # mapArray will always have an equal height and width
        # 0 == undefined block, #1 == empty block, #2 == wall
        self.canvasList = []
        for y in range(0, 21):
            a = []
            for x in range(0, 21):
                val = "0"
                a.append(val)
            self.mapArray.append(a)

    def initCheckboxes(self):
        self.cbSensorVar = IntVar()
        cbSensor = Checkbutton(self, text="Show sensor data", variable=self.cbSensorVar,
                               command=self.cbSensorToggle)
        cbSensor.place(x=0, y=460)

        self.cbMovementVar = IntVar()
        cbMovement = Checkbutton(self, text="Show movement data", variable=self.cbMovementVar,
                                 command=self.cbMovementToggle)
        cbMovement.place(x=120, y=460)

        self.cb_sensor_overview_var = IntVar()
        cb_sensor_overview = Checkbutton(self, text="Show sensor overview", variable = self.cb_sensor_overview_var,
                                         command = self.cb_sensor_overview_toggle)
        cb_sensor_overview.place(x= 263, y = 460)

        return cbSensor, cbMovement, cb_sensor_overview

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

        buttonBothSpeeds = Button(self, command=lambda: self.setSpeed(0), bg=buttonColor,
                                  activebackground=buttonActiveColor, text="Both Speeds", width=buttonWidth,
                                  height=buttonHeight)
        buttonLeftSpeed = Button(self, command=lambda: self.setSpeed(1), bg=buttonColor,
                                 activebackground=buttonActiveColor,
                                 text="Left Speed", width=buttonWidth, height=buttonHeight)
        buttonRightSpeed = Button(self, command=lambda: self.setSpeed(2), bg=buttonColor,
                                  activebackground=buttonActiveColor,
                                  text="Right Speed", width=buttonWidth, height=buttonHeight)
        buttonTowerSpeed = Button(self, command=lambda: self.setSpeed(3), bg=buttonColor,
                                  activebackground=buttonActiveColor,
                                  text="Tower Speed", width=buttonWidth, height=buttonHeight)

        buttonY = 600

        buttonRight.place(x=365, y=buttonY)
        buttonLeft.place(x=195, y=buttonY)
        buttonForward.place(x=280, y=510)
        buttonBack.place(x=280, y=buttonY)

        buttonBothSpeeds.place(x=10, y=buttonY)
        buttonLeftSpeed.place(x=10, y=510)
        buttonRightSpeed.place(x=95, y=510)
        buttonTowerSpeed.place(x=95, y=buttonY)

    def setSpeed(self, side):
        global commandQueue
        if side == 0:  # both
            ans = simpledialog.askinteger("Speeds", "Enter speed for both motor pairs:")
            if ans is not None and 0 <= ans <= 255:
                commandQueue = ["speed_both_" + str(ans)]
        elif side == 1:  # left
            ans = simpledialog.askinteger("Left Speed", "Enter speed for left motor pair:")
            if ans is not None and 0 <= ans <= 255:
                commandQueue = ["speed_left_" + str(ans)]
        elif side == 2:  # right
            ans = simpledialog.askinteger("Right Speed", "Enter speed for right motor pair:")
            if ans is not None and 0 <= ans <= 255:
                commandQueue = ["speed_right_" + str(ans)]
        elif side == 3:  # tower
            ans = simpledialog.askinteger("Laser Tower Speed", "Enter speed for the laser tower motor:")
            if ans is not None and 0 <= ans <= 255:
                commandQueue = ["speed_tower_" + str(ans)]

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

    def close_window(self):
        self.sensor_window.destroy()
        self.cb_sensor_overview_var.set("0")

    def cb_sensor_overview_toggle(self):
        if self.cb_sensor_overview.getvar(str(self.cb_sensor_overview_var)) == "1":
            print("overview value is 1")
            self.sensor_window = Toplevel(root)
            self.sensor_window.geometry('500x355') #293x322
            self.sensor_window.title("Sensor values")
            self.canvas = Canvas(self.sensor_window, bg="black", width=str(self.canvasWidth), height=str(self.canvasHeight))
            self.canvas.pack()
            dora_picture = PhotoImage(file="dora.png")
            self.label = Label(self.canvas, image=dora_picture)
            self.label.image = dora_picture
            self.label.pack()

            left_sensorsX=125
            upper_sensorsY=10
            right_sensorsX=345
            lower_sensorsY=210

            self.sens0_value, self.sens1_value, self.sens2_value, self.sens3_value,\
            self.sens4_value, self.sens5_value = (StringVar(),)*6

            self.sens_value_dict = {0:self.sens0_value, 1:self.sens1_value, 2:self.sens2_value, 3:self.sens3_value,
                           4:self.sens4_value, 5:self.sens5_value}

            self.sensor0,self.sensor1,self.sensor2,self.sensor3,self.sensor4,self.sensor5 = (0,)*6

            self.sensor_dict = {0: self.sensor0, 1: self.sensor1, 2: self.sensor2, 3: self.sensor3,
                           4: self.sensor4, 5: self.sensor5}

            for i in range(6):
                self.sens_value_dict[i].set("0")
                temp_label = Label(self.sensor_window, text = self.sens_value_dict[i].get())
                self.sensor_dict[i] = temp_label

            self.sensor_dict[0].place(x=left_sensorsX,y=upper_sensorsY)     #Upper left
            self.sensor_dict[1].place(x=left_sensorsX, y=lower_sensorsY)    #Lower left
            self.sensor_dict[2].place(x=right_sensorsX, y=upper_sensorsY)   #Upper right
            self.sensor_dict[3].place(x=right_sensorsX, y=lower_sensorsY)   #Lower right
            self.sensor_dict[4].place(x=235, y=5)                           #Up
            self.sensor_dict[5].place(x=235, y=240)                         #Down

            button = Button(self.sensor_window, text="Close", command=self.close_window)
            button.pack()


        elif self.cb_sensor_overview.getvar(str(self.cb_sensor_overview_var)) == "0":
            self.sensor_window.destroy()
            print("overview value is 0")

    def update_sensor_values(self, messages):
        for i in range(6):
            #If messages contains int, change to str(messages[i])
            self.sens_value_dict[i].set(messages[i])
            self.sensor_dict[i].config(text=self.sens_value_dict[i].get())

    def close(self):
        root.withdraw()
        sys.exit()

    root.bind('<Escape>', close)

    def moveRight(self):
        self.addToMessages("MOVE", "Right")
        global commandQueue
        commandQueue = ["turn_right"]
        # self.robotPos = self.addTuple(self.robotPos, t2)
        # self.robRotation += math.pi / 10

    def moveLeft(self):
        self.addToMessages("MOVE", "Left")
        global commandQueue
        commandQueue = ["turn_left"]
        # self.robotPos = self.addTuple(self.robotPos, t2)
        # self.robRotation -= math.pi / 10

    def moveForward(self):
        self.addToMessages("MOVE", "Forward")
        global commandQueue
        commandQueue = ["forward"]
        # self.robotPos = (self.robotPos[0] - self.robotSpeed * math.cos(self.robRotation), self.robotPos[1])
        # self.robotPos = (self.robotPos[0], self.robotPos[1] - self.robotSpeed * math.sin(self.robRotation))

        # self.robotPos = self.addTuple(self.robotPos, t2)

    def moveBackward(self):
        self.addToMessages("MOVE", "Backward")
        global commandQueue
        commandQueue = ["backward"]

        # self.robotPos = (self.robotPos[0] + self.robotSpeed * math.cos(self.robRotation), self.robotPos[1])
        # self.robotPos = (self.robotPos[0], self.robotPos[1] + self.robotSpeed * math.sin(self.robRotation))

    def stop(self):
        self.addToMessages("MOVE", "Stop")
        global commandQueue
        commandQueue += ["stop"]

    def printToLog(self):
        with open('robotLog.txt', 'a') as file:
            file.write(self.messages[-1][0] + "\t" + self.messages[-1][1])

        self.textBox.config(state=NORMAL)

        if self.messages[-1][0] == "MOVE" and self.cbMovement.getvar(str(self.cbMovementVar)) == "1":
            self.textBox.insert("0.0", self.messages[-1][1])
        elif self.messages[-1][0] == "SENS" and self.cbSensor.getvar(str(self.cbSensorVar)) == "1":
            self.textBox.insert("0.0", self.messages[-1][1])
            if self.cb_sensor_overview.getvar(str(self.cb_sensor_overview_var)) == "1":
                self.update_sensor_values(self.messages[-1][1])

        elif self.messages[-1][0] == "LASER" and self.cbSensor.getvar(str(self.cbSensorVar)) == "1":
            self.textBox.insert("0.0", self.messages[-1][1])
        elif self.messages[-1][0] == "GYRO" and self.cbSensor.getvar(str(self.cbSensorVar)) == "1":
            self.textBox.insert("0.0", self.messages[-1][1])

        self.textBox.config(state=DISABLED)

    def addToMessages(self, type, message):
        self.messages.append((type, strftime("%H:%M:%S", gmtime()) + "\t" + message + "\n"))
        self.printToLog()

    def canvUpdate(self):
        global mapList, robList, m1Down, m1UpPos, m1DownPos
        self.canvasOffX = self.canvasWidth / 2 - (self.mapSize * 20) / 2
        self.canvasOffY = self.canvasHeight / 2 - (self.mapSize * 20) / 2
        self.mDown = m1Down

        if self.mDown:
            a = (m1DownPos[0] - m1UpPos[0])
            a = a / 10000.0
            self.mapRotation += math.degrees(a)

        self.mPrevDown = self.mDown

        if mapList:
            self.mapArray = mapList
        # if robList:
        #    self.robRotation = robList[2]
        #    self.robotPos = (robList[0], robList[1])

        # self.mapRotation -= math.pi / 800
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
                    if self.getMapValue(x, y) == "2":
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

                    # Tuples with coords to box corner
                    leftUp = (x * boxWidth + xOffset, y * boxHeight + yOffset)
                    rightUp = (x * boxWidth + xOffset + boxWidth, y * boxHeight + yOffset)
                    leftDown = (x * boxWidth + xOffset, y * boxHeight + yOffset + boxHeight)
                    rightDown = (x * boxWidth + xOffset + boxWidth, y * boxHeight + yOffset + boxHeight)
                    offset3d = (0, -self.mapSize)
                    # center = (self.canvasWidth / 2 + xOffset, self.canvasHeight / 2 + yOffset)
                    center = ((self.mapSize * 20) / 2 + xOffset, (self.mapSize * 20) / 2 + yOffset)

                    if rotation != 0:
                        leftUp = self.rotatePoint(leftUp, center, rotation)
                        rightUp = self.rotatePoint(rightUp, center, rotation)
                        leftDown = self.rotatePoint(leftDown, center, rotation)
                        rightDown = self.rotatePoint(rightDown, center, rotation)
                    self.drawLine(center[0], center[1], center[0] + 1, center[1] + 1, False)
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
        global laserList

        robotCenter = (self.robotPos[0] * self.mapSize + self.mapSize / 2 + self.canvasOffX,
                       self.robotPos[1] * self.mapSize + self.mapSize / 2 + self.canvasOffY)

        robotWidth = self.mapSize
        robotHeight = self.mapSize / 2
        robotOffset = (0, -self.mapSize / 1.5)
        rOff2 = (0, -self.mapSize / 3)
        xOffset = self.canvasOffX
        yOffset = self.canvasOffY
        robotRotation = self.mapRotation
        center = ((self.mapSize * 20) / 2 + xOffset, (self.mapSize * 20) / 2 + yOffset)

        rLeftUp = (robotCenter[0] - robotWidth / 2, robotCenter[1] - robotHeight / 2)
        rRightUp = (robotCenter[0] + robotWidth / 2, robotCenter[1] - robotHeight / 2)
        rLeftDown = (robotCenter[0] - robotWidth / 2, robotCenter[1] + robotHeight / 2)
        rRightDown = (robotCenter[0] + robotWidth / 2, robotCenter[1] + robotHeight / 2)
        rLeftUpUp = (
            robotCenter[0] - robotWidth / 2 - self.mapSize / 3, robotCenter[1] + robotHeight / 2)
        rRightUpUp = (
            robotCenter[0] - robotWidth / 2 - self.mapSize / 3, robotCenter[1] - robotHeight / 2)

        if robotRotation != 0:
            rLeftUp = self.rotatePoint(rLeftUp, center, robotRotation)
            rRightUp = self.rotatePoint(rRightUp, center, robotRotation)
            rLeftDown = self.rotatePoint(rLeftDown, center, robotRotation)
            rRightDown = self.rotatePoint(rRightDown, center, robotRotation)
            rLeftUpUp = self.rotatePoint(rLeftUpUp, center, robotRotation)
            rRightUpUp = self.rotatePoint(rRightUpUp, center, robotRotation)
            robotCenter = self.rotatePoint(robotCenter, center, robotRotation)

        if self.robRotation != 0:
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

        tempLaser = copy.deepcopy(laserList)
        for i in range(len(tempLaser)):
            step = -2 * math.pi / len(tempLaser)
            p = (robotCenter[0] + tempLaser[i] * math.cos(step * i + self.robRotation + robotRotation),
                 robotCenter[1] + tempLaser[i] * math.sin(step * i + self.robRotation + robotRotation))
            # p = self.rotatePoint(p, center, robotRotation)
            # p = self.rotatePoint(p, oldRobotCenter, self.robRotation)
            self.mapCanvas.create_line(robotCenter[0], robotCenter[1], p[0], p[1])
            # self.drawLine(40, 40, p[0], p[1], False)

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
        if 0 <= x < 21 and 0 <= y < 21:
            return self.mapArray[y][x]
        return None

    def drawLine(self, x1, y1, x2, y2, thick):
        line = self.mapCanvas.create_line(x1, y1, x2, y2)
        self.canvasList.append(line)

        if thick:
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
    connectedLock.acquire()
    global client_sock, client_info
    client_sock, client_info = server_sock.accept()
    connectedLock.release()
    print("Accepted connection on RFCOM channel %d" % port)


def blue():
    connectedLock.acquire()
    global newMessageQueue, mapList, robList, laserList
    data = ""
    try:
        while True:
            data += str(client_sock.recv(4096))[2:-1]

            # if len(data) > 0:
            #    print("received: " + data)

            while data.find('#') != -1:
                # Take out current cmd
                separatorPos = data.find('#')
                cmd = data[:separatorPos]

                # Strip current cmd from data
                data = data[separatorPos + 1:]

                if "!req" not in cmd:
                    messagesLock.acquire()

                    if "sens" in cmd:
                        newMessageQueue += [("SENS", cmd)]
                    elif "gyro" in cmd:
                        newMessageQueue += [("GYRO", cmd)]
                    elif "laser" in cmd:
                        newMessageQueue += [("LASER", cmd)]

                        # Strip [laser] and parse as list
                        cmd = cmd[7:]
                        laserList = ast.literal_eval(cmd)
                    elif "move" in cmd:
                        newMessageQueue += [("MOVE", cmd)]
                    elif "rob" in cmd:
                        newMessageQueue += [("ROB", cmd)]

                        # Strip [rob] and split to list
                        cmd = cmd[5:]
                        robList = ast.literal_eval(cmd)
                    elif "map" in cmd:
                        # We have the whole map
                        newMessageQueue += [("MAP", cmd)]

                        cmd = cmd[5:]
                        l = ast.literal_eval(cmd)

                        mapList = []
                        for y in range(0, 21):
                            l2 = []
                            for x in range(0, 21):
                                l2.append(l[y * 21 + x])
                            mapList.append(l2)

                    messagesLock.release()
                    root.event_generate("<<AddMessage>>")

                else:  # !req received
                    if commandQueue:
                        print(commandQueue[0])
                        client_sock.send(commandQueue.pop(0))
                    else:
                        print("none")
                        client_sock.send("none")
    except IOError:
        pass

    print("disconnected")
    client_sock.close()
    server_sock.close()
    connectedLock.release()
    print("all done")


def main():
    global connectThread, blueThread
    app = Window(root)

    def handleMessageQueue(self):
        messagesLock.acquire()
        if newMessageQueue:
            app.addToMessages(newMessageQueue[0][0], newMessageQueue[0][1])
            newMessageQueue.pop(0)
        messagesLock.release()

    root.bind('<<AddMessage>>', handleMessageQueue)

    def keyDown(e):
        global moveState
        if e.char == 'w' and moveState != "forward":
            moveState = "forward"
            app.moveForward()
        if e.char == 'a' and moveState != "left":
            moveState = "left"
            app.moveLeft()
        if e.char == 's' and moveState != "backward":
            moveState = "backward"
            app.moveBackward()
        if e.char == 'd' and moveState != "right":
            moveState = "right"
            app.moveRight()
        if e.char == 'm':
            global commandQueue
            commandQueue = ["manual"]

    def keyRelease(e):
        global moveState
        moveState = "stop"
        app.stop()

    def mDown(e):
        global m1Down, m1DownPos, m1UpPos
        m1UpPos = m1DownPos
        m1DownPos = (e.x, e.y)
        m1Down = True

    def mUp(e):
        global m1Down
        m1Down = False

    root.bind('<KeyPress>', keyDown)
    root.bind('<KeyRelease>', keyRelease)
    root.bind('<B1-Motion>', mDown)
    root.bind('<ButtonRelease-1>', mUp)

    connectThread.daemon = True
    blueThread.daemon = True

    connectThread.start()
    blueThread.start()

    root.mainloop()

    connectThread.join()
    blueThread.join()


if __name__ == '__main__':
    main()
