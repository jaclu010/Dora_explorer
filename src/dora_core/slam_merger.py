#####
#
# slam_merger.py
# Updated: 20/12 2016
# Author: Johan Nilsson
#
#####
import copy

# returns the new vector v1 - v2
def subtract(v1, v2):
    if (v1 == None or v2 == None): return None
    return (v1[0] - v2[0], v1[1] - v2[1])

def check_t_range(p1, maxX, maxY):
    if (p1[0] >= 0 and p1[1] >= 0 and p1[0] < maxX and p1[1] < maxY):
        return True
    return False

def returnFinal(final, sub, subpos, pos):

    l = copy.deepcopy(final)

    best_p = 0
    best_fit = (0, 0)

    for y_ in range(-1, 2):
        for x_ in range(-1, 2):
            innerp = 0
            for y in range(len(sub)):
                for x in range(len(sub[0])):
                    startp = subtract(pos, subpos)
                    xx = x + startp[0] + x_
                    yy = y + startp[1] + y_
                    if (xx >= 0 and yy >= 0 and xx < len(l) and yy < len(l)):
                        # print(xx,yy)

                        prevval = l[yy][xx]
                        val = sub[y][x]
                        # if (abs(val) <= 0.5 and abs(prevval) <= 0.5): innerp +=1
                        if (abs(val) >= 2 and abs(prevval) >= 2): innerp += 1
            if (innerp > best_p):
                best_p = innerp
                best_fit = (x_, y_)

    #print(best_p, best_fit)
    for y in range(len(sub)):
        for x in range(len(sub[0])):
            startp = startp = subtract(pos, subpos)
            xx = x + startp[0] + best_fit[0]
            yy = y + startp[1] + best_fit[1]

            if (xx >= 0 and yy >= 0 and xx < len(l) and yy < len(l)):
                prevval = l[yy][xx]
                val = sub[y][x]
                if (val) > 0:
                    l[yy][xx] = val
    return l


#returns a sliced submap, and new position
def slice_submap(grid, pos):

    minx = 1000
    miny = 1000
    maxx = 0
    maxy = 0

    subpos = (0,0)
    sub = []

    for y in range(len(grid)):
        for x in range(len(grid[0])):

            if (grid[y][x] >= 1):
                if x < minx: minx = x
                if y < miny: miny = y
                if x > maxx: maxx = x
                if y > maxy: maxy = y

    #print(minx,maxx, miny, maxy, pos)

    if (pos[0] < minx): minx = pos[0]
    if (pos[1] < miny): miny = pos[1]
    if (pos[0] > maxx): maxx = pos[0]
    if (pos[1] > maxy): maxy = pos[1]


    yi = 0
    for y in range(miny, maxy + 1):
        inner = []
        xi = 0
        for x in range(minx, maxx + 1):
            inner.append(grid[y][x])

            if (x == pos[0] and y == pos[1]):
                subpos = (xi, yi)

            xi += 1
        sub.append(inner)
        yi += 1

    return [sub, subpos]


def raycast_seen(grid, robot_position, numsub):
    gridder = [[1 for x in range(31)] for y in range(31)]
    for y in range(len(grid)):
        for x in range(len(grid)):
            val = float(grid[y][x]) / numsub

            #print(grid[y][x],numsub, val, robot_position)

            if (val >= 0.3):
                line = bresenham([robot_position[0], robot_position[1]], [x,y], True)

                #gridder[y][x] = 0

                for p in line.path:
                    valler = float(grid[p[1]][p[0]]) / numsub

                    if not (x == p[0] and y == p[1]):
                        if (valler <= 0.4):
                            gridder[p[1]][p[0]] = 0
                        else:
                            break
    return gridder


#Returns new grid with floors, input grid is 2d-array is size m*n
def raycast_floor(grid, robot_position):
    newgrid = copy.deepcopy(grid)
    for y in range(len(newgrid)):
        for x in range(len(newgrid[0])):
            val = newgrid[y][x]

            if (val >= 2):
                line = bresenham([robot_position[0], robot_position[1]], [x, y])
                if (line.path):
                    if not(line.path[0][0] == robot_position[0] and line.path[0][1] == robot_position[1]):
                        line.path.reverse()
                for p in line.path:
                    valler = newgrid[p[1]][p[0]]
                    
                    if not (x == p[0] and y == p[1]):
                        if (valler == 0):
                            newgrid[p[1]][p[0]] = 1
                        if (valler >= 2):
                            break

                #print("THIS PATH", line.path)

            elif (val == 0 or val == 1):
                up = (x, y-1)
                down = (x,y+1)
                left = (x-1, y)
                right = (x+1,y)
                count = 0
                if (check_t_range(up, 31, 31)):
                    vals = newgrid[up[1]][up[0]]
                    if (vals >= 2):
                        count += 1
                if (check_t_range(down, 31, 31)):
                    vals = newgrid[down[1]][down[0]]
                    if (vals >= 2):
                        count += 1
                if (check_t_range(left, 31, 31)):
                    vals = newgrid[left[1]][left[0]]
                    if (vals >= 2):
                        count += 1
                if (check_t_range(right, 31, 31)):
                    vals = newgrid[right[1]][right[0]]
                    if (vals >= 2):
                        count += 1

                #if x == 15 and y == 12:
                #    print(x, y, val, count)

                if (count >= 2):
                    line = bresenham([robot_position[0], robot_position[1]], [x, y])
                    if (line.path):
                        if not(line.path[0][0] == robot_position[0] and line.path[0][1] == robot_position[1]):
                            line.path.reverse()
                        
                    for p in line.path:
                        valler = newgrid[p[1]][p[0]]

                        if not (x == p[0] and y == p[1]):
                            if (valler == 0):
                                newgrid[p[1]][p[0]] = 1
                            if (valler >= 2):
                                break
                    #print("That path", line.path)
    return newgrid


#Returns new grid with floors, input grid is 2d-array is size m*n
def raycast_floor2(grid, robot_position, inputGrid, offset):

    newgrid = copy.deepcopy(grid)
    for y in range(len(newgrid)):
        for x in range(len(newgrid[0])):
            val = newgrid[y][x]

            if (val >= 2):
                line = bresenham([robot_position[0], robot_position[1]], [x, y])
                for p in line.path:
                    valler = newgrid[p[1]][p[0]]

                    if not (x == p[0] and y == p[1]):
                        if (valler == 0):
                            newgrid[p[1]][p[0]] = 1
                        if (valler >= 2):
                            break

            elif (val == 0 or val == 1):
                up = (x, y-1)
                down = (x,y+1)
                left = (x-1, y)
                right = (x+1,y)
                count = 0
                if (check_t_range(up, 31, 31)):
                    vals = newgrid[up[1]][up[0]]
                    if (vals >= 2):
                        count += 1
                if (check_t_range(down, 31, 31)):
                    vals = newgrid[down[1]][down[0]]
                    if (vals >= 2):
                        count += 1
                if (check_t_range(left, 31, 31)):
                    vals = newgrid[left[1]][left[0]]
                    if (vals >= 2):
                        count += 1
                if (check_t_range(right, 31, 31)):
                    vals = newgrid[right[1]][right[0]]
                    if (vals >= 2):
                        count += 1

                if (count >= 2):
                    line = bresenham([robot_position[0], robot_position[1]], [x, y])
                    #print(line.path)
                    for p in line.path:
                        valler = newgrid[p[1]][p[0]]

                        if not (x == p[0] and y == p[1]):
                            if (valler == 0):
                                newgrid[p[1]][p[0]] = 1
                            if (valler >= 2):
                                break

    newgrid2 = copy.deepcopy(inputGrid)
    offset = (0,0)
    print(offset)
    for y in range(len(newgrid)):
        for x in range(len(newgrid[0])):
            realxy = (x+offset[0], y + offset[1])

            if (realxy[0] >= 0 and realxy[1] >= 0 and realxy[1] < len(newgrid2) and realxy[0] < len(newgrid2[0])):
                a = 0
                val2 = newgrid[y][x]
                val = newgrid2[realxy[1]][realxy[0]]
                if (val2 == 1):
                    if (val != 2):
                        newgrid2[realxy[1]][realxy[0]] = 1
    return newgrid2


# class bresenham generates points (x,y) containing points of a line between start-point and end-point.
# The class uses bresenhams line-drawing algorithm to generate these points.
# The class i mainly used for raycasting.
class bresenham:
    def __init__(self, start, end, walls=False):
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
        derr = 10000
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
                
        if walls:
            self.path.append((end[0], end[1]))

    def swap(self, n1, n2):
        return [n2, n1]


#A submap contains a 2D-grid containing walls from one laser-reading.
## It also contains the center_position which are the local coordinates for robot in submap.
#Position contains the global coordinates in the "final" map
class SubMap:
    def __init__(self):
        self.grid = []
        self.center_p = (0,0)
        self.position = (0,0)
        self.direction = 0

        #0 north
        #1 east
        #2 south
        #3 west


    def get_grid(self):
        return self.grid


    def width(self):
        if(len(self.grid)) > 0:
            return len(self.grid[0])
        return 0


    def height(self):
        return (len(self.grid))


    def set_sub_map(self, sub, center_p, real_pos, direction=0):
        self.grid = copy.deepcopy(sub)
        self.center_p = center_p
        self.position = real_pos
        self.direction = direction


    def print_(self):
        print("______")
        for y in range(self.height()):
            print(self.grid[y])
        print("Robot_pos:", self.center_p)


    def get_grid_value(self, x, y):
        if (x >= 0 and y >= 0 and x < self.width() and y < self.height()):
            return self.grid[y][x]
        return None


# A Mapping object contains the final map that all laser-readings have generated.
# The object contains submaps which are used to generate the final map.
class Mapping:
    def __init__(self):
        # The laser_array contains data of laser readings.
        self.grid = []
        self.finalmap = []

        self.finalmapholder = []
        #self.finalsubmapholder = []

        self.finalmapholder = [[0 for x in range(31)] for y in range(31)]

        self.subfinal = []
        self.init_grid()
        self.init_final()
        self.init_subfinal()
        self.rot = 0
        self.map_center = (10, 10)
        
        self.maxiter = 6
        self.curriter = 0

        self.currfilter = [[0 for x in range(31)] for y in range(31)]
        
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


    # This function removes "bad" walls from the final map.
    def remove_bad_values(self):
        print("____________")
        for y in range(len(self.finalmap)):
            for x in range(len(self.finalmap)):

                if (self.currfilter[y][x] == 1):
                    continue
                
                val = 0
                if (len(self.submaps)):
                    val = self.finalmap[y][x] / len(self.submaps)
                
                if val <= 0.5:
                    self.finalmap[y][x] = 0
                else:
                    self.finalmap[y][x] = val * (3*len(self.submaps) /4 )
        self.submaps = []
        

    def init_map(self, grid):
        grid = [[0 for x in range(31)] for y in range(31)]


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


    #This function generates a submap and stores it.
    #Input: submap is a 2D-grid, center_p is the robot-position in the submap, and global_pos is
    # the position of the robot in the final_grid
    def add_submap(self, submap, center_p, global_pos, direction=0):

        sub = SubMap()
        sub.set_sub_map(submap, center_p, global_pos, direction)
        self.submaps.append(sub)


    # Given a 2D-grid lst, this function rotates the grid clock-wise and return the rotated grid
    # along with the center_point for the grid
    def rotate_2d_array(self, lst, center_p):

        m = len(lst)
        if (m > 0):

            #for r in lst:
            #    print(r)
            #print("pos", center_p)


            n = len(lst[0])
            # Creates a list containing 5 lists, each of 8 items, all set to 0
            w, h = 8, 5
            roted = [[0 for x in range(m)] for y in range(n)]

            for r in range(m):
                for c in range(n):
                    roted[c][m-1-r] = lst[r][c]

            ##y = r, x = c

            newcent = (m-1-center_p[1], center_p[0])
            #print("_____")
            #for r in roted:
            #    print(r)
            #print(newcent)


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


    #This function generates the final map by adding a submaps to it.
    def generate_map(self, ir_grid):

        self.init_subfinal()
        
        #self.init_map(self.finalmapholder)
        robot_poss = (0,0)

        if len(self.submaps) > 0:
            i = len(self.submaps) - 1
            sub = self.submaps[i]
            self.first = False
            
            if (self.first):
                print("NEVER? YES")
                #If the final grid is empty, add the first submap to the middle of the
                #final grid

                cent = sub.center_p
                final_center = sub.position

                s1 = sub.grid
                newgrid = [sub.grid, cent]
                if sub.direction == 0:
                    #north, rotate once
                    newgrid = self.rotate_2d_array(sub.grid, cent)
                elif sub.direction == 1:
                    #east, rotate twice
                    firstrot = self.rotate_2d_array(sub.grid, cent) 
                    newgrid = self.rotate_2d_array(firstrot[0], firstrot[1])
                elif sub.direction == 2:
                    #south
                    firstrot = self.rotate_2d_array(sub.grid, cent) 
                    secrot = self.rotate_2d_array(firstrot[0], firstrot[1])
                    newgrid = self.rotate_2d_array(secrot[0], secrot[1])
                s1 = newgrid[0]
                cent = newgrid[1]

                for y in range(len(s1)):
                    for x in range(len(s1[0])):
                        startp = subtract(final_center, cent)
                        xx = x + startp[0]
                        yy = y + startp[1]
                        if (xx >= 0 and yy >= 0 and xx < len(self.finalmap) and yy < len(self.finalmap)):
                            #prevval = self.finalmap[yy][xx]
                            #val = sub.get_grid_value(x, y)
                            val = s1[y][x]
                            self.finalmap[yy][xx] = val
                            self.subfinal[yy][xx] = val
                            self.finalmapholder[yy][xx] = val
                self.first = False
            else:
                # If we are adding a submap to the final_grid, we need to find the best
                # rotation of the submap, and the best place to place it in the final grid.
                #print("YEBANYO DIRECTION", sub.direction)
                s1 = sub.grid
                cent = sub.center_p
                init1 = copy.deepcopy(s1)
                initcent = sub.center_p
                rotated_grids = []
                best_rot = 0
                best_points = 0
                best_offset = (0,0)
                
                if (s1):
                    #First of all, we need to store all the rotated grids, along with the rotated
                    #robot position.
                    for l in range(4):
                        points = 0
                        if True:
                            s1 = copy.deepcopy(init1)
                            cent = initcent

                            if sub.direction == 0:
                                rot = self.rotate_2d_array(s1,cent)
                                s1 = rot[0]
                                cent = rot[1]
                            elif (sub.direction == 1):
                                rot = self.rotate_2d_array(s1,cent)
                                s1 = rot[0]
                                cent = rot[1]
                                rot = self.rotate_2d_array(s1,cent)
                                s1 = rot[0]
                                cent = rot[1]
                            elif (sub.direction == 2):
                                rot = self.rotate_2d_array(s1,cent)
                                s1 = rot[0]
                                cent = rot[1]
                                rot = self.rotate_2d_array(s1,cent)
                                s1 = rot[0]
                                cent = rot[1]
                                rot = self.rotate_2d_array(s1,cent)
                                s1 = rot[0]
                                cent = rot[1]
                        rotated_grids.append((s1, cent))

                        final_center = sub.position
                        points = 0

                        best_o = (0,0)
                        best_inner = 0
                        
                        # Since we are uncertain about the robot's position in the final_grid
                        # We need to loop through around that point to see where the submap fits
                        # the best. When we found the best rotation of the grid and best position
                        # we store what rotation and offset, to later be inserted into the final grid
                        for y_ in range(-1,2):
                            for x_ in range(-1,2):
                                innerp = 0
                                for y in range(len(s1)):
                                    for x in range(len(s1[0])):

                                        startp = subtract(final_center, cent)
                                        xx = x + startp[0] + x_
                                        yy = y + startp[1] + y_
                                        if (xx >= 0 and yy >= 0 and xx < len(ir_grid) and yy < len(ir_grid)):

                                            prevval = ir_grid[yy][xx]
                                            prevval2 = self.finalmap[yy][xx]
                                            val = s1[y][x]
                                            #if (abs(val) <= 0.5 and abs(prevval) <= 0.5): innerp +=1
                                            if (abs(val) >= 0.3 and abs(prevval) == 2): innerp += 2
                                            #if (abs(val) >= 0.3 and abs(prevval2) >= 0.3): innerp += 1
                                #print("l",l ,"x",x_,"y", y_,"point", innerp)
                                if innerp > best_inner:
                                    best_inner = innerp
                                    best_o = (x_, y_)


                        if (best_inner > best_points):
                            best_points = best_inner
                            best_rot = l
                            best_offset = best_o

                if rotated_grids:
                    #By using the stored rotation and stored offset, we add the values of the submap
                    # to the final grid.

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
                                holdprevval = self.finalmapholder[yy][xx]


                                self.subfinal[yy][xx] = val
                                self.finalmap[yy][xx] = val + prevval
                                self.finalmapholder[yy][xx] = val + holdprevval

            #magic
            if (len(self.submaps) == self.maxiter):
            #if (True):
                filt = raycast_seen(self.finalmapholder, sub.position,len(self.submaps))
                self.currfilter = filt


    def get_grid_value(self, x, y):
        if (x >= 0 and y >= 0 and x < len(self.grid) and y < len(self.grid)):
            return self.grid[y][x]
        return None

    def get_grid_pos(self, offset, pos, size):

        offset = (offset[0]/2, offset[1]/2)
        new_pos = (int(offset[0] + pos[0]/size), int(offset[1] + pos[1]/size))

        return new_pos
