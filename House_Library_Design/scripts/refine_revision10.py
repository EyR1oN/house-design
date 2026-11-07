from pathlib import Path
import bpy,json,shutil
from mathutils import Vector
R=Path(__file__).resolve().parents[1];backup=R.parent/'House_Library_Revision9_Backup'
assert not backup.exists(),'Revision 10 already started; do not apply twice'
backup.mkdir()
for name in ['House_Library_Design.blend','README.md']:shutil.copy2(R/name,backup/name)
for name in ['data','previews']:shutil.copytree(R/name,backup/name)
shutil.copy2(R.parent/'HOUSE_HANDOFF_UK.md',backup/'HOUSE_HANDOFF_UK.md')
shutil.copy2(R.parent/'House_Browser_Viewer/House_Viewer.html',backup/'House_Viewer.html')
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));row=next(r for r in p if r['label']=='Laundry_Gas_Boiler');objects=[bpy.data.objects[n] for n in row['objects']]
for o in objects:o.location.x-=.35
e=json.loads((R/'data/electrical_points.json').read_text(encoding='utf8'))
for id,x in [('E1_022_SOCKET',9.38),('E1_023_SOCKET',9.51)]:
 r=next(q for q in e if q['id']==id)
 for o in bpy.data.objects:
  if o.name.startswith(id):o.location.x+=x-r['x_m']
 r['x_m']=x
(R/'data/electrical_points.json').write_text(json.dumps(e,indent=2),encoding='utf8')
pl=json.loads((R/'data/plumbing_fixture_points.json').read_text(encoding='utf8'))
for r in pl:
 if r['id']=='P1_BOILER_CONNECTION_ZONE':r['x_m']=8.91
(R/'data/plumbing_fixture_points.json').write_text(json.dumps(pl,indent=2),encoding='utf8')
bpy.context.view_layer.update()
def bb(os):
 v=[o.matrix_world@Vector(c) for o in os for c in o.bound_box];return [[min(c[i] for c in v),max(c[i] for c in v)] for i in range(3)]
row['bounds']=bb(objects);front=next(r for r in p if r['label']=='Laundry_Deep_Pantry')['bounds'][0][0];gap=front-row['bounds'][0][1]
assert gap>.51 and row['bounds'][0][0]>8.46 and row['bounds'][1][0]>2.603+.653
for id in ['E1_022_SOCKET','E1_023_SOCKET']:
 b=bb([bpy.data.objects[id]]);assert b[0][0]>row['bounds'][0][1] and b[0][1]<front
old=json.loads((backup/'data/placements.json').read_text(encoding='utf8'))
assert all(next(q for q in p if q['label']==r['label'])==r for r in old if r['label']!='Laundry_Gas_Boiler')
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');s['interior_revision']='LIBRARY 10.0 Boiler shifted 350 mm toward entrance'
report={'revision':10,'removed_objects':[],'boiler_shift_m':-.35,'boiler_side_gap_m':gap,'door_sweep_separation_m':row['bounds'][1][0]-(2.603+.653),'passed':True,'scope':'Model geometry and proposed positions; engineering routes unconfirmed'}
for name in ['revision10_report.json','revision10_verification.json','verification.json']:(R/'data'/name).write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
for c in bpy.data.objects['E1_022_SOCKET'].users_collection:objects.extend(o for o in c.all_objects if o.type=='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in set(objects):
 if o.name in bpy.context.view_layer.objects and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision10_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION10_VERIFIED_AND_SAVED',report)
