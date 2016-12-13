from __future__ import print_function
import math


def vector_length(vec):
    if (vec == None): return None
    vecx = vec[0]
    vecy = vec[1]
    return math.sqrt(vecx * vecx + vecy * vecy)

def normalize(vec):
    if (vec == None): return None
    length = vector_length(vec)
    return (vec[0] / length, vec[1] / length)

def pointlength(p1, p2):
    # returns the length between two points
    return (math.sqrt(((p1[0] - p2[0]) * (p1[0] - p2[0])) + (p1[1] - p2[1]) * (p1[1] - p2[1])))

def line_to_vector(p1, p2):
    if (p1 == None or p2 == None): return None
    return (p2[0] - p1[0], p2[1] - p1[1])

def rounds(val):
    if val % 1 >= 0.5:
        return math.ceil(val)
    else:
        return math.floor(val)

# Returns point of intersection between two vectors
def vectorIntersection(x1, y1, x2, y2, x3, y3, x4, y4):
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / \
         ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / \
         ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    return (px, py)


def getIndex(item):
    return item[2]

def add_submap_score(y, x, score, submap):
    submap[int(y)][int(x)] += score
    return submap


def mapper(read):
    unreliable = False
    # Variables
    size = len(read)
    corr = 7.0  # degrees
    step = 360.0 / size
    cell_size = 40
    min_dist = 40
    d_mean_covar = 11
    d_delta_covar = 1.65
    two_delta_covar = 35
    good_reading_count = 3
    angle_deviation_filter = 8
    score_percent_filter = 0.5
    score_filter = 3
    dot_filter_value = 19
    dot_min_dist = 7
    dot_score_dist = 3
    dot_dist_cut = 30
    round_base = 4
    res = []

    # Convert to angles
    for i in range(size):
        angle = (i * step) - corr
        if angle < 0:
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

        if abs(angle) < two_delta_covar and dist >= 30:
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

        prev_p = pointlength((x_b, y_b), (x, y))
        next_p = pointlength((x_f, y_f), (x, y))

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

    # Give each point values
    # ----------------------
    # Green - the first reading
    # Red - regular values, to show rotation
    # Yellow - delta_mean triggered
    # Orange - Too high delta values
    # Purple - invalid measurement
    dots = [None] * size

    for i in range(size):
        x = sin_cos[i][0]
        y = sin_cos[i][1]
        d = 0
        if abs(delta_mean[i][0]) + abs(delta_mean[i][1]) > d_mean_covar:
            d = 2
        if abs(double_delta[i][0]) > d_delta_covar and abs(double_delta[i][1]) > d_delta_covar:
            d = 1
        if two_delta[i] < two_delta_covar:
            d = 4
        if read[i] < min_dist or read[i] > 10000:
            d = 3  # Invalid measures

        dots[i] = d

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
        valX /= normalized
        valY /= normalized
        lines.append((valX, valY, d_distX, d_distY, good_readings[i][2]))

    # Draw lines
    for i in range(num_vectors):
        x0 = lines[i][2] - line_expansion * lines[i][0]
        x1 = lines[i][2] + line_expansion * lines[i][0]
        y0 = lines[i][3] - line_expansion * lines[i][1]
        y1 = lines[i][3] + line_expansion * lines[i][1]

        _x0 = sin_cos[good_readings[i][0]][0]
        _x1 = sin_cos[good_readings[i][1]][0]
        _y0 = sin_cos[good_readings[i][0]][1]
        _y1 = sin_cos[good_readings[i][1]][1]
        # intersections.append((_x0, _y0, good_readings[i][0]))
        # intersections.append((_x1, _y1, good_readings[i][1]))

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

    if angle_deviation:
        rob_rot /= len(angle_deviation)
    else:
        rob_rot = 0

    #print(avg_angle, rob_rot)

    # -----
    # Calculate intersection points for all vectors
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

    # Draw polygon from all normalized points
    for i in range(len(dot_averaging)):
        next_i = i + 1
        if next_i >= len(dot_averaging): next_i = 0
        # c2.create_line(dot_averaging[i][0] + offsetX, dot_averaging[i][1] + offsetY,
        # dot_averaging[next_i][0] + offsetX, dot_averaging[next_i][1] + offsetY, fill='#ABABAB', width=2)
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

    closest_points = []
    line_score = []
    # print(new_lines)
    for l in new_lines:
        score = 0
        line_len = 0
        min_score_per_wall = 0

        closest_1 = l[4][0]
        closest_2 = l[4][1]
        dx = sin_cos[closest_2][0] - sin_cos[closest_1][0]
        dy = sin_cos[closest_2][1] - sin_cos[closest_1][1]

        d_readings = closest_2 - closest_1
        line_len = math.hypot(dx, dy)
        min_score_per_wall = int(line_len / d_readings)

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

        # print(score, d_readings, min_score_per_wall, line_len)
        # if score > score_filter:
        if line_len > 40 and d_readings < 5:
            closest_points.append((closest_1, closest_2, l))
            line_score.append(-1)
        else:
            closest_points.append((closest_1, closest_2, l))
            line_score.append(score)

    final_score = []

    for i in range(len(closest_points)):
        if closest_points[i][0] != closest_points[i][1]:
            final_score.append((line_score[i] / (closest_points[i][1] - closest_points[i][0]), closest_points[i]))
        else:
            final_score.append((1, closest_points[i]))

    rotated_lines = []

    startpos = (15, 15)
    firstpos = True
    starter = (0, 0)
    rob_pos = (0, 0)
    first_bounding = ((0, 0), (0, 0))

    nr = 31
    submap = [[0 for x in range(nr)] for y in range(nr)]

    # print("rob_", rob_rot)
    curr_id = 0
    best_index = 0
    best_ang = 10000

    for fs in final_score:

        thickness = (fs[0] * 100) // 10
        if thickness > 10:
            thickness = 4
        color = 'red'

        # rob_rot = 30
        ncos = math.cos(math.radians(rob_rot))
        nsin = math.sin(math.radians(rob_rot))
        x1n = fs[1][2][0] * ncos - fs[1][2][1] * nsin
        y1n = fs[1][2][1] * ncos + fs[1][2][0] * nsin
        x2n = fs[1][2][2] * ncos - fs[1][2][3] * nsin
        y2n = fs[1][2][3] * ncos + fs[1][2][2] * nsin

        if fs[0] <= 0:
            thickness = 1
            color = '#ACACAC'

        # c2.create_line(x1n + offsetX, y1n + offsetY, x2n + offsetX, y2n + offsetY, fill=color, width=thickness)
        rotated_lines.append((fs[0], x1n, y1n, x2n, y2n))
        p1 = (x1n, y1n)
        p2 = (x2n, y2n)

        vecer = line_to_vector(p1, p2)
        vec_deg = math.atan2(vecer[1], vecer[0]) % math.radians(90)

        angle_from = 0
        if (vec_deg >= math.radians(45)):
            angle_from = math.radians(90) - vec_deg
        else:
            angle_from = vec_deg

        if (curr_id == 0):
            best_ang = angle_from
            best_index = 0
        else:
            if (angle_from < best_ang and vector_length(vecer) >= 35):
                best_ang = angle_from
                best_index = curr_id

        # print("current_Degree", curr_id, fs[0] > 0, math.degrees(vec_deg), angle_from, vecer[0], vecer[1])
        curr_id += 1
        # "GO HERE"
        # print(xs)
    #print("____")
    for l in range(best_index, best_index + len(rotated_lines)):

        id = l % len(rotated_lines)
        # print(id)
        roted = rotated_lines[id]

        x1n = roted[1]
        y1n = roted[2]
        x2n = roted[3]
        y2n = roted[4]

        clr = "red"
        if (id == best_index): clr = "green"
        if (roted[0] <= 0): clr = "gray"

        p1 = (x1n, y1n)
        p2 = (x2n, y2n)

        vec = line_to_vector(p1, p2)
        vec_normalized = normalize(vec)
        norm_vec = (-vec[1], vec[0])
        norm_vec = normalize(norm_vec)
        check_len = 10
        vec_deg = math.atan2(vec[1], vec[0]) % math.radians(90)

        angle_from = 0
        if (vec_deg >= math.radians(45)):
            angle_from = math.radians(90) - vec_deg
        else:
            angle_from = vec_deg
        #print(id, math.degrees(angle_from))

        if (math.degrees(angle_from) >= 14.5): clr = "purple"

        # print("deg", math.degrees() % 90 )
        #c2.create_line(x1n + offsetX, y1n + offsetY, x2n + offsetX, y2n + offsetY, fill=clr, width=2)
        # print("FINAL", fs[0])
        if (roted[0] > 0 and math.degrees(angle_from) < 14.5):
            num_tiles = vector_length(vec) / 40
            x_ = vec_normalized[0]
            y_ = vec_normalized[1]
            tlen = 40
            numline = 2
            for a in range(int(math.ceil(num_tiles))):

                for i in range(0, numline):
                    if not (i == 0 and a == 0):
                        xs = x1n + a * x_ * tlen + x_ * tlen / numline * i
                        ys = y1n + a * y_ * tlen + y_ * tlen / numline * i

                        midx1 = x1n + a * x * tlen + x_ * tlen / 2
                        midy1 = y1n + a * y * tlen + y_ * tlen / 2

                        xs1 = xs + norm_vec[0] * 20
                        ys1 = ys + norm_vec[1] * 20

                        px1 = x1n + x_ * tlen * a
                        py1 = y1n + y_ * tlen * a

                        px2 = px1 + norm_vec[0] * tlen
                        py2 = py1 + norm_vec[1] * tlen

                        px3 = px1 + x_ * tlen
                        py3 = py1 + y_ * tlen

                        px4 = px3 + norm_vec[0] * tlen
                        py4 = py3 + norm_vec[1] * tlen

                        midx = midx1 + norm_vec[0] * 14
                        midy = midy1 + norm_vec[1] * 14

                        vsd = line_to_vector(p1, (xs, ys))
                        # print("len", vector_length(vsd), vector_length(vec))
                        # print("vlen", vector_length(vsd))
                        if (vector_length(vsd) < vector_length(vec) - 5):

                            # startpos = (15, 15)
                            # firstpos = True
                            # starter = (0, 0)
                            """d
                            c2.create_oval(midx + offsetX - 2, midy + offsetY - 2, midx + offsetX + 2,
                                           midy + offsetY + 2)
                            c2.create_oval(midx1 + offsetX - 2, midy1 + offsetY - 2, midx1 + offsetX + 2,
                                           midy1 + offsetY + 2, fill="red")
                            """

                            if (firstpos):
                                starter = (xs1, ys1)

                                #draw_dot(c2, px1, py1, 3, "green")
                                #draw_dot(c2, px2, py2, 5, "red")
                                #draw_dot(c2, px3, py3, 5, "red")
                                #draw_dot(c2, px4, py4, 2, "white")

                                minx = px2
                                miny = py2
                                maxx = px3
                                maxy = py3
                                if (px3 < px2):
                                    minx = px3
                                    maxx = px2

                                if (py3 < py2):
                                    miny = py3
                                    maxy = py2

                                first_bounding = ((minx, miny), (maxx, maxy))
                               # print("asd", minx, miny, maxx, maxy)

                                # print(px2, py2, px3, py3)

                                firstpos = False
                                # submap[startpos[1]][startpos[0]] = 1
                                # else:
                                # pos2 = (round((xs1 - starter[0]) / 40), round((ys1 - starter[1]) / 40))
                                # print("asdasd, pos", pos2)
                                # submap[startpos[1] + pos2[1]][startpos[0] + pos2[0]] = 1
                                # c2.create_oval(xs1 + offsetX - 2, ys1 + offsetY - 2, xs1 + offsetX + 2,ys1 + offsetY + 2, fill="orange")

                            w = first_bounding[1][0] - first_bounding[0][0]
                            h = first_bounding[1][1] - first_bounding[0][1]

                            #print("POS", xs1, ys1)
                            _x = first_bounding[0][0] - xs1 + 15 * w
                            _y = first_bounding[0][1] - ys1 + 15 * h
                            # print("wh",w,h)
                            if (w != 0 and h != 0):
                                indx = int(-_x / w)
                                indy = int(-_y / h)
                                submap[indy][indx] = 1


    return submap

def test_print(mapp):
    for row in mapp:
        col_counter = 0
        for col in row:
            if col != 1 and col != 0:
                if col >= 10:
                    col = col % 10
                    print(GREEN + str(col) + ENDC, end='')
                elif col < 0:
                    print(WARNING + str(abs(col)) + ENDC, end='')
                else:
                    print(BLUE + str(col) + ENDC, end='')
            else:
                print(col, end='')

            if col_counter == 30:
                print('')
                col_counter = 0
                col_counter += 1




if __name__ == '__main__':

    GREEN = '\033[92m'
    BLUE = '\033[94m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    with open('laser_log.log', 'r') as data:
        reads = data.readlines()
        read = reads[0].lstrip('\n').split('#')
        for r in read:
            if not r:
                continue
            if r.startswith('[laser]'):
                r = eval(r[len('[laser]'):].lstrip('#'))
            else:
                r = eval(r.lstrip('#'))

            mapp = mapper(r)
            #print(len(mapp))
            for row in mapp:
                col_counter = 0
                for col in row:
                    if col != 1 and col != 0:
                        if col >= 10:
                            col = col % 10
                            print(GREEN + str(col) + ENDC, end='')
                        elif col < 0:
                            print(WARNING + str(abs(col)) + ENDC, end='')
                        else:
                            print(BLUE + str(col) + ENDC, end='')
                    else:
                        print(col, end='')

                    if col_counter == 30:
                        print('')
                        col_counter = 0
                    col_counter += 1
                        
                        

            raw_input('Continue..')