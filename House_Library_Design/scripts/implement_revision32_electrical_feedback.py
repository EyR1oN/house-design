"""Move kitchen and laundry appliance outlets to concealed, appliance-aligned positions."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'House_Library_Design.blend'
POINTS_PATH = ROOT / 'data' / 'electrical_points.json'
PATCH_FLOOR_1 = ROOT.parent / '.local-preview' / 'revision32_electrical_floor1.glb'
FLOOR_Z = {1: 0.0, 2: 3.2}

TARGETS = {
    'E1_005_SOCKET': {
        'x_m': 8.58, 'y_m': 6.02, 'height_aff_m': 0.76, 'face': 'E',
        'purpose': 'Kitchen island double socket for blender, mixer and kettle',
        'installation_detail': (
            'Double socket flush to the kitchen-facing side panel of the island, '
            'just below the worktop, for blender/mixer and kettle. Keep leads on the '
            'island side and away from the sink and hob.'
        ),
    },
    'E1_006_SOCKET': {
        'x_m': 8.58, 'y_m': 6.67, 'height_aff_m': 0.76, 'face': 'E',
        'purpose': 'Kitchen island double socket for small appliances and spare use',
        'installation_detail': (
            'Second double socket flush to the kitchen-facing side panel of the island, '
            'just below the worktop, for mixer/blender and other small appliances.'
        ),
    },
    'E1_022_SOCKET': {
        'x_m': 10.03, 'y_m': 3.7941, 'height_aff_m': 0.55, 'face': 'S',
        'purpose': 'Concealed rear-wall supply for the washing machine in the laundry stack',
        'installation_detail': (
            'Rear wall behind the washer, with cable routed behind the appliance. '
            'Leave the recess and plug depth required by the selected washer; confirm '
            'manufacturer instructions and a side-accessible isolation arrangement.'
        ),
    },
    'E1_023_SOCKET': {
        'x_m': 10.03, 'y_m': 3.7941, 'height_aff_m': 1.45, 'face': 'S',
        'purpose': 'Concealed rear-wall supply for the dryer above the washing machine',
        'installation_detail': (
            'Rear wall behind the dryer, with cable routed behind the stack. Leave the '
            'recess and plug depth required by the selected dryer and stacking kit; '
            'confirm manufacturer instructions and side access for service.'
        ),
    },
}

EXPECTED_OLD = {
    'E1_005_SOCKET': (8.68, 5.95, 0.74),
    'E1_006_SOCKET': (8.68, 6.75, 0.74),
    'E1_022_SOCKET': (9.28, 3.7941, 1.14),
    'E1_023_SOCKET': (9.43, 3.7941, 1.14),
}


def assembly(point_id):
    return sorted((obj for obj in bpy.data.objects
                   if obj.name == point_id or obj.name.startswith(point_id + '_')),
                  key=lambda obj: obj.name)


def set_metadata(root, point):
    root['design_status'] = 'PROPOSED_INTERIOR'
    root['section'] = 'RIGHT'
    root['level'] = point['level']
    root['point_id'] = point['id']
    root['room'] = point['room']
    root['device_type'] = point['type']
    root['purpose'] = point['purpose']
    root['height_above_finished_floor_m'] = point['height_aff_m']
    root['circuit_group_proposed'] = point['proposed_group']
    root['wall_face'] = point['face']
    root['modules'] = point['modules']
    root['as_built_verified'] = False
    root['mep_status'] = 'PROPOSED_POSITION_ONLY'
    root['electrical_point'] = True


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
points = json.loads(POINTS_PATH.read_text(encoding='utf-8'))
by_id = {point['id']: point for point in points}
if len(by_id) != len(points):
    raise RuntimeError('Electrical schedule contains duplicate point IDs.')

for point_id, expected in EXPECTED_OLD.items():
    point = by_id.get(point_id)
    root = bpy.data.objects.get(point_id)
    if point is None or root is None:
        raise RuntimeError(f'Missing scheduled Blender point {point_id}.')
    values = (point['x_m'], point['y_m'], point['height_aff_m'])
    if any(abs(a - b) > 0.002 for a, b in zip(values, expected)):
        raise RuntimeError(f'{point_id} schedule changed since the reviewed baseline: {values}')
    if (root.location - Vector((expected[0], expected[1],
                                FLOOR_Z[point['level']] + expected[2]))).length > 0.002:
        raise RuntimeError(f'{point_id} Blender model no longer matches its schedule.')

changes = []
for point_id, target in TARGETS.items():
    point = by_id[point_id]
    root = bpy.data.objects[point_id]
    parts = assembly(point_id)
    if len(parts) < 2:
        raise RuntimeError(f'{point_id} socket assembly is incomplete.')
    if any(obj.parent or obj.constraints for obj in parts):
        raise RuntimeError(f'{point_id} assembly has parenting or constraints; refusing movement.')
    old = {key: point[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face')}
    center = Vector((target['x_m'], target['y_m'], FLOOR_Z[point['level']] + target['height_aff_m']))
    delta = center - root.location
    for obj in parts:
        obj.location += delta
        obj.hide_set(False)
        obj.hide_render = False
    point.update({key: target[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face', 'purpose')})
    point['installation_detail'] = target['installation_detail']
    set_metadata(root, point)
    if (root.location - center).length > 0.002:
        raise RuntimeError(f'{point_id} did not move to its scheduled position.')
    changes.append({'id': point_id, 'old': old,
                    'new': {key: point[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face')},
                    'assembly': [obj.name for obj in parts]})

scene = bpy.context.scene
scene['interior_revision'] = 'LIBRARY 32.0 concealed kitchen and laundry appliance outlets'
scene['electrical_revision'] = 32
POINTS_PATH.write_text(json.dumps(points, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for window in bpy.context.window_manager.windows:
    window.view_layer = scene.view_layers['Ground_Design']
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
expected_names = []
for point_id in TARGETS:
    for obj in assembly(point_id):
        obj.select_set(True)
        expected_names.append(obj.name)
bpy.context.view_layer.objects.active = bpy.data.objects['E1_005_SOCKET']
PATCH_FLOOR_1.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(PATCH_FLOOR_1), use_selection=True,
                          export_format='GLB', export_cameras=False, export_lights=False,
                          export_extras=True)
if not PATCH_FLOOR_1.is_file() or PATCH_FLOOR_1.stat().st_size < 1024:
    raise RuntimeError('Revised floor-1 electrical patch failed to export.')
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)
print(json.dumps({'revision': 32, 'changes': changes,
                  'patch': str(PATCH_FLOOR_1), 'patch_nodes': expected_names}, ensure_ascii=False))
