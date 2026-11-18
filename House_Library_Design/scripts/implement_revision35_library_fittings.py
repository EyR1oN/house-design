"""Move the stair switch to the terrace wall and use library fittings."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
MODEL = PROJECT / 'House_Library_Design.blend'
POINTS = PROJECT / 'data/electrical_points.json'
PLACEMENTS = PROJECT / 'data/placements.json'
OUTPUT = PROJECT.parent / '.local-preview'
CABINET = 'LIB_Ground_WC_Overtoilet_Cabinet'
MANIFEST = {row['role']: row for row in json.loads(
    (PROJECT/'data/library_manifest.json').read_text(encoding='utf-8'))}

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
if scene.get('electrical_revision') != 34:
    raise ValueError('Expected the revision 34 master.')
points = json.loads(POINTS.read_text(encoding='utf-8'))
rows = {row['id']: row for row in points}
placements = json.loads(PLACEMENTS.read_text(encoding='utf-8'))


def layer(name):
    for window in bpy.context.window_manager.windows:
        window.view_layer = scene.view_layers[name]
    bpy.context.view_layer.update()


def assembly(key):
    return [obj for obj in scene.objects if obj.name == key or obj.name.startswith(key+'_')]


def export(floor, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT/f'revision35_floor{floor}.glb'),
        use_selection=True, export_format='GLB', export_extras=True,
        export_cameras=False, export_lights=False)


def place(role, label, group, level, sources, rotation, transform_source, anchor, dimensions,
          collection, point_id=None):
    corners = [rotation @ transform_source(obj) @ Vector(v)
               for obj in sources for v in obj.bound_box]
    lo = Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    hi = Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    scale = [d / (hi[i]-lo[i]) if d else 1.0 for i, d in enumerate(dimensions)]
    offset = Vector((lo.x if point_id else (lo.x+hi.x)/2,
                     (lo.y+hi.y)/2 if point_id else hi.y, (lo.z+hi.z)/2))
    transform = Matrix.Translation(anchor) @ Matrix.Diagonal((*scale,1)) @ Matrix.Translation(-offset) @ rotation
    meta = MANIFEST[role]
    new_parts = []
    for i, original in enumerate(sources):
        copy = original.copy()
        copy.parent = None
        copy.matrix_world = transform @ transform_source(original)
        copy.name = (point_id if i == 0 else f'{point_id}_Library_{i}') if point_id else f'{CABINET}_Library_{i}'
        collection.objects.link(copy)
        # Linked library materials and meshes stay intact.
        for key, value in dict(library_role=role, source_url=meta['source_url'],
                               license=meta['license'], level=level).items():
            copy[key] = value
        if point_id:
            copy['viewer_fixed_light'] = True
            copy['electrical_point'] = True
        new_parts.append(copy)
    if point_id:
        # Make the point origin the mounting datum while preserving library geometry.
        head = new_parts[0]
        world = head.matrix_world.copy()
        head.data = head.data.copy()
        head.data.transform(Matrix.Translation(-Vector(anchor)) @ world)
        head.matrix_world = Matrix.Translation(anchor)
    vertices = [transform @ transform_source(obj) @ Vector(v)
                for obj in sources for v in obj.bound_box]
    placements.append(dict(label=label, role=role, group=group, level=level,
        source_url=meta['source_url'], license=meta['license'], scale=scale,
        bounds=[[min(v[i] for v in vertices),max(v[i] for v in vertices)] for i in range(3)],
        objects=[obj.name for obj in new_parts]))
    return new_parts


layer('Ground_Design')
key = 'E1_094_SWITCH'
switch = bpy.data.objects[key]
old = switch.location.copy()
deps = bpy.context.evaluated_depsgraph_get()
x = 6.55
for test_x in (x-.0375, x, x+.0375):
    hit, loc, normal, _, surface, _ = scene.ray_cast(
        deps, Vector((test_x,11.54,1.05)), Vector((0,1,0)), distance=.4)
    if not hit or surface.name != 'R_L1_SOURCE_WALL_3' or normal.y > -.99:
        raise ValueError(f'Terrace-wall switch is obstructed at x={test_x}: {surface}')
dest = Vector((x, loc.y-.0055, 1.05))
switch_parts = assembly(key)
move = Matrix.Translation(dest) @ Matrix.Rotation(-math.pi/2,4,'Z') @ Matrix.Translation(-old)
for part in switch_parts:
    part.matrix_world = move @ part.matrix_world
purpose = 'Lower two-way stair light control beside terrace door, before first step'
switch['purpose'] = purpose
switch['wall_face'] = 'S'
rows[key].update(x_m=dest.x, y_m=dest.y, face='S', purpose=purpose)

old_cabinet = assembly(CABINET)
cabinet_collection = old_cabinet[0].users_collection[0]
with bpy.data.libraries.load(str(PROJECT/'assets/prepared/wall_kitchen_cabinet.blend')) as (source, target):
    names = {'Cube_PREPARED','Cube.001_PREPARED','Cylinder.001_PREPARED','Cylinder.002_PREPARED'}
    target.objects = [name for name in source.objects if name in names]
if len(target.objects) != len(names):
    raise ValueError('Opaque single cabinet variant is incomplete.')
for obj in old_cabinet:
    bpy.data.objects.remove(obj, do_unlink=True)
cabinet = place('wall_kitchen_cabinet','Ground_WC_Overtoilet_Cabinet','WC',1,
    target.objects, Matrix.Rotation(math.pi/2,4,'X'), lambda o:o.matrix_basis,
    (5.94,7.028,1.80),(.54,.28,.61),cabinet_collection)
export(1,switch_parts+cabinet)

layer('Upper_Design')
source_lamp = sorted(assembly('LIB_Upper_Bath_Sconce_9.06'), key=lambda o:o.name)
if len(source_lamp) != 6:
    raise ValueError('Iron Wall Sconce library instance is incomplete.')
new_lights = []
for key, label, group in (('L2_095','Child_Reading_Sconce','Child_Room'),
                           ('L2_096','Stairs_Wall_Sconce','Stairs')):
    original_parts = assembly(key)
    collection = original_parts[0].users_collection[0]
    row = rows[key]
    row['x_m'] = 5.49005
    if key == 'L2_095':
        row['installation_detail'] = 'Select a version with a control on the fixture within reach from the bed.'
    for obj in original_parts:
        bpy.data.objects.remove(obj, do_unlink=True)
    new_lights += place('sconce',label,group,2,source_lamp,
        Matrix.Rotation(-math.pi/2,4,'Z'), lambda o:o.matrix_world,
        (row['x_m'],row['y_m'],3.2+row['height_aff_m']),(None,None,.30),collection,key)
export(2,new_lights)

scene['interior_revision'] = 'LIBRARY 35.0 terrace stair switch and library fittings'
scene['electrical_revision'] = 35
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)
POINTS.write_text(json.dumps(points, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
PLACEMENTS.write_text(json.dumps(placements, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
