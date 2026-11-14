"""Remove stale child-bed switch triangles, correct socket extras, rebuild viewer."""
from pathlib import Path
import json
import math
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
from open_stair_exit_viewer import read_glb, write_glb, accessor
from build_viewer import build as build_viewer

viewer = ROOT / 'House_Browser_Viewer'
glb_path = viewer / 'House_Floor_2.glb'
backup_glb = ROOT / '.local-preview/pre-revision23/House_Browser_Viewer/House_Floor_2.glb'
schedule_path = ROOT / 'House_Library_Design/data/electrical_points.json'
report_path = ROOT / 'House_Library_Design/data/revision23_report.json'
if not backup_glb.is_file():
    raise FileNotFoundError('Create .local-preview/pre-revision23 before patching the GLB')

document, binary = read_glb(glb_path.read_bytes())
schedule = json.loads(schedule_path.read_text(encoding='utf-8'))
by_id = {point['id']: point for point in schedule}
aggregate = next((node for node in document['nodes']
                  if node.get('name') == 'PART_DESIGN_Child_Room'), None)
if aggregate is None or 'mesh' not in aggregate:
    raise ValueError('The active child-room aggregate mesh is missing')

# GLB uses floor-relative Y. This is the precise three-rocker plate that was
# removed from the Blender source but survived inside the older room aggregate.
target = {
    'x': (5.48, 5.515),
    'y': (1.0, 1.16),
    'z': (-2.44, -2.16),
}
mesh = document['meshes'][aggregate['mesh']]
primitive_data = []
removed_by_primitive = []
for primitive in mesh['primitives']:
    if primitive.get('mode', 4) != 4 or 'indices' not in primitive:
        raise ValueError('Child-room aggregate must use indexed triangles')
    positions = accessor(document, binary, primitive['attributes']['POSITION'])
    index_accessor = primitive['indices']
    indices = [row[0] for row in accessor(document, binary, index_accessor)]
    component_type = document['accessors'][index_accessor]['componentType']
    index_format = {5121: 'B', 5123: 'H', 5125: 'I'}[component_type]
    remove_faces = set()
    for face in range(len(indices) // 3):
        tri = [positions[indices[face * 3 + j]] for j in range(3)]
        inside = all(
            target[axis][0] <= vertex[coordinate] <= target[axis][1]
            for vertex in tri
            for axis, coordinate in (('x', 0), ('y', 1), ('z', 2))
        )
        if inside:
            remove_faces.add(face)
    primitive_data.append((primitive, indices, index_format, remove_faces, positions))
    removed_by_primitive.append({
        'material': primitive.get('material'),
        'faces_removed': len(remove_faces),
        'faces_before': len(indices) // 3,
    })

removed_total = sum(len(item[3]) for item in primitive_data)
if removed_total != 752 or [entry['faces_removed'] for entry in removed_by_primitive] != [188, 0, 564]:
    raise ValueError(f'Expected exactly 752 stale switch faces, got {removed_by_primitive}')

# Correct canonical metadata on standalone socket roots; a previous GLB merge
# inherited bedroom metadata even though the geometry was placed in the child room.
metadata_roots = ['E2_080_SOCKET', 'E2_082_SOCKET', 'E2_084_SOCKET']
for point_id in metadata_roots:
    point = by_id.get(point_id)
    node = next((item for item in document['nodes'] if item.get('name') == point_id), None)
    if point is None or node is None:
        raise ValueError(f'Missing schedule or GLB root for {point_id}')
    node['extras'] = {
        'design_status': 'PROPOSED_INTERIOR',
        'section': 'RIGHT',
        'level': point['level'],
        'point_id': point['id'],
        'room': point['room'],
        'device_type': point['type'],
        'purpose': point['purpose'],
        'height_above_finished_floor_m': point['height_aff_m'],
        'circuit_group_proposed': point['proposed_group'],
        'wall_face': point['face'],
        'modules': point['modules'],
        'as_built_verified': False,
        'mep_status': 'PROPOSED_POSITION_ONLY',
        'revision': 23,
        'electrical_point': True,
    }

append_offset = (len(binary) + 3) & ~3
binary += b'\0' * (append_offset - len(binary))
for primitive, indices, index_format, remove_faces, _ in primitive_data:
    if not remove_faces:
        continue
    remaining = [value for face in range(len(indices) // 3) if face not in remove_faces
                 for value in indices[face * 3:face * 3 + 3]]
    packed = struct.pack('<' + index_format * len(remaining), *remaining)
    view_index = len(document.setdefault('bufferViews', []))
    document['bufferViews'].append({
        'buffer': 0,
        'byteOffset': append_offset,
        'byteLength': len(packed),
        'target': 34963,
    })
    accessor_index = len(document.setdefault('accessors', []))
    document['accessors'].append({
        'bufferView': view_index,
        'componentType': document['accessors'][primitive['indices']]['componentType'],
        'count': len(remaining),
        'type': 'SCALAR',
        'min': [min(remaining)],
        'max': [max(remaining)],
    })
    primitive['indices'] = accessor_index
    binary += packed
    append_offset += len(packed)
    aligned = (append_offset + 3) & ~3
    binary += b'\0' * (aligned - len(binary))
    append_offset = aligned

aggregate.setdefault('extras', {})['stale_switch_geometry_removed_revision'] = 23
scene = document['scenes'][document.get('scene', 0)]
scene_extras = scene.setdefault('extras', {})
scene_extras['interior_revision'] = 'LIBRARY 23.0 child switch aggregate cleanup and fixed light visibility'
scene_extras['child_room_switch_cleanup'] = {
    'revision': 23,
    'removed_device': 'E2_085_SWITCH',
    'removed_triangles': removed_total,
    'removed_by_primitive': removed_by_primitive,
    'scope_glb_bounds_m': {
        'x': list(target['x']), 'floor_relative_y': list(target['y']), 'z': list(target['z'])
    },
}

output = write_glb(document, binary)
temporary = glb_path.with_suffix('.revision23.tmp')
temporary.write_bytes(output)
temporary.replace(glb_path)

report = {
    'revision': 23,
    'removed_stale_child_bed_switch': 'E2_085_SWITCH',
    'removed_switch_triangles': removed_total,
    'removed_switch_triangles_by_primitive': removed_by_primitive,
    'standalone_socket_metadata_corrected': metadata_roots,
    'stationary_light_rule': 'Preserve all fixed LIB lamp/pendant/sconce/light fixtures, ceiling structures, and R15 built-in hood lights; hide only office task lamps.',
}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
html_path = viewer / 'House_Viewer.html'
build_viewer(html_path)
print(json.dumps({**report, 'viewer_rebuilt': str(html_path)}, ensure_ascii=False))
