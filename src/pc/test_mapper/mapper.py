#######
#
# slam_gui.py
# Updated: 20/12 2016
# Authors: Jacob Lundberg
#
# This code does the exact same as SLAM_SUBMAPPER.py
# with the difference of TKinter drawings.
# See src/dora_core/SLAM_SUBMAPPER.py for comments
#
#######

import math
from tkinter import *

# from scipy.optimize import curve_fit
# import numpy as np

offsetX = 300
offsetY = 300

active_gui = True

with open("log_output.txt", "r") as f:
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


def drawText(canvas, x, y, text, color):
    canvas.create_text(x + offsetX, y + offsetY, text=text, fill=color)

# Always round .5 up
def rounds(val):
    return rounds2(val, 0.5)


# Rounds input value up if equal to base
# Opposite direction for negative values
def rounds2(val, base):
    if abs(val) % 1 >= base:
        return int(math.ceil(abs(val)) * math.copysign(1, val))
    else:
        return int(math.floor(abs(val)) * math.copysign(1, val))


def pickDir(dir_x, dir_y, dist_x, dist_y):
    print(dist_x, dist_y)
    if dir_y == 1:
        if dist_y < 0:
            y = rounds2(dist_y, 0.9)
        else:
            y = rounds2(dist_y, 0)
        x = rounds2(dist_x, 0.9)
    elif dir_y == -1:
        if dist_y < 0:
            y = rounds2(dist_y, 0.9)
        else:
            y = rounds2(dist_y, 0.1)
        if dist_x > 0:
            x = rounds2(dist_x, 0.1)
        else:
            x = rounds2(dist_x, 0.9)
    elif dir_x == 1:
        if dist_x < 0:
            x = rounds2(dist_x, 0.9)
        else:
            x = rounds2(dist_x, 0.1)
        if dist_y < 0:
            y = rounds2(dist_y, 0.9)
        else:
            y = rounds2(dist_y, 0.1)
    elif dir_x == -1:
        if dist_x < 0:
            x = rounds2(dist_x, 0.9)
        else:
            x = rounds2(dist_x, 0.1)
        y = rounds2(dist_y, 1)

    print(x, y)
    return (int(x), int(y))
    

# Returns point of intersection between two vectors
def vectorIntersection(x1, y1, x2, y2, x3, y3, x4, y4):
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / \
         ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / \
         ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    return (px, py)


def getIndex(item):
    return item[2]


def roundHalf(val):
    return round(val * 2.0) / 2.0


root = Tk()
root.title("Submapping")

width = 600
height = 600
c = Canvas(root, width=600, height=600)
c2 = Canvas(root, width=600, height=600)
c3 = Canvas(root, width=600, height=600)

c.pack(side=LEFT)
c3.pack(side=RIGHT)
c2.pack(side=RIGHT)

read = read_list[3]

curr_index = 13
automode = False


def mapper():
    global curr_index
    global automode
    global offsetX
    global offsetY
    bad_reading = False
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

    if curr_index >= len(read_list):
        curr_index = 0
    elif curr_index < 0:
        curr_index = len(read_list) - 1

    read = read_list[curr_index]

    # Variables
    size = len(read)
    corr = 7.0  # degrees
    cell_size = 40
    min_dist = 40
    d_mean_covar = 11
    d_delta_covar = 1.65
    two_delta_covar = 45
    good_reading_count = 3
    angle_deviation_filter = 8
    dot_filter_value = 18
    dot_min_dist = 7
    dot_score_dist = 6
    dot_dist_cut = 20 # 30
    res = []

    uncertain_threshold = 1
    
    if size > 0:
        step = 360.0 / size
    else:
        bad_reading = True

    # Convert to angles
    for i in range(size):
        angle = (i * step) - corr
        if angle < 0:
            angle = 360 - abs(i * step - corr)
        res.append((read[i], angle))

    # Move corrected readings to end of array
    if not bad_reading:
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
        x = sin_cos[i][0]
        y = sin_cos[i][1]
        dx = x - sin_cos[i - 1][0]
        dy = y - sin_cos[i - 1][1]
        delta.append((dx, dy))
        dist = math.hypot(x, y)

        d_next_i = i + 3
        if d_next_i > size - 2:
            d_next_i -= size

        # len2d = math.hypot(f2x - b2x, f2y - b2y)
        v1x = sin_cos[i - 2][0] - x
        v1y = sin_cos[i - 2][1] - y
        v2x = sin_cos[d_next_i][0] - x
        v2y = sin_cos[d_next_i][1] - y
        angle = abs(math.degrees(math.atan2(v2y, v2x) - math.atan2(v1y, v1x)))
        if angle > 180:
            angle -= 270
        else:
            angle -= 90

        two_delta.append(abs(angle))

        if abs(angle) < two_delta_covar and dist >= 20:
            intersections.append((sin_cos[i][0], sin_cos[i][1], i))

    # Calculate delta of delta values
    double_delta = []

    for i in range(size):

        ddx = delta[i][0] - delta[i - 1][0]
        ddy = delta[i][1] - delta[i - 1][1]
        double_delta.append((ddx, ddy))

        next_i = i + 1
        if next_i >= size: next_i = 0
        x_b = sin_cos[i - 1][0]
        y_b = sin_cos[i - 1][1]
        x_f = sin_cos[next_i][0]
        y_f = sin_cos[next_i][1]
        x = sin_cos[i][0]
        y = sin_cos[i][1]

        prev_p = math.hypot(x_b - x, y_b - y)
        next_p = math.hypot(x_f - x, y_f - y)

        
        if not (next_p > dot_dist_cut and prev_p > dot_dist_cut):
            if next_p > dot_dist_cut or prev_p > dot_dist_cut:
                intersections.append((x, y, i))

    # Calculate average delta of deltas
    delta_mean = []

    for i in range(size):
        change_x = 0.0
        change_y = 0.0
        if 1 < i < size - 2:
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
        delta_mean.append((change_x, change_y))

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
    bad_readings_cnt = 0
    uncertain_values = 0
    for i in range(size):
        x = sin_cos[i][0]
        y = sin_cos[i][1]
        if i == 0:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='green')
        # elif 5 < i < 20:
        #    c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='red')
        else:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2)
        d = 0

        if read[i] < min_dist or read[i] > 10000:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='purple')
            d = 3  # Invalid measures
            uncertain_values += 1

        if abs(delta_mean[i][0]) + abs(delta_mean[i][1]) > d_mean_covar:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='yellow')
            bad_readings_cnt += 1
            d = 2
        elif abs(double_delta[i][0]) > d_delta_covar and abs(double_delta[i][1]) > d_delta_covar:
            c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='orange')
            d = 1
            bad_readings_cnt += 1

        if two_delta[i] < two_delta_covar:
            c.create_oval(x + offsetX - 8, y + offsetY - 8, x + offsetX + 8, y + offsetY + 8, fill='magenta')
            d = 4

        dots[i] = d

    # Legitimacy check 1
    if not bad_reading:
        if uncertain_values > (size / uncertain_threshold):
            bad_reading = True

    # Dot value 0 == good value
    # Appended to list
    good_readings = []
    i = 0

    while i < size:
        cnt = 0
        j = i
        while j < size and dots[j] == 0:
            cnt += 1
            j += 1

        if cnt > good_reading_count:
            good_readings.append((i, cnt + i - 1, cnt - 1))

        i += cnt + 1

    # Merge first and last element if they are next to each other
    if len(good_readings) > 0 and good_readings[-1][1] == size - 1 and good_readings[0][0] == 0:
        good_readings[0] = (good_readings[-1][0] - size, good_readings[0][1],
                            good_readings[-1][2] + good_readings[0][2])
        good_readings.pop()

    # -----
    # Calculate lines from good readings
    # Calculate vectors from lines
    # Remove bad lines and get rotation
    # -----
    lines = []
    vectors = []
    angles = []
    filtered_vectors = []
    angle_deviation = []
    line_expansion = 200
    avg_angle = 0
    rob_rot = 0
    num_vectors = len(good_readings)
    for i in range(num_vectors):
        d_nr = good_readings[i][2]
        valX = 0
        valY = 0
        d_distX = 0
        d_distY = 0
        for j in range(good_readings[i][0], good_readings[i][1], 1):
            valX += delta[j][0]
            valY += delta[j][1]
            d_distX += sin_cos[j][0]
            d_distY += sin_cos[j][1]

        valX /= d_nr
        valY /= d_nr
        d_distX /= d_nr
        d_distY /= d_nr
        normalized = math.hypot(valX, valY)
        if normalized:
            valX /= normalized
            valY /= normalized
        else:
            print("----------------WARNING MAP MAYBE WRONG------------------")
        lines.append((valX, valY, d_distX, d_distY, good_readings[i][2]))

    # Draw lines
    for i in range(num_vectors):
        x0 = lines[i][2] - line_expansion * lines[i][0]
        x1 = lines[i][2] + line_expansion * lines[i][0]
        y0 = lines[i][3] - line_expansion * lines[i][1]
        y1 = lines[i][3] + line_expansion * lines[i][1]
        c.create_line(x0 + offsetX, y0 + offsetY, x1 + offsetX, y1 + offsetY, fill='blue')
        c.create_text(x0 + offsetX, y0 + offsetY, fill='magenta', text=str(i))

        _x0 = sin_cos[good_readings[i][0]][0]
        _x1 = sin_cos[good_readings[i][1]][0]
        _y0 = sin_cos[good_readings[i][0]][1]
        _y1 = sin_cos[good_readings[i][1]][1]
        c.create_line(_x0 + offsetX, _y0 + offsetY, _x1 + offsetX, _y1 + offsetY, fill='cyan')
        #intersections.append((_x0, _y0, good_readings[i][0]))
        #intersections.append((_x1, _y1, good_readings[i][1]))

        vectors.append((x0, y0, x1, y1))
        angles.append((math.degrees(math.atan2(-lines[i][1], lines[i][0])), i, 0))

    if angles:
        for alpha in angles:
            angle = alpha[0]
            if angle < -180:
                angle += 180
            elif angle > 180:
                angle -= 180
            angle %= 90
            if angle > 45:
                angle -= 90

            avg_angle += angle
            angle_deviation.append(angle)

        avg_angle /= len(angles)

        for i in range(num_vectors):
            angle = angle_deviation[i]
            if angle - avg_angle < angle_deviation_filter:
                filtered_vectors.append(vectors[i])
                rob_rot += angle
            else:
                c.create_line(vectors[i][0] + offsetX, vectors[i][1] + offsetY,
                              vectors[i][2] + offsetX, vectors[i][3] + offsetY, fill='red')

    if angle_deviation:
        rob_rot /= len(angle_deviation)
    else:
        rob_rot = 0

    print(avg_angle, rob_rot)

    # -----
    # Calculate intersection points for all vectors
    #
    # -----
    filtered_len = len(filtered_vectors)
    for v in range(filtered_len):
        x1 = filtered_vectors[v][0]
        x2 = filtered_vectors[v][2]
        y1 = filtered_vectors[v][1]
        y2 = filtered_vectors[v][3]
        for w in range(filtered_len):
            intersection = (0, 0)
            x3 = filtered_vectors[w][0]
            x4 = filtered_vectors[w][2]
            y3 = filtered_vectors[w][1]
            y4 = filtered_vectors[w][3]

            if v != w:
                intersection = vectorIntersection(x1, y1, x2, y2, x3, y3, x4, y4)

            best_len = 10000  # Big number, to be safe
            cur_nr = -10000
            for i in range(size):
                x = sin_cos[i][0]
                y = sin_cos[i][1]
                dx = intersection[0] - x
                dy = intersection[1] - y
                hypot = math.hypot(dx, dy)
                if hypot < best_len:
                    best_len = hypot
                    cur_nr = i

            intersections.append((intersection[0], intersection[1], cur_nr))

    # -----
    # Do some filtering of the intersections to remove bad ones
    #
    # -----
    filtered_intersections = []
    used = []
    dot_averaging = []
    # Filter intersections outside the grid
    for d in intersections:
        x1 = d[0]
        y1 = d[1]

        for _d in range(size):
            _x1 = sin_cos[_d][0]
            _y1 = sin_cos[_d][1]
            d_x1 = x1 - _x1
            d_y1 = y1 - _y1
            hypot = math.hypot(d_x1, d_y1)
            if hypot < dot_min_dist:
                filtered_intersections.append(d)
                break

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

    # -----
    # Sort intersections
    # Create new lines between intersections and form an 'outer loop'
    # -----
    new_lines = []
    dot_averaging.sort(key=getIndex)

    for i in range(len(dot_averaging)):
        next_i = i + 1
        if next_i >= len(dot_averaging): next_i = 0
        if dot_averaging[i][2] > dot_averaging[next_i][2]:
            new_lines.append((dot_averaging[i][0], dot_averaging[i][1],
                              dot_averaging[next_i][0], dot_averaging[next_i][1],
                              (-(size - dot_averaging[i][2]), dot_averaging[next_i][2])))
        else:
            new_lines.append((dot_averaging[i][0], dot_averaging[i][1],
                              dot_averaging[next_i][0], dot_averaging[next_i][1],
                              (dot_averaging[i][2], dot_averaging[next_i][2])))

    # -----
    # Draw all new lines
    # Calculate hit percent of dots on every line
    # -----
    cnt = 0
    for d in dot_averaging:
        c.create_oval(int(d[0]) - 7 + offsetX, int(d[1]) - 7 + offsetY,
                      int(d[0]) + 7 + offsetX, int(d[1]) + 7 + offsetY, fill='maroon')
        c.create_text(int(d[0]) + offsetX, int(d[1]) + offsetY, fill='white', text=str(cnt))
        cnt += 1

    closest_points = []
    line_score = []
    # print(new_lines)
    for i in range(len(new_lines)):
        l = new_lines[i]
        score = 0
        line_len = 0
        min_score_per_wall = 0

        closest_1 = l[4][0]
        closest_2 = l[4][1]
        dx = sin_cos[closest_2][0] - sin_cos[closest_1][0]
        dy = sin_cos[closest_2][1] - sin_cos[closest_1][1]

        d_readings = closest_2 - closest_1
        line_len = math.hypot(dx, dy)

        line_angle = abs(math.degrees(math.atan2(dy, dx)))
        if line_angle > 180:
            line_angle -= 270
        else:
            line_angle -= 90

        x1 = l[0]
        y1 = l[1]
        x2 = l[2]
        y2 = l[3]

        for d in range(size):
            x0 = sin_cos[d][0]
            y0 = sin_cos[d][1]

            dist = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1) / math.sqrt(
                (y2 - y1) * (y2 - y1) + (x2 - x1) * (x2 - x1))

            if dist < dot_score_dist:
                score += 1

        #print(score, d_readings, min_score_per_wall, line_len)
        # if score > score_filter:
        print(i, closest_1, closest_2, d_readings, line_len)
        #if 30 <= abs(line_angle)-abs(rob_rot) <= 60:
        #    closest_points.append((closest_1, closest_2, l))
        #    line_score.append(-1)
        if (line_len < 20 and d_readings < 1) or (line_len > 25 and d_readings < 3) or (line_len > 40 and d_readings <5) or (line_len > 60 and d_readings < 6) or (line_len > 80 and d_readings < 6) or (line_len > 100 and d_readings < 9):
            closest_points.append((closest_1, closest_2, l))
            line_score.append(-1)
        else:
            closest_points.append((closest_1, closest_2, l))
            line_score.append(score)
        #print(closest_points[-1])

    final_score = []

    for i in range(len(closest_points)):
        if closest_points[i][0] != closest_points[i][1]:
            final_score.append((line_score[i] / (closest_points[i][1] - closest_points[i][0]), closest_points[i]))
        else:
            final_score.append((-1, closest_points[i]))
        #print(i, final_score[-1])

    # Draw score vectors

    c2.create_oval(offsetX - 5, offsetY - 5, 5 + offsetX, 5 + offsetY, fill='black')
    c3.create_oval(height/2 - 5, height/2 - 5, 5 + height/2, 5 + height/2, fill='black')
    # print(final_score)

    rotated_lines = []

    for i in range(len(final_score)):
        fs = final_score[i]
        thickness = (fs[0] * 100) // 10
        if thickness > 10:
            thickness = 4
        color = 'red'
        #print(thickness)
        # rob_rot = 30
        ncos = math.cos(math.radians(rob_rot))
        nsin = math.sin(math.radians(rob_rot))
        x1n = fs[1][2][0] * ncos - fs[1][2][1] * nsin
        y1n = fs[1][2][1] * ncos + fs[1][2][0] * nsin
        x2n = fs[1][2][2] * ncos - fs[1][2][3] * nsin
        y2n = fs[1][2][3] * ncos + fs[1][2][2] * nsin

        if line_score[i] <= 0 or fs[0] <= 0:
            thickness = 1
            color = '#ACACAC'

        c2.create_line(x1n + offsetX, y1n + offsetY, x2n + offsetX, y2n + offsetY, fill=color, width=thickness)
        rotated_lines.append((thickness, x1n, y1n, x2n, y2n))
        #print(rotated_lines[-1])

    nr = 31
    submap = [[0 for x in range(nr)] for y in range(nr)]
    straightened_lines = []

    # -----
    # Actual grid aligning
    # dx_dy Value closer to 1 is more aligned to x- or y- axis
    # -----
    found_start = False
    starting_point = 0
    best_angle = 90
    best_angle_pos = 0
    possible_starting_points = []

    for i in range(len(rotated_lines)):
        next_i = i + 1
        if next_i >= len(rotated_lines): next_i = 0

        dx = rotated_lines[i][3] - rotated_lines[i][1]
        dy = rotated_lines[i][4] - rotated_lines[i][2]
        dx_n = rotated_lines[i - 1][3] - rotated_lines[i - 1][1]
        dy_n = rotated_lines[i - 1][4] - rotated_lines[i - 1][2]
        line_scr = line_score[i]
        line_scr_n = line_score[next_i]
        line_scr_p = line_score[i-1]
        dir_x = dx
        dir_y = dy

        l_len = math.hypot(dx, dy)
        dx /= l_len
        dy /= l_len
        l_len_n = math.hypot(dx_n, dy_n)
        dx_n /= l_len_n
        dy_n /= l_len_n
        angle = abs(math.degrees(math.atan2(dy_n, dx_n) - math.atan2(dy, dx)))
        this_line_angle = abs(math.degrees(math.atan2(dy,dx)))

        if line_angle > 180:
            this_line_angle -= 270
        else:
            this_line_angle -= 90
        this_line_angle = abs(this_line_angle)
        #print(i, this_line_angle)

        if angle > 180:
            angle -= 270
        else:
            angle -= 90

        angle = abs(angle)
        if angle < best_angle:
            best_angle = angle
            best_angle_pos = i

        dx_dy = abs(dx) + abs(dy)
        dx_dy_n = abs(dx_n) + abs(dy_n)

        if dx_dy < 1.3:
            if abs(dx) > abs(dy):
                dir_x = rounds(dx)
                dir_y = 0
            else:
                dir_y = rounds(dy)
                dir_x = 0

        if dx_dy_n < 1.3:
            if abs(dx) > abs(dy):
                dir_x_n = rounds(dx)
                dir_y_n = 0
            else:
                dir_y_n = rounds(dy)
                dir_x_n = 0

        #if not found_start:
        if line_scr == -1 and line_scr_n != -1:
            possible_starting_points.append(next_i)
            found_start = True

        if line_scr == -1:
            dir_x = rounds(dx)
            dir_y = rounds(dy)
        elif abs(dir_x) > abs(dir_y):
            dir_x = rounds(dx)
            dir_y = 0
        else:
            dir_x = 0
            dir_y = rounds(dy)

        if 30 < this_line_angle < 60:
            if l_len > 40:
                line_score[i] = -1

        straightened_lines.append((dir_x, dir_y, dx_dy, l_len, rotated_lines[i][0]))

    best_dist = 10000
    #print(found_start, starting_point)
    for i in possible_starting_points:
        x = rotated_lines[i][1]
        y = rotated_lines[i][2]
        dist = math.hypot(x, y)
        if dist < best_dist:
            best_dist = dist
            starting_point = i

    if not found_start:
        starting_point = best_angle_pos

    for i in range(starting_point):
        straightened_lines.append(straightened_lines.pop(0))
        line_score.append(line_score.pop(0))

    # Merge concecutive lines in the same direction
    merged_lines = []
    #print(starting_point)
    s_line_size = len(straightened_lines)
    i = 0
    #print("START DOT, END DOT, DIR X, DIR Y, dx_dy, LENGTH, GOOD/BAD, START DOT, END DOT")
    while i < s_line_size:
        temp_list = []
        cnt = 0
        new_len = straightened_lines[i][3]
        dx = straightened_lines[i][0]
        dy = straightened_lines[i][1]
        line_scr = line_score[i]
        new_score = 0
        percent_score = straightened_lines[i][0]
        
        for j in range(i + 1, s_line_size + 1, 1):
            k = j
            if k >= s_line_size: k = 0
            #print(i, k)
            dx_n = straightened_lines[k][0]
            dy_n = straightened_lines[k][1]
            l_len_n = straightened_lines[k][3]
            line_scr_n = line_score[k]
            percent_score_n = straightened_lines[k][0]

            if line_scr != -1 and line_scr_n != -1:
                if dx == dx_n and dy == dy_n and line_scr_n != -1:
                    new_len += l_len_n
                    cnt += 1
                    percent_score += percent_score_n
                elif line_scr_n != -1:
                    score = math.ceil(math.sqrt(line_scr*abs(percent_score)*20 / new_len + cnt + 3))
                    #print((i + starting_point) % s_line_size, (k + starting_point) % s_line_size, line_scr*abs(percent_score), new_len/40, percent_score, score)
                    merged_lines.append((dx, dy, straightened_lines[i][2], new_len, 1, (i + starting_point) % s_line_size, (k + starting_point) % s_line_size, score))
                    print((i + starting_point) % s_line_size, (k + starting_point) % s_line_size, merged_lines[-1])
                    break
            elif line_scr == -1:
                if dx == dx_n and dy == dy_n and line_scr_n == -1:
                    new_len += l_len_n
                    cnt += 1
                else:
                    merged_lines.append((dx, dy, straightened_lines[i][2], new_len, -1, (i + starting_point) % s_line_size, (k + starting_point) % s_line_size, -1))
                    print((i + starting_point) % s_line_size, (k + starting_point) % s_line_size, merged_lines[-1])
                    break
            else:
                score = math.ceil(math.sqrt(line_scr*abs(percent_score)*20 / new_len + cnt + 3))
                #print((i + starting_point) % s_line_size, (k + starting_point) % s_line_size, line_scr*abs(percent_score), new_len/40, percent_score, score)
                merged_lines.append((dx, dy, straightened_lines[i][2], new_len, 1, (i + starting_point) % s_line_size, (k + starting_point) % s_line_size, score))
                print((i + starting_point) % s_line_size, (k + starting_point) % s_line_size, merged_lines[-1])
                break

        i += cnt + 1

    # -----
    # Extract block of lines not containing bad ones
    #
    # -----
    merged_lines_again = []
    merged_lines_size = len(merged_lines)
    i = 0
    while i < merged_lines_size:
        cnt = 0
        temp = []
        ls = merged_lines[i][4]

        if ls != -1:
            temp.append(merged_lines[i])
            for j in range(i + 1, merged_lines_size, 1):
                k = j
                ls_n = merged_lines[k][4]
                if ls_n != -1:
                    cnt += 1
                    temp.append(merged_lines[k])
                else:
                    break
            merged_lines_again.append(temp)

        i += cnt + 1

    # -----
    # Draw lines and fill grid
    # 
    # -----
    bad_score_cnt = 1
    for i in line_score:
        if i < 0:
            bad_score_cnt += 1
    if not bad_reading:
        if bad_score_cnt / size > 0.65:
            bad_reading = True

    offset_grid = height / nr
    
    if not bad_reading:
        first_line = merged_lines_again[0][0]
        start_dir = (first_line[0], first_line[1])
        f_line_end_dot = (rotated_lines[first_line[6]][1], rotated_lines[first_line[6]][2])
        start_pos_x = f_line_end_dot[0]
        start_pos_y = f_line_end_dot[1]
        pos_corr = pickDir(start_dir[0], start_dir[1], start_pos_x / 40, start_pos_y / 40)
        first_x = x = 15 + pos_corr[0]
        first_y = y = 15 + pos_corr[1]
 
        print("----START DIR: " + str(start_dir) + ", FIRST DOT POS " + str(f_line_end_dot) + ", ROUNDED TO: " + str(pos_corr))

        for lines in merged_lines_again:
            line_end_dot_nr = lines[0][6]
            line_end_dot = (rotated_lines[line_end_dot_nr][1], rotated_lines[line_end_dot_nr][2])
            for i in range(len(lines)):
                next_i = i + 1
                if next_i >= len(lines): next_i = 0

                line_dist = roundHalf(math.hypot(rotated_lines[lines[i][5]][0] / 40, rotated_lines[lines[i][5]][1] / 40))
                #print(i, lines[i][5], line_dist)
                dir_x = lines[i][0]
                dir_y = lines[i][1]
                l_len = lines[i][3]
                cnt = rounds2(l_len / 40, 0.25)

                # Reduce score with this value
                if dx_dy < 1.1:
                    rl_score = 0
                elif dx_dy < 1.2:
                    rl_score = 1
                elif dx_dy < 1.3:
                    rl_score = 2
                else:
                    rl_score = 3

                score = rounds((2 + merged_lines[i][7] - rl_score) / bad_score_cnt)
                #print(merged_lines[i][5], score, line_dist)
                if line_scr_n == -1 or line_scr_p == -1:
                    score -= 1

                score += 5 - round(line_dist / 2)
                if score < 1:
                    score = 1
                print(l_len, cnt)
                if l_len < 30:
                    score = 1
                # Draw backwards if first line
                if i == 0:
                    if dir_x == -1:
                        extra = (1, 1)
                    elif dir_y == 1:
                        extra = (1, 1)
                    else:
                        extra = (0, 0)
                    x = first_x + rounds2((line_end_dot[0] - start_pos_x) / 40, 0.45)
                    y = first_y + rounds2((line_end_dot[1] - start_pos_y) / 40, 0.45)
                    print("----New line seg: " + str(line_end_dot[0] - start_pos_x)+
                          ", " + str(line_end_dot[1] - start_pos_y) + " Rounded: " + 
                          str(rounds((line_end_dot[0] - start_pos_x) / 40)) + ", " +
                          str(rounds((line_end_dot[1] - start_pos_y) / 40)) + ", X/Y: " + str(x) + ", " + str(y))
                    for j in range(cnt):
                        cnt_x = j * dir_x + dir_x + extra[0]
                        cnt_y = j * dir_y + extra[1]
                        if 0 <= y - cnt_y < nr:
                            if 0 <= x - cnt_x < nr:
                                submap[y - cnt_y][x - cnt_x] += score
                        c3.create_line(x * offset_grid, y * offset_grid,
                                       (x + cnt * (-dir_x)) * offset_grid,
                                       (y + cnt * (-dir_y)) * offset_grid,
                                       fill='green', width=5)
                else:
                    if dir_x == -1:
                        extra = (-1, -1)
                    elif dir_y == 1:
                        extra = (-1, 0)
                    elif dir_y == -1:
                        extra = (0, -1)
                    else:
                        extra = (0, 0)
                    next_x = x + cnt * dir_x
                    next_y = y + cnt * dir_y
                    for j in range(cnt):
                        cnt_x = j * dir_x + extra[0]
                        cnt_y = j * dir_y + extra[1]
                        if 0 <= y + cnt_y < nr:
                            if 0 <= x + cnt_x < nr:
                                submap[y + cnt_y][x + cnt_x] += score
                        c3.create_line(x * offset_grid, y * offset_grid,
                                       next_x * offset_grid, next_y * offset_grid,
                                       fill='green', width=5)
                    x = next_x
                    y = next_y

        c3.create_oval(first_x * offset_grid - 5,
                       first_y * offset_grid - 5,
                       first_x * offset_grid + 5,
                       first_y * offset_grid + 5, fill='red')
    
        for i in range(nr):
            for j in range(nr):
                t_col ='magenta'
                score = submap[i][j]
                if i == first_y and j == first_x:
                    color = 'green'
                elif i == 15 and j == 15:
                    color = 'red'
                    t_col = 'white'

                elif score == 0:
                    color = 'white'
                elif score < 0:
                    color = 'gray'
                else:
                    color = 'yellow'
                if color != 'white':
                    c3.create_rectangle(j * offset_grid, i * offset_grid, j * offset_grid + offset_grid,
                                        i * offset_grid + offset_grid, fill=color, outline='white')
                c3.create_text(j * offset_grid + offset_grid / 2, i * offset_grid + offset_grid / 2,
                               fill=t_col, text=score)


    print("Current index: " + str(curr_index) + ", List size: " + str(size) + ", No. bad readings: " +
          str(bad_readings_cnt) + ", No. bad lines: " + str(bad_score_cnt) + ", No. invalid measures: " + str(uncertain_values))
    print(rob_rot)
    root.after(200, mapper)


root.after(1, mapper)
root.mainloop()
