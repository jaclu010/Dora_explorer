import math
import time
from tkinter import *
#from scipy.optimize import curve_fit
#import numpy as np

with open("slamfixed2.txt", "r") as f:
    a = f.readlines()
read_list = []
for e in a:
    e = e[:-1]
    e = e.replace(",","")
    e = e.replace("[", "")
    e = e.replace("]", "")
    inner = e.split()
    inner2 = []
    for char in inner:
        inner2.append(int(float(char)))
    #inner = list(map(int(float), inner))
    read_list.append(inner2)

def clearCanvas(canvas):
    canvas.delete(ALL)

def pointlength(p1, p2):
    #returns the length between to points
    return (math.sqrt( ((p1[0] - p2[0]) * (p1[0] - p2[0])) + (p1[1] - p2[1])*(p1[1] - p2[1]) ) )

# Function definition for SciPy
def f(x, A, B):
    return A*x+B


root = Tk()
root.title("SLAM DUNKKK")
width = 400
height = 400
c = Canvas(root, width=400, height=400)
c2 = Canvas(root, width=400, height=400)
c.pack(side=LEFT)
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
read = [91, 91, 87, 89, 87, 89, 88, 88, 85, 89, 87, 86, 87, 90, 90, 90, 90, 88, 89, 90, 89, 91, 89, 90, 92, 92, 91, 93,
        91, 92, 93, 93, 92, 92, 92, 93, 94, 95, 97, 97, 98, 102, 101, 100, 102, 97, 97, 94, 93, 94, 93, 91, 88, 92, 89,
        89, 87, 91, 90, 88, 86, 85, 82, 83, 84, 80, 80, 82, 79, 77, 78, 74, 74, 78, 76, 73, 74, 72, 71, 70, 70, 70, 68,
        72, 71, 71, 72, 69, 76, 69, 69, 72, 68, 68, 67, 69, 68, 69, 72, 71, 67, 70, 71, 74, 72, 72, 73, 76, 75, 76, 78,
        81, 77, 78, 77, 77, 78, 83, 86, 89, 84, 86, 87, 84, 87, 90, 87, 87, 89, 91, 91, 93, 93, 92, 99, 98, 99, 99, 100,
        96, 96, 93, 94, 93, 91, 91, 90, 90, 91, 89, 92, 93, 90, 87, 89, 89, 88, 86, 85, 84, 85, 84, 86, 87, 86, 86, 89,
        86, 86, 83, 84, 86, 86, 85, 86, 86, 86, 82, 85, 86, 87, 86, 84, 83, 87, 85, 85, 87, 87, 87, 89, 89, 87, 90, 93,
        91, 93, 91, 92, 94, 92, 92, 94, 92, 93, 93, 95, 96, 95, 97, 96, 94, 93, 91, 87, 90, 88, 88, 89, 88, 86, 88, 81,
        80, 79, 78, 76, 75, 73, 74, 77, 70, 71, 72, 73, 69, 70, 71, 71, 67, 66, 69, 69, 65, 66, 68, 64, 67, 62, 64, 65,
        61, 66, 61, 62, 64, 62, 65, 64, 66, 62, 67, 64, 65, 68, 68, 64, 63, 65, 68, 70, 68, 66, 64, 72, 68, 68, 67, 72,
        71, 70, 71, 71, 75, 76, 76, 76, 77, 79, 78, 78, 80, 85, 82, 81, 88, 88, 91, 88, 85, 87, 89, 91, 90, 90, 94, 96,
        95, 97, 96, 99, 98, 99, 96, 94, 93, 91, 92, 91, 92, 89, 89, 89, 91, 91, 92, 92, 90, 88, 89, 88]
read3 = [192, 200, 206, 213, 217, 233, 235, 246, 259, 269, 287, 295, 727, 717, 744, 747, 765, -17, 755, 1188, 1194,
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
    if (automode):
        clearCanvas(c)
        clearCanvas(c2)
        curr_index+= 1
    else:
        while 1:
            ins = input("Write f to step forward, or b to step backwards. Write a to enter Automode\n")
            if (ins == "f"):
                clearCanvas(c)
                clearCanvas(c2)
                curr_index += 1
                break
            elif(ins == "b"):
                clearCanvas(c)
                clearCanvas(c2)
                curr_index -= 1
                break
            elif (ins == "a"):
                automode = True
                break

   
    if (curr_index >= len(read_list)):
        curr_index = 0
    elif (curr_index < 0):
        curr_index = len(read_list) - 1

    read = read_list[curr_index]    

    size = len(read)
    step = 0.0
    corr = 7.0  # degrees
    step = 360 / size
    res = []
    angle = 0
    
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
    biggestX = 0
    biggestY = 0

    # Extract cartesian coordinates
    for j in range(size):
        x = math.cos(math.radians(res[j][1])) * res[j][0]
        y = -math.sin(math.radians(res[j][1])) * res[j][0]
        sin_cos.append((x, y))
        if abs(x) > biggestX:
            biggestX = abs(x)
        if abs(y) > biggestY:
            biggestY = abs(y)



    # Calculate delta values
    delta = []
    dx = 0
    dy = 0

    for i in range(size):
        if i == 0:
            dx = sin_cos[i][0] - sin_cos[size - 1][0]
            dy = sin_cos[i][1] - sin_cos[size - 1][1]
        else:
            dx = sin_cos[i][0] - sin_cos[i - 1][0]
            dy = sin_cos[i][1] - sin_cos[i - 1][1]
        delta.append((dx, dy))
    
    # Calculate delta of delta values
    double_delta = []
    ddx = 0
    ddy = 0

    for i in range(size):
        if i == 0:
            ddx = delta[i][0] - delta[size - 1][0]
            ddy = delta[i][1] - delta[size - 1][1]
        else:
            ddx = delta[i][0] - delta[i - 1][0]
            ddy = delta[i][1] - delta[i - 1][1]
        double_delta.append((ddx, ddy))

    # Calculate average delta of deltas
    deltaMean = []
    changeX = 0.0
    changeY = 0.0

    for i in range(size):
        changeX = 0.0
        changeY = 0.0
        if i > 5:
            changeX += double_delta[i][0]
            changeY += double_delta[i][1]
            changeX += double_delta[i - 1][0]
            changeY += double_delta[i - 1][1]
            changeX += double_delta[i - 2][0]
            changeY += double_delta[i - 2][1]
            changeX += double_delta[i - 3][0]
            changeY += double_delta[i - 3][1]
            changeX += double_delta[i - 4][0]
            changeY += double_delta[i - 4][1]
            #changeX /= 5
            #changeY /= 5
        deltaMean.append((changeX, changeY))

    # print(str(i) + ' ' + str(changeX))
    # print(str(i) + ' ' + str(changeY))

    # Draw grid (just for show)
    cell_size = 40

    for i in range(cell_size):
        c.create_line(0, i * cell_size, height, i * cell_size)
        c.create_line(0, i * cell_size, height, i * cell_size)
        c.create_line(cell_size * i, 0, i * cell_size, width)
        c.create_line(cell_size * i, 0, i * cell_size, width)
        c.create_oval(195, 195, 205, 205, fill='black')


    # Give each point values
    # ----------------------
    # Green - the first reading
    # Red - regular values, to show rotation
    # Yellow - deltaMean triggered
    # Orange - Too high delta values
    dots = [None] * size
    d_mean_covar = 1.8
    d_delta_covar = 1.9

    for i in range(size):
        #print(str(sin_cos[i][0]) + "   \t   " + str(deltaMean[i]) + "  \t  " + str(double_delta[i]) + "  \t  " + str(res[i]))
        x = sin_cos[i][0]
        y = sin_cos[i][1]
        if i == 0:
            c.create_oval(x + 198, y + 198, x + 202, y + 202, fill='green')
        elif i > 5 and i < 20:
            c.create_oval(x + 198, y + 198, x + 202, y + 202, fill='red')
        else:
            c.create_oval(x + 198, y + 198, x + 202, y + 202)
        d = 0
        if abs(deltaMean[i][0]) > d_mean_covar and abs(deltaMean[i][1] > d_mean_covar):
            c.create_oval(x + 198, y + 198, x + 202, y + 202, fill='yellow')
            d = 2
        if abs(double_delta[i][0]) > d_delta_covar and abs(double_delta[i][1]) > d_delta_covar:
            c.create_oval(x + 198, y + 198, x + 202, y + 202, fill='orange')
            d = 1
        if read[i] < 2 or read[i] > 10000:
            c.create_oval(x + 198, y + 198, x + 202, y + 202, fill='purple')
            d = 3 #Invalid measures
        dots[i] = d

    good_readings = []
    cnt = 0
    i = 0

    # Dot value 0 == good value
    # Appended to list
    while i < size:
        cnt = 0
        e = i
        while e < size and dots[e] == 0:
            cnt += 1
            e += 1

        if cnt > 7:
            good_readings.append((i, cnt + i - 1, cnt - 1))

        i += cnt + 1

    # Merge first and last element if they are next to each other
    if len(good_readings) > 0 and good_readings[-1][1] == size-1 and good_readings[0][0] == 0:
        good_readings[0] = (good_readings[-1][0]-size, good_readings[0][1], good_readings[-1][2] + good_readings[0][2])
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
        #_x = []
        #_y = []
        for j in range(good_readings[i][0], good_readings[i][1], 1):
            valX += delta[j][0]
            valY += delta[j][1]
            d_distX += sin_cos[j][0]
            d_distY += sin_cos[j][1]
            #_x.append(sin_cos[j][0])
            #_y.append(sin_cos[j][1])

        valX /= d_nr
        valY /= d_nr
        d_distX /= d_nr
        d_distY /= d_nr
        lines.append((valX, valY, d_distX, d_distY, good_readings[i][2]))

        #x = np.array(_x)
        #y = np.array(_y)
        #A, B = curve_fit(f, x, y)[0]
        #ls_res.append((A, B))
    # Draw lines
    vectors_x = []
    vectors_y = []
    angles = []

    for i in range(num_vectors):
        if abs(lines[i][0]) < abs(lines[i][1]):
            x0 = int(round(200 + lines[i][2] + lines[i][0] * lines[i][2] * (-math.copysign(1, lines[i][1]))))
            x1 = int(round(200 + lines[i][2] - lines[i][0] * lines[i][2] * (-math.copysign(1, lines[i][1]))))
            # print(i,x0,x1)
            c.create_line(x0, 0, x1, height, fill='blue')
            # close_to.append((int(base*round(float(lines[i][2])/base)), 0))
            #angles.append(math.degrees(math.acos(lines[i][0])))
            vectors_x.append((x0,0,x1,height))
        else:
            y0 = int(round(200 + lines[i][3] - lines[i][1] * lines[i][3] * (-math.copysign(1, lines[i][0]))))
            y1 = int(round(200 + lines[i][3] + lines[i][1] * lines[i][3] * (-math.copysign(1, lines[i][0]))))
            # print(i, y0,y1)
            c.create_line(0, y0, width, y1, fill='blue')
            #print(lines[i][1])
            if (math.fabs(lines[i][1]) <= 1):
                angles.append(math.degrees(math.asin(lines[i][1])))
            else:
                angles.append(None)
            # close_to.append((int(base * round(float(lines[i][3]) / base)),1))
            vectors_y.append((0,y0,height,y1))
    # for i in range(num_vectors):

    #print(vectors_x)
    #print(vectors_y)
    #intersection lines
    #print(lines[0])

    """
    fix_origo = 200
    for i in range(num_vectors):
        dy_dx = lines[i][1]/lines[i][0]
        m = lines[i][3] - dy_dx*lines[i][2]
        y0 = fix_origo + m
        y1 = fix_origo + dy_dx*400 + m
        c.create_line(0, y0, 400, y1, fill='red')
    """

    fix_origo = 200
    for i in range(num_vectors):
        x0 = fix_origo + sin_cos[good_readings[i][0]][0]
        x1 = fix_origo + sin_cos[good_readings[i][1]][0]
        y0 = fix_origo + sin_cos[good_readings[i][0]][1]
        y1 = fix_origo + sin_cos[good_readings[i][1]][1]
        c.create_line(x0, y0, x1, y1, fill='cyan')

    intersections = []

    for v in vectors_x:
        x1 = v[0]
        x2 = v[2]
        y1 = v[1]
        y2 = v[3]
        for w in vectors_y:
            x3 = w[0]
            x4 = w[2]
            y3 = w[1]
            y4 = w[3]

            px = ((x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4))/((x1-x2)*(y3-y4)-(y1-y2)*(x3-x4))
            py = ((x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4))/((x1-x2)*(y3-y4)-(y1-y2)*(x3-x4))

            intersections.append((px, py))

    used = []
    #Res contains the final normalized points
    res = []
    val = 20
    #Filter out points near each other
    for v in intersections:
        if (not v in used):
            i = 1
            newv = (v[0],v[1])
            for w in intersections:
                if (math.fabs(v[0] - w[0]) <= val and math.fabs(v[1] - w[1]) <= val):
                    newv = (newv[0] + w[0], newv[1] + w[1])
                    i += 1
                    used.append(w)
            newv = (newv[0] / i, newv[1] / i)
            res.append(newv)
            used.append(v)
    #Draw all nomalized points
    for d in res:  
        c.create_oval(int(d[0])-5, int(d[1])-5, int(d[0])+5, int(d[1])+5, fill='maroon')

    #print(res)
    #pointlength

    #bad sorting yes
    """
    sortedres = []
   
    sortedres.append(res.pop(0))
    while (len(res) > 0):
        besti = 0
        bestl = pointlength(sortedres[len(sortedres)-1], res[0])
        
        for i in range(1,len(res)):
            nl = pointlength(sortedres[len(sortedres)-1], res[0])
            if (nl < bestl):
                besti = i
                bestl = nl
        sortedres.append(res.pop(besti))

    print(sortedres)


    #for v in res:

    sortedres.append()
    for v in res:
        if len(sortedres) == 0:
            sortedres.append(v)
        best = None 
        for w in res:
            if (v != w):
    



    #Draw polygon from all normalized points
    for i in range(len(sortedres)):
        nexti = i+1
        if (nexti >= len(sortedres)): nexti = 0
        c2.create_line(sortedres[i][0], sortedres[i][1], sortedres[nexti][0], sortedres[nexti][1])
    """

    """
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
    """

    """





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
    avg_angle = 0

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
            avg_angle = sum_angle / score


    
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
    print(avg_angle)
    """
    #print(least_sq)
    #print(math.degrees(np.arctan(ls_res[0][0])))
    # if(i > 20 and i < 50):
    #	change += doubledelta[i][0]
    # print(change)


    root.after(10,test)
root.after(1, test)
root.mainloop()