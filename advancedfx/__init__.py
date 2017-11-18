# Copyright (c) advancedfx.org
#
# Last changes:
# 2017-11-18 dominik.matrixstorm.com
#
# First changes:
# 2016-07-19 dominik.matrixstorm.com

import bpy

bl_info = {
	"name": "advancedfx Blender Scripts",
	"author": "Dominik Tugend",
	"version": (1, 4, 2),
	"blender": (2, 77, 0),
	"location": "File > Import/Export",
	"description": "Supports importing afxGameRecord (.agr) and importing/exporting HLAE Camera Motion (.bvh) files.",
	#"warning": "",
	#"wiki_url": "",
	#"tracker_url": "",
	"category": "Import-Export",
}

from . import utils, import_agr, import_bvh, export_bvh

def menu_func_import_agr(self, context):
	self.layout.operator(import_agr.AgrImporter.bl_idname, text="HLAE afxGameRecord (.agr)")

def menu_func_import_bvh(self, context):
	self.layout.operator(import_bvh.BvhImporter.bl_idname, text="HLAE camera motion data (.bvh)")

def menu_func_export_bvh(self, context):
	self.layout.operator(export_bvh.BvhExporter.bl_idname, text="HLAE camera motion data (.bvh)")

def register():
	#bpy.utils.register_module(__name__)
	bpy.utils.register_class(import_agr.AgrImporter)
	bpy.types.INFO_MT_file_import.append(menu_func_import_agr)
	bpy.utils.register_class(import_bvh.BvhImporter)
	bpy.types.INFO_MT_file_import.append(menu_func_import_bvh)
	bpy.utils.register_class(export_bvh.BvhExporter)
	bpy.types.INFO_MT_file_export.append(menu_func_export_bvh)

def unregister():
	bpy.types.INFO_MT_file_export.remove(menu_func_export_bvh)
	bpy.utils.unregister_class(export_bvh.BvhExporter)
	bpy.types.INFO_MT_file_import.remove(menu_func_import_bvh)
	bpy.utils.unregister_class(import_bvh.BvhImporter)
	bpy.types.INFO_MT_file_import.remove(menu_func_import_agr)
	bpy.utils.unregister_class(import_agr.AgrImporter)
	#bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
	unregister()
	register()