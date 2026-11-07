from pathlib import Path
import bpy,json,math
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
bpy.context.view_layer.update();r=json.loads((R/'data/revision14_report.json').read_text(encoding='utf8'));p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));d={q['label']:q for q in p};checks=[]
def check(n,v,detail=None):checks.append({'check':n,'passed':bool(v),'detail':detail});print(n,v,detail,flush=True);assert v,n
def bb(o,M=None):
 v=[(M if M is not None else Matrix.Identity(4))@o.matrix_world@Vector(c) for c in o.bound_box];return [[min(c[i] for c in v),max(c[i] for c in v)] for i in range(3)]
def sep(a,b):return any(a[i][1]<=b[i][0]+.0001 or b[i][1]<=a[i][0]+.0001 for i in range(3))
def exact_box_separate(o,M,b):
 v=[M@o.matrix_world@Vector(c) for c in o.bound_box]
 if max(q.z for q in v)<=b[2][0]+.0001 or min(q.z for q in v)>=b[2][1]-.0001:return True
 points=sorted(set((round(q.x,8),round(q.y,8)) for q in v))
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 lower=[]
 for q in points:
  while len(lower)>=2 and cross(lower[-2],lower[-1],q)<=0:lower.pop()
  lower.append(q)
 upper=[]
 for q in reversed(points):
  while len(upper)>=2 and cross(upper[-2],upper[-1],q)<=0:upper.pop()
  upper.append(q)
 poly=lower[:-1]+upper[:-1];rect=[(x,y) for x in b[0] for y in b[1]];axes=[(1,0),(0,1)]+[(poly[(i+1)%len(poly)][1]-q[1],q[0]-poly[(i+1)%len(poly)][0]) for i,q in enumerate(poly)]
 for ax,ay in axes:
  A=[x*ax+y*ay for x,y in poly];B=[x*ax+y*ay for x,y in rect]
  if max(A)<=min(B)+.000001 or max(B)<=min(A)+.000001:return True
 return False
pivot=Vector(r['pivot_blender']);movers=[bpy.data.objects[n] for n in r['motion_groups']['pivot']];obstacles={l:q['bounds'] for l,q in d.items() if q['group']=='Kitchen' and l not in ['Kitchen_Tall_Corner_Pantry','Ground_Flush_Kitchen','Kitchen_Cutting_Boards']};obstacles['Stone worktop']=bb(bpy.data.objects['Kitchen_CONTINUOUS_L_WORKTOP'])
clear=True
for k in range(91):
 u=k/90;slide=.22*min(u/.3,1);angle=-math.pi/2*max(0,(u-.3)/.7);T=Matrix.Translation(Vector((0,slide,0)))@Matrix.Translation(pivot)@Matrix.Rotation(angle,4,'Z')@Matrix.Translation(-pivot)
 for o in movers:
  b=bb(o,T)
  for l,ob in obstacles.items():
   if not sep(b,ob) and not exact_box_separate(o,T,ob):print('COLLISION',k,o.name,l);clear=False
check('91 pivot-slide positions clear of oven return sink fridge island and worktop',clear)
check('Oak shelf door instead of cargo baskets',len([n for n in r['new_objects'] if 'Pivot_Oak_Shelf_' in n])==7 and not any(o.name.startswith('R13_Carrier_') for o in bpy.data.objects))
check('Seven rounded white corner shelves',len([n for n in r['new_objects'] if 'Rounded_White_Corner_Shelf_' in n])==7)
check('Wood door depth 180mm',abs(bpy.data.objects['R14_Pivot_Oak_Shelf_0'].dimensions.y-.18)<.001)
check('Window sill clear',max(bb(bpy.data.objects[n])[1][1] for n in r['motion_groups']['fixed'] if 'Counter_Return_Filler' not in n)<4.56)
check('Pantry stands on floor',abs(d['Kitchen_Tall_Corner_Pantry']['bounds'][2][0])<.001)
old=json.loads((R.parent/'House_Library_Revision13_Backup/data/placements.json').read_text(encoding='utf8'));check('Other furniture unchanged',all(d[q['label']]==q for q in old if q['label']!='Kitchen_Tall_Corner_Pantry'))
result={'revision':14,'passed':True,'checks':checks,'limitation':'Geometry and visual arrangement checked; actual pivot-slide hardware must be engineered for the cabinet'}
for n in ['revision14_verification.json','verification.json']:(R/'data'/n).write_text(json.dumps(result,indent=2),encoding='utf8')
print('REVISION14_VERIFIED')
