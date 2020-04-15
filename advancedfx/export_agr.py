# Thanks to Darkhandrob for most of the code
# https://github.com/darkhandrob
#
#
#

import gc
import math
import os
import struct

import traceback

import bpy, bpy.props, bpy.ops,time
import mathutils

from io_scene_valvesource import import_smd as vs_import_smd, utils as vs_utils

from advancedfx import utils as afx_utils

class ExportAgr(bpy.types.Operator, vs_utils.Logger):
	"""Exports every models with its animation as a FBX"""   # blender will use this as a tooltip for menu items and buttons.
	bl_idname = "advancedfx.agr_to_fbx"		# unique identifier for buttons and menu items to reference.
	bl_label = "HLAE afxGameRecord"		# display name in the interface.
	bl_options = {'REGISTER', 'UNDO', 'PRESET'}  # enable undo and setting presets for the operator.
	
	# Properties used by the file browser
	filepath: bpy.props.StringProperty(subtype="DIR_PATH")
	
	global_scale: bpy.props.FloatProperty(
		name="Scale",
		description="Scale everything by this value (0.01 default, 0.0254 is more accurate)",
		min=0.000001, max=1000000.0,
		soft_min=0.001, soft_max=1.0,
		default=0.01,
	)

	root_name: bpy.props.StringProperty(
		name="Root Bone Name",
		description="Set the root bone name for each model",
		default="root",
	)
	
	def menu_draw_export(self, context):
		layout = self.layout
		layout.operator("advancedfx.agr_to_fbx", text="HLAE afxGameRecord")
	
	# Open the filebrowser with the custom properties
	def invoke(self, context, event):
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	# main function
	def execute(self, context):
		time_start = time.time()
		# Change Filepath, if something is inputted in the File Name Box
		if not self.filepath.endswith("\\"):
			self.filepath = self.filepath.rsplit(sep="\\", maxsplit=1)[0] + "\\"

		for CurrentModel in bpy.data.objects:
			if CurrentModel.name.find("afx.") != -1:
				# select root
				CurrentModel.select_set(1)
				# select childrens
				for CurrentChildren in CurrentModel.children:
					CurrentChildren.select_set(1)
				# rename top to root
				CurrentObjectName = CurrentModel.name
				CurrentModel.name = "root"
				# export single object as fbx
				fullfiles = self.filepath + "/" + CurrentObjectName + ".fbx"
				bpy.ops.export_scene.fbx(
					filepath = fullfiles, 
					use_selection = True, 
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
		if bpy.data.objects.find("afxCam") != -1:
			bpy.data.objects["afxCam"].select_set(1)
			fullfiles = self.filepath + "/afxcam.fbx"
			bpy.ops.export_scene.fbx(
				filepath = fullfiles, 
				use_selection = True, 
				bake_anim_use_nla_strips = False, 
				bake_anim_use_all_actions = False, 
				bake_anim_simplify_factor = 0,
				add_leaf_bones=False)
			bpy.data.objects["afxCam"].select_set(0)
					
		print(" ")
		print("FBX-Export script finished in %.4f sec." % (time.time() - time_start))
		return {'FINISHED'}
