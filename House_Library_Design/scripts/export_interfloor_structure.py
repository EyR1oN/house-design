"""Export the existing upper-floor concrete slab and screed for the web viewer.

This creates a small temporary GLB patch and never saves or edits the master.
Run Blender with House_Library_Design.blend open as the input file.
"""
from pathlib import Path

import bpy

PROJECT = Path(__file__).resolve().parents[1]
MASTER = PROJECT / 'House_Library_Design.blend'
PATCH = PROJECT.parent / '.local-preview' / 'interfloor-structure.glb'
NAMES = ('R_L2_STRUCTURAL_SLAB', 'R_L2_SCREED')

if Path(bpy.data.filepath).resolve() != MASTER.resolve():
    raise RuntimeError(f'Open the current house master before exporting: {MASTER}')

scene = bpy.context.scene
bpy.context.window.view_layer = scene.view_layers['Exterior']
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')

for name in NAMES:
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != 'MESH':
        raise RuntimeError(f'Missing structural mesh: {name}')
    obj.hide_set(False)
    obj.select_set(True)
    print(f'INTERFLOOR_SOURCE {name}: bounds={tuple(round(v, 4) for v in obj.dimensions)}')

bpy.context.view_layer.objects.active = bpy.data.objects[NAMES[0]]
PATCH.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=str(PATCH),
    use_selection=True,
    export_format='GLB',
    export_cameras=False,
    export_lights=False,
    export_extras=True,
)
print(f'INTERFLOOR_PATCH {PATCH} ({PATCH.stat().st_size} bytes); master unchanged')
