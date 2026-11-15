"""Revision 33: mount worktop outlets on the backsplash and laundry outlets behind the stack."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'House_Library_Design.blend'
POINTS = ROOT / 'data/electrical_points.json'
PATCH = ROOT.parent / '.local-preview/revision33_electrical_floor1.glb'
# Start the wall ray in the free space immediately in front of the mounting surface.
TARGETS = {
    'E1_005_SOCKET': (7.0, 1.12, 9.95, 'Hob_stone_splash', math.pi,
                      'Blender and mixer at the worktop beside the hob'),
    'E1_006_SOCKET': (7.0, 1.28, 9.95, 'Hob_stone_splash', math.pi,
                      'Second small appliance outlet at the worktop beside the hob'),
    'E1_022_SOCKET': (3.45, .55, 10.35, 'R_L1_SOURCE_WALL_6', -math.pi/2,
                      'Washer outlet directly behind the washer'),
    'E1_023_SOCKET': (3.45, 1.45, 10.35, 'R_L1_SOURCE_WALL_6', -math.pi/2,
                      'Dryer outlet directly behind the dryer'),
}

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
for window in bpy.context.window_manager.windows:
    window.view_layer = scene.view_layers['Ground_Design']
deps = bpy.context.evaluated_depsgraph_get()
points = json.loads(POINTS.read_text(encoding='utf-8'))
schedule = {p['id']: p for p in points}
bpy.ops.object.select_all(action='DESELECT')
for key, (y, z, start, surface, angle, purpose) in TARGETS.items():
    point = schedule[key]
    root = bpy.data.objects[key]
    old = root.location.copy()
    if point['face'] != ('E' if surface == 'Hob_stone_splash' else 'S'):
        raise ValueError(f'Unexpected baseline orientation: {key}')
    hit, contact, normal, _, obj, _ = scene.ray_cast(deps, Vector((start,y,z)), Vector((1,0,0)))
    if not hit or obj.name != surface or normal.x > -.99:
        raise ValueError(f'Unexpected mounting surface: {key}')
    center = Vector((round(contact.x - .0055, 6), y, z))
    transform = Matrix.Translation(center) @ Matrix.Rotation(angle,4,'Z') @ Matrix.Translation(-old)
    parts = [o for o in bpy.data.objects if o.name == key or o.name.startswith(key+'_')]
    if len(parts) < 2 or any(o.parent or o.constraints for o in parts):
        raise ValueError(f'Unexpected outlet assembly: {key}')
    for part in parts:
        part.matrix_world = transform @ part.matrix_world
        part.select_set(True)
    point.update(x_m=center.x, y_m=y, height_aff_m=z, face='W', purpose=purpose,
                 installation_detail=(
                    'On the hood backsplash beside the hob, outside the cooking surface footprint.'
                    if surface == 'Hob_stone_splash' else
                    'Centered behind the appliance on the wall facing its rear panel. Confirm plug clearance and service access with the selected appliance.'
                 ))
    root['wall_face'] = 'W'
    root['height_above_finished_floor_m'] = z
    root['purpose'] = purpose

bpy.context.view_layer.update()
for key in TARGETS:
    root = bpy.data.objects[key]
    holes = [o for o in bpy.data.objects if o.name.startswith(key+'_hole')]
    if not holes or any(o.location.x >= root.location.x for o in holes):
        raise ValueError(f'Outlet face points into the wall: {key}')
scene['interior_revision'] = 'LIBRARY 33.0 backsplash and rear appliance outlets'
scene['electrical_revision'] = 33
bpy.ops.export_scene.gltf(filepath=str(PATCH), use_selection=True, export_format='GLB',
                          export_cameras=False, export_lights=False, export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)
POINTS.write_text(json.dumps(points, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
