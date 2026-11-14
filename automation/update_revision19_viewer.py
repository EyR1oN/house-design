"""Replace only the two revised door assemblies in the floor-one GLB."""
from pathlib import Path
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
from open_stair_exit_viewer import read_glb, write_glb

viewer = ROOT / 'House_Browser_Viewer'
base_path = viewer / 'House_Floor_1.glb'
patch_path = viewer / 'revision19_doors_floor1.glb'
backup_path = ROOT / '.local-preview/pre-revision19/House_Floor_1.glb'
if not backup_path.exists():
    shutil.copy2(base_path, backup_path)

report = json.loads((ROOT / 'House_Library_Design/data/revision19_report.json').read_text(encoding='utf8'))
placements = json.loads((ROOT / 'House_Library_Design/data/placements.json').read_text(encoding='utf8'))
prefixes = ('LIB_Door_L1_KITCHEN_DOOR', 'LIB_Door_L1_LAUNDRY_DOOR')
expected = {name for row in placements if row['label'] in ('Door_L1_KITCHEN_DOOR', 'Door_L1_LAUNDRY_DOOR')
            for name in row['objects']}

base, base_bin = read_glb(backup_path.read_bytes())
patch, patch_bin = read_glb(patch_path.read_bytes())

def reachable(document):
    seen = set()
    def visit(index):
        if index in seen:
            return
        seen.add(index)
        for child in document['nodes'][index].get('children', []):
            visit(child)
    for root in document['scenes'][document.get('scene', 0)]['nodes']:
        visit(root)
    return seen

current_active = reachable(base)
patch_active = reachable(patch)
patch_names = {patch['nodes'][index].get('name') for index in patch_active}
if patch_names != expected:
    raise ValueError(f'Patch nodes differ from the two door placements: missing={expected-patch_names}, extra={patch_names-expected}')

removed = {index for index, node in enumerate(base['nodes'])
           if node.get('name', '').startswith(prefixes)}
if not removed or not removed.issubset(current_active):
    raise ValueError(f'Expected active old door nodes to replace; found {len(removed)}')
for scene in base['scenes']:
    scene['nodes'] = [index for index in scene['nodes'] if index not in removed]
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
        primitive['attributes'] = {key: index + offsets['accessors']
                                   for key, index in primitive['attributes'].items()}
        if 'indices' in primitive:
            primitive['indices'] += offsets['accessors']
        if 'material' in primitive:
            primitive['material'] += offsets['materials']
for node in patch['nodes']:
    node['extras'] = {**node.get('extras', {}), 'level': 1, 'revision': 19}
    if 'mesh' in node:
        node['mesh'] += offsets['meshes']
    if 'children' in node:
        node['children'] = [index + offsets['nodes'] for index in node['children']]

for key in keys:
    base.setdefault(key, []).extend(patch.get(key, []))
base['scenes'][base.get('scene', 0)]['nodes'].extend(index + offsets['nodes'] for index in patch_roots)
extras = base['scenes'][base.get('scene', 0)].setdefault('extras', {})
extras['interior_revision'] = 'LIBRARY 19.0 entry and laundry door swings'
extras['door_swing_revision'] = {
    'revision': 19,
    'doors': [door['id'] for door in report['doors']],
}
for key in ('extensionsUsed', 'extensionsRequired'):
    if patch.get(key):
        base[key] = sorted(set(base.get(key, []) + patch[key]))

new_active = reachable(base)
active_names = [base['nodes'][index].get('name') for index in new_active]
if len(active_names) != len(set(active_names)):
    raise ValueError('Duplicate active node names after replacing door assemblies')
if not expected.issubset(active_names):
    raise ValueError('One or more door components are missing after replacement')
if any(name.startswith(prefixes) for name in active_names if name not in expected):
    raise ValueError('An old or aggregate door node remains active after replacement')
for view in base.get('bufferViews', []):
    if view.get('byteOffset', 0) + view['byteLength'] > len(base_bin):
        raise ValueError('GLB bufferView exceeds binary payload')

temporary = base_path.with_suffix('.revision19.tmp')
temporary.write_bytes(write_glb(base, base_bin))
temporary.replace(base_path)
print(json.dumps({
    'updated': str(base_path),
    'old_active_door_nodes_removed': len(removed),
    'new_active_door_nodes': len(expected),
    'floor_two_unchanged': True,
    'pantry_pivot_nodes': sum(base['nodes'][index].get('extras', {}).get('pantry_role') == 'pivot'
                              for index in new_active),
    'active_node_count': len(new_active),
    'bytes': base_path.stat().st_size,
}, ensure_ascii=False))
