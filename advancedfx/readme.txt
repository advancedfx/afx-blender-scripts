Installation:

You need to install latest Blender Source Tools first
( http://steamreview.org/BlenderSourceTools/ ),
since we depend on it.
This version of afx-blender-scripts was tested using
Blender Source Tools 3.0.1.

If you have a previous version of afx-blender-scripts installed, uninstall
it first through Blender!

afx-blender-scripts is installed like the Blender Source Tools are.

Of course when using AGR import you need the decompiled(player) models
in a folder structure like it is in CS:GO's pak01_dir.pak
We recommend Crowbar ( http://steamcommunity.com/groups/CrowbarTool )
and YOU NEED TO TICK THE "Folder for each model" option in the Decompile
options!



Known problems:

Using the AGR Import menu entry causes the Blender Source Tools import menu
entry not to function anymore until you restart Blender!



Usage:

Always make sure to select the correct render properties in your project first
(FPS, resolution).

The scripts can be accessed through entries in the import menu and export menu.

"Add interpolated key frames" option:
Default is off (disabled).
This creates interpolated key frames for Blender frames in-between the original
key frames. This is useful in case your Blender project FPS doesn't match your
recorded FPS, because interpolation is set to constant between all keyframes
(see notice bellow for reason).
Of course this will add more data and take longer if that's the case when you
enable it.

Don't forget to enter the "Asset Path" when using AGR import, it needs to be
the full path to the folder structure with the decompiled models.
We recommend using Crowbar ( http://steamcommunity.com/groups/CrowbarTool )
and YOU NEED TO TICK THE "Folder for each model" option in the Decompile
options!

Notice:
The interpolation is set to CONSTANT for everything, because
Blender doesn't support proper interpolation of curves for quaternions yet.



Changelog:

1.9.4 (2020-01-03T14:04Z):
- Removed "Remove useless meshes" option (by Devostated)
- Added "Skip Physic Meshes" option, enabled by default (by Devostated)
- Removed irritating missing ?.qc Error (by Devostated)
- Test with Blender Source Tools 3.0.3.
- Test with Blender Source Tools 2.81a.

1.9.2 (2020-01-03T10:31Z):
- Added option for model instancing (faster), enabled by default.
- Test with Blender Source Tools 3.0.3.
- Test with Blender Source Tools 2.81a.

1.8.0 (2019-08-30T06:28Z):
- Added option "Remove useless meshes" (Removes Physics and smd_bone_vis for faster workflow.) (by Devostated).
- Added saving, loading and removing presets (by Devostated).
- Test with Blender Source Tools 3.0.1.

1.7.1.1 (2019-08-06T13:32Z):
- Changed back default scale to 0.01, even though 0.0254 is more accurate.

1.7.1 (2019-08-06T13:20Z):
- Minor changes

1.7.0 (2019-01-26T14:18Z):
- Updated to Blender 2.80 beta (needs latest Blender Source Tools 2.11.0b1-3251fc47b768116b91a8f5550166bc5ccb01efdf or newer ( https://github.com/Artfunkel/BlenderSourceTools/tree/master/io_scene_valvesource )).
- Fixed HLAE BVH Export exporting wrong rotation.

1.6.0 (2018-10-05T17:45Z):
- Update HLAE AGR Import:
  - Added option "Bones (skeleton) only", thanks to https://github.com/Darkhandrob

1.5.1 (2018-08-16T08:24Z):
- Update HLAE Camera IO (.cam) export:
  - Fixed it not working when camera object name did not match camera object data name

1.5.0 (2018-04-27T17:11Z):
- Added HLAE Camera IO (.cam) import
- Added HLAE Camera IO (.cam) export
- Update HLAE AGR Import:
  - Added option "Add interpolated key frames" (default off)
- Updated HLAE BVH Import:
  - Renamed to HLAE old Cam IO (.bvh) import
  - Added option "Add interpolated key frames" (default off)
  - Bug fixes
- Updated HLAE BVH Export:
  - Renamed to HLAE old Cam IO (.bvh) export
  - Bug fixes
- Tested with Blender Source Tools 2.10.2
- Please see updated usage note above regarding
  "Add interpolated key frames"

1.4.3 (2017-12-23T21:14Z):
- Updated HLAE AGR Import:
  Added option "Preserve SMD Polygons & Normals":
  Import raw (faster), disconnected polygons from SMD files;
  these are harder to edit but a closer match to the original mesh.
  (Enabled by default, much less time spent on importing models now.)

1.4.2 (2017-11-18T20:00Z):
- Updated HLAE AGR Import: Added option "Scale invisible to zero"
  to scale entities to 0 upon hide_render (might be useful for FBX export).
  This option creates drivers and modifiers on each entity,
  so no extra animation data.
  Please don't be scared if at frame 0 (default) everything is scaled to
  zero (not visible), this is because the animations start at frame 1.

1.4.1 (2017-11-01T18:53Z):
- Updated HLAE AGR Import: Now will only work with the "Folder for each model"
  Option in Crowbar. This is important to avoid naming collissions that can occur.
  In return this also works with the newest Crowbar version (currently 0.49.0).

1.4.0 (2017-09-16T22:00Z):
- Updated HLAE AGR Import to agr version 4 (also bug fixes)

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


MIT License

Copyright (c) 2019 advancedfx.org

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
