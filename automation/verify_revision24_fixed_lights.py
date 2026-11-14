"""Verify revision 23 switch cleanup, child points, metadata, and fixed-light nodes."""
from pathlib import Path
import base64
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
from open_stair_exit_viewer import read_glb, accessor

point_path = ROOT / 'House_Library_Design/data/electrical_points.json'
points = json.loads(point_path.read_text(encoding='utf-8'))
by_id = {point['id']: point for point in points}
child_points = sorted(point['id'] for point in points if point.get('room') == 'Child_Room')
expected_child = ['E2_080_SOCKET', 'E2_081_DATA', 'E2_082_SOCKET', 'E2_083_SWITCH', 'E2_084_SOCKET']
assert child_points == expected_child, child_points
assert 'E2_085_SWITCH' not in by_id

svg_path = ROOT / 'House_Library_Design/exports/Electrical_Points_Floor_2.svg'
svg = svg_path.read_text(encoding='utf-8')
assert all(svg.count(point_id) == 1 for point_id in expected_child)
assert 'E2_085_SWITCH' not in svg

doc, binary = read_glb((ROOT / 'House_Browser_Viewer/House_Floor_2.glb').read_bytes())
active = set()

def visit(index):
    if index in active:
        return
    active.add(index)
    for child in doc['nodes'][index].get('children', []):
        visit(child)

for index in doc['scenes'][doc.get('scene', 0)].get('nodes', []):
    visit(index)
active_names = [doc['nodes'][index].get('name', '') for index in active]
assert len(active_names) == len(set(active_names)), 'Duplicate active node names'
assert not any(name.startswith('E2_085_SWITCH') for name in active_names)

def node(name):
    return next(doc['nodes'][index] for index in active if doc['nodes'][index].get('name') == name)

# The removed plate's obsolete mesh faces lived inside this unnamed room aggregate.
aggregate = node('PART_DESIGN_Child_Room')
mesh = doc['meshes'][aggregate['mesh']]
target = {'x': (5.48, 5.515), 'y': (1.0, 1.16), 'z': (-2.44, -2.16)}
remaining_target_faces = 0
for primitive in mesh['primitives']:
    positions = accessor(doc, binary, primitive['attributes']['POSITION'])
    indices = [row[0] for row in accessor(doc, binary, primitive['indices'])]
    for offset in range(0, len(indices), 3):
        tri = [positions[indices[offset + j]] for j in range(3)]
        center = [sum(vertex[axis] for vertex in tri) / 3 for axis in range(3)]
        is_target = (target['x'][0] <= center[0] <= target['x'][1]
                     and target['y'][0] <= center[1] <= target['y'][1]
                     and target['z'][0] <= center[2] <= target['z'][1]
                     and all(target['x'][0] <= vertex[0] <= target['x'][1] for vertex in tri))
        remaining_target_faces += int(is_target)
assert remaining_target_faces == 0, f'{remaining_target_faces} faces remain at the removed switch location'

expected_roots = {
    'E2_080_SOCKET': (8.319, 1.1, -1.1),
    'E2_082_SOCKET': (5.4955458641, 0.95, -2.6),
}
for point_id, expected_xyz in expected_roots.items():
    root = node(point_id)
    assert math.dist(root.get('translation', []), expected_xyz) < 0.002, (point_id, root.get('translation'))
    extras = root.get('extras', {})
    point = by_id[point_id]
    assert extras.get('point_id') == point_id
    assert extras.get('room') == point['room']
    assert extras.get('purpose') == point['purpose']
    assert abs(extras.get('height_above_finished_floor_m', -999) - point['height_aff_m']) < 1e-6

fixed_floor1 = [
    'R18_Ceiling_L1',
    'LIB_Pendant_Dining1_Inner Bulb_PREPARED', 'LIB_Pendant_Dining1_Cube_PREPARED',
    'LIB_Pendant_Dining1_Circle.003_PREPARED', 'LIB_Pendant_Dining1_Circle.002_PREPARED',
    'LIB_Pendant_Dining2_Inner Bulb_PREPARED', 'LIB_Pendant_Dining2_Cube_PREPARED',
    'LIB_Pendant_Dining2_Circle.003_PREPARED', 'LIB_Pendant_Dining2_Circle.002_PREPARED',
    'R15_Hood_Underside_Light_6.233', 'R15_Hood_Underside_Light_6.747',
    'LIB_Ground_Flush_Entry', 'LIB_Ground_Flush_Kitchen', 'LIB_Ground_Flush_Laundry',
    'LIB_Ground_Flush_Living_Dining', 'LIB_Ground_Flush_WC',
]
doc1, _ = read_glb((ROOT / 'House_Browser_Viewer/House_Floor_1.glb').read_bytes())
active1 = set()

def visit1(index):
    if index in active1:
        return
    active1.add(index)
    for child in doc1['nodes'][index].get('children', []):
        visit1(child)

for index in doc1['scenes'][doc1.get('scene', 0)].get('nodes', []):
    visit1(index)
names1 = {doc1['nodes'][index].get('name', '') for index in active1}
for name in fixed_floor1:
    assert name in names1, f'Fixed ground-floor light missing from GLB: {name}'

fixed_floor2 = [
    'R18_Ceiling_L2', 'LIB_Pendant_Bedroom', 'LIB_Bedroom_Bedside_Pendant_8.82',
    'LIB_Bedroom_Bedside_Pendant_11.2', 'LIB_Pendant_Office',
    'LIB_Upper_Bath_Sconce_9.06', 'LIB_Upper_Bath_Sconce_10.44',
    'LIB_Upper_Hall_Flush', 'LIB_Upper_Bath_Flush', 'LIB_Closet_Flush',
]
for name in fixed_floor2:
    assert name in active_names, f'Fixed upper-floor light missing from GLB: {name}'

for document, data in ((doc, binary), (doc1, _)):
    assert all(view.get('byteOffset', 0) + view['byteLength'] <= len(data)
               for view in document.get('bufferViews', [])), 'GLB bufferView is out of range'

viewer_html = (ROOT / 'House_Browser_Viewer/House_Viewer.html').read_text(encoding='utf-8')
marker = 'window.HOUSE_DATA='
payload_start = viewer_html.index(marker) + len(marker)
viewer_data, _end = json.JSONDecoder().raw_decode(viewer_html[payload_start:])
assert len(viewer_data['photos']) == 36
for floor, expected_data in ((1, (ROOT / 'House_Browser_Viewer/House_Floor_1.glb').read_bytes()),
                             (2, (ROOT / 'House_Browser_Viewer/House_Floor_2.glb').read_bytes())):
    embedded = base64.b64decode(viewer_data['models'][str(floor)])
    assert embedded == expected_data, f'Offline viewer floor {floor} differs from the GLB file'
assert 'R15_Hood_Underside_Light_' in viewer_html
assert '(?:lamp|pendant|sconce|light|flush)' in viewer_html

result = {
    'revision': 24,
    'child_room_points_match_schedule': child_points,
    'stale_bed_switch_mesh_faces_remaining': remaining_target_faces,
    'standalone_socket_metadata_matches_schedule': True,
    'fixed_light_nodes_present_on_both_floors': fixed_floor1 + fixed_floor2,
    'flush_ceiling_lights_included': True,
    'glb_buffer_views_in_range': True,
    'offline_viewer_matches_both_models_and_36_renders': True,
}
(ROOT / 'House_Library_Design/data/revision24_verification.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
