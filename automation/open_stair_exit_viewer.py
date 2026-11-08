"""Remove the upper TV/storage wall extension from the merged floor-2 viewer mesh.
Preserves the closet wall's shared end reveal, the remaining closet wall faces,
and the lower-floor wall (exported separately in House_Floor_1.glb).
"""
from pathlib import Path
import json
import math
import struct

ROOT = Path(__file__).resolve().parents[1]
GLB_PATH = ROOT / 'House_Browser_Viewer' / 'House_Floor_2.glb'
MAGIC = b'glTF'
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def read_glb(data):
    magic, version, total = struct.unpack_from('<4sII', data, 0)
    if (magic, version, total) != (MAGIC, 2, len(data)):
        raise ValueError('Invalid GLB header')
    offset = 12
    document = binary = None
    while offset < len(data):
        length, kind = struct.unpack_from('<II', data, offset)
        chunk = data[offset + 8:offset + 8 + length]
        if kind == JSON_CHUNK:
            document = json.loads(chunk.decode('utf-8').rstrip(' \t\r\n\0'))
        elif kind == BIN_CHUNK:
            binary = chunk
        offset += 8 + length
    if document is None or binary is None:
        raise ValueError('GLB must contain JSON and BIN chunks')
    return document, binary


def write_glb(document, binary):
    document['buffers'][0]['byteLength'] = len(binary)
    raw_json = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    raw_json += b' ' * (-len(raw_json) % 4)
    binary += b'\0' * (-len(binary) % 4)
    total = 12 + 8 + len(raw_json) + 8 + len(binary)
    return (struct.pack('<4sII', MAGIC, 2, total)
            + struct.pack('<II', len(raw_json), JSON_CHUNK) + raw_json
            + struct.pack('<II', len(binary), BIN_CHUNK) + binary)


def accessor(document, binary, index):
    item = document['accessors'][index]
    view = document['bufferViews'][item['bufferView']]
    component = item['componentType']
    count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[item['type']]
    fmt = {5126: 'f', 5125: 'I', 5123: 'H', 5121: 'B'}[component]
    size = struct.calcsize(fmt) * count
    stride = view.get('byteStride', size)
    start = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    return [struct.unpack_from('<' + fmt * count, binary, start + i * stride)
            for i in range(item['count'])]


def area_xy(tri):
    a, b, c = tri
    return abs((b[0] - a[0]) * (c[1] - a[1])
               - (b[1] - a[1]) * (c[0] - a[0])) * 0.5


def patch():
    document, binary = read_glb(GLB_PATH.read_bytes())
    walls = next((node for node in document['nodes'] if node.get('name') == 'Walls'), None)
    if walls is None:
        raise ValueError('Combined Walls node not found')

    # The removed Blender object occupied x=6.49..6.62, y=7.03..8.40,
    # z=2.90..5.87. These are its merged GLB coordinates; y is floor-relative.
    removed_ids = set()
    candidates = []
    preserved_reveal_count = 0
    for primitive in document['meshes'][walls['mesh']]['primitives']:
        if primitive.get('mode', 4) != 4 or 'indices' not in primitive:
            raise ValueError('Expected indexed triangle mesh for combined Walls')
        points = accessor(document, binary, primitive['attributes']['POSITION'])
        indices, fmt = accessor(document, binary, primitive['indices']), None
        component_type = document['accessors'][primitive['indices']]['componentType']
        fmt = {5121: 'B', 5123: 'H', 5125: 'I'}[component_type]
        indices = [row[0] for row in indices]
        remove_faces = set()
        for offset in range(0, len(indices), 3):
            tri = [points[indices[offset + i]] for i in range(3)]
            xs, ys, zs = ([v[axis] for v in tri] for axis in range(3))
            in_extension = (
                min(xs) >= 6.48 and max(xs) <= 6.63
                and min(ys) >= -0.31 and max(ys) <= 2.71
                and min(zs) >= -8.41 and max(zs) <= -7.02
            )
            # This is the shared vertical end of the upstairs closet wall.
            # Keep it even though it touches the removed wall's boundary.
            closet_reveal = (
                max(xs) <= 6.495 and min(xs) >= 6.485
                and min(zs) >= -7.415 and max(zs) <= -7.145
                and min(ys) >= -0.001 and max(ys) <= 2.701
            )
            if closet_reveal:
                preserved_reveal_count += 1
            elif in_extension:
                remove_faces.add(offset // 3)
        candidates.append((primitive, indices, fmt, remove_faces, points))

    removed = sum(len(entry[3]) for entry in candidates)
    scene_extras = document.get('scenes', [{}])[document.get('scene', 0)].get('extras', {})
    already_patched = scene_extras.get('stair_exit_revision', {}).get('revision') == 17
    if already_patched and removed == 0 and preserved_reveal_count == 2:
        print(json.dumps({'status': 'already_patched', 'preserved_closet_wall_reveal_triangles': 2}))
        return
    if removed != 380 or preserved_reveal_count != 2:
        raise ValueError(f'Expected 380 upper-wall triangles removed and 2 closet reveal triangles retained; got {removed} and {preserved_reveal_count}. No changes written.')

    # Confirm the main closet-wall faces remain complete on both sides.
    preserved_wall_area = {-7.0301: 0.0, -7.4102: 0.0}
    for primitive, indices, _, remove_faces, points in candidates:
        for face in range(len(indices) // 3):
            if face in remove_faces:
                continue
            tri = [points[indices[face * 3 + i]] for i in range(3)]
            plane = next((z for z in preserved_wall_area
                          if all(abs(v[2] - z) < 0.001 for v in tri)), None)
            if plane is not None and min(v[0] for v in tri) >= 5.485 and max(v[0] for v in tri) <= 6.495:
                preserved_wall_area[plane] += area_xy(tri)
    for plane, area in preserved_wall_area.items():
        if abs(area - 2.70) > 0.01:
            raise ValueError(f'Closet wall face at z={plane} is {area:.4f} m²; expected 2.700 m²')

    append_offset = (len(binary) + 3) & ~3
    binary += b'\0' * (append_offset - len(binary))
    for primitive, indices, fmt, remove_faces, _ in candidates:
        kept = [value for face in range(len(indices) // 3) if face not in remove_faces
                for value in indices[face * 3:face * 3 + 3]]
        packed = struct.pack('<' + fmt * len(kept), *kept)
        view_index = len(document.setdefault('bufferViews', []))
        document['bufferViews'].append({'buffer': 0, 'byteOffset': append_offset,
                                        'byteLength': len(packed), 'target': 34963})
        accessor_index = len(document.setdefault('accessors', []))
        document['accessors'].append({
            'bufferView': view_index,
            'componentType': document['accessors'][primitive['indices']]['componentType'],
            'count': len(kept), 'type': 'SCALAR', 'min': [min(kept)], 'max': [max(kept)],
        })
        primitive['indices'] = accessor_index
        binary += packed
        append_offset += len(packed)
        aligned = (append_offset + 3) & ~3
        binary += b'\0' * (aligned - len(binary))
        append_offset = aligned

    scene = document.setdefault('scenes', [])[document.get('scene', 0)]
    scene.setdefault('extras', {})['stair_exit_revision'] = {
        'revision': 17,
        'removed_upper_tv_wall_extension': True,
        'closet_wall_preserved': True,
        'ground_floor_tv_storage_wall_preserved': True,
        'threshold_preserved': True,
        'removed_triangles': removed,
    }
    scene['extras']['interior_revision'] = 'LIBRARY 17.0 remove upper TV-wall extension'
    output = write_glb(document, binary)
    temporary = GLB_PATH.with_suffix('.stair-exit.tmp')
    temporary.write_bytes(output)
    temporary.replace(GLB_PATH)
    print(json.dumps({
        'output': str(GLB_PATH),
        'removed_upper_wall_triangles': removed,
        'preserved_closet_wall_reveal_triangles': preserved_reveal_count,
        'preserved_closet_wall_face_areas_m2': preserved_wall_area,
        'lower_tv_storage_wall_in_floor_1_unchanged': True,
        'size_bytes': len(output),
    }))


if __name__ == '__main__':
    patch()
