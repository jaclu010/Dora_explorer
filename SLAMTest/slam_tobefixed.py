import math
import time

from tkinter import *
import copy

# from scipy.optimize import curve_fit
# import numpy as np

offsetX = 300
offsetY = 300

with open("slamfixed2.txt", "r") as f:
    a = f.readlines()
read_list = []
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
    # returns the length between two points
    return (math.sqrt(((p1[0] - p2[0]) * (p1[0] - p2[0])) + (p1[1] - p2[1]) * (p1[1] - p2[1])))


# Function definition for SciPy
def f(x, A, B):
    return A * x + B

def getIndex(item):
    return item[2]


def draw_rect(canvas, p1, p2, p3, p4):
    canvas.create_line(p1[0] + offsetX, p1[1] + offsetY, p2[0] + offsetX, p2[1] + offsetY)
    canvas.create_line(p2[0] + offsetX, p2[1] + offsetY, p3[0] + offsetX, p3[1] + offsetY)
    canvas.create_line(p3[0] + offsetX, p3[1] + offsetY, p4[0] + offsetX, p4[1] + offsetY)
    canvas.create_line(p4[0] + offsetX, p4[1] + offsetY, p1[0] + offsetX, p1[1] + offsetY)


root = Tk()
root.title("SLAM DUNKKK")
width = 600
height = 600
c = Canvas(root, width=600, height=600)
c2 = Canvas(root, width=600, height=600)
c3 = Canvas(root, width=600, height=600)
c.pack(side=LEFT)
c3.pack(side=RIGHT)
c2.pack(side=RIGHT)


# Old hardcoded readings
read1 = [68, 66, 66, 66, 67, 67, 67, 69, 70, 72, 72, 76, 79, 83, 83, 88, 92, 95, 95, 102, 100, 100, 95, 94, 91, 91, 90,
         89, 89, 89, 89, 90, 90, 90, 92, 95, 95, 98, 104, 104, 104, 95, 93, 93, 90, 86, 82, 79, 79, 76, 75, 73, 73, 72,
         73, 73, 73, 74, 76, 78, 80, 80, 83, 87, 90, 90, 94, 95, 95, 101, 97, 92, 92, 91, 91, 91, 91, 89, 89, 88, 88,
         87, 88, 89, 80, 91, 91, 91, 91, 91, 95, 94, 94, 92, 85, 81, 81, 77, 75, 71, 69, 69]
read2 = [88, 89, 86, 87, 87, 86, 90, 86, 86, 88, 89, 87, 87, 87, 87, 87, 89, 90, 87, 87, 90, 87, 89, 89, 86, 89, 90, 90,
         91, 91, 90, 88, 92, 90, 90, 90, 92, 91, 94, 96, 95, 99, 100, 101, 99, 98, 94, 96, 92, 92, 92, 89, 84, 89, 91,
         85, 88, 85, 82, 83, 82, 80, 81, 77, 77, 77, 73, 75, 75, 71, 73, 72, 75, 74, 71, 69, 72, 71, 70, 69, 70, 69, 72,
         72, 69, 69, 72, 69, 72, 69, 71, 69, 68, 68, 70, 71, 69, 70, 68, 69, 69, 73, 72, 71, 73, 74, 76, 74, 76, 74, 76,
         77, 78, 80, 79, 84, 82, 85, 87, 86, 87, 85, 86, 90, 89, 88, 94, 90, 93, 94, 93, 93, 93, 93, 96, 98, 98, 98, 99,
         97, 96, 93, 91, 92, 91, 89, 90, 91, 92, 89, 92, 84, 89, 84, 85, 86, 86, 87, 87, 85, 87, 87, 84, 85, 86, 85, 88,
         85, 87, 83, 85, 85, 87, 83, 87, 88, 88, 84, 87, 85, 87, 86, 88, 88, 87, 91, 91, 91, 91, 93, 94, 91, 92, 92, 91,
         92, 93, 93, 95, 95, 98, 97, 95, 97, 95, 95, 92, 90, 87, 88, 80, 82, 82, 82, 80, 81, 78, 81, 74, 73, 74, 69, 72,
         69, 68, 70, 68, 66, 69, 64, 67, 66, 67, 66, 66, 66, 62, 62, 64, 63, 61, 62, 61, 65, 57, 61, 66, 64, 64, 66, 64,
         64, 64, 68, 66, 67, 69, 69, 67, 66, 66, 69, 68, 72, 69, 68, 71, 72, 73, 75, 74, 74, 75, 76, 77, 80, 83, 86, 85,
         81, 85, 86, 88, 86, 89, 95, 94, 94, 94, 93, 94, 96, 99, 101, 97, 98, 97, 96, 94, 94, 93, 91, 92, 93, 90, 91,
         89, 92, 91, 95, 90, 92, 91, 92, 91, 90, 91, 91, 92, 91, 90]
read3 = [91, 91, 87, 89, 87, 89, 88, 88, 85, 89, 87, 86, 87, 90, 90, 90, 90, 88, 89, 90, 89, 91, 89, 90, 92, 92, 91, 93,
         91, 92, 93, 93, 92, 92, 92, 93, 94, 95, 97, 97, 98, 102, 101, 100, 102, 97, 97, 94, 93, 94, 93, 91, 88, 92, 89,
         89, 87, 91, 90, 88, 86, 85, 82, 83, 84, 80, 80, 82, 79, 77, 78, 74, 74, 78, 76, 73, 74, 72, 71, 70, 70, 70, 68,
         72, 71, 71, 72, 69, 76, 69, 69, 72, 68, 68, 67, 69, 68, 69, 72, 71, 67, 70, 71, 74, 72, 72, 73, 76, 75, 76, 78,
         81, 77, 78, 77, 77, 78, 83, 86, 89, 84, 86, 87, 84, 87, 90, 87, 87, 89, 91, 91, 93, 93, 92, 99, 98, 99, 99,
         100,
         96, 96, 93, 94, 93, 91, 91, 90, 90, 91, 89, 92, 93, 90, 87, 89, 89, 88, 86, 85, 84, 85, 84, 86, 87, 86, 86, 89,
         86, 86, 83, 84, 86, 86, 85, 86, 86, 86, 82, 85, 86, 87, 86, 84, 83, 87, 85, 85, 87, 87, 87, 89, 89, 87, 90, 93,
         91, 93, 91, 92, 94, 92, 92, 94, 92, 93, 93, 95, 96, 95, 97, 96, 94, 93, 91, 87, 90, 88, 88, 89, 88, 86, 88, 81,
         80, 79, 78, 76, 75, 73, 74, 77, 70, 71, 72, 73, 69, 70, 71, 71, 67, 66, 69, 69, 65, 66, 68, 64, 67, 62, 64, 65,
         61, 66, 61, 62, 64, 62, 65, 64, 66, 62, 67, 64, 65, 68, 68, 64, 63, 65, 68, 70, 68, 66, 64, 72, 68, 68, 67, 72,
         71, 70, 71, 71, 75, 76, 76, 76, 77, 79, 78, 78, 80, 85, 82, 81, 88, 88, 91, 88, 85, 87, 89, 91, 90, 90, 94, 96,
         95, 97, 96, 99, 98, 99, 96, 94, 93, 91, 92, 91, 92, 89, 89, 89, 91, 91, 92, 92, 90, 88, 89, 88]
read4 = [192, 200, 206, 213, 217, 233, 235, 246, 259, 269, 287, 295, 727, 717, 744, 747, 765, -17, 755, 1188, 1194,
         1187, 1182, 1186, -17, -17, -17, -17, 2082, 1167, 862, 586, 485, 444, 339, 316, 252, 230, 226, 228, 179, 168,
         164, 169, 164, 205, 200, 205, 116, 110, 102, 101, 99, 91, 87, 85, 80, 80, 76, 76, 76, 75, 74, 73, 71, 71, 69,
         70, 69, 67, 66, 65, 66, 64, 61, 61, 59, 61, 61, 59, 56, 58, 57, 59, 55, 60, 54, 54, 53, 54, 59, 53, 55, 53, 51,
         52, 49, 52, 51, 49, 51, 55, 51, 53, 53, 49, 37, 50, 51, 52, 49, 54, 53, 55, 56, 54, 54, 59, 61, 61, 58, 59, 60,
         60, 64, 65, 62, 62, 65, 67, 68, 70, 68, 72, 71, 68, 68, 70, 79, 78, 75, 76, 77, 77, 76, 81, 80, 84, 87, 88, 90,
         92, 96, 99, 100, 105, 111, 122, 127, 134, 139, 145, 151, 156, 162, 171, 180, 189, 200, 103, 101, 105, 108, 322,
         350, 363, 137, 133, 136, 131, -17, 879, 877, 881, 878, 871, 872, 878, 866, 873, 875, 884, 549, 472, 470, 439,
         333, 392, 303, 387, 401, 399, 407, 411, 417, 405, 325, 328, 316, 318, 419, 426, 415, 398, 385, 329, 264, 238,
         193, 162, 168, 315, 306, 304, 159, 149, 147, 146, 147, 275, 273, 268, 263, 258, 251, 248, 244, 240, 239, 235,
         233, 231, 230, 222, 222, 217, 217, 213, 211, 212, 210, 209, 211, 210, 208, 206, 207, 207, 206, 204, 201, 198,
         89, 88, 88, 90, 87, 88, 88, 88, 87, 87, 88, 89, 89, 90, 89, 91, 89, 91, 93, 92, 93, 93, 94, 95, 95, 94, 96, 97,
         97, 98, 100, 99, 102, 103, 105, 108, 107, 110, 112, 113, 117, 116, 118, 120, 121, 125, 126, 128, 129, 129, 134,
         133, 139, 142, 148, 151, 153, 158, 169, 172, 177, 184, 187, 196, 205, 211, 221, 230, 249, 257, 288, 298, 729,
         727, 730, 740, 753]
read = read_list[3]

curr_index = 0
automode = False


def test():
    global curr_index
    global automode
    global offsetX
    global offsetY
    if (automode):
        clearCanvas(c)
        clearCanvas(c2)
        clearCanvas(c3)
        curr_index += 1
    else:
        while 1:
            ins = input("Write f to step forward, or b to step backwards. Write a to enter Automode\n")
            if (ins == "f"):
                clearCanvas(c)
                clearCanvas(c2)
                clearCanvas(c3)
                curr_index += 1
                break
            elif (ins == "b"):
                clearCanvas(c)
                clearCanvas(c2)
                clearCanvas(c3)
                curr_index -= 1
                break
            elif (ins == "a"):
                automode = True
                break
            elif (ins == "o"):
                xs = input("write offsetX")
                ys = input("write offsetY")
                offsetX += int(xs)
                offsetY += int(ys)
                clearCanvas(c)
                clearCanvas(c2)
                clearCanvas(c3)
                break

    if (curr_index >= len(read_list)):
        curr_index = 0
    elif (curr_index < 0):
        curr_index = len(read_list) - 1

    read = read_list[curr_index]

    # Variables
    size = len(read)
    corr = 7.0  # degrees
    step = 360 / size
    cell_size = 40
    min_dist = 40
    d_mean_covar = 11
    d_delta_covar = 1.65
    two_delta_covar = 1.35
    good_reading_count = 3
    angle_deviation_filter = 8
    score_percent_filter = 0.5
    score_filter = 3
    dot_filter_value = 19
    dot_min_dist = 7
    res = []

    # Convert to angles
    for i in range(size):
        angle = (i * step) - corr
        if (angle < 0):
            angle = 360 - abs(i * step - corr)
        res.append((read[i], angle))

    # Move corrected readings to end of array
    curr = res[0][1]
    while curr > 180:
        res.append(res.pop(0))
        curr = res[0][1]

    sin_cos = []
    intersections = []

    # Extract cartesian coordinates
    for j in range(size):
        x = math.cos(math.radians(res[j][1])) * res[j][0]
        y = -math.sin(math.radians(res[j][1])) * res[j][0]
        sin_cos.append((x, y))

    # Calculate delta values
    delta = []
    two_delta = []

    for i in range(size):
        dx = sin_cos[i][0] - sin_cos[i - 1][0]
        dy = sin_cos[i][1] - sin_cos[i - 1][1]
        delta.append((dx, dy))

        dnexti = i + 2
        if dnexti > size-1:
            dnexti -= size
            
        b2x = sin_cos[i-2][0]
        b2y = sin_cos[i-2][1]
        f2x = sin_cos[dnexti][0]
        f2y = sin_cos[dnexti][1]
        len2d = pointlength((f2x, f2y), (b2x, b2y))
        x = abs(b2x-f2x) / len2d
        y = abs(b2y-f2y) / len2d
        two_delta.append(x+y)
        if two_delta[-1] > two_delta_covar:
            intersections.append((sin_cos[i][0], sin_cos[i][1], i))

    # Calculate delta of delta values
    double_delta = []

    for i in range(size):
    
        ddx = delta[i][0] - delta[i - 1][0]
        ddy = delta[i][1] - delta[i - 1][1]
        double_delta.append((ddx, ddy))
        
        nexti = i+1
        if nexti >= size: nexti = 0
        x_b = sin_cos[i-1][0]
        y_b = sin_cos[i-1][1]
        x_f = sin_cos[nexti][0]
        y_f = sin_cos[nexti][1]
        x = sin_cos[i][0]
        y = sin_cos[i][1]
        
        prevp = pointlength((x_b, y_b), (x,y))
        nextp = pointlength((x_f, y_f), (x,y))

        if nextp > 40 or prevp > 40:
            intersections.append((x,y,i))


    # Calculate average delta of deltas
    delta_mean = []

    for i in range(size):
        change_x = 0.0
        change_y = 0.0
        if 1 < i < size-2:
            change_x += double_delta[i][0]
            change_y += double_delta[i][1]
            change_x += double_delta[i - 1][0]
            change_y += double_delta[i - 1][1]
            change_x += double_delta[i + 1][0]
            change_y += double_delta[i + 1][1]
            change_x += double_delta[i - 2][0]
            change_y += double_delta[i - 2][1]
            change_x += double_delta[i + 2][0]
            change_y += double_delta[i + 2][1]
            # change_x /= 5
            # change_y /= 5
        delta_mean.append((change_x, change_y))

    # print(str(i) + ' ' + str(change_x))
    # print(str(i) + ' ' + str(change_y))

    # Draw grid (just for show)


    for i in range(cell_size):
        c.create_line(0, i * cell_size, height, i * cell_size, dash=1)
        c.create_line(0, i * cell_size, height, i * cell_size, dash=1)
        c.create_line(cell_size * i, 0, i * cell_size, width, dash=1)
        c.create_line(cell_size * i, 0, i * cell_size, width, dash=1)
        c.create_oval(offsetX - 5, offsetY - 5, offsetX + 5, offsetY + 5, fill='black')

    # Give each point values
    # ----------------------
    # Green - the first reading
    # Red - regular values, to show rotation
    # Yellow - delta_mean triggered
    # Orange - Too high delta values
    # Purple - invalid measurement
    dots = [None] * size

    for i in range(size):
        # print(str(sin_cos[i][0]) + "   \t   " + str(delta_mean[i]) + "  \t  " + str(double_delta[i]) + "  \t  " + str(res[i]))
        x = sin_cos[i][0]
        y = sin_cos[i][1]
        if i == 0:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='green')
        #elif 5 < i < 20:
        #    c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='red')
        else:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2)
        d = 0
        if abs(delta_mean[i][0]) + abs(delta_mean[i][1]) > d_mean_covar:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='yellow')
            d = 2
        if abs(double_delta[i][0]) > d_delta_covar and abs(double_delta[i][1]) > d_delta_covar:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='orange')
            d = 1
        if two_delta[i] > two_delta_covar:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='magenta')
            d = 4
        if read[i] < min_dist or read[i] > 10000:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='purple')
            d = 3  # Invalid measures

        dots[i] = d

    # Dot value 0 == good value
    # Appended to list
    good_readings = []
    i = 0

    while i < size:
        cnt = 0
        e = i
        while e < size and dots[e] == 0:
            cnt += 1
            e += 1

        if cnt > good_reading_count:
            good_readings.append((i, cnt + i - 1, cnt - 1))

        i += cnt + 1

    # Merge first and last element if they are next to each other
    if len(good_readings) > 0 and good_readings[-1][1] == size - 1 and good_readings[0][0] == 0:
        good_readings[0] = (
            good_readings[-1][0] - size, good_readings[0][1], good_readings[-1][2] + good_readings[0][2])
        good_readings.pop()
        
    # Calculate lines
    num_vectors = len(good_readings)
    lines = []
    ls_res = []

    for i in range(num_vectors):
        d_nr = good_readings[i][2]
        valX = 0
        valY = 0
        d_distX = 0
        d_distY = 0
        # _x = []
        # _y = []
        for j in range(good_readings[i][0], good_readings[i][1], 1):
            valX += delta[j][0]
            valY += delta[j][1]
            d_distX += sin_cos[j][0]
            d_distY += sin_cos[j][1]
            # _x.append(sin_cos[j][0])
            # _y.append(sin_cos[j][1])

        valX /= d_nr
        valY /= d_nr
        d_distX /= d_nr
        d_distY /= d_nr
        normalized = math.sqrt(valX * valX + valY * valY)
        valX /= normalized
        valY /= normalized
        lines.append((valX, valY, d_distX, d_distY, good_readings[i][2]))
        print(valX,valY)

        # x = np.array(_x)
        # y = np.array(_y)
        # A, B = curve_fit(f, x, y)[0]
        # ls_res.append((A, B))
    # Draw lines
    vectors_x = []
    vectors_y = []

    angles = []
    vec_id_x = 0
    vec_id_y = 0

    line_expansion = 200
    for i in range(num_vectors):

        x0 = lines[i][2] - line_expansion * lines[i][0]
        x1 = lines[i][2] + line_expansion * lines[i][0]
        y0 = lines[i][3] - line_expansion * lines[i][1]
        y1 = lines[i][3] + line_expansion * lines[i][1]
        c.create_line(x0 + offsetX, y0 + offsetY, x1 + offsetX, y1 + offsetY, fill='blue')

        _x0 = sin_cos[good_readings[i][0]][0]
        _x1 = sin_cos[good_readings[i][1]][0]
        _y0 = sin_cos[good_readings[i][0]][1]
        _y1 = sin_cos[good_readings[i][1]][1]
        c.create_line(_x0 + offsetX, _y0 + offsetY, _x1 + offsetX, _y1 + offsetY, fill='cyan')
        intersections.append((_x0, _y0, good_readings[i][0]))
        intersections.append((_x1, _y1, good_readings[i][1]))

        if abs(lines[i][0]) < abs(lines[i][1]):
            vectors_x.append((x0, y0, x1, y1))
            #print(lines[i][0])
            angles.append((math.degrees(math.acos(lines[i][0])), vec_id_x, 0))
            vec_id_x += 1
        else:
            vectors_y.append((x0, y0, x1, y1))
            angles.append((math.degrees(math.acos(lines[i][1])), vec_id_y, 1))
            vec_id_y += 1

    angle_deviation = []
    avg_angle = 0
    #print("Vector_x: " + str(vectors_x))
    #print("Vector_y: " + str(vectors_y))
    #print(angles)
    for i in range(len(angles)):
        #avg_angle = 0
        if angles:
            temp_angle = abs(angles[i][0])
            if 45 < temp_angle < 90:
                angle_deviation.append((((90 - temp_angle) % 90, (90 - temp_angle) // 90), angles[i][1], angles[i][2]))
                avg_angle += (90 - temp_angle) % 90
            else:
                angle_deviation.append(((temp_angle % 90, temp_angle // 90), angles[i][1], angles[i][2]))
                avg_angle += temp_angle % 90
        else:
            angle_deviation.append(((None, None), angles[i][1], angles[i][2]))
    
    if angles:
        avg_angle /= len(angles)
            
    #print(angles)
    #print("Angle_deviation: " + str(angle_deviation))
    print(avg_angle)
    rob_rot = 0
    filtered_x = []
    filtered_y = []

    for alpha in angle_deviation:
        if abs(alpha[0][0] - avg_angle) < angle_deviation_filter:
            if alpha[2] == 0:
                filtered_x.append(vectors_x[alpha[1]])
                rob_rot += vectors_x[alpha[1]][0]
            elif alpha[2] == 1:
                filtered_y.append(vectors_y[alpha[1]])
                rob_rot += vectors_y[alpha[1]][0]
        else:
            if alpha[2] == 0:
                c.create_line(vectors_x[alpha[1]][0] + offsetX, vectors_x[alpha[1]][1] + offsetY,
                              vectors_x[alpha[1]][2] + offsetX, vectors_x[alpha[1]][3] + offsetY, fill='red')
            elif alpha[2] == 1:
                c.create_line(vectors_y[alpha[1]][0] + offsetX, vectors_y[alpha[1]][1] + offsetY,
                              vectors_y[alpha[1]][2] + offsetX, vectors_y[alpha[1]][3] + offsetY, fill='red')
    
    nr_good_angles = len(filtered_x) + len(filtered_y)
    if nr_good_angles != 0:
        rob_rot /= nr_good_angles
    else:
        rob_rot = 0

        
    """
            if alpha[2] == 0:

                vectors_x.pop(alpha[1])
                #print(alpha)
            elif alpha[2] == 1:
                print(111, alpha[1])
                c.create_line(vectors_y[alpha[1]][0] + offsetX, vectors_y[alpha[1]][1] + offsetY,
                              vectors_y[alpha[1]][2] + offsetX, vectors_y[alpha[1]][3] + offsetY, fill='red')
                vectors_y.pop(alpha[1])
                #print(alpha)
    """

    # print(vectors_x)
    # print(vectors_y)
    # intersection lines
    # print(lines[0])


    #print(filtered_x)
    #print(filtered_y)
    for v in filtered_x:
        x1 = v[0]
        x2 = v[2]
        y1 = v[1]
        y2 = v[3]
        for w in filtered_y:
            x3 = w[0]
            x4 = w[2]
            y3 = w[1]
            y4 = w[3]

            px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / \
                 ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
            py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / \
                 ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))

            best_len = 10000  # Big number, to be safe
            cur_nr = -10000
            for i in range(size):
                x = sin_cos[i][0]
                y = sin_cos[i][1]
                dx = px - x
                dy = py - y
                hypot = math.sqrt(dx*dx + dy*dy)
                if hypot < best_len:
                    best_len = hypot
                    cur_nr = i
                

            intersections.append((px, py, cur_nr))


    

    # print(intersections)
    filtered_intersections = []
    # Filter intersections outside the grid
    for d in intersections:

        x1 = d[0]
        y1 = d[1]

        for _d in range(size):
            _x1 = sin_cos[_d][0]
            _y1 = sin_cos[_d][1]

            d_x1 = x1 - _x1
            d_y1 = y1 - _y1

            hypot = math.sqrt(d_x1 * d_x1 + d_y1 * d_y1)

            if hypot < dot_min_dist:
                filtered_intersections.append(d)
                break


    used = []
    # Res contains the final normalized points - res is used in the first for loop, changed to dot_averaging
    dot_averaging = []
    # Filter out points near each other

    for v in filtered_intersections:
        if (not v in used):
            i = 1
            newv = (v[0], v[1], v[2])
            for w in filtered_intersections:
                if math.fabs(v[0] - w[0]) <= dot_filter_value and math.fabs(v[1] - w[1]) <= dot_filter_value:
                    newv = (newv[0] + w[0], newv[1] + w[1], newv[2])
                    i += 1
                    used.append(w)
            newv = (newv[0] / i, newv[1] / i, newv[2])
            dot_averaging.append(newv)
            used.append(v)

    #
    # ----------------------------------------------------
    # bad sorting yes, it was, but not now
    all_lines = []
    dot_averaging.sort(key=getIndex)

    # Draw polygon from all normalized points
    for i in range(len(dot_averaging)):
        nexti = i + 1
        if (nexti >= len(dot_averaging)): nexti = 0
        c2.create_line(dot_averaging[i][0] + offsetX, dot_averaging[i][1] + offsetY,
                       dot_averaging[nexti][0] + offsetX, dot_averaging[nexti][1] + offsetY, fill='#ABABAB', width=3)
        all_lines.append((dot_averaging[i][0], dot_averaging[i][1],
                          dot_averaging[nexti][0], dot_averaging[nexti][1], (dot_averaging[i][2], dot_averaging[nexti][2])))
    #
    # ----------------------------------------------------
    #

    # This is the real deal:
    # Draw a line between all mean dots
    # Calculate hit percent of dots on every line

    # Draw all normalized points
    cnt = 0
    for d in dot_averaging:
        c.create_oval(int(d[0]) - 7 + offsetX, int(d[1]) - 7 + offsetY,
                      int(d[0]) + 7 + offsetX, int(d[1]) + 7 + offsetY, fill='maroon')
        c.create_text(int(d[0]) + offsetX, int(d[1]) + offsetY, fill='white', text=str(cnt))
        cnt += 1

    closest_points = []
    line_score = []

    # print(dot_averaging)
    """
    for i in range(len(dot_averaging)):
        for j in range(i, len(dot_averaging), 1):
            if dot_averaging[i] != dot_averaging[j]:
                all_lines.append((dot_averaging[i][0], dot_averaging[i][1],
                                  dot_averaging[j][0], dot_averaging[j][1]))
                c2.create_line(dot_averaging[i][0] + offsetX, dot_averaging[i][1] + offsetY,
                               dot_averaging[j][0] + offsetX, dot_averaging[j][1] + offsetY, fill='#FF6666')
    """
    for l in all_lines:
        score = 0

        closest_1 = l[4][0]
        closest_2 = l[4][1]
        #hypot_a = None
        #hypot_b = None

        x1 = l[0]
        y1 = l[1]
        x2 = l[2]
        y2 = l[3]

        for d in range(size):
            x0 = sin_cos[d][0]
            y0 = sin_cos[d][1]

            #d_x1 = abs(x1 - sin_cos[d][0])
            #d_y1 = abs(y1 - sin_cos[d][1])
            #d_x2 = abs(x2 - sin_cos[d][0])
            #d_y2 = abs(y2 - sin_cos[d][1])

            #hypot_1 = math.sqrt(d_x1 * d_x1 + d_y1 * d_y1)
            #hypot_2 = math.sqrt(d_x2 * d_x2 + d_y2 * d_y2)

            dist = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1) / math.sqrt(
                (y2 - y1) * (y2 - y1) + (x2 - x1) * (x2 - x1))

            #if hypot_a == None or hypot_1 < hypot_a:
                #hypot_a = hypot_1
                #closest_1 = d

            #if hypot_b == None or hypot_2 < hypot_b:
                #hypot_b = hypot_2
                #closest_2 = d

            if dist < 3:
                score += 1
        if score > score_filter:
            closest_points.append((closest_1, closest_2, l))
            line_score.append(score)

    #print(closest_points)
    for i in range(len(closest_points)):
        if closest_points[i][0] >= 0 and closest_points[i][1] < 0:
            closest_points[i] = (closest_points[i][0], size + closest_points[i][0], closest_points[i][2])
    #print(closest_points)
    # print(closest_points)
    # print(line_score)
    final_score = []

    for i in range(len(closest_points)):
        if i == len(closest_points) - 1:
            final_score.append(
                (line_score[i] / (size - (closest_points[i][0] - closest_points[i][1])), closest_points[i]))
        elif closest_points[i][0] != closest_points[i][1]:
            final_score.append((line_score[i] / (closest_points[i][1] - closest_points[i][0]), closest_points[i]))
        #print(final_score[-1][0])

    # Draw score vectors

    c2.create_oval(offsetX - 5, offsetY - 5, 5 + offsetX, 5 + offsetY, fill='black')
    #print(final_score)

    filtered_glas = []
    rotated_lines = []


    for fs in final_score:
        thickness = (fs[0] * 100) // 10
        thickness /= 2
        color = 'red'

        # rob_rot = 30
        ncos = math.cos(math.radians(rob_rot))
        nsin = math.sin(math.radians(rob_rot))
        x1n = fs[1][2][0] * ncos - fs[1][2][1] * nsin
        y1n = fs[1][2][1] * ncos + fs[1][2][0] * nsin
        x2n = fs[1][2][2] * ncos - fs[1][2][3] * nsin
        y2n = fs[1][2][3] * ncos + fs[1][2][2] * nsin

        if score_percent_filter < fs[0]:
            filtered_glas.append(fs)
            c2.create_line(fs[1][2][0] + offsetX, fs[1][2][1] + offsetY,
                           fs[1][2][2] + offsetX, fs[1][2][3] + offsetY, fill='red',
                           width=thickness)
        else:
            thickness = 1
            color = '#ACACAC'

        c3.create_line(x1n + offsetX, y1n + offsetY, x2n + offsetX, y2n + offsetY, fill=color, width=thickness)
        rotated_lines.append((fs[0], x1n, y1n, x2n, y2n))

    nr = 31
    submap = [[-1 for x in range(nr)] for y in range(nr)]
    straightened_lines = []
    cur_x = 15
    cur_y = 15

    #
    # Actual grid aligning
    # dx_dy Value closer to 1 is more aligned to x- or y- axis
    #
    # WARNING WORK IN PROGRESS
    found_start = False
    starting_point = 0

    for i in range(len(rotated_lines)):
        nexti = i+1
        if nexti >= len(rotated_lines): nexti = 0
        dir_x = 0
        dir_y = 0
        dir_x_n = 0
        dir_y_n = 0

        dx = rotated_lines[i][3] - rotated_lines[i][1]
        dy = rotated_lines[i][4] - rotated_lines[i][2]
        dx_n = rotated_lines[nexti][3] - rotated_lines[nexti][1]
        dy_n = rotated_lines[nexti][4] - rotated_lines[nexti][2]

        legnth = math.sqrt(dx * dx + dy * dy)
        dx /= legnth
        dy /= legnth
        legnth_n = math.sqrt(dx_n * dx_n + dy_n * dy_n)
        dx_n /= legnth_n
        dy_n /= legnth_n

        dx_dy = abs(dx) + abs(dy)
        dx_dy_n = abs(dx_n) + abs(dy_n)

        if dx_dy < 1.3:
            if abs(dx) > abs(dy):
                dir_x = round(dx)
            else:
                dir_y = round(dy)

        if dx_dy_n < 1.3:
            if abs(dx) > abs(dy):
                dir_x = round(dx)
            else:
                dir_y = round(dy)

        if not found_start:
            if dir_x != dir_x_n or dir_y != dir_y_n:
                starting_point = nexti
                found_start = True

        straightened_lines.append((dx, dy, dx_dy, legnth))

    for nr in range(len(rotated_lines)):
        i = nr + starting_point
        if i >= len(rotated_lines):
            i -= len(rotated_lines)
        #print(i)
        dir_x = 0
        dir_y = 0
        base = 1
        rl_score = -1

        nexti = i+1
        if nexti >= len(rotated_lines): nexti = 0

        dx_dy = straightened_lines[i][2]
        dx = straightened_lines[i][0]
        dy = straightened_lines[i][1]

        #print(dx_dy)
        if dx_dy < 1.1:
            rl_score = 0
        elif dx_dy < 1.2:
            rl_score = 1
        elif dx_dy < 1.3:
            rl_score = 2

        # If dx positive and ~1, dir = RIGHT
        # If dy negative and ~1, dir = UP
        # If dx negative and ~1, dir = LEFT
        # If dy positive and ~1, dir = DOWN

        if rl_score != -1:
            if abs(dx) > abs(dy):
                dir_x = round(dx)
            else:
                dir_y = round(dy)

        """
        if rl_score == 0:
            base = 10
        elif rl_score == 1:
            base = 10
        elif rl_score == 2:
            base = 5
        """
        base = 5
        legnth_round = int(base * round(float(straightened_lines[i][3]) / base))


        score = 10 - rl_score * 2

        if rl_score == -1:
            score = -1

        if rl_score < 2:
            if 30 < legnth_round < 50:
                submap[cur_y][cur_x] = score

        nr_cells = legnth / 40

        #print(cur_x, cur_y)
        #print(rl_score, legnth_round, nr_cells, legnth, dx, dy, dx_dy)

    #for i in range(len(submap)):
        #print(submap[i])

    """
    # print(filtered_glas)
    filtered_corners = []

    for i in range(len(filtered_glas)):
        d1 = (filtered_glas[i][1][2][0], filtered_glas[i][1][2][1])
        d2 = (filtered_glas[i][1][2][2], filtered_glas[i][1][2][3])
        for j in range(i + 1, len(filtered_glas), 1):
            e1 = (filtered_glas[j][1][2][0], filtered_glas[j][1][2][1])
            e2 = (filtered_glas[j][1][2][2], filtered_glas[j][1][2][3])

            if d1 == e1 or d1 == e2:
                filtered_corners.append((d1, i, j))
            elif d2 == e1 or d2 == e2:
                filtered_corners.append((d2, i, j))

    # print(filtered_corners)
    best_corner = ()
    grad = 0
    best_grad = 90

    for dot in filtered_corners:
        if filtered_glas[dot[1]][1][2][0] == dot[0][0]:
            v1 = (filtered_glas[dot[1]][1][2][2] - dot[0][0], -(filtered_glas[dot[1]][1][2][3] - dot[0][1]))
        else:
            v1 = (filtered_glas[dot[1]][1][2][0] - dot[0][0], -(filtered_glas[dot[1]][1][2][1] - dot[0][1]))

        if filtered_glas[dot[2]][1][2][0] == dot[0][0]:
            v2 = (filtered_glas[dot[2]][1][2][2] - dot[0][0], -(filtered_glas[dot[2]][1][2][3] - dot[0][1]))
        else:
            v2 = (filtered_glas[dot[2]][1][2][0] - dot[0][0], -(filtered_glas[dot[2]][1][2][1] - dot[0][1]))

        v_len1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])
        v_len2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1])
        v1_ = (v1[0] / v_len1, v1[1] / v_len1)
        v2_ = (v2[0] / v_len2, v2[1] / v_len2)
        val = v1_[0] * v2_[0] + v1_[1] * v2_[1]
        grad = math.degrees(math.acos(val))
        #print(val, grad)

        if abs(grad - 90) < best_grad:
            best_grad = grad
            best_corner = (grad, dot[0], v1_, v2_, v_len1, v_len2)
            #print(best_grad)

    cell_x = 0
    cell_y = 0
    # print(best_corner)
    if best_corner:
        dot = best_corner[1]
        #print(dot)
        c2.create_oval(dot[0] + offsetX - 5, dot[1] + offsetY - 5, dot[0] + offsetX + 5, dot[1] + offsetY + 5, fill='green')
        cell_x = int(best_corner[4] / 20)
        cell_y = int(best_corner[4] / 20)
        #print(cell_x, cell_y)

    offset_cell = 20
    #print(best_grad)
    #print(best_corner)
    #print(curr_index)

    #-------------------------------------------------------------

    if cell_x:
        for i in range(cell_x):
            negX = -math.copysign(1, best_corner[1][0])
            negY = -math.copysign(1, best_corner[1][1])
            neg = negX * negY
            p1 = (best_corner[1][0] + i * 40 * best_corner[2][0], best_corner[1][1] + i * 40 * best_corner[2][1] * (-1))
            p2 = (p1[0] + 40 * best_corner[2][0], p1[1] + 40 * best_corner[2][1] * (-1))
            p3 = (p2[0] + 40 * best_corner[2][1] * negY * neg, p2[1] + 40 * best_corner[2][0] * negY * neg)
            p4 = (p1[0] + 40 * best_corner[2][1] * negY * neg, p1[1] + 40 * best_corner[2][0] * negY * neg)
            print(p1,p2,p3,p4)
            draw_rect(c2, p1, p2, p3, p4)

    if cell_y:
        for i in range(cell_y):
            negX = -math.copysign(1, best_corner[1][0])
            negY = -math.copysign(1, best_corner[1][1])
            neg = negX * negY
            p1 = (best_corner[1][0] + i * 40 * best_corner[2][1], best_corner[1][1] - i * 40 * best_corner[2][0])
            p2 = (p1[0] + 40 * best_corner[2][1], p1[1] - 40 * best_corner[2][0])
            p3 = (p2[0] - 40 * best_corner[2][0], p2[1] - 40 * best_corner[2][1])
            p4 = (best_corner[1][0] - 40 * best_corner[2][0], best_corner[1][1] - 40 * best_corner[2][1])
            print(p1, p2, p3, p4)
            print(negX, negY, neg)
            draw_rect(c2, p1, p2, p3, p4)


    for l in all_lines:
        closest_1 = 0
        closest_2 = 0
        hypot_a = 100
        hypot_b = 100

        for i in range(size):
            d_x1 = abs(l[0]-200 - sin_cos[i][0])
            d_y1 = abs(l[1]-200 - sin_cos[i][1])
            d_x2 = abs(l[2]-200 - sin_cos[i][0])
            d_y2 = abs(l[3]-200 - sin_cos[i][1])

            hypot_1 = math.sqrt(d_x1*d_x1 + d_y1*d_y1)
            hypot_2 = math.sqrt(d_x2*d_x2 + d_y2*d_y2)

            #print(i, d_x1, d_y1, d_x2, d_y2)
            if hypot_1 < hypot_a:
                hypot_a = hypot_1
                closest_1 = i

            if hypot_2 < hypot_b:
                hypot_b = hypot_2
                closest_2 = i
        closest_points.append((closest_1, closest_2))

    # New chapter %% --------

    print(all_lines)
    print(closest_points)


    for i in range(len(all_lines)):
        score = 0
        x1 = all_lines[i][0]-200
        y1 = all_lines[i][1]-200
        x2 = all_lines[i][2]-200
        y2 = all_lines[i][3]-200

        for j in range(closest_points[i][0], closest_points[i][1], 1):
            x0 = sin_cos[j][0]
            y0 = sin_cos[j][1]

            dist = abs((y2-y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1) / math.sqrt((y2-y1)*(y2-y1) + (x2-x1)*(x2-x1))
            print(i, j, dist, x0, y0)
            if dist < 20:
                score += 1

        line_score.append(score)
    print(line_score)


    
    # for closest_points

    
    nr = 0
    g = 0

    while g < n:
        nr = 0
        e = g +1
        while e < n and math.fabs(intersections[g][0] - intersections[e][0]) < 20 and math.fabs(intersections[g][0] - intersections[e][0]) < 20:
            nr += 1
            e += 1

        if nr > 0:
            inters_.append((g, g + nr - 1))
        print(g, e)
        g += e

    for i in range(n):
        if i == n-1
            if math.fabs(intersections[-1][0] - intersections[e][0]) < 20 and math.fabs(intersections[g][0] - intersections[e][0]) < 20:

    new_intersections = []

    print(inters_)


    angle_deviation = []

    for i in range(num_vectors):
        if (angles[i] != None):
            if angles[i] > 0:
                angle_deviation.append((angles[i] % 90, angles[i] // 90))
            else:
              angle_deviation.append((angles[i] % -90, angles[i] // -90))
        else: angle_deviation.append(None)



    rob_rot = 0

    score = 0
    filtered_angles = []
    sum_angle = 0
    rob_rot = 0

    for i in range(num_vectors):
        temp_list = []
        cnt = 0

        for j in range(num_vectors):
            if (angle_deviation[j] != None and angle_deviation[i] != None):
                if abs(abs(angle_deviation[j][0]) - abs(angle_deviation[i][0])) < 10:
                    cnt += 1
                    sum_angle += angle_deviation[j][0]

        if cnt > score:
            score = cnt
            rob_rot = sum_angle / score



    fix_origo = 200
    for i in range(num_vectors):
        x0 = 0
        x1 = 400
        y0 = fix_origo + (x0*ls_res[i][0]) + ls_res[i][1]
        y1 = fix_origo + (x1*ls_res[i][0]) + ls_res[i][1]
        c.create_line(x0, y0, x1, y1, fill='red')

    for i in range(cell_size):
        c2.create_line(0, i * cell_size, height, i * cell_size)
        c2.create_line(0, i * cell_size, height, i * cell_size)
        c2.create_line(cell_size * i, 0, i * cell_size, width)
        c2.create_line(cell_size * i, 0, i * cell_size, width)
        c2.create_oval(195, 195, 205, 205, fill='black')


    base = 5
    least_sq = []

    for i in range(num_vectors):
        a = 0
        b = 0
        sumY = 0
        sumYY = 0
        sumX = 0
        sumXX = 0
        sumYX = 0
        mX = 0
        mY = 0
        dot_cnt = good_readings[i][2]

        for j in range(good_readings[i][0], good_readings[i][1], 1):
            sumX += sin_cos[j][0]
            sumXX += math.pow(sin_cos[j][0], 2)
            sumY += sin_cos[j][1]
            sumYX += sin_cos[j][0]*sin_cos[j][1]

        a = (dot_cnt*sumYX-sumX*sumY)/(dot_cnt*sumXX-sumX*sumX)
        b = (sumY*sumXX-sumX*sumYX)/(dot_cnt*sumXX-sumX*sumX)

        mX = sumX / dot_cnt
        mY = sumY / dot_cnt

        least_sq.append((a, b))


    for i in range(num_vectors):
        x0 = 0
        x1 = 400
        y0 = fix_origo + (x0*least_sq[i][0]) + least_sq[i][1]
        y1 = fix_origo + (y0*least_sq[i][0]) + least_sq[i][1]
        c.create_line(x0, y0, x1, y1, fill='green')

    print(lines)
    print(good_readings)
    #print(close_to)
    print(biggestX, biggestY)
    print(size)
    #print(least_sq)
    print(angles)
    print(angle_deviation)
    print(rob_rot)
    """
    # print(least_sq)
    # print(math.degrees(np.arctan(ls_res[0][0])))
    # if(i > 20 and i < 50):
    #   change += doubledelta[i][0]
    # print(change)


    root.after(200, test)


root.after(1, test)
root.mainloop()
