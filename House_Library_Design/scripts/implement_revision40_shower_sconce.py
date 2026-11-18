"""Place a matching library sconce above the ground-floor shower-room mirror."""
import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
MASTER = PROJECT/'House_Library_Design.blend'
SCHEDULE = PROJECT/'data/electrical_points.json'
PLACEMENTS = PROJECT/'data/placements.json'
PATCH = PROJECT.parent/'.local-preview/revision40_floor1.glb'
POINT = 'L1_105'
GROUP = 'GROUND_SHOWER_LIGHT'

bpy.ops.wm.open_mainfile(filepath=str(MASTER))
scene = bpy.context.scene
if scene.get('electrical_revision') != 39:
    raise ValueError('Expected revision 39 master.')

points = json.loads(SCHEDULE.read_text(encoding='utf-8'))
by_id = {point['id']: point for point in points}
placements = json.loads(PLACEMENTS.read_text(encoding='utf-8'))
record = next(item for item in placements if item['label']=='Stairs_Wall_Sconce')
fixtures = [bpy.data.objects[name] for name in record['objects']]

def show_layer(name):
    for window in bpy.context.window_manager.windows:
        window.view_layer = scene.view_layers[name]
    bpy.context.view_layer.update()

show_layer('Upper_Design')
source_poses = {obj.name: obj.matrix_world.copy() for obj in fixtures}
show_layer('Ground_Design')
mirror = bpy.data.objects['LIB_Ground_Vanity_Mirror_BathroomMirror_PREPARED']
corners = [mirror.matrix_world @ Vector(v) for v in mirror.bound_box]
y = round((min(p.y for p in corners)+max(p.y for p in corners))/2,4)
z = 2.12
deps = bpy.context.evaluated_depsgraph_get()
for sample_y in (y-.055,y,y+.055):
    hit, loc, normal, _, support, _ = scene.ray_cast(
        deps,Vector((5.85,sample_y,z)),Vector((-1,0,0)),distance=.45)
    if not hit or support.name != 'R_L1_SOURCE_WALL_3' or normal.x < .99:
        raise ValueError('No clear mounting wall over lower shower mirror.')
anchor=Vector((round(loc.x,5),y,z))
delta=anchor-source_poses['L2_096'].translation
collection=bpy.data.collections.new('LIB_Ground_Shower_Mirror_Sconce')
scene.collection.children.link(collection)
parts=[]
purpose='Wall sconce centered over the ground-floor shower mirror'
for source in fixtures:
    obj=source.copy()
    obj.name=POINT+source.name[len('L2_096'):]
    collection.objects.link(obj)
    obj.matrix_world=Matrix.Translation(delta) @ source_poses[source.name]
    for name,value in dict(point_id=POINT,room='Ground_WC',level=1,purpose=purpose,
        circuit_group_proposed=GROUP,height_above_finished_floor_m=z,viewer_fixed_light=True,
        electrical_point=True).items():
        obj[name]=value
    parts.append(obj)

bpy.context.view_layer.update()
vertices=[obj.matrix_world@Vector(v) for obj in parts for v in obj.bound_box]
if min(p.z for p in vertices)-max(p.z for p in corners)<.08:
    raise ValueError('The sconce is too close to the top of the mirror.')
placements.append(dict(record,label='Ground_Shower_Mirror_Sconce',group='Ground_WC',level=1,
    bounds=[[min(v[i] for v in vertices),max(v[i] for v in vertices)] for i in range(3)],
    objects=[obj.name for obj in parts]))

points.append(dict(id=POINT,room='Ground_WC',level=1,type='LIGHT_POINT',x_m=anchor.x,
    y_m=y,height_aff_m=z,face='E',purpose=purpose,proposed_group=GROUP,modules=1,
    status='PROPOSED_NOT_AS_BUILT',control_point='E1_025_SWITCH'))
by_id['L1_057'].update(proposed_group=GROUP,control_point='E1_025_SWITCH')
by_id['E1_025_SWITCH'].update(purpose='Shower ceiling and mirror sconce together; separate extractor control',
                               proposed_group=GROUP+' + GROUND_SHOWER_EXTRACT')
switch=bpy.data.objects['E1_025_SWITCH']
switch['purpose']=by_id['E1_025_SWITCH']['purpose']
switch['circuit_group_proposed']=by_id['E1_025_SWITCH']['proposed_group']
bpy.ops.object.select_all(action='DESELECT')
for obj in parts:
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(PATCH),use_selection=True,export_format='GLB',
    export_extras=True,export_cameras=False,export_lights=False)
bpy.ops.object.select_all(action='DESELECT')
scene['electrical_revision']=40
scene['interior_revision']='LIBRARY 40.0 lower shower mirror sconce'
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER),compress=True)
for path,data in ((SCHEDULE,points),(PLACEMENTS,placements)):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
