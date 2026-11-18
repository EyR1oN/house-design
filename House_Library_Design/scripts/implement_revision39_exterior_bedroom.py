"""Add exterior outlets and lighting and simplify the bedroom controls."""
import json
from math import pi
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
MASTER = PROJECT/'House_Library_Design.blend'
SCHEDULE = PROJECT/'data/electrical_points.json'
PLACEMENTS = PROJECT/'data/placements.json'
PATCH_DIR = PROJECT.parent/'.local-preview'

bpy.ops.wm.open_mainfile(filepath=str(MASTER))
scene = bpy.context.scene
if scene.get('electrical_revision') != 38:
    raise ValueError('Expected revision 38.')
points = json.loads(SCHEDULE.read_text(encoding='utf-8'))
by_id = {p['id']:p for p in points}
placements = json.loads(PLACEMENTS.read_text(encoding='utf-8'))


def layer(floor):
    for window in bpy.context.window_manager.windows:
        window.view_layer = scene.view_layers['Ground_Design' if floor == 1 else 'Upper_Design']
    bpy.context.view_layer.update()


def assembly(key):
    return sorted((obj for obj in scene.objects
        if obj.name == key or obj.name.startswith(key+'_')),key=lambda obj:obj.name)


def row(key, room, kind, center, face, purpose, group):
    point = dict(id=key,room=room,level=1,type=kind,x_m=center[0],y_m=center[1],
        height_aff_m=center[2],face=face,purpose=purpose,proposed_group=group,
        modules=1,status='PROPOSED_NOT_AS_BUILT')
    points.append(point)
    return point


def stamp(obj, point):
    props = dict(point_id=point['id'],room=point['room'],purpose=point['purpose'],
        device_type=point['type'],modules=point['modules'],level=point['level'],
        wall_face=point['face'],circuit_group_proposed=point['proposed_group'],
        height_above_finished_floor_m=point['height_aff_m'],electrical_point=True)
    for name,value in props.items():
        obj[name]=value


def clone(source, point, angle, collection=None, source_pose=None):
    original = assembly(source)
    target = Vector((point['x_m'],point['y_m'],point['height_aff_m']))
    rotation = Matrix.Rotation(angle,4,'Z')
    origin = original[0].location if source_pose is None else source_pose[source].translation
    transform = Matrix.Translation(target) @ rotation @ Matrix.Translation(-origin)
    result = []
    for obj in original:
        part = obj.copy()
        part.name = point['id']+obj.name[len(source):]
        if collection is None:
            for group in obj.users_collection:
                group.objects.link(part)
        else:
            collection.objects.link(part)
        part.matrix_world = transform @ (obj.matrix_world if source_pose is None else source_pose[obj.name])
        stamp(part,point)
        result.append(part)
    return result


def box_bounds(objects):
    bounds = [o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    return [[min(v[i] for v in bounds),max(v[i] for v in bounds)] for i in range(3)]


def export(floor, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(PATCH_DIR/f'revision39_floor{floor}.glb'),
        use_selection=True,export_format='GLB',export_extras=True,
        export_cameras=False,export_lights=False)


layer(2)
lamp = assembly('L2_096')
lamp_pose = {obj.name:obj.matrix_world.copy() for obj in lamp}
source_placement = next(p for p in placements if p['label']=='Stairs_Wall_Sconce')
layer(1)

curtain = next(p for p in placements if p['label']=='Curtain_Living_Dining_6.72')
curtain_parts = [bpy.data.objects[name] for name in curtain['objects']]
curtain_edge = 6.8449
# Open space beside the switches while keeping the curtain's door-side edge.
curtain_fit = Matrix.Translation((curtain_edge*.25,0,0)) @ Matrix.Diagonal((.75,1,1,1))
for obj in curtain_parts:
    obj.matrix_world = curtain_fit @ obj.matrix_world
bpy.context.view_layer.update()
curtain['bounds'] = box_bounds(curtain_parts)
curtain['scale'][0] *= .75

fixtures = [
    ('E1_099_SOCKET','E1_093_SOCKET','Exterior','SOCKET',(8.8835,1.99,.42),'E',-pi/2,
     'Front outdoor outlet beside the entrance','OUTDOOR_GENERAL'),
    ('E1_100_SOCKET','E1_093_SOCKET','Exterior','SOCKET',(10.49,12.3735,.10),'N',0,
     'Rear outdoor outlet near the right corner','OUTDOOR_GENERAL'),
    ('E1_101_SWITCH','E1_020_SWITCH','Entry','SWITCH',(8.3345,2.25,1.05),'W',pi,
     'Porch light switch beside the entry controls','PORCH_LIGHT'),
    ('E1_102_SWITCH','E1_094_SWITCH','Living','SWITCH',(6.55,11.82443,1.22),'S',0,
     'Terrace light switch above the stair switch','TERRACE_LIGHT'),
    ('L1_103','L2_096','Exterior','LIGHT_POINT',(8.878,1.99,1.95),'E',0,
     'Porch wall light','PORCH_LIGHT'),
    ('L1_104','L2_096','Exterior','LIGHT_POINT',(6.68,12.368,1.87),'N',pi/2,
     'Terrace wall light','TERRACE_LIGHT'),
]
ground = []
for key,source,room,kind,center,face,angle,purpose,group in fixtures:
    point = row(key,room,kind,center,face,purpose,group)
    if kind == 'LIGHT_POINT':
        collection = bpy.data.collections.new('LIB_'+group)
        scene.collection.children.link(collection)
        parts = clone(source,point,angle,collection,lamp_pose)
        bpy.context.view_layer.update()
        placements.append(dict(source_placement,label=group,group='Exterior',level=1,
            bounds=box_bounds(parts),objects=[o.name for o in parts]))
    else:
        parts = clone(source,point,angle)
        if kind == 'SOCKET':
            point['installation_detail'] = 'Exterior general-purpose outlet location, subject to fixture and site review.'
            for obj in parts:
                if 'installation_detail' in obj:
                    del obj['installation_detail']
    ground.extend(parts)

for key in ('E1_019_SWITCH','E1_091_SWITCH'):
    point = by_id[key]
    point['purpose'] = 'Living ceiling and both dining pendants, switched as separate lighting groups'
    stamp(bpy.data.objects[key],point)
export(1,ground+curtain_parts)

layer(2)
for obj in assembly('E2_091_SWITCH'):
    bpy.data.objects.remove(obj,do_unlink=True)
points.remove(by_id['E2_091_SWITCH'])

entry = 'E2_027_SWITCH'
parts = assembly(entry)
plate, first, second, third = parts
plate.data = plate.data.copy()
for vertex in plate.data.vertices:
    vertex.co.x *= 2/3
first.location.x = plate.location.x-.0375
second.location.x = plate.location.x+.0375
bpy.data.objects.remove(third,do_unlink=True)
point = by_id[entry]
point.update(modules=2,purpose='Bedroom ceiling light and LED strip dimmer; ceiling control shared with both bedsides',
             proposed_group='BEDROOM_CEILING + BEDROOM_LED',
             ceiling_controls=['E2_030_SWITCH','E2_031_SWITCH'])
upper = [plate,first,second]
for obj in upper:
    stamp(obj,point)

for key, side in (('E2_030_SWITCH','Left'),('E2_031_SWITCH','Right')):
    point = by_id[key]
    point.update(purpose=f'{side} reading pendant and shared bedroom ceiling control',
                 proposed_group=f'BEDROOM_CEILING + BEDROOM_READING_{side.upper()}',
                 ceiling_controls=[entry, 'E2_031_SWITCH' if side=='Left' else 'E2_030_SWITCH'])
    for obj in assembly(key):
        stamp(obj,point)
        upper.append(obj)
export(2,upper)

bpy.ops.object.select_all(action='DESELECT')
scene['electrical_revision'] = 39
scene['interior_revision'] = 'LIBRARY 39.0 exterior power and lighting, bedroom controls'
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER),compress=True)
for path,data in ((SCHEDULE,points),(PLACEMENTS,placements)):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
