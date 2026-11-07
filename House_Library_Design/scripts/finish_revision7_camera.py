from pathlib import Path
import bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));o=bpy.data.objects['R3_CAMERA_LAUNDRY'];o.location=(8.53,3.08,1.40);o.rotation_euler=(Vector((10.05,3.19,1.20))-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=14;bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
