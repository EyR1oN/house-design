"""Remove the misplaced child-room switch and export omitted sockets for the viewer."""
from pathlib import Path
import bpy
import json

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'House_Library_Design.blend'
VIEWER = ROOT.parent / 'House_Browser_Viewer'
POINTS = ROOT / 'data' / 'electrical_points.json'
PATCH = VIEWER / 'revision22_child_electrical.glb'

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
upper = scene.view_layers.get('Upper_Design')
if upper is None:
    raise RuntimeError('Upper_Design view layer is missing')
for window in bpy.context.window_manager.windows:
    window.view_layer = upper

# Remove the complete three-rocker switch assembly above the child's bed.
remove_names = {
    'E2_085_SWITCH',
    'E2_085_SWITCH_rocker',
    'E2_085_SWITCH_rocker.001',
    'E2_085_SWITCH_rocker.002',
}
found = {obj.name for obj in bpy.data.objects if obj.name in remove_names}
if found != remove_names:
    raise RuntimeError(f'Unexpected E2_085 assembly: missing={sorted(remove_names - found)}')
for name in sorted(remove_names):
    obj = bpy.data.objects.get(name)
    bpy.data.objects.remove(obj, do_unlink=True)

points = json.loads(POINTS.read_text(encoding='utf-8'))
removed_points = [p for p in points if p.get('id') == 'E2_085_SWITCH']
if len(removed_points) != 1:
    raise RuntimeError(f'Expected one E2_085 point in schedule, found {len(removed_points)}')
points = [p for p in points if p.get('id') != 'E2_085_SWITCH']
POINTS.write_text(json.dumps(points, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

scene['interior_revision'] = 'LIBRARY 22.0 child-room electrical points and switch cleanup'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)

# These two socket assemblies are in the master but absent from the exported L2 GLB.
export_names = []
for point_id in ('E2_080_SOCKET', 'E2_082_SOCKET'):
    related = [
        obj.name for obj in bpy.data.objects
        if obj.name == point_id or obj.name.startswith(point_id + '_')
    ]
    if not related:
        raise RuntimeError(f'No Blender objects found for {point_id}')
    export_names.extend(related)

for obj in bpy.context.selected_objects:
    obj.select_set(False)
for name in export_names:
    obj = bpy.data.objects[name]
    obj.hide_set(False)
    obj.hide_render = False
    obj.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['E2_080_SOCKET']
bpy.ops.export_scene.gltf(
    filepath=str(PATCH),
    use_selection=True,
    export_format='GLB',
    export_cameras=False,
    export_lights=False,
    export_extras=True,
)

if not PATCH.is_file() or PATCH.stat().st_size == 0:
    raise RuntimeError('The child electrical GLB patch was not exported')
print(json.dumps({
    'revision': 22,
    'removed_objects': sorted(remove_names),
    'removed_point_id': 'E2_085_SWITCH',
    'retained_child_points': [p['id'] for p in points if p.get('room') == 'Child_Room'],
    'exported_socket_objects': sorted(export_names),
    'patch': PATCH.name,
    'patch_bytes': PATCH.stat().st_size,
}, ensure_ascii=False))
