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
        self.lines_score = []
        self.goodr = []
        self.vector_x = []
        self.vector_y = []
        self.intersections = []
        self.fixval = 0

    #update all values so it corresponds to laser_array
    def update_laser(self, l_array):
        self.laser_array = l_array
        self.fixval = self.get_fix_value()
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
        if (i < self.line_size()): 
            if (i < 0): i = self.size() - 1 + i
            return self.lines[i]
        return None

    #returns the value at index i of laser_array
    def get_value(self, i):
        i = self.fixi(i)
        if (i < self.size() ):
            if (i < 0): i = self.size() - 1 + i
            return self.laser_array[i]
        return None

    def get_true_value(self, i):
        if (i < self.size() ): 
            if (i < 0): i = self.size() - 1 + i
            return self.laser_array[i]
        return None


    def fixi(self, i):
        i += self.fixval
        if (i >= self.size()): i = i - self.size()
        return i

    # returns the angle (in radians) of laser reading at position i
    def get_angle(self, i):
        if (i < 0): i = self.size() - 1 + i
        i = self.fixi(i)
        step = 2*math.pi / self.size()
        corr = math.radians(7)
        angle = (i * step) - corr
        if (angle < math.radians(0)):
            angle = math.radians(360) - abs(i*step - corr)
        return angle

    def get_true_angle(self, i):
        if (i < 0): i = self.size() - 1 + i
        step = 2*math.pi / self.size()
        corr = math.radians(7)
        angle = (i * step) - corr
        if (angle < math.radians(0)):
            angle = math.radians(360) - abs(i*step - corr)
        return angle


    def get_fix_value(self):
        i = 0
        while self.get_true_angle(i) > math.radians(180):
            i += 1
        return i


    #returns the position (tuple) of the laser reading at index i
    def get_laser_pos(self, i):
        if (i < self.size()):
            if (i < 0): i = self.size() - 1 + i
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
        if (i < self.size()):
            if (i < 0): i = self.size() - 1 + i
            previ = i - 1
            if (i == 0):
                previ = self.size() - 1
            v1 = self.get_laser_pos(i)
            v2 = self.get_laser_pos(previ)

            return self.subtract(v1,v2)
        return None

    def get_delta2(self, i):
        if (i < self.size()):
            if (i < 0): i = self.size() - 1 + i
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
        
        d_mean_covar = 1.8
        d_delta_covar = 1.9
        d = 0
        if (abs(self.get_delta_mean(i)[0]) > d_mean_covar and abs(self.get_delta_mean(i)[1]) > d_mean_covar): 
            d = 2
        if (abs(self.get_delta2(i)[0]) > d_delta_covar and abs(self.get_delta2(i)[1]) > d_delta_covar):
            d = 1
        if (self.get_true_value(i) < 2 or self.get_true_value(i) > 10000): 
            d = 3
        
        return d

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
            if (cnt > 10):
                 good_readings.append((i, cnt + i - 1, cnt - 1))
            i += cnt + 1
           
            #if (not (e < self.size() and self.get_dot_value(e) == 0)):i+=1
        
        #print("we done 308 325 16")
        #print(self.size())
        # Merge first and last element if they are next to each other
        if len(good_readings) > 0 and good_readings[-1][1] == self.size() - 1 and good_readings[0][0] == 0:
            good_readings[0] = (
                good_readings[-1][0] - self.size(), good_readings[0][1], good_readings[-1][2] + good_readings[0][2])
            good_readings.pop()

        self.goodr = good_readings
        #if len(good_readings) > 0 and good_readings[-1][1] == self.size() - 1 and good_readings[0][0] == 0:

        #    good_readings[0] = (good_readings[-1][0] - self.size(), good_readings[0][1], good_readings[-1][2] + good_readings[0][2])
        #    good_readings.pop()

        #Calculat the lines
        num_vec = len(good_readings)
        for i in range(num_vec):
            d_nr = good_readings[i][2]
            valX = 0
            valY = 0
            d_distX = 0
            d_distY = 0
            for j in range(good_readings[i][0], good_readings[i][1],1):
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

    def set_intersections(self):
        self.intersections = []

        inter = []

        for v in self.vector_x:
            x1 = v[0]
            x2 = v[2]
            y1 = v[1]
            y2 = v[3]
            for w in self.vector_y:
                x3 = w[0]
                x4 = w[2]
                y3 = w[1]
                y4 = w[3]
                px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / \
                     ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
                py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / \
                     ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
                inter.append((px, py))

        used = []
        val = 50

        for v in inter:
            if (not v in used):
                i = 1
                newv = (v[0], v[1])
                for w in inter:
                    if math.fabs(v[0] - w[0]) <= val and math.fabs(v[1] - w[1]) <= val:
                        newv = (newv[0] + w[0], newv[1] + w[1])
                        i += 1
                        used.append(w)
                newv = (newv[0] / i, newv[1] / i)
                self.intersections.append(newv)
                used.append(v)

        for d in self.intersections:
            c.create_oval(int(d[0]) - 5 + offsetX, int(d[1]) - 5 + offsetY,
                          int(d[0]) + 5 + offsetX, int(d[1]) + 5 + offsetY, fill='maroon')

        all_lines = []
        closest_points = []
        line_score = []
        #self.lines_sore 
        for i in range(len(self.intersections)):
            for j in range(i, len(self.intersections), 1):
                if (self.intersections[i] != self.intersections[j]):
                    p1 = (self.intersections[i][0], self.intersections[i][1])
                    p2 = (self.intersections[j][0], self.intersections[j][1])
                    all_lines.append((p1, p2))

                    x1 = p1[0]
                    y1 = p1[1]
                    x2 = p2[0]
                    y2 = p2[1]
                    score = 0
                    closest_1 = 0
                    closest_2 = 0
                    hypot_a = None
                    hypot_b = None
                    up = False
                    num = 0
                    for k in range(self.size()):
                        pos = self.get_laser_pos(k)
                        x0 = pos[0]
                        y0 = pos[1]
                        d_x1 = abs(x1 - x0) 
                        d_y1 = abs(y1 - y0)
                        d_x2 = abs(x2 - x0)
                        d_y2 = abs(y2 - y1)
                        hypot_1 = math.sqrt(d_x1*d_x1 + d_y1*d_y1)
                        hypot_2 = math.sqrt(d_x2*d_x2 + d_y2*d_y2)
                        dist = abs((y2-y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1) / math.sqrt((y2-y1)*(y2-y1) + (x2-x1)*(x2-x1))
                        if hypot_a == None or hypot_1 < hypot_a:
                            hypot_a = hypot_1
                            closest_1 = k
                        if hypot_b == None or hypot_2 < hypot_b:
                            hypot_b = hypot_2
                            closest_2 = k
                        if dist < 5:
                            score += 1
                    if (score > 10):
                        l = (p1, p2)
                        fac = 1
                        if (closest_1 < closest_2): fac = closest_2 - closest_1

                        if (closest_2 < closest_1): fac = closest_1 - closest_2
                        #print(fac)
                        print(closest_1, closest_2, fac)
                        self.lines_score.append((l, closest_1, closest_2, score/fac, 0))
                        #print(closest_1, closest_2)


        #line score contains (line, closest1(i), closest2(i), score, finalscore)
        """
        for i in range(len(self.lines_score)):

            i0 = self.lines_score[i][0]
            i1 = self.lines_score[i][1]
            i2 = self.lines_score[i][2]
            i3 = self.lines_score[i][3]
            i4 = self.lines_score[i][4]
            print(i1, i2)
            print ()
            if (i == len(self.lines_score)-1):
                i4 = i3 / (self.size() - (i1 - i2))
            elif (i1 != i2):
                i4 = i3 /(i2 - i1)
            print("bejs", i4)

            if (i1 > i2):
                self.lines_score[i] = (i0, i2, i1, i3, i4)
            else:
                self.lines_score[i] = (i0, i1, i2, i3,i4)
        """

        
        """
        0.8247422680412371
        0.07317073170731707
        0.06707317073170732
        0.9381443298969072
        0.8955223880597015
        0.765625

        """
        for ls in self.lines_score:
            l = ls[0]
            print("hehah",ls[3])
            if(ls[4] > 0.7):
                c.create_line(l[0][0] + offsetX, l[0][1] + offsetY, l[1][0] + offsetX, l[1][1] + offsetY)
        sys.exit(0)




    def draw_lines(self):
        line_expansion = 300
        self.vector_x = []
        self.vector_y = []
        for i in range (len(self.goodr)):
            l = self.lines[i]
            p1 = l[0]
            p2 = l[1]
            x0 = p2[0] - line_expansion * p1[0]
            y0 = p2[1] - line_expansion * p1[1]
            x1 = p2[0] + line_expansion * p1[0]
            y1 = p2[1] + line_expansion * p1[1]
            c.create_line(x0 + offsetX, y0 + offsetY, x1 + offsetX, y1 + offsetY, fill="blue")

            _x0 = self.get_laser_pos(self.goodr[i][0])[0]
            _x1 = self.get_laser_pos(self.goodr[i][1])[0]
            _y0 = self.get_laser_pos(self.goodr[i][0])[1]
            _y1 = self.get_laser_pos(self.goodr[i][1])[1]
            c.create_line(_x0 + offsetX, _y0 + offsetY, _x1 + offsetX, _y1 + offsetY, fill='cyan')
            if (abs(p1[0]) < abs(p1[1])):
                self.vector_x.append((x0, y0, x1, y1))
            else:
                self.vector_y.append((x0, y0, x1, y1))

        self.set_intersections()


    def draw_dots(self):
        # Give each point values
        # ----------------------
        # Green - the first reading
        # Red - regular values, to show rotation
        # Yellow - delta_mean triggered
        # Orange - Too high delta values
        # Purple - invalid measurement
        for i in range(self.size()):
            x = self.get_laser_pos(i)[0]
            y = self.get_laser_pos(i)[1]

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
s.laser.update_laser(read_list[1])
las = 0
def draw():
    global s
    global las
    s.laser.update_laser(read_list[las])
    if (las >= len(read_list)):
        las = 0
    #print(s.laser.get_fix_value())
    #sys.exit(0)
    #las += 1
    #for i in range(s.laser.size()):
    #    print (s.laser.get_delta_mean(i))
    #print("oh yeah")
    #sys.exit(0)
    clearCanvas(c)

    s.laser.draw_dots()
    s.laser.draw_lines()


    root.after(10, draw)
root.after(1, draw)
root.mainloop()