from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
m=bpy.data.materials.get('R14 Warm walnut reference')
if m is None:
 m=bpy.data.materials['R7 Natural vertical oak'].copy();m.name='R14 Warm walnut reference'
 for n in m.node_tree.nodes:
  if n.type=='VALTORGB':n.color_ramp.elements[0].color=(.055,.025,.013,1);n.color_ramp.elements[1].color=(.18,.085,.04,1)
for o in bpy.data.objects:
 if o.name.startswith('R14_Pivot_Oak_'):o.data.materials.clear();o.data.materials.append(m)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True);r=json.loads((R/'data/revision14_report.json').read_text(encoding='utf8'));bpy.ops.object.select_all(action='DESELECT')
for n in r['new_objects']:bpy.data.objects[n].select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision14_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('WALNUT_FINISH_APPLIED')
