from pathlib import Path
import bpy,json,math
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text());removed=[]
def rec(l):return next(r for r in p if r['label']==l)
def obs(l):return [bpy.data.objects[n] for n in rec(l)['objects']]
def bb(os):
 bpy.context.view_layer.update();vs=[o.matrix_world@Vector(v) for o in os for v in o.bound_box];return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
def delete(l):
 global p
 for o in obs(l):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
 p=[r for r in p if r['label']!=l]
for l in ['Laundry_Bulk_Pantry','Laundry_Ventilated_Pantry','Laundry_Tower_Joinery']:delete(l)
# Move boiler from east wall to north wall, facing the clear room centre.
H=Matrix.Translation(Vector((9.26,3.61,1.84)))@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Translation(Vector((-10.198,-3.54,-1.84)))
for o in obs('Laundry_Gas_Boiler'):o.matrix_world=H@o.matrix_world
# Same east-wall appliance location; replace scattered joinery with one aligned run.
taupe=bpy.data.materials['R7 Warm greige cabinet'];oak=bpy.data.materials['R7 Natural vertical oak'];metal=bpy.data.materials['R7 Brushed warm metal'];group=bpy.data.collections['DESIGN_Laundry'];new=[]
def box(name,c,size,m,bevel=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.name='R9_'+name
 for col in list(o.users_collection):col.objects.unlink(o)
 group.objects.link(o);o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:mod=o.modifiers.new('Soft edges','BEVEL');mod.width=min(bevel,min(size)/3);mod.segments=3
 o['design_status']='PROPOSED_INTERIOR';o['level']=1;new.append(o);return o
# Appliance tower 654mm wide, pantry 460mm wide; both face west, backs east.
tower=[]
for y in [2.652,3.288]:tower.append(box('Tower_Side_'+str(y),(10.025,y,1.325),(.67,.018,2.59),taupe))
for z in [1.81,2.61]:tower.append(box('Tower_Upper_Shelf_'+str(z),(10.025,2.97,z),(.67,.654,.018),taupe))
tower.append(box('Tower_Upper_Front',(9.697,2.97,2.21),(.018,.614,.766),taupe));tower.append(box('Tower_Upper_Pull',(9.679,2.97,1.86),(.020,.20,.016),metal))
# Compact deep pantry obtains volume from depth, leaving the long side wall clear.
pantry=[]
for y in [3.331,3.773]:pantry.append(box('Pantry_Side_'+str(y),(10.015,y,1.325),(.65,.018,2.59),taupe))
pantry.append(box('Pantry_Back',(10.331,3.552,1.325),(.018,.424,2.59),taupe))
for z in [.105,.685,1.13,1.49,1.85,2.21,2.61]:pantry.append(box('Pantry_Shelf_'+str(z),(10.015,3.552,z),(.65,.46,.018),taupe))
# Split sliding upper fronts stay inside footprint and do not swing toward boiler.
for i,y in enumerate([3.441,3.663]):
 pantry.append(box('Pantry_Sliding_Front_'+str(i),(9.673+i*.021,y,1.874),(.018,.23,1.442),taupe))
 pantry.append(box('Pantry_Sliding_Pull_'+str(i),(9.653+i*.021,y+( .084 if i==0 else -.084),1.81),(.018,.012,.24),metal))
# Large lower potato pull-out and two independent middle vegetable bins.
pantry.append(box('Potato_Base',(10.015,3.552,.125),(.57,.42,.018),oak))
for y in [3.337,3.767]:pantry.append(box('Potato_Side_'+str(y),(10.015,y,.395),(.57,.012,.54),oak))
pantry.append(box('Potato_Back',(10.296,3.552,.395),(.012,.442,.54),oak))
for j in range(6):pantry.append(box('Potato_Vent_Front_'+str(j),(9.69,3.552,.17+j*.092),(.026,.432,.073),oak))
pantry.append(box('Potato_Pull',(9.665,3.552,.62),(.020,.20,.016),metal))
for k,y in enumerate([3.442,3.662]):
 pantry.append(box('Vegetable_Base_'+str(k),(10.015,y,.724),(.57,.198,.018),oak))
 for yy in [y-.102,y+.102]:pantry.append(box('Vegetable_Side_'+str(k)+'_'+str(yy),(10.015,yy,.903),(.57,.012,.35),oak))
 pantry.append(box('Vegetable_Back_'+str(k),(10.296,y,.903),(.012,.212,.35),oak))
 for j in range(4):pantry.append(box('Vegetable_Vent_Front_'+str(k)+'_'+str(j),(9.69,y,.768+j*.087),(.026,.207,.067),oak))
 pantry.append(box('Vegetable_Pull_'+str(k),(9.665,y,1.03),(.020,.14,.016),metal))
# A sack supported by the bin base.
bagmat=bpy.data.materials['R8 Jute sack'];bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(10.015,3.552,.389));o=bpy.context.object;o.name='R9_Potato_Sack';o.scale=(.235,.175,.255)
for col in list(o.users_collection):col.objects.unlink(o)
group.objects.link(o);o.data.materials.append(bagmat);new.append(o);pantry.append(o)
foods=[bpy.data.materials[n] for n in ['R8 Preserves tomatoes','R8 Preserves vegetables','R8 Preserves fruit']];lid=bpy.data.materials['R8 Jar lids']
for level,z in enumerate([1.139,1.499,1.859,2.219]):
 for row,x in enumerate([9.83,10.015,10.20]):
  for j,y in enumerate([3.40,3.55,3.70]):
   for suffix,radius,depth,zz,m in [('Jar',.049,.21,z+.105,foods[(j+level)%3]),('Lid',.05,.015,z+.2175,lid)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=depth,location=(x,y,zz));o=bpy.context.object;o.name='R9_Preserves_'+suffix+'_%d_%d_%d'%(level,row,j)
    for col in list(o.users_collection):col.objects.unlink(o)
    group.objects.link(o);o.data.materials.append(m);new.append(o);pantry.append(o)
# Towels now stored in cabinet above dryer, away from food storage.
os=obs('Laundry_Towels');b=bb(os);H=Matrix.Translation(Vector((10.01,2.97,1.874)))@Matrix.Translation(Vector([-sum(v)/2 for v in b]))
for o in os:o.matrix_world=H@o.matrix_world
for l,os,role in [('Laundry_Aligned_Tower',tower,'custom_laundry_joinery'),('Laundry_Deep_Pantry',pantry,'custom_deep_pantry')]:p.append({'label':l,'role':role,'group':'Laundry','level':1,'source_url':'','license':'PROJECT_CUSTOM','objects':[o.name for o in os],'bounds':bb(os)})
for l in ['Laundry_Gas_Boiler','Laundry_Towels']:rec(l)['bounds']=bb(obs(l))
# Accessible north-wall service sockets, clear of both the cabinets and boiler body.
e=json.loads((R/'data/electrical_points.json').read_text())
for id,x in [('E1_022_SOCKET',8.94),('E1_023_SOCKET',9.07)]:
 r=next(q for q in e if q['id']==id);d=Vector((x-r['x_m'],0,1.14-r['height_aff_m']))
 for o in bpy.data.objects:
  if o.name.startswith(id):o.location+=d
 r.update(x_m=x,height_aff_m=1.14,purpose=('Washer' if '022' in id else 'Dryer')+'; accessible north wall, proposed')
(R/'data/electrical_points.json').write_text(json.dumps(e,indent=2),encoding='utf8')
pl=json.loads((R/'data/plumbing_fixture_points.json').read_text())
for r in pl:
 if r['id']=='P1_BOILER_CONNECTION_ZONE':r.update(x_m=9.26,y_m=3.71,height_aff_m=1.30)
(R/'data/plumbing_fixture_points.json').write_text(json.dumps(pl,indent=2),encoding='utf8')
# Two views from the clear entrance; no lens positioned inside joinery.
for name,pos,target,lens in [('R3_CAMERA_LAUNDRY',(8.53,3.05,1.42),(10.05,3.21,1.30),14),('R3_CAMERA_LAUNDRY_REVERSE',(8.66,2.84,1.50),(9.73,3.41,1.30),15)]:
 o=bpy.data.objects[name];o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');s['interior_revision']='LIBRARY 9.0 Single end-wall laundry run, north-wall boiler, clear centre'
report={'revision':9,'removed_objects':removed,'new_objects':[o.name for o in new],'changed_labels':['Laundry_Gas_Boiler','Laundry_Towels'],'layout':'Appliance tower and deep pantry on east end wall; boiler north wall; long-side bulky cabinet removed','potato_bin_usable_m':[.558,.412,.54],'potato_bin_geometric_litres':.558*.412*.54*1000,'modelled_preserve_jars':36};(R/'data/revision9_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
# Re-export moved boiler, towels, full north-wall electrical collection and new joinery.
export=new+obs('Laundry_Gas_Boiler')+obs('Laundry_Towels')
for c in bpy.data.objects['E1_022_SOCKET'].users_collection:export.extend(o for o in c.all_objects if o.type=='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in set(export):
 if o.name in bpy.context.view_layer.objects and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision9_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False);print('REVISION9_SAVED')
