"""Reposition the upper bathroom outlet, towel radiator and hanging towel."""
import json
from math import pi
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
MASTER = PROJECT/'House_Library_Design.blend'
POINTS = PROJECT/'data/electrical_points.json'
PLACEMENTS = PROJECT/'data/placements.json'
PATCH = PROJECT.parent/'.local-preview/revision37_floor2.glb'

bpy.ops.wm.open_mainfile(filepath=str(MASTER))
scene = bpy.context.scene
if scene.get('electrical_revision') != 36:
    raise ValueError('Expected the revision 36 model.')
for window in bpy.context.window_manager.windows:
    window.view_layer = scene.view_layers['Upper_Design']
bpy.context.view_layer.update()

points = json.loads(POINTS.read_text(encoding='utf-8'))
placements = json.loads(PLACEMENTS.read_text(encoding='utf-8'))
socket_id = 'E2_046_SOCKET'
socket = bpy.data.objects[socket_id]
socket_parts = [o for o in scene.objects if o.name == socket_id or o.name.startswith(socket_id+'_')]
point = next(p for p in points if p['id'] == socket_id)
target = Vector((9.43,5.4972,4.43))
delta = target-socket.location
for part in socket_parts:
    part.location += delta
purpose = 'Recessed service outlet concealed behind the left edge of the bathroom mirror'
point.update(x_m=target.x,y_m=target.y,height_aff_m=1.23,purpose=purpose,
    installation_detail='Coordinate a recessed fitting and a service-accessible mirror; the visible glass face stays clear.')
socket['purpose'] = purpose
socket['height_above_finished_floor_m'] = 1.23
socket['recessed_behind_mirror'] = True

transform = Matrix.Translation((8.96,5.5395,4.34)) @ Matrix.Rotation(pi/2,4,'Z') @ Matrix.Translation((-8.515,-6.89,-4.34))
towel_parts = []
for label in ('Upper_Bath_Towel_Radiator','Upper_Bath_Hanging_Towel'):
    record = next(p for p in placements if p['label'] == label)
    parts = [bpy.data.objects[name] for name in record['objects']]
    for part in parts:
        part.matrix_world = transform @ part.matrix_world
    towel_parts.extend(parts)
    corners = [o.matrix_world @ Vector(v) for o in parts for v in o.bound_box]
    record['bounds'] = [[min(p[i] for p in corners), max(p[i] for p in corners)] for i in range(3)]

bpy.context.view_layer.update()
fittings_max_y = max((o.matrix_world @ Vector(v)).y for o in towel_parts for v in o.bound_box)
leaf = bpy.data.objects['LIB_Door_L2_BATHROOM_DOOR_Door.001_PREPARED']
leaf_min_y = min((leaf.matrix_world @ Vector(v)).y for v in leaf.bound_box)
if leaf_min_y-fittings_max_y < .1:
    raise ValueError('The towel radiator is too close to the open door leaf.')
mirror = bpy.data.objects['LIB_Upper_Bath_Mirror_BathroomMirror_PREPARED']
glass_back = min((mirror.matrix_world @ Vector(v)).y for v in mirror.bound_box)
socket_front = max((o.matrix_world @ Vector(v)).y for o in socket_parts for v in o.bound_box)
if socket_front > glass_back:
    raise ValueError('The recessed outlet intersects the mirror.')
print(f'Open leaf gap: {leaf_min_y-fittings_max_y:.3f} m')

bpy.ops.object.select_all(action='DESELECT')
for obj in socket_parts+towel_parts:
    obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(PATCH), use_selection=True, export_format='GLB',
    export_cameras=False, export_lights=False, export_extras=True)
bpy.ops.object.select_all(action='DESELECT')
scene['electrical_revision'] = 37
scene['interior_revision'] = 'LIBRARY 37.0 upper bathroom service outlet and towel radiator'
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER), compress=True)
for path,data in ((POINTS,points),(PLACEMENTS,placements)):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
