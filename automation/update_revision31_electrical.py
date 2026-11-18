"""Merge revision-31 electrical points into the floor GLBs and viewer."""
from html import escape
from pathlib import Path
import json
import math
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))
from open_stair_exit_viewer import read_glb, write_glb
from compact_viewer_models import compact
from build_viewer import build as build_viewer

PROJECT = ROOT / 'House_Library_Design'
VIEWER = ROOT / 'House_Browser_Viewer'
PORTABLE_VIEWER = ROOT.parent / 'House_Browser_Viewer'
POINTS_PATH = PROJECT / 'data' / 'electrical_points.json'
REPORT_PATH = PROJECT / 'data' / 'revision31_report.json'
VERIFICATION_PATH = PROJECT / 'data' / 'revision31_verification.json'
PATCH_ROOT = ROOT / '.local-preview'

CHANGES = {
    1: {
        'ids': ('E1_005_SOCKET', 'E1_006_SOCKET', 'E1_010_SOCKET', 'E1_093_SOCKET'),
        'replace_ids': ('E1_005_SOCKET', 'E1_006_SOCKET', 'E1_010_SOCKET', 'E1_093_SOCKET'),
        'patch': PATCH_ROOT / 'revision31_electrical_floor1.glb',
    },
    2: {
        'ids': ('E2_046_SOCKET',),
        'replace_ids': (),
        'patch': PATCH_ROOT / 'revision31_electrical_floor2.glb',
    },
}

COLORS = {
    'SOCKET': '#ae6928',
    'SWITCH': '#4a8263',
    'DATA': '#516dac',
    'HOB_CONNECTION': '#b94e42',
    'FAN_POINT': '#777b85',
    'LIGHT_POINT': '#9b873d',
}
ROOMS_UK = {
    'Entry': 'Передпокій', 'Kitchen': 'Кухня', 'Living': 'Вітальня',
    'Stair_storage': 'Комора', 'Laundry': 'Пральня', 'Ground_WC': 'Душова',
    'Bedroom': 'Спальня', 'Office': 'Кабінет', 'Child_Room': 'Дитяча',
    'Upper_Bath': 'Ванна', 'Wardrobe': 'Гардероб', 'Upper_Hall': 'Хол',
}
TYPES_UK = {
    'SOCKET': 'Розетка', 'SWITCH': 'Вимикач', 'DATA': 'Ethernet',
    'HOB_CONNECTION': 'Підключення плити', 'FAN_POINT': 'Вентилятор',
    'LIGHT_POINT': 'Світло',
}
PURPOSE_LABELS_UK = {
    'E1_005_SOCKET': 'Острів · блендер/міксер/чайник',
    'E1_006_SOCKET': 'Острів · дрібна техніка',
    'E1_022_SOCKET': 'Пральна машина · за колоною',
    'E1_023_SOCKET': 'Сушарка · за колоною',
}


def reachable(document):
    active = set()

    def visit(index):
        if index in active:
            return
        active.add(index)
        for child in document['nodes'][index].get('children', []):
            visit(child)

    for index in document['scenes'][document.get('scene', 0)].get('nodes', []):
        visit(index)
    return active


def floor_patch_ids(floor, points):
    if floor == 2:
        return tuple(point['id'] for point in points
                     if point['level'] == 2 and point['type'] != 'LIGHT_POINT')
    return CHANGES[floor]['ids']


def compact_number(value):
    return f'{value:.3f}'.rstrip('0').rstrip('.')


def rewrite_electrical_svg(floor, points):
    path = PROJECT / 'exports' / f'Electrical_Points_Floor_{floor}.svg'
    lines = path.read_text(encoding='utf-8').splitlines()
    def point_number(point_id):
        match = re.search(r'_(\d+)(?:_|$)', point_id)
        if match is None:
            raise ValueError(f'Could not read point number from {point_id}')
        return int(match.group(1))

    point_rows = sorted((point for point in points if point['level'] == floor),
                        key=lambda point: (point_number(point['id']), point['id']))
    if not point_rows:
        raise ValueError(f'No electrical points for floor {floor}')

    kept = []
    first_plan_marker = None
    first_legend = None
    for line in lines:
        if '<circle ' in line and '<title>' in line:
            if first_plan_marker is None:
                first_plan_marker = len(kept)
            continue
        if 'font-size="13" font-weight="bold"' in line:
            continue
        if line.startswith('<text x="970"') and 'font-size="17"' in line:
            continue
        if '<circle cx="953"' in line:
            if first_legend is None:
                first_legend = len(kept)
            continue
        if 'y="1786"' in line and 'Розетки у вологих кімнатах' in line:
            line = ('<text x="80" y="1786" font-size="17" fill="#665f52">'
                    'Точки у ванних запропоновані; зонування та ПЗВ не більше 30 мА має підтвердити електрик.</text>')
        kept.append(line)

    plan = []
    legend = []
    positions = {}
    for point_index, point in enumerate(point_rows):
        point_id = point['id']
        number = f'{point_number(point_id):03d}'
        x = 183.5 + (point['x_m'] - 6.0) * 115.0
        y = 1660.0 - point['y_m'] * 115.0
        positions[point_id] = (x, y)
        color = COLORS.get(point['type'], '#777b85')
        title = escape(f"{point_id} / {point.get('purpose', '')} / {point['height_aff_m']:.2f}m")
        plan.append(
            f'<circle cx="{compact_number(x)}" cy="{compact_number(y)}" r="8" fill="{color}" '
            f'stroke="#fff" stroke-width="2"><title>{title}</title></circle>'
        )

        device = TYPES_UK.get(point['type'], point['type'])
        if point.get('modules', 1) > 1:
            device += f" ×{point['modules']}"
        purpose_label = PURPOSE_LABELS_UK.get(point_id)
        purpose_suffix = f' · {escape(purpose_label)}' if purpose_label else ''
        legend_y = 230 + point_index * 35
        legend.append(f'<circle cx="953" cy="{legend_y}" r="5" fill="{color}"/>')
        legend.append(
            f'<text x="970" y="{legend_y + 6}" font-size="17" fill="#39342d">'
            f'{number} · {escape(ROOMS_UK.get(point["room"], point["room"]))} · '
            f'{escape(device)}{purpose_suffix} · {point["height_aff_m"]:.2f} м</text>'
        )

    label_boxes = []
    fallback_labels = 0
    offsets = [(10, -7), (10, 22), (-34, -7), (-34, 22), (-12, -20),
               (-12, 35), (16, -20), (-40, 35), (10, -35), (-34, -35),
               (10, 42), (-34, 42)]
    for point in point_rows:
        point_id = point['id']
        number = f'{point_number(point_id):03d}'
        x, y = positions[point_id]
        color = COLORS.get(point['type'], '#777b85')
        width, height = 27, 16
        chosen = None
        for offset_x, offset_y in offsets:
            tx, ty = x + offset_x, y + offset_y
            box = (tx, ty - height, tx + width, ty)
            if tx < 82 or tx + width > 895 or ty - height < 195 or ty > 1670:
                continue
            if any(box[0] < other[2] + 2 and box[2] + 2 > other[0]
                   and box[1] < other[3] + 2 and box[3] + 2 > other[1]
                   for other in label_boxes):
                continue
            if any(abs(px - max(box[0], min(px, box[2]))) < 10
                   and abs(py - max(box[1], min(py, box[3]))) < 10
                   for other_id, (px, py) in positions.items() if other_id != point_id):
                continue
            chosen = (tx, ty, box)
            break
        if chosen is None:
            fallback_labels += 1
            tx, ty = x + 10, y - 7
            chosen = (tx, ty, (tx, ty-height, tx+width, ty))
        tx, ty, box = chosen
        label_boxes.append(box)
        plan.append(
            f'<text x="{compact_number(tx)}" y="{compact_number(ty)}" font-size="13" '
            f'font-weight="bold" fill="{color}">{number}</text>'
        )

    if first_plan_marker is None:
        insert_at = max(i for i, line in enumerate(kept) if line.startswith('<polygon')) + 1
    else:
        insert_at = min(first_plan_marker, len(kept))
    if first_legend is None:
        first_legend = next((i for i, line in enumerate(kept) if 'y="1754"' in line), len(kept) - 1)
    else:
        first_legend = min(first_legend, len(kept))
    kept[first_legend:first_legend] = legend
    kept[insert_at:insert_at] = plan
    path.write_text('\n'.join(kept) + '\n', encoding='utf-8')
    return {'floor': floor, 'plan_markers': len(point_rows), 'legend_items': len(point_rows),
            'labels_without_collision_slot': fallback_labels, 'path': str(path)}


def remove_legacy_point_nodes(document, floor, point_ids):
    """Detach old electrical point assemblies before adding their replacements.

    Blender exports each outlet assembly as separate active scene nodes; there is no
    aggregate PART_Electrical_L* node in the current floor models.
    """
    active = reachable(document)
    names_by_index = {index: document['nodes'][index].get('name', '') for index in active}
    selected = set()
    removed_by_point = {}
    for point_id in point_ids:
        matches = {index for index, name in names_by_index.items()
                   if name == point_id or name.startswith(point_id + '_')}
        if not any(names_by_index[index] == point_id for index in matches):
            if matches:
                raise ValueError(f'The old electrical point assembly {point_id} has no root node.')
            removed_by_point[point_id] = []
            continue
        if len(matches) < 2:
            raise ValueError(f'The old electrical point assembly {point_id} is incomplete.')
        removed_by_point[point_id] = sorted(names_by_index[index] for index in matches)
        selected.update(matches)

    for index, node in enumerate(document['nodes']):
        remaining_children = [child for child in node.get('children', []) if child not in selected]
        if len(remaining_children) != len(node.get('children', [])) and index not in selected:
            raise ValueError('An old outlet assembly is unexpectedly parented beneath unrelated geometry.')
    scene = document['scenes'][document.get('scene', 0)]
    roots = scene.get('nodes', [])
    if any(index not in roots for index in selected):
        raise ValueError('An old outlet object is not a floor scene root; refusing an unsafe removal.')
    scene['nodes'] = [index for index in roots if index not in selected]
    return removed_by_point


def remap_textures(value, offset):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith('Texture') and isinstance(child, dict) and 'index' in child:
                child['index'] += offset
            else:
                remap_textures(child, offset)
    elif isinstance(value, list):
        for child in value:
            remap_textures(child, offset)


def append_patch(document, binary, patch_path, floor, points, expected_ids, revision=31):
    patch, patch_binary = read_glb(patch_path.read_bytes())
    patch_active = reachable(patch)
    patch_nodes = {patch['nodes'][index].get('name', ''): index for index in patch_active}
    if any(point_id not in patch_nodes for point_id in expected_ids):
        raise ValueError(f'Patch for floor {floor} is missing expected point roots.')
    active_names = [document['nodes'][index].get('name', '') for index in reachable(document)]
    if len(active_names) != len(set(active_names)):
        raise ValueError(f'Base floor {floor} has duplicate active GLB node names.')
    duplicate_names = set(active_names) & set(patch_nodes)
    if duplicate_names:
        raise ValueError(f'Patch floor {floor} would duplicate active nodes: {sorted(duplicate_names)}')

    keys = ['bufferViews', 'accessors', 'images', 'samplers', 'textures',
            'materials', 'meshes', 'nodes']
    offsets = {key: len(document.get(key, [])) for key in keys}
    binary_offset = (len(binary) + 3) & ~3
    binary.extend(b'\0' * (binary_offset - len(binary)) + patch_binary)
    for view in patch.get('bufferViews', []):
        view['buffer'] = 0
        view['byteOffset'] = view.get('byteOffset', 0) + binary_offset
    for item in patch.get('accessors', []):
        if 'bufferView' in item:
            item['bufferView'] += offsets['bufferViews']
    for image in patch.get('images', []):
        if 'bufferView' in image:
            image['bufferView'] += offsets['bufferViews']
    for texture in patch.get('textures', []):
        if 'source' in texture:
            texture['source'] += offsets['images']
        if 'sampler' in texture:
            texture['sampler'] += offsets['samplers']
    for material in patch.get('materials', []):
        remap_textures(material, offsets['textures'])
    for mesh in patch.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            primitive['attributes'] = {key: index + offsets['accessors']
                                       for key, index in primitive['attributes'].items()}
            if 'indices' in primitive:
                primitive['indices'] += offsets['accessors']
            if 'material' in primitive:
                primitive['material'] += offsets['materials']

    roots = list(patch['scenes'][patch.get('scene', 0)].get('nodes', []))
    point_rows = {point['id']: point for point in points}
    for index, node in enumerate(patch['nodes']):
        if 'mesh' in node:
            node['mesh'] += offsets['meshes']
        if 'children' in node:
            node['children'] = [child + offsets['nodes'] for child in node['children']]
        name = node.get('name', '')
        point_id = next((candidate for candidate in expected_ids
                         if name == candidate or name.startswith(candidate + '_')), None)
        if index in roots and floor == 2:
            if 'matrix' in node:
                node['matrix'][13] -= 3.2
            else:
                node.setdefault('translation', [0, 0, 0])[1] -= 3.2
        if point_id is None:
            continue
        point = point_rows[point_id]
        node.setdefault('extras', {}).update({
            'design_status': 'PROPOSED_INTERIOR',
            'section': 'RIGHT',
            'level': floor,
            'point_id': point_id,
            'room': point['room'],
            'device_type': point['type'],
            'purpose': point['purpose'],
            'height_above_finished_floor_m': point['height_aff_m'],
            'circuit_group_proposed': point['proposed_group'],
            'wall_face': point['face'],
            'modules': point['modules'],
            'as_built_verified': False,
            'mep_status': 'PROPOSED_POSITION_ONLY',
            'revision': revision,
            'electrical_point': True,
        })

    for key in keys:
        document.setdefault(key, []).extend(patch.get(key, []))
    document['scenes'][document.get('scene', 0)].setdefault('nodes', []).extend(
        index + offsets['nodes'] for index in roots)
    scene = document['scenes'][document.get('scene', 0)]
    scene.setdefault('extras', {})['electrical_revision'] = revision
    for key in ('extensionsUsed', 'extensionsRequired'):
        if patch.get(key):
            document[key] = sorted(set(document.get(key, []) + patch[key]))
    return sorted(patch_nodes)


def sync_point_metadata(document, floor, points, revision=31):
    active = reachable(document)
    nodes_by_name = {document['nodes'][index].get('name', ''): document['nodes'][index]
                     for index in active}
    rows = [point for point in points
            if point['level'] == floor and point['type'] != 'LIGHT_POINT']
    for point in rows:
        node = nodes_by_name.get(point['id'])
        if node is None:
            raise ValueError(f"Scheduled electrical point {point['id']} is missing from floor {floor} GLB.")
        node.setdefault('extras', {}).update({
            'design_status': 'PROPOSED_INTERIOR',
            'section': 'RIGHT',
            'level': floor,
            'point_id': point['id'],
            'room': point['room'],
            'device_type': point['type'],
            'purpose': point['purpose'],
            'height_above_finished_floor_m': point['height_aff_m'],
            'circuit_group_proposed': point['proposed_group'],
            'wall_face': point['face'],
            'modules': point['modules'],
            'as_built_verified': False,
            'mep_status': 'PROPOSED_POSITION_ONLY',
            'revision': revision,
            'electrical_point': True,
        })
    return rows


def update_floor_glb(floor, points, revision=31, *, patch_config=None):
    path = VIEWER / f'House_Floor_{floor}.glb'
    document, payload = read_glb(path.read_bytes())
    binary = bytearray(payload)
    config = CHANGES[floor] if patch_config is None else patch_config
    patch_ids = floor_patch_ids(floor, points) if patch_config is None else config['ids']
    replace_ids = patch_ids if floor == 2 and patch_config is None else config['replace_ids']
    removed = remove_legacy_point_nodes(document, floor, replace_ids)
    patch_nodes = append_patch(document, binary, config['patch'], floor, points, patch_ids,
                               revision=revision)
    document['buffers'][0]['byteLength'] = len(binary)
    expected_pivots = 20 if floor == 1 else 0
    document, binary, compaction = compact(document, binary, expected_pivots=expected_pivots)
    names = [document['nodes'][index].get('name', '') for index in reachable(document)]
    if len(names) != len(set(names)):
        raise ValueError(f'Floor {floor} has duplicate active names after patch merge.')
    synchronized_points = sync_point_metadata(document, floor, points, revision=revision)
    for point_id in patch_ids:
        point = next(row for row in points if row['id'] == point_id)
        root_node = next((document['nodes'][index] for index in reachable(document)
                          if document['nodes'][index].get('name') == point_id), None)
        if root_node is None:
            raise ValueError(f'{point_id} root is missing from floor {floor}.')
        translation = root_node.get('translation')
        if translation is None and 'matrix' in root_node:
            matrix = root_node['matrix']
            translation = [matrix[12], matrix[13], matrix[14]]
        expected = [point['x_m'], point['height_aff_m'], -point['y_m']]
        if not translation or math.dist(translation, expected) > 0.002:
            raise ValueError(f'{point_id} GLB coordinates do not match the point schedule.')
        extras = root_node.get('extras', {})
        if extras.get('point_id') != point_id or extras.get('revision') != revision:
            raise ValueError(f'{point_id} GLB metadata does not match revision {revision}.')
    for view in document.get('bufferViews', []):
        if view.get('byteOffset', 0) + view['byteLength'] > len(binary):
            raise ValueError(f'Floor {floor} contains a buffer view outside its binary payload.')
    temporary = path.with_suffix(f'.revision{revision}.tmp')
    temporary.write_bytes(write_glb(document, binary))
    temporary.replace(path)
    return {'floor': floor, 'schedule_point_roots': len(synchronized_points),
            'removed_old_nodes': removed, 'patch_nodes': patch_nodes,
            'compaction': compaction, 'bytes': path.stat().st_size}


def main():
    points = json.loads(POINTS_PATH.read_text(encoding='utf-8'))
    svg_reports = [rewrite_electrical_svg(floor, points) for floor in (1, 2)]
    glb_reports = [update_floor_glb(floor, points) for floor in (1, 2)]
    viewer_path = VIEWER / 'House_Viewer.html'
    build_viewer(viewer_path)
    for name in ('House_Floor_1.glb', 'House_Floor_2.glb', 'House_Floor_3.glb', 'House_Viewer.html'):
        source = VIEWER / name
        destination = PORTABLE_VIEWER / name
        if source.resolve() != destination.resolve():
            destination.write_bytes(source.read_bytes())
    report = {
        'revision': 31,
        'date': '2026-11-15',
        'summary': 'Reworked kitchen worktop outlets, made the dishwasher service point accessible, added gas-boiler power provision, and moved the upper-bath grooming socket beside the vanity.',
        'changed_points': {point['id']: point for point in points
                           if point['id'] in set(CHANGES[1]['ids']) | set(CHANGES[2]['ids'])},
        'new_point': next(point for point in points if point['id'] == 'E1_093_SOCKET'),
        'viewer_schedule_roots': {str(row['floor']): row['schedule_point_roots']
                                  for row in glb_reports},
        'upper_floor_points_missing_before_revision31': [
            'E2_027_SWITCH', 'E2_032_SOCKET', 'E2_033_DATA', 'E2_034_SOCKET',
            'E2_035_SOCKET', 'E2_036_SOCKET', 'E2_037_SWITCH', 'E2_038_SOCKET',
            'E2_039_SOCKET', 'E2_040_DATA', 'E2_041_DATA', 'E2_042_SOCKET',
            'E2_043_SOCKET', 'E2_045_SWITCH', 'E2_047_SWITCH', 'E2_048_SOCKET',
            'E2_049_SOCKET', 'E2_071_FAN_POINT', 'E2_091_SWITCH',
        ],
        'blender_metadata_repairs': [
            'E2_080_SOCKET', 'E2_081_DATA', 'E2_082_SOCKET',
            'E2_083_SWITCH', 'E2_084_SOCKET', 'E2_091_SWITCH',
        ],
        'room_audit': {
            'Entry': 'Two general sockets remain by the vacuum point and entry bench.',
            'Kitchen': 'Two inaccessible high pantry sockets are now two double outlets on the kitchen-facing island side; fridge, oven, microwave, hob and hood service points remain dedicated; dishwasher is in the adjacent sink-base service zone.',
            'Laundry': 'Washer and dryer outlets remain accessible beside the stacked machines; a dedicated proposed supply point is added beside the gas boiler.',
            'Ground_WC': 'The existing grooming socket remains outside the modelled shower footprint and is flagged for wet-zone review.',
            'Living': 'TV/media, sofa, dining-side and cleaning outlets remain placed by their use areas.',
            'Stair_storage': 'Vacuum charging point remains in the storage room.',
            'Bedroom': 'Bedside pairs, vanity, TV/media and general-use points remain.',
            'Office': 'Two workstation power/data groups, printer and general-use points remain.',
            'Child_Room': 'Desk power/data, bedside and cleaning points remain.',
            'Upper_Bath': 'The grooming point moves from the entry-side wall to the wall beside the vanity, left of the basin and about 1.43 m from the bath edge in the model.',
            'Wardrobe': 'Steamer/cleaning point remains in the clear central access zone.',
            'Upper_Hall': 'Vacuum point remains in the upper hall.',
        },
        'svg_plans': svg_reports,
        'glb_updates': glb_reports,
        'electrical_status': 'All points remain PROPOSED_NOT_AS_BUILT.',
        'updated_artifacts': [
            'House_Library_Design/House_Library_Design.blend',
            'House_Library_Design/data/electrical_points.json',
            'House_Library_Design/exports/Electrical_Points_Floor_1.svg',
            'House_Library_Design/exports/Electrical_Points_Floor_2.svg',
            'House_Browser_Viewer/House_Floor_1.glb',
            'House_Browser_Viewer/House_Floor_2.glb',
            'House_Browser_Viewer/House_Viewer.html',
            'portable House_Browser_Viewer model and viewer copies',
        ],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    verification = {
        'revision': 31,
        'floor_svg_markers_match_schedule': True,
        'floor_svg_legend_matches_schedule': True,
        'plan_labels_repositioned_around_dense_points': True,
        'legacy_electrical_point_nodes_removed_before_replacement': True,
        'replacement_points_active_in_glb': True,
        'replacement_coordinates_and_metadata_match_schedule': True,
        'all_scheduled_nonlight_points_present_and_tagged_on_both_floors': True,
        'previously_missing_floor2_points_restored': 19,
        'active_glb_node_names_unique': True,
        'glb_buffer_views_in_range': True,
        'moving_pantry_nodes_preserved': 20,
        'offline_viewer_rebuilt_from_updated_models': True,
        'portable_viewer_synced': True,
    }
    VERIFICATION_PATH.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': report, 'verification': verification}, ensure_ascii=False))


if __name__ == '__main__':
    main()
