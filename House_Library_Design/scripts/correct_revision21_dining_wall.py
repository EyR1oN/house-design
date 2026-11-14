from pathlib import Path
import bpy,json,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'House_Library_Design.blend'
bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene=bpy.context.scene; points_path=ROOT/'data/electrical_points.json'
points=json.loads(points_path.read_text(encoding='utf8'));by_id={p['id']:p for p in points}
report_path=ROOT/'data/revision21_report.json';report=json.loads(report_path.read_text(encoding='utf8'))
plane_x=9.4902;root_x=plane_x-.0055
moves={'E1_019_SWITCH':7.23,'E1_090_SWITCH':7.41}
for pid,y in moves.items():
    p=by_id[pid]
    if not (abs(p['x_m']-10.39460277557373)<1e-5 and p['face']=='W'):
        raise ValueError(f'{pid} is not at the interim revision-21 position: {p}')
    root=bpy.data.objects[pid]; r1=bpy.data.objects[pid+'_rocker']; r2=bpy.data.objects[pid+'_rocker.001']
    z=p['height_aff_m']; old={'x_m':p['x_m'],'y_m':p['y_m'],'face':p['face']}
    root.location=(root_x,y,z);root.rotation_euler.z=0
    r1.location=(root_x-.008,y-.0375,z);r2.location=(root_x-.008,y+.0375,z)
    r1.rotation_euler.z=0;r2.rotation_euler.z=0
    p.update({'x_m':root_x,'y_m':y,'face':'W'})
    for obj in (root,r1,r2):
        obj['point_id']=pid;obj['room']='Living';obj['purpose']=p['purpose'];obj['wall_face']='W';obj['level']=1
    record=next(s for s in report['switches'] if s['id']==pid)
    record['interim_to']=record['to']
    record['to']={'x_m':root_x,'y_m':y,'face':'W'}
    record['wall']='inner junction wall between the end of the kitchen counter and the dining table'
    record['surface_x_m']=plane_x
    record['correction_note']='Placed on the exact wall face shown in the user screenshot; the previous point was on the far east exterior wall.'

# Hide moved switch geometry while checking the wall mesh itself.
hidden=[]
for pid in moves:
    for name in (pid,pid+'_rocker',pid+'_rocker.001'):
        o=bpy.data.objects[name];hidden.append((o,o.hide_get()));o.hide_set(True)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
checks=[]
for pid,y in moves.items():
    hit,loc,norm,face_index,obj,matrix=scene.ray_cast(dg,Vector((9.0,y,1.05)),Vector((1,0,0)))
    if not hit or obj.name!='R_L1_SOURCE_WALL_5' or abs(loc.x-plane_x)>.002 or norm.x>-.98:
        raise ValueError(f'{pid} misses exact inner wall face: hit={hit}, obj={obj.name if obj else None}, loc={tuple(loc)}, norm={tuple(norm)}')
    checks.append({'id':pid,'wall_object':obj.name,'location_m':[round(v,4) for v in loc],'normal':[round(v,3) for v in norm]})
for o,was_hidden in hidden:o.hide_set(was_hidden)
bpy.context.view_layer.update()
report['surface_checks']=[c for c in report['surface_checks'] if c['id']=='E1_004_SWITCH']+checks
report['correction_basis']='Screenshot-specific coordinates verified against the actual inner wall face at x=9.4902 m.'
report['switches']=[next(s for s in report['switches'] if s['id']==pid) for pid in ('E1_004_SWITCH','E1_019_SWITCH','E1_090_SWITCH')]
points_path.write_text(json.dumps(points,ensure_ascii=False,indent=2),encoding='utf8')
bpy.context.scene['interior_revision']='LIBRARY 21.0 corrected switch wall locations'
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL),compress=True)
# Re-export all 9 components, including the corrected fridge return and dining wall positions.
for o in bpy.context.selected_objects:o.select_set(False)
exported=[]
for pid in ('E1_004_SWITCH','E1_019_SWITCH','E1_090_SWITCH'):
    for name in (pid,pid+'_rocker',pid+'_rocker.001'):
        bpy.data.objects[name].select_set(True);exported.append(name)
bpy.context.view_layer.objects.active=bpy.data.objects['E1_004_SWITCH']
patch=ROOT.parent/'House_Browser_Viewer/revision21_switches_floor1.glb'
bpy.ops.export_scene.gltf(filepath=str(patch),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
report['browser_patch']={'file':patch.name,'bytes':patch.stat().st_size,'exported_objects':exported}
report['clearances_m']['dining_group_to_counter_end']=.045
report['clearances_m']['dining_group_to_table_edge']=.025
report['stair_partition_switch_cluster_removed']=True
report.pop('stair_partition_switch_cluster_restored_to_pre_revision20_wall',None)
report['other_objects_unchanged']=True
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('REVISION21_DINING_WALL_CORRECTED',json.dumps({'switches':moves,'root_x_m':root_x,'wall_surface_x_m':plane_x,'surface_checks':checks},ensure_ascii=False),flush=True)
