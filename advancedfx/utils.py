import mathutils
import math
import bpy

NEWER_THAN_290 = bpy.app.version >= (2, 90, 0)

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
		 
		return qYawZ @ qPitchY @ qRollX

def GetInterKeyRange(lastTime, time):
	loF = lastTime
	lo = int(math.ceil(loF))
	if(lo == loF):
		lo = lo + 1
	
	hiF = time
	hi = int(math.floor(hiF))
	if( hi == hiF ):
		hi = hi -1
	
	return range(lo,hi+1)

def AddKey_Value(interKey, keyframe_points, time, value):
	if(interKey and 0 < len(keyframe_points)):
		lastItem = keyframe_points[-1]
		lastTime = lastItem.co[0]
		lastValue = lastItem.co[1]
		
		for interTime in GetInterKeyRange(lastTime, time):
			dT = (interTime -lastTime) / (time-lastTime)
			interValue = lastValue * (1.0 - dT) + value * dT
			keyframe_points.add(1)
			item = keyframe_points[-1]
			item.co = [interTime, interValue]
			item.interpolation = 'CONSTANT'
	
	keyframe_points.add(1)
	item = keyframe_points[-1]
	item.co = [time, value]
	item.interpolation = 'CONSTANT'

def AddKeysList_Value(interpolation, keyframe_points, data):
	keyframe_points.add(len(data) // 2)
	keyframe_points.foreach_set("co", data)
	if keyframe_points[0].interpolation != interpolation:
		if NEWER_THAN_290:
			interpolation_value = bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items[interpolation].value
			keyframe_points.foreach_set("interpolation", [interpolation_value] * len(keyframe_points))
		else:
			for item in keyframe_points:
				item.interpolation = interpolation

def AppendInterKeys_Value(time, value, data):
	if 0 == len(data):
		return
	lastValue = data[-1]
	lastTime = data[-2]
	for interTime in GetInterKeyRange(lastTime, time):
		dT = (interTime-lastTime) / (time-lastTime)
		interValue = lastValue * (1.0 - dT) + value * dT
		data.extend((interTime, interValue))

def AddKey_Visible(interKey, keyframe_points_hide_render, time, visible):
	if(interKey and 0 < len(keyframe_points_hide_render)):
		lastItem = keyframe_points_hide_render[-1]
		lastTime = lastItem.co[0]
		lastVisible = 0 == lastItem.co[1]
		
		for interTime in GetInterKeyRange(lastTime, time):
			keyframe_points_hide_render.add(1)
			item = keyframe_points_hide_render[-1]
			item.co = [interTime, 0.0 if( lastVisible and visible ) else 1.0]
			item.interpolation = 'CONSTANT'
	
	keyframe_points_hide_render.add(1)
	item = keyframe_points_hide_render[-1]
	item.co = [time, 0.0 if( visible ) else 1.0]
	item.interpolation = 'CONSTANT'

def AddKeysList_Visible(keyframe_points, data):
	keyframe_points.add(len(data) // 2)
	keyframe_points.foreach_set("co", data)
	if NEWER_THAN_290:
		interpolation_value = bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items['CONSTANT'].value
		keyframe_points.foreach_set("interpolation", [interpolation_value] * len(keyframe_points))
	else:
		for item in keyframe_points:
			item.interpolation = 'CONSTANT'

def AppendInterKeys_Visible(time, invisible, data):
	if 0 == len(data):
		return
	lastInvisible = data[-1]
	lastTime = data[-2]
	for interTime in GetInterKeyRange(lastTime, time):
		data.extend((interTime, 0 if lastInvisible == 0 and invisible == 0 else 1))

def AddKey_Location(interKey, keyframe_points_location_x, keyframe_points_location_y, keyframe_points_location_z, time, location):
	if(interKey and 0 < len(keyframe_points_location_x) and 0 < len(keyframe_points_location_y) and 0 < len(keyframe_points_location_z)):
		lastItemX = keyframe_points_location_x[-1]
		lastItemY = keyframe_points_location_y[-1]
		lastItemZ = keyframe_points_location_z[-1]
		lastTime = lastItemX.co[0]
		lastLocation = mathutils.Vector((lastItemX.co[1], lastItemY.co[1], lastItemZ.co[1]))
		
		for interTime in GetInterKeyRange(lastTime, time):
			interLocation = lastLocation.lerp(location, (interTime -lastTime) / (time-lastTime))
			keyframe_points_location_x.add(1)
			keyframe_points_location_y.add(1)
			keyframe_points_location_z.add(1)
			itemX = keyframe_points_location_x[-1]
			itemY = keyframe_points_location_y[-1]
			itemZ = keyframe_points_location_z[-1]
			itemX.co = [interTime, interLocation.x]
			itemY.co = [interTime, interLocation.y]
			itemZ.co = [interTime, interLocation.z]
			itemX.interpolation = 'CONSTANT'
			itemY.interpolation = 'CONSTANT'
			itemZ.interpolation = 'CONSTANT'
	
	keyframe_points_location_x.add(1)
	keyframe_points_location_y.add(1)
	keyframe_points_location_z.add(1)
	itemX = keyframe_points_location_x[-1]
	itemY = keyframe_points_location_y[-1]
	itemZ = keyframe_points_location_z[-1]
	itemX.co = [time, location.x]
	itemY.co = [time, location.y]
	itemZ.co = [time, location.z]
	itemX.interpolation = 'CONSTANT'
	itemY.interpolation = 'CONSTANT'
	itemZ.interpolation = 'CONSTANT'
	
def AddKeysList_Location(interpolation, keyframe_points_x, keyframe_points_y, keyframe_points_z, data_x, data_y, data_z):
	keyframe_points_x.add(len(data_x) // 2)
	keyframe_points_x.foreach_set("co", data_x)
	keyframe_points_y.add(len(data_y) // 2)
	keyframe_points_y.foreach_set("co", data_y)
	keyframe_points_z.add(len(data_z) // 2)
	keyframe_points_z.foreach_set("co", data_z)
	if keyframe_points_x[0].interpolation != interpolation:
		if NEWER_THAN_290:
			interpolation_value = bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items[interpolation].value
			keyframe_points_x.foreach_set("interpolation", [interpolation_value] * len(keyframe_points_x))
			keyframe_points_y.foreach_set("interpolation", [interpolation_value] * len(keyframe_points_y))
			keyframe_points_z.foreach_set("interpolation", [interpolation_value] * len(keyframe_points_z))
		else:
			for item in keyframe_points_x:
				item.interpolation = interpolation
			for item in keyframe_points_y:
				item.interpolation = interpolation
			for item in keyframe_points_z:
				item.interpolation = interpolation

def AppendInterKeys_Location(time, location, data_x, data_y, data_z):
	if 0 == len(data_x):
		return
	lastX = data_x[-1]
	lastY = data_y[-1]
	lastZ = data_z[-1]
	lastTime = data_x[-2]
	lastLocation = mathutils.Vector((lastX, lastY, lastZ))
	for interTime in GetInterKeyRange(lastTime, time):
		interLocation = lastLocation.lerp(location, (interTime-lastTime) / (time-lastTime))
		data_x.extend((interTime, interLocation.x))
		data_y.extend((interTime, interLocation.y))
		data_z.extend((interTime, interLocation.z))

def AddKey_Scale(interKey, keyframe_points_scale_x, keyframe_points_scale_y, keyframe_points_scale_z, time, scale):
	AddKey_Location(interKey, keyframe_points_scale_x, keyframe_points_scale_y, keyframe_points_scale_z, time, scale)

def AddKey_Rotation(interKey, keyframe_points_rotation_quaternion_w, keyframe_points_rotation_quaternion_x, keyframe_points_rotation_quaternion_y, keyframe_points_rotation_quaternion_z, time, rotation):
	if(interKey and 0 < len(keyframe_points_rotation_quaternion_w) and 0 < len(keyframe_points_rotation_quaternion_x) and 0 < len(keyframe_points_rotation_quaternion_y) and 0 < len(keyframe_points_rotation_quaternion_z)):
		lastItemW = keyframe_points_rotation_quaternion_w[-1]
		lastItemX = keyframe_points_rotation_quaternion_x[-1]
		lastItemY = keyframe_points_rotation_quaternion_y[-1]
		lastItemZ = keyframe_points_rotation_quaternion_z[-1]
		lastTime = lastItemW.co[0]
		lastRotation = mathutils.Quaternion((lastItemW.co[1], lastItemX.co[1], lastItemY.co[1], lastItemZ.co[1]))
		
		for interTime in GetInterKeyRange(lastTime, time):
			interRotation = lastRotation.slerp(rotation, (interTime -lastTime) / (time-lastTime))
			keyframe_points_rotation_quaternion_w.add(1)
			keyframe_points_rotation_quaternion_x.add(1)
			keyframe_points_rotation_quaternion_y.add(1)
			keyframe_points_rotation_quaternion_z.add(1)
			itemW = keyframe_points_rotation_quaternion_w[-1]
			itemX = keyframe_points_rotation_quaternion_x[-1]
			itemY = keyframe_points_rotation_quaternion_y[-1]
			itemZ = keyframe_points_rotation_quaternion_z[-1]
			itemW.co = [interTime, interRotation.w]
			itemX.co = [interTime, interRotation.x]
			itemY.co = [interTime, interRotation.y]
			itemZ.co = [interTime, interRotation.z]
			itemW.interpolation = 'CONSTANT'
			itemX.interpolation = 'CONSTANT'
			itemY.interpolation = 'CONSTANT'
			itemZ.interpolation = 'CONSTANT'
	
	keyframe_points_rotation_quaternion_w.add(1)
	keyframe_points_rotation_quaternion_x.add(1)
	keyframe_points_rotation_quaternion_y.add(1)
	keyframe_points_rotation_quaternion_z.add(1)
	itemW = keyframe_points_rotation_quaternion_w[-1]
	itemX = keyframe_points_rotation_quaternion_x[-1]
	itemY = keyframe_points_rotation_quaternion_y[-1]
	itemZ = keyframe_points_rotation_quaternion_z[-1]
	itemW.co = [time, rotation.w]
	itemX.co = [time, rotation.x]
	itemY.co = [time, rotation.y]
	itemZ.co = [time, rotation.z]
	itemW.interpolation = 'CONSTANT'
	itemX.interpolation = 'CONSTANT'
	itemY.interpolation = 'CONSTANT'
	itemZ.interpolation = 'CONSTANT'

def AddKeysList_Rotation(interpolation, keyframe_points_w, keyframe_points_x, keyframe_points_y, keyframe_points_z, data_w, data_x, data_y, data_z):
	keyframe_points_w.add(len(data_w) // 2)
	keyframe_points_w.foreach_set("co", data_w)
	keyframe_points_x.add(len(data_x) // 2)
	keyframe_points_x.foreach_set("co", data_x)
	keyframe_points_y.add(len(data_y) // 2)
	keyframe_points_y.foreach_set("co", data_y)
	keyframe_points_z.add(len(data_z) // 2)
	keyframe_points_z.foreach_set("co", data_z)
	if keyframe_points_w[0].interpolation != interpolation:
		if NEWER_THAN_290:
			interpolation_value = bpy.types.Keyframe.bl_rna.properties["interpolation"].enum_items[interpolation].value
			keyframe_points_w.foreach_set("interpolation", [interpolation_value] * len(keyframe_points_w))
			keyframe_points_x.foreach_set("interpolation", [interpolation_value] * len(keyframe_points_x))
			keyframe_points_y.foreach_set("interpolation", [interpolation_value] * len(keyframe_points_y))
			keyframe_points_z.foreach_set("interpolation", [interpolation_value] * len(keyframe_points_z))
		else:
			for item in keyframe_points_w:
				item.interpolation = interpolation
			for item in keyframe_points_x:
				item.interpolation = interpolation
			for item in keyframe_points_y:
				item.interpolation = interpolation
			for item in keyframe_points_z:
				item.interpolation = interpolation

def AppendInterKeys_Rotation(time, rotation, data_w, data_x, data_y, data_z):
	if 0 == len(data_w):
		return
	lastW = data_w[-1]
	lastX = data_x[-1]
	lastY = data_y[-1]
	lastZ = data_z[-1]
	lastTime = data_w[-2]
	lastRotation = mathutils.Quaternion((lastW, lastX, lastY, lastZ))
	for interTime in GetInterKeyRange(lastTime, time):
		interRotation = lastRotation.slerp(rotation, (interTime-lastTime) / (time-lastTime))
		data_w.extend((interTime, interRotation.w))
		data_x.extend((interTime, interRotation.x))
		data_y.extend((interTime, interRotation.y))
		data_z.extend((interTime, interRotation.z))
