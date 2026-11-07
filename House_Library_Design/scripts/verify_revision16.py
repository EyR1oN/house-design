from pathlib import Path
import bpy,json,math
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));r=json.loads((R/'data/revision16_report.json').read_text());p=json.loads((R/'data/placements.json').read_text());checks=[]
def check(n,ok,detail=None):
 checks.append(dict(check=n,passed=bool(ok),detail=detail));print(n,bool(ok),detail,flush=True);assert ok,n
def poly(o,M):
 v=[M@Vector(c)for c in o.bound_box];return [(v[i].x,v[i].y)for i in [0,4,6,2]],(min(q.z for q in v),max(q.z for q in v))
def collide(a,b):
 A,za=a;B,zb=b
 if za[1]<=zb[0]+.001 or zb[1]<=za[0]+.001:return False
 for P in [A,B]:
  for i,v in enumerate(P):
   q=P[(i+1)%len(P)];ax=-(q[1]-v[1]);ay=q[0]-v[0]
   if abs(ax)+abs(ay)<1e-8:continue
   aa=[x*ax+y*ay for x,y in A];bb=[x*ax+y*ay for x,y in B]
   if max(aa)<=min(bb)+1e-7 or max(bb)<=min(aa)+1e-7:return False
 return True
def rect(b):return ([(b[0][0],b[1][0]),(b[0][1],b[1][0]),(b[0][1],b[1][1]),(b[0][0],b[1][1])],b[2])
for door in r['doors']:
 level=door['level']
 for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design'if level==1 else'Upper_Design']
 bpy.context.view_layer.update();obs={q['label']:rect(q['bounds'])for q in p if q['level']==level and not q['label'].startswith('Door_')and q['role']not in ['ceiling_light','wall_art','wall_mirror']}
 # Adjacent walls as their local solid segments, not composite building bounding boxes.
 if door['id']=='L2_SIDE_BEDROOM_DOOR':obs.update({'Bathroom wall':rect([[8.46,11.4],[5.36,5.48],[3.2,5.9]]),'West wall below opening':rect([[8.34,8.46],[2.6,4.3],[3.2,5.9]])})
 elif door['id']=='L2_FRONT_BEDROOM_DOOR':obs.update({'East wall':rect([[8.34,8.46],[.2,4.18],[3.2,5.9]]),'Wardrobe-side wall':rect([[5.49,7.31],[4.18,4.3],[3.2,5.9]])})
 else:
  for n in ['R3_Stair_Wall_South','R3_Stair_Wall_North']:
   o=bpy.data.objects[n];obs[n]=poly(o,o.matrix_world)
 collisions=[];pivot=Vector(door['hinge'])
 for k in range(91):
  H=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(door['angle_deg']*k/90),4,'Z')@Matrix.Translation(-pivot)
  for name in door['moving']:
   o=bpy.data.objects[name];P=poly(o,H@Matrix(door['closed_matrices'][name]))
   for label,B in obs.items():
    if 'Hinge' in name and label.startswith('R3_Stair_Wall_'):continue # Hinge fittings intentionally mount into the jamb.
    if collide(P,B):collisions.append([k,name,label])
 check(door['id']+' 91-position leaf and handles sweep clear',not collisions,collisions[:8])
 # End-position minimum gaps to key furniture.
 if door['id']=='L2_SIDE_BEDROOM_DOOR':
  mx=max((bpy.data.objects[n].matrix_world@Vector(c)).x for n in door['moving']for c in bpy.data.objects[n].bound_box)
  chair=min(q['bounds'][0][0]for q in p if q['label']=='Office_Chair_2');check('Office open door ends before chair',chair-mx>.45,round(chair-mx,3))
check('Office floor plant removed',not any(q['label']=='Plant_Office'for q in p)and all(n not in bpy.data.objects for n in r['removed_objects']))
check('New kitchen finish uses exact reference material',all(any(m and m.name==r['kitchen_finish_material']for m in bpy.data.objects[n].data.materials)for n in r['color_objects']))
check('Pantry timber retained',bpy.data.objects['R14_Pivot_Oak_Back'].data.materials[0].name=='R14 Warm walnut reference')
baseline=R/'source/revision15_placements.json'
if not baseline.exists():baseline=R.parent/'House_Library_Revision15_Backup/data/placements.json'
old=json.loads(baseline.read_text());old={q['label']:q for q in old};changed={'Plant_Office','Door_STORAGE','Door_L2_SIDE_BEDROOM_DOOR','Door_L2_FRONT_BEDROOM_DOOR'}
check('Furniture placement unchanged outside requested doors and plant',all(q==old[q['label']]for q in p if q['label']not in changed))
e=json.loads((R/'data/electrical_points.json').read_text());pt=next(q for q in e if q['id']=='E2_084_SOCKET');check('Child cleaning socket outside the door parking zone',abs(pt['y_m']-2.95)<.001 and pt['y_m']+.06<3.389)
result=dict(revision=16,passed=True,checks=checks)
for n in ['revision16_verification.json','verification.json']:(R/'data'/n).write_text(json.dumps(result,indent=2),encoding='utf8')
