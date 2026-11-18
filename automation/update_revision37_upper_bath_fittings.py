"""Replace the upper bathroom fittings in the floor export and viewer."""
import json
import shutil

import update_revision31_electrical as electrical

SOCKET = 'E2_046_SOCKET'
TOWEL_ROOTS = {'LIB_Upper_Bath_Towel_Radiator', 'LIB_Upper_Bath_Hanging_Towel'}


def main():
    points = json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    path = electrical.VIEWER/'House_Floor_2.glb'
    document, binary = electrical.read_glb(path.read_bytes())
    scene = document['scenes'][document.get('scene',0)]
    roots = scene['nodes']
    old = {i for i in roots if document['nodes'][i].get('name') in TOWEL_ROOTS}
    if len(old) != len(TOWEL_ROOTS):
        raise ValueError('Original bathroom fittings were not found.')
    scene['nodes'] = [i for i in roots if i not in old]
    path.write_bytes(electrical.write_glb(document,binary))
    report = electrical.update_floor_glb(2, points, revision=37, patch_config={
        'ids': (SOCKET,), 'replace_ids': (SOCKET,),
        'patch': electrical.ROOT/'.local-preview/revision37_floor2.glb',
    })
    if not all(any(name.startswith(root+'_') for name in report['patch_nodes'])
               for root in TOWEL_ROOTS):
        raise ValueError('Bathroom fitting patch is missing a library asset.')
    plan = electrical.rewrite_electrical_svg(2, points)
    if plan['plan_markers'] != sum(p['level'] == 2 for p in points):
        raise ValueError('Upper floor electrical plan differs from schedule.')
    print(json.dumps(plan))
    electrical.build_viewer(electrical.VIEWER/'House_Viewer.html')
    portable = electrical.ROOT.parent/'House_Browser_Viewer'
    if portable.is_dir():
        for name in ('House_Floor_2.glb','House_Viewer.html'):
            shutil.copyfile(electrical.VIEWER/name,portable/name)


if __name__ == '__main__':
    main()
