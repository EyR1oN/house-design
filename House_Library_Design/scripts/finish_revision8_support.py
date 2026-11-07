from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
bpy.data.objects['R8_Potato_Sack'].location.z-=.011;bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
r=json.loads((R/'data/revision8_report.json').read_text());bpy.ops.object.select_all(action='DESELECT')
for n in r['new_objects']:bpy.data.objects[n].select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision8_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
