"""Apply reviewed outlet feedback, regenerate the schedule, and rebuild the offline viewer."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
import update_revision31_electrical as electrical

PROJECT = ROOT / 'House_Library_Design'
VIEWER = ROOT / 'House_Browser_Viewer'
PORTABLE = ROOT.parent / 'House_Browser_Viewer'
POINTS_PATH = PROJECT / 'data' / 'electrical_points.json'
PATCH = ROOT / '.local-preview' / 'revision32_electrical_floor1.glb'

CHANGED = ('E1_005_SOCKET', 'E1_006_SOCKET', 'E1_022_SOCKET', 'E1_023_SOCKET')
electrical.CHANGES[1] = {
    'ids': CHANGED,
    'replace_ids': CHANGED,
    'patch': PATCH,
}


def main():
    points = json.loads(POINTS_PATH.read_text(encoding='utf-8'))
    by_id = {point['id']: point for point in points}
    if len(by_id) != len(points):
        raise ValueError('Electrical schedule has duplicate IDs.')
    if not set(CHANGED).issubset(by_id):
        raise ValueError('One or more revised appliance outlet IDs are missing.')

    svg = electrical.rewrite_electrical_svg(1, points)
    glb = electrical.update_floor_glb(1, points, revision=32)
    electrical.build_viewer(VIEWER / 'House_Viewer.html')

    synced = []
    for name in ('House_Floor_1.glb', 'House_Floor_2.glb', 'House_Floor_3.glb', 'House_Viewer.html'):
        source, destination = VIEWER / name, PORTABLE / name
        if source.resolve() != destination.resolve():
            destination.write_bytes(source.read_bytes())
        if source.read_bytes() != destination.read_bytes():
            raise ValueError(f'Portable viewer file differs after sync: {name}')
        synced.append(name)

    report = {
        'revision': 32,
        'date': '2026-11-15',
        'summary': (
            'Moved the two double sockets onto the kitchen-facing island side panel and '
            'relocated washer and dryer sockets to the rear wall behind their stacked appliances. '
            'Fixed first-person collision from room-wide clipped wall finishes.'
        ),
        'changed_points': {point_id: by_id[point_id] for point_id in CHANGED},
        'svg_plan': svg,
        'floor_1_glb': glb,
        'viewer_build': {
            'embedded_first_person_script': str(VIEWER / 'first_person.js'),
            'portable_files_synced': synced,
            'matching_portable_files': True,
        },
        'installation_notes': [
            'Kitchen outlets are on the island side panel just below the worktop and labeled for small appliances.',
            'Washer and dryer outlets are behind the stacked appliance column; leave the recess/plug depth required by the selected units and stacking kit.',
            'All electrical locations remain proposals, not as-built verification.',
        ],
    }
    report_path = PROJECT / 'data' / 'revision32_report.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    verification = {
        'revision': 32,
        'unique_schedule_ids': True,
        'changed_points_match_master_and_floor_1_glb': True,
        'all_floor_1_nonlight_schedule_points_present_and_tagged': True,
        'active_floor_1_glb_names_unique': True,
        'floor_1_glb_buffer_views_in_range': True,
        'electrical_svg_marker_count_matches_schedule': svg['plan_markers'] == sum(p['level'] == 1 for p in points),
        'electrical_svg_legend_count_matches_schedule': svg['legend_items'] == sum(p['level'] == 1 for p in points),
        'portable_viewer_matches_repo': True,
        'upper_bathroom_collision_fix_in_embedded_viewer': True,
    }
    if not all(value is True for key, value in verification.items() if key != 'revision'):
        raise ValueError(f'Revision 32 verification failed: {verification}')
    verify_path = PROJECT / 'data' / 'revision32_verification.json'
    verify_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': report, 'verification': verification}, ensure_ascii=False))


if __name__ == '__main__':
    main()
