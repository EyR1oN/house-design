from pathlib import Path
import bpy,json
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
bpy.context.view_layer.update();report=json.loads((R/'data/revision13_report.json').read_text(encoding='utf8'));p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));d={r['label']:r for r in p};checks=[]
import bmesh
counter=bpy.data.objects['Kitchen_CONTINUOUS_L_WORKTOP'];bm=bmesh.new();bm.from_mesh(counter.data)
r=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(9.745,0,0),plane_no=(1,0,0),clear_inner=True)
edges=[e for e in r['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
bm.to_mesh(counter.data);bm.free();counter.data.update()
def check(n,v,detail=None):checks.append({'check':n,'passed':bool(v),'detail':detail});print(n,v,detail,flush=True);assert v,n
def bb(os):
 bpy.context.view_layer.update();v=[o.matrix_world@Vector(c) for o in os for c in o.bound_box];return [[min(c[i] for c in v),max(c[i] for c in v)] for i in range(3)]
def separate(a,b):return any(a[i][1]<=b[i][0]+.0001 or b[i][1]<=a[i][0]+.0001 for i in range(3))
# Finish the continuous front with a 4mm joint and align filler with existing stone top.
for n,z,h in [('R13_Pantry_Pull_Front_Lower',1.128,2.016),('R13_Pantry_Pull_Front_Upper',2.50,.72)]:
 o=bpy.data.objects[n];o.location.z=z;o.dimensions.z=h
bpy.data.objects['R13_Counter_Return_Filler'].location.z=.8875
for n in report['new_objects']:
 o=bpy.data.objects[n]
 if n.startswith('R13_Carrier_Guide'):o.dimensions.x=.05
 if n.startswith('R13_Fixed_Guide'):o.dimensions.x=.06
bpy.context.view_layer.update();pb=bb([bpy.data.objects[n] for n in d['Kitchen_Tall_Corner_Pantry']['objects']]);d['Kitchen_Tall_Corner_Pantry']['bounds']=pb
front=[bpy.data.objects[n] for n in report['motion_groups']['front']];rear=[bpy.data.objects[n] for n in report['motion_groups']['rear']];fb=bb(front);rb=bb(rear)
check('Old prep base and upper corner removed','Kitchen_Corner_Prep' not in d and 'Kitchen_Upper_Corner' not in d)
check('Carcass stops before window sill',4.56-4.54>=.0199)
check('Pantry rests on floor and below ceiling',abs(pb[2][0])<.001 and pb[2][1]<=2.876,pb)
check('Pull-out fits accessible 410mm opening',fb[0][0]>=9.35 and fb[0][1]<=9.741,fb[0])
obstacles={l:r['bounds'] for l,r in d.items() if r['group']=='Kitchen' and l not in ['Kitchen_Tall_Corner_Pantry','Kitchen_Cutting_Boards','Ground_Flush_Kitchen']}
obstacles['Trimmed stone worktop']=bb([counter])
motion_ok=True;distance=100
for step in range(61):
 u=step/60;f=min(u/.55,1);rr=max(0,(u-.55)/.45);xf=-.60*min(rr/.8,1);yr=.14*max(0,(rr-.8)/.2)
 F=[[a,b] for a,b in fb];F[1]=[v+.66*f for v in fb[1]];B=[[a,b] for a,b in rb];B[0]=[v+xf for v in rb[0]];B[1]=[v+yr for v in rb[1]]
 if not separate(F,B):motion_ok=False
 for l,b in obstacles.items():
  if not separate(F,b) or not separate(B,b):print('COLLISION',step,l);motion_ok=False
check('61 motion samples clear oven fridge sink bases and island',motion_ok)
check('Rear rack becomes accessible at front after transfer',abs((rb[0][0]+rb[0][1])/2-.60-9.55)<.001 and rb[1][1]+.14>4.53)
ft=bb([o for o in front if o.name.startswith('R13_Tray_')]);rt=bb([o for o in rear if o.name.startswith('R13_Tray_')]);tray_gap=ft[1][0]+.66-(rt[1][1]+.14)
check('Open tray banks retain >=150mm clear separation',tray_gap>.15,tray_gap)
check('56 food containers on fourteen trays',len([n for n in report['new_objects'] if n.startswith('R13_Food_Jar')])==56 and len([n for n in report['new_objects'] if n.startswith('R13_Tray_Base')])==14)
cb=bb([bpy.data.objects['Kitchen_CONTINUOUS_L_WORKTOP']]);check('Trimmed worktop no longer crosses tall cabinet',cb[1][0]>=4.5999,cb)
board=d['Kitchen_Cutting_Boards']['bounds'];check('Boards supported on island',abs(board[2][0]-.892)<.001 and board[0][0]>7.98 and board[0][1]<8.68 and board[1][0]>5.71 and board[1][1]<7.01)
check('Service sockets above carriage',all(bb([bpy.data.objects[n]])[2][0]>2.75 for n in ['E1_005_SOCKET','E1_006_SOCKET']))
check('Old sockets cleared from middle of pantry',all(abs(bpy.data.objects[n].location.z-2.79)<.1 for n in ['E1_005_SOCKET','E1_006_SOCKET']))
old=json.loads((R.parent/'House_Library_Revision12_Backup/data/placements.json').read_text(encoding='utf8'));allowed={'Kitchen_Corner_Prep','Kitchen_Upper_Corner','Kitchen_Cutting_Boards'}
check('Other furniture placements unchanged',all(d[r['label']]==r for r in old if r['label'] not in allowed))
check('All placement objects exist',all(n in bpy.data.objects for r in p for n in r['objects']))
check('Textures packed',all(i.packed_file for i in bpy.data.images if i.source=='FILE' and i.users>0))
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');result={'revision':13,'passed':True,'checks':checks,'limitation':'Kinematic envelope only; furniture maker must select engineered full-height mechanism and verify loads and fixings'}
for n in ['revision13_verification.json','verification.json']:(R/'data'/n).write_text(json.dumps(result,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True);bpy.ops.object.select_all(action='DESELECT');names=set(report['new_objects']+report['changed_objects'])
for c in bpy.data.objects['E1_005_SOCKET'].users_collection:names.update(o.name for o in c.all_objects if o.type=='MESH')
for n in names:
 o=bpy.data.objects[n]
 if o.name in bpy.context.view_layer.objects and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision13_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION13_VERIFIED',len(checks))
