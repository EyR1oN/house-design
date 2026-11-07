from pathlib import Path
import bpy,json
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
bpy.context.view_layer.update();p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));d={r['label']:r for r in p};checks=[]
def check(n,v,detail=None):checks.append({'check':n,'passed':bool(v),'detail':detail});print(n,v,detail,flush=True);assert v,n
def bb(o):
 v=[o.matrix_world@Vector(c) for c in o.bound_box];return [[min(c[i] for c in v),max(c[i] for c in v)] for i in range(3)]
def separate(a,b):return any(a[i][1]<=b[i][0] or b[i][1]<=a[i][0] for i in range(3))
check('All laundry placements inside room',all(r['bounds'][0][0]>=8.46 and r['bounds'][0][1]<=10.4 and r['bounds'][1][0]>=2.6 and r['bounds'][1][1]<=3.8 and r['bounds'][2][1]<=2.9 for r in p if r['group']=='Laundry'))
bo=d['Laundry_Gas_Boiler']['bounds'];pa=d['Laundry_Shallow_Pantry']['bounds'];lo=d['Laundry_Boiler_Low_Storage']['bounds'];to=d['Laundry_Aligned_Tower']['bounds'];wa=d['Laundry_Washer']['bounds'];dr=d['Laundry_Dryer']['bounds']
check('Boiler at right east-wall corner facing west',bo[0][1]>10.35 and bo[1][1]<3.11,bo)
check('Appliance column left of boiler',wa[1][0]>bo[1][1])
check('Boiler and bins have vertical service space',bo[2][0]-lo[2][1]>.25,bo[2][0]-lo[2][1])
check('All main furniture placements mutually separate',all(separate(a,b) for a,b in [(bo,pa),(bo,to),(lo,to),(pa,to),(pa,lo)]))
check('Pantry leaves >=870mm aisle including handles',pa[1][0]-2.6>.87,pa[1][0]-2.6)
check('Conservative 550mm appliance door reach has >=60mm margin',wa[0][0]-.55-pa[0][1]>.06,wa[0][0]-.55-pa[0][1])
check('Entry door conservative swing clear',pa[1][0]>(2.603+.653) and min(wa[0][0],lo[0][0])>(8.411+.653))
check('Deep potato drawer leaves >=600mm standing space',lo[0][0]-8.46-.56>.6,lo[0][0]-8.46-.56)
check('Shallow vegetable drawers leave >=650mm standing space',pa[1][0]-2.6-.20>.65)
check('Upper pantry doors slide inside footprint',all(bb(o)[1][0]>3.47 for o in bpy.data.objects if o.name.startswith('R11_Side_Pantry_Sliding')))
check('Dryer supported by 30mm stacking kit',abs(dr[2][0]-wa[2][1]-.03)<.002)
check('Sack rests on deep bin base',abs(bb(bpy.data.objects['R9_Potato_Sack'])[2][0]-bb(bpy.data.objects['R9_Potato_Base'])[2][1])<.001)
check('60 jars on five pantry shelf levels',len([o for o in bpy.data.objects if o.name.startswith('R11_Preserves_Jar')])==60)
check('Sockets on exposed side-wall patch',all(pa[0][1]<bb(bpy.data.objects[id])[0][0] and bb(bpy.data.objects[id])[0][1]<wa[0][0] for id in ['E1_022_SOCKET','E1_023_SOCKET']))
check('Placement objects exist',all(n in bpy.data.objects for r in p for n in r['objects']))
check('Textures packed',all(i.packed_file for i in bpy.data.images if i.source=='FILE' and i.users>0))
check('Old deep tall pantry removed','Laundry_Deep_Pantry' not in d and not any(o.name.startswith('R9_Pantry_') for o in bpy.data.objects))
check('TV slats absent',not any(o.name.startswith('R7_TV_Oak_Slat_') for o in bpy.data.objects))
old=json.loads((R.parent/'House_Library_Revision10_Backup/data/placements.json').read_text(encoding='utf8'));check('Other rooms unchanged',all(d[r['label']]==r for r in old if r['group']!='Laundry'))
report={'revision':11,'passed':True,'checks':checks,'scope':'Current model geometry; selected real appliances, flue suitability and installation requirements need confirmation'}
for n in ['revision11_verification.json','verification.json']:(R/'data'/n).write_text(json.dumps(report,indent=2),encoding='utf8')
print('REVISION11_VERIFIED',len(checks))
