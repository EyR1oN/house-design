from pathlib import Path
import bpy,sys,os
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'House_Library_Design.blend'))
s=bpy.context.scene
def layer(n):
 for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers[n]
 for vl in s.view_layers:vl.use=vl.name==n
 bpy.context.view_layer.update()
def camera(n,pos,target,lens=21,ortho=None):
 o=bpy.data.objects.get(n)
 if o:return o
 d=bpy.data.cameras.new(n);o=bpy.data.objects.new(n,d);bpy.data.collections['QA_CAMERAS'].objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens
 if ortho:d.type='ORTHO';d.ortho_scale=ortho
 return o
cams={'Bedroom':camera('LIBRARY_CAMERA_BEDROOM',(7.60,11.24,4.91),(10.00,9.15,4.18)),
'Bedroom_TV':bpy.data.objects['INTERIOR5_BEDROOM_TV'],
'Bedroom_Desk':camera('LIBRARY_CAMERA_BEDROOM_DESK',(8.8,10.10,4.82),(7.08,11.25,4.04),26),
'Living':bpy.data.objects['INTERIOR5_LIVING'],
'Kitchen':camera('LIBRARY_CAMERA_KITCHEN',(8.85,7.30,1.72),(9.45,4.82,1.20),21),
'Office':camera('R3_CAMERA_OFFICE_INTERIOR',(10.28,5.25,4.84),(10.30,2.48,4.07),20),
'Upper_Bath':bpy.data.objects['INTERIOR4_UPPER_BATH'],
'Ground_Shower':bpy.data.objects['INTERIOR4_GROUND_SHOWER'],
'Wardrobe':camera('LIBRARY_CAMERA_WARDROBE',(6.80,5.60,4.85),(5.70,5.60,4.38),16),
'Ground_Plan':bpy.data.objects['DESIGN_CAMERA_PLAN'],
'Upper_Plan':bpy.data.objects['INTERIOR4_UPPER_PLAN']}
cams.update({
'Child':camera('R3_CAMERA_CHILD_CORNER',(7.11,3.60,4.80),(6.45,1.80,4.00),22),
'Child_Desk':camera('R3_CAMERA_CHILD_DESK',(6.60,3.95,4.80),(7.38,.72,4.04),22),
'Entry':camera('R3_CAMERA_ENTRY',(7.77,3.20,1.62),(6.42,1.25,1.16),20),
'Entry_Reverse':camera('R3_CAMERA_ENTRY_REVERSE',(6.15,.90,1.62),(7.60,3.42,1.16),20),
'Laundry':camera('R3_CAMERA_LAUNDRY',(8.65,2.20,1.62),(9.45,3.39,1.0),18),
'Kitchen_Reverse':camera('R3_CAMERA_KITCHEN_REVERSE',(9.66,4.80,1.67),(8.49,6.40,1.10),22),
'Living_TV':camera('R3_CAMERA_LIVING_TV',(9.73,10.89,1.65),(6.77,9.39,1.28),24),
'Living_Dining':camera('R3_CAMERA_LIVING_DINING',(7.42,11.45,1.66),(8.52,8.77,.98),23),
'Ground_Shower_Reverse':camera('R3_CAMERA_SHOWER_REVERSE',(5.97,6.63,1.61),(5.94,4.47,1.05),18),
'Upper_Hall':camera('R3_CAMERA_UPPER_HALL',(7.59,7.83,4.83),(7.51,4.75,4.22),20),
'Upper_Hall_Reverse':camera('R3_CAMERA_UPPER_HALL_REVERSE',(7.65,4.73,4.82),(7.52,7.78,4.20),20),
'Upper_Bath_Reverse':camera('R3_CAMERA_UPPER_BATH_REVERSE',(10.84,6.91,4.83),(9.65,5.67,4.17),20),
'Office_Reverse':camera('R3_CAMERA_OFFICE_REVERSE',(10.37,1.00,4.79),(10.16,3.84,4.00),21),
'Wardrobe_Reverse':camera('R3_CAMERA_WARDROBE_REVERSE',(6.75,5.41,4.76),(6.20,6.46,4.25),16)
})
cams.update({'Stair_Storage':camera('R3_CAMERA_STAIR_STORAGE',(6.25,8.34,1.55),(5.70,9.34,.98),17),'Stair_Top':camera('R3_CAMERA_STAIR_TOP',(6.02,7.74,4.81),(5.99,10.32,2.04),23)})
cams.update({'Laundry_Reverse':camera('R3_CAMERA_LAUNDRY_REVERSE',(10.07,2.84,1.62),(8.94,3.09,1.10),18),'Ground_Hall':camera('R3_CAMERA_GROUND_HALL',(7.65,6.66,1.62),(7.34,4.51,1.12),21),'Ground_Hall_Reverse':camera('R3_CAMERA_GROUND_HALL_REVERSE',(7.35,4.44,1.63),(7.48,6.82,1.16),21)})
cams['Stair_Entry']=camera('R4_CAMERA_STAIR_ENTRY',(7.66,11.12,1.58),(6.20,11.30,1.0),23)
cams['Child_Storage']=camera('R4_CAMERA_CHILD_STORAGE',(7.70,1.21,4.80),(6.30,3.70,4.32),21)
for key,pos,target,lens in [('Child',(7.94,3.60,4.82),(6.70,1.40,4.05),19),('Child_Desk',(5.97,2.98,4.80),(7.97,1.34,4.02),22)]:
 cams[key].location=pos;cams[key].rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler();cams[key].data.lens=lens
selection=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(cams)
s.render.resolution_x=800;s.render.resolution_y=665;s.render.resolution_percentage=100
for name in [n for n in selection if n.endswith('Plan')]:
 ly='Upper_Design' if name.startswith('Upper') else 'Ground_Design';layer(ly);s.camera=cams[name];s.render.engine='BLENDER_WORKBENCH';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=False;old=[];cap=4.3 if ly=='Upper_Design' else 1.1;wc='R_L2_WALLS' if ly=='Upper_Design' else 'R_L1_WALLS'
 for o in list(bpy.context.view_layer.objects):
  if o.type=='MESH' and any(c.name==wc for c in o.users_collection):
   if min((o.matrix_basis@v.co).z for v in o.data.vertices)>cap:o.hide_render=True;old.append((o,None));continue
   orig=o.data;o.data=orig.copy();old.append((o,orig))
   for v in o.data.vertices:
    if v.co.z>cap:v.co.z=cap
 s.render.filepath=str(ROOT/'previews/r7_draft'/f'{name}.png');bpy.ops.render.render(write_still=True)
 for o,me in old:
  if me:temp=o.data;o.data=me;bpy.data.meshes.remove(temp)
  else:o.hide_render=False
def find(lc,n):
 if lc.name==n:return lc
 for c in lc.children:
  a=find(c,n)
  if a:return a
ceiling=bpy.data.collections['INTERIOR_RENDER_CEILINGS']
s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;
if os.environ.get('HOUSE_RENDER_GPU')=='1':
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='ONEAPI';pref.get_devices()
 for d in pref.devices:d.use=d.type=='ONEAPI'
 s.cycles.device='GPU'
s.view_settings.exposure=-.40
for name in [n for n in selection if not n.endswith('Plan')]:
 ly='Ground_Design' if name in ['Stair_Storage','Stair_Entry'] or name.split('_')[0] in ['Living','Kitchen','Ground','Entry','Laundry','Storage'] else 'Upper_Design';layer(ly);s.camera=cams[name];find(bpy.context.view_layer.layer_collection,ceiling.name).exclude=False
 for o in ceiling.objects:o.hide_render=not (o.name.startswith('Render_ground') if ly=='Ground_Design' else not o.name.startswith('Render_ground'))
 bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');old_strength=bg.inputs['Strength'].default_value
 temporary_day=None
 if name.startswith('Child'):
  bg.inputs['Strength'].default_value=.8
  d=bpy.data.lights.new('PHOTO_ONLY_CHILD_DAYLIGHT','AREA');d.energy=220;d.color=(1,.94,.85);d.shape='RECTANGLE';d.size=1.40;d.size_y=1.0;temporary_day=bpy.data.objects.new('PHOTO_ONLY_CHILD_DAYLIGHT',d);s.collection.objects.link(temporary_day);temporary_day.location=(6.95,.45,5.0);temporary_day.rotation_euler=(Vector((6.85,2.45,4.0))-temporary_day.location).to_track_quat('-Z','Y').to_euler()
 s.render.filepath=str(ROOT/'previews/r7_draft'/f'{name}.png');bpy.ops.render.render(write_still=True);bg.inputs['Strength'].default_value=old_strength
 if temporary_day:bpy.data.objects.remove(temporary_day,do_unlink=True)
 find(bpy.context.view_layer.layer_collection,ceiling.name).exclude=True
 print('RENDERED_LIBRARY_VIEW',name,flush=True)
s.render.engine='BLENDER_EEVEE_NEXT';layer('Upper_Design');s.camera=bpy.data.objects['INTERIOR4_UPPER_OVERVIEW']

for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='SOLID';area.spaces.active.shading.use_scene_lights=False;area.spaces.active.shading.use_scene_world=False
if os.environ.get('HOUSE_RENDER_READONLY')!='1':bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'House_Library_Design.blend'),compress=True)

