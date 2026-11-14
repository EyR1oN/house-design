from pathlib import Path
import bpy, json, math
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'House_Library_Design.blend'
POINTS_PATH = ROOT / 'data' / 'electrical_points.json'
REPORT_PATH = ROOT / 'data' / 'revision25_report.json'
PATCH_PATH = ROOT.parent / 'House_Browser_Viewer' / 'revision25_switches_floor1.glb'

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
bpy.context.window.view_layer = scene.view_layers['Ground_Design']
bpy.context.view_layer.update()

points = json.loads(POINTS_PATH.read_text(encoding='utf8'))
by_id = {p['id']: p for p in points}
if len(by_id) != len(points):
    raise ValueError('Duplicate IDs in electrical point schedule')
if 'E1_091_SWITCH' in by_id or 'E1_092_SWITCH' in by_id:
    raise ValueError('Revision 25 switch IDs are already in use')

# Move the pantry light switch onto the short TV-wall strip between the storage
# door frame and the TV screen. The switch face points into the living room (+X).
storage_id = 'E1_020_SWITCH'
storage = by_id[storage_id]
if storage['face'] != 'E' or abs(storage['x_m'] - 6.6255) > 0.01 or abs(storage['y_m'] - 7.91) > 0.01:
    raise ValueError(f'Unexpected original storage switch location: {storage}')
storage_xy = (6.6415, 8.775)
storage_surface_x = 6.636
storage_root = bpy.data.objects[storage_id]
storage_rocker = bpy.data.objects[storage_id + '_rocker']
storage_root.location = (storage_xy[0], storage_xy[1], storage['height_aff_m'])
storage_root.rotation_euler = (0, 0, 0)
storage_rocker.location = (storage_xy[0] + 0.008, storage_xy[1], storage['height_aff_m'])
storage_rocker.rotation_euler = (0, 0, 0)
storage.update({'x_m': storage_xy[0], 'y_m': storage_xy[1]})
for obj in (storage_root, storage_rocker):
    obj['point_id'] = storage_id
    obj['room'] = 'Stair_storage'
    obj['purpose'] = 'Storage light'
    obj['wall_face'] = 'E'

# Add a second control location at the stair end of the TV wall. Each double
# rocker is paired with the corresponding living-room switch at the dining side.
new_points = [
    {
        'id': 'E1_091_SWITCH', 'room': 'Living', 'level': 1, 'type': 'SWITCH',
        'x_m': 6.6415, 'y_m': 10.48, 'height_aff_m': 1.05, 'face': 'E',
        'purpose': 'Living ceiling + dining pendants; stair-side second control',
        'proposed_group': 'GROUND_LIGHT', 'modules': 2,
        'status': 'PROPOSED_NOT_AS_BUILT', 'control_pair_with': 'E1_019_SWITCH',
        'control_type': 'PROPOSED_MULTI_WAY_SECOND_LOCATION'
    },
    {
        'id': 'E1_092_SWITCH', 'room': 'Living', 'level': 1, 'type': 'SWITCH',
        'x_m': 6.6415, 'y_m': 10.68, 'height_aff_m': 1.05, 'face': 'E',
        'purpose': 'Living LED strips dimmer; stair-side second control',
        'proposed_group': 'GROUND_LIGHT', 'modules': 2,
        'status': 'PROPOSED_NOT_AS_BUILT', 'control_pair_with': 'E1_090_SWITCH',
        'control_type': 'PROPOSED_MULTI_WAY_SECOND_LOCATION'
    }
]
templates = {
    'root': bpy.data.objects['E1_019_SWITCH'],
    'rocker_a': bpy.data.objects['E1_019_SWITCH_rocker'],
    'rocker_b': bpy.data.objects['E1_019_SWITCH_rocker.001']
}
for point in new_points:
    pid = point['id']
    if pid in bpy.data.objects:
        raise ValueError(f'Blender object already exists: {pid}')
    y = point['y_m']
    z = point['height_aff_m']
    positions = {
        'root': (point['x_m'], y, z),
        'rocker_a': (point['x_m'] + 0.008, y - 0.0375, z),
        'rocker_b': (point['x_m'] + 0.008, y + 0.0375, z)
    }
    names = {
        'root': pid,
        'rocker_a': pid + '_rocker',
        'rocker_b': pid + '_rocker.001'
    }
    for key, template in templates.items():
        obj = template.copy()
        obj.data = template.data
        obj.name = names[key]
        obj.location = positions[key]
        obj.rotation_euler = (0, 0, 0)
        target_collection = template.users_collection[0]
        target_collection.objects.link(obj)
        obj['point_id'] = pid
        obj['room'] = 'Living'
        obj['purpose'] = point['purpose']
        obj['wall_face'] = 'E'
        obj['level'] = 1
        if key == 'root':
            obj['device_type'] = 'SWITCH'
            obj['height_above_finished_floor_m'] = z
            obj['circuit_group_proposed'] = 'GROUND_LIGHT'
            obj['as_built_verified'] = False
            obj['mep_status'] = 'PROPOSED_POSITION_ONLY'
    points.append(point)
    by_id[pid] = point

# Confirm the three wall faces in the actual ground-floor scene before export.
hidden = []
for obj in bpy.context.view_layer.objects:
    if obj.name.startswith('E1_') and 'SWITCH' in obj.name:
        hidden.append((obj, obj.hide_get()))
        obj.hide_set(True)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
checks = []
for pid, y, expected_object, expected_x in [
    (storage_id, storage_xy[1], 'R7_TV_Continuous_Plaster', storage_surface_x),
    ('E1_091_SWITCH', 10.48, 'R7_TV_Continuous_Plaster', 6.636),
    ('E1_092_SWITCH', 10.68, 'R7_TV_Continuous_Plaster', 6.636)
]:
    hit, loc, norm, face_index, obj, matrix = scene.ray_cast(
        depsgraph, Vector((7.1, y, 1.05)), Vector((-1, 0, 0)), distance=2.0)
    if not hit or obj.name != expected_object or abs(loc.x - expected_x) > 0.003 or norm.x < 0.98:
        raise ValueError(f'{pid} does not meet its intended wall: hit={hit}, object={obj.name if obj else None}, loc={tuple(loc)}, normal={tuple(norm)}')
    checks.append({'id': pid, 'wall_object': obj.name,
                   'surface_m': [round(v, 4) for v in loc],
                   'normal': [round(v, 3) for v in norm]})
for obj, was_hidden in hidden:
    obj.hide_set(was_hidden)
bpy.context.view_layer.update()

# Keep a verified minimum gap around the relocated single-gang plate.
clearances = {
    'storage_switch_to_storage_door_frame_m': round((storage_xy[1] - 0.0375) - 8.68, 4),
    'storage_switch_to_tv_screen_m': round(8.95 - (storage_xy[1] + 0.0375), 4),
    'tv_wall_end_to_stair_switch_group_m': round(10.81 - (10.68 + 0.075), 4),
    'gap_between_stair_side_switch_plates_m': round((10.68 - 0.075) - (10.48 + 0.075), 4)
}
if min(clearances.values()) < 0.03:
    raise ValueError(f'Switch plates lack a 30 mm separation margin: {clearances}')

POINTS_PATH.write_text(json.dumps(points, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
scene['interior_revision'] = 'LIBRARY 25.0 pantry and stair-side living switches'
scene['electrical_design_note'] = 'All electrical points remain proposed positions; stair-side living controls are proposed multi-way pairs.'
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)

# Export only the changed/new switch assemblies for a non-destructive GLB patch.
for obj in bpy.context.selected_objects:
    obj.select_set(False)
export_names = []
for pid, count in [(storage_id, 1), ('E1_091_SWITCH', 2), ('E1_092_SWITCH', 2)]:
    names = [pid, pid + '_rocker'] + ([pid + '_rocker.001'] if count == 2 else [])
    for name in names:
        obj = bpy.data.objects[name]
        obj.select_set(True)
        export_names.append(name)
bpy.context.view_layer.objects.active = bpy.data.objects[storage_id]
PATCH_PATH.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(PATCH_PATH), use_selection=True,
                          export_format='GLB', export_cameras=False,
                          export_lights=False, export_extras=True)

report = {
    'revision': 25,
    'title': 'Pantry switch moved between storage door and TV; living light controls added by stairs',
    'proposed_multi_way_pairs': [
        {'stair_side': 'E1_091_SWITCH', 'dining_side': 'E1_019_SWITCH', 'circuit': 'Living ceiling + dining pendants'},
        {'stair_side': 'E1_092_SWITCH', 'dining_side': 'E1_090_SWITCH', 'circuit': 'Living LED strips dimmer'}
    ],
    'switches': [
        {'id': storage_id, 'old': {'x_m': 6.6255, 'y_m': 7.91, 'face': 'E'},
         'to': {'x_m': storage_xy[0], 'y_m': storage_xy[1], 'face': 'E'},
         'objects': [storage_id, storage_id + '_rocker']},
        *[{'id': p['id'], 'to': {'x_m': p['x_m'], 'y_m': p['y_m'], 'face': p['face']},
           'pair_with': p['control_pair_with'], 'purpose': p['purpose'],
           'objects': [p['id'], p['id'] + '_rocker', p['id'] + '_rocker.001']} for p in new_points]
    ],
    'surface_checks': checks,
    'clearances_m': clearances,
    'all_switches_height_aff_m': 1.05,
    'status': 'PROPOSED_NOT_AS_BUILT',
    'export_patch': {'file': PATCH_PATH.name, 'objects': export_names}
}
REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print('REVISION25_SWITCH_LAYOUT', json.dumps(report, ensure_ascii=False), flush=True)
