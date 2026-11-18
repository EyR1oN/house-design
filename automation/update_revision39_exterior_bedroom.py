"""Refresh the electrical plans and viewer for revision 39."""
import json
import shutil

import update_revision31_electrical as electrical
from update_revision34_first_package import remove_merged_fixtures

GROUND = ('E1_099_SOCKET','E1_100_SOCKET','E1_101_SWITCH','E1_102_SWITCH','L1_103','L1_104')
BEDROOM = ('E2_027_SWITCH','E2_030_SWITCH','E2_031_SWITCH')
BEDROOM_LEGACY = {
    'PART_DESIGN_Bedroom': ((((7.985,8.215),(1.01,1.09),(-8.539,-8.518)),752),),
    'PART_Electrical_L2': ((((7.733,7.967),(1.01,1.09),(-8.539,-8.518)),752),),
}


def remove_legacy_curtain(path):
    document,binary = electrical.read_glb(path.read_bytes())
    scene = document['scenes'][document.get('scene',0)]
    roots = scene['nodes']
    old = [i for i in roots if document['nodes'][i].get('name') == 'LIB_Curtain_Living_Dining_6.72']
    if len(old) != 1:
        raise ValueError('Original terrace curtain root not found.')
    roots.remove(old[0])
    path.write_bytes(electrical.write_glb(document,binary))


def main():
    points = json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    electrical.ROOMS_UK['Exterior'] = 'Фасад'
    electrical.PURPOSE_LABELS_UK.update({
        'E1_099_SOCKET': 'Біля входу',
        'E1_100_SOCKET': 'Біля заднього кута',
        'E1_101_SWITCH': 'Світло ґанку',
        'E1_102_SWITCH': 'Світло тераси',
        'L1_103': 'Ґанок',
        'L1_104': 'Тераса',
        'E2_027_SWITCH': 'Стеля та LED',
        'E2_030_SWITCH': 'Лівий підвіс та стеля',
        'E2_031_SWITCH': 'Правий підвіс та стеля',
    })
    remove_legacy_curtain(electrical.VIEWER/'House_Floor_1.glb')
    remove_merged_fixtures(electrical.VIEWER/'House_Floor_2.glb',BEDROOM_LEGACY)
    for floor,ids,replace in (
        (1,GROUND,()),
        (2,BEDROOM,BEDROOM+('E2_091_SWITCH',)),
    ):
        electrical.update_floor_glb(floor,points,revision=39,patch_config={
            'ids': ids,'replace_ids': replace,
            'patch': electrical.ROOT/'.local-preview'/f'revision39_floor{floor}.glb',
        })
        plan = electrical.rewrite_electrical_svg(floor,points)
        expected = sum(point['level']==floor for point in points)
        if plan['plan_markers'] != expected or plan['legend_items'] != expected:
            raise ValueError(f'Floor {floor} electrical plan does not match its schedule.')
        print(json.dumps(plan))
    electrical.build_viewer(electrical.VIEWER/'House_Viewer.html')
    portable = electrical.ROOT.parent/'House_Browser_Viewer'
    if portable.is_dir():
        for name in ('House_Floor_1.glb','House_Floor_2.glb','House_Viewer.html'):
            shutil.copyfile(electrical.VIEWER/name,portable/name)


if __name__ == '__main__':
    main()
