"""Add a matching lower stair sconce on the shared stair light circuit."""
import json
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
MASTER = PROJECT/'House_Library_Design.blend'
POINTS = PROJECT/'data/electrical_points.json'
PLACEMENTS = PROJECT/'data/placements.json'
OUTPUT = PROJECT.parent/'.local-preview'

bpy.ops.wm.open_mainfile(filepath=str(MASTER))
scene = bpy.context.scene
if scene.get('electrical_revision') != 35:
    raise ValueError('Expected revision 35 master.')
points = json.loads(POINTS.read_text(encoding='utf-8'))
placements = json.loads(PLACEMENTS.read_text(encoding='utf-8'))
source_placement = next(p for p in placements if p['label'] == 'Stairs_Wall_Sconce')
sources = [bpy.data.objects[name] for name in source_placement['objects']]
upper = sources[0]
upper_location = upper.location.copy()

for window in bpy.context.window_manager.windows:
    window.view_layer = scene.view_layers['Ground_Design']
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
y, z = 10.70, 2.08
for sample_y in (y-.07,y,y+.07):
    hit, p, normal, _, support, _ = scene.ray_cast(
        deps, Vector((5.76,sample_y,z)), Vector((-1,0,0)), distance=.35)
    if not hit or support.name != 'R_L1_SOURCE_WALL_3' or normal.x < .99:
        raise ValueError('Lower stair sconce has no clear mounting surface.')
anchor = Vector((round(p.x,5),y,z))
delta = anchor - upper_location
collection = bpy.data.collections.new('LIB_Stairs_Lower_Wall_Sconce')
bpy.context.scene.collection.children.link(collection)
parts = []
key = 'L1_097'
for source in sources:
    part = source.copy()
    part.name = key + source.name[len(upper.name):]
    part.matrix_world = Matrix.Translation(delta) @ source.matrix_world
    part['level'] = 1
    part['point_id'] = key
    collection.objects.link(part)
    parts.append(part)
points.append(dict(id=key, level=1, room='Stairs', type='LIGHT_POINT', x_m=anchor.x,
    y_m=y, height_aff_m=z, face='E', modules=1, proposed_group='STAIR_LIGHT',
    purpose='Lower stair wall light controlled together with the upper sconce',
    status='PROPOSED_NOT_AS_BUILT'))
placements.append(dict(source_placement, label='Stairs_Lower_Wall_Sconce', level=1,
    bounds=[[v+delta[i] for v in pair] for i,pair in enumerate(source_placement['bounds'])],
    objects=[part.name for part in parts]))

off = bpy.data.materials.new('Stair sconces - unlit bulb')
off.diffuse_color = (.76, .72, .65, 1)
off.use_nodes = True
shader = off.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = off.diffuse_color
shader.inputs['Roughness'].default_value = .34
for part in sources + parts:
    slots = [i for i, mat in enumerate(part.data.materials)
             if mat and mat.use_nodes and any(node.type == 'EMISSION' for node in mat.node_tree.nodes)]
    if slots:
        part.data = part.data.copy()
        for i in slots:
            part.data.materials[i] = off

for floor, layer, fixtures in ((1,'Ground_Design',parts),(2,'Upper_Design',sources)):
    for window in bpy.context.window_manager.windows:
        window.view_layer = scene.view_layers[layer]
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for part in fixtures:
        part.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT/f'revision36_floor{floor}.glb'),
        use_selection=True, export_format='GLB', export_extras=True,
        export_cameras=False, export_lights=False)
scene['electrical_revision'] = 36
scene['interior_revision'] = 'LIBRARY 36.0 two stair sconces'
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER), compress=True)
for path, data in ((POINTS,points),(PLACEMENTS,placements)):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
