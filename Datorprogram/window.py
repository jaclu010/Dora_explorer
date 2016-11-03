from tkinter import *
from time import gmtime, strftime

root = Tk()
root.geometry("1280x720")

class Window(Frame):
    def __init__(self, master = None):
        Frame.__init__(self, master)
        self.master = master
        self.master.title("Dora The Explorer")
        self.pack(fill=BOTH, expand=1)

        menu = Menu(self.master)
        self.master.config(menu=menu)

        file = Menu(menu)
        file.add_command(label="Clear robotLog.txt", command=clearRobotLog)
        file.add_command(label="Exit", command=self.close)
        menu.add_cascade(label="File", menu=file)

        self.leftFrame = Frame(master)
        self.leftFrame.grid(row=0, column=0)

        self.mapCanvas = self.initCanvas()
        self.textBox = self.initText()
        self.initButtons()
        self.cbSensor, self.cbMovement = self.initCheckboxes()

        if self.cbSensor.grab_status() == 0:
            print("heeeeel yeaaaah!")

    def initCheckboxes(self):
        cbSensor = Checkbutton(self, text="Show sensor data")
        #cbSensor.deselect()
        cbSensor.place(x=0, y=460)

        cbMovement = Checkbutton(self, text="Show movement data")
        #cbMovement.deselect()
        cbMovement.place(x=130, y=460)
        return cbSensor, cbMovement

    def initCanvas(self):
        mapCanvas = Canvas(self, bg="red", width="780", height="720")
        mapCanvas.place(x=500, y=0)
        return mapCanvas

    def initText(self):
        dataTextBox = Text(self, state=DISABLED, bg="gray62", width="62", height="30")
        dataTextBox.place(x=0, y=0)

        #button = Button(dataTextBox, text="Click")
        #dataTextBox.window_create(INSERT, window=button)

        return dataTextBox

    def initButtons(self):
        buttonHeight = 5
        buttonWidth = 10
        buttonColor = "gray42"
        buttonActiveColor = "gray58"

        buttonRight = Button(self, command=self.moveRight, bg=buttonColor, activebackground = buttonActiveColor, text="Right", width=buttonWidth, height=buttonHeight)
        buttonLeft = Button(self, command=self.moveLeft, bg=buttonColor, activebackground = buttonActiveColor, text="Left", width=buttonWidth, height=buttonHeight)
        buttonForward = Button(self, command=self.moveForward, bg=buttonColor, activebackground = buttonActiveColor, text="Forward", width=buttonWidth, height=buttonHeight)
        buttonBack = Button(self, command=self.moveBackward, bg=buttonColor, activebackground = buttonActiveColor, text="Down", width=buttonWidth, height=buttonHeight)

        buttonY = 600

        buttonRight.place(x=285, y=buttonY)
        buttonLeft.place(x=115, y=buttonY)
        buttonForward.place(x=200, y=510)
        buttonBack.place(x=200, y=buttonY)

    def addText(self, text):
        self.textBox.insert(END, text)

    def close(self):
        root.withdraw()
        sys.exit()

    root.bind('<Escape>', close)

    def moveRight(self):
        self.textBox.config(state=NORMAL)
        Window.printToLog(self, text="Right")
        self.textBox.config(state=DISABLED)
        print("Right")

    def moveLeft(self):
        self.textBox.config(state=NORMAL)
        Window.printToLog(self, text="Left")
        self.textBox.config(state=DISABLED)
        print("Left")

    def moveForward(self):
        self.textBox.config(state=NORMAL)
        Window.printToLog(self, text="Forward")
        self.textBox.config(state=DISABLED)
        print("Forward")

    def moveBackward(self):
        self.textBox.config(state=NORMAL)
        Window.printToLog(self, text = "Backward")
        self.textBox.config(state=DISABLED)
        print("Backward")

    def printToLog(self, text):
        self.textBox.config(state=NORMAL)

        string = strftime("%Y-%m-%d %H:%M:%S", gmtime()) +"\t"+text + "\n"
        with open('robotLog.txt', 'a') as file:
            file.write(string)

        self.textBox.insert("0.0", string)
        self.textBox.config(state=DISABLED)

def clearRobotLog():
    open('robotLog.txt', 'w').close()

def main():
    app = Window(root)
    root.mainloop()


if __name__ == '__main__':
    main()