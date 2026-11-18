"""Refresh both exported floors and electrical plans for revision 41."""
import json
import shutil

import update_revision31_electrical as electrical
from update_revision34_first_package import remove_merged_fixtures

BATH_ROOTS = {'LIB_Upper_Bath_Sconce_9.06','LIB_Upper_Bath_Sconce_10.44'}
OFFICE_LEGACY = (
    (((11.380,11.402),(1.081,1.159),(-3.268,-2.812)),1292),
    (((11.380,11.402),(1.081,1.159),(-4.588,-4.132)),1292),
)
UPPER_LEGACY = {
    'PART_Electrical_L2': (
        (((8.319,8.342),(1.011,1.089),(-6.764,-6.536)),752),
    ) + OFFICE_LEGACY,
}


def remove_old_bath_lights(path):
    document,binary=electrical.read_glb(path.read_bytes())
    scene=document['scenes'][document.get('scene',0)]
    roots=scene['nodes']
    old={i for i in roots if document['nodes'][i].get('name') in BATH_ROOTS}
    if len(old)!=len(BATH_ROOTS):
        raise ValueError('The old upper-bath sconces were not found.')
    scene['nodes']=[i for i in roots if i not in old]
    path.write_bytes(electrical.write_glb(document,binary))


def mark_reserve():
    path=electrical.PROJECT/'exports/Electrical_Points_Floor_1.svg'
    data=path.read_text(encoding='utf-8')
    overlay=(
        '<rect x="226.05" y="1577.2" width="64.4" height="59.8" rx="3" '
        'fill="none" stroke="#68547b" stroke-width="2" stroke-dasharray="6 4">'
        '<title>Вільне місце для майбутньої станції або батареї</title></rect>\n'
        '<text x="80" y="1850" font-size="17" fill="#68547b">'
        'Пунктир у прихожій · резерв місця для станції або батареї.</text>\n'
    )
    path.write_text(data.replace('</g></svg>',overlay+'</g></svg>',1),encoding='utf-8')


def main():
    points=json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    electrical.COLORS['PANEL']='#68547b'
    electrical.TYPES_UK['PANEL']='Щиток'
    electrical.ROOMS_UK['Exterior']='Фасад'
    electrical.PURPOSE_LABELS_UK.update({
        'E1_005_SOCKET':'Фартух · блендер і міксер',
        'E1_006_SOCKET':'Фартух · дрібна техніка',
        'E1_025_SWITCH':'Стеля / витяжка',
        'E1_099_SOCKET':'Біля входу',
        'E1_100_SOCKET':'Біля заднього кута',
        'E1_101_SWITCH':'Світло ґанку',
        'E1_102_SWITCH':'Світло тераси',
        'L1_103':'Ґанок',
        'L1_104':'Тераса',
        'E1_106_PANEL':'Головний',
        'E2_027_SWITCH':'Стеля та LED',
        'E2_030_SWITCH':'Лівий підвіс та стеля',
        'E2_031_SWITCH':'Правий підвіс та стеля',
        'E2_038_SOCKET':'Центр двох столів',
        'E2_042_SOCKET':'3D-принтер',
        'E2_045_SWITCH':'Стеля / витяжка',
        'E2_107_SOCKET':'Зовнішній край стола 1',
        'E2_108_SOCKET':'Зовнішній край стола 2',
    })
    upper_path=electrical.VIEWER/'House_Floor_2.glb'
    remove_old_bath_lights(upper_path)
    remove_merged_fixtures(upper_path,UPPER_LEGACY)
    for floor,ids,replace in (
        (1,('E1_106_PANEL',),('L1_105',)),
        (2,('E2_038_SOCKET','E2_045_SWITCH','E2_107_SOCKET','E2_108_SOCKET'),
         ('E2_038_SOCKET','E2_039_SOCKET','E2_045_SWITCH')),
    ):
        electrical.update_floor_glb(floor,points,revision=41,patch_config={
            'ids': ids,'replace_ids': replace,
            'patch': electrical.ROOT/'.local-preview'/f'revision41_floor{floor}.glb',
        })
        plan=electrical.rewrite_electrical_svg(floor,points)
        expected=sum(p['level']==floor for p in points)
        if plan['plan_markers']!=expected or plan['legend_items']!=expected:
            raise ValueError(f'Floor {floor} plan does not match the schedule.')
        print(json.dumps(plan))
    mark_reserve()
    electrical.build_viewer(electrical.VIEWER/'House_Viewer.html')
    portable=electrical.ROOT.parent/'House_Browser_Viewer'
    if portable.is_dir():
        for name in ('House_Floor_1.glb','House_Floor_2.glb','House_Viewer.html'):
            shutil.copyfile(electrical.VIEWER/name,portable/name)


if __name__=='__main__':
    main()
