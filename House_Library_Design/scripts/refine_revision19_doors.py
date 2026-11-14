from pathlib import Path
import bpy, json, math
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'House_Library_Design.blend'))
scene = bpy.context.scene
for window in bpy.context.window_manager.windows:
    window.view_layer = scene.view_layers['Ground_Design']
bpy.context.view_layer.update()

placements_path = ROOT / 'data/placements.json'
placements = json.loads(placements_path.read_text(encoding='utf8'))
history = json.loads((ROOT / 'data/revision3_report.json').read_text(encoding='utf8'))
old_doors = {door['id']: door for door in history['doors']}
selected = [
    {
        'id': 'L1_KITCHEN_DOOR',
        'hinge_side': 'left/west jamb, unchanged',
        'target_angle_deg': -90,
        'description': 'Opens toward the entry foyer, to the left when approached from the foyer',
        'rehinge': False,
    },
    {
        'id': 'L1_LAUNDRY_DOOR',
        'hinge_side': 'south jamb (right jamb from the foyer approach)',
        'target_angle_deg': 90,
        'description': 'Pulls toward the entry foyer and parks to the right when approached from the foyer',
        'rehinge': False,
    },
]

def rotate_about(point, angle_deg):
    return (Matrix.Translation(point)
            @ Matrix.Rotation(math.radians(angle_deg), 4, 'Z')
            @ Matrix.Translation(-point))

def bounds_for(objects):
    bpy.context.view_layer.update()
    points = [obj.matrix_world @ Vector(corner)
              for obj in objects for corner in obj.bound_box]
    return [[min(p[i] for p in points), max(p[i] for p in points)] for i in range(3)]

report = {'revision': 19, 'doors': [], 'changed_objects': [], 'unchanged_other_door_instances': True}
exports = []
for item in selected:
    door_id = item['id']
    old = old_doors[door_id]
    row = next(row for row in placements if row['label'] == 'Door_' + door_id)
    objects = [bpy.data.objects[name] for name in row['objects']]
    old_pivot = Vector(old['hinge'])
    old_angle = old['angle_deg']
    inverse = rotate_about(old_pivot, -old_angle)
    closed = {obj.name: inverse @ obj.matrix_world.copy()
              for obj in objects if obj.get('hinged_leaf')}
    leaf = next(obj for obj in objects
                if obj.get('hinged_leaf') and 'Door.001' in obj.get('source_object_name', ''))
    closed_points = [closed[leaf.name] @ Vector(corner) for corner in leaf.bound_box]

    if item['rehinge']:
        # Move the hinge edge from the south end to the north end of the closed leaf.
        far_y = max(point.y for point in closed_points)
        hinge_x = (min(point.x for point in closed_points)
                   + max(point.x for point in closed_points)) / 2
        new_pivot = Vector((hinge_x, far_y, 0.0))
        center = (old_pivot + new_pivot) / 2
        hand_flip = rotate_about(center, 180)
        closed = {name: hand_flip @ matrix for name, matrix in closed.items()}
    else:
        new_pivot = old_pivot.copy()

    final_rotation = rotate_about(new_pivot, item['target_angle_deg'])
    moving_names = []
    for obj in objects:
        if obj.name in closed:
            obj.matrix_world = final_rotation @ closed[obj.name]
            obj['door_hinge_world'] = list(new_pivot)
            obj['door_open_angle_deg'] = item['target_angle_deg']
            obj['door_swing_description'] = item['description']
            obj['door_instance_id'] = door_id
            moving_names.append(obj.name)
            report['changed_objects'].append(obj.name)

    bpy.context.view_layer.update()
    row['bounds'] = bounds_for(objects)
    door_record = {
        'id': door_id,
        'approach': 'entry foyer',
        'previous_hinge_world_m': list(old_pivot),
        'new_hinge_world_m': list(new_pivot),
        'previous_angle_deg': old_angle,
        'new_angle_deg': item['target_angle_deg'],
        'hinge_side': item['hinge_side'],
        'rehinged': item['rehinge'],
        'swing_description': item['description'],
        'moving_objects': moving_names,
        'fixed_objects': [obj.name for obj in objects if obj.name not in moving_names],
        'bounds_m': row['bounds'],
    }
    report['doors'].append(door_record)
    exports.extend(row['objects'])

scene['interior_revision'] = 'LIBRARY 19.0 entry and laundry door swings'
placements_path.write_text(json.dumps(placements, ensure_ascii=False, indent=2), encoding='utf8')
(ROOT / 'data/revision19_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'House_Library_Design.blend'), compress=True)

for obj in bpy.context.selected_objects:
    obj.select_set(False)
for name in exports:
    bpy.data.objects[name].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects[exports[0]]
patch_path = ROOT.parent / 'House_Browser_Viewer/revision19_doors_floor1.glb'
bpy.ops.export_scene.gltf(
    filepath=str(patch_path), use_selection=True, export_format='GLB',
    export_cameras=False, export_lights=False, export_extras=True,
)
print('REVISION19_DOORS_SAVED', json.dumps(report, ensure_ascii=False), flush=True)
print('REVISION19_PATCH_EXPORTED', patch_path, patch_path.stat().st_size, flush=True)
