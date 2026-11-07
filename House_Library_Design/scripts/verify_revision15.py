from pathlib import Path
import bpy,json,math
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
bpy.context.view_layer.update();r=json.loads((R/'data/revision15_report.json').read_text());checks=[]
def check(n,ok,detail=None):
 checks.append({'check':n,'passed':bool(ok),'detail':detail});print(n,bool(ok),detail,flush=True);assert ok,n
def bb(o,T=Matrix.Identity(4)):
 v=[T@o.matrix_world@Vector(c)for c in o.bound_box];return [[min(p[i]for p in v),max(p[i]for p in v)]for i in range(3)]
def sep(a,b):return any(a[i][1]<=b[i][0]+.0001 or b[i][1]<=a[i][0]+.0001 for i in range(3))
check('Old chimney and exposed hood removed',all(n not in bpy.data.objects for n in r['removed_objects']))
new=[bpy.data.objects[n]for n in r['new_objects']]
check('Cabinet clears window and partition',all(bb(o)[1][0]>6.1 and bb(o)[1][1]<7.11 for o in new))
check('Cabinet below ceiling',max(bb(o)[2][1]for o in new)<2.895)
check('Extraction underside height retained',abs(bb(bpy.data.objects['R15_Filter_Frame'])[2][0]-1.76)<.001)
duct=bb(bpy.data.objects['R15_Concealed_150mm_Duct'])
check('Six usable shelves clear duct',len(r['shelves'])==6 and all(sep(bb(bpy.data.objects[n]),duct)for n in r['shelves']))
socket=[bb(o) for o in bpy.data.objects if o.name.startswith('E1_012_SOCKET')]
check('Shelves avoid existing socket',all(sep(bb(bpy.data.objects[n]),b)for n in r['shelves']for b in socket))
old=json.loads((R.parent/'House_Library_Revision14_Backup/data/placements.json').read_text());p=json.loads((R/'data/placements.json').read_text());d={q['label']:q for q in p}
check('All other furniture and rooms unchanged',all(d[q['label']]==q for q in old if q['label']!='Kitchen_Hood'))
clear=True
for k in range(91):
 for i,y in [(0,6.192),(1,7.088)]:
  a=math.radians(k*85/90)*(1 if i==0 else -1);pivot=Vector((10.031,y,0));T=Matrix.Translation(pivot)@Matrix.Rotation(a,4,'Z')@Matrix.Translation(-pivot)
  for n in [f'R15_Hood_Door_{i}',f'R15_Hood_Door_Handle_{i}']:
   b=bb(bpy.data.objects[n],T)
   if not(b[0][0]>9.49 and b[1][0]>6.1 and b[1][1]<7.11):clear=False
check('Both cabinet door arcs clear neighbouring window and partition',clear,'91 positions, each leaf opening outward to 85 degrees (opening stop to keep projecting handles clear of partition)')
check('Master stored with closed cabinet',all(not bpy.data.objects[n].hide_render for n in r['doors']))
result={'revision':15,'passed':True,'checks':checks,'limitations':'Spatial mockup; appliance specification, mounting, duct routing and loads require selected product instructions.'}
for n in ['revision15_verification.json','verification.json']:(R/'data'/n).write_text(json.dumps(result,indent=2),encoding='utf8')

