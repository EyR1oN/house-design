from pathlib import Path
import bpy,bmesh,json,math,shutil
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];backup=R.parent/'House_Library_Revision12_Backup'
assert not backup.exists(),'Revision 13 already started; do not reapply'
backup.mkdir()
for n in ['House_Library_Design.blend','README.md']:shutil.copy2(R/n,backup/n)
for n in ['data','previews']:shutil.copytree(R/n,backup/n)
shutil.copy2(R.parent/'HOUSE_HANDOFF_UK.md',backup/'HOUSE_HANDOFF_UK.md');shutil.copy2(R.parent/'House_Browser_Viewer/House_Viewer.html',backup/'House_Viewer.html')
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));new=[];changed=[];removed=[]
def rec(l):return next(r for r in p if r['label']==l)
def obs(l):return [bpy.data.objects[n] for n in rec(l)['objects']]
def bb(os):
 bpy.context.view_layer.update();v=[o.matrix_world@Vector(c) for o in os for c in o.bound_box];return [[min(c[i] for c in v),max(c[i] for c in v)] for i in range(3)]
def delete(l):
 global p
 removed.append('LIB_'+l)
 for o in obs(l):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
 p=[r for r in p if r['label']!=l]
delete('Kitchen_Corner_Prep');delete('Kitchen_Upper_Corner')
for n in ['Corner_stone_splash','Corner_east_splash','Corner_LED_strip']:
 o=bpy.data.objects.get(n)
 if o:removed.append(n);bpy.data.objects.remove(o,do_unlink=True)
# Preserve existing sink cut-out and rest of continuous counter; trim only its corner arm.
counter=bpy.data.objects['Kitchen_CONTINUOUS_L_WORKTOP'];bm=bmesh.new();bm.from_mesh(counter.data)
for v in bm.verts:v.co=counter.matrix_world@v.co
r=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,4.60,0),plane_no=(0,1,0),clear_inner=True)
edges=[e for e in r['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
bm.to_mesh(counter.data);bm.free();counter.matrix_world=Matrix.Identity(4);counter.data.update();changed.append(counter)
# Boards stay usable on the island rather than disappearing with the prep corner.
boards=obs('Kitchen_Cutting_Boards');bounds=bb(boards);delta=Vector((8.33-sum(bounds[0])/2,6.10-sum(bounds[1])/2,.892-bounds[2][0]))
for o in boards:o.location+=delta;changed.append(o)
rec('Kitchen_Cutting_Boards')['bounds']=bb(boards);removed.append('LIB_Kitchen_Cutting_Boards')
group=bpy.data.collections['DESIGN_Kitchen'];white=bpy.data.materials['R7 Warm appliance enamel'];oak=bpy.data.materials['R7 Natural vertical oak'];steel=bpy.data.materials['R7 Brushed warm metal'];dark=bpy.data.materials['R7 Graphite details'];stone=bpy.data.materials['LIBRARY_PBR_Warm_Stone']
roles={'fixed':[],'front':[],'rear':[]}
def link(o,n,m,role):
 o.name='R13_'+n
 for c in list(o.users_collection):c.objects.unlink(o)
 group.objects.link(o);o.data.materials.append(m);o['design_status']='PROPOSED_INTERIOR';o['level']=1;o['pantry_role']=role;roles[role].append(o.name);new.append(o);return o
def box(n,c,size,m,role='fixed',bevel=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=link(bpy.context.object,n,m,role);o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:mod=o.modifiers.new('Soft edges','BEVEL');mod.width=min(bevel,min(size)/3);mod.segments=3
 return o
# Same corner footprint, shortened by 60mm to clear the actual window sill at Y=4.56.
for x in [9.359,10.381]:box('Pantry_Side_'+str(x),(x,4.24,1.4875),(.018,.60,2.775),white)
box('Pantry_Back',(9.87,3.949,1.4875),(1.004,.018,2.775),oak)
for z in [.109,2.866]:box('Pantry_Fixed_Shelf_'+str(z),(9.87,4.24,z),(1.04,.60,.018),white)
box('Pantry_Toe_Kick',(9.87,4.24,.05),(1.00,.55,.10),white)
box('Pantry_Blind_Front',(10.065,4.531,1.4875),(.63,.018,2.775),white)
box('Counter_Return_Filler',(10.065,4.57,.8925),(.63,.06,.035),stone)
# Two matching front panels form a single pull-out door, not a hinged door into the oven.
for tag,z,h in [('Lower',1.08,1.92),('Upper',2.485,.75)]:box('Pantry_Pull_Front_'+tag,(9.55,4.553,z),(.38,.018,h),white,'front')
box('Pantry_Pull_Handle',(9.55,4.578,1.18),(.018,.025,.42),steel,'front')
foods=[]
for n,col in [('Dry rice',(.73,.65,.47)),('Pasta',(.72,.47,.20)),('Tea',(.20,.27,.17))]:
 m=bpy.data.materials.new('R13 '+n);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Roughness'].default_value=.55;foods.append(m)
# The front carrier rolls out first; rear carrier shifts left within the carcass, then approaches opening.
levels=[.18,.57,.96,1.35,1.74,2.13,2.52]
for role,cx in [('front',9.55),('rear',10.15)]:
 for x in [cx-.148,cx+.148]:box('Carrier_Post_'+role+'_'+str(x),(x,4.055,1.41),(.016,.018,2.55),dark,role)
 for i,z in enumerate(levels):
  box('Tray_Base_'+role+'_'+str(i),(cx,4.215,z),(.34,.36,.014),oak,role)
  for x in [cx-.164,cx+.164]:box('Tray_Side_'+role+'_'+str(i)+'_'+str(x),(x,4.215,z+.041),(.012,.36,.068),white,role)
  for y in [4.041,4.389]:box('Tray_Rail_'+role+'_'+str(i)+'_'+str(y),(cx,y,z+.041),(.316,.012,.068),white,role)
  for j,(dx,y) in enumerate([(-.085,4.125),(.085,4.125),(-.085,4.295),(.085,4.295)]):
   depth=.22 if (i+j)%3==0 else .18;radius=.045
   bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=radius,depth=depth,location=(cx+dx,y,z+.007+depth/2));o=link(bpy.context.object,'Food_Jar_'+role+'_%d_%d'%(i,j),foods[(i+j)%3],role)
   bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.046,depth=.014,location=(cx+dx,y,z+.007+depth+.007));link(bpy.context.object,'Food_Lid_'+role+'_%d_%d'%(i,j),white,role)
 # Telescoping guide elements visible when the cabinet is opened.
 for z in [.135,2.765]:
  box('Carrier_Guide_'+role+'_'+str(z),(cx,4.215,z),(.07,.40,.018),steel,role)
  box('Fixed_Guide_'+role+'_'+str(z),(cx,4.215,z-.024),(.085,.48,.018),dark)
# Horizontal guide for the rear carrier, behind its trays.
for z in [.13,2.755]:box('Rear_Transfer_Rail_'+str(z),(9.85,3.995,z),(.88,.026,.022),dark)
# Preserve sockets as accessible upper service points; remove the obsolete prep-corner light.
e=json.loads((R/'data/electrical_points.json').read_text(encoding='utf8'))
for id in ['E1_005_SOCKET','E1_006_SOCKET']:
 r=next(q for q in e if q['id']==id);delta=Vector((0,3.973-r['y_m'],2.79-r['height_aff_m']))
 for o in bpy.data.objects:
  if o.name.startswith(id):o.location+=delta
 r.update(y_m=3.973,height_aff_m=2.79,purpose='Proposed accessible upper service socket inside corner pantry')
e=[r for r in e if r['id']!='L1_053']
for o in list(bpy.data.objects):
 if o.name.startswith('L1_053'):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
(R/'data/electrical_points.json').write_text(json.dumps(e,indent=2),encoding='utf8')
p.append({'label':'Kitchen_Tall_Corner_Pantry','role':'custom_two_stage_corner_pantry','group':'Kitchen','level':1,'source_url':'','license':'PROJECT_CUSTOM','objects':[o.name for o in new],'bounds':bb(new)})
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');s['interior_revision']='LIBRARY 13.0 Tall corner pantry with sequential pull-out carriers'
report={'revision':13,'removed_objects':removed,'new_objects':[o.name for o in new],'changed_objects':[o.name for o in changed],'motion_groups':roles,'motions_blender':{'front':[0,.66,0],'rear':[-.60,.14,0]},'carcass_m':[1.04,.60,2.875],'shelf_levels_per_carrier':7,'jars':56,'hardware_status':'Custom spatial concept, not a certified catalogue mechanism; furniture maker must select compatible runners, load rating and mounting'}
(R/'data/revision13_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
cam=bpy.data.cameras.new('R13_CAMERA_PANTRY_OPEN');o=bpy.data.objects.new('R13_CAMERA_PANTRY_OPEN',cam);s.collection.objects.link(o);o.location=(8.80,6.60,1.48);o.rotation_euler=(Vector((9.65,4.43,1.43))-o.location).to_track_quat('-Z','Y').to_euler();cam.lens=17
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
export=new+changed
for c in bpy.data.objects['E1_005_SOCKET'].users_collection:export.extend(o for o in c.all_objects if o.type=='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in set(export):
 if o.name in bpy.context.view_layer.objects and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision13_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION13_SAVED',len(new),len(removed))
