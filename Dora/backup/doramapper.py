import math
import time
import copy
# import numpy as np
offsetX = 200
offsetY = 200
"""
with open("slamfixed4.txt", "r") as f:
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
"""
def pointlength(p1, p2):
    # returns the length between to points
    return (math.sqrt(((p1[0] - p2[0]) * (p1[0] - p2[0])) + (p1[1] - p2[1]) * (p1[1] - p2[1])))


class Laser_Data:
    def __init__(self):
        self.laser_array = []
        self.lines = []
        self.lines_score = []
        self.cornor = []
        self.goodr = []
        self.vector_x = []
        self.vector_y = []
        self.intersections = []
        self.fixval = 0
        self.rot = 0

    # update all values so it corresponds to laser_array
    def update_laser(self, l_array):
        self.laser_array = l_array
        self.fixval = self.get_fix_value()
        self.good_read()

    def set_cornor(self):
        self.cornor = []
        for i in range(len(self.lines_score)):
            l1 = self.lines_score[i][0]
            for j in range(len(self.lines_score)):
                l2 = self.lines_score[j][0]
                p1 = l1[0]
                p2 = l1[1]
                p3 = l2[0]
                p4 = l2[1]
                # s1,s2,s3 are a binary statement, containing info if two lines is built by same point
                s1 = (i != j)
                s2 = (p1 == p3) or (p2 == p4)
                s2 = (p1 == p4) or (p1 == p3) or (p2 == p4) or (p2 == p3)
                if (s1 and s2):
                    self.cornor.append((i, j))
                    # s2 = (l1[1][0] == l2[0][0] and l1[1][1] == l2[0][1]) or (l1[0][0] == l2[1][0] and l1[0][1] == l2[1][1])
                    # s3 = (l1[0][0] == l2[0][0] and l1[0][1] == l2[0][1]) or (l1[1][0] == l2[1][0] and l1[1][1] == l2[1][1])
                    #print((i,j), (p1, p2), (p3,p4))

        #sys.exit(0)
    # returns the point on the cornor between l1 and l2, otherwise None if no cornor
    def get_same_point(self, l1, l2):
        if (l1 == None or l2 == None): return None
        if (l1[0] == l2[0] or l1[0] == l2[1]): return l1[0]
        if (l1[1] == l2[0] or l1[1] == l2[1]): return l1[1]
        return None


    def find_line_model(self, points):
        """ find a line model for the given points
        :param points selected points for model fitting
        :return line model
        """

        # [WARNING] vertical and horizontal lines should be treated differently
        #           here we just add some noise to avoid division by zero

        # find a line model for these points

        print(points)
        print(points[1][1])
        m = (points[1][1] - points[0][1]) / (points[1][0] - points[0][0] + sys.float_info.epsilon)
        c = points[1][1] - m*points[1][0]


        #m = (points[1, 1] - points[0, 1]) / (points[1, 0] - points[0, 0] + sys.float_info.epsilon)  # slope (gradient) of the line
        #c = points[1, 1] - m * points[1, 0]  # y-intercept of the line

        return m, c

    def find_intercept_point(self, m, c, x0, y0):
        """ find an intercept point of the line model with
            a normal from point (x0,y0) to it
        :param m slope of the line model
        :param c y-intercept of the line model
        :param x0 point's x coordinate
        :param y0 point's y coordinate
        :return intercept point
        """

        # intersection point with the model
        x = (x0 + m * y0 - m * c) / (1 + m ** 2)
        y = (m * x0 + (m ** 2) * y0 - (m ** 2) * c) / (1 + m ** 2) + c

        return x, y

    # returns laser_array
    def get_laser_array(self):
        return self.laser_array

    # returns the size of laser_array
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

    # returns the value at index i of laser_array
    def get_value(self, i):
        i = self.fixi(i)
        if (i < self.size()):
            if (i < 0): i = self.size() - 1 + i
            return self.laser_array[i]
        return None

    def get_true_value(self, i):
        if (i < self.size()):
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
        step = 2 * math.pi / self.size()
        corr = math.radians(7)
        angle = (i * step) - corr
        if (angle < math.radians(0)):
            angle = math.radians(360) - abs(i * step - corr)
        return angle

    def get_true_angle(self, i):
        if (i < 0): i = self.size() - 1 + i
        step = 2 * math.pi / self.size()
        corr = math.radians(7)
        angle = (i * step) - corr
        if (angle < math.radians(0)):
            angle = math.radians(360) - abs(i * step - corr)
        return angle

    def get_fix_value(self):
        i = 0
        while self.get_true_angle(i) > math.radians(180):
            i += 1
        return i

    # returns the position (tuple) of the laser reading at index i
    def get_laser_pos(self, i):
        if (i < self.size()):
            if (i < 0): i = self.size() - 1 + i
            offsd = 0
            x = math.cos(self.get_angle(i)) * (self.get_value(i) + offsd)
            y = -math.sin(self.get_angle(i)) * (self.get_value(i) + offsd)
            return (x, y)
        return None

    def get_laser_pos2(self, i, offset, rot_point, angle):
        if (i < self.size()):
            if (i < 0): i = self.size() - 1 + i
            x = math.cos(self.get_angle(i)) * (self.get_value(i) + offset)
            y = -math.sin(self.get_angle(i)) * (self.get_value(i) + offset)

            return self.rotate_point(rot_point, (x,y), angle)
        return None

    # Return the vector s*v where s is a scalar, and v is vector
    def multiply(self, s, v):
        if (v == None): return None
        return (s * v[0], s * v[1])

    # returns the new vector v1 + v2
    def add(self, v1, v2):
        if (v1 == None or v2 == None): return None
        return (v1[0] + v2[0], v1[1] + v2[1])

    # returns the new vector v1 - v2
    def subtract(self, v1, v2):
        if (v1 == None or v2 == None): return None
        return (v1[0] - v2[0], v1[1] - v2[1])

    # returns the dot-product of v1 and v2
    def dot(self, v1, v2):
        if (v1 == None or v2 == None): return None
        return v1[0] * v2[0] + v1[1] * v2[1]

    # returns the vector that is between point p1 and p2
    def line_to_vector(self, l):
        if (l == None): return None
        p1 = l[0]
        p2 = l[1]
        if (p1 == None or p2 == None): return None
        return (p2[0] - p1[0], p2[1] - p1[1])

    # returns the point that has been rotated around center angle degrees.
    """
    def rotate_point(self, center, p, angle):
        s = math.sin(angle)
        c = math.cos(angle)
        px = p[0] - center[0]
        py = p[1] - center[1]
        xnew = px * c + py * s
        ynew = px * s + py * c
        return (xnew + center[0], ynew + center[1])

    """
    def rotate_point(self, center, p, angle):
        cx = center[0]
        cy = center[1]
        px = p[0]
        py = p[1]

        return (math.cos(angle) * (px - cx) - math.sin(angle) * (py - cy) + cx, math.sin(angle) * (px - cx) + math.cos(angle) * (py - cy) + cy)


    # sets the element at x,y in 2D-array to value
    def set_block(self, m, x, y, value):
        if (x >= 0 and y >= 0 and y < len(m) and x < len(m[0])):
            m[y][x] = value

    # returns the length of vector vec
    def vector_length(self, vec):
        if (vec == None): return None
        vecx = vec[0]
        vecy = vec[1]
        return math.sqrt(vecx * vecx + vecy * vecy)

    # returns the length of line l
    def line_length(self, p1, p2):
        return math.sqrt((p2[0] - p1[0]) * (p2[0] - p1[0]) + (p2[1] - p1[1]) * (p2[1] - p1[1]))

    # using bressenhams line drawing algorithm to draw a line from p1 to p2 in 2d-list m
    def draw_line(self, grid, p1, p2, value):
        x0 = p1[0]
        y0 = p1[1]
        x1 = p2[0]
        y1 = p2[1]

        #print(x0,y0, "->", x1, y1)


        if (x1 - x0 != 0):
            m = (y1 * 1.0 - y0 * 1.0) / (x1 * 1.0 - x0 * 1.0)
            y = y0
            for x in range(x0, x1+1):
                self.set_block(grid, x, int(y + 0.5), value)
                y += m
        else:
            for y in range(y0, y1):
                self.set_block(grid, x0, y+1, value)
                #print(x0, y)
    # Returns the normalized vector
    def normalize(self, vec):
        if (vec == None): return None
        length = self.vector_length(vec)
        return (vec[0] / length, vec[1] / length)

    # returns the first delta
    def get_delta(self, i):
        if (i < self.size()):
            if (i < 0): i = self.size() - 1 + i
            previ = i - 1
            if (i == 0):
                previ = self.size() - 1
            v1 = self.get_laser_pos(i)
            v2 = self.get_laser_pos(previ)
            return self.subtract(v1, v2)
        return None

    def get_delta2(self, i):
        if (i < self.size()):
            if (i < 0): i = self.size() - 1 + i
            previ = i - 1
            if (i == 0):
                previ = self.size() - 1
            v1 = self.get_delta(i)
            v2 = self.get_delta(previ)

            return self.subtract(v1, v2)
        return None

    # return the delta mean
    def get_delta_mean(self, i):
        c_x = 0.0
        c_y = 0.0
        if 1 < i < (self.size()-2):
            c_x += self.get_delta2(i)[0]
            c_y += self.get_delta2(i)[1]
            c_x += self.get_delta2(i - 1)[0]
            c_y += self.get_delta2(i - 1)[1]
            c_x += self.get_delta2(i - 2)[0]
            c_y += self.get_delta2(i - 2)[1]
            c_x += self.get_delta2(i + 1)[0]
            c_y += self.get_delta2(i + 1)[1]
            c_x += self.get_delta2(i + 2)[0]
            c_y += self.get_delta2(i + 2)[1]
        return (c_x, c_y)
        # Get the dot_value. Used to filter good and bad dots

    def get_dot_value(self, i):

        d_mean_covar = 1.8
        d_delta_covar = 1.9
        d = 0
        if (abs(self.get_delta_mean(i)[0]) > d_mean_covar and abs(self.get_delta_mean(i)[1]) > d_mean_covar):
            d = 2
            #print(i, self.get_delta_mean(i))
        if (abs(self.get_delta2(i)[0]) > d_delta_covar and abs(self.get_delta2(i)[1]) > d_delta_covar):
            d = 1
        if (self.get_value(i) < 40 or self.get_value(i) > 10000):
            d = 3

        return d

    def good_read(self):
        # FIX THIS LATER GOOD SHIT IH YEAH
        # I (JOHAN) HAVE NO IDEA WHAT THIS IS, BUT WE SHOULD FIX THIS
        self.lines = []
        self.lines_score = []
        good_readings = []
        i = 0
        good_val = 4
        while i < self.size():
            cnt = 0
            e = i
            while e < self.size() and (self.get_dot_value(e) == 0):
                cnt += 1
                e += 1
            if (cnt > good_val):
                good_readings.append((i, cnt + i - 1, cnt - 1))
            i += cnt + 1

            # if (not (e < self.size() and self.get_dot_value(e) == 0)):i+=1

        # print("we done 308 325 16")
        # print(self.size())
        # Merge first and last element if they are next to each other
        if len(good_readings) > 0 and good_readings[-1][1] == self.size() - 1 and good_readings[0][0] == 0:
            good_readings[0] = (
                good_readings[-1][0] - self.size(), good_readings[0][1], good_readings[-1][2] + good_readings[0][2])
            good_readings.pop()

        self.goodr = good_readings
        # if len(good_readings) > 0 and good_readings[-1][1] == self.size() - 1 and good_readings[0][0] == 0:
        #    good_readings[0] = (good_readings[-1][0] - self.size(), good_readings[0][1], good_readings[-1][2] + good_readings[0][2])
        #    good_readings.pop()
        # Calculat the lines
        num_vec = len(good_readings)
        for i in range(num_vec):
            d_nr = good_readings[i][2]
            valX = 0
            valY = 0
            d_distX = 0
            d_distY = 0
            for j in range(good_readings[i][0], good_readings[i][1], 1):
                # print(good_readings[i][0], good_readings[i][1], 1)
                # print(self.size())
                valX += self.get_delta(j)[0]
                valY += self.get_delta(j)[1]
                d_distX += self.get_laser_pos(j)[0]
                d_distY += self.get_laser_pos(j)[1]
            valX /= d_nr
            valY /= d_nr
            d_distX /= d_nr
            d_distY /= d_nr
            self.lines.append(((valX, valY), (d_distX, d_distY), good_readings[i][2]))

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
        val = 20
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

        all_lines = []
        closest_points = []
        line_score = []
        # self.lines_sore
        first = True
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
                    for k in range(self.size()):
                        pos = self.get_laser_pos(k)
                        x0 = pos[0]
                        y0 = pos[1]
                        d_x1 = abs(x1 - x0)
                        d_y1 = abs(y1 - y0)
                        d_x2 = abs(x2 - x0)
                        d_y2 = abs(y2 - y1)
                        hypot_1 = math.sqrt(d_x1 * d_x1 + d_y1 * d_y1)
                        hypot_2 = math.sqrt(d_x2 * d_x2 + d_y2 * d_y2)
                        dist = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1) / math.sqrt(
                            (y2 - y1) * (y2 - y1) + (x2 - x1) * (x2 - x1))
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
                        val = 0
                        c1 = closest_1
                        c2 = closest_2
                        tf = first
                        if (first):
                            c1 = closest_1
                            c2 = closest_2
                            val = self.size() - (c2 - c1)
                            first = False
                        else:
                            if (closest_1 > closest_2):
                                c1 = closest_2
                                c2 = closest_1
                            val = c2 - c1
                        # print("HEHE: ", c1, c2, score, val, i, j)
                        if (val > 0):
                            self.lines_score.append((l, c1, c2, score, val))

    def draw_lines(self):
        line_expansion = 40
        self.vector_x = []
        self.vector_y = []
        for i in range(len(self.goodr)):
            l = self.lines[i]
            p1 = l[0]
            p2 = l[1]
            x0 = p2[0] - line_expansion * p1[0]
            y0 = p2[1] - line_expansion * p1[1]
            x1 = p2[0] + line_expansion * p1[0]
            y1 = p2[1] + line_expansion * p1[1]
            #c.create_line(x0 + offsetX, y0 + offsetY, x1 + offsetX, y1 + offsetY, fill="blue")
            _x0 = self.get_laser_pos(self.goodr[i][0])[0]
            _x1 = self.get_laser_pos(self.goodr[i][1])[0]
            _y0 = self.get_laser_pos(self.goodr[i][0])[1]
            _y1 = self.get_laser_pos(self.goodr[i][1])[1]
            #c.create_line(_x0 + offsetX, _y0 + offsetY, _x1 + offsetX, _y1 + offsetY, fill='cyan')
            if (abs(p1[0]) < abs(p1[1])):
                self.vector_x.append((x0, y0, x1, y1))
            else:
                self.vector_y.append((x0, y0, x1, y1))
        self.set_intersections()
        self.set_cornor()


class SubMap:
    def __init__(self):
        self.grid = []
        self.center_p = (0,0)

    def get_grid(self):
        return self.grid

    def width(self):
        if(len(self.grid)) > 0:
            return len(self.grid[0])
        return 0

    def height(self):
        return (len(self.grid))

    def set_sub_map(self, sub, center_p):
        self.grid = copy.deepcopy(sub)
        self.center_p = center_p
        #self.draw_submap(0,0)

    def get_grid_value(self, x, y):
        if (x >= 0 and y >= 0 and x < self.width() and y < self.height()):
            return self.grid[y][x]
        return None


class Mapping:
    def __init__(self):
        # The laser_array contains data of laser readings.
        self.laser = Laser_Data()
        self.grid = []
        self.finalmap = []
        self.init_grid()
        self.init_final()
        self.rot = 0
        self.map_center = (10, 10)

        self.submaps = []

    def init_grid(self):
        # Init grid
        self.grid = []
        for y in range(21):
            inner = []
            for x in range(21):
                inner.append(0)
            self.grid.append(inner)

    def init_final(self):
        # Init grid
        self.finalmap = []
        for y in range(31):
            inner = []
            for x in range(31):
                inner.append(0)
            self.finalmap.append(inner)

    def add_submap(self, submap, center_p):
        sub = SubMap()
        sub.set_sub_map(submap, center_p)
        self.submaps.append(sub)


    def rotate_2d_array(self, lst, center_p):


        m = len(lst)
        if (m > 0):
            n = len(lst[0])
            # Creates a list containing 5 lists, each of 8 items, all set to 0
            w, h = 8, 5.
            roted = [[0 for x in range(m)] for y in range(n)]

            for r in range(m):
                for c in range(n):
                    roted[c][m-1-r] = lst[r][c]

            ##y = r, x = c

            newcent = (m-1-center_p[1], center_p[0])
            #print(center_p, newcent)
            return (roted, newcent)
        return None



    def generate_map(self):

        for i in range(len(self.submaps)):
            sub = self.submaps[i]
            #print(len(sub))
            if (i == 0):
                #first submap, can place it in the middle of the map
                cent = sub.center_p
                final_center = (15,15)

                s1 = sub.grid
            #s2 = self.rotate_2d_array(sub.grid)

            #Get best rotating of sub-grid

                for y in range(sub.height()):
                    for x in range(sub.width()):
                        startp = self.laser.subtract(final_center, cent)
                        xx = x + startp[0]
                        yy = y + startp[1]
                        prevval = self.finalmap[yy][xx]
                        val = sub.get_grid_value(x, y)
                        self.finalmap[yy][xx] = val
            else:
                #We need to find best rotation
                #print("_____")
                s1 = sub.grid
                cent = sub.center_p
                rotated_grids = []
                best_rot = 0
                best_points = 0

                for l in range(4):

                    points = 0
                    if l != 0:
                        for k in range(l):
                            rot = self.rotate_2d_array(s1,cent)
                            s1 = rot[0]
                            cent = rot[1]

                    rotated_grids.append((s1, cent))

                    final_center = (15, 15)
                    points = 0
                    for y in range(len(s1)):

                        for x in range(len(s1[0])):
                            startp = self.laser.subtract(final_center, cent)
                            xx = x + startp[0]
                            yy = y + startp[1]

                            prevval = self.finalmap[yy][xx]
                            val = s1[y][x]
                            if (abs(val) <= 0.5 and abs(prevval) <= 0.5): points +=1
                            if (abs(val) >= 0.5 and abs(prevval) >= 0.5): points += 1

                    if (points > best_points):
                        best_points = points
                        best_rot = l
                #print(i,best_rot, best_points)

                s1 = rotated_grids[best_rot][0]
                cent = rotated_grids[best_rot][1]

                for y in range(len(s1)):
                    for x in range(len(s1[0])):
                        startp = self.laser.subtract(final_center, cent)
                        xx = x + startp[0]
                        yy = y + startp[1]
                        prevval = self.finalmap[yy][xx]
                        val = s1[y][x]

                        self.finalmap[yy][xx] = val + prevval


    def get_grid_value(self, x, y):
        if (x >= 0 and y >= 0 and x < len(self.grid) and y < len(self.grid)):
            return self.grid[y][x]
        return None

    def get_grid_pos(self, offset, pos, size):

        offset = (offset[0]/2, offset[1]/2)
        new_pos = (int(offset[0] + pos[0]/size), int(offset[1] + pos[1]/size))
        #news = (new_pos[0]/40, new_pos[1]/40)
        #print(news)

        return new_pos

    # creates a grid from
    def fit_grid(self):
        b_index = 0
        b_angle = 10000
        laser = self.laser
        corn = laser.cornor
        center = (0, 0)
        self.init_grid()
        #print("num Corn: ", len(corn))
        #print(len(corn))
        for i in range(len(corn)):
            i1 = corn[i][0]
            i2 = corn[i][1]
            l1 = laser.lines_score[i1][0]
            l2 = laser.lines_score[i2][0]
            v1 = laser.normalize(laser.line_to_vector(l1))
            v2 = laser.normalize(laser.line_to_vector(l2))
            #print(print(laser.dot(v1,v2)))
            ang = math.acos(round(laser.dot(v1, v2), 4))
            rotvalue = 90 - abs(math.degrees(ang))
            if (rotvalue <= 12):
                if (ang < b_angle):
                    b_angle = ang
                    b_index = i



        if (len(corn) > 0):

            best_line = (laser.lines_score[corn[b_index][0]][0], laser.lines_score[corn[b_index][1]][0])

            #print(best_line)
            best_vector = (laser.line_to_vector(best_line[0]), laser.line_to_vector(best_line[1]))
            best_norm_vector = (laser.normalize(best_vector[0]), laser.normalize(best_vector[1]))
            #print(laser.dot(v1,v2))
            angle = math.acos(round(laser.dot(v1, v2),4))
            #print(math.degrees(angle))
            rotated_lines = []
            rotated_vec = []
            rotated_center = (0, 0)

            if (90 - abs(math.degrees(angle)) <=9):
                deg_trans = math.atan(-best_norm_vector[1][1] / best_norm_vector[1][0])
                bl = best_line[1]
                bl2 = best_line[0]
                deg_trans = -math.atan2(bl[0][1] - bl[1][1], bl[0][0] - bl[1][0])
                deg_trans2 = -math.atan2(bl2[0][1] - bl2[1][1], bl2[0][0] - bl2[1][0])

                if (deg_trans2 < deg_trans): deg_trans = deg_trans2

                deg_trans = deg_trans % math.radians(90)

                center_point = laser.get_same_point(best_line[0], best_line[1])
                if (center_point != None):
                    for i in range(len(laser.lines_score)):
                        p1 = laser.lines_score[i][0][0]
                        p2 = laser.lines_score[i][0][1]
                        rp1 = laser.rotate_point(center_point, p1, deg_trans)
                        rp2 = laser.rotate_point(center_point, p2, deg_trans)
                        l = (rp1, rp2)
                        rotated_lines.append(l)
                        rotated_vec.append((rp2[0] - rp1[0], (rp2[1] - rp1[1])))
                    rotated_center = laser.rotate_point(center_point, center, deg_trans)


                #draw_dot(c, bl[0], "yellow")
                #draw_dot(c, bl[1], "yellow")

                #draw_line(c, (0, 0), laser.get_laser_pos2(0, 0, (0,0), deg_trans), "red")

                minx = -1
                miny = -1
                maxx = -1
                maxy = -1

                for i in range(0,laser.size()):
                    #print(math.degrees(deg_trans))
                    rot_p = laser.get_laser_pos2(i, 25, (0,0), deg_trans)
                    
                    #print(rot_p)
                    
                    fixed = (rot_p[0] / 40, rot_p[1] / 40)
                    
                    #drawfix = laser.multiply(20, fixed)

                    fixed = (round(fixed[0]), round(fixed[1]))
                    
                    gridp = laser.add((10,10), fixed)
                    #print(gridp)
                    gridp = (int(gridp[0]), int(gridp[1]))
                    #print(gridp)
                    value = self.get_grid_value(gridp[0], gridp[1])
                        #print(laser.multiply(1/40, rot_p))
                        #print(gridp)
                    dval = laser.get_dot_value(i)
                    #if (dval != 3):
                    num = 1
                    if (dval != 0): num = 1/2
                    if (dval == 3): num = 1/4

                    if (i == 0):
                        minx = gridp[0]
                        miny = gridp[1]
                        maxx = gridp[0]
                        maxy = gridp[1]
                    else:
                        if gridp[0] < minx: minx = gridp[0]
                        if gridp[1] < miny: miny = gridp[1]
                        if gridp[0] > maxx: maxx = gridp[0]
                        if gridp[1] > maxy: maxy = gridp[1]

                    

                    laser.set_block(self.grid, gridp[0], gridp[1], value + num)
                    #c2.create_oval(rot_p[0] + offsetX-2, rot_p[1] + offsetY-2, rot_p[0] + offsetX+2, rot_p[1] + offsetY+2)

                
                #for row in self.grid:
                #    print(row)
                        
                
                #print((minx, miny), (maxx, maxy))
                lst = []
                center_p = (0,0)
                yy = 0
                print("______SUBMAP_____")
                for y in range(miny, maxy + 1):

                    inner = []
                    xx = 0
                    for x in range(minx, maxx+1):
                        inner.append(self.get_grid_value(x, y))

                        if (x == 10 and y == 10):
                            center_p = (xx,yy)

                        xx += 1
                    lst.append(inner)
                    yy += 1

                self.add_submap(lst, center_p)

    def print_grid(self):
        for g in self.grid:
            print(g)

#s = Mapping()

#vasd = 0
"""d
def update():
    #global laser
    global read_list
    #for i in range(len(read_list)):

    s.laser.update_laser(read_list[i])

        #s.laser.draw_dots()
    s.laser.draw_lines()

    s.fit_grid()

    if (len(s.submaps) > 10):
        s.generate_map()
"""



#update()

#root.after(1, draw)
#root.mainloop()
