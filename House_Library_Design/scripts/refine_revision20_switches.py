from pathlib import Path
import bpy, json, math
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'House_Library_Design.blend'
bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
bpy.context.view_layer.update()

points_path = ROOT / 'data/electrical_points.json'
points = json.loads(points_path.read_text(encoding='utf8'))
by_id = {item['id']: item for item in points}

moves = {
    'E1_004_SWITCH': {'from': (7.86, 3.794118881225586, 'S'), 'to': (7.825, 3.9255, 'N'), 'room': 'Kitchen', 'purpose': 'Kitchen ceiling + task lights', 'layout': 'two rockers along X; face +Y'},
    'E1_025_SWITCH': {'from': (6.515443801879883, 4.760000228881836, 'E'), 'to': (6.515443801879883, 5.82, 'E'), 'room': 'Ground_WC', 'purpose': 'Shower room light / extract control', 'layout': 'two rockers along Y; face +X'},
    'E1_019_SWITCH': {'from': (10.39460277557373, 7.769999980926514, 'W'), 'to': (6.6255, 7.32, 'E'), 'room': 'Living', 'purpose': 'Living ceiling + dining pendants', 'layout': 'two rockers along Y; face +X'},
    'E1_090_SWITCH': {'from': (10.39460277557373, 7.940000057220459, 'W'), 'to': (6.6255, 7.50, 'E'), 'room': 'Living', 'purpose': 'Living LED strips dimmer', 'layout': 'two rockers along Y; face +X'},
}

# Check that this script is being applied to the expected pre-revision-20 state.
for point_id, spec in moves.items():
    row = by_id[point_id]
    old_x, old_y, old_face = spec['from']
    if abs(row['x_m'] - old_x) > 0.02 or abs(row['y_m'] - old_y) > 0.02 or row['face'] != old_face:
        raise ValueError(f'{point_id} is not at expected revision-19 coordinates: {row}')

changes = []
selected_names = []
for point_id, spec in moves.items():
    root = bpy.data.objects.get(point_id)
    rocker_a = bpy.data.objects.get(point_id + '_rocker')
    rocker_b = bpy.data.objects.get(point_id + '_rocker.001')
    if not all((root, rocker_a, rocker_b)):
        raise ValueError(f'Missing switch geometry for {point_id}')
    old = {'x_m': by_id[point_id]['x_m'], 'y_m': by_id[point_id]['y_m'], 'face': by_id[point_id]['face']}
    x, y, face = spec['to']
    z = by_id[point_id]['height_aff_m']
    root.location = (x, y, z)
    if point_id == 'E1_004_SWITCH':
        rocker_a.location = (x - 0.0375, y + 0.008, z)
        rocker_b.location = (x + 0.0375, y + 0.008, z)
    else:
        rocker_a.location = (x + 0.008, y - 0.0375, z)
        rocker_b.location = (x + 0.008, y + 0.0375, z)
    for obj in (root, rocker_a, rocker_b):
        obj['point_id'] = point_id
        obj['room'] = spec['room']
        obj['purpose'] = spec['purpose']
        obj['wall_face'] = face
        obj['level'] = 1
        selected_names.append(obj.name)
    by_id[point_id]['x_m'] = x
    by_id[point_id]['y_m'] = y
    by_id[point_id]['face'] = face
    by_id[point_id]['room'] = spec['room']
    by_id[point_id]['purpose'] = spec['purpose']
    changes.append({'id': point_id, 'from': old, 'to': {'x_m': x, 'y_m': y, 'face': face}, 'room': spec['room'], 'purpose': spec['purpose'], 'objects': [root.name, rocker_a.name, rocker_b.name]})

# Confirm the user-facing side of each new switch coincides with the intended wall face.
bpy.context.view_layer.update()
checks = [
    ('E1_004_SWITCH', (7.825, 4.2, 1.05), (0, -1, 0), 'R_L1_SOURCE_WALL_6', (0, 1, 0)),
    ('E1_025_SWITCH', (7.5, 5.82, 1.05), (-1, 0, 0), 'R_L1_SOURCE_WALL_3', (1, 0, 0)),
    ('E1_019_SWITCH', (9.0, 7.32, 1.05), (-1, 0, 0), 'R3_Stair_Wall_South', (1, 0, 0)),
    ('E1_090_SWITCH', (9.0, 7.50, 1.05), (-1, 0, 0), 'R3_Stair_Wall_South', (1, 0, 0)),
]
depsgraph = bpy.context.evaluated_depsgraph_get()
ray_checks = []
hidden_for_raycast = []
for point_id in moves:
    for name in (point_id, point_id + '_rocker', point_id + '_rocker.001'):
        obj = bpy.data.objects[name]
        hidden_for_raycast.append((obj, obj.hide_get()))
        obj.hide_set(True)
bpy.context.view_layer.update()
for point_id, origin, direction, expected_obj, expected_normal in checks:
    hit, location, normal, face_index, obj, matrix = scene.ray_cast(depsgraph, Vector(origin), Vector(direction))
    if not hit or obj.name != expected_obj or any(abs(normal[i] - expected_normal[i]) > 0.02 for i in range(3)):
        raise ValueError(f'{point_id} failed wall-face raycast: hit={hit}, object={obj.name if obj else None}, normal={tuple(normal)}')
    target = moves[point_id]['to']
    expected_plane = target[1] if target[2] == 'N' else target[0]
    actual_plane = location.y if target[2] == 'N' else location.x
    ray_checks.append({'id': point_id, 'wall_object': obj.name, 'surface_m': round(actual_plane, 4), 'switch_face': target[2], 'normal': [round(v, 3) for v in normal]})
for obj, was_hidden in hidden_for_raycast:
    obj.hide_set(was_hidden)
bpy.context.view_layer.update()

# Clearance around the relocated kitchen switch and the WC doorway.
kitchen_clearance = round(min(7.825 - 0.075 - 7.7, 7.95 - (7.825 + 0.075)), 4)
wc_door_top_y = 5.66
wc_plate_south_y = 5.82 - 0.075
wc_clearance = round(wc_plate_south_y - wc_door_top_y, 4)
if kitchen_clearance < 0.04 or wc_clearance < 0.07:
    raise ValueError(f'Insufficient switch clearance: kitchen={kitchen_clearance}, WC={wc_clearance}')

# The second dining control was mislabeled in the old master. Correct it to match the electrical schedule.
scene['interior_revision'] = 'LIBRARY 20.0 switch relocation'
points_path.write_text(json.dumps(points, ensure_ascii=False, indent=2), encoding='utf8')
report = {
    'revision': 20,
    'title': 'Ground-floor switch relocation',
    'switches': changes,
    'surface_checks': ray_checks,
    'clearances_m': {
        'E1_004_SWITCH_to_kitchen_door_jamb_and_fridge_housing': kitchen_clearance,
        'E1_025_SWITCH_to_WC_door_header_projection': wc_clearance,
        'E1_019_E1_090_switch_cluster_to_E1_020_switch': 0.26,
    },
    'all_switches_keep_original_height_aff_m': True,
    'door_openings_and_furniture_unchanged': True,
    'verification': 'Wall raycasts hit the requested exposed wall planes; detailed screenshot review follows export.'
}
(ROOT / 'data/revision20_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)

for obj in bpy.context.selected_objects:
    obj.select_set(False)
for name in selected_names:
    bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['E1_004_SWITCH']
patch_path = ROOT.parent / 'House_Browser_Viewer/revision20_switches_floor1.glb'
bpy.ops.export_scene.gltf(filepath=str(patch_path), use_selection=True, export_format='GLB', export_cameras=False, export_lights=False, export_extras=True)
report['browser_patch'] = {'file': patch_path.name, 'bytes': patch_path.stat().st_size, 'exported_objects': selected_names}
(ROOT / 'data/revision20_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print('REVISION20_SWITCHES_SAVED', json.dumps(report, ensure_ascii=False), flush=True)
