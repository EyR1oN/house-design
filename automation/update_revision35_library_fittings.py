"""Update the floor exports and offline viewer for the library fittings."""
import json
import shutil

import update_revision31_electrical as electrical

CABINET = 'LIB_Ground_WC_Overtoilet_Cabinet'
CHANGES = {1: ('E1_094_SWITCH',), 2: ('L2_095', 'L2_096')}


def remove_old_cabinet(path):
    document, binary = electrical.read_glb(path.read_bytes())
    scene = document['scenes'][document.get('scene',0)]
    roots = scene['nodes']
    old = {i for i in roots if document['nodes'][i].get('name','').startswith(CABINET+'_')}
    if len(old) != 10:
        raise ValueError(f'Expected ten original cabinet parts, found {len(old)}')
    scene['nodes'] = [i for i in roots if i not in old]
    path.write_bytes(electrical.write_glb(document, binary))


def main():
    points = json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    remove_old_cabinet(electrical.VIEWER/'House_Floor_1.glb')
    for floor, ids in CHANGES.items():
        report = electrical.update_floor_glb(floor, points, revision=35, patch_config={
            'ids': ids, 'replace_ids': ids,
            'patch': electrical.ROOT/'.local-preview'/f'revision35_floor{floor}.glb',
        })
        plan = electrical.rewrite_electrical_svg(floor, points)
        expected = sum(p['level'] == floor for p in points)
        if plan['plan_markers'] != expected or plan['legend_items'] != expected:
            raise ValueError(f'Floor {floor} plan marker mismatch.')
        print(json.dumps({'glb': report, 'plan': plan}))
    electrical.build_viewer(electrical.VIEWER/'House_Viewer.html')
    portable = electrical.ROOT.parent/'House_Browser_Viewer'
    if portable.is_dir():
        for name in ('House_Floor_1.glb','House_Floor_2.glb','House_Viewer.html'):
            shutil.copyfile(electrical.VIEWER/name, portable/name)


if __name__ == '__main__':
    main()
