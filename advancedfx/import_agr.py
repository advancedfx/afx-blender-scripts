import gc
import math
import os
import struct
import copy
from collections import defaultdict

import traceback

import bpy, bpy.props, bpy.ops, time
import mathutils

from os.path import splitext, basename

from io_scene_valvesource import import_smd as vs_import_smd, utils as vs_utils

from advancedfx import utils as afx_utils

class GAgrImporter:
	onlyBones = False
	smd = None

class SmdImporterEx(vs_import_smd.SmdImporter):
	bl_idname = "advancedfx.smd_importer_ex"
	
	qc = None
	smd = None
	smdSkip = False

	# Properties used by the file browser
	filepath : bpy.props.StringProperty(name="File Path", description="File filepath used for importing the SMD/VTA/DMX/QC file", maxlen=1024, default="", options={'HIDDEN'})
	files : bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN'})
	directory : bpy.props.StringProperty(maxlen=1024, default="", subtype='FILE_PATH', options={'HIDDEN'})
	filter_folder : bpy.props.BoolProperty(name="Filter Folders", description="", default=True, options={'HIDDEN'})
	filter_glob : bpy.props.StringProperty(default="*.smd;*.vta;*.dmx;*.qc;*.qci", options={'HIDDEN'})

	# Custom properties
	doAnim : bpy.props.BoolProperty(name="importer_doanims", default=True)
	createCollections : bpy.props.BoolProperty(name="importer_use_collections", description="importer_use_collections_tip", default=False)
	makeCamera : bpy.props.BoolProperty(name="importer_makecamera",description="importer_makecamera_tip",default=False)
	append : bpy.props.EnumProperty(name="importer_bones_mode",description="importer_bones_mode_desc",items=(
		('VALIDATE',"importer_bones_validate","importer_bones_validate_desc"),
		('APPEND',"importer_bones_append","importer_bones_append_desc"),
		('NEW_ARMATURE',"importer_bones_newarm","importer_bones_newarm_desc")),
		default='APPEND')
	upAxis : bpy.props.EnumProperty(name="Up Axis",items=vs_utils.axes,default='Z',description="importer_up_tip")
	rotMode : bpy.props.EnumProperty(name="importer_rotmode",items=( ('XYZ', "Euler", ''), ('QUATERNION', "Quaternion", "") ),default='XYZ',description="importer_rotmode_tip")
	boneMode : bpy.props.EnumProperty(name="importer_bonemode",items=(('NONE','Default',''),('ARROWS','Arrows',''),('SPHERE','Sphere','')),default='SPHERE',description="importer_bonemode_tip")
	
	def execute(self, context):
		self.existingBones = []
		self.num_files_imported = 0
		self.readQC(self.filepath, False, False, False, 'XYZ', outer_qc = True)
		GAgrImporter.smd = self.smd
		return {'FINISHED'}
	
	def readPolys(self):
		if GAgrImporter.onlyBones:
			return
		super(SmdImporterEx, self).readPolys()
	
	def readShapes(self):
		if GAgrImporter.onlyBones:
			return
		super(SmdImporterEx, self).readShapes()
	
	def readSMD(self, filepath, upAxis, rotMode, newscene = False, smd_type = None, target_layer = 0):
		s = splitext(basename(filepath))[0].rstrip("123456789")
		if SmdImporterEx.smdSkip and (smd_type == vs_utils.PHYS or s.endswith("_lod") or any(filepath.endswith(u) for u in ("skeleto.smd", "skel.smd"))):
			return 0
		else:
			return super().readSMD(filepath, upAxis, rotMode, newscene, smd_type, target_layer) # call parent method

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
	
def ReadFloat(file):
	buf = file.read(4)
	if(len(buf) < 4):
		return None
	return struct.unpack('<f', buf)[0]

def ReadDouble(file):
	buf = file.read(8)
	if(len(buf) < 8):
		return None
	return struct.unpack('<d', buf)[0]
	
def ReadVector(file, quakeFormat = False):
	x = ReadFloat(file)
	if x is None:
		return None
	y = ReadFloat(file)
	if y is None:
		return None
	z = ReadFloat(file)
	if z is None:
		return None
		
	if math.isinf(x) or math.isinf(y) or math.isinf(z):
		x = 0
		y = 0
		z = 0
	
	return mathutils.Vector((-y,x,z)) if quakeFormat else mathutils.Vector((x,y,z))

def ReadQAngle(file):
	x = ReadFloat(file)
	if x is None:
		return None
	y = ReadFloat(file)
	if y is None:
		return None
	z = ReadFloat(file)
	if z is None:
		return None
	
	if math.isinf(x) or math.isinf(y) or math.isinf(z):
		x = 0
		y = 0
		z = 0
	
	return afx_utils.QAngle(x,y,z)

def ReadQuaternion(file, quakeFormat = False):
	x = ReadFloat(file)
	if x is None:
		return None
	y = ReadFloat(file)
	if y is None:
		return None
	z = ReadFloat(file)
	if z is None:
		return None
	w = ReadFloat(file)
	if w is None:
		return None
	
	if math.isinf(x) or math.isinf(y) or math.isinf(z) or math.isinf(w):
		w = 1
		x = 0
		y = 0
		z = 0
	
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
		self.dictionary = {}
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
			self.dictionary[len(self.dictionary)] = str
			return str
			
		return self.dictionary[idx]
		
	def Peekaboo(self,file,what):
		if self.peeked is None:
			self.peeked = self.Read(file)
			
		if(what == self.peeked):
			self.peeked = None
			return True
		
		return False
		
class ModelData:
	def __init__(self,smd):
		self.smd = smd
		self.curves = []

class ModelHandle:
	def __init__(self,objNr,modelName):
		self.objNr = objNr
		self.modelName = modelName
		self.modelData = False
		self.lastRenderOrigin = None
		self.lastRenderRotQuat = None
		self.boneLastRenderRotQuats = {}
		self.camData = None
		
		self.lastTime = None
		self.visible = None
		self.location = None
		self.rotation = None
		self.bones = None

		# We are lazy, so we use frame 0 to set as not visible (initially) / hide_render 1:
		self.visibilityFrames = [0, 1]
		self.locationXFrames = []
		self.locationYFrames = []
		self.locationZFrames = []
		self.rotationWFrames = []
		self.rotationXFrames = []
		self.rotationYFrames = []
		self.rotationZFrames = []
		self.boneLocationXFrames = defaultdict(list)
		self.boneLocationYFrames = defaultdict(list)
		self.boneLocationZFrames = defaultdict(list)
		self.boneRotationWFrames = defaultdict(list)
		self.boneRotationXFrames = defaultdict(list)
		self.boneRotationYFrames = defaultdict(list)
		self.boneRotationZFrames = defaultdict(list)
	
	def UpdateVisible(self,curTime,visible,interKey):
		self.Update(curTime,interKey)
		self.visible = visible
	
	def UpdateLocation(self,curTime,location,interKey):
		self.Update(curTime,interKey)
		self.location = location
		
	def UpdateRotation(self,curTime,rotation,interKey):
		self.Update(curTime,interKey)
		self.rotation = rotation
	
	def UpdateBones(self,curTime,bones,interKey):
		self.Update(curTime,interKey)
		self.bones = bones
	
	def Update(self,curTime,interKey):
		if((self.lastTime is not None) and ((curTime is None) or (self.lastTime < curTime))):
			
			if self.visible is not None:
				if interKey:
					afx_utils.AppendInterKeys_Visible(self.lastTime, 0 if self.visible else 1, self.visibilityFrames)
				self.visibilityFrames.extend((self.lastTime, 0 if self.visible else 1))
			
			if self.location is not None:
			
				self.lastRenderOrigin = self.location
			
				if interKey:
					afx_utils.AppendInterKeys_Location(self.lastTime, self.location, self.locationXFrames, self.locationYFrames, self.locationZFrames)
				self.locationXFrames.extend((self.lastTime, self.location.x))
				self.locationYFrames.extend((self.lastTime, self.location.y))
				self.locationZFrames.extend((self.lastTime, self.location.z))
			
			if self.rotation is not None:
			
				# make sure we take the shortest path:
				if self.lastRenderRotQuat is not None:
					dot = self.lastRenderRotQuat.dot(self.rotation)
					if dot < 0:
						self.rotation.negate()
				self.lastRenderRotQuat = self.rotation
			
				if interKey:
					afx_utils.AppendInterKeys_Rotation(self.lastTime, self.rotation, self.rotationWFrames, self.rotationXFrames, self.rotationYFrames, self.rotationZFrames)
				self.rotationWFrames.extend((self.lastTime, self.rotation.w))
				self.rotationXFrames.extend((self.lastTime, self.rotation.x))
				self.rotationYFrames.extend((self.lastTime, self.rotation.y))
				self.rotationZFrames.extend((self.lastTime, self.rotation.z))
				
			if self.bones is not None:
				for idx,i in enumerate(self.bones):
					
					bone = self.bones[i]
					
					renderRotQuat = bone.rotation_quaternion.copy()
					
					# make sure we take the shortest path:
					if i in self.boneLastRenderRotQuats:
						dot = self.boneLastRenderRotQuats[i].dot(renderRotQuat)
						if dot < 0:
							renderRotQuat.negate()
					self.boneLastRenderRotQuats[i] = renderRotQuat
					
					if interKey:
						afx_utils.AppendInterKeys_Location(self.lastTime, bone.location, self.boneLocationXFrames[i], self.boneLocationYFrames[i], self.boneLocationZFrames[i])
						afx_utils.AppendInterKeys_Rotation(self.lastTime, renderRotQuat, self.boneRotationWFrames[i], self.boneRotationXFrames[i], self.boneRotationYFrames[i], self.boneRotationZFrames[i])
					
					self.boneLocationXFrames[i].extend((self.lastTime, bone.location.x))
					self.boneLocationYFrames[i].extend((self.lastTime, bone.location.y))
					self.boneLocationZFrames[i].extend((self.lastTime, bone.location.z))
					
					self.boneRotationWFrames[i].extend((self.lastTime, renderRotQuat.w))
					self.boneRotationXFrames[i].extend((self.lastTime, renderRotQuat.x))
					self.boneRotationYFrames[i].extend((self.lastTime, renderRotQuat.y))
					self.boneRotationZFrames[i].extend((self.lastTime, renderRotQuat.z))
			
			self.visible = None
			self.location = None
			self.rotation = None
			self.bones = None
		
		self.lastTime = curTime

#	
#	def __hash__(self):
#		return hash((self.handle, self.modelName))
#	
#	def __eq__(self, other):
#		return (self.handle, self.modelName) == (other.handle, other.modelName)

class CameraData:
	def __init__(self,o,c):
		self.o = o
		self.c = c
		self.curves = []
		
		self.lastRenderOrigin = None
		self.lastRenderRotQuat = None

		self.lastTime = None
		self.lens = None
		self.location = None
		self.rotation = None
		
		self.locationXFrames = []
		self.locationYFrames = []
		self.locationZFrames = []
		self.rotationWFrames = []
		self.rotationXFrames = []
		self.rotationYFrames = []
		self.rotationZFrames = []
		self.lensFrames = []
		
	def UpdateLens(self,curTime,lens,interKey):
		self.Update(curTime,interKey)
		self.lens = lens
	
	def UpdateLocation(self,curTime,location,interKey):
		self.Update(curTime,interKey)
		self.location = location
		
	def UpdateRotation(self,curTime,rotation,interKey):
		self.Update(curTime,interKey)
		self.rotation = rotation
	
	def Update(self,curTime,interKey):
		if((self.lastTime is not None) and ((curTime is None) or (self.lastTime < curTime))):
			
			if self.lens is not None:
				if interKey:
					afx_utils.AppendInterKeys_Value(self.lastTime, self.lens, self.lensFrames)

				self.lensFrames.extend((self.lastTime, self.lens))
			
			if self.location is not None:
			
				self.lastRenderOrigin = self.location
			
				if interKey:
					afx_utils.AppendInterKeys_Location(self.lastTime, self.location, self.locationXFrames, self.locationYFrames, self.locationZFrames)
				self.locationXFrames.extend((self.lastTime, self.location.x))
				self.locationYFrames.extend((self.lastTime, self.location.y))
				self.locationZFrames.extend((self.lastTime, self.location.z))
			
			if self.rotation is not None:
			
				# make sure we take the shortest path:
				if self.lastRenderRotQuat is not None:
					dot = self.lastRenderRotQuat.dot(self.rotation)
					if dot < 0:
						self.rotation.negate()
				self.lastRenderRotQuat = self.rotation
			
				if interKey:
					afx_utils.AppendInterKeys_Rotation(self.lastTime, self.rotation, self.rotationWFrames, self.rotationXFrames, self.rotationYFrames, self.rotationZFrames)
				self.rotationWFrames.extend((self.lastTime, self.rotation.w))
				self.rotationXFrames.extend((self.lastTime, self.rotation.x))
				self.rotationYFrames.extend((self.lastTime, self.rotation.y))
				self.rotationZFrames.extend((self.lastTime, self.rotation.z))
			
			self.lens = None
			self.location = None
			self.rotation = None
		
		self.lastTime = curTime

class AgrTimeConverter:
	def __init__(self,context):
		self.fps = context.scene.render.fps
		self.time = 0
		self.frameTime = 0
		self.newTime = 0
		self.errorCount = 0
		self.maxError = None
		
	def Frame(self,frameTime):
		self.time = self.newTime
		self.frameTime = frameTime
		
		if 0 != frameTime:
			fps = 1.0/frameTime
			error = self.fps -fps
			if (0>= error) or (0.001 < error):
				self.errorCount = self.errorCount + 1
				if (self.maxError is None) or (abs(self.maxError) < abs(error)):
					self.maxError = error
					
	def FrameEnd(self):
		self.newTime = self.time + self.frameTime
		
	def GetTime(self):
		return 1.0 + self.time * self.fps

class AgrImporter(bpy.types.Operator, vs_utils.Logger):
	bl_idname = "advancedfx.agrimporter"
	bl_label = "HLAE afxGameRecord (.agr)"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}
	
	# Properties used by the file browser
	filepath: bpy.props.StringProperty(subtype="FILE_PATH")
	filter_glob: bpy.props.StringProperty(default="*.agr", options={'HIDDEN'})

	# Custom properties	
	assetPath: bpy.props.StringProperty(
		name="Asset Path",
		description="Directory path containing the (decompiled) assets in a folder structure as in the pak01_dir.pak.",
		default="",
		#subtype = 'DIR_PATH'
	)

	interKey: bpy.props.BoolProperty(
		name="Add interpolated key frames",
		description="Create interpolated key frames for frames in-between the original key frames.",
		default=False)

	global_scale: bpy.props.FloatProperty(
		name="Scale",
		description="Scale everything by this value (0.01 old default, 0.0254 is more accurate)",
		min=0.000001, max=1000000.0,
		soft_min=0.001, soft_max=1.0,
		default=0.01,
	)
	
	frame_rate: bpy.props.IntProperty(
		name="Frame Rate",
		description="Sets Frame Rate of the project (Between 1 and 1000 FPS).",
		min=1, max=1000,
		soft_min=25, soft_max=60,
		default=30,
	)

	scaleInvisibleZero: bpy.props.BoolProperty(
		name="Scale invisible to zero",
		description="If set entities will scaled to zero when not visible.",
		default=False,
	)
	
	smdSkip: bpy.props.BoolProperty(
		name="Skip Physic, LOD and Shared_Player_Skeleton meshes",
		description="Skips the import of physic (collision) meshes if the .qc contains them.",
		default = True
	)
	
	qcSkip: bpy.props.BoolProperty(
		name="Skip Stattrack and Stickers",
		description="Skips the import of Stattrack and Sticker meshes if the .qc contains them.",
		default = True
	)
	
	onlyBones: bpy.props.BoolProperty(
		name="Bones (skeleton) only",
		description="Import only bones (skeletons) (faster).",
		default=False)
		
	modelInstancing: bpy.props.BoolProperty(
		name="Model instancing",
		description="Objects with same model are instanced, animation data is separate and modifiers duplicated (faster). Recommended to disable it for beginners, who want to export it to other 3D application",
		default=True)
	
	keyframeInterpolation: bpy.props.EnumProperty(
		name="Keyframe interpolation",
		description="Constant recommended for beginners." if afx_utils.NEWER_THAN_290 else "Constant recommended for beginners. Advanced users can choose Bezier for significantly faster import times.",
		items=[
			('CONSTANT', "Constant (recommended)", "No interpolation"),
			('LINEAR', "Linear", "Linear interpolation"),
			('BEZIER', "Bezier" if afx_utils.NEWER_THAN_290 else "Bezier (fast import)", "Smooth interpolation"),
		],
		default='CONSTANT'
	)
	
	# class properties
	valveMatrixToBlender = mathutils.Matrix.Rotation(math.pi/2,4,'Z')
	blenderCamUpQuat = mathutils.Quaternion((math.cos(0.5 * math.radians(90.0)), math.sin(0.5* math.radians(90.0)), 0.0, 0.0))
	
	def execute(self, context):
		time_start = time.time()
		result = None
		try:
			bpy.utils.unregister_class(vs_import_smd.SmdImporter)
			bpy.utils.register_class(SmdImporterEx)
			result = self.readAgr(context)
		finally:
			bpy.utils.unregister_class(SmdImporterEx)
			bpy.utils.register_class(vs_import_smd.SmdImporter)

		for area in context.screen.areas:
			if area.type == 'VIEW_3D':
				space = area.spaces.active
				#space.grid_lines = 64
				#space.grid_scale = self.global_scale * 512
				#space.grid_subdivisions = 8
				space.clip_end = self.global_scale * 56756
		
		self.errorReport("Error report")
        
		if result is not None:
			if result['frameBegin'] is not None:
				bpy.context.scene.frame_start = result['frameBegin']
			if result['frameEnd'] is not None:
				bpy.context.scene.frame_end = result['frameEnd']
		
		print("AGR import finished in %.4f sec." % (time.time() - time_start))
		return {'FINISHED'}
	
	def invoke(self, context, event):
		bpy.context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	def addCurvesToModel(self, context, modelData):
		
		a = modelData.smd.a
		
		# Create actions and their curves (boobs):
		#vs_utils.select_only(a)
		
		a.animation_data_create()
		action = bpy.data.actions.new(name="game_data")
		a.animation_data.action = action
		
		modelData.curves.append(action.fcurves.new("hide_render"))
		
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
				
		# Create visibility driver:
		
		for child in a.children:
			d = child.driver_add('hide_render').driver
			d.type = 'AVERAGE'
			v = d.variables.new()
			v.name = 'hide_render'
			v.targets[0].id = a
			v.targets[0].data_path = 'hide_render'
			
		if self.scaleInvisibleZero:
			
			ds = a.driver_add('scale')
			
			for df in ds:
				d = df.driver
				d.type = 'AVERAGE'
				v = d.variables.new()
				v.name = 'hide_render'
				v.targets[0].id = a
				v.targets[0].data_path = 'hide_render'
				m = df.modifiers.new('GENERATOR')
				m.coefficients[0] = self.global_scale
				m.coefficients[1] = -self.global_scale
				m.poly_order = 1
				m.mode = 'POLYNOMIAL'
				m.use_additive = False
		
		return modelData
	
	def importModel(self, context, modelHandle):
	
		def makeModelName(modelHandle):
			name = modelHandle.modelName.rsplit('/',1)
			name = name[len(name) -1]
			name = (name[:30] + '..') if len(name) > 30 else name
			name = "afx." +str(modelHandle.objNr)+ " " + name
			return name
			
		def copyObj(src,parent=None):
			dst = src.copy()
			dst.animation_data_clear()
			dst.modifiers.clear()
			
			for srcMod in src.modifiers:
				
				dstMod = dst.modifiers.new(srcMod.name, srcMod.type)
				
				#collect names of writable properties
				properties = [p.identifier for p in srcMod.bl_rna.properties
							  if not p.is_readonly]

				# copy those properties
				for prop in properties:
					setattr(dstMod, prop, getattr(srcMod, prop))
		
				if (srcMod.name == 'Armature') and (srcMod.object == src.parent):
					dstMod.object = parent
			
			bpy.context.scene.collection.objects.link(dst)
			
			for srcChild in src.children:
				dstChild = copyObj(srcChild,dst)
				dstChild.parent = dst
				dstChild.matrix_parent_inverse = srcChild.matrix_parent_inverse.copy()
			
			return dst
		
		modelData = None
		
		if self.modelInstancing:
			modelData = self.modelObjects.pop(modelHandle.modelName, None)
		
		if modelData is None:
			# No instance we are allowed to use, so import it for real:
		
			filePath = self.assetPath.rstrip("/\\") + "/" +modelHandle.modelName.lower()
			filePath = os.path.splitext(filePath)[0]
			filePath = filePath + "/" + os.path.basename(filePath).lower() + ".qc"
			
			SmdImporterEx.smdSkip = self.smdSkip
			GAgrImporter.smd = None
			GAgrImporter.onlyBones = self.onlyBones
			modelData = None

			try:
				if self.qcSkip and any(filePath.endswith(a) for a in ("stattrack.qc", "decal_a.qc", "decal_b.qc", "decal_c.qc", "decal_d.qc", "decal_e.qc")):
					return
				bpy.ops.advancedfx.smd_importer_ex(filepath=filePath, doAnim=False)
				modelData = ModelData(GAgrImporter.smd)
			except Exception as e:
				if '?.qc' in str(e):
					pass
				else:
					self.error("Failed to import \""+filePath+"\".")
				return None
			finally:
				GAgrImporter.smd = None
				
			armature = modelData.smd.a
			
			# Update name:
			armature.name = makeModelName(modelHandle)
			
			# Fix rotation:
			if armature.rotation_mode != 'QUATERNION':
				armature.rotation_mode = 'QUATERNION'
			for bone in armature.pose.bones:
				if bone.rotation_mode != 'QUATERNION':
					bone.rotation_mode = 'QUATERNION'
						
			# Scale:
			
			armature.scale[0] = self.global_scale
			armature.scale[1] = self.global_scale
			armature.scale[2] = self.global_scale
			
			# Insert into instance dictionary:
			self.modelObjects[modelHandle.modelName] = modelData
		
		else:
			print("Instancing %i (%s)." % (modelHandle.objNr,modelHandle.modelName))
			modelData = copy.copy(modelData)
			
			modelData.smd = copy.copy(modelData.smd)
			modelData.smd.a = copyObj(modelData.smd.a)
			modelData.smd.a.name = makeModelName(modelHandle)
			
			modelData.curves = []
		
		modelData = self.addCurvesToModel(context, modelData)
		
		return modelData
	
	def createCamera(self, context, camName):
		
		c = bpy.data.cameras.new(camName)
		o = bpy.data.objects.new(camName, c)

		context.scene.collection.objects.link(o)

		#vs_utils.select_only(o)
			
		camData = CameraData(o,c)
			
		# Rotation mode:
		if o.rotation_mode != 'QUATERNION':
			o.rotation_mode = 'QUATERNION'
				
		
		# Create actions and their curves:
		
		o.animation_data_create()
		action = bpy.data.actions.new(name="game_data")
		o.animation_data.action = action
		
		for i in range(3):
			camData.curves.append(action.fcurves.new("location",index = i))
		
		for i in range(4):
			camData.curves.append(action.fcurves.new("rotation_quaternion",index = i))
			
		c.animation_data_create()
		action = bpy.data.actions.new(name="game_data")
		c.animation_data.action = action
			
		camData.curves.append(action.fcurves.new("lens"))
		
		return camData
	
	def readAgr(self,context):
		file = None
		result = { 'result': False, 'frameBegin': 1, 'frameEnd': None }
		bpy.context.scene.render.fps = self.frame_rate

		try:
			self.modelObjects = {}
		
			file = open(self.filepath, 'rb')
			
			if file is None:
				self.error('Could not open file.')
				return result
			
			file.seek(0, 2)
			fileSize = file.tell()
			file.seek(0, 0)
			
			context.window_manager.progress_begin(0.0, 1.0)
			
			version = ReadAgrVersion(file)
			
			if version is None:
				self.error('Invalid file format.')
				return result
				
			if 5 != version:
				self.error('Version '+str(version)+' is not supported!')
				return result
				
			timeConverter = AgrTimeConverter(context)
			currentTime = timeConverter.GetTime()
			dictionary = AgrDictionary()
			handleToLastModelHandle = {}
			unusedModelHandles = []
			camData = None
			
			modelHandles = []
			
			stupidCount = 0
			
			objNr = 0
			
			while True:
			
				if 0 < fileSize and 0 == stupidCount % 100:
					val = float(file.tell())/float(fileSize)
					context.window_manager.progress_update(val * 0.5)
					print("AGR Read %f%%" % (100*val))
				
				stupidCount = stupidCount +1
				
				if 4096 <= stupidCount:
					stupidCount = 0
					gc.collect()
					#break
				
				node0 = dictionary.Read(file)
				
				if node0 is None:
					break
					
				elif 'afxFrame' == node0:
					frameTime = ReadFloat(file)
					
					timeConverter.Frame(frameTime)
					currentTime = timeConverter.GetTime()
					
					afxHiddenOffset = ReadInt(file)
					if afxHiddenOffset:
						curOffset = file.tell()
						file.seek(afxHiddenOffset -4, 1)
						
						numHidden = ReadInt(file)
						for i in range(numHidden):
							handle = ReadInt(file)
							
							modelHandle = handleToLastModelHandle.pop(handle, None)
							if modelHandle is not None:
								# Make ent invisible:
								modelData =  modelHandle.modelData
								if modelData: # this can happen if the model could not be loaded
									modelHandle.UpdateVisible(currentTime, False, self.interKey)
								
								unusedModelHandles.append(modelHandle)
								#print("Marking %i (%s) as hidden/reusable." % (modelHandle.objNr,modelHandle.modelName))
							
						file.seek(curOffset,0)
						
				elif 'afxFrameEnd' == node0:
					timeConverter.FrameEnd()
					
				elif 'afxHidden' == node0:
					# skipped, because will be handled earlier by afxHiddenOffset
					
					numHidden = ReadInt(file)
					for i in range(numHidden):
						handle = ReadInt(file)
				
				elif 'deleted' == node0:
					handle = ReadInt(file)
					modelHandle = handleToLastModelHandle.pop(handle, None)
					if modelHandle is not None:
						# Make removed ent invisible:
						modelData = modelHandle.modelData
						if modelData: # this can happen if the model could not be loaded
							modelHandle.UpdateVisible(currentTime, False, self.interKey)
						
						unusedModelHandles.append(modelHandle)
						#print("Marking %i (%s) as deleted/reusable." % (modelHandle.objNr,modelHandle.modelName))
				
				elif 'entity_state' == node0:
					visible = None
					modelHandle = None
					modelData = None
					handle = ReadInt(file)
					if dictionary.Peekaboo(file,'baseentity'):
						
						modelName = dictionary.Read(file)
						
						visible = ReadBool(file)
						
						renderOrigin = ReadVector(file, quakeFormat=True)
						renderAngles = ReadQAngle(file)
						
						renderOrigin = renderOrigin * self.global_scale
						renderRotQuat = renderAngles.to_quaternion()
						
						modelHandle = handleToLastModelHandle.get(handle, None)
						
						if (modelHandle is not None) and (modelHandle.modelName != modelName):
							# Switched model, make old model invisible:
							modelData = modelHandle.modelData
							if modelData: # this can happen if the model could not be loaded
								modelHandle.UpdateVisible(currentTime, False, self.interKey)
							
							modelHandle = None
						
						if modelHandle is None:
							
							# Check if we can reuse s.th. and if not create new one:
							
							bestIndex = 0
							bestLength = 0
							
							for idx,val in enumerate(unusedModelHandles):
								if (val.modelName == modelName) and ((modelHandle is None) or val.lastRenderOrigin is None or ((val.lastRenderOrigin -renderOrigin).length < bestLength)):
									modelHandle = val
									bestLength = 0 if val.lastRenderOrigin is None else (val.lastRenderOrigin -renderOrigin).length
									bestIndex = idx
							
							if modelHandle is not None:
								# Use the one we found:
								del unusedModelHandles[bestIndex]
								print("Reusing %i (%s)." % (modelHandle.objNr,modelHandle.modelName))
							else:
								# If not then create a new one:
								objNr = objNr + 1
								modelHandle = ModelHandle(objNr, modelName)
								print("Creating %i (%s)." % (modelHandle.objNr,modelHandle.modelName))
								modelHandles.append(modelHandle)
							
							handleToLastModelHandle[handle] = modelHandle
						
						modelData = modelHandle.modelData
						if modelData is False:
							# We have not tried to import the model for this (new) handle yet, so try to import it:
							modelData = self.importModel(context, modelHandle)
							modelHandle.modelData = modelData
						
						if modelData is not None:
							modelHandle.UpdateVisible(currentTime, visible, self.interKey)
							modelHandle.UpdateLocation(currentTime, renderOrigin, self.interKey)
							modelHandle.UpdateRotation(currentTime, renderRotQuat, self.interKey)
						
					if dictionary.Peekaboo(file,'baseanimating'):
						#skin = ReadInt(file)
						#body = ReadInt(file)
						#sequence  = ReadInt(file)
						hasBoneList = ReadBool(file)
						if hasBoneList:
							numBones = ReadInt(file)
							
							bones = {}
							
							for i in range(numBones):
								#pos = file.tell()
								vec = ReadVector(file, quakeFormat=False)
								quat = ReadQuaternion(file, quakeFormat=False)
								
								if (modelData is None):
									continue
								
								#if not(True == visible):
								#	# Only key-frame if visible
								#	continue
								
								if(i < len(modelData.smd.boneIDs)):
									bone = modelData.smd.a.pose.bones[modelData.smd.boneIDs[i]]
									
									#self.warning(str(pos)+": "+str(i)+"("+bone.name+"): "+str(vec)+" "+str(quat))
									
									matrix = mathutils.Matrix.Translation(vec) @ quat.to_matrix().to_4x4()
									
									if bone.parent:
										matrix = bone.parent.matrix @ matrix
									else:
										matrix = self.valveMatrixToBlender @ matrix
									
									bone.matrix = matrix
									
									bones[i] = bone
									
							modelHandle.UpdateBones(currentTime,bones,self.interKey)
					
					if dictionary.Peekaboo(file,'camera'):
						thidPerson = ReadBool(file)
						pos = ReadVector(file, quakeFormat=True)
						rot = ReadQAngle(file)
						fov = ReadFloat(file)
						
						modelCamData = modelHandle.camData
						if modelHandle.camData is None:
							modelCamData = self.createCamera(context,"camera."+str(modelHandle.objNr))
							modelHandle.camData = modelCamData
						
						lens = modelCamData.c.sensor_width / (2.0 * math.tan(math.radians(fov) / 2.0))
						
						renderOrigin = pos * self.global_scale
						renderRotQuat = rot.to_quaternion() @ self.blenderCamUpQuat
						
						modelCamData.UpdateLens(currentTime, lens, self.interKey)
						modelCamData.UpdateLocation(currentTime, renderOrigin, self.interKey)
						modelCamData.UpdateRotation(currentTime, renderRotQuat, self.interKey)
					
					dictionary.Peekaboo(file,'/')
					
					viewModel = ReadBool(file)
					
					#if modelData is not None:
					#	for fc in modelData.curves:
					#		fc.update()
					
				elif 'afxCam' == node0:
					
					if camData is None:
						camData = self.createCamera(context,"afxCam")
					
						if camData is None:
							self.error("Failed to create camera.")
							return result
					
					
					renderOrigin = ReadVector(file, quakeFormat=True)
					renderAngles = ReadQAngle(file)
					
					fov = ReadFloat(file)
					
					lens = camData.c.sensor_width / (2.0 * math.tan(math.radians(fov) / 2.0))
					
					renderOrigin = renderOrigin * self.global_scale
					renderRotQuat = renderAngles.to_quaternion() @ self.blenderCamUpQuat
					
					camData.UpdateLens(currentTime, lens, self.interKey)
					camData.UpdateLocation(currentTime, renderOrigin, self.interKey)
					camData.UpdateRotation(currentTime, renderRotQuat, self.interKey)
				
				else:
					self.warning('Unknown packet at '+str(file.tell()))
					return result
			
			totalFrames = 0
			for modelHandle in modelHandles:
				modelHandle.Update(None,self.interKey) #finish lingering updates
				modelCamData = modelHandle.camData
				if modelCamData is not None:
					modelCamData.Update(None,self.interKey) #finish lingering updates
					totalFrames += len(modelCamData.locationXFrames) * 3
					totalFrames += len(modelCamData.rotationWFrames) * 4
					totalFrames += len(modelCamData.lensFrames)
				totalFrames += len(modelHandle.visibilityFrames)
				totalFrames += len(modelHandle.locationXFrames) * 3
				totalFrames += len(modelHandle.rotationWFrames) * 4
				for i in modelHandle.boneLocationXFrames:
					totalFrames += len(modelHandle.boneLocationXFrames[i]) * 3
					totalFrames += len(modelHandle.boneRotationWFrames[i]) * 4
			if camData is not None:
				camData.Update(None,self.interKey) #finish lingering updates
				totalFrames += len(camData.locationXFrames) * 3
				totalFrames += len(camData.rotationWFrames) * 4
				totalFrames += len(camData.lensFrames)
			
			importedFrames = 0
			
			def updateImportProgress(newFrames):
				nonlocal importedFrames
				importedFrames += newFrames
				val = importedFrames / totalFrames
				print("AGR Import %f%%" % (100*val))
				context.window_manager.progress_update(0.5 + val * 0.5)
			
			for modelHandle in modelHandles:
				modelCamData = modelHandle.camData
				if modelCamData is not None:
					curves = modelCamData.curves
					afx_utils.AddKeysList_Location(self.keyframeInterpolation, curves[0].keyframe_points, curves[1].keyframe_points, curves[2].keyframe_points, modelCamData.locationXFrames, modelCamData.locationYFrames, modelCamData.locationZFrames)
					afx_utils.AddKeysList_Rotation(self.keyframeInterpolation, curves[3].keyframe_points, curves[4].keyframe_points, curves[5].keyframe_points, curves[6].keyframe_points, modelCamData.rotationWFrames, modelCamData.rotationXFrames, modelCamData.rotationYFrames, modelCamData.rotationZFrames)
					afx_utils.AddKeysList_Value(self.keyframeInterpolation, curves[7].keyframe_points, modelCamData.lensFrames)
					updateImportProgress(len(modelCamData.locationXFrames) * 3 + len(modelCamData.rotationWFrames) * 4 + len(modelCamData.lensFrames))
					for curve in curves:
						curve.update()
				if modelHandle.modelData is None:
					continue
				curves = modelHandle.modelData.curves
				afx_utils.AddKeysList_Visible(curves[0].keyframe_points, modelHandle.visibilityFrames)
				afx_utils.AddKeysList_Location(self.keyframeInterpolation, curves[1].keyframe_points, curves[2].keyframe_points, curves[3].keyframe_points, modelHandle.locationXFrames, modelHandle.locationYFrames, modelHandle.locationZFrames)
				afx_utils.AddKeysList_Rotation(self.keyframeInterpolation, curves[4].keyframe_points, curves[5].keyframe_points, curves[6].keyframe_points, curves[7].keyframe_points, modelHandle.rotationWFrames, modelHandle.rotationXFrames, modelHandle.rotationYFrames, modelHandle.rotationZFrames)
				updateImportProgress(len(modelHandle.visibilityFrames) + len(modelHandle.locationXFrames) * 3 + len(modelHandle.rotationWFrames) * 4)
				currentFrames = 0
				for i in modelHandle.boneLocationXFrames:
					afx_utils.AddKeysList_Location(self.keyframeInterpolation, curves[7*i+8].keyframe_points, curves[7*i+9].keyframe_points, curves[7*i+10].keyframe_points, modelHandle.boneLocationXFrames[i], modelHandle.boneLocationYFrames[i], modelHandle.boneLocationZFrames[i])
					currentFrames += len(modelHandle.boneLocationXFrames[i]) * 3
				updateImportProgress(currentFrames)
				currentFrames = 0
				for i in modelHandle.boneRotationWFrames:
					afx_utils.AddKeysList_Rotation(self.keyframeInterpolation, curves[7*i+11].keyframe_points, curves[7*i+12].keyframe_points, curves[7*i+13].keyframe_points, curves[7*i+14].keyframe_points, modelHandle.boneRotationWFrames[i], modelHandle.boneRotationXFrames[i], modelHandle.boneRotationYFrames[i], modelHandle.boneRotationZFrames[i])
					currentFrames += len(modelHandle.boneRotationWFrames[i]) * 4
				updateImportProgress(currentFrames)
				for curve in curves:
					curve.update()
			if camData is not None:
				curves = camData.curves
				afx_utils.AddKeysList_Location(self.keyframeInterpolation, curves[0].keyframe_points, curves[1].keyframe_points, curves[2].keyframe_points, camData.locationXFrames, camData.locationYFrames, camData.locationZFrames)
				afx_utils.AddKeysList_Rotation(self.keyframeInterpolation, curves[3].keyframe_points, curves[4].keyframe_points, curves[5].keyframe_points, curves[6].keyframe_points, camData.rotationWFrames, camData.rotationXFrames, camData.rotationYFrames, camData.rotationZFrames)
				afx_utils.AddKeysList_Value(self.keyframeInterpolation, curves[7].keyframe_points, camData.lensFrames)
				updateImportProgress(len(camData.locationXFrames) * 3 + len(camData.rotationWFrames) * 4 + len(camData.lensFrames))
				for curve in curves:
					curve.update()
			
			result['frameEnd'] = int(math.ceil(timeConverter.GetTime()))
			
			if 0 < timeConverter.errorCount:
				self.warning("FPS mismatch was detected %i times. The maximum error was %f. Solution: Make sure to set the Blender project FPS correctly before importing." % (timeConverter.errorCount, timeConverter.maxError))
			
			context.window_manager.progress_end()
			
		finally:
			if file is not None:
				file.close()
		
		result['result'] = True
		return result
