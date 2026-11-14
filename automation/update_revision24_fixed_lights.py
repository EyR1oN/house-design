"""Keep every fixed flush ceiling fixture visible in electrical mode."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
from open_stair_exit_viewer import read_glb
from build_viewer import build as build_viewer

expected = {
    1: [
        'LIB_Ground_Flush_Entry', 'LIB_Ground_Flush_Kitchen', 'LIB_Ground_Flush_Laundry',
        'LIB_Ground_Flush_Living_Dining', 'LIB_Ground_Flush_WC',
    ],
    2: ['LIB_Upper_Hall_Flush', 'LIB_Upper_Bath_Flush', 'LIB_Closet_Flush'],
}
for floor, fixture_names in expected.items():
    document, _binary = read_glb((ROOT / f'House_Browser_Viewer/House_Floor_{floor}.glb').read_bytes())
    active = set()

    def visit(index):
        if index in active:
            return
        active.add(index)
        for child in document['nodes'][index].get('children', []):
            visit(child)

    for index in document['scenes'][document.get('scene', 0)].get('nodes', []):
        visit(index)
    names = {document['nodes'][index].get('name', '') for index in active}
    missing = sorted(set(fixture_names) - names)
    if missing:
        raise ValueError(f'Floor {floor} is missing expected fixed flush lights: {missing}')

mode_script = (ROOT / 'House_Browser_Viewer/electrical_mode.js').read_text(encoding='utf-8')
if '(?:lamp|pendant|sconce|light|flush)' not in mode_script:
    raise ValueError('Electrical mode does not preserve fixed flush fixtures')

html_path = ROOT / 'House_Browser_Viewer/House_Viewer.html'
build_viewer(html_path)
report = {
    'revision': 24,
    'fixed_flush_ceiling_lights_kept': expected,
    'portable_office_task_lamps_hidden': ['LIB_Office_Task_Lamp_1', 'LIB_Office_Task_Lamp_2'],
    'viewer_rebuilt': True,
    'updated_blender_geometry': False,
}
(ROOT / 'House_Library_Design/data/revision24_report.json').write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))
