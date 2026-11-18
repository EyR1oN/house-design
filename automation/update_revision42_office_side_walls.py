"""Update the upper electrical plan and 3D export for the office side outlets."""
import json
import shutil

import update_revision31_electrical as electrical

OUTLETS = ('E2_107_SOCKET','E2_108_SOCKET')


def main():
    points = json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    electrical.PURPOSE_LABELS_UK.update({
        'E2_027_SWITCH':'Стеля та LED',
        'E2_030_SWITCH':'Лівий підвіс та стеля',
        'E2_031_SWITCH':'Правий підвіс та стеля',
        'E2_038_SOCKET':'Центр двох столів',
        'E2_042_SOCKET':'3D-принтер',
        'E2_045_SWITCH':'Стеля / витяжка',
        'E2_107_SOCKET':'Бічна стіна біля крісла 1',
        'E2_108_SOCKET':'Протилежна стіна біля крісла 2',
    })
    electrical.update_floor_glb(2,points,revision=42,patch_config={
        'ids':OUTLETS,'replace_ids':OUTLETS,
        'patch':electrical.ROOT/'.local-preview/revision42_floor2.glb',
    })
    plan = electrical.rewrite_electrical_svg(2,points)
    expected = sum(p['level']==2 for p in points)
    if plan['plan_markers'] != expected or plan['legend_items'] != expected:
        raise ValueError('Upper plan differs from the schedule.')
    print(json.dumps(plan))
    portable = electrical.ROOT.parent/'House_Browser_Viewer'
    if portable.is_dir():
        shutil.copyfile(electrical.VIEWER/'House_Floor_2.glb',portable/'House_Floor_2.glb')


if __name__=='__main__':
    main()
