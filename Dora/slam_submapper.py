from __future__ import print_function
import math


def pointlength(p1, p2):
    # returns the length between two points
    return (math.sqrt(((p1[0] - p2[0]) * (p1[0] - p2[0])) + (p1[1] - p2[1]) * (p1[1] - p2[1])))


def rounds(val):
    if val % 1 >= 0.5:
        return math.ceil(val)
    else:
        return math.floor(val)


def pickDirection(dir_x, dir_y, d_x, d_y, org_d_x, org_d_y):
    if dir_x == -1:
        d_x = int(math.floor(d_x) * math.copysign(1, org_d_x))
        d_y = int(math.ceil(d_y) * math.copysign(1, org_d_y))
    elif dir_y == -1:
        d_x = int(math.ceil(d_x) * math.copysign(1, org_d_x))
        d_y = int(math.floor(d_y) * math.copysign(1, org_d_y))
    elif dir_x == 1:
        d_x = int(math.floor(d_x) * math.copysign(1, org_d_x))
        d_y = int(math.ceil(d_y) * math.copysign(1, org_d_y))
    elif dir_y == 1:
        d_x = int(math.ceil(d_x) * math.copysign(1, org_d_x))
        d_y = int(math.floor(d_y) * math.copysign(1, org_d_y))
    return (d_x, d_y)


# Returns point of intersection between two vectors
def vectorIntersection(x1, y1, x2, y2, x3, y3, x4, y4):
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / \
         ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / \
         ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    return (px, py)


def getIndex(item):
    return item[2]


curr_index = 0
automode = False


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
    dot_dist_cut = 20  # 30
    round_base = 4
    res = []
    bad_reading = False

    # Convert to angles
    for i in range(size):
        angle = (i * step) - corr
        if angle < 0:
            angle = 360 - abs(i * step - corr)
        res.append((read[i], angle))

    # Move corrected readings to end of array
    curr = res[0][1]
    #print("before res append")
    while curr > 180:
        #print(curr)
        res.append(res.pop(0))
        curr = res[0][1]
    #print("after res append")
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
            #c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='yellow')
            d = 2
        if abs(double_delta[i][0]) > d_delta_covar and abs(double_delta[i][1]) > d_delta_covar:
            #c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='orange')
            d = 1
        if two_delta[i] < two_delta_covar:
            #c.create_oval(x + offsetX - 8, y + offsetY - 8, x + offsetX + 8, y + offsetY + 8, fill='magenta')
            d = 4
        if read[i] < min_dist or read[i] > 10000:
            #c.create_oval(x + offsetX - 2, y + offsetY - 2, x + offsetX + 2, y + offsetY + 2, fill='purple')
            d = 3  # Invalid measures

        dots[i] = d

    # Dot value 0 == good value
    # Appended to list
    good_readings = []
    i = 0
    #print("before good raeding")
    while i < size:
        cnt = 0
        j = i
        while j < size and dots[j] == 0:
            cnt += 1
            j += 1

        if cnt > good_reading_count:
            good_readings.append((i, cnt + i - 1, cnt - 1))

        i += cnt + 1
    #print("after good reading")
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
        rob_rot += math.copysign(2, rob_rot)
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
            final_score.append((-1, closest_points[i]))
        #print(i, final_score[-1])

    # Draw score vectors
    rotated_lines = []

    for fs in final_score:
        thickness = (fs[0] * 100) // 10
        if thickness > 10:
            thickness = 4
        color = 'red'
        ncos = math.cos(math.radians(rob_rot))
        nsin = math.sin(math.radians(rob_rot))
        x1n = fs[1][2][0] * ncos - fs[1][2][1] * nsin
        y1n = fs[1][2][1] * ncos + fs[1][2][0] * nsin
        x2n = fs[1][2][2] * ncos - fs[1][2][3] * nsin
        y2n = fs[1][2][3] * ncos + fs[1][2][2] * nsin

        if fs[0] <= 0:
            thickness = 1
            color = '#ACACAC'

        rotated_lines.append((fs[0], x1n, y1n, x2n, y2n))

    nr = 31
    submap = [[0 for x in range(nr)] for y in range(nr)]
    straightened_lines = []

    #
    # Actual grid aligning
    # dx_dy Value closer to 1 is more aligned to x- or y- axis
    #
    found_start = False
    starting_point = 0
    best_angle = 90
    best_angle_pos = 0
    #print(line_score)

    for i in range(len(rotated_lines)):
        next_i = i + 1
        if next_i >= len(rotated_lines): next_i = 0

        dx = rotated_lines[i][3] - rotated_lines[i][1]
        dy = rotated_lines[i][4] - rotated_lines[i][2]
        dx_n = rotated_lines[i - 1][3] - rotated_lines[i - 1][1]
        dy_n = rotated_lines[i - 1][4] - rotated_lines[i - 1][2]
        line_scr = line_score[i]
        line_scr_n = line_score[next_i]
        line_scr_p = line_score[i - 1]

        dir_x = dx
        dir_y = dy
        dir_x_n = dx_n
        dir_y_n = dy_n

        l_len = math.hypot(dx, dy)
        dx /= l_len
        dy /= l_len
        l_len_n = math.hypot(dx_n, dy_n)
        dx_n /= l_len_n
        dy_n /= l_len_n
        angle = abs(math.degrees(math.atan2(dy_n, dx_n) - math.atan2(dy, dx)))
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

        if not found_start:
            if line_scr == -1 and line_scr_n != -1:
                starting_point = next_i
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

        straightened_lines.append((dir_x, dir_y, dx_dy, l_len))

    if not found_start:
        starting_point = best_angle_pos

    for i in range(starting_point):
        straightened_lines.append(straightened_lines.pop(0))
        line_score.append(line_score.pop(0))

    dist_from_start = res[dot_averaging[starting_point][2]][0]

    org_d_x = rotated_lines[starting_point][1]
    org_d_y = rotated_lines[starting_point][2]

    d_x = abs(org_d_x / 40)
    d_y = abs(org_d_y / 40)
    s_dir_x = straightened_lines[0][0]
    s_dir_y = straightened_lines[0][1]
    rob_pos = pickDirection(s_dir_x, s_dir_y, d_x, d_y, org_d_x, org_d_y)

    # print(1111, d_x, d_y, dist_from_start)
    start_x = 15 + rob_pos[0]
    cur_x = int(15 + rob_pos[0])
    start_y = 15 + rob_pos[1]
    cur_y = int(15 + rob_pos[1])

    # Merge concecutive lines in the same direction
    merged_lines = []
    # print(starting_point)
    s_line_size = len(straightened_lines)
    i = 0
    # print("START DOT, END DOT, DIR X, DIR Y, dx_dy, LENGTH, GOOD/BAD, START DOT, END DOT")
    #print("before line straightening")
    while i < s_line_size:
        temp_list = []
        cnt = 0
        new_len = straightened_lines[i][3]
        dx = straightened_lines[i][0]
        dy = straightened_lines[i][1]
        line_scr = line_score[i]

        for j in range(i + 1, s_line_size + 1, 1):
            k = j
            if k >= s_line_size: k = 0

            dx_n = straightened_lines[k][0]
            dy_n = straightened_lines[k][1]
            l_len_n = straightened_lines[k][3]
            line_scr_n = line_score[k]

            if line_scr != -1 and line_scr_n != -1:
                if dx == dx_n and dy == dy_n and line_scr_n != -1:
                    new_len += l_len_n
                    cnt += 1
                elif line_scr_n != -1:
                    merged_lines.append((dx, dy, straightened_lines[i][2], new_len, 1,
                                         (i + starting_point) % s_line_size, (k + starting_point) % s_line_size))
                    #print((i + starting_point) % s_line_size, (k + starting_point) % s_line_size, merged_lines[-1])
                    break
            elif line_scr == -1:
                if dx == dx_n and dy == dy_n and line_scr_n == -1:
                    new_len += l_len_n
                    cnt += 1
                else:
                    merged_lines.append((dx, dy, straightened_lines[i][2], new_len, -1,
                                         (i + starting_point) % s_line_size, (k + starting_point) % s_line_size))
                    #print((i + starting_point) % s_line_size, (k + starting_point) % s_line_size, merged_lines[-1])
                    break
            else:
                merged_lines.append((dx, dy, straightened_lines[i][2], new_len, 1, (i + starting_point) % s_line_size,
                                     (k + starting_point) % s_line_size))
                #print((i + starting_point) % s_line_size, (k + starting_point) % s_line_size, merged_lines[-1])
                break

        i += cnt + 1
    #print("after line straightening")
    first_loop = True

    if not bad_reading:
        for i in range(len(merged_lines)):

            next_i = i + 1
            if next_i >= len(merged_lines): next_i = 0
            rl_score = -1

            prev_dx = merged_lines[i - 1][0]
            prev_dy = merged_lines[i - 1][1]
            dx_dy = merged_lines[i][2]
            dir_x = merged_lines[i][0]
            dir_y = merged_lines[i][1]
            dx_n = merged_lines[next_i][0]
            dy_n = merged_lines[next_i][1]
            line_scr = merged_lines[i][4]
            line_scr_n = merged_lines[next_i][4]
            line_scr_p = merged_lines[i - 1][4]

            bad_dot_1 = (rotated_lines[merged_lines[i][5]][1], rotated_lines[merged_lines[i][5]][2])
            bad_dot_2 = (rotated_lines[merged_lines[i][6]][1], rotated_lines[merged_lines[i][6]][2])

            if dir_x != 0 and dir_y != 0:
                line_scr = -1

            if dx_dy < 1.1:
                rl_score = 0
            elif dx_dy < 1.2:
                rl_score = 1
            elif dx_dy < 1.3:
                rl_score = 2

            l_len = merged_lines[i][3]

            len_round = round_base * rounds(float(l_len) / round_base)

            nr_cells = len_round / 40
            score = 10  # - rl_score * 2

            cnt = int(rounds(nr_cells))

            start_dot_x = bad_dot_1[0] / 40
            start_dot_y = bad_dot_1[1] / 40
            b_dx = rounds(bad_dot_2[0] / 40)
            b_dy = rounds(bad_dot_2[1] / 40)
            bad_dx = rounds((bad_dot_2[0] - bad_dot_1[0]) / 40)
            bad_dy = rounds((bad_dot_2[1] - bad_dot_1[1]) / 40)
            diff = bad_dx - bad_dy

            if not first_loop and line_scr_p == -1:
                new_pos = pickDirection(dir_x, dir_y, abs(start_dot_x), abs(start_dot_y), start_dot_x, start_dot_y)
                cur_x = int(15 + new_pos[0])
                cur_y = int(15 + new_pos[1])
                # print(1111, 15+new_pos[0], 15+new_pos[1], start_dot_x, start_dot_y)

                # print(subline[i][5], 15+b_dy, 15+b_dx, b_dx, b_dy)
                # if line_scr != -1:
                # if dir_x != 0:
                #   submap[15 + b_dy + dir_x][15 + b_dx] += -10
                # else:
                #    submap[15 + b_dy][15 + b_dx - dir_y] += -10

                # print(bad_dot_1, bad_dot_2)



                # print("START DOT: "+ str(merged_lines[i][5]) + ",  POSX: " + str(cur_x)
                # + ",  POSY: " +  str(cur_y) + ",  LINE LENGTH: " + str(nr_cells) +
                # ",  CELL COUNT: " + str(cnt) + ",  N DIR X, Y: " + str(dx_n) +
                # ", " + str(dy_n) + ",  DIFF: " + str(diff) + ",  BAD DX/DY: " + str(bad_dx) + str(bad_dy))
            # print(line_scr)

            real_b_dx = 0
            real_b_dy = 0

            if line_scr == -1:
                score = -1
                dir_x = int(math.copysign(1, bad_dx))
                dir_y = int(math.copysign(1, bad_dy))
                # print(bad_dot_1, bad_dot_2)
                # print(b_dx, b_dy)

            if abs(bad_dx) > abs(bad_dy):
                real_b_dx = dir_x
            else:
                real_b_dy = dir_y

            # print(cur_x, cur_y)
            a_bad_dx = abs(bad_dx)
            a_bad_dy = abs(bad_dy)

            if nr_cells > 0:
                if line_scr != -1:
                    for j in range(cnt):
                        cnt_x = int(j * dir_x)
                        cnt_y = int(j * dir_y)
                        #print(cur_y, cur_y + cnt_y, cnt_x, cur_x + cnt_x)
                        submap[cur_y + cnt_y][cur_x + cnt_x] += score

                        # cur_x += dir_x * cnt
                        # cur_y += dir_y * cnt
                if line_scr_n != -1:
                    if line_scr != -1:
                        if dx_n == dir_y and dy_n == -dir_x:
                            if dir_x != 0:
                                cur_x += int(((cnt - 1) * dir_x) + dir_x)
                                cur_y += int(dy_n)
                            else:
                                cur_x += int(dx_n)
                                cur_y += int(((cnt - 1) * dir_y) + dir_y)
                        else:
                            if dir_x != 0:
                                cur_x += int(((cnt - 1) * dir_x))
                            else:
                                cur_y += int(((cnt - 1) * dir_y))
          #  print(cur_x, cur_y)

            first_loop = False

    minx = 1000
    miny = 1000
    maxx = 0
    maxy = 0


    for y in range(nr):
        for x in range(nr):
            score = submap[y][x]

            if (score > 0):
                if (x < minx):
                    minx = x
                if (x > maxx):
                    maxx = x
                if (y < miny):
                    miny = y
                if (y > maxy):
                    maxy = y    
    
    subb = []

    interny = 0
    rob_xy = (0,0)
    for y in range(miny, maxy + 1):
        inner = []
        internx = 0
        for x in range(minx, maxx + 1):

            vall = 1
            if (submap[y][x] == 0):
                vall = 0

            inner.append(vall)

            if (x == 15 and y == 15):
                rob_xy = (internx, interny)

                internx += 1
        subb.append(inner)
        interny += 1
                
            
    return (subb, rob_xy)


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
            print(len(mapp))
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
