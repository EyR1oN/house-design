from pathlib import Path
import bpy,json,shutil,math
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];backup=R.parent/'House_Library_Revision10_Backup'
assert not backup.exists(),'Do not apply revision 11 twice'
backup.mkdir()
for n in ['House_Library_Design.blend','README.md']:shutil.copy2(R/n,backup/n)
for n in ['data','previews']:shutil.copytree(R/n,backup/n)
shutil.copy2(R.parent/'HOUSE_HANDOFF_UK.md',backup/'HOUSE_HANDOFF_UK.md');shutil.copy2(R.parent/'House_Browser_Viewer/House_Viewer.html',backup/'House_Viewer.html')
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));removed=[];changed=[];new=[]
def rec(l):return next(r for r in p if r['label']==l)
def obs(l):return [bpy.data.objects[n] for n in rec(l)['objects']]
def bb(os):
 bpy.context.view_layer.update();v=[o.matrix_world@Vector(c) for o in os for c in o.bound_box];return [[min(c[i] for c in v),max(c[i] for c in v)] for i in range(3)]
for l in ['Laundry_Washer','Laundry_Dryer','Laundry_Stacking_Kit','Laundry_Aligned_Tower','Laundry_Towels']:
 for o in obs(l):o.location.y+=.48;changed.append(o)
 rec(l)['bounds']=bb(obs(l))
H=Matrix.Translation(Vector((10.198,2.88,1.95)))@Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Translation(Vector((-8.91,-3.61,-1.84)))
for o in obs('Laundry_Gas_Boiler'):o.matrix_world=H@o.matrix_world;changed.append(o)
rec('Laundry_Gas_Boiler')['bounds']=bb(obs('Laundry_Gas_Boiler'))
# Retain the deep vegetable bins, now under the boiler; remove previous tall pantry.
bins=[]
for o in obs('Laundry_Deep_Pantry'):
 if o.name.startswith(('R9_Potato','R9_Vegetable')):o.location.y-=.672;bins.append(o);changed.append(o)
 else:removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
p=[r for r in p if r['label']!='Laundry_Deep_Pantry']
taupe=bpy.data.materials['R7 Warm greige cabinet'];oak=bpy.data.materials['R7 Natural vertical oak'];metal=bpy.data.materials['R7 Brushed warm metal'];group=bpy.data.collections['DESIGN_Laundry']
def box(n,c,size,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.name='R11_'+n
 for col in list(o.users_collection):col.objects.unlink(o)
 group.objects.link(o);o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);mod=o.modifiers.new('Soft edges','BEVEL');mod.width=min(.003,min(size)/3);mod.segments=3;o['design_status']='PROPOSED_INTERIOR';new.append(o);return o
for y in [2.659,3.101]:bins.append(box('Boiler_Bin_Side_'+str(y),(10.015,y,.585),(.65,.018,1.11),taupe))
bins.append(box('Boiler_Bin_Back',(10.331,2.88,.585),(.018,.424,1.11),taupe))
for z in [.105,.685,1.13]:bins.append(box('Boiler_Bin_Shelf_'+str(z),(10.015,2.88,z),(.65,.46,.018),taupe))
# Side-wall pantry shortened to keep a conservative 550mm appliance door sweep clear.
pan=[]
for x in [8.499,9.121]:pan.append(box('Side_Pantry_Side_'+str(x),(x,3.66,1.325),(.018,.25,2.59),taupe))
pan.append(box('Side_Pantry_Back',(8.81,3.776,1.325),(.604,.018,2.59),taupe))
for z in [.105,.685,1.12,1.42,1.72,2.02,2.32,2.61]:pan.append(box('Side_Pantry_Shelf_'+str(z),(8.81,3.66,z),(.64,.25,.018),taupe))
for i,x in enumerate([8.65,8.96]):
 pan.append(box('Side_Pantry_Sliding_Front_'+str(i),(x,3.525-i*.021,1.876),(.312,.018,1.442),taupe))
 pan.append(box('Side_Pantry_Sliding_Pull_'+str(i),(x+(.095 if i==0 else -.095),3.509-i*.021,1.81),(.012,.018,.24),metal))
for k,(base,height) in enumerate([(.125,.54),(.724,.35)]):
 pan.append(box('Side_Vegetable_Base_'+str(k),(8.81,3.66,base),(.59,.198,.018),oak))
 for x in [8.515,9.105]:pan.append(box('Side_Vegetable_Side_'+str(k)+'_'+str(x),(x,3.66,base+.009+height/2),(.012,.21,height),oak))
 pan.append(box('Side_Vegetable_Back_'+str(k),(8.81,3.767,base+.009+height/2),(.602,.012,height),oak))
 count=6 if k==0 else 4
 for j in range(count):pan.append(box('Side_Vegetable_Vent_'+str(k)+'_'+str(j),(8.81,3.552,base+.05+j*.087),(.59,.026,.067),oak))
 pan.append(box('Side_Vegetable_Pull_'+str(k),(8.81,3.531,base+height-.02),(.20,.020,.016),metal))
foods=[bpy.data.materials[n] for n in ['R8 Preserves tomatoes','R8 Preserves vegetables','R8 Preserves fruit']];lid=bpy.data.materials['R8 Jar lids']
for level,z in enumerate([1.129,1.429,1.729,2.029,2.329]):
 for row,y in enumerate([3.60,3.72]):
  for j,x in enumerate([8.56,8.66,8.76,8.86,8.96,9.06]):
   for suffix,radius,depth,zz,m in [('Jar',.042,.21,z+.105,foods[(j+level)%3]),('Lid',.043,.015,z+.2175,lid)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=depth,location=(x,y,zz));o=bpy.context.object;o.name='R11_Preserves_'+suffix+'_%d_%d_%d'%(level,row,j)
    for col in list(o.users_collection):col.objects.unlink(o)
    group.objects.link(o);o.data.materials.append(m);new.append(o);pan.append(o)
for l,os,role in [('Laundry_Boiler_Low_Storage',bins,'custom_ventilated_bins'),('Laundry_Shallow_Pantry',pan,'custom_sidewall_pantry')]:p.append({'label':l,'role':role,'group':'Laundry','level':1,'source_url':'','license':'PROJECT_CUSTOM','objects':[o.name for o in os],'bounds':bb(os)})
# Sockets on exposed north-wall patch between pantry and appliance front, below jars.
e=json.loads((R/'data/electrical_points.json').read_text(encoding='utf8'))
for id,x in [('E1_022_SOCKET',9.28),('E1_023_SOCKET',9.43)]:
 r=next(q for q in e if q['id']==id)
 for o in bpy.data.objects:
  if o.name.startswith(id):o.location.x+=x-r['x_m']
 r['x_m']=x
(R/'data/electrical_points.json').write_text(json.dumps(e,indent=2),encoding='utf8')
pl=json.loads((R/'data/plumbing_fixture_points.json').read_text(encoding='utf8'))
for r in pl:
 if r['id']=='P1_BOILER_CONNECTION_ZONE':r.update(x_m=10.30,y_m=2.88,height_aff_m=1.41)
(R/'data/plumbing_fixture_points.json').write_text(json.dumps(pl,indent=2),encoding='utf8')
for name,pos,target,lens in [('R3_CAMERA_LAUNDRY',(8.53,3.00,1.42),(10.05,3.20,1.42),14),('R3_CAMERA_LAUNDRY_REVERSE',(8.53,2.72,1.50),(9.65,3.36,1.45),14)]:
 o=bpy.data.objects[name];o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');s['interior_revision']='LIBRARY 11.0 East-wall boiler right, appliance tower left, shallow sidewall pantry'
report={'revision':11,'removed_objects':removed,'changed_objects':[o.name for o in changed],'new_objects':[o.name for o in new],'modelled_preserve_jars':60,'pantry_cabinet_size_m':[.64,.25,2.59],'layout':'Boiler right and machines left facing entry; shallow north-wall pantry; deep bins under boiler','engineering':'Flue endpoint requested by user; actual compatible flue/vent and routes not verified'}
(R/'data/revision11_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
export=new+changed
for c in bpy.data.objects['E1_022_SOCKET'].users_collection:export.extend(o for o in c.all_objects if o.type=='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in set(export):
 if o.name in bpy.context.view_layer.objects and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision11_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION11_SAVED')
