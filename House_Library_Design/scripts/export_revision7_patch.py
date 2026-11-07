from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text());report=json.loads((R/'data/revision7_report.json').read_text());labels=report['changed_placements']+list(report['new_groups']);os=[]
for r in p:
 if r['label'] in labels:os.extend(bpy.data.objects[n] for n in r['objects'])
for group in ['Kitchen','Laundry','Living_Dining']:os.extend(o for o in bpy.data.collections['DESIGN_'+group].objects if o.type=='MESH')
for col in bpy.data.objects['E1_022_SOCKET'].users_collection:
 print('ELECTRICAL_COLLECTION',col.name);os.extend(o for o in col.all_objects if o.type=='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in set(os):
 if o.name in bpy.context.view_layer.objects and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision7_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
