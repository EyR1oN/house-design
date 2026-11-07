from pathlib import Path
import bpy,json,math,hashlib
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene;placements=json.loads((R/'data/placements.json').read_text());checks=[]
def check(name,value,detail=None):
 checks.append(dict(check=name,passed=bool(value),detail=detail));print(name,bool(value),flush=True)
check('All ready placements present',all(all(n in bpy.data.objects for n in a['objects']) for a in placements),len(placements))
actual={}
for level in [1,2]:
 for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design' if level==1 else 'Upper_Design']
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 for a in placements:
  if a['level']!=level:continue
  vs=[]
  for name in a['objects']:
   o=bpy.data.objects[name];e=o.evaluated_get(dg);vs.extend(e.matrix_world@Vector(v) for v in e.bound_box)
  b=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)];actual[a['label']]=b
  check('Bounded geometry '+a['label'],all(math.isfinite(t) for p in b for t in p) and all(abs(b[i][j]-a['bounds'][i][j])<.015 for i in range(3) for j in [0,1]),b)
check('Hob clearance to end wall',7.11-actual['Kitchen_Hob'][1][1]>=.32,7.11-actual['Kitchen_Hob'][1][1])
check('Dishwasher between sink and hob',actual['Kitchen_Window_Sink'][1][1]<actual['Kitchen_Dishwasher_45cm'][1][0] and actual['Kitchen_Dishwasher_45cm'][1][1]<actual['Kitchen_Hob'][1][0])
check('Closet central passage',abs(actual['Closet_West_5.665'][0][1]-6.04)<.002 and abs(actual['Closet_North'][0][1]-6.91)<.002)
check('Curtains at room edges',all(a[0][1]-a[0][0]<.36 and a[1][1]-a[1][0]<.15 for n,a in actual.items() if n.startswith('Curtain')))

check('Bedroom wardrobe fills niche',abs(actual['Bedroom_Wardrobe_9.205'][0][0]-8.48)<.002 and abs(actual['Bedroom_Wardrobe_10.655'][0][1]-11.38)<.002)
check('Bedroom wardrobe below ceiling',actual['Bedroom_Wardrobe_9.205'][2][1]<=5.885)
check('Entry wardrobe fills wall',abs(actual['Entry_Wardrobe_1.0825'][1][0]-.22)<.002 and abs(actual['Entry_Wardrobe_2.8075'][1][1]-3.67)<.002)
check('Desk chair clear of balcony doorway',actual['Bedroom_Vanity_Chair'][0][1]<7.89)
check('Island aisle at least 1200mm',9.75-actual['Kitchen_Crockery_6.185'][0][1]>=1.20)
check('Island clear of refrigerator swing',actual['Kitchen_Crockery_6.185'][1][0]-(4.59+.63)>.65)
check('Dining seats clear kitchen exit',actual['Dining_Chair_7.99'][1][0]-7.11>=.60)
check('All furniture beneath finished ceiling',all(b[2][1]<=(2.885 if next(a['level'] for a in placements if a['label']==n)==1 else 5.885)+.001 for n,b in actual.items()))
check('Single shower door',len([o for o in bpy.data.objects if o.name=='R3_Shower_Single_Door'])==1)
check('No visible stair rails',all(o.hide_render and o.hide_viewport for o in bpy.data.objects if o.get('removed_from_design')))
check('Child room furnished',all(n in actual for n in ['Child_Single_Bed','Child_Desk','Child_Desk_Chair','Child_Wardrobe']))
check('Makeup vanity with mirror', 'Bedroom_Makeup_Vanity' in actual and 'Bedroom_Vanity_Desk' not in actual)
check('All used texture files packed',all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.users>0))
check('Library furniture has no rig dependencies',all(not bpy.data.objects[n].constraints and not bpy.data.objects[n].animation_data and not bpy.data.objects[n].parent for a in placements for n in a['objects']))
current={o.name:([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')}
bpy.ops.wm.open_mainfile(filepath=str(R/'source/House_Intermediate.blend'))
check('Architectural geometry unchanged',all(o.name in current and current[o.name]==([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')))
backup=R.parent/'House_Intermediate_Backup_2026-09-30/House_Intermediate.blend'
check('Intermediate backup unchanged',hashlib.sha256(backup.read_bytes()).hexdigest()==hashlib.sha256((R/'source/House_Intermediate.blend').read_bytes()).hexdigest())
report={'passed':all(c['passed'] for c in checks),'checks':checks,'ready_model_types':len(set(a['role'] for a in placements)),'placements':len(placements)}
(R/'data/verification.json').write_text(json.dumps(report,indent=2),encoding='utf8')
assert report['passed'],'Inspect data/verification.json'
