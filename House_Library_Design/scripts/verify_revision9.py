from pathlib import Path
import bpy,json,math
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
bpy.context.view_layer.update();p=json.loads((R/'data/placements.json').read_text());d={r['label']:r for r in p};checks=[]
def check(n,v,detail=None):checks.append({'check':n,'passed':bool(v),'detail':detail});print(n,v,detail,flush=True);assert v,n
def bb(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
check('Bulky north-wall pantry removed','Laundry_Bulk_Pantry' not in d and not any(o.name.startswith('R8_Bulk_Pantry') for o in bpy.data.objects))
check('All laundry joinery on same east end-wall run',all(d[l]['bounds'][0][0]>9.63 and d[l]['bounds'][0][1]<10.40 for l in ['Laundry_Aligned_Tower','Laundry_Deep_Pantry']))
check('Laundry placements inside room including ceiling fixture',all(r['bounds'][0][0]>=8.46 and r['bounds'][0][1]<=10.4 and r['bounds'][1][0]>=2.60 and r['bounds'][1][1]<=3.80 and r['bounds'][2][1]<=2.90 for r in p if r['group']=='Laundry'))
check('Pantry and tower have side separation',d['Laundry_Deep_Pantry']['bounds'][1][0]-d['Laundry_Aligned_Tower']['bounds'][1][1]>.02)
front=min(d[l]['bounds'][0][0] for l in ['Laundry_Aligned_Tower','Laundry_Deep_Pantry','Laundry_Washer','Laundry_Dryer']);check('Clear centre depth >=1150mm',front-8.46>1.15,front-8.46)
check('Fully extended 560mm drawer leaves >=600mm user space',front-8.46-.56>.60,front-8.46-.56)
check('Entry door sweep clear of end-wall furniture',front-(8.411+.653)>.55)
bo=bb(bpy.data.objects['R7_Gas_Boiler_Body']);check('Boiler is on north wall facing south',abs(bo[1][1]-3.786)<.002 and abs(bo[0][1]-bo[0][0]-.44)<.002,bo)
check('Boiler service rectangle free of cabinets',bo[1][0]-2.60>.5 and bo[0][1]<front and bo[2][0]>1.45)
check('Pantry doors slide inside footprint',all(bb(o)[0][0]>9.65 for o in bpy.data.objects if o.name.startswith('R9_Pantry_Sliding_Front')))
wa=d['Laundry_Washer']['bounds'];dr=d['Laundry_Dryer']['bounds'];check('Dryer stays stacked with 30mm support kit',abs(dr[2][0]-wa[2][1]-.03)<.002)
check('Sack rests on potato bin',abs(bb(bpy.data.objects['R9_Potato_Sack'])[2][0]-bb(bpy.data.objects['R9_Potato_Base'])[2][1])<.001)
check('Four pantry levels with 36 modelled jars',len([o for o in bpy.data.objects if o.name.startswith('R9_Preserves_Jar')])==36)
check('Washer/dryer service sockets remain exposed',all(bb(bpy.data.objects[id])[0][1]<front for id in ['E1_022_SOCKET','E1_023_SOCKET']))
check('TV slats remain absent',not any(o.name.startswith('R7_TV_Oak_Slat_') for o in bpy.data.objects))
check('All placement objects exist',all(n in bpy.data.objects for r in p for n in r['objects']));check('All used file textures packed',all(i.packed_file for i in bpy.data.images if i.source=='FILE' and i.users>0))
old=json.loads((R.parent/'House_Library_Revision8_Backup/data/placements.json').read_text());check('Other rooms unchanged',all(d[r['label']]['bounds']==r['bounds'] for r in old if r['group']!='Laundry'))
arch={o.name:([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')};bpy.ops.wm.open_mainfile(filepath=str(R.parent/'House_Library_Revision8_Backup/House_Library_Design.blend'));check('Architecture unchanged',all(arch[o.name]==([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')))
report={'revision':9,'passed':True,'checks':checks,'scope':'Geometry, clear floor area, drawer extension and door swing; not gas installation approval'}
for name in ['revision9_verification.json','verification.json']:(R/'data'/name).write_text(json.dumps(report,indent=2),encoding='utf8')
print('REVISION9_VERIFIED',len(checks))
