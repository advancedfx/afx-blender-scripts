# Copyright (c) advancedfx.org
#
# Last changes:
# 2016-08-05 dominik.matrixstorm.com
#
# First changes:
# 2016-07-19 dominik.matrixstorm.com

import math

import mathutils

class QAngle:
	def __init__(self,x,y,z):
		self.x = x
		self.y = y
		self.z = z
		
	def to_quaternion(self):
		pitchH = 0.5 * math.radians(self.x)
		qPitchY = mathutils.Quaternion((math.cos(pitchH), -math.sin(pitchH), 0.0, 0.0))
		
		yawH = 0.5 * math.radians(self.y)
		qYawZ = mathutils.Quaternion((math.cos(yawH), 0.0, 0.0, math.sin(yawH)))
		 
		rollH = 0.5 * math.radians(self.z)
		qRollX = mathutils.Quaternion((math.cos(rollH), 0.0, math.sin(rollH), 0.0))
		 
		return qYawZ * qPitchY * qRollX
