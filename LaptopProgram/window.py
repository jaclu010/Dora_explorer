from tkinter import *
from tkinter import simpledialog
import math
from time import gmtime, strftime
from bluetooth import *
import threading
import ast
import copy


class BluetoothThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        blue()

# Bluetooth concurrency
blue_thread = BluetoothThread()
messages_lock = threading.Lock()
new_message_queue = []

# Bluetooth connection
server_sock = BluetoothSocket(RFCOMM)

# Queue with commands to send to Dora
command_queue = []
move_state = "stop"

# Mouse button 1 states
m1_down = False
m1_down_pos = (0, 0)
m1_up_pos = m1_down_pos

#GUI root window
root = Tk()
root.geometry("1280x720")

# Lists with data from Dora
map_list = []
rob_list = []
laser_list = []

# Initiates all variables and windows concerning the GUI.
class Window(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)

        self.frame = Frame
        self.canvas_width = 780
        self.canvas_height = 720
        self.map_array = []

        self.m_down = False
        self.m_prev_down = m1_down

        self.up = False
        self.map_size = 25
        self.map_rotation = math.pi / 4
        self.rob_rotation = math.pi
        self.robot_pos = (10, 10)
        self.robot_speed = 0.5

        self.master = master
        self.master.title("Dora The Explorer")
        self.pack(fill=BOTH, expand=1)
        self.messages = []

        #Create dropdown menu
        menu = Menu(self.master)
        self.master.config(menu=menu)
        file = Menu(menu)
        file.add_command(label="Clear robotLog.txt", command=clear_robot_log)
        file.add_command(label="Help", command=self.show_help)
        file.add_command(label="Exit", command=self.close)
        menu.add_cascade(label="File", menu=file)
        self.map_canvas = self.initCanvas()

        # All canvasobjects are kept in this list
        self.canvas_list = []

        self.canvas_off_x = self.map_size
        self.canvas_off_y = self.map_size

        self.text_box = self.init_text()
        self.init_buttons()
        self.cb_sensor, self.cb_movement, self.cb_sensor_overview = self.init_checkboxes()
        self.canv_update()

    # Sets up a help window
    def show_help(self):
        from tkinter import messagebox
        help_text = 'Keyboard controls:\n\n\
                    W, A, S, D - Drive Dora\n\
                    M - Switch between manual and autonomous mode\n\
                    P, I, O - Set the constants Kp, Ki and Kd respectively for the PID algorithm\n\
                    Esc - Exit the program'
        messagebox.showinfo("Help", help_text)

    def debug_init_map_array(self):
        # mapArray will always have an equal height and width
        # 0 == undefined block, #1 == empty block, #2 == wall
        self.canvas_list = []
        for y in range(0, 31):
            a = []
            for x in range(0, 31):
                val = "0"
                a.append(val)
            self.map_array.append(a)

    #Initialize checkboxes for displaying a sensor overview and toggling
    #what to show in the datalog
    def init_checkboxes(self):
        self.cb_sensor_var = IntVar()
        cb_sensor = Checkbutton(self, text="Show sensor data", variable=self.cb_sensor_var)
        cb_sensor.place(x=0, y=460)

        self.cb_movement_var = IntVar()
        cb_movement = Checkbutton(self, text="Show movement data", variable=self.cb_movement_var,
                                  command=self.cb_movement_toggle)
        cb_movement.place(x=120, y=460)

        self.cb_sensor_overview_var = IntVar()
        cb_sensor_overview = Checkbutton(self, text="Show sensor overview", variable=self.cb_sensor_overview_var,
                                         command=self.cb_sensor_overview_toggle)
        cb_sensor_overview.place(x=263, y=460)

        return cb_sensor, cb_movement, cb_sensor_overview

    #Canvas where the map and the robot's position are drawn
    def initCanvas(self):
        map_canvas = Canvas(self, bg="white", width=str(self.canvas_width), height=str(self.canvas_height))
        map_canvas.place(x=500, y=0)
        self.debug_init_map_array()
        return map_canvas

    #Textbox for showing datalog
    def init_text(self):
        data_text_box = Text(self, state=DISABLED, bg="gray62", width="62", height="30")
        data_text_box.place(x=0, y=0)
        # button = Button(dataTextBox, text="Click")
        # dataTextBox.window_create(INSERT, window=button)
        return data_text_box

    #Buttons for steering the robot and to change motors' speed
    def init_buttons(self):
        button_height = 5
        button_width = 10
        button_color = "gray42"
        button_active_color = "gray58"

        button_right = Button(self, command=self.move_right, bg=button_color, activebackground=button_active_color,
                              text="Right", width=button_width, height=button_height)
        button_left = Button(self, command=self.move_left, bg=button_color, activebackground=button_active_color,
                             text="Left", width=button_width, height=button_height)
        button_forward = Button(self, command=self.move_forward, bg=button_color, activebackground=button_active_color,
                                text="Forward", width=button_width, height=button_height)
        button_back = Button(self, command=self.move_backward, bg=button_color, activebackground=button_active_color,
                             text="Backward", width=button_width, height=button_height)
        button_forward_left = Button(self, command=self.move_forward_left, bg=button_color, activebackground=button_active_color,
                             text="Forward \n Left", width=button_width, height=button_height)
        button_forward_right = Button(self, command=self.move_forward_right, bg=button_color, activebackground=button_active_color,
                             text="Forward \n Right", width=button_width, height=button_height)

        button_both_speeds = Button(self, command=lambda: self.set_speed(0), bg=button_color,
                                    activebackground=button_active_color, text="Both Speeds", width=button_width,
                                    height=button_height)
        button_left_speed = Button(self, command=lambda: self.set_speed(1), bg=button_color,
                                   activebackground=button_active_color,
                                   text="Left Speed", width=button_width, height=button_height)
        button_right_speed = Button(self, command=lambda: self.set_speed(2), bg=button_color,
                                    activebackground=button_active_color,
                                    text="Right Speed", width=button_width, height=button_height)
        button_tower_speed = Button(self, command=lambda: self.set_speed(3), bg=button_color,
                                    activebackground=button_active_color,
                                    text="Tower Speed", width=button_width, height=button_height)

        button_y = 600

        button_right.place(x=365, y=button_y)
        button_left.place(x=195, y=button_y)
        button_forward.place(x=280, y=510)
        button_back.place(x=280, y=button_y)
        button_forward_left.place(x=195,y=510)
        button_forward_right.place(x=365, y=510)

        button_both_speeds.place(x=10, y=button_y)
        button_left_speed.place(x=10, y=510)
        button_right_speed.place(x=95, y=510)
        button_tower_speed.place(x=95, y=button_y)

    def set_speed(self, side):
        global command_queue
        if side == 0:  # both
            ans = simpledialog.askinteger("Speeds", "Enter speed for both motor pairs:")
            if ans is not None and 0 <= ans <= 255:
                command_queue = ["speed_both_" + str(ans)]
        elif side == 1:  # left
            ans = simpledialog.askinteger("Left Speed", "Enter speed for left motor pair:")
            if ans is not None and 0 <= ans <= 255:
                command_queue = ["speed_left_" + str(ans)]
        elif side == 2:  # right
            ans = simpledialog.askinteger("Right Speed", "Enter speed for right motor pair:")
            if ans is not None and 0 <= ans <= 255:
                command_queue = ["speed_right_" + str(ans)]
        elif side == 3:  # tower
            ans = simpledialog.askinteger("Laser Tower Speed", "Enter speed for the laser tower motor:")
            if ans is not None and 0 <= ans <= 255:
                command_queue = ["speed_tower_" + str(ans)]

    def add_text(self, text):
        self.text_box.insert(END, text)

    #Called when cb_movement is toggled. Clears the textbox
    def cb_movement_toggle(self):
        if self.cb_movement.getvar(str(self.cb_movement_var)) == "0":
            self.text_box.config(state=NORMAL)
            self.text_box.delete("0.0", END)
            self.text_box.config(state=DISABLED)

    def close_window(self):
        self.sensor_window.destroy()
        self.cb_sensor_overview_var.set("0")

    #Called when cb_sensor_overview is toggled. Creates a window with updating
    #sensor values. Is destroyed when disabled
    def cb_sensor_overview_toggle(self):
        if self.cb_sensor_overview.getvar(str(self.cb_sensor_overview_var)) == "1":
            self.sensor_window = Toplevel(root)
            self.sensor_window.geometry('500x355')  # 293x322
            self.sensor_window.title("Sensor values")
            self.canvas = Canvas(self.sensor_window, bg="black", width=str(self.canvas_width),
                                 height=str(self.canvas_height))
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

    #Update the sensor values displayed in the sensor overview window
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

    def move_right(self):
        self.add_to_messages("MOVE", "Right")
        global command_queue
        command_queue = ["turn_right"]
        # self.robotPos = self.addTuple(self.robotPos, t2)
        # self.robRotation += math.pi / 10

    def move_left(self):
        self.add_to_messages("MOVE", "Left")
        global command_queue
        command_queue = ["turn_left"]
        # self.robotPos = self.addTuple(self.robotPos, t2)
        # self.robRotation -= math.pi / 10

    def move_forward(self):
        self.add_to_messages("MOVE", "Forward")
        global command_queue
        command_queue = ["forward"]
        # self.robotPos = (self.robotPos[0] - self.robotSpeed * math.cos(self.robRotation), self.robotPos[1])
        # self.robotPos = (self.robotPos[0], self.robotPos[1] - self.robotSpeed * math.sin(self.robRotation))

        # self.robotPos = self.addTuple(self.robotPos, t2)

    def move_backward(self):
        self.add_to_messages("MOVE", "Backward")
        global command_queue
        command_queue = ["backward"]

        # self.robotPos = (self.robotPos[0] + self.robotSpeed * math.cos(self.robRotation), self.robotPos[1])
        # self.robotPos = (self.robotPos[0], self.robotPos[1] + self.robotSpeed * math.sin(self.robRotation))

    def move_forward_left(self):
        self.add_to_messages("MOVE", "Forward left")
        global command_queue
        command_queue = ["forward_left"]

    def move_forward_right(self):
        self.add_to_messages("MOVE", "Forward right")
        global command_queue
        command_queue = ["forward_right"]

    def stop(self):
        self.add_to_messages("MOVE", "Stop")
        global command_queue
        command_queue += ["stop"]

    #Writes all sensor and movement data to a log file
    def print_to_log(self):
        with open('robotLog.txt', 'a') as file:
            file.write(self.messages[-1][0] + "\t" + self.messages[-1][1])

        self.text_box.config(state=NORMAL)

        if self.messages[-1][0] == "MOVE" and self.cb_movement.getvar(str(self.cb_movement_var)) == "1":
            self.text_box.insert("0.0", self.messages[-1][1])
        elif self.messages[-1][0] == "SENS" and self.cb_sensor.getvar(str(self.cb_sensor_var)) == "1":
            self.text_box.insert("0.0", self.messages[-1][1])

        elif self.messages[-1][0] == "LASER" and self.cb_sensor.getvar(str(self.cb_sensor_var)) == "1":
            self.text_box.insert("0.0", self.messages[-1][1])
        elif self.messages[-1][0] == "GYRO" and self.cb_sensor.getvar(str(self.cb_sensor_var)) == "1":
            self.text_box.insert("0.0", self.messages[-1][1])

        self.text_box.config(state=DISABLED)

    def add_to_messages(self, type, message):
        if type == "SENS" and self.cb_sensor_overview.getvar(str(self.cb_sensor_overview_var)) == "1":
            # Take only the list of values from the message string
            parts = message.split('[')
            self.update_sensor_values(ast.literal_eval('[' + parts[2]))

        self.messages.append((type, strftime("%H:%M:%S", gmtime()) + "\t" + message + "\n"))
        self.print_to_log()

    def canv_update(self):
        global map_list, rob_list, m1_down, m1_up_pos, m1_down_pos
        self.canvas_off_x = 10 #self.canvas_width / 2 - (self.map_size * 20) / 2
        self.canvas_off_y = 10 #self.canvas_height / 2 - (self.map_size * 20) / 2
        self.m_down = m1_down

        if self.m_down:
            a = (m1_down_pos[0] - m1_up_pos[0])
            a = a / 10000.0
            self.map_rotation += math.degrees(a)

        self.m_prev_down = self.m_down

        if map_list:
            self.map_array = map_list
        # if rob_list:
        #    self.rob_rotation = rob_list[2]
        #    self.robot_pos = (rob_list[0], rob_list[1])

        # self.map_rotation -= math.pi / 800
        self.draw_2dmap()
        self.map_canvas.after(10, self.canv_update)

    def draw_2dmap(self):
        self.clear_canvas()
        x_offset = self.canvas_off_x
        y_offset = self.canvas_off_y
        box_width = box_height = self.map_size
        ez_draw = True
        # rotation in rad, rotate around map center
        rotation = self.map_rotation

        if ez_draw:
            for y in range(0, 31):
                for x in range(0, 31):
                    if self.get_map_value(x, y) == 2:
                        self.draw_box(x * box_width + x_offset, y * box_height + y_offset, box_width, box_height, True)
                    if self.get_map_value(x, y) == 1:
                        self.draw_box(x * box_width + x_offset, y * box_height + y_offset, box_width, box_height, True, "white")
        else:
            """# Now draw with lines
            for y in range(0, 31):
                for x in range(0, 31):
                    cur_val = self.get_map_value(x, y)
                    up_val = self.get_map_value(x, y - 1)
                    down_val = self.get_map_value(x, y + 1)
                    right_val = self.get_map_value(x + 1, y)
                    left_val = self.get_map_value(x - 1, y)

                    # Tuples with coords to box corner
                    left_up = (x * box_width + x_offset, y * box_height + y_offset)
                    right_up = (x * box_width + x_offset + box_width, y * box_height + y_offset)
                    left_down = (x * box_width + x_offset, y * box_height + y_offset + box_height)
                    right_down = (x * box_width + x_offset + box_width, y * box_height + y_offset + box_height)
                    offset3d = (0, -self.map_size)
                    # center = (self.canvasWidth / 2 + xOffset, self.canvasHeight / 2 + yOffset)
                    center = ((self.map_size * 20) / 2 + x_offset, (self.map_size * 20) / 2 + y_offset)

                    if rotation != 0:
                        left_up = self.rotate_point(left_up, center, rotation)
                        right_up = self.rotate_point(right_up, center, rotation)
                        left_down = self.rotate_point(left_down, center, rotation)
                        right_down = self.rotate_point(right_down, center, rotation)
                    self.draw_line(center[0], center[1], center[0] + 1, center[1] + 1, False)
                    ##Current glitch _|"""

            if cur_val == 2:
                # Now we should draw things
                if right_val == 1:
                    self.draw_3d(right_up, right_down, offset3d)
                if up_val == 1:
                    self.draw_3d(left_up, right_up, offset3d)
                if left_val == 1:
                    self.draw_3d(left_down, left_up, offset3d)
                if down_val == 1:
                    self.draw_3d(right_down, left_down, offset3d)
            self.draw_robot()

    def add_tuple(self, t1, t2):
        return (t1[0] + t2[0], t1[1] + t2[1])

    def draw_robot(self):
        global laser_list

        robot_center = (self.robot_pos[0] * self.map_size + self.map_size / 2 + self.canvas_off_x,
                        self.robot_pos[1] * self.map_size + self.map_size / 2 + self.canvas_off_y)

        robot_width = self.map_size
        robot_height = self.map_size / 2
        robot_offset = (0, -self.map_size / 1.5)
        r_off2 = (0, -self.map_size / 3)
        x_offset = self.canvas_off_x
        y_offset = self.canvas_off_y
        robot_rotation = self.map_rotation
        center = ((self.map_size * 20) / 2 + x_offset, (self.map_size * 20) / 2 + y_offset)

        r_left_up = (robot_center[0] - robot_width / 2, robot_center[1] - robot_height / 2)
        r_right_up = (robot_center[0] + robot_width / 2, robot_center[1] - robot_height / 2)
        r_left_down = (robot_center[0] - robot_width / 2, robot_center[1] + robot_height / 2)
        r_right_down = (robot_center[0] + robot_width / 2, robot_center[1] + robot_height / 2)
        r_left_up_up = (robot_center[0] - robot_width / 2 - self.map_size / 3, robot_center[1] + robot_height / 2)
        r_right_up_up = (robot_center[0] - robot_width / 2 - self.map_size / 3, robot_center[1] - robot_height / 2)

        if robot_rotation != 0:
            r_left_up = self.rotate_point(r_left_up, center, robot_rotation)
            r_right_up = self.rotate_point(r_right_up, center, robot_rotation)
            r_left_down = self.rotate_point(r_left_down, center, robot_rotation)
            r_right_down = self.rotate_point(r_right_down, center, robot_rotation)
            r_left_up_up = self.rotate_point(r_left_up_up, center, robot_rotation)
            r_right_up_up = self.rotate_point(r_right_up_up, center, robot_rotation)
            robot_center = self.rotate_point(robot_center, center, robot_rotation)

        if self.rob_rotation != 0:
            r_left_up = self.rotate_point(r_left_up, robot_center, self.rob_rotation)
            r_right_up = self.rotate_point(r_right_up, robot_center, self.rob_rotation)
            r_left_down = self.rotate_point(r_left_down, robot_center, self.rob_rotation)
            r_right_down = self.rotate_point(r_right_down, robot_center, self.rob_rotation)
            r_right_up_up = self.rotate_point(r_right_up_up, robot_center, self.rob_rotation)
            r_left_up_up = self.rotate_point(r_left_up_up, robot_center, self.rob_rotation)
            robot_center = self.rotate_point(robot_center, robot_center, self.rob_rotation)

        self.draw_line(robot_center[0], robot_center[1], robot_center[0] + 2, robot_center[1] + 2, False)
        self.draw_3d(r_left_up, r_right_up, robot_offset)
        self.draw_3d(r_right_up, r_right_down, robot_offset)
        self.draw_3d(r_right_down, r_left_down, robot_offset)
        self.draw_3d(r_left_down, r_left_up, robot_offset)
        self.draw_3d(r_left_down, r_left_up_up, r_off2)
        self.draw_3d(r_left_up_up, r_right_up_up, r_off2)
        self.draw_3d(r_right_up_up, r_left_up, r_off2)
        self.draw_3d(r_left_up, r_left_down, r_off2)

        temp_laser = copy.deepcopy(laser_list)
        for i in range(len(temp_laser)):
            step = -2 * math.pi / len(temp_laser)
            p = (robot_center[0] + temp_laser[i] * math.cos(step * i + self.rob_rotation + robot_rotation),
                 robot_center[1] + temp_laser[i] * math.sin(step * i + self.rob_rotation + robot_rotation))
            # p = self.rotatePoint(p, center, robot_rotation)
            # p = self.rotatePoint(p, oldRobotCenter, self.robRotation)
            self.map_canvas.create_line(robot_center[0], robot_center[1], p[0], p[1])
            # self.draw_line(40, 40, p[0], p[1], False)

    def draw_3d(self, p1, p2, offset):
        # self.draw_line(p1[0], p1[1], p1[0] + offset[0], p1[1] - offset[1], False)

        self.draw_line(p1[0], p1[1], p2[0], p2[1], False)

        self.draw_line(p1[0], p1[1], p1[0] + offset[0], p1[1] + offset[1], False)
        self.draw_line(p1[0] + offset[0], p1[1] + offset[1], p2[0] + offset[0], p2[1] + offset[1], False)

    def rotate_point(self, p1, p2, angle):
        # rotate p1 around p2
        newX = p2[0] + (p1[0] - p2[0]) * math.cos(angle) - (p1[1] - p2[1]) * math.sin(angle)
        newY = p2[1] + (p1[0] - p2[0]) * math.sin(angle) + (p1[1] - p2[1]) * math.cos(angle)

        ans = (newX, newY)
        return ans

    def get_map_value(self, x, y):
        if 0 <= x < 31 and 0 <= y < 31:
            return self.map_array[y][x]
        return None

    def draw_line(self, x1, y1, x2, y2, thick):
        line = self.map_canvas.create_line(x1, y1, x2, y2)
        self.canvas_list.append(line)

        if thick:
            line1 = self.map_canvas.create_line(x1 - 1, y1 - 1, x2 - 1, y2 - 1)
            self.canvas_list.append(line1)
            line2 = self.map_canvas.create_line(x1 + 1, y1 + 1, x2 + 1, y2 + 1)
            self.canvas_list.append(line2)

    def draw_box(self, x, y, w, h, f, color ="blue"):
        # draws a box at x,y with height h and width w. f = boolean. fill if true
        if not f:
            self.draw_line(x, y, x + w, y, False)
            self.draw_line(x + w, y, x + w, y + h, False)
            self.draw_line(x + w, y + h, x, y + h, False)
            self.draw_line(x, y + h, x, y, False)
        else:
            self.map_canvas.create_rectangle(x, y, x + w, y + h, fill=color)

    def clear_canvas(self):
        self.map_canvas.delete(ALL)
        self.canvas_list = []

def clear_robot_log():
    open('robotLog.txt', 'w').close()


def blue():
    global server_sock, new_message_queue, map_list, rob_list, laser_list
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
                    separator_pos = data.find('#')
                    cmd = data[:separator_pos]

                    # Strip current cmd from data
                    data = data[separator_pos + 1:]

                    if "!req" not in cmd:
                        messages_lock.acquire()

                        if "sens" in cmd:
                            new_message_queue += [("SENS", cmd)]
                        elif "gyro" in cmd:
                            new_message_queue += [("GYRO", cmd)]
                        elif "laser" in cmd:
                            new_message_queue += [("LASER", cmd)]

                            # Strip [laser] and parse as list
                            cmd = cmd[7:]
                            laser_list = ast.literal_eval(cmd)
                        elif "move" in cmd:
                            new_message_queue += [("MOVE", cmd)]
                        elif "rob" in cmd:
                            new_message_queue += [("ROB", cmd)]

                            # Strip [rob] and split to list
                            cmd = cmd[5:]
                            rob_list = ast.literal_eval(cmd)
                        elif "map" in cmd:
                            # We have the whole map
                            new_message_queue += [("MAP", cmd)]

                            cmd = cmd[5:]
                            l = ast.literal_eval(cmd)

                            map_list = []
                            
                            for y in range(0, 31):
                                l2 = []
                                for x in range(0, 31):
                                    l2.append(l[y * 31 + x])
                                map_list.append(l2)
                        print(str(map_list))
                        messages_lock.release()
                        root.event_generate("<<AddMessage>>")

                    else:  # !req received
                        if command_queue:
                            print(command_queue[0])
                            client_sock.send(command_queue.pop(0))
                        else:
                            client_sock.send("none")
        except IOError:
            pass

        print("Client disconnected")
        client_sock.close()


def main():
    app = Window(root)
    root.iconbitmap("dora.ico")

    def handle_message_queue(self):
        messages_lock.acquire()
        if new_message_queue:
            app.add_to_messages(new_message_queue[0][0], new_message_queue[0][1])
            new_message_queue.pop(0)
        messages_lock.release()

    root.bind('<<AddMessage>>', handle_message_queue)

    def key_down(e):
        global move_state, command_queue
        if e.char == 'w' and move_state != "forward":
            move_state = "forward"
            app.move_forward()
        if e.char == 'a' and move_state != "left":
            move_state = "left"
            app.move_left()
        if e.char == 's' and move_state != "backward":
            move_state = "backward"
            app.move_backward()
        if e.char == 'd' and move_state != "right":
            move_state = "right"
            app.move_right()
        if e.char == 'q' and move_state != "forward left":
            move_state = "forward_left"
            app.move_forward_left()
        if e.char == 'e' and move_state != "forward right":
            move_state = "forward_right"
            app.move_forward_right()
        if e.char == 'm':
            command_queue = ["manual"]
        if e.char == 'p':
            ans = simpledialog.askfloat("Kp", "Enter proportional constant Kp:")
            if ans is not None:
                command_queue = ["pid_p_" + str(ans)]
        if e.char == 'i':
            ans = simpledialog.askfloat("Ki", "Enter integral constant Ki:")
            if ans is not None:
                command_queue = ["pid_i_" + str(ans)]
        if e.char == 'o':
            ans = simpledialog.askfloat("Kd", "Enter derivative constant Kd:")
            if ans is not None:
                command_queue = ["pid_d_" + str(ans)]

    def key_release(e):
        global move_state
        move_state = "stop"
        app.stop()

    def m_down(e):
        global m1_down, m1_down_pos, m1_up_pos
        m1_up_pos = m1_down_pos
        m1_down_pos = (e.x, e.y)
        m1_down = True

    def m_up(e):
        global m1_down
        m1_down = False

    root.bind('<KeyPress>', key_down)
    root.bind('<KeyRelease>', key_release)
    root.bind('<B1-Motion>', m_down)
    root.bind('<ButtonRelease-1>', m_up)

    global blue_thread
    blue_thread.daemon = True
    blue_thread.start()

    root.mainloop()

    blue_thread.join()

if __name__ == '__main__':
    main()
