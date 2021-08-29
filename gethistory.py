import requests # requests library to make REST calls
import time
from datetime import datetime
#import dateutil
from dateutil import tz
import json
import sys

from temperatureLog import TemperatureLog, LogItem, Results, Averages
from globals import nomRate, sausageRate, sausageFactor, time_floatToStr, dec0, dec1, round10


try:
	from icecream import ic
except ImportError:  # Graceful fallback if IceCream isn't installed.
	ic = lambda *a: None if not a else (a[0] if len(a) == 1 else a)  # noqa


historicalEndTime_moving = 0		# (Initialised with junk)
latestProcessedTime = 0

class GetHistory(object):
	def __init__ (self, _setupHasChanged, _historySetup):   # Instance veariables . . .
		self.setupHasChanged			= _setupHasChanged
		self.historySetup	= _historySetup

	##############################################################################
	##############################################################################
		self.results = self.readEmon(self.setupHasChanged)
		self.latestTemp = 0		# create an instance variable


	debugging = False			# Controls the amount of printout
	millisecsIn1Minute = 60 * 1000

	#ic.enable()

	def time_strToFloat(self, timeStr):
		(hour, minute) = timeStr.split(':')
		return int(hour) + int(minute)/60


	def predictTimeAndRate(self, latestTemp, timeNow_hr, plan_finalTemp,
						endTimeToday_float, doingDay2):
		# Calculate time remaining at the planned rate
		tempNow = latestTemp
		tempTarget = plan_finalTemp
		timeIdeal = 0
		_rateIsMeaningless = False
		#ic("In predict...")

		if tempTarget > tempNow:
			tempIncrease = tempTarget - tempNow
			timeIdeal = tempIncrease / self.historySetup.plan_riseRate

		#ic(f"{timeIdeal} {endTimeToday_float} {timeNow_hr}")
		latenessMin = (timeIdeal - (endTimeToday_float - timeNow_hr)) * 60
		easyFinish_hr = timeNow_hr + timeIdeal
		#print(f"asyFinish_hr = {timeNow_hr} + ({tempTarget} - {tempNow}) / {plan_riseRate})")

		if latestTemp >= plan_finalTemp:  # Hot enough
			rateRequired = 0
		elif timeNow_hr >= endTimeToday_float - 0.15:  # Too late to catch up
			rateRequired = 999999  # ... or even more
			_rateIsMeaningless = True
		else:
			rateRequired = (plan_finalTemp - latestTemp) / (endTimeToday_float - timeNow_hr)
			#ic(plan_finalTemp, latestTemp, endTimeToday_float, timeNow_hr)

		return [latenessMin, rateRequired, easyFinish_hr, _rateIsMeaningless]



	def hrToHrMin_rounded(self, hourDecimal):		# Rounded to 15-minute units
		if hourDecimal >= 24:
			return "Tomorrow?"
		
		quarterHrs = round(hourDecimal * 4)
		leadingZero = "0" if quarterHrs % 4 == 0  else ""
		return f"{int(quarterHrs / 4)}:{leadingZero}{(quarterHrs % 4) * 15}"

	

	#################################################################################

	
	def readEmon(self, setupHasChanged):
		global historicalEndTime_moving, latestProcessedTime

		#ic("In readEmon")
		
		# Set these as required
		cruiseTemp = 165
		firstDayEndTime = "14:30"
		
		plan_finalTemp = -999		#  Keep the interpreter happy

		#ic(self.historySetup.isRealTime, self.historySetup.isFirstDay)
		doingDay2 = not self.historySetup.isFirstDay
	
		if doingDay2:
			plan_finalTemp = cruiseTemp
			endTimeToday_str = self.historySetup.finishTime
			#ic("in readEmon() self.finishTime is " + self.historySetup.finishTime)
		else:
			plan_finalTemp = self.historySetup.finishTemp
			endTimeToday_str = firstDayEndTime

		# EpochConverter - https://www.epochconverter.com/timezones?q=1624062600&tz=Australia%2FSydney
		#     Programming tools - https://www.epochconverter.com/#tools

		dateAndTimeStr = self.historySetup.dateAndTimeStr
		if dateAndTimeStr == "Today Now":
			dateAndTimeStr = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time()))

		(dateStr, unwantedTime) = dateAndTimeStr.split(' ')
		#ic(endTimeToday_str)
		#ic("Timepoint for internet read: {dateStr}")
		#ic(self.finishTime)
		#ic(dateAndTimeStr)

		if setupHasChanged:
			#ic('setupHasChanged is true')
			historicalEndTime_moving = datetime.strptime(dateAndTimeStr, '%Y-%m-%d %H:%M').timestamp() * 1000 # !!!! Needs timezones?? .replace(tzinfo=from_zone).astimezone(to_zone).timestamp()
			latestProcessedTime = 0		# Prevent false "Nothing new ..." update failure

		timeLeap = self.millisecsIn1Minute * 10		# Take 10-minute steps through history instead of the normal 1-minute steps.



		#
		##########################################################################
		# Get blocks of data from the internet, merge them, then report results.
		##########################################################################
		#

		if self.historySetup.isRealTime:
			timeOz_timeStamp = time.time() * 1000		# 2021-08019 13:06 yields approx 1629,342,360 * 1000 (commas added by me)
		else:
			timeOz_timeStamp = historicalEndTime_moving

		feedId_boilerTop  = 424220
		feedId_boilerSide = 369278

		minutesOfData = 18
		# Specify what we want from internet
		dataRequest_top  = LogItem(dateStr, timeOz_timeStamp, feedId_boilerTop,  minutesOfData)
		dataRequest_side = LogItem(dateStr, timeOz_timeStamp, feedId_boilerSide, minutesOfData)

		if self.debugging:
			#ic (dataRequest)
			#ic ("FeedId is " + str(dataRequest.feedId))
			#ic ("End time is " + str(dataRequest.timeStampEnd))
			pass
		
		historicalEndTime_moving += timeLeap

		# Read top and side data from the internet.  Return a .logItem cotaining the AVERAGE teperature of the 2 data requests.
		#   Of interest is .points[], .fatalError, .ErrorStr
		averageObj = Averages(dataRequest_top, dataRequest_side, latestProcessedTime)
		fullData = averageObj.tempLog
		averages = [fullData[i][0] for i in range(len(fullData))]
		rates    = [fullData[i][1] for i in range(len(fullData))]
		logSideInfo = averageObj.log_side.logItem

		results = Results()
		results.averages = averages
		results.rates = rates

		errorSeen = False
		if logSideInfo.fatalError or logSideInfo.length == 0:
			errorSeen = True
			results.failureReason += logSideInfo.errorStr + '\n'

		if not errorSeen:
			results.latestTime = averages[-1].time
			results.timeNow = time_floatToStr(results.latestTime)
			results.latestTemp = averages[-1].temp

			if abs(latestProcessedTime - results.latestTime) < 0.003:        # (= 10 seconds). I have seen 9 seconds difference
				#ic(latestProcessedTime, results.latestTime)
				timeStr = time.strftime("%H:%M:%S", time.localtime(timeOz_timeStamp / 1000))
				results.failureReason += f'Nothing new at {timeStr}\n'
				print(f'Nothing new at {timeStr}')
			else:
				if self.debugging:
					# Print the results
					print(averageObj)
					print("end time = " + str(logSideInfo.timeStampEnd))
					print("feed id = " + str(logSideInfo.feedId))
					print("length = " +  str(logSideInfo.length))
					print("Fatal = " +  str(logSideInfo.fatalError))
					print("Error = " + logSideInfo.errorStr)
					# print("Values = ") 
					# print(averages)

				if logSideInfo.fatalError:
					results.failureReason += logSideInfo.errorStr + '\n'
					print("Fatal error: " + logSideInfo.errorStr)
				else:
					fltHour = results.latestTime

					latestTempStr = "{:.1f}".format(results.latestTemp)
					topTempStr    = "{:.0f}".format(float(fullData[-1][2]))
					sideTempStr   = "{:.0f}".format(float(fullData[-1][3]))
					tempNowStr = f'{latestTempStr}  ({topTempStr} - {sideTempStr})'
					print(f'Temp at  {results.timeNow} is {tempNowStr}')
					results.tempNow = tempNowStr


					# --------- We want to print something like this:  -----------------
					# Length is 18
					# Temp at   12:00 is 55.8
					# Last  1 min: 33
					# Last  2 min: 32
					# Last  4 min: 31 ---
					# Last  8 min: 30
					# Last 16 min: 27
					# Want 145 in 2.5 hr (at 14:30)
					# Need 36 deg/hr
					# Predicted finish time at  this  rate: 14:45
					# Predicted finish time at target rate: 15:45

					currentRate = 0
					span = 1
					pointCnt = len(averages)
					results.dataLength = pointCnt

					results.last124816 = []
					# Show the rates of rise averaged over 1 min, 2 min, 4 min, 8 min, 16 min
					# (Note: Latest is at end of array. Earlier one preceed it)
					while span < pointCnt:
						earlierTemp = averages[pointCnt -1 - span].temp
						hourlyIncrease = (results.latestTemp - earlierTemp) * 60 / span

						spanSpace = ""
						if span < 10: spanSpace = " "

						rateString = str(round(hourlyIncrease))

						marker = ""
						if span == 4:
							currentRate = hourlyIncrease
							
							#ic(self.sausageFactor)
							#ic(self.plan_riseRate)
							if hourlyIncrease > self.historySetup.plan_riseRate * sausageFactor:
								marker = " === Sausages!"
							else:
								marker = " ---"

						results.last124816.append(rateString)
						print(f"Last {spanSpace}{span} min: {rateString}{marker}")

						span *= 2

					latestProcessedTime = results.latestTime

					results.last2 = results.last124816[1]
					results.last4 = results.last124816[2]
					results.last8 = results.last124816[3]
					
					endTimeToday_float = self.time_strToFloat(endTimeToday_str)
					results.atTime = endTimeToday_str		# Correct??

					latenessMin, rateRequired, easyFinish_hr, rateIsMeaningless  = \
							self.predictTimeAndRate(results.latestTemp, fltHour, plan_finalTemp, endTimeToday_float, doingDay2)

					hrsTill_and_time__string = f"{dec1(endTimeToday_float - fltHour)} hr (at {self.hrToHrMin_rounded(endTimeToday_float)})"
					results.want = dec0(plan_finalTemp)
					print(f"Want {dec0(plan_finalTemp)} in {hrsTill_and_time__string}")
					
					if not rateIsMeaningless:
						results.need = dec0(rateRequired)
						print(f"Need {dec0(rateRequired)} deg/hr") 

					# Original plan was not inform the user of lateness on the 1st day, and not
					#  to inform him of predicted finish time on the second day.
					# The "if" and "else" associated with tht are commented out below - see "xxx"
					#
					tempTxt = ""
					# xxx if not doingDay2:
					if currentRate == 0:
						tempTxt = "Tomorrow?"
					elif plan_finalTemp - results.latestTemp < 0:
						tempTxt = "Now"
					else:
						tempTxt = self.hrToHrMin_rounded(fltHour +  (plan_finalTemp - results.latestTemp) / currentRate)

					results.finishTimeThis = tempTxt
					print(f"Predicted finish time at  this rate: {tempTxt}")

					tempTxt = self.hrToHrMin_rounded(easyFinish_hr)
					results.finishTimeTarget = tempTxt
					print(f"Predicted finish time at target rate: {tempTxt}")
					# xxx else:
					ic("Setting lateness (day 1) instead of predictions")
					roundedLateness = round10(latenessMin)
					results.lateness = roundedLateness

					if roundedLateness > 0:
						print(f"!! Running {roundedLateness} minutes late !")
					else:
						print(f"Running {abs(roundedLateness)} minutes early")
					# xxx End of commented if/else above

		return results

			##ic(r.status_code)
	# End of  readEmon()


