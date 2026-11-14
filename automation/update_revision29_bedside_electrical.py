"""Replace the four revised bedside plates in the upper-floor GLB and rebuild the viewer."""
from pathlib import Path
import json
import math
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
from open_stair_exit_viewer import accessor, read_glb, write_glb
from build_viewer import build as build_viewer

VIEWER = ROOT / 'House_Browser_Viewer'
GLB_PATH = VIEWER / 'House_Floor_2.glb'
PATCH_PATH = ROOT / '.local-preview' / 'revision29_bedside_electrical.glb'
POINTS_PATH = ROOT / 'House_Library_Design' / 'data' / 'electrical_points.json'
SVG_PATH = ROOT / 'House_Library_Design' / 'exports' / 'Electrical_Points_Floor_2.svg'
REPORT_PATH = ROOT / 'House_Library_Design' / 'data' / 'revision29_report.json'
VERIFICATION_PATH = ROOT / 'House_Library_Design' / 'data' / 'revision29_verification.json'
BEDROOM_FLOOR_Z = 3.2

IDS = ('E2_028_SOCKET', 'E2_029_SOCKET', 'E2_030_SWITCH', 'E2_031_SWITCH')
OLD_REGIONS = {
    'E2_028_SOCKET': {'x': (10.86, 11.04), 'y': (0.62, 0.74), 'z': (-11.84, -11.80)},
    'E2_030_SWITCH': {'x': (10.86, 11.04), 'y': (0.92, 1.04), 'z': (-11.84, -11.80)},
    'E2_029_SOCKET': {'x': (11.37, 11.415), 'y': (0.62, 0.74), 'z': (-8.70, -8.50)},
    'E2_031_SWITCH': {'x': (11.37, 11.415), 'y': (0.92, 1.04), 'z': (-8.70, -8.50)},
}
EXPECTED_PATCH_NODES = {
    'E2_028_SOCKET', 'E2_028_SOCKET_hole', 'E2_028_SOCKET_hole.001',
    'E2_028_SOCKET_hole.002', 'E2_028_SOCKET_hole.003',
    'E2_029_SOCKET', 'E2_029_SOCKET_hole', 'E2_029_SOCKET_hole.001',
    'E2_029_SOCKET_hole.002', 'E2_029_SOCKET_hole.003',
    'E2_030_SWITCH', 'E2_030_SWITCH_rocker', 'E2_030_SWITCH_rocker.001',
    'E2_031_SWITCH', 'E2_031_SWITCH_rocker', 'E2_031_SWITCH_rocker.001',
}


def reachable(document):
    seen = set()

    def visit(index):
        if index in seen:
            return
        seen.add(index)
        for child in document['nodes'][index].get('children', []):
            visit(child)

    for root in document['scenes'][document.get('scene', 0)].get('nodes', []):
        visit(root)
    return seen


def in_box(point, bounds):
    return all(bounds[axis][0] <= point[index] <= bounds[axis][1]
               for index, axis in enumerate(('x', 'y', 'z')))


def remap_textures(value, offset):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith('Texture') and isinstance(child, dict) and 'index' in child:
                child['index'] += offset
            else:
                remap_textures(child, offset)
    elif isinstance(value, list):
        for child in value:
            remap_textures(child, offset)


points = json.loads(POINTS_PATH.read_text(encoding='utf-8'))
by_id = {point['id']: point for point in points}
if any(point_id not in by_id for point_id in IDS):
    raise ValueError('The bedside electrical schedule is missing a target point.')

document, binary = read_glb(GLB_PATH.read_bytes())
patch, patch_binary = read_glb(PATCH_PATH.read_bytes())
active = reachable(document)
active_names = [document['nodes'][index].get('name', '') for index in active]
if len(active_names) != len(set(active_names)):
    raise ValueError('The base upper-floor GLB already has duplicate active node names.')
if any(name.startswith(tuple(point_id for point_id in IDS)) for name in active_names):
    raise ValueError('A bedside electrical patch is already active; refusing to add a duplicate.')
patch_active = reachable(patch)
patch_names = {patch['nodes'][index].get('name', '') for index in patch_active}
if patch_names != EXPECTED_PATCH_NODES:
    raise ValueError(
        f'Unexpected bedside patch nodes: missing={sorted(EXPECTED_PATCH_NODES - patch_names)}, '
        f'extra={sorted(patch_names - EXPECTED_PATCH_NODES)}'
    )

electrical_node = next(
    (document['nodes'][index] for index in active
     if document['nodes'][index].get('name') == 'PART_Electrical_L2'),
    None,
)
if electrical_node is None or 'mesh' not in electrical_node:
    raise ValueError('The packed upper-floor electrical mesh is missing.')
electrical_mesh = document['meshes'][electrical_node['mesh']]
removed_by_primitive = []
removed_by_point = {point_id: 0 for point_id in IDS}
index_formats = {5121: 'B', 5123: 'H', 5125: 'I'}
for primitive_index, primitive in enumerate(electrical_mesh['primitives']):
    if primitive.get('mode', 4) != 4 or 'indices' not in primitive:
        raise ValueError('The packed electrical mesh contains an unsupported primitive.')
    positions = accessor(document, binary, primitive['attributes']['POSITION'])
    index_accessor = primitive['indices']
    indices = [row[0] for row in accessor(document, binary, index_accessor)]
    component_type = document['accessors'][index_accessor]['componentType']
    if component_type not in index_formats:
        raise ValueError(f'Unsupported electrical index component type: {component_type}')
    kept = []
    removed = {point_id: 0 for point_id in IDS}
    for face in range(len(indices) // 3):
        triangle = [positions[indices[face * 3 + part]] for part in range(3)]
        point_id = next((name for name, bounds in OLD_REGIONS.items()
                         if all(in_box(vertex, bounds) for vertex in triangle)), None)
        if point_id is None:
            kept.extend(indices[face * 3:face * 3 + 3])
        else:
            removed[point_id] += 1
            removed_by_point[point_id] += 1
    removed_count = len(indices) // 3 - len(kept) // 3
    removed_by_primitive.append({
        'primitive': primitive_index,
        'material': primitive.get('material'),
        'faces_before': len(indices) // 3,
        'faces_removed': removed_count,
    })
    if removed_count:
        packed = struct.pack('<' + index_formats[component_type] * len(kept), *kept)
        binary_offset = (len(binary) + 3) & ~3
        binary += b'\0' * (binary_offset - len(binary))
        view_index = len(document.setdefault('bufferViews', []))
        document['bufferViews'].append({
            'buffer': 0,
            'byteOffset': binary_offset,
            'byteLength': len(packed),
            'target': 34963,
        })
        accessor_index = len(document.setdefault('accessors', []))
        document['accessors'].append({
            'bufferView': view_index,
            'componentType': component_type,
            'count': len(kept),
            'type': 'SCALAR',
            'min': [min(kept)],
            'max': [max(kept)],
        })
        primitive['indices'] = accessor_index
        binary += packed
    if removed != {point_id: 0 for point_id in IDS}:
        removed_by_primitive[-1]['faces_removed_by_point'] = removed

if any(removed_by_point[point_id] == 0 for point_id in IDS):
    raise ValueError(f'Could not locate all four old plate assemblies: {removed_by_point}')

# Append the Blender-exported geometry and remap every glTF index into the base.
keys = ['bufferViews', 'accessors', 'images', 'samplers', 'textures', 'materials', 'meshes', 'nodes']
offsets = {key: len(document.get(key, [])) for key in keys}
binary_offset = (len(binary) + 3) & ~3
binary += b'\0' * (binary_offset - len(binary)) + patch_binary
for view in patch.get('bufferViews', []):
    view['buffer'] = 0
    view['byteOffset'] = view.get('byteOffset', 0) + binary_offset
for item in patch.get('accessors', []):
    if 'bufferView' in item:
        item['bufferView'] += offsets['bufferViews']
for image in patch.get('images', []):
    if 'bufferView' in image:
        image['bufferView'] += offsets['bufferViews']
for texture in patch.get('textures', []):
    if 'source' in texture:
        texture['source'] += offsets['images']
    if 'sampler' in texture:
        texture['sampler'] += offsets['samplers']
for material in patch.get('materials', []):
    remap_textures(material, offsets['textures'])
for mesh in patch.get('meshes', []):
    for primitive in mesh.get('primitives', []):
        primitive['attributes'] = {
            key: index + offsets['accessors']
            for key, index in primitive['attributes'].items()
        }
        if 'indices' in primitive:
            primitive['indices'] += offsets['accessors']
        if 'material' in primitive:
            primitive['material'] += offsets['materials']

patch_roots = list(patch['scenes'][patch.get('scene', 0)].get('nodes', []))
for index, node in enumerate(patch['nodes']):
    if 'mesh' in node:
        node['mesh'] += offsets['meshes']
    if 'children' in node:
        node['children'] = [child + offsets['nodes'] for child in node['children']]
    name = node.get('name', '')
    point_id = next((item for item in IDS if name == item or name.startswith(item + '_')), None)
    if point_id is None:
        continue
    point = by_id[point_id]
    if index in patch_roots:
        if 'matrix' in node:
            node['matrix'][13] -= BEDROOM_FLOOR_Z
        else:
            node.setdefault('translation', [0, 0, 0])[1] -= BEDROOM_FLOOR_Z
    node.setdefault('extras', {}).update({
        'design_status': 'PROPOSED_INTERIOR',
        'section': 'RIGHT',
        'level': 2,
        'point_id': point_id,
        'room': point['room'],
        'device_type': point['type'],
        'purpose': point['purpose'],
        'height_above_finished_floor_m': point['height_aff_m'],
        'circuit_group_proposed': point['proposed_group'],
        'wall_face': point['face'],
        'modules': point['modules'],
        'as_built_verified': False,
        'mep_status': 'PROPOSED_POSITION_ONLY',
        'revision': 29,
        'electrical_point': True,
    })

for key in keys:
    document.setdefault(key, []).extend(patch.get(key, []))
scene = document['scenes'][document.get('scene', 0)]
scene.setdefault('nodes', []).extend(index + offsets['nodes'] for index in patch_roots)
scene.setdefault('extras', {})['interior_revision'] = 'LIBRARY 29.0 primary-bedroom bedside electrical alignment'
scene['extras']['bedside_electrical_revision'] = 29
for key in ('extensionsUsed', 'extensionsRequired'):
    if patch.get(key):
        document[key] = sorted(set(document.get(key, []) + patch[key]))

# Update plan markers from the same coordinates recorded in the point schedule.
svg_lines = SVG_PATH.read_text(encoding='utf-8').splitlines()
updated_svg = set()
for point_id in IDS:
    point = by_id[point_id]
    map_x = 183.5 + (point['x_m'] - 6.0) * 115.0
    map_y = 1660.0 - point['y_m'] * 115.0
    circle_pattern = re.compile(
        r'(<circle cx=")[^"]+(" cy=")[^"]+(" r="8"[^>]*><title>'
        + re.escape(point_id)
        + r' / [^<]* / )[0-9.]+(m</title></circle>)'
    )
    circle_indexes = [i for i, line in enumerate(svg_lines) if point_id in line]
    if len(circle_indexes) != 1:
        raise ValueError(f'Expected one SVG marker for {point_id}, found {len(circle_indexes)}')
    idx = circle_indexes[0]
    line, count = circle_pattern.subn(
        lambda match: match.group(1) + f'{map_x:.3f}'.rstrip('0').rstrip('.')
        + match.group(2) + f'{map_y:.3f}'.rstrip('0').rstrip('.')
        + match.group(3) + f'{point["height_aff_m"]:.2f}' + match.group(4),
        svg_lines[idx],
    )
    if count != 1:
        raise ValueError(f'Could not rewrite SVG marker for {point_id}')
    svg_lines[idx] = line
    label_idx = idx + 1
    label_number = point_id.split('_')[1]
    if label_idx >= len(svg_lines) or f'>{label_number}</text>' not in svg_lines[label_idx]:
        raise ValueError(f'Missing SVG label after {point_id}')
    label_pattern = re.compile(
        r'(<text x=")[^"]+(" y=")[^"]+("[^>]*>)'
        + re.escape(label_number)
        + r'(</text>)'
    )
    svg_lines[label_idx], label_count = label_pattern.subn(
        lambda match: match.group(1) + f'{map_x + 10:.3f}'.rstrip('0').rstrip('.')
        + match.group(2) + f'{map_y - 7:.3f}'.rstrip('0').rstrip('.')
        + match.group(3) + label_number + match.group(4),
        svg_lines[label_idx],
    )
    if label_count != 1:
        raise ValueError(f'Could not rewrite SVG label for {point_id}')

    legend_indexes = [i for i, line in enumerate(svg_lines) if f'>{label_number} ·' in line]
    if len(legend_indexes) != 1:
        raise ValueError(f'Expected one SVG legend entry for {point_id}, found {len(legend_indexes)}')
    legend_idx = legend_indexes[0]
    legend_pattern = re.compile(r'(<text[^>]*>[^<]* · )[0-9.]+( м</text>)')
    svg_lines[legend_idx], legend_count = legend_pattern.subn(
        lambda match: match.group(1) + f'{point["height_aff_m"]:.2f}' + match.group(2),
        svg_lines[legend_idx],
    )
    if legend_count != 1:
        raise ValueError(f'Could not rewrite SVG legend height for {point_id}')
    updated_svg.add(point_id)
SVG_PATH.write_text('\n'.join(svg_lines) + '\n', encoding='utf-8')

# Confirm the plan's marker, nearby label and legend agree with the point schedule.
for point_id in IDS:
    point = by_id[point_id]
    label_number = point_id.split('_')[1]
    expected_x = 183.5 + (point['x_m'] - 6.0) * 115.0
    expected_y = 1660.0 - point['y_m'] * 115.0
    marker = next(line for line in svg_lines if f'<title>{point_id} / ' in line)
    label = next(line for line in svg_lines if f'>{label_number}</text>' in line)
    legend = next(line for line in svg_lines if f'>{label_number} ·' in line)
    marker_match = re.search(r'<circle cx="([0-9.]+)" cy="([0-9.]+)"', marker)
    label_match = re.search(r'<text x="([0-9.]+)" y="([0-9.]+)"', label)
    if not marker_match or not label_match:
        raise ValueError(f'Could not parse SVG marker or label for {point_id}')
    if (not math.isclose(float(marker_match.group(1)), expected_x, abs_tol=0.001)
            or not math.isclose(float(marker_match.group(2)), expected_y, abs_tol=0.001)
            or not math.isclose(float(label_match.group(1)), expected_x + 10, abs_tol=0.001)
            or not math.isclose(float(label_match.group(2)), expected_y - 7, abs_tol=0.001)
            or f'{point["height_aff_m"]:.2f} м</text>' not in legend):
        raise ValueError(f'SVG marker, label or legend is out of sync for {point_id}')

# Verify the old positions are clear in the retained combined electrical mesh.
for primitive in electrical_mesh['primitives']:
    positions = accessor(document, binary, primitive['attributes']['POSITION'])
    indices = [row[0] for row in accessor(document, binary, primitive['indices'])]
    for face in range(len(indices) // 3):
        triangle = [positions[indices[face * 3 + part]] for part in range(3)]
        if any(all(in_box(vertex, bounds) for vertex in triangle)
               for bounds in OLD_REGIONS.values()):
            raise ValueError('Old bedside plate geometry remains in the packed electrical mesh.')

active_after = reachable(document)
active_names_after = [document['nodes'][index].get('name', '') for index in active_after]
if len(active_names_after) != len(set(active_names_after)):
    raise ValueError('Duplicate active node names after bedside patch merge.')
if not EXPECTED_PATCH_NODES.issubset(active_names_after):
    raise ValueError('A component from the revised bedside electrical assemblies is missing.')
for point_id in IDS:
    node = next(document['nodes'][index] for index in active_after
                if document['nodes'][index].get('name') == point_id)
    translation = node.get('translation')
    if translation is None and 'matrix' in node:
        translation = [node['matrix'][12], node['matrix'][13], node['matrix'][14]]
    point = by_id[point_id]
    expected = [point['x_m'], point['height_aff_m'], -point['y_m']]
    if not translation or math.dist(translation, expected) > 0.002:
        raise ValueError(f'{point_id} GLB position mismatch: {translation} != {expected}')
    extras = node.get('extras', {})
    if extras.get('point_id') != point_id or extras.get('revision') != 29:
        raise ValueError(f'{point_id} GLB electrical metadata is incomplete.')
if not updated_svg == set(IDS):
    raise ValueError('The floor-2 electrical plan is missing revised bedside markers.')
for buffer_view in document.get('bufferViews', []):
    if buffer_view.get('byteOffset', 0) + buffer_view['byteLength'] > len(binary):
        raise ValueError('The upper GLB contains a buffer view beyond its binary payload.')

temporary = GLB_PATH.with_suffix('.revision29.tmp')
temporary.write_bytes(write_glb(document, binary))
temporary.replace(GLB_PATH)
build_viewer(VIEWER / 'House_Viewer.html')

table_top = 0.48
report = {
    'revision': 29,
    'date': '2026-11-14',
    'summary': 'Aligned both primary-bedroom bedside socket/switch pairs with their nightstands and lowered the bedside switches.',
    'layout': {
        'left_bedside': {
            'nightstand_center_xy_m': [11.087, 11.32],
            'point_center_xy_m': [11.394638, 11.32],
            'wall_face': 'W',
        },
        'right_bedside': {
            'nightstand_center_xy_m': [11.087, 8.78],
            'point_center_xy_m': [11.394638, 8.78],
            'wall_face': 'W',
        },
        'socket_center_height_m': 0.68,
        'switch_center_height_m': 0.82,
        'nightstand_top_height_m': table_top,
        'socket_center_above_tabletop_m': 0.20,
        'switch_center_above_tabletop_m': 0.34,
        'switch_to_socket_center_spacing_m': 0.14,
    },
    'points': {point_id: {
        'x_m': by_id[point_id]['x_m'],
        'y_m': by_id[point_id]['y_m'],
        'height_aff_m': by_id[point_id]['height_aff_m'],
        'face': by_id[point_id]['face'],
        'purpose': by_id[point_id]['purpose'],
    } for point_id in IDS},
    'old_packed_faces_removed': removed_by_point,
    'removed_faces_by_primitive': removed_by_primitive,
    'updated_artifacts': [
        'House_Library_Design/House_Library_Design.blend',
        'House_Library_Design/data/electrical_points.json',
        'House_Library_Design/exports/Electrical_Points_Floor_2.svg',
        'House_Browser_Viewer/House_Floor_2.glb',
        'House_Browser_Viewer/House_Viewer.html',
    ],
}
REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
verification = {
    'revision': 29,
    'all_four_points_match_schedule': True,
    'all_four_assemblies_active_in_glb': True,
    'all_four_glb_extras_match_schedule': True,
    'old_geometry_removed_from_electrical_aggregate': True,
    'all_floor_2_electrical_svg_markers_match_schedule': True,
    'all_floor_2_electrical_svg_labels_match_markers': True,
    'all_floor_2_electrical_svg_legend_heights_match_schedule': True,
    'active_glb_node_names_unique': True,
    'glb_buffer_views_in_range': True,
    'offline_viewer_rebuilt_from_current_models': True,
    'expected_new_glb_nodes': sorted(EXPECTED_PATCH_NODES),
    'old_assembly_triangles_removed': removed_by_point,
}
VERIFICATION_PATH.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'report': report, 'verification': verification}, ensure_ascii=False))
