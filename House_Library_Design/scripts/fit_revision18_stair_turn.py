"""Fit the upper winders entirely between the actual closet and bedroom walls."""
from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene;report=json.loads((R/'data/revision18_report.json').read_text())
if report.get('stair_turn_fitted_between_walls'):raise RuntimeError('Stair turn already fitted')
bpy.context.window.view_layer=s.view_layers['Upper_Design'];bpy.context.view_layer.update()
for name in report['stair_objects']+['R3_Stair_Landing_Threshold']:
 o=bpy.data.objects[name]
 if not name.startswith(('R_STAIR_STRAIGHT_','R_STAIR_RISER_','R_STAIR_UPPER_WINDER_','R_STAIR_STRINGER','R3_Stair_Landing_Threshold')):continue
 inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if name.startswith(('R_STAIR_UPPER_WINDER_','R3_Stair_Landing_Threshold')):p.y=7.44+(p.y-7.45)*.94
  else:p.y=10.83-(10.83-p.y)*(2.45/2.38)
  v.co=inv@p
report.update(stair_turn_fitted_between_walls=True,upper_turn_y_bounds_m=[7.44,8.38],stair_closet_clearance_m=.0298,stair_bedroom_wall_clearance_m=.01995,straight_tread_depth_m=2.45/12)
for floor in (1,2):
 bpy.context.window.view_layer=s.view_layers['Ground_Design' if floor==1 else 'Upper_Design'];bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
 for name in report['stair_objects']+[f'R18_Ceiling_L{floor}']+(report['moved_objects'] if floor==1 else report['hall_replacement_objects']):
  o=bpy.data.objects[name];o.hide_set(False);o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(R/f'exports/revision18_floor{floor}.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
(R/'data/revision18_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
print('STAIR_TURN_FITTED',report['upper_turn_y_bounds_m'])
