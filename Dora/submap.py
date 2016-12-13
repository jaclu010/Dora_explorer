import copy

# returns the new vector v1 - v2
def subtract(v1, v2):
    if (v1 == None or v2 == None): return None
    return (v1[0] - v2[0], v1[1] - v2[1])

#Returns new grid with floors, input grid is 2d-array is size m*n
def raycast_floor(grid, robot_position):
    newgrid = copy.deepcopy(grid)
    for y in range(len(newgrid)):
        for x in range(len(newgrid[0])):
            val = newgrid[y][x]
            if (val == 2):
                line = bresenham([robot_position[0], robot_position[1]], [x, y])
                for p in line.path:
                    valler = newgrid[p[1]][p[0]]
                    if not (x == p[0] and y == p[1]):
                        if (valler == 0):
                            newgrid[p[1]][p[0]] = 1
                        if (valler == 2):
                            break
    return newgrid



class bresenham:
    def __init__(self, start, end):
        self.start = list(start)
        self.end = list(end)
        self.path = []

        self.steep = abs(self.end[1] - self.start[1]) > abs(self.end[0] - self.start[0])

        if self.steep:
            #print('Steep')
            self.start = self.swap(self.start[0], self.start[1])
            self.end = self.swap(self.end[0], self.end[1])

        if self.start[0] > self.end[0]:
            #print('flippin and floppin')
            _x0 = int(self.start[0])
            _x1 = int(self.end[0])
            self.start[0] = _x1
            self.end[0] = _x0

            _y0 = int(self.start[1])
            _y1 = int(self.end[1])
            self.start[1] = _y1
            self.end[1] = _y0

        dx = self.end[0] - self.start[0]
        dy = abs(self.end[1] - self.start[1])
        error = 0
        derr = 100000
        if (dx > 0):
            derr = dy / float(dx)

        ystep = 0
        y = self.start[1]

        if self.start[1] < self.end[1]:
            ystep = 1
        else:
            ystep = -1

        for x in range(self.start[0], self.end[0] + 1):
            if self.steep:
                self.path.append((y, x))
            else:
                self.path.append((x, y))

            error += derr

            if error >= 0.5:
                y += ystep
                error -= 1.0

        #print (start)
        #print(end)
        #print()
        #print(self.start)
        #print(self.end)

    def swap(self, n1, n2):
        return [n2, n1]


"""
A submap contains a 2D-grid containing walls from one laser-reading.
It also contains the center_position which are the local coordinates for robot in submap.
Position contains the global coordinates in the "final" map
"""
class SubMap:
    def __init__(self):
        self.grid = []
        self.center_p = (0,0)
        self.position = (0,0)

    def get_grid(self):
        return self.grid

    def width(self):
        if(len(self.grid)) > 0:
            return len(self.grid[0])
        return 0

    def height(self):
        return (len(self.grid))

    def set_sub_map(self, sub, center_p, real_pos):
        self.grid = copy.deepcopy(sub)
        self.center_p = center_p
        self.position = real_pos

    def print_(self):
        print("______")
        for y in range(self.height()):
            print(self.grid[y])
        print("Robot_pos:", self.center_p)


    def get_grid_value(self, x, y):
        if (x >= 0 and y >= 0 and x < self.width() and y < self.height()):
            return self.grid[y][x]
        return None

class Mapping:
    def __init__(self):
        # The laser_array contains data of laser readings.
        self.grid = []
        self.finalmap = []
        self.subfinal = []
        self.init_grid()
        self.init_final()
        self.init_subfinal()
        self.rot = 0
        self.map_center = (10, 10)

        self.maxiter = 10
        self.curriter = 0

        self.num_readings = 0

        self.first = True

        self.submaps = []

    def init_grid(self):
        # Init grid
        self.grid = []
        for y in range(21):
            inner = []
            for x in range(21):
                inner.append(0)
            self.grid.append(inner)


    def remove_bad_values(self):
        for y in range(len(self.finalmap)):
            for x in range(len(self.finalmap)):
                val = 0
                if (len(self.submaps)):
                    val = self.finalmap[y][x] / len(self.submaps)

                if val <= 0.6:
                    self.finalmap[y][x] = 0
                else:
                    val2 = val * 7
                    self.finalmap[y][x] = val2
        self.submaps = []

    def init_final(self):
        # Init grid
        self.finalmap = []
        for y in range(31):
            inner = []
            for x in range(31):
                inner.append(0)
            self.finalmap.append(inner)

    def init_subfinal(self):
        # Init grid
        self.subfinal = []
        for y in range(31):
            inner = []
            for x in range(31):
                inner.append(0)
            self.subfinal.append(inner)

    def add_submap(self, submap, center_p, global_pos):

        sub = SubMap()
        sub.set_sub_map(submap, center_p, global_pos)
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

    def print_(self):
        print("FINAL_____")
        for y in range(len(self.finalmap)):
            inner = []
            for x in range(len(self.finalmap[0])):
                inner.append(round(self.finalmap[y][x] / len(self.submaps), 1))
            print(inner)
            #print(self.finalmap[y])
        print("finalll")



    def generate_map(self):
        #self.init_final()
        #for i in range(len(self.submaps)):
        self.init_subfinal()
        if len(self.submaps) > 0:
            i = len(self.submaps) - 1
            sub = self.submaps[i]

            if (self.first):
                #first submap, can place it in the middle of the map
                cent = sub.center_p
                final_center = sub.position

                s1 = sub.grid

                newgrid = self.rotate_2d_array(sub.grid, cent)

                s1 = newgrid[0]
                cent = newgrid[1]

                #s1.grid =
            #s2 = self.rotate_2d_array(sub.grid)

            #Get best rotating of sub-grid

                for y in range(len(s1)):
                    for x in range(len(s1[0])):
                        startp = subtract(final_center, cent)
                        xx = x + startp[0]
                        yy = y + startp[1]
                        if (xx >= 0 and yy >= 0 and xx < len(self.finalmap) and yy < len(self.finalmap)):
                            prevval = self.finalmap[yy][xx]
                            #val = sub.get_grid_value(x, y)
                            val = s1[y][x]
                            self.finalmap[yy][xx] = val
                            self.subfinal[yy][xx] = val
                self.first = False
            else:
                #We need to find best rotation
                #print("_____")
                s1 = sub.grid
                cent = sub.center_p
                rotated_grids = []
                best_rot = 0
                best_points = 0
                best_offset = (0,0)
                if (s1):
                    for l in range(4):

                        points = 0
                        if l != 0:
                            for k in range(l):
                                rot = self.rotate_2d_array(s1,cent)
                                s1 = rot[0]
                                cent = rot[1]

                        rotated_grids.append((s1, cent))

                        final_center = sub.position
                        points = 0

                        best_o = (0,0)
                        best_inner = 0

                        for y_ in range(-2,3):
                            for x_ in range(-2,3):
                                innerp = 0
                                for y in range(len(s1)):
                                    for x in range(len(s1[0])):

                                        #FIX -check from -1,1, -1,1

                                        startp = subtract(final_center, cent)
                                        xx = x + startp[0] + x_
                                        yy = y + startp[1] + y_
                                        if (xx >= 0 and yy >= 0 and xx < len(self.finalmap) and yy < len(self.finalmap)):

                                            prevval = self.finalmap[yy][xx]
                                            val = s1[y][x]
                                            #if (abs(val) <= 0.5 and abs(prevval) <= 0.5): innerp +=1
                                            if (abs(val) >= 0.3 and abs(prevval) >= 0.3): innerp += 1
                                #print("l",l ,"x",x_,"y", y_,"point", innerp)
                                if innerp > best_inner:
                                    best_inner = innerp
                                    best_o = (x_, y_)


                        if (best_inner > best_points):
                            best_points = best_inner
                            best_rot = l
                            best_offset = best_o
                #print(i,best_rot, best_points)

                #print("best off", best_offset, "best Rot", best_rot)
                if rotated_grids:
                    s1 = rotated_grids[best_rot][0]
                    cent = rotated_grids[best_rot][1]

                    for y in range(len(s1)):
                        for x in range(len(s1[0])):
                            startp = subtract(final_center, cent)
                            xx = x + startp[0] + best_offset[0]
                            yy = y + startp[1] + best_offset[1]

                            if (xx >= 0 and yy >= 0 and xx < len(self.finalmap) and yy < len(self.finalmap)):
                                prevval = self.finalmap[yy][xx]
                                val = s1[y][x]

                                self.subfinal[yy][xx] = val
                                self.finalmap[yy][xx] = val + prevval


    def get_grid_value(self, x, y):
        if (x >= 0 and y >= 0 and x < len(self.grid) and y < len(self.grid)):
            return self.grid[y][x]
        return None

    def get_grid_pos(self, offset, pos, size):

        offset = (offset[0]/2, offset[1]/2)
        new_pos = (int(offset[0] + pos[0]/size), int(offset[1] + pos[1]/size))

        return new_pos
