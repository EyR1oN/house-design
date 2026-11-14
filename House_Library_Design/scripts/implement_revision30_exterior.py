"""Build the right-section exterior from sheets 2–11 of the architectural PDF."""
from math import ceil, hypot, pi, sin
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT = Path(__file__).resolve().parents[1]
WORK = PROJECT.parent / '.local-preview'
MASTER = PROJECT / 'House_Library_Design.blend'
bpy.ops.wm.open_mainfile(filepath=str(MASTER))
scene = bpy.context.scene
side = bpy.data.collections['R_BALCONIES_PORCH_TERRACE']
parent = next(c for c in bpy.data.collections if side.name in c.children)
names = ('R30_ENTRY_EXTERIOR', 'R30_BALCONIES', 'R30_ROOF')

# Keep the original building shell, column and the unrelated garden terrace.
for name in names:
    old = bpy.data.collections.get(name)
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
entry, balconies, roof = [bpy.data.collections.new(n) for n in names]
for col in (entry, balconies, roof):
    parent.children.link(col)
for obj in list(side.objects):
    if obj.name.startswith(('R_FRONT_ENTRY_STEP_', 'R_FRONT_BALCONY_', 'R_REAR_BALCONY_', 'R_UPPER_FRONT_BALCONY', 'R_UPPER_REAR_BALCONY')) or obj.name == 'R_ENTRY_PORCH':
        bpy.data.objects.remove(obj, do_unlink=True)


def material(name, rgb, roughness=.65, metallic=0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = mat.diffuse_color
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Metallic'].default_value = metallic
    return mat


plaster = material('Exterior • warm white stucco', (.72, .71, .66))
stone = material('Exterior • charcoal plinth', (.16, .155, .145))
paving = material('Exterior • flamed greige paving', (.36, .342, .306), .86)
joint = material('Exterior • paving joints', (.24, .229, .212))
iron = material('Exterior • graphite railing and flashing', (.073, .075, .077), .37, .42)
sheet = material('Exterior • gray profiled metal roofing', (.13, .136, .142), .44, .35)


def mesh(col, name, pts, faces, mat, nav=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(pts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    data.materials.append(mat)
    obj['viewer_fixed_finish'] = True
    if nav:
        obj['viewer_exterior_navigation'] = nav
    return obj


def solid(col, name, top, thickness, mat, nav=None):
    # The top contour is counter-clockwise in plan.
    n = len(top)
    return mesh(col, name, top + [(x, y, z-thickness) for x, y, z in top],
                [tuple(range(n)), tuple(reversed(range(n, 2*n)))] +
                [(j, j+n, (j+1)%n+n, (j+1)%n) for j in range(n)], mat, nav)


def box(col, name, x0, x1, y0, y1, z0, z1, mat, nav=None):
    return solid(col, name, [(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)], z1-z0, mat, nav)


def beam(col, name, a, b, width, depth, mat, nav=None):
    # Square/rectangular trim in a local frame: X across, Y along, Z upright.
    a, b = Vector(a), Vector(b)
    vec = b-a
    along = vec.normalized()
    across = along.cross(Vector((0, 0, 1))).normalized()
    up = across.cross(along)
    if up.z < 0:
        across, up = -across, -up
    temp = box(col, name, -width/2,width/2,0,vec.length,-depth/2,depth/2,mat,nav)
    for v in temp.data.vertices:
        x,y,z = v.co
        v.co = a+x*across+y*along+z*up
    return temp


def tile_grid(col, name, x0,x1,y0,y1, z, step_x=.35, step_y=.30):
    nx, ny = ceil((x1-x0)/step_x), ceil((y1-y0)/step_y)
    pts, faces = [], []
    for j in range(ny):
        for i in range(nx):
            a = x0+(x1-x0)*i/nx+.002
            b = x0+(x1-x0)*(i+1)/nx-.002
            c = y0+(y1-y0)*j/ny+.002
            d = y0+(y1-y0)*(j+1)/ny-.002
            k = len(pts)
            pts += [(a,c,z),(b,c,z),(b,d,z),(a,d,z)]
            faces.append((k,k+1,k+2,k+3))
    return mesh(col, name, pts, faces, paving, 'ignore')


# Plan 2: the landing sits inside the recess; the treads turn along the side
# of the landing and stop at the corner column. Model datum is -0.48 m.
box(entry,'R30_Entry_Threshold',8.33,8.73,.92,1.92,-.20,-.025,paving,'surface')
box(entry,'R30_Porch_Concrete',8.68,10.40,.44,2.22,-.48,-.03,joint,'surface')
tile_grid(entry,'R30_Porch_Pavers',8.72,10.40,.44,2.22,-.029)
for i, (x,y,z) in enumerate(((10.78,-.18,-.33),(10.59,.13,-.18))):
    box(entry,f'R30_Porch_Front_Tread_{i+1}',8.72,10.40,y,(.13,.44)[i],-.48,z,stone,'surface')
    box(entry,f'R30_Porch_Side_Tread_{i+1}',(10.59,10.40)[i],x,.20,2.22,-.48,z,stone,'surface')
box(entry,'R30_Entry_Column_Plinth',10.399,10.781,-.181,.201,-.48,.0,stone,'solid')
column_head = box(entry,'R30_Entry_Column_Head',10.40,10.78,-.18,.20,2.898,2.917,plaster,'ignore')
column_head['viewer_clip_with_walls'] = True
box(entry,'R30_Entry_Paved_Approach',8.72,11.87,-1.10,2.22,-.56,-.48,joint,'surface')
tile_grid(entry,'R30_Entry_Approach_Pavers',8.72,11.87,-1.10,-.18,-.479)
tile_grid(entry,'R30_Entry_Side_Path',10.78,11.87,-.18,2.22,-.479)

# Plan 3: 1 m lateral balcony and 3.2 x 1 m rear balcony. Bring each
# threshold to the finished deck without filling the adjacent wall opening.
for label, rect, threshold, runs in (
    ('Front', (10.83,11.83,-.18,2.17), (10.45,11.00,.44,1.24),
     [((10.86,-.151),(11.80,-.151)),((11.80,-.151),(11.80,2.14))]),
    ('Rear', (7.60,10.80,12.21,13.21), (7.89,8.69,11.83,12.28),
     [((7.63,12.21),(7.63,13.18)),((7.63,13.18),(10.77,13.18)),((10.77,13.18),(10.77,12.21))]),
):
    box(balconies,f'R30_{label}_Balcony_Slab',*rect,2.80,3.15,plaster,'surface')
    box(balconies,f'R30_{label}_Balcony_Finish',*rect,3.15,3.18,joint,'surface')
    tile_grid(balconies,f'R30_{label}_Balcony_Tile',*rect,3.181)
    box(balconies,f'R30_{label}_Balcony_Threshold',*threshold,3.145,3.186,paving,'surface')
    post_keys = set()
    for index,(a,b) in enumerate(runs):
        for z, width, height, nav in ((4.177,.054,.046,'railing'),(3.27,.033,.025,'ignore')):
            beam(balconies,f'R30_{label}_Rail_{index}_{z}',(*a,z),(*b,z),width,height,iron,nav)
        count = ceil(hypot(b[0]-a[0],b[1]-a[1])/.105)
        for i in range(count+1):
            t=i/count
            x,y=(round(a[k]+(b[k]-a[k])*t,5) for k in range(2))
            if (x,y) in post_keys: continue
            post_keys.add((x,y))
            w=.022 if i in (0,count) or i%8==0 else .011
            box(balconies,f'R30_{label}_Picket_{len(post_keys):02}',x-w,x+w,y-w,y+w,3.18 if w>.012 else 3.27,4.178,iron,'ignore')

# Correct the existing office door swing around its actual jamb on sheet 3.
def pivot_turn(x, y):
    pivot = Vector((x,y,0))
    return Matrix.Translation(pivot) @ Matrix.Rotation(pi*65/180,4,'Z') @ Matrix.Translation(-pivot)

delta = pivot_turn(10.64,.50) @ pivot_turn(11.58,.50).inverted()
if not scene.get('right_exterior_pdf_revision'):
    for obj in bpy.data.objects:
        if obj.name.startswith(('R_L2_FRONT_BALCONY_DOOR_GLASS_', 'R3_Glazed_Door_Leaf_L2_FRONT_BALCONY_DOOR_')):
            obj.matrix_world = delta @ obj.matrix_world

# Sheet 11: half of 15.060 x 14.440, 119 mm half-ridge, measured from
# the existing party axis (x=5.30), front/rear roof axes at y=0 and 12.26.
# Sections 1–1/2–2 control the vertical silhouette (see handoff).
x0,x1,y0,y1=5.30,12.83,-1.09,13.35
yc=(y0+y1)/2
ze,zr=6.277,8.862
ridge, cut=(x0+.119,yc,zr),(x0,yc,zr)
fl,fr,rr,rl=(x0,y0,ze),(x1,y0,ze),(x1,y1,ze),(x0,y1,ze)
facets = (([fl,fr,ridge,cut],0),([fr,rr,ridge],1),([ridge,rr,rl,cut],0))


def clipped(poly, axis, edge, sign):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da,db=sign*(a[axis]-edge),sign*(b[axis]-edge)
        if da>=0: out.append(a)
        if (da<0)!=(db<0):
            t=da/(da-db)
            out.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(3)))
    return out


for f,(poly,axis) in enumerate(facets):
    solid(roof,f'R30_Roof_Slope_{f+1}',poly,.050,sheet)
    # Shallow pressed ribs follow the fall, trimmed exactly at the hips.
    pts,faces=[],[]
    lo,hi=min(p[axis] for p in poly),max(p[axis] for p in poly)
    count=ceil((hi-lo)/.22)
    for i in range(count):
        mid=lo+(hi-lo)*(i+.5)/count
        borders=[mid-.024,mid-.016,mid,mid+.016,mid+.024]
        for j,(a,b) in enumerate(zip(borders,borders[1:])):
            strip=clipped(clipped(poly,axis,a,1),axis,b,-1)
            if len(strip)<3: continue
            k=len(pts)
            for x,y,z in strip:
                cross=(x,y)[axis]
                distance=abs(cross-mid)/.024
                run=y-y0 if f==0 else x1-x if f==1 else y1-y
                rise=.016*max(0,1-distance)*(.84+.16*sin(run*2*pi/.35))
                pts.append((x,y,z+.001+rise))
            faces.append(tuple(range(k,len(pts))))
    mesh(roof,f'R30_Roof_Profiles_{f+1}',pts,faces,sheet)

for i,(a,b) in enumerate(((fr,ridge),(ridge,rr),(cut,ridge))):
    beam(roof,f'R30_Roof_Hip_Cap_{i}',tuple((*a[:2],a[2]+.021)),tuple((*b[:2],b[2]+.021)),.14,.054,iron)
for i,(a,b) in enumerate(((fl,fr),(fr,rr),(rr,rl))):
    beam(roof,f'R30_Roof_Fascia_{i}',(*a[:2],ze-.135),(*b[:2],ze-.135),.065,.27,iron)
    off=((0,-.072),(.072,0),(0,.072))[i]
    beam(roof,f'R30_Roof_Gutter_{i}',(a[0]+off[0],a[1]+off[1],ze-.205),
         (b[0]+off[0],b[1]+off[1],ze-.205),.108,.083,iron)
for i,y in enumerate((y0-.072,y1+.072)):
    o=box(roof,f'R30_Cut_Gutter_Outlet_{i}',x0,x0+.14,y-.052,y+.052,5.975,6.07,iron)
# Soffit under each plane; no adjoining roof or neighboring section.
box(roof,'R30_Roof_Soffit',x0,x1,y0,y1,6.00,6.026,plaster)
solid(roof,'R30_Roof_Wall_Crown',[(x,y,6.0) for x,y in
      ((5.30,-.34),(10.99,-.34),(10.99,2.17),(11.94,2.17),(11.94,12.37),(5.30,12.37))],
      .101,plaster)
# Exterior face at the shared party cut, between the attic and roof slopes.
mesh(roof,'R30_Roof_Party_Section',[(*fl[:2],6.026),fl,cut,rl,(*rl[:2],6.026)],
     [(0,1,2,3,4)],plaster)
# Vent stacks placed from their footprints on the roof plan. Shared stack
# stops at the same section plane as the roofing.
for label, x,y,w,d,top in (('Side',9.76,7.40,1.18,.40,8.862),
                           ('Front',10.45,2.48,.54,.43,8.862),
                           ('Shared',5.395,7.15,.19,2.45,9.26)):
    box(roof,f'R30_Vent_{label}',max(x0,x-w/2),x+w/2,y-d/2,y+d/2,6.026,top-.075,plaster)
    box(roof,f'R30_Vent_{label}_Coping',max(x0,x-w/2-.045),x+w/2+.045,y-d/2-.045,y+d/2+.045,top-.075,top,iron)
# The PDF shows outlets near the front on the side eave and on the section
# axis at the front/rear. Fit the visible right-hand pipe to the side wall.
def pipe(col, name, a, b):
    start, end = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.044,depth=(end-start).length+.035,
                                       location=(start+end)/2)
    obj=bpy.context.object
    obj.rotation_euler=(end-start).to_track_quat('Z','Y').to_euler()
    for original in list(obj.users_collection): original.objects.unlink(obj)
    col.objects.link(obj)
    obj.name=name
    obj.data.materials.append(iron)
    obj['viewer_fixed_finish']=True
    obj['viewer_exterior_navigation']='ignore'

pipe(roof,'R30_Gutter_Offset',(11.995,2.52,5.84),(12.90,2.52,6.06))
pipe(roof,'R30_Upper_Downpipe',(11.995,2.52,3.12),(11.995,2.52,5.84))
pipe(roof,'R30_Lower_Downpipe',(10.995,2.52,-.42),(10.995,2.52,2.79))
pipe(roof,'R30_Downpipe_Jog',(10.995,2.52,2.79),(11.995,2.52,3.12))

scene['right_exterior_pdf_revision']=30
scene['interior_revision']='LIBRARY 30.0 right-section exterior and roof'

def layercol(layer,name):
    if layer.name==name: return layer
    for child in layer.children:
        if result:=layercol(child,name): return result
    return None

for layer in scene.view_layers:
    for old_name in ('ROOF','GUTTERS_AND_DOWNSPOUTS'):
        item=layercol(layer.layer_collection,old_name)
        if item: item.exclude=True
    for col in (entry,balconies,roof):
        layercol(layer.layer_collection,col.name).exclude = (
            layer.name != 'Exterior' and
            (col == roof or (col == entry and layer.name not in ('Ground_Design','Ground_Plan')) or
             (col == balconies and layer.name not in ('Upper_Design','Upper_Plan')))
        )

WORK.mkdir(exist_ok=True)
# Existing finished exterior wall faces are cut with the floor in the viewer.
facades = {i:[] for i in (1,2)}
for obj in bpy.data.collections['R_FACADE_LAYERS'].objects:
    if obj.name.endswith(('_RENDER','_INSULATION')):
        obj['viewer_fixed_finish'] = True
        obj['viewer_clip_with_walls'] = True
        obj['viewer_exterior_navigation'] = 'ignore'
        facades[int(obj.name[3])].append(obj)
bpy.context.window.view_layer=scene.view_layers['Upper_Design']
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER),compress=True)
bpy.context.window.view_layer=scene.view_layers['Exterior']
for tag, objects in (('entry', list(entry.objects)+facades[1]),
                     ('balconies', list(balconies.objects)+facades[2]),
                     ('roof', list(roof.objects)+list(bpy.data.collections['R_ATTIC'].objects))):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(WORK/f'exterior-{tag}.glb'),export_format='GLB',
                             use_selection=True,export_extras=True,export_lights=False,export_cameras=False)
