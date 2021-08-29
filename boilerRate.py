import time
import tkinter as tk
from tkinter import ttk		# For Notebook
from tkinter import *			# For TopLevel() and Text

from gethistory import GetHistory
from globals import nomRate, sausageRate, noteBookWidth, noteBookHeight, settingsShared

import graphTab as gt

try:
	from icecream import ic
except ImportError:  # Graceful fallback if IceCream isn't installed.
	ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa
ic.enable()
# Other things similar to Icecream:
#   (See https://medium.com/swlh/all-python-debugging-tools-you-need-to-know-in-2020-e3ff66b8f318)
#   objprint, PySnooper, hunter, Watchpoints, VizTracer (and more)

# results = Results(0,'',0,0,0,0,0,0,0,'',0,0,'','')
# results.dataLength = 18
# results.timeNow		 = "11:32"
# results.tempNow		 = 102.3
# results.last1			 = 12
# results.last2			 = 13
# results.last4			 = 14
# results.last8			 = 15
# results.last16		 = 16
# results.want			 = 145
# results.atTime		 = "11:45"
# results.need			 = 26
# results.lateness	 = 27
# results.finishTimeThis	= "11:00"
# results.finishTimeTarget= "12:13"


cruiseTemp = 170
day1Temp = 145
day1Finish = "14:30"
cruiseTime = "11:45"		# Might be overridden

# root window
_widthCnv = noteBookWidth+15 
_heightCnv = noteBookHeight+110
geomStr = f'{_widthCnv}x{_heightCnv}'
root = tk.Tk()
root.geometry(geomStr)
root.title('Waratah Warm-up')

# create a notebook

def rememberConfig(virtualEvent):
	continuedBelow(virtualEvent)		# . . . for programmer's convenience (while keeping interpretter happy)
	 

notebook = ttk.Notebook(root, height=noteBookHeight, width=noteBookWidth)
notebook.pack(pady=10, expand=True)
notebook.bind("<<NotebookTabChanged>>", rememberConfig)		# Just calls continuedBelow() in the "Analyse" code

# create frames
frSetup   = ttk.Frame(notebook, width=300, height=500)		# Dimensions overruled by "notebook = ttk.Notebook( . . . " above
frAnalyse = ttk.Frame(notebook, width=300, height=500)
frGraph   = ttk.Frame(notebook, width=300, height=500)

frSetup.pack  (fill='both', expand=True)
frAnalyse.pack(fill='both', expand=True)
frGraph.pack  (fill='both', expand=True)

# add frames to notebook

notebook.add(frSetup,   text='Setup')
notebook.add(frAnalyse, text='Analyse')
notebook.add(frGraph,   text='Graph')
notebook.pack(expand = 1, fill ="both")

canvas = Canvas(frGraph)
canvas.create_text(100, 100, anchor=W, angle=90, text="130 deg C")
canvas.create_text(10, 10, anchor=W, angle=90, text="At 10,10")


canvas.pack(fill = BOTH, expand = 1)
canvas.update()


########################################
# "Setup" tab
########################################

# radio buttons
realOrHistRadioPick = tk.IntVar()

# Declare some globals (with junk vlues)
finishTemp = -2
isRealTimeSelected =True


# Called when a radio button is clicked
# Updates the  text boxes on the Setup page with the selected configuration
def radioCall():
	global isRealTimeSelected, finishTemp

	#ic(realOrHistRadioPick.get())
	index = int(realOrHistRadioPick.get())
	isRealTimeSelected = radioDefinition[index][1] == "Real time"
	isFirstDay.set(radioDefinition[index][4])
	historyDate.set(radioDefinition[index][2])
	historyTime.set(radioDefinition[index][3])
	comment.set(radioDefinition[index][5])

	if isFirstDay.get(): 
		finishTemp = day1Temp
		finishTime.set(day1Finish)
	else:
		finishTemp = cruiseTemp
		finishTime.set(cruiseTime)

	setFinish()


def setFinish():
	global cruiseTemp, day1Temp, day1Finish, cruiseTime, finishTemp, isRealTimeSelected

	temperatureInfo.set(f"Warm-up finish at {finishTime.get()}, with temperature {finishTemp}")
# End of SetFinish()


row = 0
ttk.Label(frSetup, text ="Setup page", font=("Arial", 18)).grid(column = 0, row = row, columnspan=2)
row +=1


radioDefinition = [
	(0, "Real time",     "Today",      "Now",   True,  ""),
	(1, "History day 1", "2021-06-18", "10:21", True,  "Too slow at first, then too fast"), 
	(2, "History day 2", "2021-06-19", "10:21", False, "Late from about 8am till 10:55, then early")
]

i = 0
for option in (radioDefinition):
	r = ttk.Radiobutton(
			frSetup,
			text=option[1],
			value=option[0],
			variable=realOrHistRadioPick,
			command=radioCall
	).grid(column = 0, row = row, sticky=W, padx=9, columnspan=2)
	#r.pack(fill='x', padx=5, pady=5)
	row +=1



isFirstDay = BooleanVar()
Checkbutton(frSetup, text='First day', variable=isFirstDay, command=setFinish).grid(row=row, column=1, sticky=W, padx=9)
row +=1

historyDate = StringVar()
Label(frSetup, text='Date:').grid(row=row, column=0, sticky=E, padx=9)
Entry(frSetup, textvariable = historyDate).grid(row=row, column=1)
row +=1

historyTime = StringVar()
Label(frSetup, text='Time:').grid(row=row, column=0, sticky=E, padx=9)
Entry(frSetup, textvariable = historyTime).grid(row=row, column=1)
row +=1

finishTime = StringVar()
Label(frSetup, text='Finish time:').grid(row=row, column=0, sticky=E, padx=9)
Entry(frSetup, textvariable=finishTime).grid(row=row, column=1)
row +=1

comment = IntVar()
Label(frSetup, text='Comment:').grid(row=row, column=0, sticky=E, padx=9)
Entry(frSetup, textvariable = comment).grid(row=row, column=1)
row +=1

Label(frSetup, text="  .  .  .  .  .  .  .").grid(row=row, column=1, sticky=W, columnspan=2, padx=9)
row +=1

temperatureInfo = StringVar()
Label(frSetup, textvariable = temperatureInfo).grid(row=row, column=0, sticky=W, columnspan=2, padx=9)
row +=1

rateTxt = f"Target rate = {nomRate}, Sausage rate = {round(sausageRate)}" 
Label(frSetup, text=rateTxt).grid(row=row, column=0, sticky=W, columnspan=2, padx=9)
row +=1

# Make RealTime the default radio-button option
realOrHistRadioPick.set(0)
#ic(f"Setting initial radio index to {realOrHistRadioPick.get()}")
radioCall()		# Update fields with values corresponding to the initial radio-button selection



########################################
# "Analyse" tab
########################################
lastTab = 0
setupHasChanged = True

def continuedBelow(virtualEvent):		# Called by rememberConfig() when tab changes
	global nomRate, settingsShared, finishTemp, isRealTimeSelected, setupHasChanged, lastTab

	actionNeeded = lastTab == 0
	lastTab = virtualEvent.widget.index("current")

	if actionNeeded: 	# We have just left the set-up tab (0), so save the new settings
		#ic(f"setupHasChanged was {setupHasChanged}, now True")
		setupHasChanged = True
		settings = settingsShared		# mmm ... Let's change the name
		settings.isFirstDay = isFirstDay.get()
		settings.plan_riseRate = nomRate
		settings.isRealTime = isRealTimeSelected

		dateAndTimeStr = historyDate.get() + ' ' + historyTime.get()
		if dateAndTimeStr == "Today Now":
			dateAndTimeStr = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time()))
		settings.dateAndTimeStr = dateAndTimeStr

		setFinish()
		settings.finishTemp = finishTemp		# To ensure that finishTemp is set

		settings.finishTime = finishTime.get()
		#ic(settings.finishTime)

		strDayNow = "Today"
		if settings.isRealTime:
			tempTxt ="Real time"
		else:
			tempTxt ="Historical"
			strDayNow = historyDate.get()

		realOrHist.set(tempTxt + " analysis")

		if settings.isFirstDay:
			strDayNow = strDayNow + ", first day."
		else:
			strDayNow = strDayNow + ", second day."

		strMission = f"End temperature = {settings.finishTemp} at {settings.finishTime}" 
		endConditions.set(strDayNow + ' ' + strMission)
		settings.strDayNow = strDayNow
		settings.strMission = strMission

		## Decided not to do this any more
		# if settings.isFirstDay:
		# 	lateness.set("n/a")
		# else:
		# 	endAtCurrent.set("n/a")
		# 	endAtTarget.set("n/a")

		##ic(settings)

		####################################
		##ic(results)

		getAndDisplayResults()


def dec1(self, floatNum):
	return format(floatNum, '0.1f')


def getAndDisplayResults():		# This is a GUI 'command' so it can't have parameters
	global finishTemp, setupHasChanged, settingsShared, canvas, _widthCnv, _heightCnv
	#ic("Refreshing")

	history = GetHistory(setupHasChanged, settingsShared)

	#ic(history.finishTemp)
	results = history.results
	#ic(results)
	if results.failureReason != '':
		tempNow.set(f"ERROR: {results.failureReason}")
	elif results.dataLength == 0:
		tempNow.set("Internet fail?")
	else:
		setupHasChanged = False

		tempNow.set(results.tempNow)
		timeNow.set(results.timeNow)
		historyTime.set(results.timeNow)		# Upate the time on the setting page
		#ic(results.timeNow)

		last4.set(f"{results.last4}  ({results.last2}, {results.last4}, {results.last8})")
		if float(results.last4) > sausageRate:
			actualLabel.config(fg ='red')
		elif float(results.last4) > nomRate:
			actualLabel.config(fg ='DarkOrange1')
		else:
			actualLabel.config(fg ='green')

		need.set(results.need)
		#ic(results.need)

		#if settingsShared.isFirstDay:
		endAtCurrent.set(results.finishTimeThis)
		endAtTarget.set(results.finishTimeTarget)
		#else:
		lateness.set(results.lateness)

		#
		tempGraph = gt.graphTab()
		tempGraph.initUI(canvas, _widthCnv, _heightCnv, results)



row = 0
realOrHist = StringVar()
ttk.Label(frAnalyse, textvariable=realOrHist, font=("Arial", 18)).grid(column = 0, row = row, columnspan=3, pady=7)
row += 1

endConditions = StringVar()
Label(frAnalyse, textvariable=endConditions).grid(row=row, sticky=W, columnspan=3, padx=9)
row +=1

tempTxt = f"Target rate = {nomRate}, Sausage rate = {round(sausageRate)}" 
Label(frAnalyse, text=tempTxt).grid(row=row, sticky=W, columnspan=3, padx=9)
row +=1

Label(frAnalyse, text="    - - - - - - - - - - - - - - - - - - - - - - - -").grid(row=row, sticky=W, columnspan=3, padx=9)
row +=1

timeNow = StringVar()
Label(frAnalyse, text="Time:", font=("Arial", 10)).grid(row=row, column=0, sticky=E, padx=9)
Label(frAnalyse, textvariable=timeNow, font=("Arial", 10)).grid(row=row, column=1, sticky=W)
row +=1

tempNow = StringVar()
Label(frAnalyse, text="Temp:", font=("Arial", 10)).grid(row=row, column=0, sticky=E, padx=9)
Label(frAnalyse, textvariable=tempNow, font=("Arial", 10)).grid(row=row, column=1, sticky=W)
row +=1

last4 = StringVar()
Label(frAnalyse, text="Deg/hr (actual):", font=("Arial", 10)).grid(row=row, column=0, sticky=E, padx=9)
actualLabel = Label(frAnalyse, textvariable=last4, font=("Arial", 10))
actualLabel.grid(row=row, column=1, sticky=W)
row +=1

need = StringVar()
Label(frAnalyse, text="Deg/hr to meet target:", font=("Arial", 10)).grid(row=row, column=0, sticky=E, padx=9)
Label(frAnalyse, textvariable=need, font=("Arial", 10)).grid(row=row, column=1, sticky=W)
row +=1

lateness = StringVar()
Label(frAnalyse, text="Lateness (minutes):", font=("Arial", 10)).grid(row=row, column=0, sticky=E, padx=9)
Label(frAnalyse, textvariable=lateness, font=("Arial", 10)).grid(row=row, column=1, sticky=W)
row +=1

endAtCurrent = StringVar()
Label(frAnalyse, text="End time @ current rate:", font=("Arial", 10)).grid(row=row, column=0, sticky=E, padx=9)
Label(frAnalyse, textvariable=endAtCurrent, font=("Arial", 10)).grid(row=row, column=1, sticky=W)
row +=1

endAtTarget = StringVar()
Label(frAnalyse, text="End time @ target rate:", font=("Arial", 10)).grid(row=row, column=0, sticky=E, padx=9)
Label(frAnalyse, textvariable=endAtTarget, font=("Arial", 10)).grid(row=row, column=1, sticky=W)
row +=1

Label(frAnalyse, text="    - - - - - - - - - - - - - - - - - - - ").grid(row=row, sticky=W, columnspan=3, padx=9)
row +=1

Button(frAnalyse, text="  Refresh  ", font=("Arial", 9), command=getAndDisplayResults).grid(row=row, column=1, sticky=W)
row +=1



########################################
# "Graph" tab
########################################
row = 0
buttonGraph = Button(frGraph, text="", width=2, height=4, bg="#ddd",
												command=getAndDisplayResults)
buttonGraph.place(x=170, y=35)
row +=1


root.mainloop()		# Run the GUI