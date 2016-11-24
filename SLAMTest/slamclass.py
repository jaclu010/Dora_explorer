import math
import time
from tkinter import *
# from scipy.optimize import curve_fit
# import numpy as np
offsetX = 200
offsetY = 200

with open("slamfixed2.txt", "r") as f:
    a = f.readlines()

read_list = []

root = Tk()
root.title("SLAM DUNKKK")
width = 400
height = 400
c = Canvas(root, width=400, height=400)
c2 = Canvas(root, width=400, height=400)
c.pack(side=LEFT)
c2.pack(side=RIGHT)

for e in a:
    e = e[:-1]
    e = e.replace(",", "")
    e = e.replace("[", "")
    e = e.replace("]", "")
    inner = e.split()
    inner2 = []
    for char in inner:
        inner2.append(int(float(char)))
    # inner = list(map(int(float), inner))
    read_list.append(inner2)

def clearCanvas(canvas):
    canvas.delete(ALL)

def pointlength(p1, p2):
    # returns the length between to points
    return (math.sqrt(((p1[0] - p2[0]) * (p1[0] - p2[0])) + (p1[1] - p2[1]) * (p1[1] - p2[1])))
# Function definition for SciPy
def f(x, A, B):
    return A * x + B
def draw_rect(canvas, p1, p2, p3, p4):
    canvas.create_line(p1[0], p1[1], p2[0], p2[1])
    canvas.create_line(p2[0], p2[1], p3[0], p3[1])
    canvas.create_line(p3[0], p3[1], p4[0], p4[1])
    canvas.create_line(p4[0], p4[1], p1[0], p1[1])

class Laser_Data:
    
    def __init__(self):
        self.laser_array = []
        self.lines = []

    #update all values so it corresponds to laser_array
    def update_laser(self, l_array):
        self.laser_array = l_array
        self.good_read()

    #returns laser_array
    def get_laser_array(self):
        return self.laser_array
    #returns the size of laser_array
    def size(self):
        return len(self.laser_array)

    def get_line_array(self):
        return self.lines

    def line_size(self):
        return len(self.lines)

    def get_line(self, i):
        if (i>= 0 and i < self.line_size()): return self.lines[i]
        return None

    #returns the value at index i of laser_array
    def get_value(self, i):
        if (i >= 0 and i < self.size() ): return self.laser_array[i]
        return None

    # returns the angle (in radians) of laser reading at position i
    def get_angle(self, i):
        step = 2*math.pi / self.size()
        corr = math.radians(7)
        return (i * step) - corr

    #returns the position (tuple) of the laser reading at index i
    def get_laser_pos(self, i):
        if (i >= 0 and i < self.size()):

            x = math.cos(self.get_angle(i)) * s.laser.get_value(i)
            y = -math.sin(self.get_angle(i)) * s.laser.get_value(i)
            return (x,y)
        return None


    #Return the vector s*v where s is a scalar, and v is vector
    def multiply(self, s, v):
        if (v == None): return None
        return (s*v[0], s*v[1])

    # returns the new vector v1 + v2
    def add(self, v1, v2):
        if (v1 == None or v2 == None): return None
        return (v1[0] + v2[0], v1[1] + v2[1])

    # returns the new vector v1 - v2
    def subtract(self, v1, v2):
        if (v1 == None or v2 == None): return None
        return (v1[0] - v2[0], v1[1] - v2[1])

    #returns the first delta
    def get_delta(self, i):
        if (i >= 0 and i < self.size()):
            previ = i - 1
            if (i == 0):
                previ = self.size() - 1
            v1 = self.get_laser_pos(i)
            v2 = self.get_laser_pos(previ)
           
            return self.subtract(v1,v2)
        return None

    def get_delta2(self, i):
        if (i >= 0 and i < self.size()):
            previ = i - 1
            if (i == 0):
                previ = self.size() - 1
            v1 = self.get_delta(i)
            v2 = self.get_delta(previ)
           
            return self.subtract(v1,v2)
        return None

    #return the delta mean
    def get_delta_mean(self, i):
        c_x = 0.0
        c_y = 0.0
        if (i > 5):
            c_x += self.get_delta2(i)[0]
            c_y += self.get_delta2(i)[1]
            c_x += self.get_delta2(i-1)[0]
            c_y += self.get_delta2(i-1)[1]
            c_x += self.get_delta2(i-2)[0]
            c_y += self.get_delta2(i-2)[1]
            c_x += self.get_delta2(i-3)[0]
            c_y += self.get_delta2(i-3)[1]
            c_x += self.get_delta2(i-4)[0]
            c_y += self.get_delta2(i-4)[1]
        return (c_x, c_y)    

    #Get the dot_value. Used to filter good and bad dots
    def get_dot_value(self, i):
        if (i >= 0 and i < self.size()):
            d_mean_covar = 1.8
            d_delta_covar = 1.9
            if (abs(self.get_delta_mean(i)[0]) > d_mean_covar and abs(self.get_delta_mean(i)[1]) > d_mean_covar): return 2
            if (abs(self.get_delta2(i)[0]) > d_delta_covar and abs(self.get_delta2(i)[1]) > d_delta_covar): return 1
            if (self.get_value(i) < 2 or self.get_value(i) > 10000): return 3
            return 0
        return None

    def good_read(self):
        #FIX THIS LATER GOOD SHIT IH YEAH
        #I (JOHAN) HAVE NO IDEA WHAT THIS IS, BUT WE SHOULD FIX THIS

        self.lines = []
        good_readings = []
        i = 0
        while i < self.size():
            cnt = 0
            e = i
            while e < self.size() and self.get_dot_value(e) == 0:
                cnt += 1
                e += 1
                if (cnt > 10 and cnt+i < self.size()):
                    print(e, cnt +i )
                    good_readings.append((i, cnt + i - 1, cnt - 1))
                i += cnt + 1
        # Merge first and last element if they are next to each other
        if len(good_readings) > 0 and good_readings[-1][1] == self.size() - 1 and good_readings[0][0] == 0:
            good_readings[0] = (good_readings[-1][0] - self.size(), good_readings[0][1], good_readings[-1][2] + good_readings[0][2])
            good_readings.pop()

        #Calculat the lines
        num_vec = len(good_readings)
        for i in range(num_vec):
            d_nr = good_readings[i][2]
            valX = 0
            valY = 0
            d_distX = 0
            d_distY = 0

            for j in range(good_readings[i][0], good_readings[i][1], 1):
                #print(good_readings[i][0], good_readings[i][1], 1)
                #print(self.size())
                valX += self.get_delta(j)[0]
                valY += self.get_delta(j)[1]
                d_distX += self.get_laser_pos(j)[0]
                d_distY += self.get_laser_pos(j)[1]
            valX /= d_nr
            valY /= d_nr
            d_distX /=d_nr
            d_distY /=d_nr
            self.lines.append( ((valX, valY), (d_distX, d_distY), good_readings[i][2]))

    def draw_lines(self):
        line_expansion = 300
        
        for i in range(self.size()):
            if (self.get_dot_value(i) == 0):
                l = self.get_line(i)
                p1 = l[0]
                p2 = l[1]
                x0 = p2[0] - line_expansion * p1[0]
                y0 = p2[1] - line_expansion * p1[1]
                x1 = p2[0] + line_expansion * p1[0]
                y1 = p2[1] + line_expansion * p1[1]
                c.create_line(x0 + offsetX, y0 + offsetY, x1 + offsetX, y1 + offsetY, fill="blue")


    def draw_dots(self):
        for i in range(self.size()):
            x = self.get_laser_pos(i)[0]
            y = self.get_laser_pos(i)[1]

            # Give each point values
            # ----------------------
            # Green - the first reading
            # Red - regular values, to show rotation
            # Yellow - delta_mean triggered
            # Orange - Too high delta values
            # Purple - invalid measurement

            color = "white"
            if (self.get_dot_value(i) == 0):
                if(i == 0): color = "green"
                elif 5 < i < 20: color = "red"
            elif (self.get_dot_value(i) == 2): color = "yellow"
            elif (self.get_dot_value(i) == 1): color = "orange"
            elif (self.get_dot_value(i) == 3): color = "purple"

            c.create_oval(x + offsetX - 2, y + offsetY - 2, x+offsetX +2, y + offsetY + 2, fill =color)

class Slam:

    def __init__(self):
        #The laser_array contains data of laser readings. 
        self.laser = Laser_Data()
   

s = Slam()
s.laser.update_laser(read_list[2])
las = 0
def draw():
    global s
    global las
    s.laser.update_laser(read_list[las])
    if (las >= len(read_list)):
        las = 0
    #las += 1
    clearCanvas(c)

    s.laser.draw_dots()
    s.laser.draw_lines()


    root.after(10, draw)
root.after(1, draw)
root.mainloop()