"""Apply the visual review corrections to the revision 25 Blender master."""
import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
POINTS = PROJECT / 'data/electrical_points.json'
LEGACY = (
    'Ground_WC_sliding_rail', 'Ground_WC_sliding_pull',
    'Upper_bath_sliding_panel', 'Upper_bath_sliding_rail', 'Upper_bath_sliding_pull',
)
MOVES = {
    'E1_001_SOCKET': (0.20, 0),
    'E1_004_SWITCH': (-0.011, 0),
    'E1_013_SOCKET': (0.006, 0),
    'E1_014_DATA': (-0.0196, 0),
    'E2_044_SOCKET': (-0.24, 0),
    'E2_050_SWITCH': (0.093, 0),
    'E2_080_SOCKET': (0.0154, 0),
    'E2_081_DATA': (0.0154, 0),
}


def assembly(pid):
    return [obj for obj in bpy.data.objects
            if obj.name == pid or obj.name.startswith(pid + '_')]


def main():
    if Path(bpy.data.filepath).resolve() != PROJECT / 'House_Library_Design.blend':
        raise RuntimeError('Open the house master before running this migration.')
    scene = bpy.context.scene
    if not scene.get('interior_revision', '').startswith('LIBRARY 25.'):
        raise RuntimeError('This migration requires revision 25.')
    points = json.loads(POINTS.read_text(encoding='utf-8'))
    schedule = {point['id']: point for point in points}
    for name in LEGACY:
        obj = bpy.data.objects[name]
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if not mesh.users:
            bpy.data.meshes.remove(mesh)
    for pid, (dx, dy) in MOVES.items():
        for obj in assembly(pid):
            obj.location += Vector((dx, dy, 0))
        schedule[pid]['x_m'] = round(schedule[pid]['x_m'] + dx, 6)
        if dy:
            schedule[pid]['y_m'] = round(schedule[pid]['y_m'] + dy, 6)

    # Fit two independent controls in the 150 mm gap between wardrobe and jamb.
    pid = 'E2_083_SWITCH'
    plate = bpy.data.objects[pid]
    scale = Matrix.Diagonal((0.54, 1, 1, 1))
    plate.matrix_basis = Matrix.Translation(plate.location) @ scale @ plate.matrix_basis.to_3x3().to_4x4()
    middle = bpy.data.objects[pid + '_rocker.001']
    mesh = middle.data
    bpy.data.objects.remove(middle, do_unlink=True)
    if not mesh.users:
        bpy.data.meshes.remove(mesh)
    for suffix, dx in (('_rocker', 0.030), ('_rocker.002', -0.030)):
        rocker = bpy.data.objects[pid + suffix]
        rocker.location.x = plate.location.x + dx
    bpy.data.objects[pid + '_rocker.002'].name = pid + '_rocker.001'
    schedule[pid]['modules'] = 2

    export_upper_devices(scene)
    scene['interior_revision'] = 'LIBRARY 26.0 visual review and wall-mounted devices'
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
    POINTS.write_text(json.dumps(points, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def export_upper_devices(scene):
    bpy.context.window.view_layer = scene.view_layers['Upper_Design']
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for pid in ('E2_044_SOCKET', 'E2_050_SWITCH', 'E2_081_DATA', 'E2_083_SWITCH'):
        for obj in assembly(pid):
            obj.select_set(True)
    patch = PROJECT.parent / '.local-preview/visual-switches.glb'
    patch.parent.mkdir(exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(patch),
        export_format='GLB', use_selection=True, export_extras=True,
        export_cameras=False, export_lights=False)


if __name__ == '__main__':
    main()
