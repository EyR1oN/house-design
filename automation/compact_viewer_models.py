"""Remove unreachable scene nodes and their unreferenced GLB payload data."""
from pathlib import Path
import argparse
import copy
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / 'House_Browser_Viewer'
ALLOWED_EXTENSIONS = {
    'KHR_materials_anisotropy', 'KHR_materials_emissive_strength', 'KHR_materials_ior',
    'KHR_materials_specular', 'KHR_materials_transmission', 'KHR_texture_transform',
}


def read_glb(path):
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError(f'Incomplete GLB: {path}')
    magic, version, total = struct.unpack_from('<4sII', raw)
    if (magic, version, total) != (b'glTF', 2, len(raw)):
        raise ValueError(f'Invalid GLB header: {path}')
    offset = 12
    chunks = []
    while offset < len(raw):
        if offset + 8 > len(raw):
            raise ValueError(f'Truncated GLB chunk header: {path}')
        length, kind = struct.unpack_from('<II', raw, offset)
        offset += 8
        if length % 4 or offset + length > len(raw):
            raise ValueError(f'Invalid GLB chunk length: {path}')
        chunks.append((kind, raw[offset:offset + length]))
        offset += length
    if not chunks or chunks[0][0] != 0x4E4F534A or any(kind not in (0x4E4F534A, 0x004E4942) for kind, _ in chunks):
        raise ValueError(f'Unsupported GLB chunk layout: {path}')
    if sum(kind == 0x4E4F534A for kind, _ in chunks) != 1 or sum(kind == 0x004E4942 for kind, _ in chunks) != 1:
        raise ValueError(f'Expected exactly one JSON and one BIN chunk: {path}')
    document = json.loads(chunks[0][1].rstrip(b' \t\r\n\0'))
    binary = next(data for kind, data in chunks if kind == 0x004E4942)
    return document, binary


def write_glb(document, binary):
    json_chunk = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    json_chunk += b' ' * (-len(json_chunk) % 4)
    binary_chunk = binary + b'\0' * (-len(binary) % 4)
    total = 12 + 8 + len(json_chunk) + 8 + len(binary_chunk)
    return (struct.pack('<4sII', b'glTF', 2, total)
            + struct.pack('<II', len(json_chunk), 0x4E4F534A) + json_chunk
            + struct.pack('<II', len(binary_chunk), 0x004E4942) + binary_chunk)


def map_array(document, key, used):
    old = document.get(key)
    if old is None:
        if used:
            raise ValueError(f'{key} are referenced but missing from the GLB document.')
        return {}
    invalid = [index for index in used
               if not isinstance(index, int) or index < 0 or index >= len(old)]
    if invalid:
        raise ValueError(f'Invalid {key} references: {invalid[:10]}')
    mapping = {index: new for new, index in enumerate(sorted(used))}
    document[key] = [old[index] for index in sorted(used)]
    return mapping


def remap_texture_fields(value, mapping):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith('Texture') and isinstance(child, dict) and isinstance(child.get('index'), int):
                child['index'] = mapping[child['index']]
            else:
                remap_texture_fields(child, mapping)
    elif isinstance(value, list):
        for child in value:
            remap_texture_fields(child, mapping)


def referenced_texture_indices(value, found):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith('Texture') and isinstance(child, dict) and isinstance(child.get('index'), int):
                found.add(child['index'])
            referenced_texture_indices(child, found)
    elif isinstance(value, list):
        for child in value:
            referenced_texture_indices(child, found)


def active_node_indices(document):
    nodes = document.get('nodes', [])
    active = set()
    visiting = set()

    def visit(index):
        if index < 0 or index >= len(nodes):
            raise ValueError(f'Invalid node reference: {index}')
        if index in visiting:
            raise ValueError(f'Node cycle detected at index {index}.')
        if index in active:
            return
        visiting.add(index)
        active.add(index)
        for child in nodes[index].get('children', []):
            visit(child)
        visiting.remove(index)

    scenes = document.get('scenes', [])
    if not scenes:
        raise ValueError('GLB has no scenes.')
    for scene in scenes:
        for index in scene.get('nodes', []):
            visit(index)
    return active


def compact(document, binary, expected_pivots=0):
    if set(document.get('extensionsUsed', [])) - ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported extensions: {sorted(set(document['extensionsUsed']) - ALLOWED_EXTENSIONS)}")
    if document.get('animations') or document.get('skins'):
        raise ValueError('Animated or skinned GLBs are not supported by this compactor.')
    buffers = document.get('buffers', [])
    if len(buffers) != 1 or buffers[0].get('uri'):
        raise ValueError('Expected one embedded GLB buffer.')
    if buffers[0].get('byteLength', 0) > len(binary):
        raise ValueError('GLB buffer exceeds its BIN chunk.')

    original = copy.deepcopy(document)
    original_binary = binary[:buffers[0]['byteLength']]
    keep_nodes = active_node_indices(document)
    node_map = map_array(document, 'nodes', keep_nodes)
    for node in document['nodes']:
        if any(key in node for key in ('camera', 'skin')):
            raise ValueError('Camera and skin node references are not supported by this compactor.')
        node['children'] = [node_map[index] for index in node.get('children', [])]
        if 'mesh' in node:
            node['mesh'] = node['mesh']
    for scene in document.get('scenes', []):
        scene['nodes'] = [node_map[index] for index in scene.get('nodes', [])]

    used_meshes = {original['nodes'][index]['mesh'] for index in keep_nodes
                   if 'mesh' in original['nodes'][index]}
    mesh_map = map_array(document, 'meshes', used_meshes)
    for old_index, new_index in mesh_map.items():
        old_mesh = original['meshes'][old_index]
        new_mesh = document['meshes'][new_index]
        if old_mesh != new_mesh:
            raise ValueError('Unexpected change while pruning meshes.')
    for node in document['nodes']:
        if 'mesh' in node:
            node['mesh'] = mesh_map[node['mesh']]

    used_materials = set()
    for mesh in document.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            if 'material' in primitive:
                used_materials.add(primitive['material'])
    material_map = map_array(document, 'materials', used_materials)
    for mesh in document.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            if 'material' in primitive:
                primitive['material'] = material_map[primitive['material']]

    used_textures = set()
    for material in document.get('materials', []):
        referenced_texture_indices(material, used_textures)
    texture_map = map_array(document, 'textures', used_textures)
    for material in document.get('materials', []):
        remap_texture_fields(material, texture_map)

    used_images = set()
    used_samplers = set()
    for texture in document.get('textures', []):
        if 'source' in texture:
            used_images.add(texture['source'])
        if 'sampler' in texture:
            used_samplers.add(texture['sampler'])
        for extension in texture.get('extensions', {}).values():
            if 'source' in extension:
                used_images.add(extension['source'])
    image_map = map_array(document, 'images', used_images)
    sampler_map = map_array(document, 'samplers', used_samplers)
    for texture in document.get('textures', []):
        if 'source' in texture:
            texture['source'] = image_map[texture['source']]
        if 'sampler' in texture:
            texture['sampler'] = sampler_map[texture['sampler']]
        for extension in texture.get('extensions', {}).values():
            if 'source' in extension:
                extension['source'] = image_map[extension['source']]

    accessor_indices = set()
    for mesh_index in used_meshes:
        mesh = original['meshes'][mesh_index]
        for primitive in mesh.get('primitives', []):
            accessor_indices.update(primitive.get('attributes', {}).values())
            if 'indices' in primitive:
                accessor_indices.add(primitive['indices'])
            for target in primitive.get('targets', []):
                accessor_indices.update(target.values())
    accessor_map = map_array(document, 'accessors', accessor_indices)
    for mesh in document.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            primitive['attributes'] = {key: accessor_map[index] for key, index in primitive.get('attributes', {}).items()}
            if 'indices' in primitive:
                primitive['indices'] = accessor_map[primitive['indices']]
            for target in primitive.get('targets', []):
                for key, index in target.items():
                    target[key] = accessor_map[index]
    for old_index, new_index in mesh_map.items():
        expected_mesh = copy.deepcopy(original['meshes'][old_index])
        for primitive in expected_mesh.get('primitives', []):
            primitive['attributes'] = {key: accessor_map[index] for key, index in primitive.get('attributes', {}).items()}
            if 'indices' in primitive:
                primitive['indices'] = accessor_map[primitive['indices']]
            if 'material' in primitive:
                primitive['material'] = material_map[primitive['material']]
            for target in primitive.get('targets', []):
                for key, index in target.items():
                    target[key] = accessor_map[index]
        if expected_mesh != document['meshes'][new_index]:
            raise ValueError(f'Mesh data changed during compaction: {old_index}')
    for old_index, new_index in material_map.items():
        expected_material = copy.deepcopy(original['materials'][old_index])
        remap_texture_fields(expected_material, texture_map)
        if expected_material != document['materials'][new_index]:
            raise ValueError(f'Material data changed during compaction: {old_index}')
    for old_index, new_index in texture_map.items():
        expected_texture = copy.deepcopy(original['textures'][old_index])
        if 'source' in expected_texture:
            expected_texture['source'] = image_map[expected_texture['source']]
        if 'sampler' in expected_texture:
            expected_texture['sampler'] = sampler_map[expected_texture['sampler']]
        for extension in expected_texture.get('extensions', {}).values():
            if 'source' in extension:
                extension['source'] = image_map[extension['source']]
        if expected_texture != document['textures'][new_index]:
            raise ValueError(f'Texture data changed during compaction: {old_index}')

    used_views = set()
    for accessor in document.get('accessors', []):
        if 'bufferView' in accessor:
            used_views.add(accessor['bufferView'])
        sparse = accessor.get('sparse', {})
        for part in ('indices', 'values'):
            if part in sparse:
                used_views.add(sparse[part]['bufferView'])
    for image in document.get('images', []):
        if 'bufferView' in image:
            used_views.add(image['bufferView'])
    view_map = map_array(document, 'bufferViews', used_views)
    new_binary = bytearray()
    for old_index, new_index in view_map.items():
        old_view = original['bufferViews'][old_index]
        if old_view.get('buffer', 0) != 0 or old_view.get('extensions'):
            raise ValueError('Nonstandard buffer views are not supported by this compactor.')
        start = old_view.get('byteOffset', 0)
        end = start + old_view['byteLength']
        if end > len(original_binary):
            raise ValueError('A referenced buffer view exceeds the source buffer.')
        new_binary.extend(b'\0' * (-len(new_binary) % 4))
        view = document['bufferViews'][new_index]
        view['buffer'] = 0
        view['byteOffset'] = len(new_binary)
        new_binary.extend(original_binary[start:end])

    for accessor in document.get('accessors', []):
        if 'bufferView' in accessor:
            accessor['bufferView'] = view_map[accessor['bufferView']]
        sparse = accessor.get('sparse', {})
        for part in ('indices', 'values'):
            if part in sparse:
                sparse[part]['bufferView'] = view_map[sparse[part]['bufferView']]
    for image in document.get('images', []):
        if 'bufferView' in image:
            image['bufferView'] = view_map[image['bufferView']]
    for old_index, new_index in image_map.items():
        expected_image = copy.deepcopy(original['images'][old_index])
        if 'bufferView' in expected_image:
            expected_image['bufferView'] = view_map[expected_image['bufferView']]
        if expected_image != document['images'][new_index]:
            raise ValueError(f'Image data changed during compaction: {old_index}')
    for old_index, new_index in accessor_map.items():
        expected_accessor = copy.deepcopy(original['accessors'][old_index])
        if 'bufferView' in expected_accessor:
            expected_accessor['bufferView'] = view_map[expected_accessor['bufferView']]
        sparse = expected_accessor.get('sparse', {})
        for part in ('indices', 'values'):
            if part in sparse:
                sparse[part]['bufferView'] = view_map[sparse[part]['bufferView']]
        if expected_accessor != document['accessors'][new_index]:
            raise ValueError(f'Accessor data changed during compaction: {old_index}')
    for old_index, new_index in view_map.items():
        before = original['bufferViews'][old_index]
        after = document['bufferViews'][new_index]
        if {k: v for k, v in before.items() if k != 'byteOffset'} != {k: v for k, v in after.items() if k != 'byteOffset'}:
            raise ValueError(f'Buffer view metadata changed during compaction: {old_index}')
        old_start = before.get('byteOffset', 0)
        new_start = after.get('byteOffset', 0)
        length = before['byteLength']
        if original_binary[old_start:old_start + length] != new_binary[new_start:new_start + length]:
            raise ValueError(f'Buffer view bytes changed during compaction: {old_index}')
    document['buffers'][0]['byteLength'] = len(new_binary)

    # Validate preserved scene structure and node transforms before writing.
    if set(node_map) != keep_nodes:
        raise ValueError('Scene node mapping is incomplete.')
    for old_index, new_index in node_map.items():
        before = original['nodes'][old_index]
        after = document['nodes'][new_index]
        if {k: v for k, v in before.items() if k not in ('children', 'mesh')} != {k: v for k, v in after.items() if k not in ('children', 'mesh')}:
            raise ValueError(f'Node transform or metadata changed: {before.get("name", old_index)}')
        if [node_map[i] for i in before.get('children', [])] != after.get('children', []):
            raise ValueError(f'Node hierarchy changed: {before.get("name", old_index)}')
        if ('mesh' in before) != ('mesh' in after) or ('mesh' in before and after['mesh'] != mesh_map[before['mesh']]):
            raise ValueError(f'Node mesh assignment changed: {before.get("name", old_index)}')
    if len(active_node_indices(document)) != len(keep_nodes):
        raise ValueError('Active scene node count changed during compaction.')
    pivot_count = sum(node.get('extras', {}).get('pantry_role') == 'pivot'
                      for node in document['nodes'])
    if pivot_count != expected_pivots:
        raise ValueError(f'Expected {expected_pivots} active pantry pivot nodes, found {pivot_count}.')
    return document, bytes(new_binary), {
        'nodes_removed': len(original['nodes']) - len(document['nodes']),
        'meshes_removed': len(original['meshes']) - len(document['meshes']),
        'materials_removed': len(original.get('materials', [])) - len(document.get('materials', [])),
        'textures_removed': len(original.get('textures', [])) - len(document.get('textures', [])),
        'images_removed': len(original.get('images', [])) - len(document.get('images', [])),
        'accessors_removed': len(original.get('accessors', [])) - len(document.get('accessors', [])),
        'buffer_views_removed': len(original.get('bufferViews', [])) - len(document.get('bufferViews', [])),
        'source_bytes': len(original_binary),
        'compact_bytes': len(new_binary),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--write', action='store_true', help='replace the current floor GLBs with compacted files')
    action.add_argument('--check', action='store_true', help='verify that both floor GLBs are already compacted (default)')
    args = parser.parse_args()
    results = []
    for floor in (1, 2):
        path = VIEWER / f'House_Floor_{floor}.glb'
        document, binary = read_glb(path)
        expected_pivots = 20 if floor == 1 else 0
        compact_document, compact_binary, counts = compact(document, binary, expected_pivots)
        encoded = write_glb(compact_document, compact_binary)
        result = {'path': str(path.relative_to(ROOT)), **counts,
                  'source_glb_bytes': path.stat().st_size, 'compact_glb_bytes': len(encoded),
                  'saved_bytes': path.stat().st_size - len(encoded)}
        results.append({'path': path, 'encoded': encoded, 'document': compact_document,
                        'binary': compact_binary, 'report': result})
    if args.write:
        pending = []
        temporary_paths = []
        try:
            for row in results:
                if row['report']['saved_bytes'] <= 0:
                    continue
                temporary = row['path'].with_suffix('.compacting.tmp')
                temporary.write_bytes(row['encoded'])
                temporary_paths.append(temporary)
                written_doc, written_binary = read_glb(temporary)
                if written_doc != row['document'] or written_binary[:len(row['binary'])] != row['binary']:
                    raise ValueError(f'Compacted output verification failed: {row["path"]}')
                pending.append((temporary, row['path']))
            for temporary, path in pending:
                temporary.replace(path)
        finally:
            for temporary in temporary_paths:
                temporary.unlink(missing_ok=True)
    output = [row['report'] for row in results]
    print(json.dumps({'written': args.write, 'floors': output}, ensure_ascii=False, indent=2))
    if not args.write and any(row['report']['saved_bytes'] for row in results):
        raise SystemExit('Models contain unreachable payload; review the report and run with --write to compact.')


if __name__ == '__main__':
    main()
