"""Update the compact viewer exports for the revision 26 visual fixes."""
from array import array
import json
from pathlib import Path
import re
import sys

from compact_viewer_models import compact, read_glb, write_glb
from open_stair_exit_viewer import accessor

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / 'House_Browser_Viewer'
PROJECT = ROOT / 'House_Library_Design'
GROUND_MOVES = {'E1_001_SOCKET': .20, 'E1_004_SWITCH': -.011, 'E1_013_SOCKET': .006, 'E1_014_DATA': -.0196}


def index_accessor(doc, binary, primitive, indices):
    old = doc['accessors'][primitive['indices']]
    values = array({5121: 'B', 5123: 'H', 5125: 'I'}[old['componentType']], indices)
    if sys.byteorder != 'little':
        values.byteswap()
    binary.extend(bytes((-len(binary)) % 4))
    view = len(doc['bufferViews'])
    data = values.tobytes()
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data), 'target': 34963})
    binary.extend(data)
    doc['accessors'].append({'bufferView': view, 'componentType': old['componentType'],
                             'type': 'SCALAR', 'count': len(indices),
                             'min': [min(indices)], 'max': [max(indices)]})
    return {**primitive, 'indices': len(doc['accessors']) - 1}


def inside(box, point):
    return all(low <= value <= high for (low, high), value in zip(box, (point[0], -point[2], point[1])))


def filter_triangles(doc, binary, node, boxes, expected):
    counts = [0] * len(boxes)
    mesh = doc['meshes'][node['mesh']]
    keep = []
    for primitive in mesh['primitives']:
        positions = accessor(doc, binary, primitive['attributes']['POSITION'])
        ids = [i for i, in accessor(doc, binary, primitive['indices'])]
        output = []
        for offset in range(0, len(ids), 3):
            triangle = ids[offset:offset + 3]
            match = next((i for i, box in enumerate(boxes)
                          if all(inside(box, positions[j]) for j in triangle)), None)
            if match is None:
                output.extend(triangle)
            else:
                counts[match] += 1
        if output:
            keep.append(primitive if len(output) == len(ids) else index_accessor(doc, binary, primitive, output))
    if counts != expected:
        raise ValueError(f'{node["name"]}: expected {expected} legacy triangles, found {counts}')
    mesh['primitives'] = keep


def separate_cladding(doc, node, material_suffixes):
    mesh = doc['meshes'][node['mesh']]
    materials = doc['materials']
    selected = [p for p in mesh['primitives']
                if materials[p['material']]['name'].endswith(material_suffixes)]
    if not selected:
        raise ValueError(f'No cladding in {node["name"]}')
    mesh['primitives'] = [p for p in mesh['primitives'] if p not in selected]
    doc['meshes'].append({'name': 'Bath wall cladding', 'primitives': selected})
    doc['nodes'].append({'name': 'Bath_Wall_Cladding', 'mesh': len(doc['meshes']) - 1,
                         'extras': {'viewer_clip_with_walls': True, 'viewer_fixed_finish': True}})
    doc['scenes'][0]['nodes'].append(len(doc['nodes']) - 1)


def attach_devices(doc, binary, patch_path):
    patch, payload = read_glb(patch_path)
    keys = ('bufferViews', 'accessors', 'materials', 'meshes', 'nodes')
    if any(patch.get(key) for key in ('textures', 'images', 'samplers', 'animations', 'skins')):
        raise ValueError('Wall device patch must use simple, untextured meshes.')
    sizes = {key: len(doc.get(key, [])) for key in keys}
    binary.extend(bytes((-len(binary)) % 4))
    for view in patch['bufferViews']:
        view['byteOffset'] = view.get('byteOffset', 0) + len(binary)
    binary.extend(payload)
    for data in patch['accessors']:
        data['bufferView'] += sizes['bufferViews']
    for mesh in patch['meshes']:
        for p in mesh['primitives']:
            p['indices'] += sizes['accessors']
            p['material'] += sizes['materials']
            p['attributes'] = {name: i + sizes['accessors'] for name, i in p['attributes'].items()}
    roots = patch['scenes'][0]['nodes']
    if len(roots) != len(patch['nodes']) or any(n.get('children') or 'matrix' in n for n in patch['nodes']):
        raise ValueError('Expected a flat set of wall-device meshes.')
    for node in patch['nodes']:
        node['translation'][1] -= 3.2
        node['mesh'] += sizes['meshes']
    for key in keys:
        doc.setdefault(key, []).extend(patch[key])
    doc['scenes'][0]['nodes'].extend(i + sizes['nodes'] for i in roots)
    doc['extensionsUsed'] = sorted(set(doc.get('extensionsUsed', [])) | set(patch.get('extensionsUsed', [])))


def update_model(floor, patch):
    path = VIEWER / f'House_Floor_{floor}.glb'
    doc, data = read_glb(path)
    binary = bytearray(data)
    nodes = {n['name']: n for n in doc['nodes']}
    if floor == 1:
        room = nodes['PART_DESIGN_WC']
        filter_triangles(doc, binary, room, [
            ((6.552, 6.598), (5.014, 6.366), (2.129, 2.166)),
            ((6.573, 6.597), (5.742, 5.758), (.919, 1.091)),
        ], [188, 188])
        separate_cladding(doc, room, ('Warm_Stone',))
        moves = GROUND_MOVES
    else:
        room = nodes['PART_DESIGN_Upper_Bath']
        filter_triangles(doc, binary, room, [
            ((8.292, 8.36), (5.794, 7.146), (0, 2.166)),
        ], [564])
        separate_cladding(doc, room, ('Warm_Stone', 'Taupe'))
        filter_triangles(doc, binary, nodes['PART_Electrical_L2'], [
            ((6.994, 7.146), (4.3, 4.325), (1.01, 1.09)),
            ((10.344, 10.496), (.197, .22), (.26, .34)),
        ], [564, 684])
        attach_devices(doc, binary, patch)
        moves = {'E2_080_SOCKET': .0154}
    for pid, dx in moves.items():
        if pid not in nodes:
            raise ValueError(f'Missing wall device {pid}')
        for node in nodes.values():
            if node.get('extras', {}).get('point_id') == pid or node['name'] == pid or node['name'].startswith(pid + '_'):
                node['translation'][0] += dx
    names = [n['name'] for n in doc['nodes']]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate viewer node names')
    doc['buffers'][0]['byteLength'] = len(binary)
    doc, payload, _ = compact(doc, binary, 20 if floor == 1 else 0)
    return path, write_glb(doc, payload)


def update_plan(floor, moves):
    path = PROJECT / f'exports/Electrical_Points_Floor_{floor}.svg'
    lines = path.read_text(encoding='utf-8').splitlines()
    for pid, dx in moves.items():
        marker = next(i for i, line in enumerate(lines) if f'<title>{pid} /' in line)
        for i, attribute in ((marker, 'cx'), (marker + 1, 'x')):
            pattern = rf'({attribute}=")([\d.]+)(")'
            lines[i], count = re.subn(pattern, lambda m: f'{m[1]}{float(m[2]) + dx * 115:.3f}{m[3]}',
                                      lines[i], count=1)
            if count != 1:
                raise ValueError(f'Missing plan coordinate for {pid}')
    if floor == 2:
        for i, line in enumerate(lines):
            if '083 ·' in line:
                lines[i] = line.replace('×3', '×2')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


if __name__ == '__main__':
    patch = ROOT / '.local-preview/visual-switches.glb'
    outputs = [update_model(floor, patch) for floor in (1, 2)]
    for path, payload in outputs:
        temp = path.with_suffix('.tmp')
        temp.write_bytes(payload)
        temp.replace(path)
    update_plan(1, GROUND_MOVES)
    update_plan(2, {'E2_044_SOCKET': -.24, 'E2_050_SWITCH': .093, 'E2_080_SOCKET': .0154, 'E2_081_DATA': .0154})
