"""Remove the redundant metal guard inside the enclosed upstairs stair wall."""
from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene;bpy.context.window.view_layer=s.view_layers['Upper_Design'];bpy.context.view_layer.update()
removed=[]
for o in list(bpy.data.objects):
 if o.name.startswith('Upper_void_guard'):
  removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
report=json.loads((R/'data/revision18_report.json').read_text());report['removed_landing_guard_objects']=sorted(set(report.get('removed_landing_guard_objects',[])+removed))
hall=[o for o in bpy.data.collections['DESIGN_Upper_Hall'].objects if o.type=='MESH' and not o.hide_render]
report['hall_replacement_objects']=[o.name for o in hall]
bpy.ops.object.select_all(action='DESELECT')
for name in report['stair_objects']+['R18_Ceiling_L2']+report['hall_replacement_objects']:
 o=bpy.data.objects[name];o.hide_set(False);o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision18_floor2.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
(R/'data/revision18_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
print('REMOVED_LANDING_GUARD',removed,'HALL',report['hall_replacement_objects'])
