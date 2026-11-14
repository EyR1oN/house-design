import bpy
from mathutils import Vector
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
s=bpy.context.scene
for vl in s.view_layers: vl.use=vl.name=='Exterior'
bpy.context.window.view_layer=s.view_layers['Exterior']
for o in bpy.data.objects:
 if o.name.startswith('L_') and o.type in ('MESH','CURVE'):
  o.hide_render=True
for o in bpy.context.view_layer.objects:
 if o.type!='MESH': continue
 if not o.name.startswith(('R_', 'R30_', 'R3_Glazed_Door_Leaf_', 'LIB_Door_L1_ENTRY_DOOR')):
  o.hide_render=True
 if o.name.startswith('R_FOUNDATION') or o.name.endswith('_PAD'):
  o.hide_render=True
bpy.ops.mesh.primitive_plane_add(size=200, location=(8,5,-.483))
o=bpy.context.object
m=bpy.data.materials.new('Render ground')
m.diffuse_color=(.44,.45,.41,1)
o.data.materials.append(m)
s.render.engine='BLENDER_WORKBENCH'
s.display.shading.light='STUDIO'
s.display.shading.color_type='MATERIAL'
s.display.shading.show_shadows=False
s.display.shading.show_cavity=True
s.display.shading.cavity_type='BOTH'
s.display.shading.show_specular_highlight=True
s.display.shading.background_type='WORLD'
s.world.color=(.55,.55,.53)
s.view_settings.view_transform='Standard'
s.render.resolution_x=1450
s.render.resolution_y=1000
s.render.resolution_percentage=100
d=bpy.data.cameras.new('QA exterior')
cam=bpy.data.objects.new('QA exterior',d)
s.collection.objects.link(cam)
s.camera=cam
cam.data.type='ORTHO'
for name, pos, target, width in [
 ('Exterior_Entry',(19,-16,11),(8.9,4.8,4.55),20.5),
 ('Exterior_Balcony',(20,23,10),(9.0,7.0,4.55),19.7),
 ('Exterior_Detail',(15,-6,4.7),(10.1,1.0,1.95),7.6),
]:
 cam.location=pos
 cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
 d.ortho_scale=width
 s.render.filepath=str(PROJECT / 'previews' / (name+'.png'))
 bpy.ops.render.render(write_still=True)
