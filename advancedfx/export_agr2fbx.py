# Thanks to Darkhandrob for doing the base function
# https://github.com/darkhandrob

import bpy, bpy.props, bpy.ops, time

class AgrExport(bpy.types.Operator):
	"""Exports every models with its animation as a FBX"""
	bl_idname = "advancedfx.agr_to_fbx"
	bl_label = "HLAE afxGameRecord"
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}

	filepath: bpy.props.StringProperty(subtype="DIR_PATH")

	global_scale: bpy.props.FloatProperty(
		name="Scale",
		description="Scale everything by this value",
		min=0.000001, max=100000.0,
		soft_min=0.1, soft_max=10.0,
		default=1,
	)

	root_name: bpy.props.StringProperty(
		name="Root Bone Name",
		description="Set the root bone name for each model",
		default="root",
	)

	skip_meshes: bpy.props.BoolProperty(
		name="Skip Meshes",
		description="Skips mesh export for faster export",
		default=True,
	)

	def menu_draw_export(self, context):
		layout = self.layout
		layout.operator("advancedfx.agr_to_fbx", text="HLAE afxGameRecord")

	def invoke(self, context, event):
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

	def execute(self, context):
		time_start = time.time()
		# Change Filepath, if something got insert in the File Name box
		if not self.filepath.endswith("\\"):
			self.filepath = self.filepath.rsplit(sep="\\", maxsplit=1)[0] + "\\"

		# export model
		bpy.ops.object.select_all(action='DESELECT')
		for CurrentModel in bpy.data.objects:
			if CurrentModel.name.find("afx.") != -1:
				for o in context.scene.objects:
					if o.name == CurrentModel.name:
         				# select root
						CurrentModel.select_set(1)
						# select childrens
						for CurrentChildren in CurrentModel.children:
							CurrentChildren.select_set(1)
						# rename top to root
						CurrentObjectName = CurrentModel.name
						CurrentModel.name = self.root_name
						# export single objects as fbx
						fullfiles = self.filepath + "/" + CurrentObjectName + ".fbx"
						if self.skip_meshes:
							bpy.ops.export_scene.fbx(
								filepath = fullfiles, 
								object_types={'ARMATURE'}, 
								use_selection = True, 
								global_scale =  self.global_scale, 
								bake_anim_use_nla_strips = False, 
								bake_anim_use_all_actions = False, 
								bake_anim_simplify_factor = 0,
								add_leaf_bones=False)
						else:
							bpy.ops.export_scene.fbx(
								filepath = fullfiles,
								object_types={'ARMATURE', 'MESH'},
								use_selection = True,
								global_scale =  self.global_scale, 
								bake_anim_use_nla_strips = False, 
								bake_anim_use_all_actions = False, 
								bake_anim_simplify_factor = 0,
								add_leaf_bones=False)
						# undo all changes
						CurrentModel.name = CurrentObjectName
						CurrentModel.select_set(0)
						for CurrentChildren in CurrentModel.children:
							CurrentChildren.select_set(0)

		# export camera
		for CameraData in bpy.data.objects:
			if any(CameraData.name.startswith(c) for c in ("afxCam", "camera")):
				# select camera
				CameraData.select_set(1)
				# scale camera
				bpy.ops.transform.resize(value=(0.01, 0.01, 0.01))
				# export single cameras as fbx
				fullfiles = self.filepath + "/" + CameraData.name + ".fbx"
				bpy.ops.export_scene.fbx(
					filepath = fullfiles, 
					object_types={'CAMERA'}, 
					use_selection = True, 
					global_scale =  self.global_scale, 
					bake_anim_use_nla_strips = False, 
					bake_anim_use_all_actions = False, 
					bake_anim_simplify_factor = 0)
				# undo all changes
				bpy.ops.transform.resize(value=(100, 100, 100))
				CameraData.select_set(0)

		print("FBX-Export script finished in %.4f sec." % (time.time() - time_start))
		return {'FINISHED'}
