import math

from tkinter import *

root = Tk()
root.title("SLAM DUNKKK")

c = Canvas(root, width=400, height=400)
c.pack()

width = 400
height = 400

read = [68, 66, 66, 66, 67, 67, 67, 69, 70, 72, 72, 76, 79, 83, 83, 88, 92, 95, 95, 102, 100, 100, 95, 94, 91, 91, 90,
        89, 89, 89, 89, 90, 90, 90, 92, 95, 95, 98, 104, 104, 104, 95, 93, 93, 90, 86, 82, 79, 79, 76, 75, 73, 73, 72,
        73, 73, 73, 74, 76, 78, 80, 80, 83, 87, 90, 90, 94, 95, 95, 101, 97, 92, 92, 91, 91, 91, 91, 89, 89, 88, 88,
        87, 88, 89, 80, 91, 91, 91, 91, 91, 95, 94, 94, 92, 85, 81, 81, 77, 75, 71, 69, 69]


# def slamDunk(read=[]):
size = len(read)

step = 0.0
corr = 7.0  # degrees
step = 360 / size
res = []
angle = 0

for i in range(size):
    angle = (i * step) - corr

    if (angle < 0):
        angle = 360 - abs(i * step - corr)

    # print(angle)
    res.append((read[i], angle))

# print(res)
sincos = []

for j in range(size):
    sincos.append((math.cos(math.radians(res[j][1])) * res[j][0], -math.sin(math.radians(res[j][1])) * res[j][0]))

delta = []
dx = 0
dy = 0

for i in range(size):
    if i == 0:
        dx = sincos[i][0] - sincos[size - 1][0]
        dy = sincos[i][1] - sincos[size - 1][1]
    else:
        dx = sincos[i][0] - sincos[i - 1][0]
        dy = sincos[i][1] - sincos[i - 1][1]

    delta.append((dx, dy))

doubledelta = []
ddx = 0
ddy = 0

for i in range(size):
    if i == 0:
        ddx = delta[i][0] - delta[size - 1][0]
        ddy = delta[i][1] - delta[size - 1][1]
    else:
        ddx = delta[i][0] - delta[i - 1][0]
        ddy = delta[i][1] - delta[i - 1][1]

    doubledelta.append((ddx, ddy))

changeX = 0.0
changeY = 0.0
deltaMean = []

for i in range(size):

    changeX = 0.0
    changeY = 0.0

    if i > 5:
        changeX += doubledelta[i][0]
        changeY += doubledelta[i][1]
        changeX += doubledelta[i - 1][0]
        changeY += doubledelta[i - 1][1]
        changeX += doubledelta[i - 2][0]
        changeY += doubledelta[i - 2][1]
        changeX += doubledelta[i - 3][0]
        changeY += doubledelta[i - 3][1]
        changeX += doubledelta[i - 4][0]
        changeY += doubledelta[i - 4][1]
        changeX /= 5
        changeY /= 5

    deltaMean.append((changeX, changeY))
# print(str(i) + ' ' + str(changeX))
# print(str(i) + ' ' + str(changeY))

for i in range(size):
    print(str(deltaMean[i]) + "   \t   " + str(delta[i]) + "  \t  " + str(doubledelta[i]) + "  \t  " + str(res[i]))
    x = sincos[i][0]
    y = sincos[i][1]
    if i == 0:
        c.create_oval(x + 195, y + 195, x + 205, y + 205, fill='green')
    elif i < 10:
        c.create_oval(x + 195, y + 195, x + 205, y + 205, fill='red')
    else:
        c.create_oval(x + 195, y + 195, x + 205, y + 205)

    if abs(doubledelta[i][0]) > .8 and abs(doubledelta[i][1]) > .8:
        c.create_oval(x + 195, y + 195, x + 205, y + 205, fill='orange')

    if abs(deltaMean[i][0]) > .2 and abs(deltaMean[i][1] > 0.2):
        c.create_oval(x + 195, y + 195, x + 205, y + 205, fill='yellow')

            # if(i > 20 and i < 50):
    #	change += doubledelta[i][0]


# print(change)



mainloop()
