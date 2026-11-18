"""Publish revision 34's targeted model changes to the local plans and viewer."""
import json
import shutil
import struct

import update_revision31_electrical as electrical
from open_stair_exit_viewer import accessor

UPPER_REPLACEMENTS = ('E2_047_SWITCH', 'E2_048_SOCKET', 'E2_050_SWITCH',
                      'E2_080_SOCKET', 'E2_082_SOCKET', 'E2_083_SWITCH')
PATCHES = {
    1: (('E1_094_SWITCH',), ()),
    2: (UPPER_REPLACEMENTS + ('L2_095', 'L2_096'), UPPER_REPLACEMENTS),
}

# Coordinates in the identity-transformed room and electrical aggregate meshes.
# Check the triangle count for each original fixture before cutting the export.
LEGACY_FIXTURES = {
    'PART_DESIGN_Child_Room': (
        (((5.484, 5.511), (.910, .990), (-2.678, -2.522)), 684),
        (((8.297, 8.337), (1.06, 1.14), (-1.178, -1.022)), 684),
        (((7.115, 7.345), (1.01, 1.09), (-4.183, -4.149)), 752),
    ),
    'PART_Electrical_L2': (
        (((6.886, 6.913), (1.010, 1.090), (-5.071, -4.990)), 436),
        (((6.883, 6.913), (1.010, 1.090), (-6.078, -5.922)), 564),
    ),
}


def remove_merged_fixtures(path, legacy_fixtures=LEGACY_FIXTURES):
    document, payload = electrical.read_glb(path.read_bytes())
    binary = bytearray(payload)
    for name, fixtures in legacy_fixtures.items():
        node = next(n for n in document['nodes'] if n.get('name') == name)
        if any(key in node for key in ('matrix', 'translation', 'rotation', 'scale')):
            raise ValueError(f'Unexpected transform on {name}')
        counts = [0] * len(fixtures)
        primitives = document['meshes'][node['mesh']]['primitives']
        for primitive in list(primitives):
            if primitive.get('mode', 4) != 4:
                raise ValueError(f'Expected indexed triangles in {name}')
            indices = [i[0] for i in accessor(document, binary, primitive['indices'])]
            vertices = accessor(document, binary, primitive['attributes']['POSITION'])
            kept = []
            for start in range(0, len(indices), 3):
                face = indices[start:start + 3]
                for i, (bounds, _) in enumerate(fixtures):
                    if all(all(lo <= v <= hi for (lo, hi), v in zip(bounds, vertices[j]))
                           for j in face):
                        counts[i] += 1
                        break
                else:
                    kept.extend(face)
            if len(kept) == len(indices):
                continue
            if not kept:
                primitives.remove(primitive)
                continue
            component = document['accessors'][primitive['indices']]['componentType']
            encoded = struct.pack(f"<{len(kept)}" + {5121: 'B', 5123: 'H', 5125: 'I'}[component], *kept)
            binary.extend(b'\0' * (-len(binary) % 4))
            view = len(document['bufferViews'])
            document['bufferViews'].append(dict(buffer=0, byteOffset=len(binary),
                                                byteLength=len(encoded), target=34963))
            binary.extend(encoded)
            primitive['indices'] = len(document['accessors'])
            document['accessors'].append(dict(bufferView=view, componentType=component,
                    type='SCALAR', count=len(kept), min=[min(kept)], max=[max(kept)]))
        if counts != [count for _, count in fixtures]:
            raise ValueError(f'Unexpected merged fixture triangle counts: {name} {counts}')
    document['buffers'][0]['byteLength'] = len(binary)
    path.write_bytes(electrical.write_glb(document, binary))


def main():
    points = json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    remove_merged_fixtures(electrical.VIEWER / 'House_Floor_2.glb')
    for floor, (ids, old_ids) in PATCHES.items():
        glb = electrical.update_floor_glb(floor, points, revision=34, patch_config={
            'ids': ids, 'replace_ids': old_ids,
            'patch': electrical.ROOT / '.local-preview' / f'revision34_floor{floor}.glb',
        })
        plan = electrical.rewrite_electrical_svg(floor, points)
        expected = sum(point['level'] == floor for point in points)
        if plan['plan_markers'] != expected or plan['legend_items'] != expected:
            raise ValueError(f'Electrical plan {floor} differs from its schedule')
        print(json.dumps({'glb': glb, 'plan': plan}))

    electrical.build_viewer(electrical.VIEWER / 'House_Viewer.html')
    portable = electrical.ROOT.parent / 'House_Browser_Viewer'
    if portable.is_dir():
        for name in ('House_Floor_1.glb', 'House_Floor_2.glb', 'House_Viewer.html',
                     'electrical_mode.js'):
            shutil.copyfile(electrical.VIEWER / name, portable / name)


if __name__ == '__main__':
    main()
