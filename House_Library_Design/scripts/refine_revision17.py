"""Remove only the upper continuation of the ground-floor TV/storage wall."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / 'House_Library_Design.blend'
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene = bpy.context.scene

upper_name = 'R3_Stair_Landing_Closure'
lower_name = 'R3_Stair_Wall_South'
closet_name = 'R_L2_SOURCE_WALL_1'
threshold_name = 'R3_Stair_Landing_Threshold'
upper = bpy.data.objects.get(upper_name)
lower = bpy.data.objects.get(lower_name)
closet = bpy.data.objects.get(closet_name)
threshold = bpy.data.objects.get(threshold_name)
if not all((lower, closet, threshold)):
    raise RuntimeError('Expected lower TV/storage wall, upstairs closet wall and stair threshold; no edits made.')

def set_layer(name):
    bpy.context.window.view_layer = scene.view_layers[name]
    bpy.context.view_layer.update()

def world_bounds(obj, layer):
    set_layer(layer)
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]

upper_bounds = world_bounds(upper, 'Upper_Design') if upper else [[6.49, 7.03, 2.9], [6.62, 8.4, 5.87]]
lower_bounds = world_bounds(lower, 'Ground_Design')
closet_faces = len(closet.data.polygons)
threshold_bounds = world_bounds(threshold, 'Upper_Design')
if upper and (upper_bounds[0][2] > 3.05 or upper_bounds[1][2] < 5.0):
    raise RuntimeError(f'Unexpected upper TV-wall continuation bounds: {upper_bounds}')
expected_lower = [[6.49, 7.03, 0.0], [6.62, 7.98, 2.9]]
if any(abs(actual - expected) > 0.02 for side, expected_side in zip(lower_bounds, expected_lower)
       for actual, expected in zip(side, expected_side)):
    raise RuntimeError(f'Ground-floor TV/storage wall bounds changed unexpectedly: {lower_bounds}')
if closet_faces < 100:
    raise RuntimeError(f'Closet-side wall mesh looks unexpectedly incomplete: {closet_faces} faces')

if upper:
    bpy.data.objects.remove(upper, do_unlink=True)
    bpy.context.view_layer.update()
assert bpy.data.objects.get(upper_name) is None
assert bpy.data.objects.get(lower_name) is not None
assert bpy.data.objects.get(closet_name) is not None
assert len(bpy.data.objects[closet_name].data.polygons) == closet_faces
assert bpy.data.objects.get(threshold_name) is not None
assert world_bounds(bpy.data.objects[lower_name], 'Ground_Design') == lower_bounds
assert world_bounds(bpy.data.objects[threshold_name], 'Upper_Design') == threshold_bounds

report = {
    'revision': 17,
    'stairs': {
        'removed_upper_tv_wall_extension': upper_name,
        'removed_bounds_m': upper_bounds,
        'ground_floor_tv_storage_wall_preserved': lower_name,
        'ground_floor_wall_bounds_m': lower_bounds,
        'closet_side_wall_preserved': closet_name,
        'closet_wall_face_count': closet_faces,
        'stair_threshold_preserved': threshold_name,
        'threshold_bounds_m': threshold_bounds,
    },
}
(ROOT / 'data' / 'revision17_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
scene['interior_revision'] = 'LIBRARY 17.0 Remove upper TV-wall extension at stair exit'
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
print('REVISION17_TV_WALL_EXTENSION_REMOVED', json.dumps(report['stairs']))
