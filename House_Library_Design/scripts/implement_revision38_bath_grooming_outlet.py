"""Add an accessible grooming outlet beside the upper bathroom mirror."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
MODEL = PROJECT/'House_Library_Design.blend'
SCHEDULE = PROJECT/'data/electrical_points.json'
PATCH = PROJECT.parent/'.local-preview/revision38_floor2.glb'
SOURCE = 'E2_046_SOCKET'
POINT = 'E2_098_SOCKET'

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
if scene.get('electrical_revision') != 37:
    raise ValueError('Expected revision 37.')
for window in bpy.context.window_manager.windows:
    window.view_layer = scene.view_layers['Upper_Design']
bpy.context.view_layer.update()

points = json.loads(SCHEDULE.read_text(encoding='utf-8'))
hidden = next(point for point in points if point['id'] == SOURCE)
x, y, height = 9.25, 5.50, 1.12
z = 3.2+height
deps = bpy.context.evaluated_depsgraph_get()
for test_x in (x-.0375, x, x+.0375):
    for test_z in (z-.0375, z, z+.0375):
        hit, contact, normal, _, surface, _ = scene.ray_cast(
            deps, Vector((test_x,5.70,test_z)), Vector((0,-1,0)), distance=.3)
        if not hit or surface.name != 'Upper_bath_south_stone' or abs(contact.y-y) > .002 or normal.y < .99:
            raise ValueError('The outlet plate has no clear mounting surface.')

purpose = 'Accessible outlet for a hair dryer and grooming, left of the upper bathroom mirror'
new_point = dict(hidden,id=POINT,x_m=x,y_m=y,height_aff_m=height,purpose=purpose,
    installation_detail='Visible outlet between the mirror and towel radiator. Confirm bathroom zones and protection before installation.')
source = bpy.data.objects[SOURCE]
delta = Vector((x,y,z))-source.location
originals = [obj for obj in scene.objects if obj.name == SOURCE or obj.name.startswith(SOURCE+'_')]
if len(originals) != 3 or any(obj.parent for obj in originals):
    raise ValueError('Unexpected outlet assembly.')
bpy.ops.object.select_all(action='DESELECT')
for original in originals:
    obj = original.copy()
    obj.name = POINT+original.name[len(SOURCE):]
    obj.location += delta
    for collection in original.users_collection:
        collection.objects.link(obj)
    if 'recessed_behind_mirror' in obj:
        del obj['recessed_behind_mirror']
    obj['point_id'] = POINT
    obj['purpose'] = purpose
    obj['height_above_finished_floor_m'] = height
    obj.select_set(True)
bpy.context.view_layer.update()
bpy.ops.export_scene.gltf(filepath=str(PATCH),use_selection=True,export_format='GLB',
    export_extras=True,export_cameras=False,export_lights=False)
bpy.ops.object.select_all(action='DESELECT')
scene['electrical_revision'] = 38
scene['interior_revision'] = 'LIBRARY 38.0 upper bathroom grooming outlet'
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL),compress=True)
points.append(new_point)
SCHEDULE.write_text(json.dumps(points,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
