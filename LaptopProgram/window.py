#####
#
# window.py
# Updated: 14/12 2016
# Authors: Jonathan Johansson, Martin Lundberg, Johan Nilsson
#
####



from tkinter import *
from tkinter import simpledialog
import math
from time import gmtime, strftime
from bluetooth import *
import threading
import ast
import slam_gui as slam
import copy


class BluetoothThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        blue()


# Bluetooth concurrency
blueThread = BluetoothThread()
messagesLock = threading.Lock()
newMessageQueue = []

# Bluetooth connection
server_sock = BluetoothSocket(RFCOMM)

# Queue with commands to send to Dora
commandQueue = []
moveState = "stop"

# Mouse button 1 states
m1Down = False
m1DownPos = (0, 0)
m1UpPos = m1DownPos

root = Tk()
width = root.winfo_screenwidth()
height = root.winfo_screenheight()
root.geometry(str(width) +"x"+str(height))
#root.geometry("1280x720")

# Lists with data from Dora
mapList = []
robot_pos = [0, 0]
laserList = []


class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)

        self.height = height
        self.width = width
        self.frame = Frame
        self.canvasWidth = self.width*0.64 #780
        self.canvasHeight = self.height
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
        file.add_command(label="Help", command=self.showHelp)
        file.add_command(label="Exit", command=self.close)
        menu.add_cascade(label="File", menu=file)
        self.mapCanvas = self.initCanvas()
        # All canvasobjects are kept in this list
        self.canvasList = []

        self.canvasOffX = self.mapSize
        self.canvasOffY = self.mapSize

        self.textBox = self.initText()
        self.slam_box = self.init_slam_canvas()
        self.slam_grid_box = self.init_slam_grid_canvas()

        self.initButtons()
        self.cbSensor, self.cbMovement, self.cb_sensor_overview, self.cb_slam_overview = self.initCheckboxes()
        self.canvUpdate()

    def showHelp(self):
        from tkinter import messagebox
        helpText = 'Keyboard controls:\n\n\
W, A, S, D - Drive Dora\n\
M - Switch between manual and autonomous mode\n\
P, I, O - Set the constants Kp, Ki and Kd respectively for the PID algorithm\n\
Esc - Exit the program'
        messagebox.showinfo("Help", helpText)

    def debugInitMapArray(self):
        # mapArray will always have an equal height and width
        # 0 == undefined block, #1 == empty block, #2 == wall
        self.canvasList = []
        for y in range(0, 31):
            a = []
            for x in range(0, 31):
                val = 0
                a.append(val)
            self.mapArray.append(a)

    def initCheckboxes(self):
        self.cbSensorVar = IntVar()
        cbSensor = Checkbutton(self, text="Show sensor data", variable=self.cbSensorVar,
                               command=self.cbSensorToggle)
        print(str(self.height))
        print(str(self.width))
        cbSensor.place(x=0, y=460)

        self.cbMovementVar = IntVar()
        cbMovement = Checkbutton(self, text="Show movement data", variable=self.cbMovementVar,
                                 command=self.cbMovementToggle)
        cbMovement.place(x=120, y=460)

        self.cb_sensor_overview_var = IntVar()
        cb_sensor_overview = Checkbutton(self, text="Show sensor overview", variable=self.cb_sensor_overview_var,
                                         command=self.cb_sensor_overview_toggle)
        cb_sensor_overview.place(x=263, y=460)

        self.cb_slam_overview_var = IntVar()
        cb_slam_overview = Checkbutton(self, text="Show laser calculations", variable=self.cb_slam_overview_var,
                                           command=self.cb_slam_overview_toggle)
        cb_slam_overview.place(x=0, y=480)
        return cbSensor, cbMovement, cb_sensor_overview, cb_slam_overview

    def initCanvas(self):
        mapCanvas = Canvas(self, bg="white", width=str(self.canvasWidth), height=str(self.canvasHeight))
        mapCanvas.place(x=500, y=0)
        self.debugInitMapArray()
        return mapCanvas

    def init_slam_canvas(self):
        slam_box = Canvas(self, state = NORMAL, bg="white", width="495", height="455")
        #slam_box.create_rectangle(10,10,100,100,fill = "blue")
        # button = Button(dataTextBox, text="Click")
        # dataTextBox.window_create(INSERT, window=button)
        return slam_box

    def init_slam_grid_canvas(self):
        slam_grid_box = Canvas(self, bg="white", width="300", height="300")
        return slam_grid_box

    def initText(self):
        dataTextBox = Text(self, state=DISABLED, bg="gray62", width="62", height="30")
        dataTextBox.place(x=0, y=0)
        # button = Button(dataTextBox, text="Click")
        # dataTextBox.window_create(INSERT, window=button)
        return dataTextBox

    def initButtons(self):
        buttonHeight = int(self.height*0.0054)
        buttonWidth = int(self.width*0.00695)
        buttonColor = "gray42"
        buttonActiveColor = "gray58"

        buttonRight = Button(self, command=self.moveRight, bg=buttonColor, activebackground=buttonActiveColor,
                             text="Right", width=buttonWidth, height=buttonHeight)
        buttonLeft = Button(self, command=self.moveLeft, bg=buttonColor, activebackground=buttonActiveColor,
                            text="Left", width=buttonWidth, height=buttonHeight)
        buttonForward = Button(self, command=self.moveForward, bg=buttonColor, activebackground=buttonActiveColor,
                               text="Forward", width=buttonWidth, height=buttonHeight)
        buttonBack = Button(self, command=self.moveBackward, bg=buttonColor, activebackground=buttonActiveColor,
                            text="Backward", width=buttonWidth, height=buttonHeight)
        button_forward_left = Button(self, command=self.move_forward_left, bg=buttonColor, activebackground=buttonActiveColor,
                             text="Forward \n Left", width=buttonWidth, height=buttonHeight)
        button_forward_right = Button(self, command=self.move_forward_right, bg=buttonColor, activebackground=buttonActiveColor,
                             text="Forward \n Right", width=buttonWidth, height=buttonHeight)

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

        print(str(buttonRight.winfo_reqwidth()))

        button_first_row = self.height*0.70
        button_second_row = self.height*0.80

        button_size_x = buttonLeft.winfo_reqwidth()
        button_size_y = buttonLeft.winfo_reqheight()


        buttonForward.place(x=self.width * 0.14, y=button_first_row)
        button_forward_left.place(x=self.width*0.2, y=button_first_row)
        button_forward_right.place(x=self.width * 0.26, y=button_first_row)

        buttonRight.place(x=self.width * 0.26, y=button_second_row)
        buttonLeft.place(x=self.width*0.14, y=button_second_row)
        buttonBack.place(x=self.width*0.2, y=button_second_row)

        buttonBothSpeeds.place(x=self.width*0.007, y=button_second_row)
        buttonLeftSpeed.place(x=self.width*0.007, y=button_first_row)
        buttonRightSpeed.place(x=self.width*0.066, y=button_first_row)
        buttonTowerSpeed.place(x=self.width*0.066, y=button_second_row)

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

    def cb_slam_overview_toggle(self):
        if self.cb_slam_overview.getvar(str(self.cb_slam_overview_var)) == "1":
            self.slam_box = self.init_slam_canvas()
            self.slam_box.place(x=0, y=0)
            self.slam_grid_box = self.init_slam_grid_canvas()
            self.slam_grid_box.place(x=500, y=0)
            read= [97, 97, 96, 96, 97, 96, 95, 96, 97, 96, 97, 99, 98, 94, 90, 86, 82, 76, 69, 63, 58, 54, 51, 49, 48, 47, 47, 44, 42, 40, 37, 37, 37, 38, 39, 38, 33, 35, 34, 30, 37, 39, 38, 40, 44, 45, 45, 45, 47, 48, 49, 52, 54, 60, 64, 70, 77, 87, 89, 97, 99, 99, 97, 96, 97, 96, 96, 98, 98, 98, 97, 96, 96, 96, 96, 96, 93, 89, 88, 84, 81, 75, 69, 67, 61, 58, 55, 53, 51, 48, 48, 47, 47, 45, 45, 47, 43, 43, 40, 40, 37, 39, 38, 34, 35, 34, 35, 35, 37, 42, 42, 44, 47, 47, 47, 49, 50, 52, 54, 57, 62, 69, 76, 83, 83, 86, 91, 98, 106, 128, 141, 140, 139, 138, 138, 138, 139, 139, 139, 139, 139, 139, 140, 140, 141, 141, 97, 89, 87, 83, 79, 71, 67, 60, 57, 54, 52, 49, 48, 45, 45, 45, 44, 44, 42, 40, 40, 37, 38, 38, 37, 38, 34, 34, 34, 38, 35, 38, 39, 42, 42, 44, 44, 45, 47, 48, 49, 51, 55, 57, 61, 65, 71, 74, 83, 86, 90, 96, 113, 140, 140, 140, 141, 140, 139, 139, 139, 139, 139, 140, 140, 141, 142, 140, 123, 104, 97, 91, 88, 80, 72, 66, 59, 55, 53, 49, 48, 47, 47, 44, 44, 44, 42, 39, 39, 35, 38, 33, 34, 32, 35, 38, 39, 39, 38, 39, 40, 42, 43, 43, 43, 45, 45, 48, 51, 53, 56, 62, 66, 72, 78, 84, 87, 89, 93, 98, 97, 96]
            #self.update_slam(read)
        elif self.cb_slam_overview.getvar(str(self.cb_slam_overview_var)) == "0":
            self.slam_box.destroy()
            self.slam_grid_box.destroy()

    def close_window(self):
        self.sensor_window.destroy()
        self.cb_sensor_overview_var.set("0")

    def cb_sensor_overview_toggle(self):
        if self.cb_sensor_overview.getvar(str(self.cb_sensor_overview_var)) == "1":
            print("overview value is 1")
            self.sensor_window = Toplevel(root)
            self.sensor_window.geometry('500x355')  # 293x322
            self.sensor_window.title("Sensor values")
            self.canvas = Canvas(self.sensor_window, bg="black", width=str(self.canvasWidth),
                                 height=str(self.canvasHeight))
            self.canvas.pack()
            dora_picture = PhotoImage(file="dora.png")
            self.label = Label(self.canvas, image=dora_picture)
            self.label.image = dora_picture
            self.label.pack()

            left_sensorsX = 125
            upper_sensorsY = 10
            right_sensorsX = 345
            lower_sensorsY = 210

            self.sens0_value, self.sens1_value, self.sens2_value, self.sens3_value, \
            self.sens4_value, self.sens5_value = (StringVar(),) * 6

            self.sens_value_dict = {0: self.sens0_value, 1: self.sens1_value, 2: self.sens2_value, 3: self.sens3_value,
                                    4: self.sens4_value, 5: self.sens5_value}

            self.sensor0, self.sensor1, self.sensor2, self.sensor3, self.sensor4, self.sensor5 = (0,) * 6

            self.sensor_dict = {0: self.sensor0, 1: self.sensor1, 2: self.sensor2, 3: self.sensor3,
                                4: self.sensor4, 5: self.sensor5}

            for i in range(6):
                self.sens_value_dict[i].set("0")
                temp_label = Label(self.sensor_window, text=self.sens_value_dict[i].get())
                self.sensor_dict[i] = temp_label

            self.sensor_dict[0].place(x=left_sensorsX, y=upper_sensorsY)  # Upper left
            self.sensor_dict[1].place(x=left_sensorsX, y=lower_sensorsY)  # Lower left
            self.sensor_dict[2].place(x=right_sensorsX, y=upper_sensorsY)  # Upper right
            self.sensor_dict[3].place(x=right_sensorsX, y=lower_sensorsY)  # Lower right
            self.sensor_dict[4].place(x=235, y=5)  # Up
            self.sensor_dict[5].place(x=235, y=240)  # Down

            button = Button(self.sensor_window, text="Close", command=self.close_window)
            button.pack()

        elif self.cb_sensor_overview.getvar(str(self.cb_sensor_overview_var)) == "0":
            self.sensor_window.destroy()
            print("overview value is 0")

    def update_sensor_values(self, sensor_values):
        sensor_mapping = {0: sensor_values[5],
                         1: sensor_values[4],
                         2: sensor_values[3],
                         3: sensor_values[2],
                         4: sensor_values[0],
                         5: sensor_values[1]}
        for i in range(6):
            # If messages contains int, change to str(messages[i])
            self.sens_value_dict[i].set(sensor_mapping[i])
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

    def move_forward_left(self):
        self.addToMessages("MOVE", "Forward left")
        global commandQueue
        commandQueue = ["forward_left"]

    def move_forward_right(self):
        self.addToMessages("MOVE", "Forward right")
        global commandQueue
        commandQueue = ["forward_right"]

    def stop(self):
        self.addToMessages("MOVE", "Stop")
        global commandQueue
        commandQueue += ["stop"]

    def update_slam(self, laser_values):
        #print(laser_values)
        #self.slam_box.create_rectangle(50,50,10,10, fill ="black")
        slam.mapper(self.slam_box, self.slam_grid_box, laser_values)


    def printToLog(self):
        with open('robotLog.txt', 'a') as file:
            file.write(self.messages[-1][0] + "\t" + self.messages[-1][1])

        self.textBox.config(state=NORMAL)

        if self.messages[-1][0] == "MOVE" and self.cbMovement.getvar(str(self.cbMovementVar)) == "1":
            self.textBox.insert("0.0", self.messages[-1][1])
        elif self.messages[-1][0] == "SENS" and self.cbSensor.getvar(str(self.cbSensorVar)) == "1":
            self.textBox.insert("0.0", self.messages[-1][1])

        elif self.messages[-1][0] == "LASER" and self.cbSensor.getvar(str(self.cbSensorVar)) == "1":
            self.textBox.insert("0.0", self.messages[-1][1])
            self.textBox.insert("0.0", "[robot][" + str(robot_pos[0]) + ", " + str(robot_pos[1]) + "]\n")
        elif self.messages[-1][0] == "GYRO" and self.cbSensor.getvar(str(self.cbSensorVar)) == "1":
            self.textBox.insert("0.0", self.messages[-1][1])

        self.textBox.config(state=DISABLED)

    def addToMessages(self, type, message):
        if type == "SENS" and self.cb_sensor_overview.getvar(str(self.cb_sensor_overview_var)) == "1":
            # Take only the list of values from the message string
            parts = message.split('[')
            self.update_sensor_values(ast.literal_eval('[' + parts[2]))
        elif type == "LASER" and self.cb_slam_overview.getvar(str(self.cb_slam_overview_var)) == "1":
            parts = message.split('[')
            self.update_slam(ast.literal_eval('[' + parts[2]))

        self.messages.append((type, strftime("%H:%M:%S", gmtime()) + "\t" + message + "\n"))
        self.printToLog()

    def canvUpdate(self):
        global mapList, robList, m1Down, m1UpPos, m1DownPos
        self.canvasOffX = 10 #self.canvasWidth / 2 - (self.mapSize * 20) / 2
        self.canvasOffY = 10 #self.canvasHeight / 2 - (self.mapSize * 20) / 2
        self.mDown = m1Down


        if self.mDown:
            a = (m1DownPos[0] - m1UpPos[0])
            a = a / 10000.0
            self.mapRotation += math.degrees(a)

        self.mPrevDown = self.mDown

        if mapList:
            self.mapArray = mapList
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
        ezDraw = True
        # rotation in rad, rotate around map center
        rotation = self.mapRotation
        if ezDraw:
            for y in range(0, 31):
                for x in range(0, 31):
                    if self.getMapValue(x, y) == 2:
                        self.drawBox(x * boxWidth + xOffset, y * boxHeight + yOffset, boxWidth, boxHeight, True)
                    if self.getMapValue(x, y) == 1:
                        self.drawBox(x * boxWidth + xOffset, y * boxHeight + yOffset, boxWidth, boxHeight, True, "white")
                    if robot_pos == [x, y]:
                        self.drawBox(x * boxWidth + xOffset, y * boxHeight + yOffset, boxWidth, boxHeight, True, "red")
        else:
            # Now draw with lines
            for y in range(0, 31):
                for x in range(0, 31):
                    curVal = str(self.getMapValue(x, y))
                    upVal = str(self.getMapValue(x, y - 1))
                    downVal = str(self.getMapValue(x, y + 1))
                    rightVal = str(self.getMapValue(x + 1, y))
                    leftVal = str(self.getMapValue(x - 1, y))

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

                    if curVal == "2":
                        # Now we should draw shit

                        if rightVal == "1" or rightVal == "1":
                            self.draw3d(rightUp, rightDown, offset3d)
                        if upVal == "1" or upVal == "1":
                            self.draw3d(leftUp, rightUp, offset3d)
                        if leftVal == "1" or leftVal == "1":
                            self.draw3d(leftDown, leftUp, offset3d)
                        if downVal == "1" or downVal == "1":
                            self.draw3d(rightDown, leftDown, offset3d)
            self.drawRobot()

    def addTuple(self, t1, t2):
        return (t1[0] + t2[0], t1[1] + t2[1])

    def drawRobot(self):
        global laserList

        robotCenter = (self.robotPos[0] * self.mapSize + self.mapSize / 2 + self.canvasOffX,
                       self.robotPos[1] * self.mapSize + self.mapSize / 2 + self.canvasOffY)

        robotWidth = self.mapSize / 2
        robotHeight = self.mapSize / 4 
        robotOffset = (0, -self.mapSize / 2)
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

        """
        Uncomment to display "laser-beams"
        tempLaser = copy.deepcopy(laserList)
        for i in range(len(tempLaser)):
            step = -2 * math.pi / len(tempLaser)
            p = (robotCenter[0] + tempLaser[i] * math.cos(step * i + self.robRotation + robotRotation),
                 robotCenter[1] + tempLaser[i] * math.sin(step * i + self.robRotation + robotRotation))
            # p = self.rotatePoint(p, center, robotRotation)
            # p = self.rotatePoint(p, oldRobotCenter, self.robRotation)
            self.mapCanvas.create_line(robotCenter[0], robotCenter[1], p[0], p[1])
            # self.drawLine(40, 40, p[0], p[1], False)
        """
        
    def draw3d(self, p1, p2, offset):
        # self.drawLine(p1[0], p1[1], p1[0] + offset[0], p1[1] - offset[1], False)
        #print("hello", p1, p2)
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
        if 0 <= x < 31 and 0 <= y < 31:
            return self.mapArray[y][x]
        return 0

    def drawLine(self, x1, y1, x2, y2, thick):
        line = self.mapCanvas.create_line(x1, y1, x2, y2)
        self.canvasList.append(line)

        if thick:
            line1 = self.mapCanvas.create_line(x1 - 1, y1 - 1, x2 - 1, y2 - 1)
            self.canvasList.append(line1)
            line2 = self.mapCanvas.create_line(x1 + 1, y1 + 1, x2 + 1, y2 + 1)
            self.canvasList.append(line2)

    def drawBox(self, x, y, w, h, f, color = "blue"):
        # draws a box at x,y with height h and width w. f = boolean. fill if true
        if not f:
            self.drawLine(x, y, x + w, y, False)
            self.drawLine(x + w, y, x + w, y + h, False)
            self.drawLine(x + w, y + h, x, y + h, False)
            self.drawLine(x, y + h, x, y, False)
        else:
            self.mapCanvas.create_rectangle(x, y, x + w, y + h, fill=color)

    def clearCanvas(self):
        self.mapCanvas.delete(ALL)
        self.canvasList = []


def clearRobotLog():
    open('robotLog.txt', 'w').close()


def blue():
    global server_sock, newMessageQueue, mapList, robot_pos, laserList
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

    while True:
        client_sock, client_info = server_sock.accept()
        print("Accepted connection on RFCOMM channel %d" % port)

        data = ""
        try:
            while True:
                rec = str(client_sock.recv(4096))[2:-1]

                # Check if connection to client is closed
                if not rec:
                    break

                data += rec

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
                            robot_pos = ast.literal_eval(cmd)
                        elif "map" in cmd:
                            # We have the whole map
                            newMessageQueue += [("MAP", cmd)]

                            cmd = cmd[5:]
                            l = ast.literal_eval(cmd)

                            mapList = []
                            
                            for y in range(0, 31):
                                l2 = []
                                for x in range(0, 31):
                                    l2.append(l[y * 31 + x])
                                mapList.append(l2)
                        messagesLock.release()
                        root.event_generate("<<AddMessage>>")

                    else:  # !req received
                        if commandQueue:
                            print(commandQueue[0])
                            client_sock.send(commandQueue.pop(0))
                        else:
                            client_sock.send("none")
        except IOError:
            pass

        print("Client disconnected")
        client_sock.close()


def main():
    app = Window(root)
    root.iconbitmap("dora.ico")

    def handleMessageQueue(self):
        messagesLock.acquire()
        if newMessageQueue:
            app.addToMessages(newMessageQueue[0][0], newMessageQueue[0][1])
            newMessageQueue.pop(0)
        messagesLock.release()

    root.bind('<<AddMessage>>', handleMessageQueue)

    def keyDown(e):
        global moveState, commandQueue
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
        if e.char == 'q' and moveState != "forward left":
            moveState = "forward_left"
            app.move_forward_left()
        if e.char == 'e' and moveState != "forward right":
            moveState = "forward_right"
            app.move_forward_right()
        if e.char == 'm':
            commandQueue = ["manual"]
        if e.char == 'p':
            ans = simpledialog.askfloat("Kp", "Enter proportional constant Kp:")
            if ans is not None:
                commandQueue = ["pid_p_" + str(ans)]
        if e.char == 'i':
            ans = simpledialog.askfloat("Ki", "Enter integral constant Ki:")
            if ans is not None:
                commandQueue = ["pid_i_" + str(ans)]
        if e.char == 'o':
            ans = simpledialog.askfloat("Kd", "Enter derivative constant Kd:")
            if ans is not None:
                commandQueue = ["pid_d_" + str(ans)]

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

    global blueThread
    blueThread.daemon = True
    blueThread.start()

    root.mainloop()

    blueThread.join()


if __name__ == '__main__':
    main()
