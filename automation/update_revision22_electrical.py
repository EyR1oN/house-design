"""Merge restored child electrical nodes into floor 2 and rebuild the offline viewer."""
from pathlib import Path
import json
import math
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
from open_stair_exit_viewer import read_glb, write_glb, accessor
from build_viewer import build as build_viewer

viewer = ROOT / 'House_Browser_Viewer'
base_path = viewer / 'House_Floor_2.glb'
patch_path = viewer / 'revision22_child_electrical.glb'
point_path = ROOT / 'House_Library_Design' / 'data' / 'electrical_points.json'
report_path = ROOT / 'House_Library_Design' / 'data' / 'revision22_report.json'

document, binary = read_glb(base_path.read_bytes())
patch, patch_binary = read_glb(patch_path.read_bytes())


def reachable(doc):
    seen = set()

    def visit(index):
        if index in seen:
            return
        seen.add(index)
        for child in doc['nodes'][index].get('children', []):
            visit(child)

    scene = doc['scenes'][doc.get('scene', 0)]
    for index in scene.get('nodes', []):
        visit(index)
    return seen


def active_names(doc):
    return [doc['nodes'][i].get('name', '') for i in reachable(doc)]


base_active = reachable(document)
patch_active = reachable(patch)
patch_names = {patch['nodes'][i].get('name') for i in patch_active}
expected_names = {
    'E2_080_SOCKET',
    'E2_080_SOCKET_hole',
    'E2_080_SOCKET_hole.001',
    'E2_080_SOCKET_hole.002',
    'E2_080_SOCKET_hole.003',
    'E2_082_SOCKET',
    'E2_082_SOCKET_hole',
    'E2_082_SOCKET_hole.001',
    'E2_082_SOCKET_hole.002',
    'E2_082_SOCKET_hole.003',
}
if patch_names != expected_names:
    raise ValueError(f'Unexpected Blender patch nodes: missing={expected_names - patch_names}, extra={patch_names - expected_names}')

old_names = active_names(document)
if any(name in old_names for name in expected_names):
    raise ValueError('The two child socket assemblies already exist in floor 2; refusing to add duplicates')
if any(name.startswith('E2_085_SWITCH') for name in old_names):
    raise ValueError('An active E2_085 switch node remains in the floor-2 GLB')

# The earlier merged electrical mesh did not contain the E2_085 switch either.
# Check its coordinates explicitly to ensure it cannot remain as anonymous geometry.
removed_switch = (5.4955458641, 1.1, -2.3)
electrical = next((n for n in document['nodes'] if n.get('name') == 'PART_Electrical_L2'), None)
if electrical is None:
    raise ValueError('PART_Electrical_L2 was not found')
nearest = math.inf
for primitive in document['meshes'][electrical['mesh']]['primitives']:
    positions = accessor(document, binary, primitive['attributes']['POSITION'])
    for vertex in positions:
        nearest = min(nearest, math.dist(vertex, removed_switch))
if nearest < 0.3:
    raise ValueError(f'Anonymous electrical geometry remains at E2_085 location (nearest vertex {nearest:.3f} m)')

# Append the Blender-exported patch and remap all GLB references.
offsets = {}
keys = ['bufferViews', 'accessors', 'images', 'samplers', 'textures', 'materials', 'meshes', 'nodes']
for key in keys:
    offsets[key] = len(document.get(key, []))
binary_offset = (len(binary) + 3) & ~3
binary += b'\0' * (binary_offset - len(binary)) + patch_binary
for view in patch.get('bufferViews', []):
    view['buffer'] = 0
    view['byteOffset'] = view.get('byteOffset', 0) + binary_offset
for item in patch.get('accessors', []):
    if 'bufferView' in item:
        item['bufferView'] += offsets['bufferViews']
for item in patch.get('images', []):
    if 'bufferView' in item:
        item['bufferView'] += offsets['bufferViews']
for item in patch.get('textures', []):
    if 'source' in item:
        item['source'] += offsets['images']
    if 'sampler' in item:
        item['sampler'] += offsets['samplers']


def remap_textures(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith('Texture') and isinstance(child, dict) and 'index' in child:
                child['index'] += offsets['textures']
            else:
                remap_textures(child)
    elif isinstance(value, list):
        for child in value:
            remap_textures(child)


for material in patch.get('materials', []):
    remap_textures(material)
for mesh in patch.get('meshes', []):
    for primitive in mesh['primitives']:
        primitive['attributes'] = {
            key: index + offsets['accessors']
            for key, index in primitive['attributes'].items()
        }
        if 'indices' in primitive:
            primitive['indices'] += offsets['accessors']
        if 'material' in primitive:
            primitive['material'] += offsets['materials']

patch_roots = list(patch['scenes'][patch.get('scene', 0)].get('nodes', []))
for index, node in enumerate(patch.get('nodes', [])):
    if index in patch_roots:
        if 'matrix' in node:
            node['matrix'][13] -= 3.2
        else:
            node.setdefault('translation', [0, 0, 0])[1] -= 3.2
        node.setdefault('extras', {}).update(level=2, revision=22, electrical_point=True)
    if 'mesh' in node:
        node['mesh'] += offsets['meshes']
    if 'children' in node:
        node['children'] = [child + offsets['nodes'] for child in node['children']]

for key in keys:
    document.setdefault(key, []).extend(patch.get(key, []))
scene = document['scenes'][document.get('scene', 0)]
scene.setdefault('nodes', []).extend(index + offsets['nodes'] for index in patch_roots)
scene.setdefault('extras', {})['interior_revision'] = 'LIBRARY 22.0 child-room electrical points and switch cleanup'
for key in ('extensionsUsed', 'extensionsRequired'):
    if patch.get(key):
        document[key] = sorted(set(document.get(key, []) + patch[key]))

combined = reachable(document)
combined_names = [document['nodes'][i].get('name', '') for i in combined]
duplicates = sorted(name for name in set(combined_names) if combined_names.count(name) > 1)
if duplicates:
    raise ValueError(f'Duplicate active floor-2 node names: {duplicates[:10]}')
if not expected_names.issubset(combined_names):
    raise ValueError(f'Missing exported socket components: {sorted(expected_names - set(combined_names))}')
if any(name.startswith('E2_085_SWITCH') for name in combined_names):
    raise ValueError('E2_085 remains active after patch merge')
for view in document.get('bufferViews', []):
    if view.get('byteOffset', 0) + view['byteLength'] > len(binary):
        raise ValueError('GLB bufferView extends past binary data')

temporary = base_path.with_suffix('.revision22.tmp')
temporary.write_bytes(write_glb(document, binary))
temporary.replace(base_path)

points = json.loads(point_path.read_text(encoding='utf-8'))
child_ids = sorted(p['id'] for p in points if p.get('room') == 'Child_Room')
if 'E2_085_SWITCH' in child_ids or len(child_ids) != 5:
    raise ValueError(f'Unexpected child-room electrical schedule after cleanup: {child_ids}')

# The floor-2 SVG had never been brought forward with the newer child-room points.
svg_path = ROOT / 'House_Library_Design' / 'exports' / 'Electrical_Points_Floor_2.svg'
svg_lines = svg_path.read_text(encoding='utf-8').splitlines()
svg_text = '\n'.join(svg_lines)
svg_ids = ['E2_080_SOCKET', 'E2_081_DATA', 'E2_082_SOCKET', 'E2_083_SWITCH', 'E2_084_SOCKET']
present = {point_id for point_id in svg_ids if point_id in svg_text}
if present and present != set(svg_ids):
    raise ValueError(f'Floor-2 SVG has only part of the child electrical points: {sorted(present)}')
if not present:
    colors = {'SOCKET': '#ae6928', 'DATA': '#516dac', 'SWITCH': '#4a8263'}
    child_records = [p for p in points if p.get('id') in svg_ids]

    def svg_number(value):
        return f'{value:.3f}'.rstrip('0').rstrip('.')

    map_lines = []
    legend_lines = []
    legend_y_values = [int(value) for value in re.findall(
        r'<text x="970" y="(\d+)" font-size="17"', svg_text
    )]
    if not legend_y_values:
        raise ValueError('Floor-2 SVG legend rows were not found')
    legend_y = max(legend_y_values) + 35
    for point in child_records:
        pid = point['id']
        number = pid.split('_')[1]
        x = 183.5 + (point['x_m'] - 6.0) * 115.0
        y = 1660.0 - point['y_m'] * 115.0
        color = colors[point['type']]
        map_lines.append(
            f'<circle cx="{svg_number(x)}" cy="{svg_number(y)}" r="8" fill="{color}" stroke="#fff" stroke-width="2">'
            f'<title>{pid} / {point["purpose"]} / {point["height_aff_m"]:.2f}m</title></circle>'
        )
        label_y = y + 17 if pid == 'E2_083_SWITCH' else y - 7
        map_lines.append(
            f'<text x="{svg_number(x + 10)}" y="{svg_number(label_y)}" font-size="13" font-weight="bold" fill="{color}">{number}</text>'
        )
        if point['type'] == 'SOCKET':
            device = f'Розетка ×{point["modules"]}'
        elif point['type'] == 'SWITCH':
            device = f'Вимикач ×{point["modules"]}'
        else:
            device = 'Ethernet'
        legend_lines.append(
            f'<circle cx="953" cy="{legend_y - 6}" r="5" fill="{color}"/>'
            f'<text x="970" y="{legend_y}" font-size="17" fill="#39342d">{number} · Дитяча · {device} · {point["height_aff_m"]:.2f} м</text>'
        )
        legend_y += 35

    map_insert = next((i for i, line in enumerate(svg_lines) if '<text x="950" y="166"' in line), None)
    legend_insert = next((i for i, line in enumerate(svg_lines) if '<text x="80" y="1754"' in line), None)
    if map_insert is None or legend_insert is None:
        raise ValueError('Floor-2 SVG insertion anchors were not found')
    svg_lines[map_insert:map_insert] = map_lines
    legend_insert = next(i for i, line in enumerate(svg_lines) if '<text x="80" y="1754"' in line)
    svg_lines[legend_insert:legend_insert] = legend_lines
    svg_path.write_text('\n'.join(svg_lines) + '\n', encoding='utf-8')
    svg_text = '\n'.join(svg_lines)
if any(svg_text.count(pid) != 1 for pid in svg_ids):
    raise ValueError('Floor-2 SVG does not contain each retained child point exactly once')
if 'E2_085_SWITCH' in svg_text:
    raise ValueError('Removed E2_085 switch is still in the floor-2 SVG')

report = {
    'revision': 22,
    'title': 'Child-room electrical points restored; bedside switch removed',
    'restored_socket_assemblies': ['E2_080_SOCKET', 'E2_082_SOCKET'],
    'active_restored_components': sorted(expected_names),
    'removed_point': 'E2_085_SWITCH',
    'retained_child_room_points': child_ids,
    'office_task_lamps_hidden_in_electrical_mode': [
        'LIB_Office_Task_Lamp_1', 'LIB_Office_Task_Lamp_2'
    ],
    'preserved_ceiling_and_fixed_lighting': True,
    'floor2_active_node_count': len(combined),
    'floor2_electrical_svg_updated': str(svg_path.relative_to(ROOT)),
    'duplicate_active_node_names': 0,
    'switch_point_geometry_clearance_m': round(nearest, 4),
    'all_buffer_views_within_glb': True,
}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

html_path = viewer / 'House_Viewer.html'
build_viewer(html_path)
html = html_path.read_text(encoding='utf-8')
if '__HOUSE_DATA_JSON__' in html or '__FIRST_PERSON_SCRIPT__' in html:
    raise ValueError('Viewer template markers remain after rebuild')
if html.count('"mime":"image/png"') != 36:
    raise ValueError('The offline gallery does not contain all 36 photos')

print(json.dumps({
    'revision': 22,
    'floor2_nodes_added': len(expected_names),
    'floor2_active_nodes': len(combined),
    'retained_child_room_points': child_ids,
    'viewer_html_bytes': html_path.stat().st_size,
    'electrical_mesh_nearest_to_removed_switch_m': round(nearest, 4),
}, ensure_ascii=False))
