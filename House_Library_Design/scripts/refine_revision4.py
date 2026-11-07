from pathlib import Path
import bpy,json,math
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene
p=json.loads((R/'data/placements.json').read_text())
def layer(name):
 for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers[name]
 bpy.context.view_layer.update()
def rec(label):return next(a for a in p if a['label']==label)
def obs(label):return [bpy.data.objects[n] for n in rec(label)['objects'] if n in bpy.data.objects]
def bounds(objects):
 vs=[o.matrix_basis@Vector(v) for o in objects for v in o.bound_box]
 return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
def transform(label,H):
 for o in obs(label):o.matrix_basis=H@o.matrix_basis
def fit(label,center,size):
 b=bounds(obs(label));sc=[size[i]/(b[i][1]-b[i][0]) for i in range(3)]
 H=Matrix.Translation(Vector(center))@Matrix.Diagonal((*sc,1))@Matrix.Translation(Vector([-sum(x)/2 for x in b]));transform(label,H)
def move(label,delta):transform(label,Matrix.Translation(Vector(delta)))
def delete(label):
 global p
 for o in obs(label):bpy.data.objects.remove(o,do_unlink=True)
 p=[a for a in p if a['label']!=label]
def turn(label,angle):
 b=bounds(obs(label));c=Vector([sum(x)/2 for x in b]);transform(label,Matrix.Translation(c)@Matrix.Rotation(angle,4,'Z')@Matrix.Translation(-c))
def support(label,x,y,z):
 b=bounds(obs(label));move(label,(x-sum(b[0])/2,y-sum(b[1])/2,z-b[2][0]))
report={'revision':4,'checks':[]}
layer('Ground_Design')
# The lower flight is entered from its rear/east winder, not through storage.
wall=bpy.data.objects['R3_Stair_Wall_North']
bpy.ops.mesh.primitive_cube_add(size=1,location=(6.555,11.33,1.11));cut=bpy.context.object;cut.scale=(.32,1.012,2.222);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
mod=wall.modifiers.new('Lower stair entrance 1000mm','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.context.view_layer.objects.active=wall;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
tree=BVHTree.FromPolygons([wall.matrix_basis@v.co for v in wall.data.vertices],[list(f.vertices) for f in wall.data.polygons])
for y in [10.89,11.12,11.4,11.75]:
 for z in [.4,1.2,2.0]:assert tree.ray_cast(Vector((6.75,y,z)),Vector((-1,0,0)),.5)[0] is None
report['checks'].append('Lower stair doorway clear: 1000 mm wide, 2220 mm headroom')
layer('Upper_Design')
# Smaller 800mm basin/cabinet; mirror and accessories follow its usable top.
fit('Upper_Bath_Vanity',(9.75,5.765,3.82),(.8,.52,.56))
fit('Upper_Bath_Mirror',(9.75,5.517,4.745),(.8,.015,.85))
for label in ['Upper_Soap','Upper_Cup','Upper_Tray']:
 if any(a['label']==label for a in p):
  b=bounds(obs(label));move(label,((sum(b[0])/2-9.75)*(.8/1.1-1),0,0))
for o in bpy.data.objects:
 if o.name.startswith('Bath_toiletry'):o.location.x=9.94 if '001' not in o.name else 10.02
for label in ['Upper_Bath_Sconce_9.06','Upper_Bath_Sconce_10.44']:
 if any(a['label']==label for a in p):move(label,(.15 if '9.06' in label else -.15,0,0))
# Replace the small sculptural vanity mirror with a useful wall-mounted mirror.
v=rec('Bedroom_Makeup_Vanity')
for n in list(v['objects']):
 o=bpy.data.objects.get(n)
 if o and o.get('source_object_name')=='Plane.002_PREPARED':bpy.data.objects.remove(o,do_unlink=True);v['objects'].remove(n)
src=rec('Upper_Bath_Mirror');new=dict(src);new.update(label='Bedroom_Wall_Makeup_Mirror',group='Bedroom',objects=[])
c=bpy.data.collections.new('LIB_Bedroom_Wall_Makeup_Mirror');bpy.data.collections['DESIGN_Bedroom'].children.link(c)
for old in obs('Upper_Bath_Mirror'):
 o=old.copy();o.name='LIB_Bedroom_Wall_Makeup_Mirror_'+old.get('source_object_name','Mirror');c.objects.link(o);new['objects'].append(o.name)
p.append(new);turn(new['label'],math.pi/2);fit(new['label'],(6.641,11.23,4.785),(.018,.78,1.15))
# Child: left/window bed, right/window work zone, wardrobe on the door wall.
move('Child_Single_Bed',(0,-1.32,0));move('Child_Plush_Toy',(0,-1.32,0))
turn('Child_Wardrobe',math.pi/2);fit('Child_Wardrobe',(6.35,3.87,4.5375),(1.60,.58,2.675))
delete('Child_Toy_Basket')
move('Child_Bookcase',(0,2.35,0));move('Child_Art',(0,-1.32,0))
turn('Child_Desk',math.pi/2);fit('Child_Desk',(8.005,1.39,3.65),(.60,1.34,.90))
turn('Child_Desk_Chair',-math.pi/2);fit('Child_Desk_Chair',(7.19,1.39,3.6),(.52,.50,.80))
fit('Child_Play_Rug',(6.92,2.54,3.2065),(1.45,1.00,.009))
delete('Office_Weight_3.0');delete('Office_Weight_3.36');delete('Office_Weight_3.72')
for o in list(bpy.data.objects):
 if o.name.startswith(('Foam_roller','Fitness_mat','Yoga_mat')):bpy.data.objects.remove(o,do_unlink=True)
# Identify the raised rear shelf from mesh height, then orient it to the wall.
desk_report=[]
for label in ['Office_Desk_1','Office_Desk_2','Child_Desk']:
 objects=obs(label);b=bounds(objects);upper=[o.matrix_basis@v.co for o in objects for v in o.data.vertices if o.type=='MESH' and (o.matrix_basis@v.co).z>b[2][1]-.025]
 high_x=sum(v.x for v in upper)/len(upper);mid=sum(b[0])/2
 if high_x<mid:turn(label,math.pi)
 b=bounds(objects);upper=[o.matrix_basis@v.co for o in objects for v in o.data.vertices if (o.matrix_basis@v.co).z>b[2][1]-.025]
 assert sum(v.x for v in upper)/len(upper)>sum(b[0])/2,'Rear shelf must be toward east wall'
 desk_report.append({'desk':label,'shelf_on_wall_side':True})
# Rest monitors on rear shelves, keyboard on lower front working surface.
def top_at(label,x,y):
 dg=bpy.context.evaluated_depsgraph_get();highest=None
 for o in obs(label):
  eo=o.evaluated_get(dg);me=eo.to_mesh();tree=BVHTree.FromPolygons([o.matrix_basis@v.co for v in me.vertices],[list(f.vertices) for f in me.polygons]);hit=tree.ray_cast(Vector((x,y,6)),Vector((0,0,-1)),4)[0];eo.to_mesh_clear()
  if hit is not None:highest=max(highest or 0,hit.z)
 assert highest is not None,(label,x,y)
 return highest+.001
for k,y in enumerate([3.22,4.52],1):
 for j,yy in enumerate([y-.275,y+.275],1):support(f'Office_Monitor_{k}_{j}',11.23,yy,top_at(f'Office_Desk_{k}',11.23,yy))
 support(f'Office_Keyboard_{k}',10.92,y,top_at(f'Office_Desk_{k}',10.92,y))
 support(f'Office_Task_Lamp_{k}',11.19,y-.44,top_at(f'Office_Desk_{k}',11.19,y-.44))
support('Child_Desk_Books',8.10,.96,top_at('Child_Desk',8.10,.96))
support('Child_Pencil_Cup',7.94,1.85,top_at('Child_Desk',7.94,1.85))
report['desks']=desk_report
for a in p:a['bounds']=bounds(obs(a['label']))
(R/'data/placements.json').write_text(json.dumps(p,indent=2));(R/'data/revision4_report.json').write_text(json.dumps(report,indent=2))
s.cycles.device='CPU';s.render.engine='BLENDER_EEVEE_NEXT';bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
print('REVISION4_SAVED',len(p),flush=True)
