"""Apply the first room and electrical changes agreed after revision 33."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
MODEL = PROJECT / 'House_Library_Design.blend'
POINTS = PROJECT / 'data/electrical_points.json'
OUTPUT = PROJECT.parent / '.local-preview'

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
if scene.get('electrical_revision') != 33:
    raise RuntimeError('Expected the revision 33 master.')
points = json.loads(POINTS.read_text(encoding='utf-8'))
rows = {p['id']: p for p in points}
patches = {1: [], 2: []}


def position(floor, x, y, height):
    return Vector((x, y, height + (3.2 if floor == 2 else 0)))


def layer(floor):
    for window in bpy.context.window_manager.windows:
        window.view_layer = scene.view_layers['Ground_Design' if floor == 1 else 'Upper_Design']
    bpy.context.view_layer.update()


def assembly(key):
    return [o for o in bpy.data.objects if o.name == key or o.name.startswith(key + '_')]


def update(key, x, y, height, purpose, **extra):
    row = rows[key]
    floor = row['level']
    parts = assembly(key)
    dest = position(floor, x, y, height)
    delta = dest - bpy.data.objects[key].location
    for part in parts:
        part.location += delta
    row.update(x_m=x, y_m=y, height_aff_m=height, purpose=purpose, **extra)
    root = bpy.data.objects[key]
    for prop, value in {'purpose': purpose, 'height_above_finished_floor_m': height,
                        'modules': row['modules'], 'circuit_group_proposed': row['proposed_group'],
                        'wall_face': row['face'], **extra}.items():
        root[prop] = value
    patches[floor].extend(parts)


def single(key, axis):
    root = bpy.data.objects[key]
    plate = root.data.copy()
    root.data = plate
    for vertex in plate.vertices:
        vertex.co[axis] *= .075 / root.dimensions[axis]
    rockers = [part for part in assembly(key) if '_rocker' in part.name]
    rockers[0].location[axis] = root.location[axis]
    for part in rockers[1:]:
        bpy.data.objects.remove(part, do_unlink=True)


def add_row(key, floor, room, kind, x, y, height, face, purpose, group, **extra):
    row = dict(id=key, room=room, level=floor, type=kind, x_m=x, y_m=y,
               height_aff_m=height, face=face, purpose=purpose, proposed_group=group,
               modules=1, status='PROPOSED_NOT_AS_BUILT', **extra)
    points.append(row)
    rows[key] = row


layer(1)
prototype = 'E1_020_SWITCH'
new = 'E1_094_SWITCH'
for source in assembly(prototype):
    part = source.copy()
    part.name = new + source.name[len(prototype):]
    for collection in source.users_collection:
        collection.objects.link(part)
    for prop in list(part.keys()):
        del part[prop]
    part['electrical_point'] = True
bpy.data.objects[new]['point_id'] = new
add_row(new, 1, 'Stairs', 'SWITCH', 5.496, 11.50, 1.05, 'E',
        'Lower two-way control for stair light', 'STAIR_LIGHT')
update(new, 5.496, 11.50, 1.05, rows[new]['purpose'], control_pair='E2_050_SWITCH')

layer(2)
update('E2_050_SWITCH', 6.71, 7.156, 1.05,
       'Upper stair two-way control and independent hall light', proposed_group='STAIR_LIGHT + UPPER_HALL_LIGHT',
       control_pair='E1_094_SWITCH', stair_switch_key='left', hall_switch_key='right')
single('E2_047_SWITCH', 1)
update('E2_047_SWITCH', 6.9046, 6.0, 1.05, 'Wardrobe general light', modules=1)
update('E2_048_SOCKET', 6.9046, 5.03, .35, 'Low wardrobe outlet for steamer or cleaning')
single('E2_083_SWITCH', 0)
child_switch = rows['E2_083_SWITCH']
update('E2_083_SWITCH', child_switch['x_m'], child_switch['y_m'], 1.05,
       'Child room ceiling light', modules=1)
update('E2_080_SOCKET', 8.3344, 1.10, .35, 'Child desk outlet below the worktop', socket_shutters=True)
update('E2_082_SOCKET', 5.49555, 2.82, .32, 'Low child bedside outlet', socket_shutters=True)


def material(name, rgb, **settings):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = mat.diffuse_color
    for key, value in settings.items():
        shader.inputs[key].default_value = value
    return mat


def box(name, floor, xyz, dimensions, mat, bevel=.003):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position(floor, *xyz))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new('Soft edges', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 3
    patches[floor].append(obj)
    return obj


metal = material('R34 Satin bronze', (.21, .15, .09), Metallic=.65, Roughness=.35)
diffuser = material('R34 Warm opal', (.94, .86, .69), **{'Emission Color': (1, .83, .62, 1), 'Emission Strength': .35})
for key, room, y, height, purpose, group in (
    ('L2_095', 'Child_Room', 2.54, 1.24, 'Bedside reading sconce with integral switch', 'CHILD_READING'),
    ('L2_096', 'Stairs', 8.12, 1.45, 'Stair wall light controlled from both levels', 'STAIR_LIGHT'),
):
    x_wall = 5.49005
    add_row(key, 2, room, 'LIGHT_POINT', x_wall+.013, y, height, 'E', purpose, group)
    body = box(key, 2, (x_wall+.013, y, height), (.026, .118, .15), metal, .007)
    shade = box(key+'_diffuser', 2, (x_wall+.044, y, height+.022), (.07, .092, .077), diffuser, .018)
    for part in (body, shade):
        part['viewer_fixed_light'] = True
        part['electrical_point'] = True
    if room == 'Child_Room':
        button = box(key+'_integral_switch', 2, (x_wall+.028, y, height-.044), (.008, .019, .015), metal, .002)
        button['electrical_point'] = True

layer(1)
oak = material('R34 Warm oak', (.39, .25, .14), Roughness=.48)
front = material('R34 Light warm cabinet', (.69, .65, .57), Roughness=.48)
prefix = 'LIB_Ground_WC_Overtoilet_Cabinet'
for suffix, xyz, size, mat in (
    ('Left', (5.678, 6.906, 1.80), (.016,.244,.61), oak),
    ('Right', (6.202, 6.906, 1.80), (.016,.244,.61), oak),
    ('Back', (5.94, 7.017, 1.80), (.508,.016,.61), oak),
    ('Top', (5.94, 6.906, 2.097), (.508,.244,.016), oak),
    ('Bottom', (5.94, 6.906, 1.503), (.508,.244,.016), oak),
    ('Shelf', (5.94, 6.906, 1.80), (.508,.244,.016), oak),
    ('FrontLeft', (5.813, 6.774, 1.80), (.249,.018,.599), front),
    ('FrontRight', (6.067, 6.774, 1.80), (.249,.018,.599), front),
    ('PullLeft', (5.899, 6.755, 1.62), (.010,.018,.070), metal),
    ('PullRight', (5.981, 6.755, 1.62), (.010,.018,.070), metal),
):
    box(prefix+'_'+suffix, 1, xyz, size, mat)

scene['interior_revision'] = 'LIBRARY 34.0 stair, child room, wardrobe and shower'
scene['electrical_revision'] = 34
for floor, objects in patches.items():
    layer(floor)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT/f'revision34_floor{floor}.glb'),
                             use_selection=True, export_format='GLB', export_extras=True,
                             export_cameras=False, export_lights=False)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL), compress=True)
POINTS.write_text(json.dumps(points, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
