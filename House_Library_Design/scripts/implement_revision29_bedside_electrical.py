"""Align the primary-bedroom socket/switch pairs above their bedside tables."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'House_Library_Design.blend'
POINTS = ROOT / 'data' / 'electrical_points.json'
PATCH = ROOT.parent / '.local-preview' / 'revision29_bedside_electrical.glb'
FLOOR_Z = 3.2

# Both pairs sit on the headboard wall, centered over the nightstand on each
# side of the bed. Face rotations keep the left plates flush with that wall.
TARGETS = {
    'E2_028_SOCKET': {'x_m': 11.394638, 'y_m': 11.32, 'height_aff_m': 0.68, 'face': 'W'},
    'E2_030_SWITCH': {'x_m': 11.394638, 'y_m': 11.32, 'height_aff_m': 0.82, 'face': 'W'},
    'E2_029_SOCKET': {'x_m': 11.394638, 'y_m': 8.78, 'height_aff_m': 0.68, 'face': 'W'},
    'E2_031_SWITCH': {'x_m': 11.394638, 'y_m': 8.78, 'height_aff_m': 0.82, 'face': 'W'},
}
FACE_Z = {'S': 0.0, 'W': -math.pi / 2}

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
upper = scene.view_layers.get('Upper_Design')
if upper is None:
    raise RuntimeError('Upper_Design view layer is missing')
for window in bpy.context.window_manager.windows:
    window.view_layer = upper

points = json.loads(POINTS.read_text(encoding='utf-8'))
by_id = {point['id']: point for point in points}
if not set(TARGETS).issubset(by_id):
    raise RuntimeError(f'Missing bedside points: {sorted(set(TARGETS) - set(by_id))}')

export_names = []
changes = []
for point_id, target in TARGETS.items():
    point = by_id[point_id]
    old = {key: point[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face')}
    root = bpy.data.objects.get(point_id)
    if root is None:
        raise RuntimeError(f'Missing Blender root object {point_id}')
    current = root.location.copy()
    expected = Vector((point['x_m'], point['y_m'], FLOOR_Z + point['height_aff_m']))
    if (current - expected).length > 0.002:
        raise RuntimeError(f'{point_id} no longer matches the schedule: {tuple(current)} != {tuple(expected)}')

    old_center = Vector((point['x_m'], point['y_m'], FLOOR_Z + point['height_aff_m']))
    new_center = Vector((target['x_m'], target['y_m'], FLOOR_Z + target['height_aff_m']))
    if point['face'] not in FACE_Z or target['face'] not in FACE_Z:
        raise RuntimeError(f'No supported plate orientation for {point_id}: {point["face"]} -> {target["face"]}')
    angle_delta = FACE_Z[target['face']] - FACE_Z[point['face']]
    transform = (Matrix.Translation(new_center)
                 @ Matrix.Rotation(angle_delta, 4, 'Z')
                 @ Matrix.Translation(-old_center))
    assembly = sorted(
        (obj for obj in bpy.data.objects
         if obj.name == point_id or obj.name.startswith(point_id + '_')),
        key=lambda obj: obj.name,
    )
    if not assembly:
        raise RuntimeError(f'No Blender geometry found for {point_id}')
    for obj in assembly:
        obj.matrix_world = transform @ obj.matrix_world
        obj.hide_set(False)
        obj.hide_render = False
        obj.select_set(True)
    root = bpy.data.objects[point_id]
    root.update_tag()
    root['electrical_point'] = True
    root['point_id'] = point_id
    root['room'] = point['room']
    root['device_type'] = point['type']
    root['purpose'] = point['purpose']
    root['level'] = point['level']
    root['height_above_finished_floor_m'] = target['height_aff_m']
    root['circuit_group_proposed'] = point['proposed_group']
    root['wall_face'] = point['face']
    root['modules'] = point['modules']
    root['as_built_verified'] = False
    root['mep_status'] = 'PROPOSED_POSITION_ONLY'

    point.update(target)
    export_names.extend(obj.name for obj in assembly)
    changes.append({
        'id': point_id,
        'old': old,
        'new': {key: point[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face')},
        'assembly': [obj.name for obj in assembly],
    })

for obj in bpy.context.selected_objects:
    obj.select_set(False)
for name in export_names:
    bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['E2_028_SOCKET']

scene['interior_revision'] = 'LIBRARY 29.0 primary-bedroom bedside electrical alignment'
bpy.context.view_layer.update()
POINTS.write_text(json.dumps(points, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)

PATCH.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=str(PATCH),
    use_selection=True,
    export_format='GLB',
    export_cameras=False,
    export_lights=False,
    export_extras=True,
)
if not PATCH.is_file() or PATCH.stat().st_size < 1024:
    raise RuntimeError('The revised bedside electrical GLB patch was not exported')

for point_id, target in TARGETS.items():
    point = by_id[point_id]
    actual = bpy.data.objects[point_id].location
    expected = (point['x_m'], point['y_m'], FLOOR_Z + point['height_aff_m'])
    if math.dist(actual, expected) > 0.002:
        raise RuntimeError(f'{point_id} failed Blender position check: {tuple(actual)}')

print(json.dumps({
    'revision': 29,
    'changes': changes,
    'patch': str(PATCH),
    'patch_bytes': PATCH.stat().st_size,
}, ensure_ascii=False))
