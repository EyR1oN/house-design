"""Revision 18: exportable ceilings, earlier stair turn and west-shifted dining group.
One-time migration; refuses to run twice. Keeps the revision 17 master backup.
"""
from pathlib import Path
import json, shutil
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'House_Library_Design.blend'
BACKUP = ROOT.parent / '.local-preview' / 'pre-revision18'
BACKUP.mkdir(exist_ok=True, parents=True)
for path in [MASTER, ROOT/'data/placements.json']:
 target = BACKUP/path.name
 if not target.exists(): shutil.copy2(path,target)
bpy.ops.wm.open_mainfile(filepath=str(MASTER))
s=bpy.context.scene
if bpy.data.objects.get('R18_Ceiling_L1'): raise RuntimeError('Revision 18 already applied')
def layer(name):
 bpy.context.window.view_layer=s.view_layers[name];bpy.context.view_layer.update()
def bounds(objects):
 pts=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
 return [[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)]
layer('Ground_Design')
placements=json.loads((ROOT/'data/placements.json').read_text())
moved=set()
for record in placements:
 if record['label'].startswith(('Dining','Pendant_Dining')):
  for name in record['objects']:
   o=bpy.data.objects.get(name)
   if o and name not in moved:
    o.matrix_world=Matrix.Translation((-.85,0,0))@o.matrix_world;moved.add(name)
  bpy.context.view_layer.update()
  record['bounds']=bounds([bpy.data.objects[n] for n in record['objects'] if n in bpy.data.objects])
for o in bpy.data.objects:
 if o.type=='LIGHT' and 'dining' in o.name.lower():o.location.x-=.85

# Keep all riser heights and the lower turn. Move the upper turn 420 mm
# towards the rear, clear of the closet wall ending at Y=7.4102.
stairs=[]
for o in list(bpy.data.collections['R_STAIRS'].objects):
 if o.type!='MESH':continue
 if o.get('removed_from_design') or o.name.startswith(('R_STAIR_BALUSTER','R_STAIR_HANDRAIL','R_STAIR_LANDING_RAIL','R_STAIR_GUARD','R_STAIR_UPPER_RAIL')):
  o.hide_render=True;o.hide_set(True);continue
 if o.name.startswith(('R_STAIR_STRAIGHT_','R_STAIR_RISER_','R_STAIR_UPPER_WINDER_','R_STAIR_STRINGER')):
  inv=o.matrix_world.inverted()
  for v in o.data.vertices:
   p=o.matrix_world@v.co
   if o.name.startswith('R_STAIR_UPPER_WINDER_'):p.y+=.42
   else:p.y=10.83-(10.83-p.y)*(2.38/2.8)
   v.co=inv@p
 stairs.append(o)
layer('Upper_Design')
threshold=bpy.data.objects['R3_Stair_Landing_Threshold']
threshold.matrix_world=Matrix.Translation((0,.42,0))@threshold.matrix_world

white=bpy.data.materials.new('R18 warm white ceiling');white.diffuse_color=(.82,.80,.75,1)
white.use_nodes=True
bs=white.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.82,.80,.75,1);bs.inputs['Roughness'].default_value=.9
def clip(poly,axis,limit,less):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ia=(a[axis]<=limit) if less else (a[axis]>=limit)
  ib=(b[axis]<=limit) if less else (b[axis]>=limit)
  if ia:out.append(a)
  if ia!=ib:
   t=(limit-a[axis])/(b[axis]-a[axis]);out.append(a+(b-a)*t)
 return out
ceilings={}
for floor in (1,2):
 layer('Ground_Design' if floor==1 else 'Upper_Design')
 sources=[o for o in bpy.data.collections[f'R_L{floor}_FLOOR'].objects if o.type=='MESH' and ('FINISHED_FLOOR' in o.name or 'FLOOR_FINISH' in o.name)]
 verts=[];faces=[];height=2.895 if floor==1 else 5.895
 def face(poly):
  if len(poly)<3:return
  start=len(verts);verts.extend((p.x,p.y,height) for p in poly);faces.append(tuple(range(start,start+len(poly))))
 for o in sources:
  for p in o.data.polygons:
   if (o.matrix_world.to_3x3()@p.normal).z<.9:continue
   poly=[o.matrix_world@o.data.vertices[i].co for i in p.vertices]
   if floor==1:
    face(clip(poly,1,7.43,True));face(clip(clip(poly,1,7.43,False),0,6.61,False))
   else:face(poly)
 if floor==2:face([Vector((5.49,7.43,0)),Vector((6.61,7.43,0)),Vector((6.61,11.83,0)),Vector((5.49,11.83,0))])
 mesh=bpy.data.meshes.new(f'R18_Ceiling_L{floor}');mesh.from_pydata(verts,[],faces);mesh.materials.append(white)
 o=bpy.data.objects.new(mesh.name,mesh);bpy.data.collections[f'R_L{floor}_FLOOR'].objects.link(o)
 o['viewer_walls']=True;o['viewer_ceiling']=True;o['level']=floor;ceilings[floor]=o

report={'revision':18,'dining_shift_m':[-.85,0,0],'moved_objects':sorted(moved),'upper_stair_turn_shift_m':.42,'straight_tread_depth_m':2.38/12,'stair_riser_height_m':3.2/18,'stair_closet_clearance_m':7.45-7.4102,'ceiling_heights_m':[2.895,5.895],'stair_objects':[o.name for o in stairs]}
(ROOT/'data/placements.json').write_text(json.dumps(placements,indent=2),encoding='utf8')
(ROOT/'data/revision18_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
s['interior_revision']='LIBRARY 18.0 ceilings, earlier stair turn and dining shift'
for floor in (1,2):
 layer('Ground_Design' if floor==1 else 'Upper_Design')
 bpy.ops.object.select_all(action='DESELECT')
 objects=stairs+[ceilings[floor]]+([bpy.data.objects[n] for n in moved] if floor==1 else [threshold])
 for o in objects:o.hide_set(False);o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(ROOT/f'exports/revision18_floor{floor}.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER),compress=True)
print('REVISION18_SAVED',json.dumps(report))
