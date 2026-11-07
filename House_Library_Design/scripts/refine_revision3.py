"""Revision 3: fitted hinged doors, children's room, vanity and installation fixes.
Run after build_library_design.py. Revision 2 backup remains untouched.
"""
from pathlib import Path
import bpy,json,math,bmesh
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/House_Library_Revision2.blend'))
scene=bpy.context.scene
manifest={a['role']:a for a in json.loads((ROOT/'data/library_manifest.json').read_text())}
audit={a['role']:a for a in json.loads((ROOT/'data/library_audit.json').read_text())}
groups={n:bpy.data.collections['DESIGN_'+n] for n in ['Kitchen','Living_Dining','Entry','WC','Laundry','Lighting_Decor','Stair_Storage','Ground_Details','Bedroom','Office','Upper_Bath','Wardrobe','Upper_Hall','Upper_Lighting']}
child=bpy.data.collections.new('DESIGN_Child_Room');parent=next(c for c in bpy.data.collections if groups['Bedroom'].name in c.children);parent.children.link(child);groups['Child_Room']=child
cache={c.name.replace('READY_ASSET_',''):(c,list(c.objects)) for c in bpy.data.collections if c.name.startswith('READY_ASSET_')}
placed=json.loads((ROOT/'source/revision2_placements.json').read_text())
code=(ROOT/'scripts/build_library_design.py').read_text();exec(code[code.index('def erase'):code.index('P=math.pi;F=3.2')])
P=math.pi;F=3.2;report={'revision':3,'doors':[],'electrical_relocations':[],'supported_props':[]}
def layer(n):
 for w in bpy.context.window_manager.windows:w.view_layer=scene.view_layers[n]
 bpy.context.view_layer.update()
def remove_label(label):
 global placed
 for a in [a for a in placed if a['label']==label]:
  for n in a['objects']:
   o=bpy.data.objects.get(n)
   if o:bpy.data.objects.remove(o,do_unlink=True)
 placed=[a for a in placed if a['label']!=label]
def mat(name,col,metal=0,rough=.5,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emission:p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=emission
 return m
stone=bpy.data.materials['LIBRARY_PBR_Warm_Stone'];plaster=bpy.data.materials['LIBRARY_PBR_Warm_Plaster'];metal=mat('R3 brushed brass',(.32,.23,.11),.8,.3)
def box(name,group,center,size,m):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 groups[group].objects.link(o);o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=min(.008,min(size)/4);mod.segments=3;o['design_status']='PROPOSED_INTERIOR';return o
# Correct stair enclosure: contiguous lower wall, true storage opening and joined landing.
layer('Ground_Design');erase(['Stair_storage_partition','Stair_partition_completion','Storage_door_lintel','Storage_flush_door','Storage_recess_pull','TV_oak_slatted_panel'])
for name,a,b,z,h in [('South',7.03,7.98,0,2.9),('North',8.68,11.83,0,2.9),('Lintel',7.98,8.68,2.10,.80)]:box('R3_Stair_Wall_'+name,'Stair_Storage',(6.555,(a+b)/2,z+h/2),(.13,b-a,h),plaster)
upper=box('R3_Stair_Landing_Closure','Upper_Hall',(6.555,7.715,4.385),(.13,1.37,2.97),plaster)
for o in list(bpy.data.objects):
 if o.name.startswith(('R_STAIR_BALUSTER','R_STAIR_HANDRAIL','R_STAIR_LANDING_RAIL','R_STAIR_GUARD','R_STAIR_UPPER_RAIL')):o.hide_render=True;o.hide_set(True);o['removed_from_design']='Enclosed by continuous wall'
asset('decorative_wall','Stair_Decorative_Panel','Living_Dining',(6.6475,9.80),(.055,1.92,2.78),.035,rot=(0,0,P/2))
for a in placed:
 if a['label']=='Living_TV':
  for n in a['objects']:bpy.data.objects[n].location.x+=.04
# Hinged ready doors. Keep architectural opening geometry; replace visible fittings.
erase(['Ground_WC_sliding_panel','Ground_WC_sliding_handle'])
openings=[a for a in json.loads((ROOT/'data/openings_schedule.json').read_text()) if a['section']=='R' and a['kind']=='DOOR']
openings.append(dict(id='STORAGE',axis='Y',a=7.98,b=8.68,c0=6.49,c1=6.62,absolute_bottom_m=0,absolute_top_m=2.1))
angles={'L1_ENTRY_DOOR':90,'L1_KITCHEN_DOOR':90,'L1_WC_DOOR':-90,'L1_LAUNDRY_DOOR':-90,'L2_REAR_BEDROOM_DOOR':90,'L2_BATHROOM_DOOR':-90,'L2_WARDROBE_DOOR':-90,'L2_FRONT_BEDROOM_DOOR':-90,'L2_SIDE_BEDROOM_DOOR':-90,'STORAGE':90}
for a in openings:
 level=1 if a['absolute_bottom_m']<1 else 2;layer('Ground_Design' if level==1 else 'Upper_Design');g='Entry' if level==1 else 'Upper_Hall'
 for o in bpy.data.objects:
  if o.name.startswith('R_'+a['id']+'_') and not o.name.endswith('_HEAD'):o.hide_render=True;o.hide_set(True);o['replaced_by_library_door']=True
 axis=a['axis'];mid=(a['a']+a['b'])/2;plane=(a['c0']+a['c1'])/2;center=(mid,plane) if axis=='X' else (plane,mid);width=a['b']-a['a'];height=a['absolute_top_m']-a['absolute_bottom_m'];rz=0 if axis=='X' else P/2
 obs=asset('hinged_door','Door_'+a['id'],g,center,(width,.165,height-.006) if axis=='X' else (.165,width,height-.006),a['absolute_bottom_m']+.006,rot=(0,0,rz))
 leaf=next(o for o in obs if o.get('source_object_name','').startswith('Door.001'))
 bb=bbox([leaf]);pivot=Vector((bb[0][0],(bb[1][0]+bb[1][1])/2,a['absolute_bottom_m'])) if axis=='X' else Vector(((bb[0][0]+bb[0][1])/2,bb[1][0],a['absolute_bottom_m']))
 theta=math.radians(angles[a['id']]);H=Matrix.Translation(pivot)@Matrix.Rotation(theta,4,'Z')@Matrix.Translation(-pivot)
 for o in obs:
  if not any(t in o.get('source_object_name','') for t in ['Door Frame','Cube_PREPARED']):o.matrix_basis=H@o.matrix_basis;o['hinged_leaf']=True
 report['doors'].append({'id':a['id'],'hinge':list(pivot),'angle_deg':angles[a['id']],'frame_fixed':True})
# Glazed exterior doors rotate about their actual jamb, not by translation.
for tag,axis,hinge,angle in [('L1_TERRACE_DOOR','X',(6.953,12.02,0),-65),('L2_REAR_BALCONY_DOOR','X',(7.953,12.02,F),-65),('L2_FRONT_BALCONY_DOOR','Y',(11.58,.50,F),65)]:
 H=Matrix.Translation(Vector(hinge))@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Translation(-Vector(hinge))
 for o in bpy.data.objects:
  if o.name.startswith('R_'+tag+'_GLASS'):o.matrix_basis=H@o.matrix_basis;o['hinged_glazed_leaf']=True
# Replace ordinary console with genuine makeup vanity including mirror.
layer('Upper_Design');remove_label('Bedroom_Vanity_Desk');remove_label('Bedroom_Plant');remove_label('Bedroom_Books')
asset('makeup_vanity','Bedroom_Makeup_Vanity','Bedroom',(6.875,11.245),(.48,1.10,1.38),F,rot=(0,0,P/2))
asset('cosmetic_jar','Bedroom_Makeup_Cream','Bedroom',(6.94,11.53),(.065,.065,.06),F+.764)
asset('bath_accessories','Bedroom_Makeup_Tray','Bedroom',(6.94,11.44),(.12,.08,.012),F+.764,only=('Tray',))
# Children's room: bed at west, daylight desk at south, east storage and central play area.
asset('child_bed','Child_Single_Bed','Child_Room',(6.03,2.88),(1.02,2.06,.80),F)
asset('desk_wooden','Child_Desk','Child_Room',(7.32,.56),(1.34,.60,.90),F,rot=(0,0,-P/2))
asset('dining_chair','Child_Desk_Chair','Child_Room',(7.32,1.25),(.50,.52,.80),F,rot=(0,0,P))
asset('wardrobe','Child_Wardrobe','Child_Room',(8.015,2.07),(.58,1.22,2.675),F,rot=(0,0,-P/2))
asset('bookcase','Child_Bookcase','Child_Room',(5.675,.89),(.35,1.0,1.45),F,rot=(0,0,P/2))
asset('rug','Child_Play_Rug','Child_Room',(6.99,2.47),(1.40,1.45,.009),F+.002)
asset('child_toy','Child_Plush_Toy','Child_Room',(6.16,2.84),(.20,.28,.25),F+.45)
asset('books','Child_Desk_Books','Child_Room',(7.76,.52),(.25,.18,.20),F+.733)
asset('bath_accessories','Child_Pencil_Cup','Child_Room',(6.85,.52),(.065,.065,.10),F+.733,only=('Tumbler',))
asset('storage_basket','Child_Toy_Basket','Child_Room',(6.18,1.43),(.30,.30,.28),F+.01)
asset('wall_art','Child_Art','Child_Room',(5.511,2.87),(.025,.90,.62),F+1.24,rot=(P/2,0,P/2))
# Bathroom: retain real shower fittings only, add tiled recess and one hinged glass door.
layer('Ground_Design');rec=next(a for a in placed if a['label']=='Ground_Shower');source_fixture=next(bpy.data.objects[n] for n in rec['objects'] if bpy.data.objects[n].get('source_object_name')=='Cube_PREPARED');source_fixture.data=source_fixture.data.copy();bm=bmesh.new();bm.from_mesh(source_fixture.data);mats=source_fixture.data.materials
bmesh.ops.delete(bm,geom=[f for f in bm.faces if 'nerez' not in mats[f.material_index].name],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(source_fixture.data);bm.free();source_fixture.data.update()
for n in rec['objects']:
 if n!=source_fixture.name:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
rec['objects']=[source_fixture.name];rec['label']='Ground_Shower_Fittings'
# Integrated tiled floor and walls; no exposed plastic shower tray.
box('R3_Shower_Tiled_Floor','WC',(5.94,4.37,.022),(.87,.87,.02),stone)
box('R3_Shower_Tiled_West','WC',(5.505,4.37,1.05),(.012,.87,2.10),stone)
box('R3_Shower_Tiled_South','WC',(5.94,3.936,1.05),(.87,.012,2.10),stone)
box('R3_Shower_Linear_Drain','WC',(5.94,4.00,.033),(.54,.035,.003),metal)
glass=mat('R3 clear shower glass',(.90,.94,.94),rough=.08);p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.45
box('R3_Shower_Fixed_Side_Glass','WC',(6.368,4.365,1.032),(.008,.845,1.99),glass)
door=box('R3_Shower_Single_Door','WC',(5.944,4.811,1.032),(.83,.008,1.99),glass);door['hinge_location']=(6.354,4.811,.037);door['door_leaf_count']=1;door['hinged']=True
for z in [.40,1.63]:box('R3_Shower_Hinge','WC',(6.353,4.818,z),(.045,.018,.055),metal)
box('R3_Shower_Door_Handle','WC',(5.61,4.830,1.07),(.12,.018,.018),metal)
# Rotate desk monitor shelves toward the wall, leaving the working surface by the chair.
for k,y in enumerate([3.22,4.52],1):
 c=Vector((11.055,y,F));H=Matrix.Translation(c)@Matrix.Rotation(P,4,'Z')@Matrix.Translation(-c)
 for a in placed:
  if a['label']=='Office_Desk_'+str(k):
   for n in a['objects']:bpy.data.objects[n].matrix_basis=H@bpy.data.objects[n].matrix_basis
for a in placed:
 if a['label']=='Bedroom_Vanity_Chair':
  for n in a['objects']:bpy.data.objects[n].location.y-=.23
# Correct opaque architectural glass material; no additional project lights.
window_glass=bpy.data.materials['glass'];window_glass.use_nodes=True;p=window_glass.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.92,.95,.97,1);p.inputs['Transmission Weight'].default_value=1;p.inputs['IOR'].default_value=1.45;p.inputs['Roughness'].default_value=.04
# Place small items onto evaluated surfaces, using downward rays instead of guessed heights.
def support(label,support_label,candidates):
 rec=next(a for a in placed if a['label']==label);target=next(a for a in placed if a['label']==support_label);layer('Ground_Design' if rec['level']==1 else 'Upper_Design');bpy.context.view_layer.update();verts=[];faces=[];dg=bpy.context.evaluated_depsgraph_get()
 for n in target['objects']:
  o=bpy.data.objects[n];e=o.evaluated_get(dg);me=e.to_mesh();base=len(verts);verts.extend(e.matrix_world@v.co for v in me.vertices);faces.extend([base+i for i in p.vertices] for p in me.polygons);e.to_mesh_clear()
 tree=BVHTree.FromPolygons(verts,faces)
 chosen=None
 for x,y in candidates:
  hit,normal,idx,dist=tree.ray_cast(Vector((x,y,10)),Vector((0,0,-1)),12)
  if hit and normal.z>.25 and hit.z>(.60 if rec['level']==1 else F+(.25 if label=='Child_Plush_Toy' else .50)):chosen=(x,y,hit.z+.001);break
 if not chosen:raise RuntimeError('No supporting ledge for '+label)
 bb=bbox([bpy.data.objects[n] for n in rec['objects']]);delta=Vector((chosen[0]-(bb[0][0]+bb[0][1])/2,chosen[1]-(bb[1][0]+bb[1][1])/2,chosen[2]-bb[2][0]))
 for n in rec['objects']:bpy.data.objects[n].location+=delta
 report['supported_props'].append({'label':label,'support':support_label,'position':chosen})
support('Ground_Vanity_Soap','Ground_Compact_Vanity',[(5.55,5.89),(5.55,5.85),(5.765,5.88)])
support('Upper_Vanity_Soap','Upper_Bath_Vanity',[(10.17,5.55),(10.21,5.57),(10.20,5.60)])
support('Upper_Vanity_Cup','Upper_Bath_Vanity',[(10.06,5.55),(10.10,5.55)])
support('Upper_Vanity_Tray','Upper_Bath_Vanity',[(9.38,5.55),(9.35,5.55)])
support('Bedroom_Makeup_Cream','Bedroom_Makeup_Vanity',[(6.94,11.53),(6.94,11.60)])
support('Bedroom_Makeup_Tray','Bedroom_Makeup_Vanity',[(6.94,11.42),(6.90,11.44)])
support('Child_Desk_Books','Child_Desk',[(7.76,.52),(7.65,.60)])
support('Child_Pencil_Cup','Child_Desk',[(6.85,.52),(6.90,.60)])
support('Child_Plush_Toy','Child_Single_Bed',[(6.16,2.84),(6.10,2.80)])
for k,y in enumerate([3.22,4.52],1):
 support('Office_Keyboard_'+str(k),'Office_Desk_'+str(k),[(10.89,y)])
 support('Office_Task_Lamp_'+str(k),'Office_Desk_'+str(k),[(11.06,y-.44)])
 for j,yy in enumerate([y-.275,y+.275],1):support('Office_Monitor_'+str(k)+'_'+str(j),'Office_Desk_'+str(k),[(11.13,yy)])
# Two physical LED profiles in bedroom and living; dimming is a proposed circuit property.
led=mat('R3 LED warm dimmable diffuser',(1,.78,.52),rough=.3,emission=2)
for name,g,c,size in [('Living_East','Living_Dining',(10.28,9.85,2.856),(.018,3.10,.018)),('Living_Rear','Living_Dining',(9.02,11.73,2.856),(2.50,.018,.018)),('Bedroom_East','Bedroom',(11.29,10.17,F+2.656),(.018,2.95,.018)),('Bedroom_Rear','Bedroom',(8.95,11.74,F+2.656),(4.36,.018,.018))]:
 o=box('R3_LED_'+name,g,c,size,led);o['dimmable']=True;o['color_temperature_k']=2700;o['control']='Proposed wall dimmer; driver accessible in storage'
# Electrical points: relocate inaccessible sockets and align all plates to actual finished walls.
points=json.loads((ROOT/'source/revision2_electrical_points.json').read_text())
changes={'E1_001_SOCKET':dict(x_m=6.05,y_m=.245,face='N'),'E1_018_SOCKET':dict(x_m=7.95,y_m=11.797),'E2_035_SOCKET':dict(y_m=11.60),'E2_036_SOCKET':dict(x_m=6.651,y_m=9.12,face='E'),'E2_028_SOCKET':dict(x_m=10.95,y_m=11.797,face='S'),'E2_030_SWITCH':dict(x_m=10.95,y_m=11.797,face='S'),'E2_029_SOCKET':dict(y_m=8.60),'E2_031_SWITCH':dict(y_m=8.60)}
def relocate(p,new):
 old=dict(p);base=0 if p['level']==1 else F;delta=Vector((new.get('x_m',p['x_m'])-p['x_m'],new.get('y_m',p['y_m'])-p['y_m'],new.get('height_aff_m',p['height_aff_m'])-p['height_aff_m']));oldface=p['face'];newface=new.get('face',oldface);angles={'E':0,'N':P/2,'W':P,'S':-P/2};origin=Vector((p['x_m'],p['y_m'],base+p['height_aff_m']));rot=Matrix.Rotation(angles[newface]-angles[oldface],4,'Z');T=Matrix.Translation(origin+delta)@rot@Matrix.Translation(-origin)
 for o in bpy.data.objects:
  if o.name==p['id'] or o.name.startswith(p['id']+'_'):o.matrix_basis=T@o.matrix_basis
 p.update(new)
 if any(abs(p[k]-old[k])>.001 for k in ['x_m','y_m','height_aff_m']) or newface!=oldface:report['electrical_relocations'].append({'id':p['id'],'from':old,'to':dict(p)})
for p in points:
 if p['id'] in changes:relocate(p,changes[p['id']])
# New room points clone real socket/switch geometry and retain schedule metadata.
newpoints=[('E2_080_SOCKET','SOCKET',7.80,.245,.95,'N','Child desk power / charger'),('E2_081_DATA','DATA',7.55,.245,.95,'N','Child desk network'),('E2_082_SOCKET','SOCKET',5.525,2.60,.95,'E','Child bedside charging'),('E2_083_SWITCH','SWITCH',7.07,4.155,1.05,'S','Child main and reading light'),('E2_084_SOCKET','SOCKET',8.319,3.43,.30,'W','Child cleaning / general use'),('E2_085_SWITCH','SWITCH',5.525,2.30,1.10,'E','Child bedside switching'),('E1_090_SWITCH','SWITCH',10.365,7.94,1.05,'W','Living LED strips dimmer'),('E2_091_SWITCH','SWITCH',8.10,8.543,1.05,'N','Bedroom LED strips dimmer')]
for id,typ,x,y,z,face,purpose in newpoints:
 level=1 if id.startswith('E1') else 2;template=next(p for p in points if p['type']==typ and p['level']==level);p=dict(template);p['id']=id;p['room']='Child_Room' if id.startswith('E2_08') else 'Living' if level==1 else 'Bedroom';p['purpose']=purpose;p['proposed_group']='UPPER_CHILD' if p['room']=='Child_Room' else 'GROUND_LIGHT' if level==1 else 'UPPER_LIGHT'
 for o in [o for o in bpy.data.objects if o.name==template['id'] or o.name.startswith(template['id']+'_')]:
  n=o.copy();n.data=o.data.copy();n.name=o.name.replace(template['id'],id);groups['Child_Room' if p['room']=='Child_Room' else 'Living_Dining' if level==1 else 'Bedroom'].objects.link(n)
 relocate(p,dict(x_m=x,y_m=y,height_aff_m=z,face=face));points.append(p)
for level in [1,2]:
 layer('Ground_Design' if level==1 else 'Upper_Design');bpy.context.view_layer.update();vs=[];fs=[]
 for o in bpy.context.view_layer.objects:
  if o.type=='MESH' and (any(c.name in ['R_L1_WALLS','R_L2_WALLS'] for c in o.users_collection) or o.name.startswith('R3_Stair_Wall') or o.name.startswith('LIB_Stair_Decorative')):
   idx=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend([idx+i for i in poly.vertices] for poly in o.data.polygons)
 tree=BVHTree.FromPolygons(vs,fs);directions={'E':Vector((1,0,0)),'W':Vector((-1,0,0)),'N':Vector((0,1,0)),'S':Vector((0,-1,0))}
 for p in points:
  if p['level']!=level or p['type']=='LIGHT_POINT':continue
  d=directions[p['face']];pos=Vector((p['x_m'],p['y_m'],p['height_aff_m']+(F if level==2 else 0)));hit,normal,idx,dist=tree.ray_cast(pos+d*.08,-d,.25)
  if hit:
   target=hit+d*.0055;relocate(p,dict(x_m=target.x,y_m=target.y))
(ROOT/'data/electrical_points.json').write_text(json.dumps(points,indent=2))
# Recalculate placement bounds after doors, support corrections and removed furniture.
for level in [1,2]:
 layer('Ground_Design' if level==1 else 'Upper_Design')
 for a in placed:
  if a['level']==level:a['bounds']=bbox([bpy.data.objects[n] for n in a['objects']])
report['ready_asset_placements']=len(placed);report['asset_types']=len(set(a['role'] for a in placed));scene['interior_revision']='LIBRARY 3.0 Hinged doors, child room, fitted installation points'
(ROOT/'data/placements.json').write_text(json.dumps(placed,indent=2));(ROOT/'data/revision3_report.json').write_text(json.dumps(report,indent=2));bpy.ops.file.pack_all()
bpy.data.libraries.write(str(ROOT/'Ready_Furniture_Library.blend'),{c for c,_ in cache.values()},fake_user=True,compress=True)
layer('Upper_Design');scene.render.engine='BLENDER_EEVEE_NEXT';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'House_Library_Design.blend'),compress=True)
print('REVISION3_BUILT',len(placed),flush=True)
