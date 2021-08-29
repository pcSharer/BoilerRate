#import boilerRate
from tkinter import *

master = Tk()
Label(master, text="First Name").grid(row=0)
Label(master, text="Last Name").grid(row=1)

e1 = Entry(master)
e2 = Entry(master)

e1.grid(row=0, column=1)
e2.grid(row=1, column=1)

mainloop( )


# #Import tkinter library
# from tkinter import *
# #Create an instance of Tkinter frame or window
# win= Tk()
# #Set the geometry of tkinter frame
# win.geometry("250x250")
# def callback():
#    Label(win, text="Hello World!", font=('Century 20 bold')).pack(pady=4)
# #Create a Label and a Button widget
# btn=Button(win, text="Press Enter", command= callback)
# btn.pack(ipadx=10)
# win.bind('<Return>',lambda event:callback())
# win.mainloop()