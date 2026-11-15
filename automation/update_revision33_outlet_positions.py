"""Regenerate the electrical plan and offline viewer after revision 33."""
import json
import shutil
from pathlib import Path

import update_revision31_electrical as electrical

ROOT = Path(__file__).resolve().parents[1]
IDS = ('E1_005_SOCKET', 'E1_006_SOCKET', 'E1_022_SOCKET', 'E1_023_SOCKET')


def main():
    electrical.CHANGES[1] = {
        'ids': IDS, 'replace_ids': IDS,
        'patch': ROOT / '.local-preview/revision33_electrical_floor1.glb',
    }
    points = json.loads(electrical.POINTS_PATH.read_text(encoding='utf-8'))
    svg = electrical.rewrite_electrical_svg(1, points)
    expected = sum(p['level'] == 1 for p in points)
    if svg['plan_markers'] != expected or svg['legend_items'] != expected:
        raise ValueError('First-floor plan does not match the schedule.')
    glb = electrical.update_floor_glb(1, points, revision=33)
    electrical.build_viewer(electrical.VIEWER / 'House_Viewer.html')
    for name in ('House_Floor_1.glb', 'House_Viewer.html'):
        shutil.copyfile(electrical.VIEWER/name, ROOT.parent/'House_Browser_Viewer'/name)
    print(json.dumps({'plan': svg, 'model': glb}))


if __name__ == '__main__':
    main()
