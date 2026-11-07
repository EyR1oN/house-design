from pathlib import Path
import bpy,json
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));r=next(q for q in p if q['label']=='Laundry_Shallow_Pantry');ratio=.58/.64
for n in r['objects']:
 o=bpy.data.objects[n];o.location.x=8.49+(o.location.x-8.49)*ratio
 if o.type=='MESH' and not n.startswith('R11_Preserves'):o.scale.x*=ratio
bpy.context.view_layer.update();vs=[bpy.data.objects[n].matrix_world@Vector(v) for n in r['objects'] for v in bpy.data.objects[n].bound_box];r['bounds']=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');report=json.loads((R/'data/revision11_report.json').read_text(encoding='utf8'));report['pantry_cabinet_size_m']=[.58,.25,2.59];report['appliance_door_sweep_extra_gap_m']=.065
(R/'data/revision11_report.json').write_text(json.dumps(report,indent=2),encoding='utf8');bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
names=set(report['new_objects']+report['changed_objects'])
for c in bpy.data.objects['E1_022_SOCKET'].users_collection:names.update(o.name for o in c.all_objects if o.type=='MESH')
for n in names:
 o=bpy.data.objects[n]
 if o.name in bpy.context.view_layer.objects and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision11_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
for path in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 t=path.read_text(encoding='utf8').replace('640 × 250 × 2590','580 × 250 × 2590').replace('лише 5 мм','65 мм');path.write_text(t,encoding='utf8')
print('PANTRY_CLEARANCE_IMPROVED')
