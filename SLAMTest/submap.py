import copy

# returns the new vector v1 - v2
def subtract(v1, v2):
    if (v1 == None or v2 == None): return None
    return (v1[0] - v2[0], v1[1] - v2[1])



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

    def print(self):
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
        sub.set_sub_map(submap, center_p, self.map_center)
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

    def print(self):
        print("FINAL_____")
        for y in range(len(self.finalmap)):
            inner = []
            for x in range(len(self.finalmap[0])):
                inner.append(round(self.finalmap[y][x] / len(self.submaps), 1))
            print(inner)
            #print(self.finalmap[y])
        print("finalll")



    def generate_map(self):
        self.init_final()
        for i in range(len(self.submaps)):
            sub = self.submaps[i]
            if (i == 0):
                #first submap, can place it in the middle of the map
                cent = sub.center_p
                final_center = (15,15)

                s1 = sub.grid
            #s2 = self.rotate_2d_array(sub.grid)

            #Get best rotating of sub-grid

                for y in range(sub.height()):
                    for x in range(sub.width()):
                        startp = subtract(final_center, cent)
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
                best_offset = (0,0)

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

                    best_o = (0,0)
                    best_inner = 0

                    for y_ in range(-1,2):
                        for x_ in range(-1,2):
                            innerp = 0
                            for y in range(len(s1)):
                                for x in range(len(s1[0])):

                                    #FIX -check from -1,1, -1,1

                                    startp = subtract(final_center, cent)
                                    xx = x + startp[0] + x_
                                    yy = y + startp[1] + y_

                                    prevval = self.finalmap[yy][xx]
                                    val = s1[y][x]
                                    #if (abs(val) <= 0.5 and abs(prevval) <= 0.5): innerp +=1
                                    if (abs(val) >= 0.5 and abs(prevval) >= 0.5): innerp += 1
                            #print("l",l ,"x",x_,"y", y_,"point", innerp)
                            if innerp > best_inner:
                                best_inner = innerp
                                best_o = (x_, y_)


                    if (best_inner > best_points):
                        best_points = best_inner
                        best_rot = l
                        best_offset = best_o
                #ƒprint(i,best_rot, best_points)

                print("best off", best_offset, "best Rot", best_rot)

                s1 = rotated_grids[best_rot][0]
                cent = rotated_grids[best_rot][1]

                for y in range(len(s1)):
                    for x in range(len(s1[0])):
                        startp = subtract(final_center, cent)
                        xx = x + startp[0] + best_offset[0]
                        yy = y + startp[1] + best_offset[1]
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