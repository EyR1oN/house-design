from pathlib import Path
import json, re, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
from open_stair_exit_viewer import read_glb, write_glb
from build_viewer import build as build_viewer

viewer = ROOT / 'House_Browser_Viewer'
base_path = viewer / 'House_Floor_1.glb'
patch_path = viewer / 'revision20_switches_floor1.glb'
report_path = ROOT / 'House_Library_Design/data/revision20_report.json'
report = json.loads(report_path.read_text(encoding='utf8'))
expected = {name for item in report['switches'] for name in item['objects']}
base, base_bin = read_glb(base_path.read_bytes())
patch, patch_bin = read_glb(patch_path.read_bytes())

def reachable(document):
    seen = set()
    def visit(index):
        if index in seen:
            return
        seen.add(index)
        for child in document['nodes'][index].get('children', []):
            visit(child)
    for index in document['scenes'][document.get('scene', 0)]['nodes']:
        visit(index)
    return seen

old_active = reachable(base)
patch_active = reachable(patch)
patch_names = {patch['nodes'][i].get('name') for i in patch_active}
if patch_names != expected:
    raise ValueError(f'Patch nodes do not match switch object set: missing={expected-patch_names}, extra={patch_names-expected}')
removed = {i for i, node in enumerate(base['nodes']) if node.get('name') in expected}
removed_active_names = {base['nodes'][i].get('name') for i in removed if i in old_active}
if removed_active_names != expected:
    raise ValueError(f'Expected all prior switch nodes active: missing={expected-removed_active_names}')
for scene in base['scenes']:
    scene['nodes'] = [index for index in scene.get('nodes', []) if index not in removed]
for node in base['nodes']:
    if 'children' in node:
        node['children'] = [index for index in node['children'] if index not in removed]

patch_roots = list(patch['scenes'][patch.get('scene', 0)]['nodes'])
keys = ['bufferViews', 'accessors', 'images', 'samplers', 'textures', 'materials', 'meshes', 'nodes']
offsets = {key: len(base.get(key, [])) for key in keys}
binary_offset = (len(base_bin) + 3) & ~3
base_bin += b'\0' * (binary_offset - len(base_bin)) + patch_bin
for view in patch.get('bufferViews', []):
    view['buffer'] = 0
    view['byteOffset'] = view.get('byteOffset', 0) + binary_offset
for accessor in patch.get('accessors', []):
    if 'bufferView' in accessor:
        accessor['bufferView'] += offsets['bufferViews']
for image in patch.get('images', []):
    if 'bufferView' in image:
        image['bufferView'] += offsets['bufferViews']
for texture in patch.get('textures', []):
    if 'source' in texture:
        texture['source'] += offsets['images']
    if 'sampler' in texture:
        texture['sampler'] += offsets['samplers']

def offset_material_textures(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith('Texture') and isinstance(child, dict) and 'index' in child:
                child['index'] += offsets['textures']
            else:
                offset_material_textures(child)
    elif isinstance(value, list):
        for child in value:
            offset_material_textures(child)
for material in patch.get('materials', []):
    offset_material_textures(material)
for mesh in patch.get('meshes', []):
    for primitive in mesh['primitives']:
        primitive['attributes'] = {key: index + offsets['accessors'] for key, index in primitive['attributes'].items()}
        if 'indices' in primitive:
            primitive['indices'] += offsets['accessors']
        if 'material' in primitive:
            primitive['material'] += offsets['materials']
for node in patch['nodes']:
    node['extras'] = {**node.get('extras', {}), 'level': 1, 'revision': 20}
    if 'mesh' in node:
        node['mesh'] += offsets['meshes']
    if 'children' in node:
        node['children'] = [index + offsets['nodes'] for index in node['children']]
for key in keys:
    base.setdefault(key, []).extend(patch.get(key, []))
base['scenes'][base.get('scene', 0)]['nodes'].extend(index + offsets['nodes'] for index in patch_roots)
base['scenes'][base.get('scene', 0)].setdefault('extras', {})['interior_revision'] = 'LIBRARY 20.0 ground-floor switch relocation'
for key in ('extensionsUsed', 'extensionsRequired'):
    if patch.get(key):
        base[key] = sorted(set(base.get(key, []) + patch[key]))

active = reachable(base)
active_names = [base['nodes'][i].get('name') for i in active]
if len(active_names) != len(set(active_names)):
    raise ValueError('Duplicate active node names after replacing switches')
if not expected.issubset(active_names):
    raise ValueError(f'Missing active relocated switch nodes: {expected-set(active_names)}')
if sum(base['nodes'][i].get('extras', {}).get('pantry_role') == 'pivot' for i in active) != 20:
    raise ValueError('The 20 moving corner-pantry nodes were not preserved')
for view in base.get('bufferViews', []):
    if view.get('byteOffset', 0) + view['byteLength'] > len(base_bin):
        raise ValueError('A GLB bufferView exceeds its binary payload')

temporary = base_path.with_suffix('.revision20.tmp')
temporary.write_bytes(write_glb(base, base_bin))
temporary.replace(base_path)

# Keep the separate electrical plan aligned with the moved point coordinates.
points = {item['id']: item for item in json.loads((ROOT / 'House_Library_Design/data/electrical_points.json').read_text(encoding='utf8'))}
svg_path = ROOT / 'House_Library_Design/exports/Electrical_Points_Floor_1.svg'
lines = svg_path.read_text(encoding='utf8').splitlines()
map_xy = lambda x, y: (183.5 + (x - 6.0) * 115.0, 1660.0 - y * 115.0)
def fmt(value):
    return f'{value:.3f}'.rstrip('0').rstrip('.')
for point_id in ('E1_004_SWITCH', 'E1_025_SWITCH', 'E1_019_SWITCH'):
    row = points[point_id]
    x, y = map_xy(row['x_m'], row['y_m'])
    tag = re.compile(r'(<circle cx=")[^"]+(" cy=")[^"]+(" r="8"[^>]*><title>' + re.escape(point_id) + r' /.*?</title></circle>)')
    matches = [i for i, line in enumerate(lines) if tag.search(line)]
    if len(matches) != 1:
        raise ValueError(f'Expected one electrical SVG marker for {point_id}, found {len(matches)}')
    i = matches[0]
    lines[i] = tag.sub(lambda m: m.group(1) + fmt(x) + m.group(2) + fmt(y) + m.group(3), lines[i])
    marker = re.compile(r'(<text x=")[^"]+(" y=")[^"]+(" font-size="13"[^>]*>' + point_id.split('_')[1] + r'</text>)')
    if not marker.search(lines[i+1]):
        raise ValueError(f'Expected SVG marker label after {point_id}')
    lines[i+1] = marker.sub(lambda m: m.group(1) + fmt(x + 10) + m.group(2) + fmt(y - 7) + m.group(3), lines[i+1])
# E1_090 was added to the schedule after this SVG was first drawn; add it beside the relocated dining controls.
row = points['E1_090_SWITCH']
x, y = map_xy(row['x_m'], row['y_m'])
if not any('E1_090_SWITCH' in line for line in lines):
    marker_i = next(i for i, line in enumerate(lines) if '<circle cx="953"' in line)
    lines[marker_i:marker_i] = [
        f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="8" fill="#4a8263" stroke="#fff" stroke-width="2"><title>E1_090_SWITCH / Living LED strips dimmer / 1.05m</title></circle>',
        f'<text x="{fmt(x + 10)}" y="{fmt(y - 7)}" font-size="13" font-weight="bold" fill="#4a8263">090</text>',
    ]
    legend_i = next(i for i, line in enumerate(lines) if '<circle cx="953" cy="1420"' in line)
    lines.insert(legend_i + 1, '<circle cx="953" cy="1455" r="5" fill="#4a8263"/><text x="970" y="1461" font-size="17" fill="#39342d">090 · Вітальня · Вимикач ×2 · 1.05 м</text>')
svg_path.write_text('\n'.join(lines) + '\n', encoding='utf8')

# Repack both current floor models and all gallery screenshots into the offline HTML viewer.
html_path = viewer / 'House_Viewer.html'
build_viewer(html_path)
html_text = html_path.read_text(encoding='utf8')
if '__HOUSE_DATA_JSON__' in html_text or '__FIRST_PERSON_SCRIPT__' in html_text:
    raise ValueError('Viewer template markers remain in the built HTML')
embedded_photo_count = html_text.count('"mime":"image/png"')
if embedded_photo_count != 36:
    raise ValueError(f'Expected 36 embedded gallery images, found {embedded_photo_count}')
verification = {
    'revision': 20,
    'updated_switch_objects': sorted(expected),
    'active_floor1_node_count': len(active),
    'switch_nodes_active_once': True,
    'duplicate_active_node_names': 0,
    'corner_pantry_pivot_nodes': 20,
    'all_buffer_views_within_glb': True,
    'floor2_glb_unchanged': True,
    'embedded_viewer_rebuilt': True,
    'gallery_photos_embedded': embedded_photo_count,
    'floor1_glb_bytes': base_path.stat().st_size,
    'viewer_html_bytes': html_path.stat().st_size,
    'electrical_svg_updated': str(svg_path.relative_to(ROOT)),
}
(ROOT / 'House_Library_Design/data/revision20_browser_verification.json').write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding='utf8')
electrical = {item['id']: item for item in json.loads((ROOT / 'House_Library_Design/data/electrical_points.json').read_text(encoding='utf8'))}
report['json_points_match_report'] = all(
    abs(electrical[item['id']]['x_m'] - item['to']['x_m']) < 1e-6
    and abs(electrical[item['id']]['y_m'] - item['to']['y_m']) < 1e-6
    and electrical[item['id']]['face'] == item['to']['face']
    for item in report['switches']
)
if not report['json_points_match_report']:
    raise ValueError('electrical_points.json does not match revision20_report.json')
report['rendered_screenshots'] = {
    name: (ROOT / 'House_Library_Design/previews' / f'{name}.png').is_file()
    for name in ('Kitchen', 'Kitchen_Reverse', 'Ground_Shower_Reverse', 'Entry_Reverse', 'Ground_Hall', 'Living_Dining')
}
if not all(report['rendered_screenshots'].values()):
    raise ValueError(f'Missing one or more rendered review screenshots: {report["rendered_screenshots"]}')
(ROOT / 'House_Library_Design/data/revision20_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(verification, ensure_ascii=False))
