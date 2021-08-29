from dataclasses import dataclass, field

import requests # requests library to make REST calls
from datetime import datetime
#import dateutil
from dateutil import tz
import json
import time
import sys

from datetime import datetime
from datetime import datetime

# # Date and time in my timezone
# now = datetime.now()
# print("now =", now)
# dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
# print("date and time =", dt_string)	


try:
	from icecream import ic
except ImportError:  # Graceful fallback if IceCream isn't installed.
	ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa
ic.enable()


millisecsInSec = 1000
millisecsIn1Minute = 60 * millisecsInSec
debugging = False

@dataclass
class PointTT:
	__slots__ = "time", "temp"
	time: float
	temp: float


@dataclass
class LogItem:
	# Line below causes an error because __slot__ cannot be used with default values (a Python bug)
	#__slots__ = "timeStampEnd", "feedId", "length", "fatalError", "errorStr", "points"    # Optional. Prevent accidental creation of additional class variables
	dateStr: str
	timeStampEnd: str
	feedId: int
	length: int
	fatalError: bool = False
	errorStr: str = ""
	points: list = field(default_factory=list)			# Default to empty 
	latestPoint: PointTT = PointTT(0, 0)


@dataclass
class Results:
	# Seems that __slots__ can't be used if default values follow.
	# I want the default values because I want to be able to make an 'empty' Results object at the start of readEmon()
	#__slots__ = 'dataLength', 'timeNow', 'tempNow', 'last1', 'last2', 'last4', 'last8', 'last16', 'want', 'atTime', 'need', 'lateness', 'finishTimeThis', 'finishTimeTarget'
	failureReason:	str = ""
	dataLength:		int = 0
	timeNow:		str = ""
	tempNow:		float = 0
	#last124816:	list[str]
	last1:			int = 0
	last2:			int = 0
	last4:			int = 0
	last8:			int = 0
	last16:			int = 0
	want:				int = 0
	atTime:			str = ""
	need:				int = 0
	lateness:		int = 0
	averages:		list = field(default_factory=list)			# Default to empty 
	rates:			list = field(default_factory=list)			# Default to empty 
	finishTimeThis:		str = "n/a"
	finishTimeTarget:	str = "n/a"


class Averages(object):
	def __init__ (self, _request_top, _request_side, _latestProcessedTime):
		self.request_top  = _request_top
		self.request_side = _request_side
		self.latestProcessedTime = _latestProcessedTime

		[self.tempLog,  self.log_side] = self.getAverages(self.request_top, self.request_side)


	def getAverages(self, request_top, request_side):
		print('Reading top . . .')
		log_top = TemperatureLog(request_top)

		averages = []
		errorSeen = False
		if log_top.logItem.fatalError or log_top.logItem.length == 0:
			errorSeen = True

		if not errorSeen:
			if abs(self.latestProcessedTime - log_top.logItem.latestPoint.time) < 0.003:        # (= 10 seconds). I have seen 9 seconds difference
				print(f'Nothing new in top log')
				errorSeen = True

		if not errorSeen:
			print('Reading side . . .')
			log_side = TemperatureLog(request_side)

			errorSeen = False
			if log_side.logItem.fatalError or log_side.logItem.length == 0:
				errorSeen = True

			if not errorSeen:
				if abs(self.latestProcessedTime - log_side.logItem.latestPoint.time) < 0.003:        # (= 10 seconds). I have seen 9 seconds difference
					print(f'Nothing new in side log')
					errorSeen = True

		if not errorSeen:
			# Do averaging (ToDo), then return the TemperatureLog for the averages. . . 
			##################################################################
	
			# Get the average from the above two sets of points
			#
			topTemps  =  log_top.logItem.points
			sideTemps = log_side.logItem.points

			lastSideIndex = 0
			print("")
			bias = 1/(60 * 10)      # (= 6 seconds) Bias the decision making to favour the middle option

			sideStr = ""
			diffStr = ""
			avValue = 0
			avStr = ""
			whichChosen = ""
			rate_placeHolder = 0    # Degrees per hour
			prevPrevPrevPrevAverage = prevPrevPrevAverage = prevPrevAverage = prevAverage = (topTemps[0].temp + sideTemps[0].temp) / 2   # Initial value

			for i in range(len(topTemps)):
				currentSmoothTime = topTemps[i].time
				topStr = f'{"{:.1f}".format(topTemps[i].temp)}'
				timeStr = f'{currentSmoothTime}'
				if lastSideIndex < len(sideTemps) - 2:   # If this is not quite the end of the data.
					# Find the side value whose time is closest to the time of the top index being used.
					# Compare the one before the expected one, the expected one, and the one after the expected one.
					# For info, print "-1", "0", or "1" to indicate which of the above 3 options wa used.
					if i == 0:      # Hack to avoid negative-index complications
						whichChosen = 0
						sideStr = f'\t{"{:.1f}".format(sideTemps[i].temp)}'

						avValue = (topTemps[i].temp + sideTemps[i].temp) / 2

						lastSideIndex = 0
						best = lastSideIndex
					else:
						timeDiffFromLastIndexPlus0 = abs(currentSmoothTime - sideTemps[lastSideIndex +0].time) + bias
						timeDiffFromLastIndexPlus1 = abs(currentSmoothTime - sideTemps[lastSideIndex +1].time)
						timeDiffFromLastIndexPlus2 = abs(currentSmoothTime - sideTemps[lastSideIndex +2].time) + bias

						if timeDiffFromLastIndexPlus0 < timeDiffFromLastIndexPlus1:
							best = lastSideIndex +0
							whichChosen = -1
							if timeDiffFromLastIndexPlus2 < timeDiffFromLastIndexPlus0:
								best = lastSideIndex +2
								whichChosen = 1
						else:
							best = lastSideIndex +1
							whichChosen = 0
							if timeDiffFromLastIndexPlus2 < timeDiffFromLastIndexPlus1:
								best = lastSideIndex +2
								whichChosen = 1

						avValue = (topTemps[i].temp + sideTemps[best].temp) / 2
						sideStr = f'\t{"{:.1f}".format(sideTemps[best].temp)}'

					avStr = f'\t{"{:.1f}".format(avValue)}'
					sideValue = sideTemps[best].temp
					topMinusSide = topTemps[i].temp - sideValue
					diffStr = f'\t{"{:.1f}".format(topMinusSide)}'

					prevPrevPrevPrevAverage = prevPrevPrevAverage
					prevPrevPrevAverage     = prevPrevAverage
					prevPrevAverage         = prevAverage
					prevAverage             = avValue


					lastSideIndex = best

					averages.append([PointTT(float(timeStr), float(avStr)), rate_placeHolder, topStr, sideStr, diffStr, whichChosen])
				
			
			# Calculate the rise-rate
			for i in range(len(averages)):
				# To dampen sample noise we measure the temp change over diffMinutes minutes
				diffMinutes = 2
				j = max(0, i-diffMinutes)		# Don't go negative
				averages[i][1] = (averages[i][0].temp - averages[j][0].temp) * 60 / diffMinutes


		return [averages, log_side]

##################################################################

		return log_top	# This should be the averages



class TemperatureLog:
	__slots__ = 'logItem'    # Optional. Prevent accidental creation of additional class variables

	def __init__ (self, logItem):   # Instance veariables . . .
		self.logItem = self.fillLogItem(logItem)
	

	def getDateTime(self, _dateStr, timeStr):
		dateParts = _dateStr.split("-")
		timeParts = timeStr.split(":")
		partsInt = list(map(int, dateParts + timeParts))      # Make list of ints from a map of strings
		return datetime(*partsInt)    # '*' opens the list



	# Updates logItemParam and returns it
	def fillLogItem(self, logItemParam):
		timeStampOz = logItemParam.timeStampEnd
		ic(logItemParam)		# dateStr, timeOz_timeStamp, feedId_boilerTop, minutesOfData
		ic()

		start = timeStampOz - logItemParam.length * millisecsIn1Minute    # Collect several minutes of data
		end   = timeStampOz
		apikey = "30301d38578cfcd4fe64ed9cc10024b6"
		url = f"http://emoncms.org/feed/data.json?id={logItemParam.feedId}&start={start}&end={end}" + \
					f"&interval=5&skipmissing=1&limitinterval=1&apikey={apikey}"
		print("Url = " + url + "\n")

		failure = False
		try:
			r = requests.get(url)
		except:
			logItemParam.errorStr += "Internet access failed\n"
			failure = True

		if not failure:
			if debugging: print("Data = " + r.content.decode(encoding='UTF-8'))   # r.contents is apparently a byte string
			try:
				# json.loads takes a string, bytes, or byte array instance which contains the JSON document as a parameter (s). It returns a Python object
				data = json.loads(r.content)    # This also works:  data = json.loads(r.content.decode(encoding='UTF-8'))
				# The format of "data" above seems too be a data array if everything went well, otherwise a dictionary like, for example: 
				# 			Data = {"success":false,"message":"feed 42422 does not exist","feeds":[42422]}
			except:
				logItemParam.errorStr += f"Couldn't parse this internet data  {r.content}\n"
				failure = True

		if not failure:
			print("")
			print("Length is " + str(len(data)))
			if len(data) < 6:
				failure = True
				if len(data) > 2:		# Probably a dictionary with failure info
					logItemParam.errorStr += "Bad data from website: " + data["message"] + "\n"


		if not failure:		# data is probably an array, not a dictionary
			#print(f"Received {data}")
			#print(f'Temp at {timeOz.strftime("%H:%M:%S")} is ')

			# There can be gaps in the list of points. Fill with interpolated values.
			#
			#ic(logItemParam.timeStampEnd)
			#ic()
			startOfFirstDay = self.getDateTime(logItemParam.dateStr, "0:0")
			startOfFirstDay_millisec = startOfFirstDay.timestamp() * millisecsInSec



			topTemps = []
			sideTemps = []
			activeStore = topTemps


			lastTimeValueIsKnown = False
			timeNoDate_last = 0		# Junk
			value_last = 0.0		# Junk
			minutesPerSample = 1
			valueChangeCnt = 0


			for index in range(len(data)):
				timeNoDate = (data[index][0] - startOfFirstDay_millisec) / (1000 * 60 * 60)    # Divisor is no. of millisecs in an hour
				timeNoDate = round(timeNoDate, 3)

				if lastTimeValueIsKnown and timeNoDate == timeNoDate_last:
					print (f"Duplicate time {timeNoDate} deleted")        # For some reason this happens at about the second last chunk
				elif lastTimeValueIsKnown and timeNoDate < timeNoDate_last:
					print (f"Time went backwards to {timeNoDate} - Deleted")        # Tends to happen at the start of a chunk
				else:
					if lastTimeValueIsKnown and timeNoDate - timeNoDate_last > (2 * minutesPerSample / 60) * 0.94:            # If slightly less than 2 sample times, or greater
						intervalsNeeded = round((timeNoDate - timeNoDate_last) / (minutesPerSample / 60))   # Hours of gap / hours of 1 sample
						timeIncrement = (timeNoDate - timeNoDate_last) / intervalsNeeded
						valueIncrement = (data[index][1] - value_last) / intervalsNeeded
						print(f" . . . . . . {(intervalsNeeded - 1)} missing samples added below")
						for i in range(intervalsNeeded):
							if i > 0:
								calculatedRoundedTime  = round(timeNoDate_last + timeIncrement * i, 3)
								calculatedRoundedValue = round(value_last + valueIncrement * i, 2)
								print(f"{calculatedRoundedTime}, {calculatedRoundedValue}")
								activeStore.append(PointTT(calculatedRoundedTime,calculatedRoundedValue))		# Note: Stored value is not negative
								# Don't append to findUniqueValues because the value is 'man-made'
						
					timeAndValue = PointTT(timeNoDate, round(data[index][1], 2))
					print(timeAndValue)
					activeStore.append(timeAndValue)
					if value_last != data[index][1]:
						valueChangeCnt += 1

					timeNoDate_last = timeNoDate
					lastTimeValueIsKnown = True
					value_last = data[index][1]



			# The temperature sensor has occasionally got stuck at a certain temperature.  Check for that.
			ic(valueChangeCnt)
			if valueChangeCnt < 3:		# Might need to increase this limit if the number of points is very large.
				failure = True
				logItemParam.errorStr += "Temp sensor stuck\n"



			# Values have noise. Smooth them and store them in logItemParam.points
			#
			logItemParam.points = list()
			i = 0
			for value in activeStore:
				if i == 0:
					logItemParam.points.append(value)
				elif i == 1 and i < len(activeStore) - 1:
					logItemParam.points.append(PointTT(value.time, (activeStore[i-1].temp + value.temp + activeStore[i+1].temp) / 3))
				elif i > 1 and i < len(activeStore) - 2:
					logItemParam.points.append(PointTT(value.time, (activeStore[i-2].temp + activeStore[i-1].temp + value.temp + activeStore[i+1].temp + activeStore[i+2].temp) / 5))
				elif i == (len(activeStore) - 2):
					logItemParam.points.append(PointTT(value.time, (activeStore[i-1].temp + value.temp + activeStore[i+1].temp) / 3))
				else:      # Latest pont, read last
					logItemParam.points.append(value)
					logItemParam.latestPoint = value

				i += 1

				hour = datetime.now().hour + datetime.now().minute / 60


		logItemParam.fatalError = failure
		ic(logItemParam.fatalError)
		return logItemParam





