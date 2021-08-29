from globals import time_floatToStr
from tkinter import Tk, Canvas, Frame, BOTH, N, W, E, NW
import tkinter.font as font
import tkinter as tk
import math
from enum import Enum
from tkinter import *			# For Button

from dataclasses import dataclass, field
@dataclass
class PointTT:
	__slots__ = "time", "temp"
	time: float
	temp: float


nomRate = 24	# We want a nomRate heating curve to be a 30 deg angle for the user, = 90 + 30 for the program.
sausageFactor = 1.4		# Firemen get penalised for going faster than sausageFactor time the nominal warm-up rate.
sausageRate = nomRate * sausageFactor

noteBookWidth = 300
noteBookHeight = 430

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



def dec1(floatNum):
	return format(floatNum, '0.1f')


class graphicsTest(Frame):
	def __init__(self):
		super().__init__()
		print(f'root.winfo_width()  says canvas width is {root.winfo_width()}  but the actual value is 300')

		self.initUI()

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
		return(90*math.pi/180 + (math.atan(degPerH * math.tan(angleOfNomRate*math.pi/180) / nomRate)))
		#return (90 + 1.6 * degPerH) * math.pi / 180		# !!!!!! Needs fixing !!!!


	def pointTT_toXy(self, timeAtFan, tempAtFan, point):
		time = point.time
		temp = point.temp
		y = fanY + (timeAtFan - time) * pxPerHr
		x = fanX + (tempAtFan - temp) * oneDegreeDistance
		return [x, y]

	
	def pointList_toCoordList(self, pointList):
		coordList = []
		time0 = pointList[-1].time		# Latest time
		temp0 = pointList[-1].temp		# Latest temp

		for i in pointList:
			coordList.append(self.pointTT_toXy(time0, temp0, i))
	
		return coordList


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
		elif lineType ==self.LineType.Ideal:
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


	canvas = None

	# def callRefresh():
	# 	graphicsTest.refresh()
	
	def initUI(self):
		global canvas

		self.master.title("Warm-up")
		canvas = Canvas(self)
		self.pack(fill=BOTH, expand=1)
		self.refresh()



	def refresh(self):		
		global canvas
		canvas.delete('all')

		print(f'cget("width")  says canvas width is {int(canvas.cget("width"))}  but the actual value is 300')
		print(f'root.winfo_width()  says canvas width is {root.winfo_width()}  but the actual value is 300')
		print(f'cget("height") says canvas width is {int(canvas.cget("height"))} but the actual value is 450')
		widthCnv = 300
		heightCnv = 450



		# Draw the coloured segmemts in the fan
		#
		_start = 90
		_extent = self.degPerHr_toRadians_90Added(24) *180/math.pi -_start 
		canvas.create_arc(fanX-radius, fanY-radius, fanX+radius, fanY+radius, 
									start=_start, extent=_extent, outline="#cfc", fill="#cfc", width=0)	# Light green


		_start = _start + _extent
		_extent = self.degPerHr_toRadians_90Added(24 * 1.4) *180/math.pi -_start 
		canvas.create_arc(fanX-radius, fanY-radius, fanX+radius, fanY+radius, 
									start=_start, extent=_extent, outline="#fc8", fill="#fc8", width=0)	# Orange


		_start = _start + _extent
		_extent = self.degPerHr_toRadians_90Added(60) *180/math.pi -_start 
		canvas.create_arc(fanX-radius, fanY-radius, fanX+radius, fanY+radius, 
									start=_start, extent=_extent, outline="#fdd", fill="#fdd", width=0)	# Pink




		# Warm-up path
		ttPoints = []
		ttPoints.append(PointTT(10.8,120))
		ttPoints.append(PointTT(10.818,120.2))
		ttPoints.append(PointTT(10.836,120.4))
		ttPoints.append(PointTT(10.854,120.65))
		ttPoints.append(PointTT(10.872,120.9))
		ttPoints.append(PointTT(10.89,121.1))
		ttPoints.append(PointTT(10.908,121.25))
		ttPoints.append(PointTT(10.926,121.55))
		ttPoints.append(PointTT(10.944,121.8))
		ttPoints.append(PointTT(10.962,122.1))
		ttPoints.append(PointTT(10.98,122.5))
		ttPoints.append(PointTT(10.998,123.05))
		ttPoints.append(PointTT(11.016,123.55))
		ttPoints.append(PointTT(11.034,123.95))
		ttPoints.append(PointTT(11.052,124.4))

		#points = [fanX+150,fanY+190, fanX+135,fanY+152, fanX+115,fanY+114, fanX+90,fanY+76, fanX+50,fanY+38, fanX,fanY]
		points = self.pointList_toCoordList(ttPoints)
		canvas.create_line(points, fill='blue', width=3)
		#[deltaX, deltaY] = self.pointAtAngle(142, 100)
		
		colourValue = 'blue'

		# Draw lines in the quadrant
		#
		# 'Current heading' line
		[quadPoints, colAndWid] = self.degPerHr_line(fanX,fanY, 26, radius, self.LineType.Actual)
		canvas.create_line( quadPoints, fill=colAndWid[0], width=colAndWid[1], dash=(5, 5))
		
		# 'Planned rate' line
		[quadPoints, colAndWid] = self.degPerHr_line(fanX,fanY, 24, radius, self.LineType.ShortGreen)
		canvas.create_line( quadPoints, fill=colAndWid[0], width=colAndWid[1])
		
		# 'Finish on time' line
		[quadPoints, colAndWid] = self.degPerHr_line(fanX,fanY, 34, radius, self.LineType.ShortPurple)
		canvas.create_line( quadPoints, fill=colAndWid[0], width=colAndWid[1])

		# Indicate extent of tab . . .
		arcX = fanX + nomRate * oneDegreeDistance / 4
		arcY = fanY + pxPerHr/4
		arcRadius = 15
		canvas.create_arc(arcX-arcRadius,arcY-arcRadius, arcX+arcRadius, arcY+arcRadius, start=90, extent=90, width=2)
		# . . . and an 'Ideal path' line
		lineX = arcX - nomRate * oneDegreeDistance / (4 * 2)
		lineY = arcY - pxPerHr/(4 * 2)
		canvas.create_line(arcX,arcY, lineX,lineY, fill='green', width=1)

		# Information about latest point
		canvas.create_line(200,fanY, fanX+10,fanY, arrow=tk.LAST)
		latestTime = time_floatToStr(ttPoints[-1].time)
		movingX = widthCnv-10
		incremX = -17
		thisY = fanY+30
		xForTime = movingX
		canvas.create_text(movingX, thisY, anchor=W, angle=90, text=latestTime)
		movingX += incremX
		movingX += incremX
		canvas.create_text(movingX, thisY, anchor=W, angle=90, text="Finish time at this rate: 15:15")
		movingX += incremX
		canvas.create_text(movingX, thisY, anchor=W, angle=90, text="30 deg/h")
		movingX += incremX
		canvas.create_text(movingX, thisY, anchor=W, angle=90, text="130 deg C")
		movingX += incremX

		# "10 minputes earlier" marker
		canvas.create_line(xForTime -25,fanY+pxPerHr/6,  185,fanY+pxPerHr/6)
		if len(ttPoints) > 10:
			timeStr = time_floatToStr(ttPoints[-10].time)
			canvas.create_text(xForTime, thisY-12 +pxPerHr/6, anchor=W, angle=90, text=timeStr)
			tempStr = f'{dec1(ttPoints[-10].temp)} deg C'
			canvas.create_text(xForTime+incremX,thisY-12 +pxPerHr/6, anchor=W, angle=90, text=tempStr)

		# Graph explanation
		movingX = 10
		incremX = 20
		thisY = fanY -10
		lineLength = 35
	
		canvas.create_line(movingX,thisY, movingX,thisY-lineLength, fill='#f8f', width=3.0)
		canvas.create_text(movingX, thisY+8, anchor=E, angle=90, text=
									"Finish at planned time (needs 31? deg/h)")
		movingX += incremX
		canvas.create_line(movingX,thisY, movingX,thisY-lineLength, fill='#4f4', width=3.0)
		canvas.create_text(movingX, thisY+8, anchor=E, angle=90, text=
									"At 24 deg/h the warm-up will end at 14:15?")
		movingX += incremX


		canvas.pack(fill=BOTH, expand=1)

		myFont = font.Font(family='Helvetica', size=12, weight='bold')
		canvas.create_text(50, heightCnv-30, anchor=NW, angle=90, font = myFont, text = 'Last 15 minutes')


root = Tk()
ex = graphicsTest()
width = 300
height = 450
geom = f'{width}x{height}+300+300'
root.geometry(geom)

btn = Button(root, text='Refresh!', width=1,
             height=3, bg="#ddd", bd='3', command=ex.refresh)
  
btn.place(x=165, y=80)
root.mainloop()

