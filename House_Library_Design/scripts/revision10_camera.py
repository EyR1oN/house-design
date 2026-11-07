from pathlib import Path
import bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
o=bpy.data.objects['R3_CAMERA_LAUNDRY_REVERSE'];o.location=(8.50,2.68,1.50);o.rotation_euler=(Vector((9.50,3.35,1.50))-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=14
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
print('BOILER_VIEW_CAMERA_UPDATED')
