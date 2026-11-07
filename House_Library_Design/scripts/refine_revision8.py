from pathlib import Path
import bpy,json,math
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text());removed=[]
for o in list(bpy.data.objects):
 if o.name.startswith('R7_TV_Oak_Slat_'):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
record=next(r for r in p if r['label']=='TV_Continuous_Wall_and_Oak_Slats');record['objects']=[n for n in record['objects'] if n not in removed];record['label']='TV_Continuous_Plain_Wall'
plaster=bpy.data.materials['LIBRARY_PBR_Warm_Plaster'];taupe=bpy.data.materials['R7 Warm greige cabinet'];oak=bpy.data.materials['R7 Natural vertical oak'];metal=bpy.data.materials['R7 Brushed warm metal'];group=bpy.data.collections['DESIGN_Laundry'];new=[]
def box(name,c,size,m,bevel=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.name='R8_'+name
 for col in list(o.users_collection):col.objects.unlink(o)
 group.objects.link(o);o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:mod=o.modifiers.new('Soft edges','BEVEL');mod.width=min(bevel,min(size)/3);mod.segments=3
 o['design_status']='PROPOSED_INTERIOR';o['level']=1;new.append(o);return o
# North wall: 960w x 400d x 2600h pantry, west of boiler service zone.
for x in [8.529,9.0,9.471]:box('Bulk_Pantry_Carcass_'+str(x),(x,3.585,1.325),(.018,.40,2.57),taupe)
box('Bulk_Pantry_Back',(9.0,3.777,1.325),(.924,.016,2.57),taupe)
for z in [.115,.825,1.175,1.525,1.875,2.225,2.61]:box('Bulk_Pantry_Shelf_'+str(z),(9.0,3.585,z),(.96,.38,.018),taupe)
box('Bulk_Pantry_Plith',(9.0,3.595,.06),(.90,.32,.10),taupe)
# Two closed upper doors protect preserved food from light.
for k,x in enumerate([8.764,9.236]):
 box('Bulk_Pantry_Upper_Door_'+str(k),(x,3.373,1.725),(.446,.022,1.756),taupe)
 box('Bulk_Pantry_Upper_Pull_'+str(k),(x+( .19 if k==0 else -.19),3.354,1.65),(.012,.018,.30),metal,.004)
# A full-height ventilated bin for a sack of potatoes, usable 420x330x630mm.
box('Potato_Bin_Base',(8.765,3.59,.135),(.43,.34,.018),oak)
for x in [8.547,8.983]:box('Potato_Bin_Side_'+str(x),(x,3.59,.47),(.012,.34,.65),oak)
box('Potato_Bin_Back',(8.765,3.758,.47),(.448,.012,.65),oak)
for j in range(7):box('Potato_Bin_Vent_Board_'+str(j),(8.764,3.372,.184+j*.092),(.448,.024,.071),oak)
box('Potato_Bin_Handle',(8.764,3.351,.725),(.19,.018,.019),metal)
# Right lower section: two separately ventilated drawers for onions/other vegetables.
for k,z in enumerate([.305,.655]):
 box('Vegetable_Drawer_Base_'+str(k),(9.235,3.59,z-.15),(.43,.34,.018),oak)
 for x in [9.017,9.453]:box('Vegetable_Drawer_Side_'+str(k)+'_'+str(x),(x,3.59,z),(.012,.34,.285),oak)
 box('Vegetable_Drawer_Back_'+str(k),(9.235,3.758,z),(.448,.012,.285),oak)
 for j in range(3):box('Vegetable_Drawer_Vent_'+str(k)+'_'+str(j),(9.236,3.372,z-.095+j*.095),(.448,.024,.072),oak)
 box('Vegetable_Drawer_Handle_'+str(k),(9.236,3.351,z+.10),(.19,.018,.019),metal)
# Model preserved jars on five usable upper levels; visible when doors are hidden in 3D.
def mat(name,col,rough=.5,metallic=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metallic;return m
foods=[mat('R8 Preserves tomatoes',(.23,.055,.025)),mat('R8 Preserves vegetables',(.10,.15,.045)),mat('R8 Preserves fruit',(.19,.075,.10))];lid=mat('R8 Jar lids',(.42,.40,.32),.3,.7)
for level,z in enumerate([.834,1.184,1.534,1.884,2.234]):
 for row,y in enumerate([3.48,3.66]):
  for j,x in enumerate([8.65,8.85,9.13,9.33]):
   for suffix,radius,depth,zz,m in [('Jar',.055,.21,z+.105,foods[(j+level)%3]),('Lid',.056,.015,z+.2175,lid)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=depth,location=(x,y,zz));o=bpy.context.object;o.name='R8_Preserve_'+suffix+'_%d_%d_%d'%(level,row,j)
    for col in list(o.users_collection):col.objects.unlink(o)
    group.objects.link(o);o.data.materials.append(m);new.append(o)
# Sack indicates the large bin's purpose without filling the walking space.
bagmat=mat('R8 Jute sack',(.29,.23,.14),.85);bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(8.765,3.59,.44));o=bpy.context.object;o.name='R8_Potato_Sack';o.scale=(.185,.145,.285)
for col in list(o.users_collection):col.objects.unlink(o)
group.objects.link(o);o.data.materials.append(bagmat);new.append(o)
def bb(os):
 bpy.context.view_layer.update();vs=[o.matrix_world@Vector(v) for o in os for v in o.bound_box];return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
record['bounds']=bb([bpy.data.objects[n] for n in record['objects']]);p.append({'label':'Laundry_Bulk_Pantry','role':'custom_bulk_pantry','group':'Laundry','level':1,'source_url':'','license':'PROJECT_CUSTOM','objects':[o.name for o in new],'bounds':bb(new)})
# Reverse camera was inside the new cabinet; move to the clear south side.
o=bpy.data.objects['R3_CAMERA_LAUNDRY_REVERSE'];o.location=(8.66,2.85,1.55);o.rotation_euler=(Vector((9.38,3.60,1.28))-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=15
s['interior_revision']='LIBRARY 8.0 Plain TV wall and bulk pantry storage';(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');report={'revision':8,'removed_objects':removed,'new_objects':[o.name for o in new],'cabinet_size_m':[.96,.40,2.60],'potato_bin_usable_m':[.42,.33,.63],'potato_bin_geometric_litres':.42*.33*.63*1000,'upper_shelf_levels':5,'modelled_preserved_jars':40,'capacity_note':'Geometric layout only; payload and shelf construction not specified'};(R/'data/revision8_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
# Patch only the new pantry; removed TV slats are deleted from browser root list.
bpy.ops.object.select_all(action='DESELECT')
for o in new:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision8_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False);print('REVISION8_SAVED')
