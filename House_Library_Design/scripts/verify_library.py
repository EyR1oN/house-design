from pathlib import Path
import bpy,json,math
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene;placements=json.loads((R/'data/placements.json').read_text(encoding='utf-8'));checks=[]
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
def object_bounds(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box]
 return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
island=object_bounds(bpy.data.objects['Crockery_oak_top'])
aisle=9.75-island[0][1]
check('Kitchen island top remains 1335 x 735 mm',abs(island[0][1]-island[0][0]-.735)<.002 and abs(island[1][1]-island[1][0]-1.335)<.002,island)
check('Kitchen working aisle at least 1050 mm',aisle>=1.05,aisle)
chair_gap=actual['Dining_Chair_7.99'][1][0]-island[1][1]
check('Dining chair clearance from island at least 120 mm',chair_gap>.12,chair_gap)
hinge=(8.02749,4.57220);fridge_sweep_clearance=10
for angle in range(111):
 a=math.radians(angle)
 for step in range(101):
  t=step/100;x=hinge[0]+.628*t*math.cos(a);y=hinge[1]+.628*t*math.sin(a)
  dx=max(island[0][0]-x,0,x-island[0][1]);dy=max(island[1][0]-y,0,y-island[1][1])
  fridge_sweep_clearance=min(fridge_sweep_clearance,math.hypot(dx,dy))
check('Fridge door sweep through 110 degrees clears island by 450 mm',fridge_sweep_clearance>.45,fridge_sweep_clearance)
check('Hob clearance to end wall',7.11-actual['Kitchen_Hob'][1][1]>=.32,7.11-actual['Kitchen_Hob'][1][1])
check('Dishwasher between sink and hob',actual['Kitchen_Window_Sink'][1][1]<actual['Kitchen_Dishwasher_45cm'][1][0] and actual['Kitchen_Dishwasher_45cm'][1][1]<actual['Kitchen_Hob'][1][0])
check('Closet central passage',abs(actual['Closet_West_5.665'][0][1]-6.04)<.002 and abs(actual['Closet_North'][0][1]-6.91)<.002)
check('Curtains at room edges',all(a[0][1]-a[0][0]<.36 and a[1][1]-a[1][0]<.15 for n,a in actual.items() if n.startswith('Curtain')))

check('Bedroom wardrobe fills niche',abs(actual['Bedroom_Wardrobe_9.205'][0][0]-8.48)<.002 and abs(actual['Bedroom_Wardrobe_10.655'][0][1]-11.38)<.002)
check('Bedroom wardrobe below ceiling',actual['Bedroom_Wardrobe_9.205'][2][1]<=5.885)
check('Entry wardrobe fills wall',abs(actual['Entry_Wardrobe_1.0825'][1][0]-.22)<.002 and abs(actual['Entry_Wardrobe_2.8075'][1][1]-3.67)<.002)
check('Desk chair clear of balcony doorway',actual['Bedroom_Vanity_Chair'][0][1]<7.89)
check('Furniture stays below finished ceilings',all(b[2][1]<=(2.885 if next(a['level'] for a in placements if a['label']==n)==1 else 5.885)+.001 for n,b in actual.items() if n!='TV_Continuous_Plain_Wall'))
check('Single shower door',len([o for o in bpy.data.objects if o.name=='R3_Shower_Single_Door'])==1)
check('No visible stair rails',all(o.hide_render and o.hide_viewport for o in bpy.data.objects if o.get('removed_from_design')))
check('Child room furnished',all(n in actual for n in ['Child_Single_Bed','Child_Desk','Child_Desk_Chair','Child_Wardrobe']))
check('Makeup vanity with mirror', 'Bedroom_Makeup_Vanity' in actual and 'Bedroom_Vanity_Desk' not in actual)
check('All used texture files packed',all(im.packed_file for im in bpy.data.images if im.source=='FILE' and im.users>0))
check('Library furniture has no rig dependencies',all(not bpy.data.objects[n].constraints and not bpy.data.objects[n].animation_data and not bpy.data.objects[n].parent for a in placements for n in a['objects']))
def architectural_signature():
 return {o.name:(tuple(tuple(v.co) for v in o.data.vertices),
                 tuple(tuple(p.vertices) for p in o.data.polygons),
                 tuple(tuple(row) for row in o.matrix_world))
         for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')}
current=architectural_signature()
bpy.ops.wm.open_mainfile(filepath=str(R/'source/House_Intermediate.blend'))
source=architectural_signature()
changed_architecture={name for name in source.keys()|current.keys() if source.get(name)!=current.get(name)}
revision18=json.loads((R/'data/revision18_report.json').read_text(encoding='utf-8'))
documented_stairs=set(revision18['stair_objects'])
check('All revision 18 stair parts remain present',documented_stairs<=current.keys(),sorted(documented_stairs-current.keys()))
def approved_movable_door(name):
 return (name.endswith('_DOOR_LEAF') or '_DOOR_GLASS_' in name) and name in source and name in current and source[name][:2]==current[name][:2]
allowed_architecture={name for name in changed_architecture
                      if name in documented_stairs or approved_movable_door(name)}
check('Only scheduled door panels and revision 18 stair parts differ from source',
      changed_architecture==allowed_architecture,sorted(changed_architecture-allowed_architecture))
prepared_roles={p.stem for p in (R/'assets/prepared').glob('*.blend')}
placement_roles={a['role'] for a in placements}
report={'passed':all(c['passed'] for c in checks),'checks':checks,'ready_model_types':len(placement_roles&prepared_roles),'project_specific_roles':len(placement_roles-prepared_roles),'placements':len(placements)}
(R/'data/verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
assert report['passed'],'Inspect data/verification.json'
