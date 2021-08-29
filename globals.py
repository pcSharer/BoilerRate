from dataclasses import dataclass, field


nomRate = 24	# We want a nomRate heating curve to be a 30 deg angle for the user, = 90 + 30 for the program.
sausageFactor = 1.4		# Firemen get penalised for going faster than sausageFactor time the nominal warm-up rate.
sausageRate = nomRate * sausageFactor


noteBookWidth = 300
noteBookHeight = 430

#########################################################################


@dataclass
class Settings:
	__slots__ = 'isFirstDay', 'finishTemp', 'finishTime', 'plan_riseRate', 'isRealTime', \
								'dateAndTimeStr', 'strDayNow', 'strMission'
	isFirstDay:			bool
	finishTemp:			str
	finishTime:			str
	plan_riseRate:	float
	isRealTime: 		bool
	dateAndTimeStr:	str
	strDayNow:			str
	strMission:			str


# 'Shared' because 'top' and 'side' both get it
settingsShared = Settings(False, '', '', 0, False, '', '', '')


##########################################################################


def dec0(floatNum):
	return format(floatNum, '0.0f')


def dec1(floatNum):
	return format(floatNum, '0.1f')


def dec2(floatNum):
	return format(floatNum, '0.2f')


def round10(number):
	return round(number / 10) * 10


##########################################################################

def leading0(number):
	if number < 10:
		return "0" + str(number)
	else:
		return str(number)

def time_floatToStr(timeFloat):
	inMinutes = round(timeFloat * 60)
	hour = int(inMinutes / 60)
	minute = inMinutes % 60
	return f'{leading0(hour)}:{leading0(minute)}'

###########################################################################

