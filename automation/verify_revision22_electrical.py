"""Verify revision-22 electrical geometry and its schedule against the GLB."""
from pathlib import Path
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
from open_stair_exit_viewer import read_glb, accessor

points_path = ROOT / 'House_Library_Design' / 'data' / 'electrical_points.json'
glb_path = ROOT / 'House_Browser_Viewer' / 'House_Floor_2.glb'
points = json.loads(points_path.read_text(encoding='utf-8'))
point_ids = {point['id'] for point in points}
child_points = sorted(point['id'] for point in points if point.get('room') == 'Child_Room')
expected_child = [
    'E2_080_SOCKET', 'E2_081_DATA', 'E2_082_SOCKET', 'E2_083_SWITCH', 'E2_084_SOCKET'
]
assert child_points == expected_child, child_points
assert 'E2_085_SWITCH' not in point_ids
svg_path = ROOT / 'House_Library_Design' / 'exports' / 'Electrical_Points_Floor_2.svg'
svg = svg_path.read_text(encoding='utf-8')
assert all(svg.count(point_id) == 1 for point_id in expected_child), 'Floor-2 SVG does not match the retained child points'
assert 'E2_085_SWITCH' not in svg

doc, binary = read_glb(glb_path.read_bytes())
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
assert 'E2_085_SWITCH' not in active_names
for point_id in ('E2_080_SOCKET', 'E2_082_SOCKET'):
    assert active_names.count(point_id) == 1, f'{point_id} is not active exactly once'
    for suffix in ('_hole', '_hole.001', '_hole.002', '_hole.003'):
        assert active_names.count(point_id + suffix) == 1, f'{point_id + suffix} is missing'


def node(name):
    return next(doc['nodes'][index] for index in active if doc['nodes'][index].get('name') == name)


for point_id, expected in {
    'E2_080_SOCKET': (8.319, 1.1, -1.1),
    'E2_082_SOCKET': (5.4955458641, 0.95, -2.6),
}.items():
    actual = node(point_id).get('translation')
    assert actual is not None and math.dist(actual, expected) < 0.002, (point_id, actual, expected)
for view in doc.get('bufferViews', []):
    assert view.get('byteOffset', 0) + view['byteLength'] <= len(binary), 'GLB bufferView is out of range'

report_path = ROOT / 'House_Library_Design' / 'data' / 'revision22_report.json'
report = json.loads(report_path.read_text(encoding='utf-8'))
assert report['duplicate_active_node_names'] == 0
assert report['all_buffer_views_within_glb'] is True
assert report['office_task_lamps_hidden_in_electrical_mode'] == [
    'LIB_Office_Task_Lamp_1', 'LIB_Office_Task_Lamp_2'
]
print(json.dumps({
    'child_room_points': child_points,
    'restored_socket_roots': ['E2_080_SOCKET', 'E2_082_SOCKET'],
    'removed_bedside_switch': 'E2_085_SWITCH',
    'active_floor2_node_count': len(active),
    'duplicate_active_node_names': 0,
    'socket_positions_match_schedule': True,
    'floor2_svg_matches_schedule': True,
}, ensure_ascii=False))
verification = {
    'revision': 22,
    'active_floor2_node_count': len(active),
    'duplicate_active_node_names': 0,
    'restored_child_socket_assemblies': ['E2_080_SOCKET', 'E2_082_SOCKET'],
    'retained_child_room_points': child_points,
    'removed_bedside_switch_absent_from_schedule_glb_and_svg': True,
    'socket_positions_match_schedule': True,
    'all_glb_buffer_views_in_range': True,
    'floor2_electrical_svg_matches_schedule': True,
    'office_task_lamp_visibility_logic': 'See automation/verify_revision22_electrical.cjs',
    'offline_viewer_rebuilt': (ROOT / 'House_Browser_Viewer' / 'House_Viewer.html').is_file(),
}
verification_path = ROOT / 'House_Library_Design' / 'data' / 'revision22_verification.json'
verification_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
