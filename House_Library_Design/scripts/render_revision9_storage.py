from pathlib import Path
import bpy
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
for vl in s.view_layers:vl.use=vl.name=='Ground_Design'
def find(lc,n):
 if lc.name==n:return lc
 for c in lc.children:
  r=find(c,n)
  if r:return r
find(bpy.context.view_layer.layer_collection,'INTERIOR_RENDER_CEILINGS').exclude=False
for o in bpy.data.collections['INTERIOR_RENDER_CEILINGS'].objects:o.hide_render=not o.name.startswith('Render_ground')
for o in bpy.context.view_layer.objects:
 if o.type=='MESH' and (not o.name.startswith('R9_') or o.name.startswith(('R9_Tower','R9_Pantry_Sliding','R9_Potato_Vent_Front','R9_Potato_Pull','R9_Vegetable_Vent_Front','R9_Vegetable_Pull'))):o.hide_render=True
bpy.ops.mesh.primitive_cube_add(size=1,location=(9.0,3.5,-.015));floor=bpy.context.object;floor.name='PHOTO_ONLY_PANTRY_FLOOR';floor.scale=(4,4,.03);floor.data.materials.append(bpy.data.materials['LIBRARY_PBR_Warm_Plaster'])
camera=bpy.data.cameras.new('R8_PHOTO_ONLY_STORAGE_INTERIOR');o=bpy.data.objects.new('R8_PHOTO_ONLY_STORAGE_INTERIOR',camera);s.collection.objects.link(o);o.location=(8.2,3.552,1.34);o.rotation_euler=(Vector((10.01,3.552,1.34))-o.location).to_track_quat('-Z','Y').to_euler();camera.type='ORTHO';camera.ortho_scale=2.85;s.camera=o;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.view_settings.exposure=-.4;s.render.resolution_x=900;s.render.resolution_y=1400;s.render.resolution_percentage=100;s.render.filepath=str(R/'previews/Laundry_Storage.png');bpy.ops.render.render(write_still=True);print('R8_STORAGE_PHOTO_RENDERED')


