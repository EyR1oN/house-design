"""Pack the current GLBs and gallery images into an offline viewer. Never edits .blend."""
from pathlib import Path
import argparse
import base64
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
MARKER = '__HOUSE_DATA_JSON__'


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
    return document


def build(output):
    if output.suffix.lower() != '.html':
        raise ValueError('Output must be an HTML file.')
    template = (ROOT / 'House_Browser_Viewer/viewer_template.html').read_text(encoding='utf-8')
    if template.count(MARKER) != 1:
        raise ValueError('Viewer template must contain exactly one data marker.')
    data = {'models': {}, 'photos': []}
    pivot_nodes = 0
    for floor in (1, 2):
        path = ROOT / f'House_Browser_Viewer/House_Floor_{floor}.glb'
        raw = read_asset(path)
        document = validate_glb(raw, path)
        if floor == 1:
            active = set()

            def visit(index):
                if index in active:
                    return
                active.add(index)
                for child in document['nodes'][index].get('children', []):
                    visit(child)

            for index in document['scenes'][document.get('scene', 0)]['nodes']:
                visit(index)
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
                      'size_mb': round(output.stat().st_size / 1_000_000, 1), 'blender_modified': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'House_Browser_Viewer/House_Viewer.html')
    arguments = parser.parse_args()
    build(arguments.output.resolve())
