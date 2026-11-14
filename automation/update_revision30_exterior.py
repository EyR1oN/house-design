"""Assemble the PDF exterior exports into the existing browser models."""
from math import cos, radians, sin
from pathlib import Path
import struct

from compact_viewer_models import compact, read_glb, write_glb
from open_stair_exit_viewer import accessor

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / 'House_Browser_Viewer'
WORK = ROOT / '.local-preview'


def replace_office_leaf_pose(doc, binary):
    """Translate only the existing glass and moving leaf frame to their actual hinge."""
    angle = radians(65)
    # Changing the pivot by -0.94 m only translates the rotated leaf.
    shifts = (-.94 * (1-cos(angle)), 0, -.94*sin(angle))
    for name, mat, expected in (
        ('PART_R_L2_DOORS','WEB_glass',24),
        ('PART_DESIGN_Office','WEB_R3 Exterior door leaf frame',96),
    ):
        node = next(n for n in doc['nodes'] if n.get('name') == name)
        if any(k in node for k in ('matrix','translation','rotation','scale')):
            raise ValueError(f'Unexpected transform for {name}')
        prim, = (p for p in doc['meshes'][node['mesh']]['primitives']
                 if doc['materials'][p['material']]['name'] == mat)
        ix = prim['attributes']['POSITION']
        a = doc['accessors'][ix]
        view = doc['bufferViews'][a['bufferView']]
        points = accessor(doc, binary, ix)
        hits = [i for i,(x,y,z) in enumerate(points)
                if 10.50<x<11.25 and .02<z<.40 and .03<y<2.50]
        if len(hits) != expected or a['componentType'] != 5126:
            raise ValueError(f'Office balcony leaf layout changed: {name}, {len(hits)} vertices')
        if sum(p['attributes'].get('POSITION') == ix for m in doc['meshes'] for p in m['primitives']) != 1:
            raise ValueError('Office balcony position accessor is shared')
        stride = view.get('byteStride',12)
        start = view.get('byteOffset',0)+a.get('byteOffset',0)
        for i in hits:
            points[i] = tuple(x+s for x,s in zip(points[i],shifts))
            struct.pack_into('<3f', binary, start+i*stride, *points[i])
        a['min'], a['max'] = [[f(coords) for coords in zip(*points)] for f in (min,max)]


def append_exterior(doc, binary, patch, payload, floor):
    if any(patch.get(k) for k in ('images','textures','extensionsUsed','animations','skins')):
        raise ValueError('Expected plain exterior meshes and materials')
    roots = patch['scenes'][patch.get('scene',0)]['nodes']
    if len(roots) != len(patch['nodes']) or any(n.get('children') for n in patch['nodes']):
        raise ValueError('Expected a flat exterior export')
    base_names = {n.get('name') for n in doc['nodes']}
    if any(n.get('name') in base_names for n in patch['nodes']):
        raise ValueError(f'Exterior already attached to floor {floor}')
    keys = ('bufferViews','accessors','materials','meshes','nodes')
    off = {k:len(doc[k]) for k in keys}
    binary.extend(b'\0' * (-len(binary)%4))
    for v in patch['bufferViews']:
        v['byteOffset'] = v.get('byteOffset',0)+len(binary)
    binary.extend(payload[:patch['buffers'][0]['byteLength']])
    for a in patch['accessors']:
        a['bufferView'] += off['bufferViews']
    for mesh in patch['meshes']:
        for p in mesh['primitives']:
            p['indices'] += off['accessors']
            p['material'] += off['materials']
            p['attributes'] = {k:v+off['accessors'] for k,v in p['attributes'].items()}
    for n in patch['nodes']:
        n['mesh'] += off['meshes']
        if floor == 2:
            if 'matrix' in n:
                n['matrix'][13] -= 3.2
            else:
                n.setdefault('translation',[0,0,0])[1] -= 3.2
    for k in keys:
        doc[k].extend(patch[k])
    doc['scenes'][doc.get('scene',0)]['nodes'].extend(n+off['nodes'] for n in roots)
    doc['buffers'][0]['byteLength'] = len(binary)


def main():
    results = []
    for floor,tag in ((1,'entry'),(2,'balconies'),(3,'roof')):
        patch,payload = read_glb(WORK/f'exterior-{tag}.glb')
        if floor == 3:
            doc,binary = patch,payload
        else:
            doc,past = read_glb(WORK/'pre-exterior'/f'House_Floor_{floor}.glb')
            binary = bytearray(past)
            if floor == 2:
                replace_office_leaf_pose(doc,binary)
            append_exterior(doc,binary,patch,payload,floor)
        doc,binary,_ = compact(doc,binary,expected_pivots=20 if floor==1 else 0)
        names = [n.get('name') for n in doc['nodes']]
        if len(names) != len(set(names)):
            raise ValueError(f'Duplicate model nodes in floor {floor}')
        results.append((VIEWER/f'House_Floor_{floor}.glb',write_glb(doc,binary)))
    for path,data in results:
        temporary = path.with_suffix('.exterior.tmp')
        temporary.write_bytes(data)
        temporary.replace(path)


if __name__ == '__main__':
    main()
