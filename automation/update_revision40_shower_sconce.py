"""Update the viewer and first-floor electrical plan for the shower sconce."""
import json
import re
import shutil

import update_revision31_electrical as electrical


def main():
    points = json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    electrical.ROOMS_UK['Exterior']='Фасад'
    electrical.PURPOSE_LABELS_UK.update({
        'E1_005_SOCKET':'Фартух · блендер і міксер',
        'E1_006_SOCKET':'Фартух · дрібна техніка',
        'E1_025_SWITCH':'Стеля й бра / витяжка',
        'E1_099_SOCKET':'Біля входу',
        'E1_100_SOCKET':'Біля заднього кута',
        'E1_101_SWITCH':'Світло ґанку',
        'E1_102_SWITCH':'Світло тераси',
        'L1_103':'Ґанок',
        'L1_104':'Тераса',
        'L1_105':'Бра над дзеркалом',
    })
    report=electrical.update_floor_glb(1,points,revision=40,patch_config={
        'ids': ('L1_105',),'replace_ids':(),
        'patch': electrical.ROOT/'.local-preview/revision40_floor1.glb',
    })
    if len(report['patch_nodes'])!=6:
        raise ValueError('Incomplete library sconce.')
    plan=electrical.rewrite_electrical_svg(1,points)
    expected=sum(p['level']==1 for p in points)
    if plan['plan_markers']!=expected or plan['legend_items']!=expected:
        raise ValueError('Electrical plan count differs from schedule.')
    svg_path=electrical.PROJECT/'exports/Electrical_Points_Floor_1.svg'
    svg=svg_path.read_text(encoding='utf-8')
    new_height=max(1860,230+(expected-1)*35+40)
    svg=re.sub(r'(height=")1860(" viewBox="0 0 1660 )1860(")',rf'\g<1>{new_height}\g<2>{new_height}\3',svg,count=1)
    svg=svg.replace('<rect width="1660" height="1860"',f'<rect width="1660" height="{new_height}"',1)
    svg_path.write_text(svg,encoding='utf-8')
    print(json.dumps(plan))
    electrical.build_viewer(electrical.VIEWER/'House_Viewer.html')
    portable=electrical.ROOT.parent/'House_Browser_Viewer'
    if portable.is_dir():
        for name in ('House_Floor_1.glb','House_Viewer.html'):
            shutil.copyfile(electrical.VIEWER/name,portable/name)


if __name__=='__main__':
    main()
