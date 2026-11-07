from pathlib import Path
import bpy,json
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text());changed=[]
for r in p:
 if r['label'].startswith(('Dining','Pendant_Dining')):
  changed.append(r['label'])
  for name in r['objects']:o=bpy.data.objects[name];o.matrix_world=Matrix.Translation(Vector((0,-.32,0)))@o.matrix_world
  bpy.context.view_layer.update();vs=[bpy.data.objects[name].matrix_world@Vector(v) for name in r['objects'] for v in bpy.data.objects[name].bound_box];r['bounds']=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
for o in bpy.data.objects:
 if o.type=='LIGHT' and 'dining' in o.name.lower():o.location.y-=.32
chair=next(r for r in p if r['label']=='Dining_Chair_7.99');island=bpy.data.objects['Crockery_oak_top'];island_edge=max((island.matrix_world@Vector(v)).y for v in island.bound_box);gap=chair['bounds'][1][0]-island_edge
assert .11<gap<.14,gap
old=json.loads((R.parent/'House_Library_Revision5_Backup/data/placements.json').read_text());cur={r['label']:r for r in p};assert all(cur[r['label']]['bounds']==r['bounds'] for r in old if r['label'] not in changed)
s['interior_revision']='LIBRARY 6.0 Dining group another 320mm toward island'
(R/'data/placements.json').write_text(json.dumps(p,indent=2));(R/'data/revision6_report.json').write_text(json.dumps({'revision':6,'additional_shift_m':.32,'chair_to_island_countertop_gap_m':gap,'changed_placements':changed,'checks_passed':True},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True);print('REVISION6_SAVED gap',gap)
