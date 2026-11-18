"""Refresh the upper GLB, electrical plan and local viewer after revision 38."""
import json
import shutil

import update_revision31_electrical as electrical


def main():
    points = json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    electrical.update_floor_glb(2,points,revision=38,patch_config={
        'ids': ('E2_098_SOCKET',), 'replace_ids': (),
        'patch': electrical.ROOT/'.local-preview/revision38_floor2.glb',
    })
    plan = electrical.rewrite_electrical_svg(2,points)
    expected = sum(p['level']==2 for p in points)
    if plan['plan_markers'] != expected or plan['legend_items'] != expected:
        raise ValueError('Upper electrical plan differs from the schedule.')
    print(json.dumps(plan))
    electrical.build_viewer(electrical.VIEWER/'House_Viewer.html')
    portable = electrical.ROOT.parent/'House_Browser_Viewer'
    if portable.is_dir():
        for name in ('House_Floor_2.glb','House_Viewer.html'):
            shutil.copyfile(electrical.VIEWER/name,portable/name)


if __name__ == '__main__':
    main()
