from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Upper_Design']
e=json.loads((R/'data/electrical_points.json').read_text());point=next(q for q in e if q['id']=='E2_084_SOCKET');assert abs(point['y_m']-3.43)<.001
r=json.loads((R/'data/revision16_report.json').read_text());dy=2.95-point['y_m'];names=[]
for o in bpy.data.objects:
 if o.name.startswith('E2_084_SOCKET'):o.location.y+=dy;names.append(o.name)
assert names;point['y_m']=2.95;r['electrical_relocation']={'id':point['id'],'from_y':3.43,'to_y':2.95,'reason':'Keep cleaning socket clear of the new wall-side door and plugged-in cable away from its swing'}
for n in names:
 if n not in r['changed_objects']['2']:r['changed_objects']['2'].append(n)
(R/'data/electrical_points.json').write_text(json.dumps(e,indent=2),encoding='utf8');(R/'data/revision16_report.json').write_text(json.dumps(r,indent=2),encoding='utf8');bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for n in r['changed_objects']['2']:bpy.data.objects[n].select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision16_floor2.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('SOCKET_MOVED',len(names))
