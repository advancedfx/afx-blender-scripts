Installation:

You need to install Blender Source Tools first
( http://steamreview.org/BlenderSourceTools/ ), since we depend on it.
This version of afx-blender-scripts was built using Blender Source Tools 2.7.1.

If you have a previous version of afx-blender-scripts installed, uninstall
it first through Blender!

afx-blender-scripts is installed like the Blender Source Tools are.

Of course when using AGR import you need the decompiled(player) models
in a folder structure like it is in CS:GO's pak01_dir.pak
(We recommend http://steamcommunity.com/groups/CrowbarTool ).



Known problems:

Using the AGR Import menu entry causes the Blender Source Tools import menu
entry not to function anymore until you restart Blender!



Usage:

The scripts can be accessed through the entries in the import menu
(AGR and BVH import) and export menu (BVH export).

Don't forget to enter the "Asset Path" when using AGR import, it needs to be
the full path to the folder structure with the decompiled models.

Notice:
The interpolation of the curves for the rotations are set to CONSTANT, because
Blender doesn't support proper interpolation of curves for quaternions yet.



Changelog:

1.3.0 (2017-09-12T12:00Z):
- Updated HLAE AGR Import to agr version 3

1.2.0 (2017-08-03T12:00Z):
- Updated HLAE AGR Import to agr version 2 (also bug fixes)

1.1.0 (2017-06-25T20:02Z):
- Updated HLAE AGR Import to agr version 1

1.0.2 (2016-12-14T12:36Z):
- Fixed HLAE AGR Import so now it will always take the shortest path for Euler based
  rotation of the models between two keyframes.

1.0.1 (2016-08-10T12:48Z):
- Fixed HLAE AGR Import failing when missing model was marked as deleted in
  AGR (should now report the missing model(s) instead as intended)

1.0.0 (2016-08-09T16:17Z):
- Added HLAE BVH Import
- Added HLAE BVH Export

0.0.1 (2016-07-27T20:39Z):
- First version
- Added HLAE AGR Import