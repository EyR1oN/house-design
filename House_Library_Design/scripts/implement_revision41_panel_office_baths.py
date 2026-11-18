"""Place a main panel and reserve space, regroup office outlets, and remove bath sconces."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT = Path(__file__).resolve().parents[1]
MASTER = PROJECT/'House_Library_Design.blend'
SCHEDULE = PROJECT/'data/electrical_points.json'
PLACEMENTS = PROJECT/'data/placements.json'
OUTPUT = PROJECT.parent/'.local-preview'

bpy.ops.wm.open_mainfile(filepath=str(MASTER))
scene = bpy.context.scene
if scene.get('electrical_revision') != 40:
    raise ValueError('Expected revision 40.')
points = json.loads(SCHEDULE.read_text(encoding='utf-8'))
by_id = {p['id']:p for p in points}
placements = json.loads(PLACEMENTS.read_text(encoding='utf-8'))


def layer(floor):
    for window in bpy.context.window_manager.windows:
        window.view_layer = scene.view_layers['Ground_Design' if floor==1 else 'Upper_Design']
    bpy.context.view_layer.update()


def assembly(key):
    return sorted((o for o in scene.objects if o.name==key or o.name.startswith(key+'_')),
                  key=lambda o:o.name)


def remove(key,count):
    parts=assembly(key)
    if len(parts)!=count:
        raise ValueError(f'Unexpected {key} part count: {len(parts)}')
    for obj in parts:
        bpy.data.objects.remove(obj,do_unlink=True)


def stamp(obj,row):
    for k,v in dict(point_id=row['id'], room=row['room'], device_type=row['type'],
        purpose=row['purpose'],level=row['level'],wall_face=row['face'],
        modules=row['modules'],height_above_finished_floor_m=row['height_aff_m'],
        circuit_group_proposed=row['proposed_group'],electrical_point=True).items():
        obj[k]=v


def export(floor,parts):
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT/f'revision41_floor{floor}.glb'),
        use_selection=True,export_format='GLB',export_extras=True,
        export_cameras=False,export_lights=False)


def bounds(objects):
    vertices=[obj.matrix_world @ Vector(v) for obj in objects for v in obj.bound_box]
    return [[min(v[i] for v in vertices),max(v[i] for v in vertices)] for i in range(3)]


layer(1)
remove('L1_105',6)
points.remove(by_id['L1_105'])
by_id['E1_025_SWITCH'].update(purpose='Shower ceiling light and independent extractor control')
stamp(bpy.data.objects['E1_025_SWITCH'],by_id['E1_025_SWITCH'])
point=dict(id='E1_106_PANEL',room='Entry',level=1,type='PANEL',x_m=6.65,y_m=.245,
    height_aff_m=1.40,face='N',modules=1,purpose='Main distribution panel, proposed position',
    proposed_group='MAIN_PANEL',status='PROPOSED_NOT_AS_BUILT',
    installation_detail='Surface-mounted enclosure shown for space planning; reserve open floor below for a future power station or battery.')
points.append(point)
panel=[]
for suffix,location,dims,color in (
    ('',(6.65,.245,1.40),(.40,.09,.43),(.76,.75,.71)),
    ('_cover',(6.65,.296,1.40),(.374,.014,.402),(.86,.85,.81)),
    ('_latch',(6.802,.307,1.40),(.021,.012,.043),(.34,.35,.34)),
):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj=bpy.context.object
    obj.name=point['id']+suffix
    obj.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mat=bpy.data.materials.new(obj.name)
    mat.diffuse_color=(*color,1)
    obj.data.materials.append(mat)
    bevel=obj.modifiers.new('Rounded enclosure edges','BEVEL')
    bevel.width=.006 if suffix!='_latch' else .002
    bevel.segments=3
    stamp(obj,point)
    panel.append(obj)
placements[:]=[p for p in placements if p['label'] not in {
    'Ground_Shower_Mirror_Sconce','Upper_Bath_Sconce_9.06','Upper_Bath_Sconce_10.44'}]
placements.append(dict(label='Entry_Backup_Power_Reserve', role='space_reserve',group='Entry',
    level=1,bounds=[[6.37,6.93],[.20,.72],[0,.70]],objects=[],
    note='Clear standing area reserved for portable power station or battery. No device or connection selected.'))
bpy.context.view_layer.update()
placements.append(dict(label='Entry_Main_Distribution_Panel',role='electrical_enclosure',
    group='Entry',level=1,bounds=bounds(panel),objects=[obj.name for obj in panel]))
export(1,panel)

layer(2)
for name in ('LIB_Upper_Bath_Sconce_9.06','LIB_Upper_Bath_Sconce_10.44'):
    remove(name,6)
points.remove(by_id['L2_067'])
bath=assembly('E2_045_SWITCH')
if len(bath)!=4:
    raise ValueError('Expected the original three-key bathroom switch.')
plate,first,second,third=bath
plate.data=plate.data.copy()
for vertex in plate.data.vertices:
    vertex.co.y *= 2/3
first.location.y=plate.location.y-.0375
second.location.y=plate.location.y+.0375
bpy.data.objects.remove(third,do_unlink=True)
bath_row=by_id['E2_045_SWITCH']
bath_row.update(modules=2,purpose='Upper bathroom ceiling light and independent extractor control')
upper=[plate,first,second]
for obj in upper:
    stamp(obj,bath_row)

center=by_id['E2_038_SOCKET']
center_height=.75
delta_y=3.87-center['y_m']
delta_z=center_height-center['height_aff_m']
center.update(y_m=3.87,height_aff_m=center_height,purpose='Six central sockets shared by the two computer desks')
for obj in assembly(center['id']):
    obj.location.y+=delta_y
    obj.location.z+=delta_z
    stamp(obj,center)
    upper.append(obj)

remove('E2_039_SOCKET',13)
points.remove(by_id['E2_039_SOCKET'])
template=assembly('E2_080_SOCKET')
for key,y,side in (('E2_107_SOCKET',2.74,'outer end of desk 1'),
                   ('E2_108_SOCKET',5.18,'outer end of desk 2')):
    target=Vector((center['x_m'],y,3.2+center_height))
    deps=bpy.context.evaluated_depsgraph_get()
    for edge in (y-.075,y,y+.075):
        hit,loc,normal,_,wall,_=scene.ray_cast(
            deps,Vector((11.36,edge,3.2+center_height)),Vector((1,0,0)),distance=.085)
        if not hit or normal.x>-.99 or abs(loc.x-11.40)>.01:
            raise ValueError(f'No wall supporting {key} at {edge}: {wall}')
    row=dict(center,id=key,y_m=y,modules=2,purpose=f'Two sockets at the {side}')
    points.append(row)
    shift=target-template[0].location
    for source in template:
        obj=source.copy()
        obj.name=key+source.name[len('E2_080_SOCKET'):]
        for collection in source.users_collection:
            collection.objects.link(obj)
        obj.location+=shift
        if 'socket_shutters' in obj:
            del obj['socket_shutters']
        stamp(obj,row)
        upper.append(obj)
export(2,upper)

bpy.ops.object.select_all(action='DESELECT')
scene['electrical_revision']=41
scene['interior_revision']='LIBRARY 41.0 entry panel, office sockets and bath lights'
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER),compress=True)
for path,data in ((SCHEDULE,points),(PLACEMENTS,placements)):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
