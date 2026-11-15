"""Refine proposed socket locations for kitchen, laundry and upper bathroom."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'House_Library_Design.blend'
POINTS_PATH = ROOT / 'data' / 'electrical_points.json'
PATCH_DIR = ROOT.parent / '.local-preview'
PATCH_FLOOR_1 = PATCH_DIR / 'revision31_electrical_floor1.glb'
PATCH_FLOOR_2 = PATCH_DIR / 'revision31_electrical_floor2.glb'
FLOOR_Z = {1: 0.0, 2: 3.2}

TARGETS = {
    'E1_005_SOCKET': {
        'template': 'E2_043_SOCKET',
        'x_m': 8.68, 'y_m': 5.95, 'height_aff_m': 0.74, 'face': 'E',
        'purpose': 'Kitchen island small appliances: blender, mixer and kettle',
        'proposed_group': 'KITCHEN_WORKTOP', 'modules': 2,
        'installation_detail': (
            'Kitchen-facing side of the island, 120 mm below the countertop; '
            'for blender and other small appliances. Confirm water-safe location '
            'and outlet finish with the kitchen installer.'
        ),
        'room': 'Kitchen', 'level': 1,
    },
    'E1_006_SOCKET': {
        'template': 'E2_043_SOCKET',
        'x_m': 8.68, 'y_m': 6.75, 'height_aff_m': 0.74, 'face': 'E',
        'purpose': 'Kitchen island small appliances and spare worktop use',
        'proposed_group': 'KITCHEN_WORKTOP', 'modules': 2,
        'installation_detail': (
            'Kitchen-facing side of the island, 120 mm below the countertop; '
            'keeps appliance leads away from the sink, hob and walking route.'
        ),
        'room': 'Kitchen', 'level': 1,
    },
    'E1_010_SOCKET': {
        'x_m': 10.394603, 'y_m': 5.62, 'height_aff_m': 0.50, 'face': 'W',
        'purpose': 'Dishwasher supply in the adjacent sink-base cabinet, not behind the appliance',
        'proposed_group': 'DISHWASHER', 'modules': 1,
        'installation_detail': (
            'Accessible service point at the dishwasher-facing end of the adjacent '
            'sink-base cabinet. Final mounting panel must stay clear of the trap, '
            'water valves and leaks; do not put the plug behind the dishwasher.'
        ),
        'room': 'Kitchen', 'level': 1,
    },
    'E2_046_SOCKET': {
        'template': 'E1_007_SOCKET',
        'x_m': 9.15, 'y_m': 5.50, 'height_aff_m': 1.12, 'face': 'N',
        'purpose': 'Hair dryer and grooming at the vanity, left of the basin',
        'proposed_group': 'WET_ROOM_REVIEW', 'modules': 1,
        'installation_detail': (
            'Beside the left edge of the vanity; modelled about 1.43 m horizontally '
            'from the bathtub edge. A qualified designer/electrician must confirm '
            'the exact bathroom zone, IP rating and protection before installation.'
        ),
        'room': 'Upper_Bath', 'level': 2,
    },
    'E1_093_SOCKET': {
        'template': 'E1_007_SOCKET',
        'x_m': 9.78, 'y_m': 2.60, 'height_aff_m': 1.85, 'face': 'N',
        'purpose': 'Gas-boiler power provision beside the appliance',
        'proposed_group': 'BOILER', 'modules': 1,
        'installation_detail': (
            'Accessible on the adjacent wall, left of the boiler body, not behind it. '
            'Final supply type, rating, isolation and clearances must follow the selected '
            'boiler instructions and the licensed installer’s design.'
        ),
        'room': 'Laundry', 'level': 1,
    },
}

EXPECTED_OLD = {
    'E1_005_SOCKET': (9.55, 3.973, 2.79, 1),
    'E1_006_SOCKET': (10.10, 3.973, 2.79, 1),
    'E1_010_SOCKET': (10.394603, 6.92, 0.35, 1),
    'E2_046_SOCKET': (8.465671, 6.67, 1.12, 2),
}


def object_assembly(point_id):
    return sorted(
        (obj for obj in bpy.data.objects
         if obj.name == point_id or obj.name.startswith(point_id + '_')),
        key=lambda obj: obj.name,
    )


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


def remove_assembly(point_id):
    for obj in object_assembly(point_id):
        bpy.data.objects.remove(obj, do_unlink=True)


def clone_assembly(template_id, target_id, target, destination_collection):
    source_root = bpy.data.objects.get(template_id)
    source_parts = object_assembly(template_id)
    if source_root is None or not source_parts:
        raise RuntimeError(f'Missing socket template assembly {template_id}')
    center = Vector((target['x_m'], target['y_m'],
                     FLOOR_Z[target['level']] + target['height_aff_m']))
    delta = center - source_root.location
    result = []
    for source in source_parts:
        if source.parent or source.constraints:
            raise RuntimeError(f'{source.name} must be an unparented, unconstrained electrical part.')
        clone = source.copy()
        if source.data is not None:
            clone.data = source.data
        suffix = source.name[len(template_id):]
        clone.name = target_id + suffix
        clone.location = source.location + delta
        for collection in list(clone.users_collection):
            collection.objects.unlink(clone)
        destination_collection.objects.link(clone)
        clone.hide_set(False)
        clone.hide_render = False
        result.append(clone)
    root = bpy.data.objects[target_id]
    root.update_tag()
    return result


def move_assembly(point_id, old, target):
    root = bpy.data.objects.get(point_id)
    if root is None:
        raise RuntimeError(f'Missing Blender root {point_id}')
    expected = Vector((old['x_m'], old['y_m'], FLOOR_Z[old['level']] + old['height_aff_m']))
    if (root.location - expected).length > 0.002:
        raise RuntimeError(f'{point_id} no longer matches its schedule: {tuple(root.location)}')
    center = Vector((target['x_m'], target['y_m'], FLOOR_Z[target['level']] + target['height_aff_m']))
    transform = Matrix.Translation(center - root.location)
    assembly = object_assembly(point_id)
    if len(assembly) < 2:
        raise RuntimeError(f'{point_id} has an incomplete Blender assembly')
    for obj in assembly:
        if obj.parent or obj.constraints:
            raise RuntimeError(f'{obj.name} must be an unparented, unconstrained electrical part.')
        obj.location += transform.to_translation()
        obj.hide_set(False)
        obj.hide_render = False
    root.update_tag()
    return assembly


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
points = json.loads(POINTS_PATH.read_text(encoding='utf-8'))
by_id = {point['id']: point for point in points}
if 'E1_093_SOCKET' in by_id:
    raise RuntimeError('Revision 31 already exists; refusing to apply it twice.')
if not set(EXPECTED_OLD).issubset(by_id):
    raise RuntimeError('One or more expected revision-30 points are missing.')
for point_id, (x, y, height, level) in EXPECTED_OLD.items():
    point = by_id[point_id]
    if (point['level'] != level or abs(point['x_m'] - x) > 0.002
            or abs(point['y_m'] - y) > 0.002
            or abs(point['height_aff_m'] - height) > 0.002):
        raise RuntimeError(f'{point_id} changed since the reviewed revision-30 baseline.')

changes = []
for point_id in ('E1_005_SOCKET', 'E1_006_SOCKET', 'E2_046_SOCKET'):
    point = by_id[point_id]
    old = {key: point[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face')}
    destination = point['level']
    target = TARGETS[point_id]
    destination_collection = bpy.data.collections.get(f'Electrical_L{destination}')
    if destination_collection is None:
        raise RuntimeError(f'Missing Electrical_L{destination} collection')
    remove_assembly(point_id)
    assembly = clone_assembly(target['template'], point_id,
                              {**target, 'level': destination}, destination_collection)
    point.update({key: target[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face', 'purpose', 'proposed_group', 'modules')})
    point['installation_detail'] = target['installation_detail']
    set_metadata(bpy.data.objects[point_id], point)
    changes.append({'id': point_id, 'old': old,
                    'new': {key: point[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face')},
                    'assembly': [obj.name for obj in assembly], 'template': target['template']})

for point_id in ('E1_010_SOCKET',):
    point = by_id[point_id]
    old = {key: point[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face')}
    target = TARGETS[point_id]
    assembly = move_assembly(point_id, point, target)
    point.update({key: target[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face', 'purpose', 'proposed_group', 'modules')})
    point['installation_detail'] = target['installation_detail']
    set_metadata(bpy.data.objects[point_id], point)
    changes.append({'id': point_id, 'old': old,
                    'new': {key: point[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face')},
                    'assembly': [obj.name for obj in assembly]})

boiler = dict(by_id['E1_007_SOCKET'])
boiler.update({'id': 'E1_093_SOCKET', 'room': 'Laundry', 'level': 1, 'type': 'SOCKET',
               'x_m': TARGETS['E1_093_SOCKET']['x_m'], 'y_m': TARGETS['E1_093_SOCKET']['y_m'],
               'height_aff_m': TARGETS['E1_093_SOCKET']['height_aff_m'],
               'face': TARGETS['E1_093_SOCKET']['face'], 'purpose': TARGETS['E1_093_SOCKET']['purpose'],
               'proposed_group': TARGETS['E1_093_SOCKET']['proposed_group'],
               'modules': TARGETS['E1_093_SOCKET']['modules'],
               'status': 'PROPOSED_NOT_AS_BUILT',
               'installation_detail': TARGETS['E1_093_SOCKET']['installation_detail']})
points.append(boiler)
by_id[boiler['id']] = boiler
collection = bpy.data.collections.get('Electrical_L1')
assembly = clone_assembly(TARGETS['E1_093_SOCKET']['template'], 'E1_093_SOCKET',
                          {**TARGETS['E1_093_SOCKET'], 'level': 1}, collection)
set_metadata(bpy.data.objects['E1_093_SOCKET'], boiler)
changes.append({'id': 'E1_093_SOCKET', 'old': None,
                'new': {key: boiler[key] for key in ('x_m', 'y_m', 'height_aff_m', 'face')},
                'assembly': [obj.name for obj in assembly], 'template': TARGETS['E1_093_SOCKET']['template']})

# Keep every existing Blender point root's metadata aligned with the point schedule.
metadata_repairs = []
for point in points:
    root = bpy.data.objects.get(point['id'])
    if root is None:
        continue
    previous = root.get('point_id')
    set_metadata(root, point)
    if previous != point['id']:
        metadata_repairs.append({'object': root.name, 'old_point_id': previous, 'new_point_id': point['id']})

# The ground bathroom point stays in its existing position; record the required wet-area review.
ground_bath = by_id['E1_026_SOCKET']
ground_bath['installation_detail'] = (
    'Existing grooming position outside the modelled shower footprint; '
    'qualified designer/electrician must confirm the exact bathroom zone, IP rating '
    'and protection before installation.'
)
set_metadata(bpy.data.objects['E1_026_SOCKET'], ground_bath)

if len({point['id'] for point in points}) != len(points):
    raise RuntimeError('Duplicate electrical point IDs after revision 31.')

scene['interior_revision'] = 'LIBRARY 31.0 proposed appliance socket positions refined'
scene['electrical_revision'] = 31
POINTS_PATH.write_text(json.dumps(points, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def export_patch(layer_name, point_ids, filepath):
    for window in bpy.context.window_manager.windows:
        window.view_layer = scene.view_layers[layer_name]
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    expected_names = []
    for point_id in point_ids:
        assembly = object_assembly(point_id)
        if not assembly:
            raise RuntimeError(f'No geometry for {point_id}')
        for obj in assembly:
            obj.hide_set(False)
            obj.hide_render = False
            obj.select_set(True)
            expected_names.append(obj.name)
    bpy.context.view_layer.objects.active = bpy.data.objects[point_ids[0]]
    filepath.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(filepath), use_selection=True,
                              export_format='GLB', export_cameras=False, export_lights=False,
                              export_extras=True)
    if not filepath.is_file() or filepath.stat().st_size < 1024:
        raise RuntimeError(f'Failed to export {filepath}')
    return expected_names

patch1_names = export_patch('Ground_Design',
                            ['E1_005_SOCKET', 'E1_006_SOCKET', 'E1_010_SOCKET', 'E1_093_SOCKET'],
                            PATCH_FLOOR_1)
upper_patch_ids = [point['id'] for point in points
                   if point['level'] == 2 and point['type'] != 'LIGHT_POINT']
patch2_names = export_patch('Upper_Design', upper_patch_ids, PATCH_FLOOR_2)

# The bedroom and child-room points had correct locations but stale copied metadata.
for point_id in ['E2_080_SOCKET', 'E2_081_DATA', 'E2_082_SOCKET', 'E2_083_SWITCH', 'E2_084_SOCKET', 'E2_091_SWITCH']:
    root = bpy.data.objects.get(point_id)
    point = by_id.get(point_id)
    if root is not None and point is not None and root.get('point_id') != point_id:
        raise RuntimeError(f'Metadata alignment failed for {point_id}')

bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)
print(json.dumps({'revision': 31, 'changes': changes, 'metadata_repairs': metadata_repairs,
                  'patches': {'floor1': str(PATCH_FLOOR_1), 'floor2': str(PATCH_FLOOR_2)},
                  'patch_nodes': {'floor1': patch1_names, 'floor2': patch2_names}}, ensure_ascii=False))
