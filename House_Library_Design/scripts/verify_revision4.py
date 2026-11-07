from pathlib import Path
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
p=json.loads((R/'data/placements.json').read_text());actual={a['label']:a['bounds'] for a in p};checks=[]
def check(name,value):checks.append({'check':name,'passed':bool(value)});assert value,name
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
bpy.context.view_layer.update();wall=bpy.data.objects['R3_Stair_Wall_North'];dg=bpy.context.evaluated_depsgraph_get();e=wall.evaluated_get(dg);me=e.to_mesh();tree=BVHTree.FromPolygons([wall.matrix_world@v.co for v in me.vertices],[list(f.vertices) for f in me.polygons])
check('Lower stair entrance unobstructed across its width and headroom',all(tree.ray_cast(Vector((6.75,y,z)),Vector((-1,0,0)),.5)[0] is None for y in [10.89,11.12,11.4,11.75] for z in [.4,1.2,2.0]));e.to_mesh_clear()
check('Child bed lies left of window, study zone right',actual['Child_Single_Bed'][0][1]<actual['Child_Desk'][0][0] and actual['Child_Single_Bed'][1][0]<.6)
check('Wardrobe sits on door wall without occupying doorway',actual['Child_Wardrobe'][1][1]<=4.18 and actual['Child_Wardrobe'][0][1]<=7.151)
check('Children furniture remains inside room',all(a['bounds'][0][0]>=5.49 and a['bounds'][0][1]<=8.34 and a['bounds'][1][0]>=.2 and a['bounds'][1][1]<=4.18 for a in p if a['group']=='Child_Room'))
check('Study chair can pull back without touching bed',actual['Child_Desk_Chair'][0][0]-actual['Child_Single_Bed'][0][1]>.35)
check('Broken basket and redundant bookcase removed','Child_Toy_Basket' not in actual and 'Child_Bookcase' not in actual)
check('Weights and floating roller removed',not any(n.startswith('Office_Weight_') and n!='Office_Weight_Cabinet' for n in actual) and not any(o.name.startswith('Foam_roller') for o in bpy.data.objects))
check('Bathroom vanity is 800mm wide',abs(actual['Upper_Bath_Vanity'][0][1]-actual['Upper_Bath_Vanity'][0][0]-.8)<.002)
b=actual['Bedroom_Wall_Makeup_Mirror'];check('Makeup wall mirror 780 by 1150mm',abs(b[1][1]-b[1][0]-.78)<.002 and abs(b[2][1]-b[2][0]-1.15)<.002)
check('Raised desk shelves all face their wall',all(a['shelf_on_wall_side'] for a in json.loads((R/'data/revision4_report.json').read_text())['desks']))
for k in [1,2]:
 for j in [1,2]:check(f'Office {k} monitor {j} rests at rear shelf height',abs(actual[f'Office_Monitor_{k}_{j}'][2][0]-actual[f'Office_Desk_{k}'][2][1]-.001)<.002)
check('Original broad verification passes',json.loads((R/'data/verification.json').read_text())['passed'])
(R/'data/revision4_verification.json').write_text(json.dumps({'passed':all(a['passed'] for a in checks),'checks':checks},indent=2));print('REVISION4_VERIFIED',len(checks),flush=True)
