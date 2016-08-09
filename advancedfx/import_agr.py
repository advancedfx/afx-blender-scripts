# Copyright (c) advancedfx.org
#
# Last changes:
# 2016-08-05 dominik.matrixstorm.com
#
# First changes:
# 2016-07-19 dominik.matrixstorm.com

import gc
import math
import os
import struct

import bpy, bpy.props, bpy.ops
import mathutils

from io_scene_valvesource import import_smd as vs_import_smd, utils as vs_utils

from .utils import QAngle

class GAgrImporter:
	qc = None
	smd = None

class SmdImporterEx(vs_import_smd.SmdImporter):
	bl_idname = "advancedfx.smd_importer_ex"
	
	filepath = bpy.props.StringProperty(subtype="FILE_PATH")

	skipRemDoubles = bpy.props.BoolProperty(name="",description="",default=False)
	append = bpy.props.EnumProperty(name="",description="",items=(
		('VALIDATE',"",""),
		('APPEND',"",""),
		('NEW_ARMATURE',"","")),
		default='APPEND')
	boneMode = bpy.props.EnumProperty(name="",items=(('NONE','Default',''),('ARROWS','Arrows',''),('SPHERE','Sphere','')),default='SPHERE',description="")

	
	def execute(self, context):
		self.existingBones = []
		self.num_files_imported = 0
		self.readQC(self.filepath, False, False, False, 'XYZ', outer_qc = True)
		GAgrImporter.qc = self.qc
		GAgrImporter.smd = self.smd
		return {'FINISHED'}


def ReadString(file):
	buf = bytearray()
	while True:
		b = file.read(1)
		if len(b) < 1:
			return None
		elif b == b"\0":
			return buf.decode("utf-8")
		else:
			buf.append(b[0])

def ReadBool(file):
	buf = file.read(1)
	if(len(buf) < 1):
		return None
	return struct.unpack('<?', buf)[0]

def ReadInt(file):
	buf = file.read(4)
	if(len(buf) < 4):
		return None
	return struct.unpack('<i', buf)[0]

def ReadDouble(file):
	buf = file.read(8)
	if(len(buf) < 8):
		return None
	return struct.unpack('<d', buf)[0]
	
def ReadVector(file, quakeFormat = False):
	x = ReadDouble(file)
	if x is None:
		return None
	y = ReadDouble(file)
	if y is None:
		return None
	z = ReadDouble(file)
	if z is None:
		return None
	
	return mathutils.Vector((-y,x,z)) if quakeFormat else mathutils.Vector((x,y,z))

def ReadQAngle(file):
	x = ReadDouble(file)
	if x is None:
		return None
	y = ReadDouble(file)
	if y is None:
		return None
	z = ReadDouble(file)
	if z is None:
		return None
	
	return QAngle(x,y,z)

def ReadQuaternion(file, quakeFormat = False):
	x = ReadDouble(file)
	if x is None:
		return None
	y = ReadDouble(file)
	if y is None:
		return None
	z = ReadDouble(file)
	if z is None:
		return None
	w = ReadDouble(file)
	if w is None:
		return None
	
	return mathutils.Quaternion((w,-y,x,z)) if quakeFormat else mathutils.Quaternion((w,x,y,z))

def ReadAgrVersion(file):
	buf = file.read(14)
	if len(buf) < 14:
		return None
	
	cmp = b"afxGameRecord\0"
	
	if buf != cmp:
		return None
	
	return ReadInt(file)

class AgrDictionary:
	def __init__(self):
		self.dict = {}
		self.peeked = None
	
	def Read(self,file):
		if self.peeked is not None:
			oldPeeked = self.peeked
			self.peeked = None
			return oldPeeked
		
		idx = ReadInt(file)
		
		if idx is None:
			return None
		
		if -1 == idx:
			str = ReadString(file)
			if str is None:
				return None
			self.dict[len(self.dict)] = str
			return str
			
		return self.dict[idx]
		
	def Peekaboo(self,file,what):
		if self.peeked is None:
			self.peeked = self.Read(file)
			
		if(what == self.peeked):
			self.peeked = None
			return True
		
		return False

class ModelHandle:
	def __init__(self,handle,modelName):
		self.handle = handle
		self.modelName = modelName

	def __hash__(self):
		return hash((self.handle, self.modelName))

	def __eq__(self, other):
		return (self.handle, self.modelName) == (other.handle, other.modelName)
		
class ModelData:
	def __init__(self,qc,smd):
		self.qc = qc
		self.smd = smd
		self.curves = []
		

class AgrImporter(bpy.types.Operator, vs_utils.Logger):
	bl_idname = "advancedfx.agr_importer"
	bl_label = "HLAE afxGameRecord (.agr)"
	bl_options = {'UNDO'}
	
	# Properties used by the file browser
	filepath = bpy.props.StringProperty(subtype="FILE_PATH")
	filename_ext = ".agr"
	filter_glob = bpy.props.StringProperty(default="*.agr", options={'HIDDEN'})

	# Custom properties
	assetPath = bpy.props.StringProperty(
		name="Asset Path",
		description="Directory path containing the (decompiled) assets in a folder structure as in the pak01_dir.pak.",
		default="",
		#subtype = 'DIR_PATH'
	)

	global_scale = bpy.props.FloatProperty(
		name="Scale",
		description="Scale everything by this value",
		min=0.000001, max=1000000.0,
		soft_min=0.001, soft_max=1.0,
		default=0.01,
	)
	
	#visibleOnly = bpy.props.FloatProperty(
	#	name="Visible Only",
	#	description="If set entities will only be created and keyframed when visible.",
	#	default=True,
	#)
	
	# class properties
	valveMatrixToBlender = mathutils.Matrix.Rotation(math.pi/2,4,'Z')
	
	def execute(self, context):
		try:
			bpy.utils.register_class(SmdImporterEx)
			ok = self.readAgr(context)
		finally:
			bpy.utils.unregister_class(SmdImporterEx)
		
		for area in context.screen.areas:
			if area.type == 'VIEW_3D':
				space = area.spaces.active
				space.grid_lines = 64
				space.grid_scale = self.global_scale * 512
				space.grid_subdivisions = 8
				space.clip_end = self.global_scale * 56756
		
		self.errorReport("Error report")
		
		return {'FINISHED'}
		
	
	def invoke(self, context, event):
		bpy.context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	def importModel(self, context, modelHandle):
		filePath = self.assetPath.rstrip("/\\") + "/" +modelHandle.modelName
		filePath = os.path.splitext(filePath)[0] + ".qc"
		
		GAgrImporter.qc = None
		GAgrImporter.smd = None
		modelData = None
		
		try:
			#bpy.ops.import_scene.smd(filepath=filePath,files=[],doAnim=False)
			bpy.ops.advancedfx.smd_importer_ex(filepath=filePath)
			modelData = ModelData(GAgrImporter.qc,GAgrImporter.smd)
		except:
			self.error("Failed to import \""+filePath+"\".")
			return None
		finally:
			GAgrImporter.qc = None
			GAgrImporter.smd = None
			
		a = modelData.smd.a
		qc = modelData.qc
		
		# Update name:
		a.name = "afx."+str(modelHandle.handle) # this is too long: +"."+modelHandle.modelName + a.name[a.name.rfind(".")+1:]
		
		# Fix rotation:
		if a.rotation_mode != 'QUATERNION':
			a.rotation_mode = 'QUATERNION'
		for bone in a.pose.bones:
			if bone.rotation_mode != 'QUATERNION':
				bone.rotation_mode = 'QUATERNION'
				
		# Scale:
		
		a.scale[0] = self.global_scale
		a.scale[1] = self.global_scale
		a.scale[2] = self.global_scale
		
		# Render visibilty set-up:
		for x in a.children:
			if x != qc.ref_mesh:
				x.hide_render = True
		
		# Create actions and their curves (boobs):
		
		bpy.context.scene.objects.active = qc.ref_mesh
		
		qc.ref_mesh.animation_data_create()
		action = bpy.data.actions.new(name="game_data")
		qc.ref_mesh.animation_data.action = action
		
		modelData.curves.append(action.fcurves.new("hide_render"))
		
		bpy.context.scene.objects.active = a
		
		a.animation_data_create()
		action = bpy.data.actions.new(name="game_data")
		a.animation_data.action = action
		
		for i in range(3):
			modelData.curves.append(action.fcurves.new("location",index = i))
		
		for i in range(4):
			modelData.curves.append(action.fcurves.new("rotation_quaternion",index = i))
		
		num_bones = len(a.pose.bones)
		
		for i in range(num_bones):
			bone = a.pose.bones[modelData.smd.boneIDs[i]]
			
			bone_string = "pose.bones[\"{}\"].".format(bone.name)
			
			for j in range(3):
				modelData.curves.append(action.fcurves.new(bone_string + "location",index = j))
			
			for j in range(4):
				modelData.curves.append(action.fcurves.new(bone_string + "rotation_quaternion",index = j))
		
		return modelData
	
	def readAgr(self,context):
		file = None
		
		try:
			file = open(self.filepath, 'rb')
			
			file.seek(0, 2)
			fileSize = file.tell()
			file.seek(0, 0)
			
			context.window_manager.progress_begin(0.0,1.0)
			
			version = ReadAgrVersion(file)
			
			if version is None:
				self.error('Invalid file format.')
				return False
				
			if 0 != version:
				self.error('Version '+str(version)+' is not supported!')
				return False
			
			firstTime = None
			dict = AgrDictionary()
			modelHandleToModelData = {}
			handleToLastModelHandle = {}
			fps = context.scene.render.fps
			
			stupidCount = 0
			
			while True:
			
				if 0 < fileSize:
					context.window_manager.progress_update(float(file.tell())/float(fileSize))
			
				node0 = dict.Read(file)
				
				if node0 is None:
					break
					
				elif 'deleted' == node0:
					handle = ReadInt(file)
					time = ReadDouble(file)
					
					modelHandle = handleToLastModelHandle.get(handle, None)
					if modelHandle is not None:
						# Make removed ent invisible:
						time = time -firstTime
						time = 1.0 + time * fps
						modelData = modelHandleToModelData.get(modelHandle, False)
						curves = modelData.curves
						bpy.context.scene.objects.active = modelData.qc.ref_mesh
						curves[0].keyframe_points.add(1)
						curves[0].keyframe_points[-1].co = [time, 1.0]
						curves[0].keyframe_points[-1].interpolation = 'CONSTANT'
				
				elif 'entity_state' == node0:
					stupidCount = stupidCount +1
					
					if 4096 <= stupidCount:
						stupidCount = 0
						gc.collect()
						# break
					
					visible = None
					time = None
					modelData = None
					handle = ReadInt(file) if dict.Peekaboo(file,'handle') else None
					if dict.Peekaboo(file,'baseentity'):
						time = ReadDouble(file) if dict.Peekaboo(file, 'time') else None
						if None == firstTime:
							firstTime = time
						time = time -firstTime
						time = 1.0 + time * fps
						
						modelName = dict.Read(file) if dict.Peekaboo(file, 'modelName') else None
						
						visible = ReadBool(file) if dict.Peekaboo(file, 'visible') else None
						
						modelHandle = handleToLastModelHandle.get(handle, None)
						
						if (modelHandle is not None) and (modelHandle.modelName != modelName):
							# Switched model, make old model invisible:
							modelData = modelHandleToModelData.get(modelHandle, False)
							curves = modelData.curves
							bpy.context.scene.objects.active = modelData.qc.ref_mesh
							curves[0].keyframe_points.add(1)
							curves[0].keyframe_points[-1].co = [time, 1.0]
							curves[0].keyframe_points[-1].interpolation = 'CONSTANT'
						
						if modelHandle is None:
							modelHandle = ModelHandle(handle, modelName)
							handleToLastModelHandle[handle] = modelHandle
						
						modelData = modelHandleToModelData.get(modelHandle, False)
						if modelData == False:
							# We have no model with this handle yet, so create a new one:
							modelData = self.importModel(context, modelHandle)
							modelHandleToModelData[modelHandle] = modelData
						
						renderOrigin = ReadVector(file, quakeFormat=True) if dict.Peekaboo(file, 'renderOrigin') else None
						renderAngles = ReadQAngle(file) if dict.Peekaboo(file, 'renderAngles') else None
						
						renderOrigin = renderOrigin * self.global_scale
						renderRotQuat = renderAngles.to_quaternion()
						
						if modelData is not None:
							curves = modelData.curves
							
							bpy.context.scene.objects.active = modelData.qc.ref_mesh
							curves[0].keyframe_points.add(1)
							curves[0].keyframe_points[-1].co = [time, 0.0 if visible else 1.0]
							curves[0].keyframe_points[-1].interpolation = 'CONSTANT'
							
							# TODO: Respect last rotation maybe (so we take shortest path)?
							bpy.context.scene.objects.active = modelData.smd.a
							curves[1+0].keyframe_points.add(1)
							curves[1+0].keyframe_points[-1].co = [time, renderOrigin.x]
							curves[1+0].keyframe_points[-1].interpolation = 'LINEAR'
							curves[1+1].keyframe_points.add(1)
							curves[1+1].keyframe_points[-1].co = [time, renderOrigin.y]
							curves[1+1].keyframe_points[-1].interpolation = 'LINEAR'
							curves[1+2].keyframe_points.add(1)
							curves[1+2].keyframe_points[-1].co = [time, renderOrigin.z]
							curves[1+2].keyframe_points[-1].interpolation = 'LINEAR'
							curves[1+3].keyframe_points.add(1)
							curves[1+3].keyframe_points[-1].co = [time, renderRotQuat.w]
							curves[1+3].keyframe_points[-1].interpolation = 'LINEAR'
							curves[1+4].keyframe_points.add(1)
							curves[1+4].keyframe_points[-1].co = [time, renderRotQuat.x]
							curves[1+4].keyframe_points[-1].interpolation = 'LINEAR'
							curves[1+5].keyframe_points.add(1)
							curves[1+5].keyframe_points[-1].co = [time, renderRotQuat.y]
							curves[1+5].keyframe_points[-1].interpolation = 'LINEAR'
							curves[1+6].keyframe_points.add(1)
							curves[1+6].keyframe_points[-1].co = [time, renderRotQuat.z]
							curves[1+6].keyframe_points[-1].interpolation = 'LINEAR'
						
						dict.Peekaboo(file,'/')
					
					if dict.Peekaboo(file,'baseanimating'):
						skin = ReadInt(file) if dict.Peekaboo(file,'skin') else None
						body = ReadInt(file) if dict.Peekaboo(file,'body') else None
						sequence  = ReadInt(file) if dict.Peekaboo(file,'sequence') else None
						if dict.Peekaboo(file,'boneList'):
							numBones = ReadInt(file)
							
							for i in range(numBones):
								vec = ReadVector(file, quakeFormat=False)
								quat = ReadQuaternion(file, quakeFormat=False)
								
								if (modelData is None):
									continue
								
								#if not(True == visible):
								#	# Only key-frame if visible
								#	continue
								
								if(i < len(modelData.smd.boneIDs)):
									bone = modelData.smd.a.pose.bones[modelData.smd.boneIDs[i]]
									
									# self.warning(str(i)+"("+bone.name+"): "+str(quat))
									
									matrix = mathutils.Matrix.Translation(vec) * quat.to_matrix().to_4x4()
									
									if bone.parent:
										matrix = bone.parent.matrix * matrix
									else:
										matrix = self.valveMatrixToBlender * matrix
									
									bone.matrix = matrix
									
									curves = modelData.curves
									
									bpy.context.scene.objects.active = modelData.smd.a
									curves[8+i*7+0].keyframe_points.add(1)
									curves[8+i*7+0].keyframe_points[-1].co = [time, bone.location.x]
									curves[8+i*7+0].keyframe_points[-1].interpolation = 'LINEAR'
									curves[8+i*7+1].keyframe_points.add(1)
									curves[8+i*7+1].keyframe_points[-1].co = [time, bone.location.y]
									curves[8+i*7+1].keyframe_points[-1].interpolation = 'LINEAR'
									curves[8+i*7+2].keyframe_points.add(1)
									curves[8+i*7+2].keyframe_points[-1].co = [time, bone.location.z]
									curves[8+i*7+2].keyframe_points[-1].interpolation = 'LINEAR'
									curves[8+i*7+3].keyframe_points.add(1)
									curves[8+i*7+3].keyframe_points[-1].co = [time, bone.rotation_quaternion.w]
									curves[8+i*7+3].keyframe_points[-1].interpolation = 'LINEAR'
									curves[8+i*7+4].keyframe_points.add(1)
									curves[8+i*7+4].keyframe_points[-1].co = [time, bone.rotation_quaternion.x]
									curves[8+i*7+4].keyframe_points[-1].interpolation = 'LINEAR'
									curves[8+i*7+5].keyframe_points.add(1)
									curves[8+i*7+5].keyframe_points[-1].co = [time, bone.rotation_quaternion.y]
									curves[8+i*7+5].keyframe_points[-1].interpolation = 'LINEAR'
									curves[8+i*7+6].keyframe_points.add(1)
									curves[8+i*7+6].keyframe_points[-1].co = [time, bone.rotation_quaternion.z]
									curves[8+i*7+6].keyframe_points[-1].interpolation = 'LINEAR'
						
						dict.Peekaboo(file,'/')
					
					viewModel = ReadBool(file) if dict.Peekaboo(file,'viewmodel') else None
					
					#if modelData is not None:
					#	for fc in modelData.curves:
					#		fc.update()
					
					dict.Peekaboo(file,'/')
				
				else:
					self.warning('Unknown packet at '+str(file.tell()))
					return False
			
			context.window_manager.progress_end()
			
		finally:
			if file is not None:
				file.close()
		
		return True
