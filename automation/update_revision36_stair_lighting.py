"""Refresh the stair lighting in the floor exports and offline viewer."""
import json
import shutil

import update_revision31_electrical as electrical

def main():
    points = json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    by_id = {point['id']: point for point in points}
    for key in ('L1_097', 'L2_096'):
        if by_id[key]['proposed_group'] != 'STAIR_LIGHT':
            raise ValueError('Stair sconces must be on the same proposed light circuit.')
    electrical.update_floor_glb(1, points, revision=36, patch_config={
        'ids': ('L1_097',), 'replace_ids': (),
        'patch': electrical.ROOT/'.local-preview/revision36_floor1.glb',
    })
    electrical.update_floor_glb(2, points, revision=36, patch_config={
        'ids': ('L2_096',), 'replace_ids': ('L2_096',),
        'patch': electrical.ROOT/'.local-preview/revision36_floor2.glb',
    })
    plan = electrical.rewrite_electrical_svg(1, points)
    if plan['plan_markers'] != sum(point['level']==1 for point in points):
        raise ValueError('Floor 1 plan marker count differs from the schedule.')
    print(json.dumps(plan))
    electrical.build_viewer(electrical.VIEWER/'House_Viewer.html')
    portable = electrical.ROOT.parent/'House_Browser_Viewer'
    if portable.is_dir():
        for name in ('House_Floor_1.glb','House_Floor_2.glb','House_Viewer.html'):
            shutil.copyfile(electrical.VIEWER/name,portable/name)


if __name__ == '__main__':
    main()
