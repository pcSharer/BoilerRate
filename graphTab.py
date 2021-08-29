from tkinter import Tk, Canvas, Frame, BOTH, N, W, E, NW
import tkinter.font as font
import tkinter as tk
import math
from enum import Enum
from tkinter import *			# For Button
#from temperatureLog import PointTT, Results
from globals import nomRate, sausageRate, time_floatToStr, dec1, settingsShared


fanX = 130
fanY = 150
radius = 140
pxPerHr = 1200
angleOfNomRate = 30
oneDegreeDistance = pxPerHr*math.tan(angleOfNomRate *math.pi/180)/nomRate

# Nominal rate (24 degC/hr  call it nomRate) is 30 degree angle (angleOfNomRate) on graph.
# Program has Y axis in the direction that the user sees as left to right.  
# 30 degC is 1 unit of distance right (decreasing Y for program) and tan(angleOfNomRate)
#    units up (decreaing X for program).
# Drawing has time scale of 1200 (=pxPerHr) Y pixels for 1 hour, 
#   therefore X pixels for 1 hr of heating at nomRate is pxPerHr * tan angleOfNomRate.
# So an hour at nomRate would result in Y decreasing by pxPerHr and X decreasing
#    by pxPerHr * tan(angleOfNomRate).
# So 1 hour is pxPerHr Y pixels (decreasing), and 1 degree increase is:
# 		 pxPerHr*Tan(angleOfNomRate)/nomRate  decreasing X
#      Call that 'oneDegreeDistance'
# So the angle of n deg/h is 90 + arctan(n * oneDegreeDistance / pxPerHr)
#      which expands to:  90 + arctan(n * Tan(angleOfNomRate)/nomRate)
# whch in Python and radians is:
#      90 * math.pi/180 + (math.atan(degPerH * math.tan(angleOfNomRate*math.pi/180) / nomRate)

class graphTab(Frame):
	def __init__(self):
		super().__init__()
		#print(f'root.winfo_width()  says canvas width is {root.winfo_width()}  but the actual value is 300')

		#self.initUI()

	class LineType(Enum):
		Actual = 0
		BentPointer = 1
		ShortGreen = 2
		ShortPurple = 3
		Ideal = 4


	def pointAtAngle(self, angle, length):
		angleRadians = angle * math.pi / 180
		return [length * math.cos(angleRadians), -length * math.sin(angleRadians)]


	def degPerHr_toRadians_90Added(self, degPerH):
		global pxPerHr, nomRate, angleOfNomRate

		degPerH = float(degPerH)
		return(90*math.pi/180 + (math.atan(degPerH * math.tan(angleOfNomRate*math.pi/180) / nomRate)))


	def pointTT_toXy(self, basePoint, point):
		timeAtFan = basePoint.time 
		tempAtFan = basePoint.temp
		time = point.time
		temp = point.temp
		y = fanY + (timeAtFan - time) * pxPerHr
		x = fanX + (tempAtFan - temp) * oneDegreeDistance
		return [x, y]

	
	# def pointList_toCoordList(self, pointList):
	# 	coordList = []
	# 	time0 = pointList[-1].time		# Latest time
	# 	temp0 = pointList[-1].temp		# Latest temp

	# 	for i in pointList:
	# 		coordList.append(self.pointTT_toXy(time0, temp0, i))
	
	# 	return coordList


	def degPerHr_line(self, x0, y0, degPerH, length, lineType):
		radians = self.degPerHr_toRadians_90Added(degPerH)

		protrusion = 1.1
		if lineType == self.LineType.Actual:
			protrusion = 1.0

		x2 = x0 +  length * math.cos(radians) * protrusion
		y2 = y0 + -length * math.sin(radians) * protrusion

		if lineType == self.LineType.Actual:
			fillAndWidths = ['blue', 2]
			resultList = [[x0, y0, x2, y2], fillAndWidths]
		elif lineType == self.LineType.Ideal:
			fillAndWidths = ['#cfc', 1]
			resultList = [[x0, y0, x2, y2], fillAndWidths]
		else:
			if lineType == self.LineType.ShortGreen:
				colour = '#4f4'
			elif lineType == self.LineType.ShortPurple:
				colour = '#f8f'
			else:
				colour = 5/0		# Crash

			fillAndWidths = [colour, 3.0]
			x1 = x0 + length * math.cos(radians) * 0.7
			y1 = y0 + -length * math.sin(radians) * 0.7
			resultList = [[x1, y1, x2, y2], fillAndWidths]
			
		return resultList


#	de-f htToWid(ht):

	def initUI(self, canvas, widthCnv, heightCnv, results):
		#global width, height

		ttPoints = results.averages
		rates = results.rates

		canvas.delete('all')
		lateness = results.lateness

		self.master.title("Warm-up")
		self.pack(fill=BOTH, expand=1)
		# print(f'cget("width")  says canvas width is {int(canvas.cget("width"))}  but the actual value is 300')
		# print(f"canvas['width']  reports {int(canvas['width'])}  but the actual value is 300")
		# print(f'canvas.winfo_width()  says canvas width is {canvas.winfo_width()}  but the actual value is 300')
		# print(f'cget("height") says canvas height is {int(canvas.cget("height"))} but the actual value is 450')



		# Draw the coloured segmemts in the fan
		#
		_start = 90
		_extent = self.degPerHr_toRadians_90Added(nomRate) *180/math.pi - _start
		canvas.create_arc(fanX-radius, fanY-radius, fanX+radius, fanY+radius, 
									start=_start, extent=_extent, outline="#cfc", fill="#cfc", width=0)	# Light green

		_start = _start + _extent
		_extent = self.degPerHr_toRadians_90Added(sausageRate) *180/math.pi - _start
		canvas.create_arc(fanX-radius, fanY-radius, fanX+radius, fanY+radius, 
									start=_start, extent=_extent, outline="#fc8", fill="#fc8", width=0)	# Orange

		_start = _start + _extent
		_extent = self.degPerHr_toRadians_90Added(60) *180/math.pi - _start
		canvas.create_arc(fanX-radius, fanY-radius, fanX+radius, fanY+radius, 
									start=_start, extent=_extent, outline="#fdd", fill="#fdd", width=0)	# Pink
		
		
		# Draw warm-up graph
		#points = self.pointList_toCoordList(ttPoints)
		basePoint = ttPoints[-1]		# The latest point, which will be positioned at the fan
		for pointNum in range(len(ttPoints)):
			if pointNum != 0:
				if rates[pointNum] > sausageRate:
					canvas.create_line(
								self.pointTT_toXy(basePoint, ttPoints[pointNum   ]),
								self.pointTT_toXy(basePoint, ttPoints[pointNum -1]),
								fill='red', width=5)
				else:
					canvas.create_line(
								self.pointTT_toXy(basePoint, ttPoints[pointNum   ]),
								self.pointTT_toXy(basePoint, ttPoints[pointNum -1]),
								fill='blue', width=3)


		# Draw lines in the quadrant
		#
		# 'Current heading' line
		[quadPoints, colAndWid] = self.degPerHr_line(fanX,fanY, results.last4, radius, self.LineType.Actual)
		canvas.create_line( quadPoints, fill=colAndWid[0], width=colAndWid[1], dash=(5, 5))
		
		# 'Planned rate' line
		[quadPoints, colAndWid] = self.degPerHr_line(fanX,fanY, nomRate, radius, self.LineType.ShortGreen)
		canvas.create_line( quadPoints, fill=colAndWid[0], width=colAndWid[1])
		
		# 'Finish on time' line
		[quadPoints, colAndWid] = self.degPerHr_line(fanX,fanY, results.need, radius, self.LineType.ShortPurple)
		canvas.create_line( quadPoints, fill=colAndWid[0], width=colAndWid[1])

		# Indicate extent of tab . . .
		cornerX = fanX + nomRate * oneDegreeDistance / 4
		cornerY = fanY + pxPerHr/4
		# arcRadius = 15
		# canvas.create_arc(cornerX-arcRadius,cornerY-arcRadius, cornerX+arcRadius, cornerY+arcRadius, start=90, extent=90, width=1)
		canvas.create_line(cornerX,cornerY, cornerX,cornerY-70, fill='black', width=1)
		canvas.create_line(cornerX,cornerY, cornerX-70,cornerY, fill='black', width=1)
		# . . . and an 'Ideal path' line
		lineX = cornerX - nomRate * oneDegreeDistance / (4 * 2)
		lineY = cornerY - pxPerHr/(4 * 2)
		canvas.create_line(cornerX,cornerY, lineX,lineY, fill='green', width=1)


		# Information about latest point
		canvas.create_line(200,fanY, fanX+10,fanY, arrow=tk.LAST)
		latestTime = time_floatToStr(ttPoints[-1].time)
		movingX = widthCnv-20
		decremX = 17
		thisY = fanY+30
		xForTime = movingX
		canvas.create_text(movingX, thisY, anchor=W, angle=90, text=latestTime)
		movingX -= decremX
		movingX -= decremX
		canvas.create_text(movingX, thisY, anchor=W, angle=90, text=f"Finish time at this rate: {results.finishTimeThis}")
		movingX -= decremX
		canvas.create_text(movingX, thisY, anchor=W, angle=90, text=f"{results.last4}  degC/hr")
		movingX -= decremX
		canvas.create_text(movingX, thisY, anchor=W, angle=90, text=results.tempNow	)
		movingX -= (decremX +10)
		canvas.create_text(movingX, fanY-55, anchor=W, angle=90, text="Refresh")

		# "10 minputes earlier" marker
		canvas.create_line(xForTime -28,fanY+pxPerHr/6,  185,fanY+pxPerHr/6)
		if len(ttPoints) > 10:
			timeStr = time_floatToStr(ttPoints[-10].time)
			canvas.create_text(xForTime, thisY-12 +pxPerHr/6, anchor=W, angle=90, text=timeStr)
			tempStr = f'{dec1(ttPoints[-10].temp)} deg C'
			canvas.create_text(xForTime-decremX,thisY-12 +pxPerHr/6, anchor=W, angle=90, text=tempStr)

		# Graph explanation
		movingX = 10
		incremX = 20
		thisY = fanY -10
		lineLength = 35
	
		canvas.create_line(movingX,thisY, movingX,thisY-lineLength, fill='#f8f', width=3.0)
		canvas.create_text(movingX, thisY+8, anchor=E, angle=90, text=
									f"Finish at planned time (needs {results.need} deg/h)")
		movingX += incremX
		canvas.create_line(movingX,thisY, movingX,thisY-lineLength, fill='#4f4', width=3.0)
		canvas.create_text(movingX, thisY+8, anchor=E, angle=90, text=
									f"At {nomRate} deg/h the warm-up will end at {results.finishTimeTarget}")
		movingX += incremX
		movingX += incremX / 2

		myFont = font.Font(family='Helvetica', size=10)#, weight='bold')
		lowY = heightCnv-80
		canvas.create_text(movingX, lowY, anchor=NW, angle=90, font = myFont, text=settingsShared.strDayNow)
		movingX += incremX
		canvas.create_text(movingX, lowY, anchor=NW, angle=90, font = myFont, text=settingsShared.strMission)
		movingX += incremX
		movingX += incremX / 2

		# button2=tk.Button(text="button2")
		# button2.place(x=160, y=45)

		canvas.pack(fill=BOTH, expand=1)

		canvas.create_text(movingX, lowY, anchor=NW, angle=90, font = myFont, text = 'Last 15 minutes')


# root = Tk()
# ex = graphTab()
# width = 300
# height = 450
# geom = f'{width}x{height}+300+300'
# root.geometry(geom)
# #Button(text="  Refresh  ", font=("Arial", 9), command=graphTab.degPerHr_line)
# btn = Button(root, text='Kill', width=1,
#              height=3, bg="#ddd", bd='3', command=root.destroy)
  
# btn.place(x=65, y=250)
# root.mainloop()

