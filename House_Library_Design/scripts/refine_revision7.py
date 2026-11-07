from pathlib import Path
import bpy,json,math,random
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text());changed=[];removed=[]
def rec(l):return next(r for r in p if r['label']==l)
def obs(l):return [bpy.data.objects[n] for n in rec(l)['objects']]
def bb(os):
 bpy.context.view_layer.update();vs=[o.matrix_world@Vector(v) for o in os for v in o.bound_box];return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
def fit(l,c,size,rot=0):
 os=obs(l);b=bb(os);mid=Vector([sum(v)/2 for v in b]);T=Matrix.Translation(mid)@Matrix.Rotation(rot,4,'Z')@Matrix.Translation(-mid)
 for o in os:o.matrix_world=T@o.matrix_world
 b=bb(os);T=Matrix.Translation(Vector(c))@Matrix.Diagonal((*[size[i]/(b[i][1]-b[i][0]) for i in range(3)],1))@Matrix.Translation(Vector([-sum(v)/2 for v in b]))
 for o in os:o.matrix_world=T@o.matrix_world
 changed.append(l)
def delete(l):
 global p
 for o in obs(l):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
 p=[r for r in p if r['label']!=l]
def mat(name,col,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;return m
plaster=bpy.data.materials['LIBRARY_PBR_Warm_Plaster'];stone=bpy.data.materials['LIBRARY_PBR_Warm_Stone'];white=mat('R7 Warm appliance enamel',(.86,.87,.85),.28);taupe=mat('R7 Warm greige cabinet',(.57,.55,.49),.6);dark=mat('R7 Graphite details',(.035,.043,.045),.35);brass=mat('R7 Brushed warm metal',(.34,.26,.15),.3,.8)
oak=mat('R7 Natural vertical oak',(.46,.28,.13),.48);nt=oak.node_tree;n=nt.nodes;tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=4;tex.inputs['Detail'].default_value=2;mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(3,28,.22);coord=n.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Generated'],mapping.inputs[0]);nt.links.new(mapping.outputs['Vector'],tex.inputs['Vector']);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.22,.12,.055,1);ramp.color_ramp.elements[1].color=(.50,.34,.17,1);nt.links.new(tex.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
def box(name,group,c,size,m,bevel=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.name=name
 for col in list(o.users_collection):col.objects.unlink(o)
 bpy.data.collections['DESIGN_'+group].objects.link(o);o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 if bevel:
  mod=o.modifiers.new('Soft edges','BEVEL');mod.width=min(bevel,min(size)/3);mod.segments=3
 o['design_status']='PROPOSED_INTERIOR';o['level']=1;return o
new_groups={}
def add(l,role,os,group):
 p.append({'label':l,'role':role,'group':group,'level':1,'source_url':'','license':'PROJECT_CUSTOM','objects':[o.name for o in os],'bounds':bb(os)});new_groups[l]=[o.name for o in os];return os
# TV: keep stair wall and both doorways intact; remove brown library cladding.
delete('Stair_Decorative_Panel')
back=box('R7_TV_Continuous_Plaster','Living_Dining',(6.628,9.745,1.45),(.016,2.13,2.90),plaster,.001)
slats=[box('R7_TV_Oak_Slat_%02d'%i,'Living_Dining',(6.663,10.355+i*.044,1.425),(.045,.024,2.79),oak,.003) for i in range(10)]
add('TV_Continuous_Wall_and_Oak_Slats','custom_tv_finish',[back]+slats,'Living_Dining')
# Island: preserve west/north edges, grow east and south; cabinet fronts remain east.
old_min=(7.98,5.91);sx=.70/.55;sy=1.30/1.10
T=Matrix.Translation(Vector((7.98,5.71,0)))@Matrix.Diagonal((sx,sy,1,1))@Matrix.Translation(Vector((-7.98,-5.91,0)))
for l in ['Kitchen_Crockery_6.185','Kitchen_Crockery_6.735']:
 for o in obs(l):o.matrix_world=T@o.matrix_world
 changed.append(l)
top=bpy.data.objects['Crockery_oak_top'];top.location=(8.33,6.36,.875);top.dimensions=(.735,1.335,.03)
# Re-plan laundry facing west / entrance.
delete('Laundry_Full_Upper_Storage');counter=bpy.data.objects.get('Laundry_counter')
if counter:removed.append(counter.name);bpy.data.objects.remove(counter,do_unlink=True)
fit('Laundry_Washer',(10.01,2.97,.44),(.65,.60,.84),-math.pi/2)
fit('Laundry_Dryer',(10.01,2.97,1.31),(.65,.60,.84),-math.pi/2)
kit=box('R7_Laundry_Stacking_Kit','Laundry',(10.01,2.97,.875),(.65,.60,.03),white);add('Laundry_Stacking_Kit','stacking_kit',[kit],'Laundry')
# A light framed tower with a storage cabinet above the dryer.
tower=[]
for y in [2.652,3.288]:tower.append(box('R7_Tower_Side_'+str(y),'Laundry',(10.025,y,1.165),(.67,.018,2.29),taupe))
tower.append(box('R7_Tower_Top','Laundry',(10.025,2.97,2.316),(.67,.654,.018),taupe))
# Upper closed cabinet clear of appliance controls.
for z in [1.795,2.30]:tower.append(box('R7_Tower_Upper_Shelf_'+str(z),'Laundry',(10.04,2.97,z),(.63,.61,.018),taupe))
tower.append(box('R7_Tower_Upper_Front','Laundry',(9.712,2.97,2.047),(.018,.606,.475),taupe));tower.append(box('R7_Tower_Upper_Pull','Laundry',(9.697,2.97,1.83),(.020,.20,.014),brass))
add('Laundry_Tower_Joinery','custom_laundry_joinery',tower,'Laundry')
# Ventilated pantry: three separate crates, potatoes and onions in different bins.
pantry=[];xmin,xmax=9.815,10.335;ymin,ymax=3.314,3.772
for y in [ymin,ymax]:pantry.append(box('R7_Pantry_Side_'+str(y),'Laundry',((xmin+xmax)/2,y,.505),(.52,.018,.99),taupe))
pantry.append(box('R7_Pantry_Back','Laundry',(10.326,3.543,.505),(.018,.44,.99),taupe));pantry.append(box('R7_Pantry_Worktop','Laundry',(10.075,3.543,1.015),(.55,.486,.03),stone))
for z in [.065,.35,.635,.92]:pantry.append(box('R7_Pantry_Shelf_'+str(z),'Laundry',(10.075,3.543,z),(.50,.44,.018),oak))
for k,z in enumerate([.205,.49,.775]):
 for j in range(6):pantry.append(box('R7_Ventilated_Drawer_%d_Slat_%d'%(k,j),'Laundry',(9.812,3.335+j*.083,z),(.025,.054,.235),oak,.002))
 pantry.append(box('R7_Pantry_Drawer_Pull_'+str(k),'Laundry',(9.786,3.543,z+.045),(.018,.19,.016),brass))
# Produce stays below the rims, visible through real ventilation gaps.
random.seed(7);potato=mat('R7 Potato skin',(.30,.20,.095),.85);onion=mat('R7 Onion skin',(.43,.27,.10),.8)
for k,z in enumerate([.11,.395]):
 for j in range(9):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=(9.89+random.random()*.31,3.37+random.random()*.32,z+.035));o=bpy.context.object;o.name='R7_Pantry_'+('Potato' if k==0 else 'Onion')+'_'+str(j)
  for col in list(o.users_collection):col.objects.unlink(o)
  bpy.data.collections['DESIGN_Laundry'].objects.link(o);o.scale=(.035,.027,.025) if k==0 else (.029,.029,.03);o.data.materials.append(potato if k==0 else onion);pantry.append(o)
add('Laundry_Ventilated_Pantry','custom_pantry',pantry,'Laundry')
fit('Laundry_Towels',(10.055,3.543,1.085),(.29,.28,.11))
# Generic wall-hung gas boiler planning envelope 440x352x720, service area open.
boiler=[];body=box('R7_Gas_Boiler_Body','Laundry',(10.198,3.54,1.84),(.352,.44,.72),white,.025);boiler.append(body)
boiler.append(box('R7_Boiler_Control_Panel','Laundry',(10.014,3.54,1.61),(.012,.30,.09),dark,.009));displaymat=mat('R7 Boiler display',(.05,.15,.17),.3);boiler.append(box('R7_Boiler_Display','Laundry',(10.006,3.54,1.617),(.003,.09,.042),displaymat,.002))
for yy in [3.43,3.65]:
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.017,depth=.016,location=(10.004,yy,1.61),rotation=(0,math.pi/2,0));o=bpy.context.object;o.name='R7_Boiler_Control_Knob_'+str(yy)
 for col in list(o.users_collection):col.objects.unlink(o)
 bpy.data.collections['DESIGN_Laundry'].objects.link(o);o.data.materials.append(white);boiler.append(o)
# Short connection indications only; no invented installed network/flue route.
for j,y in enumerate([3.39,3.465,3.54,3.615,3.69]):
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.009,depth=.18,location=(10.30,y,1.39));o=bpy.context.object;o.name='R7_Boiler_Proposed_Connector_'+str(j)
 for col in list(o.users_collection):col.objects.unlink(o)
 bpy.data.collections['DESIGN_Laundry'].objects.link(o);o.data.materials.append(brass);o['status']='PROPOSED_NOT_AS_BUILT';boiler.append(o)
bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.05,depth=.10,location=(10.24,3.54,2.25));o=bpy.context.object;o.name='R7_Boiler_Flue_Connection_Only'
for col in list(o.users_collection):col.objects.unlink(o)
bpy.data.collections['DESIGN_Laundry'].objects.link(o);o.data.materials.append(white);o['status']='CONNECTION_ONLY_ROUTE_NOT_DESIGNED';boiler.append(o)
add('Laundry_Gas_Boiler','generic_gas_boiler',boiler,'Laundry')
# Relocate accessible service sockets on north wall away from appliance backs.
e=json.loads((R/'data/electrical_points.json').read_text())
for id,newx,newz in [('E1_022_SOCKET',9.54,1.18),('E1_023_SOCKET',9.66,1.18)]:
 point=next(x for x in e if x['id']==id);d=Vector((newx-point['x_m'],0,newz-point['height_aff_m']))
 for o in bpy.data.objects:
  if o.name.startswith(id):o.location+=d
 point.update(x_m=newx,height_aff_m=newz,purpose=('Washer' if '022' in id else 'Dryer')+'; accessible beside stacked appliances, proposed')
(R/'data/electrical_points.json').write_text(json.dumps(e,indent=2))
pl=json.loads((R/'data/plumbing_fixture_points.json').read_text())
for point in pl:
 if point['id']=='P1_WASHER_WATER_DRAIN':point.update(x_m=10.34,y_m=3.22,height_aff_m=.55,status='PROPOSED_CONNECTION_POINT')
pl.append({'id':'P1_BOILER_CONNECTION_ZONE','room':'Laundry','level':1,'type':'BOILER_SERVICE_ZONE','x_m':10.30,'y_m':3.54,'height_aff_m':1.30,'status':'PROPOSED_ONLY_GAS_FLUE_CONDENSATE_ENGINEERING_REQUIRED'})
(R/'data/plumbing_fixture_points.json').write_text(json.dumps(pl,indent=2))
for r in p:
 if r['label'] in changed or r['label'] in new_groups:r['bounds']=bb(obs(r['label']))
(R/'data/placements.json').write_text(json.dumps(p,indent=2));s['interior_revision']='LIBRARY 7.0 TV oak slats, enlarged island, laundry pantry opposite entrance'
# Cameras must lie inside laundry, not in the source wall south of it.
for name,pos,target,lens in [('R3_CAMERA_LAUNDRY',(8.62,3.06,1.58),(10.06,3.20,1.30),19),('R3_CAMERA_LAUNDRY_REVERSE',(8.76,3.62,1.57),(10.08,3.15,1.23),19)]:
 o=bpy.data.objects[name];o.location=pos;o.rotation_euler=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler();o.data.lens=lens
(R/'data/revision7_report.json').write_text(json.dumps({'revision':7,'changed_placements':changed,'removed_objects':removed,'new_groups':new_groups,'island_body_m':[.70,1.30,.86],'island_top_m':[.735,1.335,.03],'boiler':'Generic planning envelope; not a selected installation or flue design','boiler_reference':'https://professional.vaillant.co.uk/downloads/product-manuals/ecotec-plus-1/ecotec-plus-combi-and-system-installation-instructions-2422739.pdf'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
# Browser replacement patch: changed ready models and full affected custom groups.
labels=changed+list(new_groups);export=[]
for label in labels:export.extend(obs(label))
for group in ['Kitchen','Laundry','Living_Dining']:
 export.extend(o for o in bpy.data.collections['DESIGN_'+group].objects if o.type=='MESH')
export.extend(o for o in bpy.data.objects if o.name.startswith(('E1_022_SOCKET','E1_023_SOCKET')) and o.type=='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in set(export):
 if o.name in bpy.context.view_layer.objects and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision7_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION7_SAVED',len(p),flush=True)
