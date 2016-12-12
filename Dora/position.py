import math



#  given distances traveled by each wheel, updates the
#  wheel position globals
def update_wheel_position(l, r):
    WHEELBASE = 16.5  # cm
    Lx = -WHEELBASE/2.0
    Ly = 0.0

    #right wheel
    Rx = WHEELBASE/2.0
    Ry = 0.0

    #print("Old wheel positions: (%lf,%lf) (%lf,%lf)\n" % (Lx, Ly, Rx, Ry))
    if (abs(r - l) <= 2):
        #  If both wheels moved about the same distance, then we get an infinite
        #  radius of curvature.  This handles that case.
                  
        #  find forward by rotating the axle between the wheels 90 degrees
        axlex = Rx - Lx
        axley = Ry - Ly

        forwardx = -axley
        forwardy = axlex

        #  normalize
        length = math.sqrt(forwardx**2 + forwardy**2)
        forwardx = forwardx / length
        forwardy = forwardy / length

        #  move each wheel forward by the amount it moved
        Lx = Lx + forwardx * l
        Ly = Ly + forwardy * l

        Rx = Rx + forwardx * r
        Ry = Ry + forwardy * r
        #  print("New wheel positions: (%lf,%lf) (%lf,%lf)\n" % (Lx, Ly, Rx, Ry))
        return (Lx, Ly, Rx, Ry)

    #  radius of curvature for left wheel
    rl = WHEELBASE * l / (r - l)

    #print("Radius of curvature (left wheel): %f" % float(rl))

    #  angle we moved around the circle, in radians
    #  theta = 2 * PI * (l / (2 * PI * rl)) simplifies to:
    theta = l / rl

    #print("Theta: %f radians" % theta)

    #Find the point P that we're circling

    Px = Lx + rl*((Lx-Rx)/WHEELBASE)
    Py = Ly + rl*((Ly-Ry)/WHEELBASE)

    #print("Center of rotation: (%f, %f)" % (Px, Py))

    #  Translate everything to the origin
    Lx_translated = Lx - Px
    Ly_translated = Ly - Py

    Rx_translated = Rx - Px
    Ry_translated = Ry - Py

    #print("Translated: (%f,%f) (%f,%f)" % (Lx_translated, Ly_translated, Rx_translated, Ry_translated))

    #  Rotate by theta
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    #print("cos(theta)=%f sin(theta)=%f" % (cos_theta, sin_theta))

    Lx_rotated = Lx_translated*cos_theta - Ly_translated*sin_theta
    Ly_rotated = Lx_translated*sin_theta + Ly_translated*sin_theta

    Rx_rotated = Rx_translated*cos_theta - Ry_translated*sin_theta
    Ry_rotated = Rx_translated*sin_theta + Ry_translated*sin_theta

    #print("Rotated: (%f,%f) (%f,%f)" % (Lx_rotated, Ly_rotated, Rx_rotated, Ry_rotated))
    #Translate back
    Lx = Lx_rotated + Px
    Ly = Ly_rotated + Py

    Rx = Rx_rotated + Px
    Ry = Ry_rotated + Py
    ##print("New wheel positions: (%lf,%lf) (%lf,%lf)\n" % (Lx, Ly, Rx, Ry))
    return (Lx,Ly,Rx,Ry)

if __name__ == '__main__':
    print("Old wheel positions: (%lf,%lf) (%lf,%lf)\n" % (Lx, Ly, Rx, Ry))
    update_wheel_position(4, 6)
    print("New wheel positions: (%lf,%lf) (%lf,%lf)\n" % (Lx, Ly, Rx, Ry))
