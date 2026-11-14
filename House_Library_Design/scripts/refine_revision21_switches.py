from pathlib import Path
import bpy, json, math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'House_Library_Design.blend'
bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene=bpy.context.scene; bpy.context.view_layer.update()
points_path=ROOT/'data/electrical_points.json'
points=json.loads(points_path.read_text(encoding='utf8')); by_id={p['id']:p for p in points}
changes=[]; exported=[]

# Move the kitchen plate around the corner onto the narrow return wall separating the fridge from the doorway.
pid='E1_004_SWITCH'; spec=by_id[pid]
if not (abs(spec['x_m']-7.825)<1e-5 and abs(spec['y_m']-3.9255)<1e-5 and spec['face']=='N'):
    raise ValueError(f'{pid} is not at the expected revision-20 location: {spec}')
x,y,z=7.8355,4.20,spec['height_aff_m']; angle=math.pi/2
root=bpy.data.objects[pid]; r1=bpy.data.objects[pid+'_rocker']; r2=bpy.data.objects[pid+'_rocker.001']
old={'x_m':spec['x_m'],'y_m':spec['y_m'],'face':spec['face']}
root.location=(x,y,z); root.rotation_euler.z=angle
r1.location=(x-0.008,y-0.0375,z); r2.location=(x-0.008,y+0.0375,z)
r1.rotation_euler.z=angle; r2.rotation_euler.z=angle
for obj in (root,r1,r2):
    obj['point_id']=pid; obj['room']='Kitchen'; obj['purpose']='Kitchen ceiling + task lights'; obj['wall_face']='W'; obj['level']=1
spec.update({'x_m':x,'y_m':y,'face':'W'})
changes.append({'id':pid,'from':old,'to':{'x_m':x,'y_m':y,'face':'W'},'room':'Kitchen','purpose':spec['purpose'],'wall':'perpendicular fridge-return surface','objects':[root.name,r1.name,r2.name]})
exported.extend([root.name,r1.name,r2.name])

# Place the dining controls on the wall segment between the end of the kitchen counter and the dining table.
placements={'E1_019_SWITCH':7.23,'E1_090_SWITCH':7.41}
for pid,y in placements.items():
    spec=by_id[pid]
    expected_y=7.32 if pid=='E1_019_SWITCH' else 7.50
    if not (abs(spec['x_m']-6.6255)<1e-5 and abs(spec['y_m']-expected_y)<1e-5 and spec['face']=='E'):
        raise ValueError(f'{pid} is not at the expected revision-20 location: {spec}')
    x,z=10.39460277557373,spec['height_aff_m']
    old={'x_m':spec['x_m'],'y_m':spec['y_m'],'face':spec['face']}
    root=bpy.data.objects[pid]; r1=bpy.data.objects[pid+'_rocker']; r2=bpy.data.objects[pid+'_rocker.001']
    root.location=(x,y,z); root.rotation_euler.z=0
    r1.location=(x-0.008,y-0.0375,z); r2.location=(x-0.008,y+0.0375,z)
    r1.rotation_euler.z=0; r2.rotation_euler.z=0
    for obj in (root,r1,r2):
        obj['point_id']=pid; obj['room']='Living'; obj['purpose']=spec['purpose']; obj['wall_face']='W'; obj['level']=1
    spec.update({'x_m':x,'y_m':y,'face':'W'})
    changes.append({'id':pid,'from':old,'to':{'x_m':x,'y_m':y,'face':'W'},'room':'Living','purpose':spec['purpose'],'wall':'east wall strip between kitchen counter and dining table','objects':[root.name,r1.name,r2.name]})
    exported.extend([root.name,r1.name,r2.name])

bpy.context.view_layer.update()
checks=[
 ('E1_004_SWITCH',(7.40,4.20,1.05),(1,0,0),'R_L1_SOURCE_WALL_6',(-1,0,0)),
 ('E1_019_SWITCH',(9.00,7.23,1.05),(1,0,0),'R_L1_SOURCE_WALL_5',(-1,0,0)),
 ('E1_090_SWITCH',(9.00,7.41,1.05),(1,0,0),'R_L1_SOURCE_WALL_5',(-1,0,0)),
]
hidden=[]
for pid in placements.keys()|{'E1_004_SWITCH'}:
    for name in (pid,pid+'_rocker',pid+'_rocker.001'):
        obj=bpy.data.objects[name]; hidden.append((obj,obj.hide_get())); obj.hide_set(True)
bpy.context.view_layer.update(); depsgraph=bpy.context.evaluated_depsgraph_get()
surface_checks=[]
for pid,origin,direction,expected_obj,expected_normal in checks:
    hit,loc,norm,face_index,obj,matrix=scene.ray_cast(depsgraph,Vector(origin),Vector(direction))
    if not hit or obj.name!=expected_obj or any(abs(norm[i]-expected_normal[i])>.02 for i in range(3)):
        raise ValueError(f'{pid} failed face check: hit={hit}, object={obj.name if obj else None}, normal={tuple(norm)}')
    surface_checks.append({'id':pid,'wall_object':obj.name,'location_m':[round(v,4) for v in loc],'normal':[round(v,3) for v in norm]})
for obj,was_hidden in hidden: obj.hide_set(was_hidden)
bpy.context.view_layer.update()

# Check the dining plate run fits the gap in Y between the modeled counter and table.
counter_end_y=7.11; table_start_y=7.51; plate_half_y=.075
low=7.23-plate_half_y; high=7.41+plate_half_y; between_gap=round(table_start_y-counter_end_y,4)
if low-counter_end_y < .035 or table_start_y-high < .02:
    raise ValueError(f'Dining switch group does not fit between counter and table: counter gap={low-counter_end_y}, table gap={table_start_y-high}')

scene['interior_revision']='LIBRARY 21.0 corrected switch wall locations'
points_path.write_text(json.dumps(points,ensure_ascii=False,indent=2),encoding='utf8')
report={'revision':21,'title':'Corrected switch wall locations from user screenshots','correction_basis':'E1_004 is on the perpendicular return face separating fridge housing and kitchen doorway. E1_019 and E1_090 are on the east wall segment between kitchen counter end and dining table, facing into the kitchen/living space.','switches':changes,'surface_checks':surface_checks,'clearances_m':{'dining_group_to_counter_end':round(low-counter_end_y,4),'dining_group_to_table_edge':round(table_start_y-high,4),'E1_004_to_fridge_housing':.109,'E1_004_to_kitchen_door_opening_along_y':.205},'all_switches_keep_original_height_aff_m':True,'stair_partition_switch_cluster_restored_to_pre_revision20_wall':True,'other_objects_unchanged':True}
(ROOT/'data/revision21_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL),compress=True)
for obj in bpy.context.selected_objects: obj.select_set(False)
for name in exported: bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['E1_004_SWITCH']
patch=ROOT.parent/'House_Browser_Viewer/revision21_switches_floor1.glb'
bpy.ops.export_scene.gltf(filepath=str(patch),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
report['browser_patch']={'file':patch.name,'bytes':patch.stat().st_size,'exported_objects':exported}
(ROOT/'data/revision21_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('REVISION21_SAVED',json.dumps(report,ensure_ascii=False),flush=True)
