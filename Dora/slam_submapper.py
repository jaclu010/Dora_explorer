#####
#
# slam_submapper.py
# Updated: 20/12 2016
# Authors: Jacob Lundberg, Johan Nilsson
#
#####

import math


def rounds(val):
    """
    Always round .5 up
    """
    return rounds2(val, 0.5)


def rounds2(val, base):
    """
    Round VAL up if equal to BASE.
    Opposite direction for negative VAL.
    """
    if abs(val) % 1 >= base:
        return int(math.ceil(abs(val)) * math.copysign(1, val))
    else:
        return int(math.floor(abs(val)) * math.copysign(1, val))



def pickDir(dir_x, dir_y, dist_x, dist_y):
    """
    Direction compensation for calculating robot grid position
    """
    if dir_y == 1:
        if dist_y < 0:
            y = rounds2(dist_y, 1)
        else:
            y = rounds2(dist_y, 0)
        x = rounds2(dist_x, 1)
    elif dir_y == -1:
        if dist_y < 0:
            y = rounds2(dist_y, 1)
        else:
            y = rounds2(dist_x, 0)
        if dist_x > 0:
            x = rounds2(dist_x, 0)
        else:
            x = rounds2(dist_x, 1)
    elif dir_x == 1:
        if dist_x < 0:
            x = rounds2(dist_x, 1)
        else:
            x = rounds2(dist_x, 0)
        if dist_y < 0:
            y = rounds2(dist_y, 1)
        else:
            y = rounds2(dist_y, 0)
    elif dir_x == -1:
        if dist_x < 0:
            x = rounds2(dist_x, 1)
        else:
            x = rounds2(dist_x, 0)
        y = rounds2(dist_y, 1)
    
    return (int(x), int(y))


def vectorIntersection(x1, y1, x2, y2, x3, y3, x4, y4):
    """
    Returns point of intersection between two vectors
    """
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / \
         ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / \
         ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
    return (px, py)


def getIndex(item):
    """
    Help function for sorting intersection array
    """
    return item[2]


def roundHalf(val):
    """
    Round VAL to nearest .5 value
    """
    return round(val * 2.0) / 2.0


def mapper(read):
    """
    Main algorithm to convert an array of measurements to a 2D grid array
    Input: [Laser readings]
    Returns: subb - 2D array

    !!Note!!: This 'script' is not designed for performance. Various unnecessary for loops
              exist. Unnecessary calculations may occur.
    """

    # If set to TRUE, stop calculations
    bad_reading = False

    # Use extra intersections at the start and end of each good reading
    # May enhace results when a lot of corners exist
    set_extra_intersections = False

    # Size of array of measurements
    size = len(read)

    # ----------
    # VARIABLES - to configure and enhance the result of a reading
    # ----------

    # No. tiles is rounded up if line length is larger than TILE_AVERAGE
    tile_average = 0.5

    # Se TILE_AVERAGE, but different value for first tile
    first_tile_average = 0.45
    
    # Compensate for hall-sensor triggering to early, # degrees
    corr = 7.0

    # Size of wall segments
    tile_size = 40

    # Mark reading as unreliable if less than MIN_DIST
    min_dist = 40

    # Maximum allowed reading value
    max_dist = 10000

    # Mark reading as bad if larger than D_MEAN_COVAR
    d_mean_covar = 11

    # Mark reading as bad if larger than D_DELTA_COVAR
    d_delta_covar = 1.65

    # Mark reading as possible corner if less than TWO_DELTA_COVAR 
    two_delta_covar = 45

    # Trigger line estimation if no. good readings in a row is larger than GOOD_READING_COUNT
    good_reading_count = 3

    # Keep vectors if angle less than ANGLE_DEVIATION_FILTER from average angle 
    angle_deviation_filter = 8

    # Average 'interections' if less than DOT_FILTER_VALUE cm from each other
    dot_filter_value = 18

    # Keep 'intersections' less than DOT_MIN_DIST from nearest measurement
    dot_min_dist = 7

    # Add score to line if measurement is less than LINE_SCORE_DIST cm from line
    line_score_dist = 6

    # Add intersection next or previous measurement is larger than DOT_DIST_CUT cm from current measurement
    dot_dist_cut = 20  # 30

    # Set line to bad line if between these values (degrees)
    lower_bound_angle = 30
    upper_bound_angle = 60

    # Discard reading if no. bad measurments is greater than SIZE / UNCERTAIN_THRESHOLD  
    uncertain_threshold = 1.5

    #-----


    res = []
    sin_cos = []
    intersections = []
    delta = []
    two_delta = []
    double_delta = []
    delta_mean = []
    good_readings = []
    
    # Legitimacy check 1
    if size > 0:
        step = 360.0 / size
    else:
        bad_reading = True

    # STEP 1 : convert to and filter dots
    # ----------
    
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

    # Extract cartesian coordinates
    for j in range(size):
        x = math.cos(math.radians(res[j][1])) * res[j][0]
        y = -math.sin(math.radians(res[j][1])) * res[j][0]
        sin_cos.append((x, y))

    # Calculate delta values
    # Calculate angle between reading + 2 and reading - 2
    for i in range(size):
        x = sin_cos[i][0]
        y = sin_cos[i][1]
        dx = x - sin_cos[i - 1][0]
        dy = y - sin_cos[i - 1][1]
        delta.append((dx, dy))
        dist = math.hypot(x, y)

        d_next_i = i + 2
        if d_next_i > size - 2:
            d_next_i -= size

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
    # Check distance to next and previous measurement
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
    # Sloppy, no loop closing 
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
    # Used to find good readings in a row
    # ----------------------
    # d = 0 - Good measurement
    # d = 2 - delta_mean triggered
    # Orange - Too high delta values
    # d = 3 - uncertain measurement
    dots = [None] * size
    bad_readings_cnt = 0
    uncertain_values = 0
    for i in range(size):
        x = sin_cos[i][0]
        y = sin_cos[i][1]
        d = 0
        if read[i] < min_dist or read[i] > max_dist:
            d = 3  
            uncertain_values += 1
        if abs(delta_mean[i][0]) + abs(delta_mean[i][1]) > d_mean_covar:
            bad_readings_cnt += 1
            d = 2
        elif abs(double_delta[i][0]) > d_delta_covar and abs(double_delta[i][1]) > d_delta_covar:
            d = 1
            bad_readings_cnt += 1
        if two_delta[i] < two_delta_covar:
            d = 4

        dots[i] = d

    # Legitimacy check 2
    if not bad_reading:
        if uncertain_values > (size / uncertain_threshold):
            bad_reading = True

    # Traverse readings and find good readings in a row
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

    # Merge first and last element if they are next to each other, and good readings
    if len(good_readings) > 0 and good_readings[-1][1] == size - 1 and good_readings[0][0] == 0:
        good_readings[0] = (good_readings[-1][0] - size, good_readings[0][1],
                            good_readings[-1][2] + good_readings[0][2])
        good_readings.pop()


    # STEP 2 : lines and vectors    
    # ----------
    # Calculate lines from good readings
    # Calculate vectors from lines
    # Remove bad lines and get rotation
    # ----------
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
            # May cause troble, may not
            print("----------------WARNING MAP MAYBE WRONG------------------")
        lines.append((valX, valY, d_distX, d_distY, good_readings[i][2]))

    # Create vectors
    # Add intersections if chosen
    for i in range(num_vectors):
        x0 = lines[i][2] - line_expansion * lines[i][0]
        x1 = lines[i][2] + line_expansion * lines[i][0]
        y0 = lines[i][3] - line_expansion * lines[i][1]
        y1 = lines[i][3] + line_expansion * lines[i][1]

        _x0 = sin_cos[good_readings[i][0]][0]
        _x1 = sin_cos[good_readings[i][1]][0]
        _y0 = sin_cos[good_readings[i][0]][1]
        _y1 = sin_cos[good_readings[i][1]][1]

        if set_extra_intersections:
            intersections.append((_x0, _y0, good_readings[i][0]))
            intersections.append((_x1, _y1, good_readings[i][1]))

        vectors.append((x0, y0, x1, y1))
        angles.append((math.degrees(math.atan2(-lines[i][1], lines[i][0])), i, 0))

    # Angle is counted from nearest x/y-axis
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

    # Legitimacy check 3
    if angle_deviation:
        rob_rot /= len(angle_deviation)
    else:
        bad_reading = True
        rob_rot = 0

    # STEP 3 : intersections
    # ----------
    # Calculate intersection points for all vectors
    # ----------
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

            best_len = max_dist
            cur_nr = -max_dist
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
    # Ignore intersections away from measurements
    # Average out intersections near each other
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

    # Filter out intersections near each other
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


    # STEP 4: new lines and score
    # -----
    # Calculate hit percent of dots on every line
    # -----

    closest_points = []
    line_score = []
    for i in range(len(new_lines)):
        l = new_lines[i]
        score = 0
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

            if dist < line_score_dist:
                score += 1

        # Check no. readings between intersections
        # Otherwise some 'not walls' may be interpreted as walls
        # Line score: -1 - Probably not a wall along this line
        if (line_len < 20 and d_readings < 1) or (line_len > 25 and d_readings < 5) or (
                line_len > 40 and d_readings < 5) or (line_len > 60 and d_readings < 6) or (
                line_len > 80 and d_readings < 6) or (line_len > 100 and d_readings < 9):
            closest_points.append((closest_1, closest_2, l))
            line_score.append(-1)
        else:
            closest_points.append((closest_1, closest_2, l))
            line_score.append(score)

    # Hit percent
    # May be higher than 100% in some cases, depends on LINE_SCORE_DIST
    final_score = []
    for i in range(len(closest_points)):
        if closest_points[i][0] != closest_points[i][1]:
            final_score.append((line_score[i] / (closest_points[i][1] - closest_points[i][0]), closest_points[i]))
        else:
            final_score.append((-1, closest_points[i]))

    # Rotate lines, depends on ROB_ROT
    # Thickness is used for scoring
    rotated_lines = []
    for i in range(len(final_score)):
        fs = final_score[i]
        thickness = (fs[0] * 100) // 10
        if thickness > 10:
            thickness = 4
        ncos = math.cos(math.radians(rob_rot))
        nsin = math.sin(math.radians(rob_rot))
        x1n = fs[1][2][0] * ncos - fs[1][2][1] * nsin
        y1n = fs[1][2][1] * ncos + fs[1][2][0] * nsin
        x2n = fs[1][2][2] * ncos - fs[1][2][3] * nsin
        y2n = fs[1][2][3] * ncos + fs[1][2][2] * nsin

        if line_score[i] <= 0 or fs[0] <= 0:
            thickness = 1

        rotated_lines.append((thickness, x1n, y1n, x2n, y2n))

    # Create the submap
    nr = 31
    submap = [[0 for x in range(nr)] for y in range(nr)]
    straightened_lines = []

    # STEP 5: Aligning and scoring
    # ----------
    # Actual grid aligning
    # Determine direction based on (dx + dy) value.
    # Should output (!=0, 0) or (0, !=0) in (x, y) direction
    # dx_dy Value closer to 1 is more aligned to x- or y- axis
    # Calculate best corner to be used if later checks fails
    # ----------
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
        line_scr_p = line_score[i - 1]
        dir_x = dx
        dir_y = dy

        l_len = math.hypot(dx, dy)
        dx /= l_len
        dy /= l_len
        l_len_n = math.hypot(dx_n, dy_n)
        dx_n /= l_len_n
        dy_n /= l_len_n
        angle = abs(math.degrees(math.atan2(dy_n, dx_n) - math.atan2(dy, dx)))
        this_line_angle = abs(math.degrees(math.atan2(dy, dx)))

        if line_angle > 180:
            this_line_angle -= 270
        else:
            this_line_angle -= 90
        this_line_angle = abs(this_line_angle)

        if angle > 180:
            angle -= 270
        else:
            angle -= 90

        angle = abs(angle)
        if angle < best_angle:
            best_angle = angle
            best_angle_pos = i

        dx_dy = abs(dx) + abs(dy)

        if dx_dy < 1.3:
            if abs(dx) > abs(dy):
                dir_x = rounds(dx)
                dir_y = 0
            else:
                dir_y = rounds(dy)
                dir_x = 0

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

        if lower_bound_angle < this_line_angle < upper_bound_angle:
            if l_len > 40:
                line_score[i] = -1

        straightened_lines.append((dir_x, dir_y, dx_dy, l_len, rotated_lines[i][0]))

    # Pick the closest intersection as a start of draw
    best_dist = max_dist
    for i in possible_starting_points:
        x = rotated_lines[i][1]
        y = rotated_lines[i][2]
        dist = math.hypot(x, y)
        if dist < best_dist:
            best_dist = dist
            starting_point = i

    if not found_start:
        starting_point = best_angle_pos

    # Rotate arrays so starting line is first
    for i in range(starting_point):
        straightened_lines.append(straightened_lines.pop(0))
        line_score.append(line_score.pop(0))

    # ----------
    # Merge concecutive lines in the same direction
    # ----------
    merged_lines = []
    s_line_size = len(straightened_lines)
    i = 0
    while i < s_line_size:
        cnt = 0
        new_len = straightened_lines[i][3]
        dx = straightened_lines[i][0]
        dy = straightened_lines[i][1]
        line_scr = line_score[i]
        percent_score = straightened_lines[i][0]

        for j in range(i + 1, s_line_size + 1, 1):
            k = j
            if k >= s_line_size: k = 0
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
                    score = math.ceil(math.sqrt(line_scr * abs(percent_score) * 20 / new_len + cnt + 3))
                    merged_lines.append((dx, dy, straightened_lines[i][2], new_len, 1,
                                         (i + starting_point) % s_line_size, (k + starting_point) % s_line_size, score))
                    break
            elif line_scr == -1:
                if dx == dx_n and dy == dy_n and line_scr_n == -1:
                    new_len += l_len_n
                    cnt += 1
                else:
                    merged_lines.append((dx, dy, straightened_lines[i][2], new_len, -1,
                                         (i + starting_point) % s_line_size, (k + starting_point) % s_line_size, -1))
                    break
            else:
                score = math.ceil(math.sqrt(line_scr * abs(percent_score) * 20 / new_len + cnt + 3))
                merged_lines.append((dx, dy, straightened_lines[i][2], new_len, 1, (i + starting_point) % s_line_size,
                                     (k + starting_point) % s_line_size, score))
                break
        i += cnt + 1

    # -----
    # Add concecutive good lines to new lists 
    # Fully ignores lines calculated as bad
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

    # Legitimacy check 4
    if not bad_reading:
        if bad_score_cnt / size > 0.65:
            bad_reading = True

    # Draw the aligned lines and fill grid based on their position
    if not bad_reading:
        first_line = merged_lines_again[0][0]
        start_dir = (first_line[0], first_line[1])
        f_line_end_dot = (rotated_lines[first_line[6]][1], rotated_lines[first_line[6]][2])
        start_pos_x = f_line_end_dot[0]
        start_pos_y = f_line_end_dot[1]
        pos_corr = pickDir(start_dir[0], start_dir[1], start_pos_x / 40, start_pos_y / 40)
        first_x = x = 15 + pos_corr[0]
        first_y = y = 15 + pos_corr[1]

        # Start drawing from the end dot of the first line, this is most probably a corner
        for lines in merged_lines_again:
            line_end_dot_nr = lines[0][6]
            line_end_dot = (rotated_lines[line_end_dot_nr][1], rotated_lines[line_end_dot_nr][2])
            for i in range(len(lines)):
                next_i = i + 1
                if next_i >= len(lines): next_i = 0

                line_dist = roundHalf(
                    math.hypot(rotated_lines[lines[i][5]][0] / 40, rotated_lines[lines[i][5]][1] / 40))
                dir_x = lines[i][0]
                dir_y = lines[i][1]
                l_len = lines[i][3]
                cnt = rounds2(l_len / 40, tile_average)

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
                if line_scr_n == -1 or line_scr_p == -1:
                    score -= 1
                score += 5 - round(line_dist / 2)
                if score < 1 or line_len < 25:
                    score = 1
                    
                # Draw the first line backwards
                if i == 0:
                    if dir_x == -1:
                        extra = (1, 1)
                    elif dir_y == 1:
                        extra = (1, 1)
                    else:
                        extra = (0, 0)
                    x = first_x + rounds2((line_end_dot[0] - start_pos_x) / 40, first_tile_average)
                    y = first_y + rounds2((line_end_dot[1] - start_pos_y) / 40, first_tile_average)

                    for j in range(cnt):
                        cnt_x = j * dir_x + dir_x + extra[0]
                        cnt_y = j * dir_y + extra[1]
                        if 0 <= y - cnt_y < nr:
                            if 0 <= x - cnt_x < nr:
                                submap[y - cnt_y][x - cnt_x] += score

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
                    x = next_x
                    y = next_y

    # Slice the grid, send only the relevant parts
    minx = 1000
    miny = 1000
    maxx = 0
    maxy = 0

    for i in range(nr):
        for j in range(nr):
            score = submap[i][j]
            if (score > 0):
                if j < minx:
                    minx = j
                if j > maxx:
                    maxx = j
                if (i < miny):
                    miny = i
                if (i > maxy):
                    maxy = i
    subb = []
    interny = 0
    rob_xy = (0, 0)
    for y in range(miny, maxy + 1):
        inner = []
        internx = 0
        for x in range(minx, maxx + 1):
            vall = 1
            if (submap[y][x] == 0):
                vall = 0
            dx = x - 15
            dy = y - 15
            inner.append(vall)
            if (x == 15 and y == 15):
                rob_xy = (internx, interny)

            internx += 1
        subb.append(inner)
        interny += 1
    return (subb, rob_xy)
