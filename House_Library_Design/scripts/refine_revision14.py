from pathlib import Path
import bpy,json,shutil,math
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];backup=R.parent/'House_Library_Revision13_Backup'
assert not backup.exists(),'Do not reapply revision 14'
backup.mkdir()
for n in ['House_Library_Design.blend','README.md']:shutil.copy2(R/n,backup/n)
for n in ['data','previews']:shutil.copytree(R/n,backup/n)
shutil.copy2(R.parent/'HOUSE_HANDOFF_UK.md',backup/'HOUSE_HANDOFF_UK.md');shutil.copy2(R.parent/'House_Browser_Viewer/House_Viewer.html',backup/'House_Viewer.html')
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));row=next(r for r in p if r['label']=='Kitchen_Tall_Corner_Pantry');old=json.loads((R/'data/revision13_report.json').read_text(encoding='utf8'));removed=list(row['objects']);kept=[];new=[]
keep=('R13_Pantry_Side_','R13_Pantry_Back','R13_Pantry_Fixed_Shelf_','R13_Pantry_Toe_Kick','R13_Pantry_Blind_Front','R13_Counter_Return_Filler')
for n in row['objects']:
 o=bpy.data.objects[n]
 if n.startswith(keep):kept.append(o);o['pantry_role']='fixed'
 else:bpy.data.objects.remove(o,do_unlink=True)
white=bpy.data.materials['R7 Warm appliance enamel'];oak=bpy.data.materials['R7 Natural vertical oak'];metal=bpy.data.materials['R7 Brushed warm metal'];dark=bpy.data.materials['R7 Graphite details'];group=bpy.data.collections['DESIGN_Kitchen']
bpy.data.objects['R13_Pantry_Back'].data.materials.clear();bpy.data.objects['R13_Pantry_Back'].data.materials.append(white)
roles={'fixed':[o.name for o in kept],'pivot':[]}
def link(o,n,m,role):
 o.name='R14_'+n
 for c in list(o.users_collection):c.objects.unlink(o)
 group.objects.link(o);o.data.materials.append(m);o['pantry_role']=role;o['level']=1;o['design_status']='PROPOSED_INTERIOR';new.append(o);roles[role].append(o.name);return o
def box(n,c,size,m,role='pivot',bevel=.003):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=link(bpy.context.object,n,m,role);o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:md=o.modifiers.new('Soft edges','BEVEL');md.width=min(bevel,min(size)/3);md.segments=3
 return o
# White outside face and oak back, sides and shelves: the door itself is a shallow bookcase.
box('Pivot_Outer_Face',(9.55,4.551,1.485),(.38,.018,2.73),white)
box('Pivot_Oak_Back',(9.55,4.532,1.445),(.35,.018,2.63),oak)
for x in [9.379,9.711]:box('Pivot_Oak_Side_'+str(x),(x,4.433,1.445),(.018,.18,2.63),oak)
levels=[.16,.59,1.02,1.45,1.88,2.31,2.74]
for i,z in enumerate(levels):
 box('Pivot_Oak_Shelf_'+str(i),(9.545,4.433,z),(.332,.18,.020),oak)
 if i<len(levels)-1:box('Pivot_Oak_Front_Lip_'+str(i),(9.545,4.352,z+.05),(.332,.018,.080),oak)
box('Pivot_Pull_Handle',(9.55,4.579,1.18),(.018,.025,.42),metal)
# Curved white shelves fill the corner behind the oak pivot module, with a recess for it.
outline=[(9.38,3.99),(10.36,3.99),(10.36,4.48),(9.79,4.48),(9.79,4.31),(9.38,4.31)]
def rounded(poly,r=.055):
 out=[]
 for i,point in enumerate(poly):
  p=Vector(point);a=Vector(poly[i-1])-p;b=Vector(poly[(i+1)%len(poly)])-p;dist=min(r,a.length*.35,b.length*.35);aa=p+a.normalized()*dist;bb=p+b.normalized()*dist
  for k in range(9):
   t=k/8;q=(1-t)**2*aa+2*(1-t)*t*p+t*t*bb;out.append(tuple(q))
 return out
poly=rounded(outline);N=len(poly)
for i,z in enumerate(levels):
 verts=[(x,y,z+dz) for dz in [-.010,.010] for x,y in poly];faces=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(j,(j+1)%N,(j+1)%N+N,j+N) for j in range(N)]
 me=bpy.data.meshes.new('R14_Rounded_Corner_Shelf_Mesh_'+str(i));me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Rounded',me);s.collection.objects.link(o);link(o,'Rounded_White_Corner_Shelf_'+str(i),white,'fixed')
 md=o.modifiers.new('Rounded shelf edges','BEVEL');md.width=.002;md.segments=3
# Compact articulated pivot/slide fittings, instead of the previous cargo runners.
for z in [.12,2.79]:
 box('Pivot_Fixed_Track_'+str(z),(9.735,4.37,z),(.025,.34,.022),dark,'fixed')
 box('Pivot_Moving_Hinge_'+str(z),(9.727,4.535,z),(.024,.028,.028),metal)
def bb(os):
 bpy.context.view_layer.update();v=[o.matrix_world@Vector(c) for o in os for c in o.bound_box];return [[min(c[i] for c in v),max(c[i] for c in v)] for i in range(3)]
row.update(objects=[o.name for o in kept+new],bounds=bb(kept+new),role='oak_pivot_bookcase_and_rounded_white_corner_shelves')
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');s['interior_revision']='LIBRARY 14.0 Reference-matched oak pivot shelving and curved white corner shelves'
report={'revision':14,'removed_objects':removed,'new_objects':[o.name for o in kept+new],'motion_groups':roles,'pivot_blender':[9.735,4.56,0],'slide_m':.22,'angle_radians':-math.pi/2,'layout':'Shallow oak shelf door moves slightly forward then pivots open; fixed rounded white corner shelves behind','reference':'User screenshot codex-clipboard-7b4c8832-192d-4d51-8240-e93d8690b74e.png','hardware_status':'Spatial design of articulated pivot-slide; final fittings and load rating require furniture maker verification'}
(R/'data/revision14_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
cam=bpy.data.objects['R13_CAMERA_PANTRY_OPEN'];cam.location=(8.15,5.90,1.48);cam.rotation_euler=(Vector((9.67,4.45,1.43))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=16
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in kept+new:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision14_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION14_SAVED',len(new),len(removed))
