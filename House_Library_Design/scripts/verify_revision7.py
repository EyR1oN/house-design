from pathlib import Path
import bpy,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
bpy.context.view_layer.update();p=json.loads((R/'data/placements.json').read_text());cur={r['label']:r for r in p};checks=[]
def check(n,v,detail=None):checks.append({'check':n,'passed':bool(v),'detail':detail});print(n,bool(v),detail,flush=True);assert v,n
def bounds(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
top=bounds(bpy.data.objects['Crockery_oak_top']);check('Island top enlarged east and south only',abs(top[0][0]-7.9625)<.001 and abs(top[0][1]-8.6975)<.001 and abs(top[1][0]-5.6925)<.001 and abs(top[1][1]-7.0275)<.001,top)
check('Kitchen working aisle at least 1050mm',9.75-top[0][1]>=1.05,9.75-top[0][1]);check('Dining chair gap remains at least 120mm',cur['Dining_Chair_7.99']['bounds'][1][0]-top[1][1]>.12)
# Conservative real-door swept rectangle at 0..110deg around the existing west hinge.
h=(8.02749,4.57220);closest=10
for angle in range(111):
 a=math.radians(angle)
 for i in range(101):
  t=i/100; x=h[0]+.628*t*math.cos(a);y=h[1]+.628*t*math.sin(a);dx=max(top[0][0]-x,0,x-top[0][1]);dy=max(top[1][0]-y,0,y-top[1][1]);closest=min(closest,math.hypot(dx,dy))
check('Fridge door sweep through 110deg clears island',closest>.45,closest)
# Preserve both stair openings and do not put decorative slats into the lower entrance.
wall=bpy.data.objects['R3_Stair_Wall_North'];tree=BVHTree.FromPolygons([wall.matrix_world@v.co for v in wall.data.vertices],[list(f.vertices) for f in wall.data.polygons]);check('Lower stair entrance still open',all(tree.ray_cast(Vector((6.75,y,z)),Vector((-1,0,0)),.5)[0] is None for y in [10.89,11.12,11.4,11.75] for z in [.4,1.2,2]))
check('TV cladding stops before lower stair entrance',cur['TV_Continuous_Wall_and_Oak_Slats']['bounds'][1][1]<10.82)
wa=cur['Laundry_Washer']['bounds'];dr=cur['Laundry_Dryer']['bounds'];check('Dryer stacked on washer via 30mm kit',abs(dr[2][0]-wa[2][1]-.03)<.002 and all(abs(sum(wa[i])/2-sum(dr[i])/2)<.001 for i in [0,1]))
check('Appliances face entrance west',bounds(bpy.data.objects['LIB_Laundry_Washer_Door_PREPARED'])[0][0]<9.73)
check('Laundry furniture stays within room',all(r['bounds'][0][0]>=8.46 and r['bounds'][0][1]<=10.40 and r['bounds'][1][0]>=2.60 and r['bounds'][1][1]<=3.80 and r['bounds'][2][1]<2.90 for r in p if r['group']=='Laundry'))
check('Open area in front of appliances >1200mm',wa[0][0]-8.46>1.2,wa[0][0]-8.46)
bo=bounds(bpy.data.objects['R7_Gas_Boiler_Body']);check('Boiler service clearances reserved',2.9-bo[2][1]>.275 and bo[2][0]-1.03>.25 and bo[0][0]-8.46>.5 and bo[1][0]-3.297>.005,bo)
check('Vegetable drawers separate from detergents upper storage',cur['Laundry_Ventilated_Pantry']['bounds'][1][0]>cur['Laundry_Washer']['bounds'][1][1])
check('All recorded placement objects present',all(n in bpy.data.objects for r in p for n in r['objects']));check('All used file textures packed',all(i.packed_file for i in bpy.data.images if i.source=='FILE' and i.users>0))
old=json.loads((R.parent/'House_Library_Revision6_Backup/data/placements.json').read_text());changed=json.loads((R/'data/revision7_report.json').read_text())['changed_placements'];removed=['Stair_Decorative_Panel','Laundry_Full_Upper_Storage'];check('Unrelated placements unchanged',all(cur[r['label']]['bounds']==r['bounds'] for r in old if r['label'] not in changed+removed))
architecture={o.name:([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')}
bpy.ops.wm.open_mainfile(filepath=str(R.parent/'House_Library_Revision6_Backup/House_Library_Design.blend'));check('Architecture unchanged',all(architecture[o.name]==([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')))
(R/'data/revision7_verification.json').write_text(json.dumps({'passed':True,'checks':checks,'gas_design_status':'Spatial concept only; no gas or flue installation approval'},indent=2));print('REVISION7_VERIFIED',len(checks))
