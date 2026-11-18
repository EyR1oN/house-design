"""Move the two office side outlets to the walls facing each other."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
MODEL = PROJECT/'House_Library_Design.blend'
POINTS = PROJECT/'data/electrical_points.json'
PATCH = PROJECT.parent/'.local-preview/revision42_floor2.glb'

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
if scene.get('electrical_revision') != 41:
    raise ValueError('Expected revision 41.')
for window in bpy.context.window_manager.windows:
    window.view_layer = scene.view_layers['Upper_Design']
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
schedule = json.loads(POINTS.read_text(encoding='utf-8'))
points = {row['id']: row for row in schedule}
x, height = 10.25, .88
z = height+3.2
selected = []

for name, start_y, ray_y, face, purpose in (
    ('E2_107_SOCKET',2.92,-1,'N','Desk 1 double outlet on the side wall within reach of the chair'),
    ('E2_108_SOCKET',5.02,1,'S','Desk 2 double outlet on the opposite side wall within reach of the chair'),
):
    contacts = []
    for sample_x in (x-.075, x, x+.075):
        for sample_z in (z-.0375, z, z+.0375):
            hit, pos, normal, _, obj, _ = scene.ray_cast(
                deps,Vector((sample_x,start_y,sample_z)),Vector((0,ray_y,0)),distance=.5)
            if not hit or obj.name != 'R_L2_SOURCE_WALL_6' or normal.y*ray_y > -.99:
                raise ValueError(f'No continuous mounting surface for {name}.')
            contacts.append(pos.y)
    if max(contacts)-min(contacts) > .001:
        raise ValueError(f'Mounting surface is not flat for {name}.')
    center = Vector((x,round(contacts[4]-ray_y*.0055,6),z))
    root = bpy.data.objects[name]
    old = root.location.copy()
    parts = [part for part in scene.objects
             if part.name == name or part.name.startswith(name+'_')]
    if len(parts)!=5 or any(part.parent for part in parts):
        raise ValueError(f'Unexpected double outlet assembly: {name}')
    turn = Matrix.Rotation(ray_y*math.pi/2,4,'Z')
    transform = Matrix.Translation(center) @ turn @ Matrix.Translation(-old)
    for part in parts:
        part.matrix_world = transform @ part.matrix_world
        part['wall_face'] = face
        part['height_above_finished_floor_m'] = height
        part['purpose'] = purpose
    points[name].update(x_m=x,y_m=center.y,height_aff_m=height,face=face,purpose=purpose)
    selected.extend(parts)

bpy.context.view_layer.update()
for part in selected:
    if '_hole' in part.name:
        root = bpy.data.objects[part.name.split('_hole')[0]]
        inward = 1 if root['wall_face']=='N' else -1
        if (part.location.y-root.location.y)*inward <= 0:
            raise ValueError(f'Outlet faces into its wall: {part.name}')

bpy.ops.object.select_all(action='DESELECT')
for part in selected:
    part.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(PATCH),use_selection=True,export_format='GLB',
    export_extras=True,export_cameras=False,export_lights=False)
bpy.ops.object.select_all(action='DESELECT')
scene['electrical_revision']=42
scene['interior_revision']='LIBRARY 42.0 opposing office side wall outlets'
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL),compress=True)
POINTS.write_text(json.dumps(schedule,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
