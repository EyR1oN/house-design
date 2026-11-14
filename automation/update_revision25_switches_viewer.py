from pathlib import Path
import base64, json, re

ROOT = Path(__file__).resolve().parents[1]
sys_path = ROOT / 'automation'
import sys
sys.path.insert(0, str(sys_path))
from open_stair_exit_viewer import read_glb, write_glb
from build_viewer import build as build_viewer

viewer = ROOT / 'House_Browser_Viewer'
base_path = viewer / 'House_Floor_1.glb'
patch_path = viewer / 'revision25_switches_floor1.glb'
report_path = ROOT / 'House_Library_Design' / 'data' / 'revision25_report.json'
report = json.loads(report_path.read_text(encoding='utf8'))
expected = {name for switch in report['switches'] for name in switch['objects']}
old_expected = set(report['switches'][0]['objects'])
base, base_bin = read_glb(base_path.read_bytes())
patch, patch_bin = read_glb(patch_path.read_bytes())

def reachable(doc):
    seen = set()
    def visit(index):
        if index in seen:
            return
        seen.add(index)
        for child in doc['nodes'][index].get('children', []):
            visit(child)
    for index in doc['scenes'][doc.get('scene', 0)]['nodes']:
        visit(index)
    return seen

base_active = reachable(base)
patch_active = reachable(patch)
patch_names = {patch['nodes'][i].get('name') for i in patch_active}
if patch_names != expected:
    raise ValueError(f'Patch mismatch: missing={expected-patch_names}, extra={patch_names-expected}')
base_names = {base['nodes'][i].get('name') for i in base_active}
existing_expected = expected & base_names
if existing_expected not in (old_expected, expected):
    raise ValueError(f'Base GLB has an unexpected active revision 25 switch set: {existing_expected}')

removed = {i for i, node in enumerate(base['nodes']) if node.get('name') in expected}
removed_active = {base['nodes'][i].get('name') for i in removed if i in base_active}
if removed_active != existing_expected:
    raise ValueError(f'Unexpected active old switch set: {removed_active}')
for scene in base['scenes']:
    scene['nodes'] = [i for i in scene.get('nodes', []) if i not in removed]
for node in base['nodes']:
    if 'children' in node:
        node['children'] = [i for i in node['children'] if i not in removed]

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

def offset_textures(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith('Texture') and isinstance(child, dict) and 'index' in child:
                child['index'] += offsets['textures']
            else:
                offset_textures(child)
    elif isinstance(value, list):
        for child in value:
            offset_textures(child)

for material in patch.get('materials', []):
    offset_textures(material)
for mesh in patch.get('meshes', []):
    for primitive in mesh['primitives']:
        primitive['attributes'] = {key: index + offsets['accessors'] for key, index in primitive['attributes'].items()}
        if 'indices' in primitive:
            primitive['indices'] += offsets['accessors']
        if 'material' in primitive:
            primitive['material'] += offsets['materials']
for node in patch['nodes']:
    node['extras'] = {**node.get('extras', {}), 'level': 1, 'revision': 25}
    if 'mesh' in node:
        node['mesh'] += offsets['meshes']
    if 'children' in node:
        node['children'] = [i + offsets['nodes'] for i in node['children']]
for key in keys:
    base.setdefault(key, []).extend(patch.get(key, []))
base['scenes'][base.get('scene', 0)]['nodes'].extend(i + offsets['nodes'] for i in patch_roots)
base['scenes'][base.get('scene', 0)].setdefault('extras', {})['interior_revision'] = 'LIBRARY 25.0 pantry and stair-side living switches'
for key in ('extensionsUsed', 'extensionsRequired'):
    if patch.get(key):
        base[key] = sorted(set(base.get(key, []) + patch[key]))

active = reachable(base)
active_names = [base['nodes'][i].get('name') for i in active]
if len(active_names) != len(set(active_names)):
    raise ValueError('Duplicate active node names after switch replacement')
if not expected.issubset(active_names):
    raise ValueError(f'Missing switch nodes after merge: {expected-set(active_names)}')
if sum(base['nodes'][i].get('extras', {}).get('pantry_role') == 'pivot' for i in active) != 20:
    raise ValueError('Corner pantry pivot count changed')
for view in base.get('bufferViews', []):
    if view.get('byteOffset', 0) + view['byteLength'] > len(base_bin):
        raise ValueError('GLB bufferView out of range')
temp = base_path.with_suffix('.revision25.tmp')
temp.write_bytes(write_glb(base, base_bin))
temp.replace(base_path)

# Keep the floor-one electrical plan markers aligned with the point schedule.
points = {point['id']: point for point in json.loads((ROOT / 'House_Library_Design/data/electrical_points.json').read_text(encoding='utf8'))}
svg_path = ROOT / 'House_Library_Design/exports/Electrical_Points_Floor_1.svg'
lines = svg_path.read_text(encoding='utf8').splitlines()
def fmt(value):
    return f'{value:.3f}'.rstrip('0').rstrip('.')
def px(x, y):
    return 183.5 + (x - 6.0) * 115.0, 1660.0 - y * 115.0
for pid in ('E1_020_SWITCH',):
    point = points[pid]
    x, y = px(point['x_m'], point['y_m'])
    circle_pattern = re.compile(r'(<circle cx=")[^"]+(" cy=")[^"]+(" r="8"[^>]*><title>' + re.escape(pid) + r' /.*?</title></circle>)')
    indexes = [i for i, line in enumerate(lines) if circle_pattern.search(line)]
    if len(indexes) != 1:
        raise ValueError(f'{pid}: expected one SVG marker, found {len(indexes)}')
    i = indexes[0]
    lines[i] = circle_pattern.sub(lambda m: m.group(1) + fmt(x) + m.group(2) + fmt(y) + m.group(3), lines[i])
    label_pattern = re.compile(r'(<text x=")[^"]+(" y=")[^"]+(" font-size="13"[^>]*>020</text>)')
    if not label_pattern.search(lines[i + 1]):
        raise ValueError('E1_020 plan label missing')
    lines[i + 1] = label_pattern.sub(lambda m: m.group(1) + fmt(x + 10) + m.group(2) + fmt(y - 7) + m.group(3), lines[i + 1])

if not any('E1_091_SWITCH' in line for line in lines):
    additions = []
    for pid in ('E1_091_SWITCH', 'E1_092_SWITCH'):
        point = points[pid]
        x, y = px(point['x_m'], point['y_m'])
        number = pid.split('_')[1]
        purpose = point['purpose'].replace('&', '&amp;')
        additions.extend([
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="8" fill="#4a8263" stroke="#fff" stroke-width="2"><title>{pid} / {purpose} / 1.05m</title></circle>',
            f'<text x="{fmt(x+10)}" y="{fmt(y-7)}" font-size="13" font-weight="bold" fill="#4a8263">{number}</text>'
        ])
    marker_090 = next(i for i, line in enumerate(lines) if 'E1_090_SWITCH' in line and '<circle' in line)
    lines[marker_090+2:marker_090+2] = additions
    table_090 = next(i for i, line in enumerate(lines) if '090 · Вітальня · Вимикач ×2 · 1.05 м' in line)
    lines[table_090+1:table_090+1] = [
        '<circle cx="953" cy="1490" r="5" fill="#4a8263"/><text x="970" y="1496" font-size="17" fill="#39342d">091 · Вітальня · Вимикач ×2 · керування зі сходів · 1.05 м</text>',
        '<circle cx="953" cy="1525" r="5" fill="#4a8263"/><text x="970" y="1531" font-size="17" fill="#39342d">092 · Вітальня · Димер ×2 · керування зі сходів · 1.05 м</text>'
    ]
svg_path.write_text('\n'.join(lines) + '\n', encoding='utf8')
svg_text = svg_path.read_text(encoding='utf8')
svg_text = svg_text.replace('data/electrical_points.csv', 'data/electrical_points.json')
svg_path.write_text(svg_text, encoding='utf8')
for pid in ('E1_020_SWITCH', 'E1_091_SWITCH', 'E1_092_SWITCH'):
    if pid not in svg_text:
        raise ValueError(f'Electrical SVG is missing {pid}')

html_path = viewer / 'House_Viewer.html'
build_viewer(html_path)
html = html_path.read_text(encoding='utf8')
if '__HOUSE_DATA_JSON__' in html or '__FIRST_PERSON_SCRIPT__' in html:
    raise ValueError('Viewer template markers remain')
photo_count = html.count('"mime":"image/png"')
if photo_count != 36:
    raise ValueError(f'Expected 36 embedded gallery photos, found {photo_count}')
data_marker = 'window.HOUSE_DATA='
if data_marker not in html:
    raise ValueError('Embedded viewer data object is missing')
data_start = html.index(data_marker) + len(data_marker)
embedded_data, _ = json.JSONDecoder().raw_decode(html[data_start:])
embedded_glb, embedded_bin = read_glb(base64.b64decode(embedded_data['models']['1']))
embedded_active = reachable(embedded_glb)
embedded_names = {embedded_glb['nodes'][i].get('name') for i in embedded_active}
if not expected.issubset(embedded_names):
    raise ValueError(f'Embedded first-floor model is missing revision 25 switch nodes: {expected-embedded_names}')
if sum(embedded_glb['nodes'][i].get('extras', {}).get('pantry_role') == 'pivot' for i in embedded_active) != 20:
    raise ValueError('Embedded first-floor model lost pantry pivot nodes')
verification = {
    'revision': 25,
    'active_floor1_node_count': len(active),
    'updated_switch_components': sorted(expected),
    'switch_nodes_active_once': True,
    'duplicate_active_node_names': 0,
    'corner_pantry_pivot_nodes': 20,
    'all_buffer_views_within_glb': True,
    'floor2_glb_unchanged': True,
    'embedded_viewer_rebuilt': True,
    'gallery_photos_embedded': photo_count,
    'viewer_html_bytes': html_path.stat().st_size,
    'electrical_svg_updated': str(svg_path.relative_to(ROOT)),
    'surface_checks': report['surface_checks'],
    'clearances_m': report['clearances_m']
}
(ROOT / 'House_Library_Design/data/revision25_browser_verification.json').write_text(json.dumps(verification, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps(verification, ensure_ascii=False))
