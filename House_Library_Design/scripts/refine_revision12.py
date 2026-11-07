from pathlib import Path
import bpy,json,shutil,math
from mathutils import Vector
R=Path(__file__).resolve().parents[1];backup=R.parent/'House_Library_Revision11_Backup'
assert not backup.exists(),'Do not reapply revision 12'
backup.mkdir()
for n in ['House_Library_Design.blend','README.md']:shutil.copy2(R/n,backup/n)
for n in ['data','previews']:shutil.copytree(R/n,backup/n)
shutil.copy2(R.parent/'HOUSE_HANDOFF_UK.md',backup/'HOUSE_HANDOFF_UK.md');shutil.copy2(R.parent/'House_Browser_Viewer/House_Viewer.html',backup/'House_Viewer.html')
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Upper_Design']
bpy.context.view_layer.update();p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));new=[];removed=['LIB_Bedroom_Makeup_Vanity','LIB_Bedroom_Wall_Makeup_Mirror','LIB_Bedroom_Vanity_Chair']
def rec(l):return next(r for r in p if r['label']==l)
def bb(os):
 bpy.context.view_layer.update();v=[o.matrix_world@Vector(c) for o in os for c in o.bound_box];return [[min(c[i] for c in v),max(c[i] for c in v)] for i in range(3)]
vr=rec('Bedroom_Makeup_Vanity');mr=rec('Bedroom_Wall_Makeup_Mirror');cr=rec('Bedroom_Vanity_Chair');group=bpy.data.objects[vr['objects'][0]].users_collection[0]
for n in list(vr['objects']):
 if n.endswith(('Plane.005_PREPARED','Circle_PREPARED')):removed.append(n);bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True);vr['objects'].remove(n)
for n in mr['objects']:removed.append(n);bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
taupe=bpy.data.materials['R7 Warm greige cabinet'];wood=bpy.data.materials['Simple wood.001'];metal=bpy.data.materials['R7 Brushed warm metal']
def link(o):
 for c in list(o.users_collection):c.objects.unlink(o)
 group.objects.link(o);o['design_status']='PROPOSED_INTERIOR';o['level']=2;new.append(o);return o
def box(n,c,size,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=link(bpy.context.object);o.name='R12_'+n;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);mod=o.modifiers.new('Soft edges','BEVEL');mod.width=min(.003,min(size)/3);mod.segments=3;return o
cab=[]
for k,y in enumerate([10.845,11.645]):
 cab.append(box('Vanity_Plinth_'+str(k),(6.85,y,3.235),(.29,.19,.07),wood))
 for yy in [y-.101,y+.101]:cab.append(box('Vanity_Side_'+str(k)+'_'+str(yy),(6.85,yy,3.58),(.32,.018,.64),taupe))
 cab.append(box('Vanity_Back_'+str(k),(6.699,y,3.58),(.018,.184,.64),taupe))
 for z in [3.269,3.903]:cab.append(box('Vanity_Support_'+str(k)+'_'+str(z),(6.85,y,z),(.32,.22,.018),taupe))
 for j,z in enumerate([3.375,3.585,3.795]):
  cab.append(box('Vanity_Drawer_Base_'+str(k)+'_'+str(j),(6.851,y,z-.083),(.286,.176,.014),wood))
  for yy in [y-.092,y+.092]:cab.append(box('Vanity_Drawer_Side_'+str(k)+'_'+str(j)+'_'+str(yy),(6.851,yy,z),(.286,.012,.164),wood))
  cab.append(box('Vanity_Drawer_Back_'+str(k)+'_'+str(j),(6.712,y,z),(.012,.176,.164),wood))
  cab.append(box('Vanity_Drawer_Front_'+str(k)+'_'+str(j),(7.020,y,z),(.018,.214,.194),taupe))
  cab.append(box('Vanity_Drawer_Pull_'+str(k)+'_'+str(j),(7.038,y,z+.018),(.018,.105,.012),metal))
vr['objects'].extend(o.name for o in cab);vr['bounds']=bb([bpy.data.objects[n] for n in vr['objects']]);vr['custom_modification']='Original marble top retained; two 220mm drawer pedestals replace metal legs; six drawers'
# Mirror is a true circular mesh, not a scaled rectangular library mirror.
mirror=bpy.data.materials.new('R12 Polished makeup mirror');mirror.use_nodes=True;bs=mirror.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.80,.82,.84,1);bs.inputs['Metallic'].default_value=1;bs.inputs['Roughness'].default_value=.025
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.397,depth=.010,location=(6.653,11.245,4.68),rotation=(0,math.pi/2,0));o=link(bpy.context.object);o.name='R12_Round_Mirror_Glass';o.data.materials.append(mirror);mos=[o]
for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
bpy.ops.mesh.primitive_torus_add(major_segments=128,minor_segments=12,location=(6.659,11.245,4.68),rotation=(0,math.pi/2,0),major_radius=.400,minor_radius=.007);o=link(bpy.context.object);o.name='R12_Round_Mirror_Frame';o.data.materials.append(metal);mos.append(o)
for f in o.data.polygons:f.use_smooth=True
mr.update(role='round_makeup_mirror',objects=[o.name for o in mos],bounds=bb(mos),source_url='',license='PROJECT_CUSTOM');mr.pop('scale',None)
chair=[bpy.data.objects[n] for n in cr['objects']]
for o in chair:o.location.y+=.255
cr['bounds']=bb(chair)
checks={'six_drawers':len([o for o in cab if o.name.startswith('R12_Vanity_Drawer_Front')])==6,'knee_width_m':.58,'chair_side_margin_m':.04,'mirror_outer_diameter_m':.814,'table_depth_unchanged':abs(vr['bounds'][0][1]-7.115)<.001,'chair_clear_of_drawer_banks':cr['bounds'][1][0]>10.955 and cr['bounds'][1][1]<11.535}
assert checks['six_drawers'] and checks['table_depth_unchanged'] and checks['chair_clear_of_drawer_banks']
old=json.loads((backup/'data/placements.json').read_text(encoding='utf8'));labels={vr['label'],mr['label'],cr['label']};assert all(rec(r['label'])==r for r in old if r['label'] not in labels)
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');s['interior_revision']='LIBRARY 12.0 Bedroom round makeup mirror and six vanity drawers'
report={'revision':12,'removed_objects':removed,'new_objects':[o.name for o in new],'changed_labels':sorted(labels),'passed':True,'checks':checks,'other_placements_unchanged':True}
for name in ['revision12_report.json','revision12_verification.json','verification.json']:(R/'data'/name).write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True);bpy.ops.object.select_all(action='DESELECT')
export=[bpy.data.objects[n] for n in vr['objects']]+mos+chair
for o in export:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision12_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION12_SAVED_AND_VERIFIED',checks)
