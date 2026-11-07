from pathlib import Path
import bpy,json,shutil,math
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];backup=R.parent/'House_Library_Revision15_Backup';assert not backup.exists(),'Do not repeat revision16'
backup.mkdir()
for n in ['House_Library_Design.blend','README.md','Design_Gallery.html']:shutil.copy2(R/n,backup/n)
for n in ['data','previews']:shutil.copytree(R/n,backup/n)
shutil.copy2(R.parent/'HOUSE_HANDOFF_UK.md',backup/'HOUSE_HANDOFF_UK.md')
for n in ['House_Viewer.html','House_Floor_1.glb','House_Floor_2.glb']:shutil.copy2(R.parent/'House_Browser_Viewer'/n,backup/n)
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));old=json.loads((R/'data/revision3_report.json').read_text());oldDoors={d['id']:d for d in old['doors']};report={'revision':16,'removed_objects':[],'changed_objects':{'1':[],'2':[]},'doors':[],'color_objects':[]}
def layer(level):
 for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design'if level==1 else'Upper_Design']
 bpy.context.view_layer.update()
def bbox(obs):
 bpy.context.view_layer.update();v=[o.matrix_world@Vector(c)for o in obs for c in o.bound_box];return [[min(q[i]for q in v),max(q[i]for q in v)]for i in range(3)]
def rot(p,a):return Matrix.Translation(p)@Matrix.Rotation(math.radians(a),4,'Z')@Matrix.Translation(-p)
for did,level,reverse,angle,desc in [('L2_SIDE_BEDROOM_DOOR',2,True,90,'North jamb hinge; inward against bathroom-side wall'),('L2_FRONT_BEDROOM_DOOR',2,True,90,'East jamb hinge; inward against east room wall'),('STORAGE',1,False,-90,'South jamb hinge; outward toward living room')]:
 layer(level);row=next(r for r in p if r['label']=='Door_'+did);obs=[bpy.data.objects[n]for n in row['objects']];orig=oldDoors[did];pivot=Vector(orig['hinge']);undo=rot(pivot,-orig['angle_deg']);closed={o.name:undo@o.matrix_world if o.get('hinged_leaf')else o.matrix_world.copy()for o in obs};leaf=next(o for o in obs if 'Door.001' in o.get('source_object_name',''))
 points=[closed[leaf.name]@Vector(c)for c in leaf.bound_box]
 if reverse:
  axis=0 if did=='L2_FRONT_BEDROOM_DOOR'else 1;far=max(q[axis]for q in points);newpivot=pivot.copy();newpivot[axis]=far;mid=(pivot+newpivot)/2;flip=rot(mid,180)
  closed={n:flip@M for n,M in closed.items()};pivot=newpivot
 for o in obs:
  o.matrix_world=rot(pivot,angle)@closed[o.name] if o.get('hinged_leaf')else closed[o.name]
  o['door_hinge_world']=list(pivot);o['door_open_angle_deg']=angle;o['door_swing_description']=desc;report['changed_objects'][str(level)].append(o.name)
 row['bounds']=bbox(obs);row['door_hinge']=list(pivot);row['door_open_angle_deg']=angle
 report['doors'].append({'id':did,'level':level,'hinge':list(pivot),'angle_deg':angle,'description':desc,'moving':[o.name for o in obs if o.get('hinged_leaf')],'fixed':[o.name for o in obs if not o.get('hinged_leaf')],'closed_matrices':{o.name:[list(v)for v in closed[o.name]]for o in obs if o.get('hinged_leaf')}})
# Remove only the office floor plant.
row=next(r for r in p if r['label']=='Plant_Office');report['removed_objects']+=row['objects']
for n in row['objects']:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
p.remove(row)
# Reuse the exact material of the existing cupboard above the refrigerator.
layer(1);ref=next(r for r in p if r['label']=='Kitchen_Fridge_Upper_Storage');target=bpy.data.objects[ref['objects'][0]].data.materials[0];report['kitchen_finish_material']=target.name
for row in p:
 if row['label']not in ['Kitchen_Hood','Kitchen_Tall_Corner_Pantry']:continue
 for n in row['objects']:
  o=bpy.data.objects[n]
  if n.startswith('R15_Hood_Underside_Light'):continue
  changed=False
  for i,m in enumerate(o.data.materials):
   if m and m.name=='R7 Warm appliance enamel':o.data.materials[i]=target;changed=True
  if changed:report['color_objects'].append(n);report['changed_objects']['1'].append(n)
# Record entire pantry in export, retaining its existing motion metadata.
pantry=next(r for r in p if r['label']=='Kitchen_Tall_Corner_Pantry')
for n in pantry['objects']:
 if n not in report['changed_objects']['1']:report['changed_objects']['1'].append(n)
report['pantry_roles']=json.loads((R/'data/revision14_report.json').read_text())['motion_groups']
s['interior_revision']='LIBRARY 16.0 Wall-side upper doors, outward storage door and matching kitchen finish'
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');(R/'data/revision16_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
for floor,names in report['changed_objects'].items():
 layer(int(floor));bpy.ops.object.select_all(action='DESELECT')
 for n in names:bpy.data.objects[n].select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(R/'exports'/f'revision16_floor{floor}.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION16_SAVED',len(report['color_objects']),report['doors'])
