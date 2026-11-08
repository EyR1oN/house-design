"""Place the dining group in the east corner requested by the owner."""
from pathlib import Path
import bpy,json,math
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene;bpy.context.window.view_layer=s.view_layers['Ground_Design'];bpy.context.view_layer.update()
report=json.loads((R/'data/revision18_report.json').read_text())
if report.get('dining_corner_corrected'):raise RuntimeError('Dining correction already applied')
p=json.loads((R/'data/placements.json').read_text())
removed=[]
for r in list(p):
 if r['label']=='Dining_Chair_8.99':
  for n in r['objects']:
   removed.append(n);bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
  p.remove(r)
moved=[n for n in report['moved_objects'] if n not in removed]
for n in moved:
 o=bpy.data.objects[n];o.matrix_world=Matrix.Translation((1.96,-.21,0))@o.matrix_world
for o in bpy.data.objects:
 if o.type=='LIGHT' and 'dining' in o.name.lower():o.location.x+=1.96;o.location.y-=.21
bpy.context.view_layer.update()
record=next(r for r in p if r['label']=='Dining_Chair_7.99')
objects=[bpy.data.objects[n] for n in record['objects']]
points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
center=Vector(((min(v.x for v in points)+max(v.x for v in points))/2,(min(v.y for v in points)+max(v.y for v in points))/2,0))
T=Matrix.Translation(Vector((8.53,7.91,0)))@Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Translation(-center)
for o in objects:o.matrix_world=T@o.matrix_world
bpy.context.view_layer.update()
for r in p:
 if not r['label'].startswith(('Dining','Pendant_Dining')):continue
 pts=[bpy.data.objects[n].matrix_world@Vector(v) for n in r['objects'] for v in bpy.data.objects[n].bound_box]
 r['bounds']=[[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)]
report.update(dining_shift_m=[1.11,-.21,0],moved_objects=moved,removed_objects=removed,dining_corner_corrected=True,dining_table_bounds_m=[[8.82,10.38],[7.51,8.31]],dining_chairs=3)
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');(R/'data/revision18_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.object.select_all(action='DESELECT')
for name in moved+report['stair_objects']+['R18_Ceiling_L1']:
 o=bpy.data.objects[name];o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision18_floor1.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
print('DINING_CORNER_CORRECTED',json.dumps(report['dining_table_bounds_m']))
