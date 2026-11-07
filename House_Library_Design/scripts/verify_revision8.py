from pathlib import Path
import bpy,json,math
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
bpy.context.view_layer.update();p=json.loads((R/'data/placements.json').read_text());cur={r['label']:r for r in p};checks=[]
def check(n,v,detail=None):checks.append({'check':n,'passed':bool(v),'detail':detail});print(n,v,detail,flush=True);assert v,n
def bb(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
check('No vertical TV slats remain',not any(o.name.startswith('R7_TV_Oak_Slat_') for o in bpy.data.objects));check('Continuous TV wall remains',bpy.data.objects.get('R7_TV_Continuous_Plaster') is not None)
b=cur['Laundry_Bulk_Pantry']['bounds'];check('Bulk cabinet fits room envelope',b[0][0]>=8.46 and b[0][1]<=10.4 and b[1][0]>=2.6 and b[1][1]<=3.8 and b[2][1]<=2.875,b)
bo=bb(bpy.data.objects['R7_Gas_Boiler_Body']);check('Boiler front service zone >=500mm',bo[0][0]-b[0][1]>.5,bo[0][0]-b[0][1]);check('Access strip beside new cabinetry >=700mm',b[1][0]-2.60>.70,b[1][0]-2.6)
# Inward 90-degree laundry door sweep remains south of cabinet fronts.
hinge=(8.411,2.603);max_y=hinge[1]+.653;check('Entry door swing clears pantry',max_y+.04<b[1][0],b[1][0]-max_y)
for id in ['E1_022_SOCKET','E1_023_SOCKET']:check('Socket accessible '+id,bb(bpy.data.objects[id])[0][0]>b[0][1])
check('Pantry reverse camera not inside cabinet',not (b[0][0]<s.objects['R3_CAMERA_LAUNDRY_REVERSE'].location.x<b[0][1] and b[1][0]<s.objects['R3_CAMERA_LAUNDRY_REVERSE'].location.y<b[1][1]))
check('Large sack rests on bin base',abs(bb(bpy.data.objects['R8_Potato_Sack'])[2][0]-bb(bpy.data.objects['R8_Potato_Bin_Base'])[2][1])<.001)
check('Five preserve shelf levels / forty jars',len([o for o in bpy.data.objects if o.name.startswith('R8_Preserve_Jar_')])==40)
old=json.loads((R.parent/'House_Library_Revision7_Backup/data/placements.json').read_text());check('Existing laundry appliances and all other furnishings unchanged',all(cur[r['label']]['bounds']==r['bounds'] for r in old if r['label']!='TV_Continuous_Wall_and_Oak_Slats'))
check('All placed objects present',all(n in bpy.data.objects for r in p for n in r['objects']));check('Used file textures packed',all(i.packed_file for i in bpy.data.images if i.source=='FILE' and i.users>0))
arch={o.name:([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')}
bpy.ops.wm.open_mainfile(filepath=str(R.parent/'House_Library_Revision7_Backup/House_Library_Design.blend'));check('Architectural geometry unchanged',all(arch[o.name]==([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')))
report={'revision':8,'passed':True,'checks':checks};(R/'data/revision8_verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');(R/'data/verification.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('REVISION8_VERIFIED',len(checks))
