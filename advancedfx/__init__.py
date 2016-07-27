# Copyright (c) advancedfx.org
#
# Last changes:
# 2016-07-27 dominik.matrixstorm.com
#
# First changes:
# 2016-07-19 dominik.matrixstorm.com

import bpy

bl_info = {
	"name": "advancedfx Blender Scripts",
	"author": "Dominik Tugend",
	"version": (0, 0, 1),
	"blender": (2, 77, 0),
	"location": "File > Import/Export",
	"description": "Supports importing afxGameRecord (.agr) and importing/exporting HLAE Camera Motion (.bvh) files.",
	#"warning": "",
	#"wiki_url": "",
	#"tracker_url": "",
	"category": "Import-Export",
}

from . import utils, import_agr

def menu_func_import_agr(self, context):
	self.layout.operator(import_agr.AgrImporter.bl_idname, text="HLAE afxGameRecord (.agr)")

def register():
	#bpy.utils.register_module(__name__)
	#bpy.utils.register_class(import_agr.SmdImporterEx)
	bpy.utils.register_class(import_agr.AgrImporter)
	bpy.types.INFO_MT_file_import.append(menu_func_import_agr)

def unregister():
	#bpy.utils.unregister_module(__name__)
	bpy.types.INFO_MT_file_import.remove(menu_func_import_agr)
	bpy.utils.unregister_class(import_agr.AgrImporter)
	#bpy.utils.unregister_class(import_agr.SmdImporterEx)

if __name__ == "__main__":
	unregister()
	register()