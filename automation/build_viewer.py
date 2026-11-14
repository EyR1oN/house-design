"""Pack the current GLBs and gallery images into an offline viewer. Never edits .blend."""
from pathlib import Path
import argparse
import base64
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
MARKER = '__HOUSE_DATA_JSON__'
FIRST_PERSON_MARKER = '__FIRST_PERSON_SCRIPT__'


def read_asset(path):
    data = path.read_bytes()
    if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
        raise ValueError(f'LFS pointer instead of file: {path}. Run git lfs pull.')
    return data


def validate_glb(data, path):
    if len(data) < 20:
        raise ValueError(f'Incomplete GLB: {path}')
    magic, version, size = struct.unpack_from('<4sII', data)
    if (magic, version, size) != (b'glTF', 2, len(data)):
        raise ValueError(f'Invalid GLB header: {path}')
    length, kind = struct.unpack_from('<II', data, 12)
    if kind != 0x4E4F534A or length + 20 > len(data):
        raise ValueError(f'Invalid GLB JSON chunk: {path}')
    document = json.loads(data[20:20 + length])
    for asset in document.get('buffers', []) + document.get('images', []):
        if 'uri' in asset and not asset['uri'].startswith('data:'):
            raise ValueError(f'External dependency in {path}: {asset["uri"]}')
    active = reachable_node_indices(document)
    nodes = document.get('nodes', [])
    if len(active) != len(nodes):
        raise ValueError(f'{path} contains unreachable scene nodes. Run automation/compact_viewer_models.py --write.')
    meshes = document.get('meshes', [])
    used_meshes = {nodes[index]['mesh'] for index in active if 'mesh' in nodes[index]}
    if any(not isinstance(index, int) or index < 0 or index >= len(meshes) for index in used_meshes):
        raise ValueError(f'{path} contains an invalid mesh reference.')
    if used_meshes != set(range(len(meshes))):
        raise ValueError(f'{path} contains unreferenced meshes. Run automation/compact_viewer_models.py --write.')
    return document


def reachable_node_indices(document):
    nodes = document.get('nodes', [])
    scenes = document.get('scenes', [])
    if not scenes:
        raise ValueError('GLB has no scenes.')
    active = set()
    visiting = set()

    def visit(index):
        if not isinstance(index, int) or index < 0 or index >= len(nodes):
            raise ValueError(f'Invalid node reference: {index}')
        if index in visiting:
            raise ValueError(f'Node cycle detected at index {index}.')
        if index in active:
            return
        active.add(index)
        visiting.add(index)
        for child in nodes[index].get('children', []):
            visit(child)
        visiting.remove(index)

    for scene in scenes:
        for index in scene.get('nodes', []):
            visit(index)
    return active


def build(output):
    if output.suffix.lower() != '.html':
        raise ValueError('Output must be an HTML file.')
    template = (ROOT / 'House_Browser_Viewer/viewer_template.html').read_text(encoding='utf-8')
    if template.count(MARKER) != 1:
        raise ValueError('Viewer template must contain exactly one data marker.')
    if template.count(FIRST_PERSON_MARKER) != 1:
        raise ValueError('Viewer template must contain exactly one first-person script marker.')
    first_person = (ROOT / 'House_Browser_Viewer/first_person.js').read_text(encoding='utf-8')
    electrical_mode = (ROOT / 'House_Browser_Viewer/electrical_mode.js').read_text(encoding='utf-8')
    data = {'models': {}, 'photos': []}
    pivot_nodes = 0
    for floor in (1, 2):
        path = ROOT / f'House_Browser_Viewer/House_Floor_{floor}.glb'
        raw = read_asset(path)
        document = validate_glb(raw, path)
        if floor == 1:
            active = reachable_node_indices(document)
            pivot_nodes = sum(document['nodes'][i].get('extras', {}).get('pantry_role') == 'pivot' for i in active)
            if pivot_nodes != 20:
                raise ValueError(f'Expected 20 moving pantry nodes, found {pivot_nodes}. Review exported pantry roles.')
        data['models'][str(floor)] = base64.b64encode(raw).decode('ascii')
    views = json.loads((ROOT / 'House_Library_Design/data/gallery_views.json').read_text(encoding='utf-8'))
    for key, title in views:
        path = ROOT / 'House_Library_Design/previews' / f'{key}.png'
        raw = read_asset(path)
        if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError(f'Invalid PNG: {path}')
        data['photos'].append({'title': title, 'image': base64.b64encode(raw).decode('ascii'), 'mime': 'image/png'})
    prefix, suffix = template.split(MARKER)
    suffix = suffix.replace(FIRST_PERSON_MARKER, first_person + '\n' + electrical_mode)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.building.tmp')
    try:
        with temporary.open('w', encoding='utf-8', newline='') as stream:
            stream.write(prefix)
            json.dump(data, stream, ensure_ascii=False, separators=(',', ':'))
            stream.write(suffix)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps({'output': str(output), 'floors': 2, 'photos': len(views), 'moving_pantry_nodes': pivot_nodes,
                      'first_person_mode': True, 'electrical_mode': True,
                      'size_mb': round(output.stat().st_size / 1_000_000, 1), 'blender_modified': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'House_Browser_Viewer/House_Viewer.html')
    arguments = parser.parse_args()
    build(arguments.output.resolve())
