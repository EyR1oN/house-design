"""House variant using downloaded ready-made assets; original project untouched."""
from pathlib import Path
import bpy,json,math,hashlib,bmesh
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1]
manifest={a['role']:a for a in json.loads((ROOT/'data/library_manifest.json').read_text(encoding='utf8'))}
audit={a['role']:a for a in json.loads((ROOT/'data/library_audit.json').read_text(encoding='utf8'))}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source/House_Intermediate.blend'))
scene=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=scene.view_layers['Upper_Design']
groups={n:bpy.data.collections['DESIGN_'+n] for n in ['Kitchen','Living_Dining','Entry','WC','Laundry','Lighting_Decor','Stair_Storage','Ground_Details','Bedroom','Office','Upper_Bath','Wardrobe','Upper_Hall','Upper_Lighting']}
cache={};placed=[]
def erase(prefixes,group=None):
 for o in list(groups[group].all_objects if group else bpy.data.objects):
  if o.name.startswith(tuple(prefixes)):bpy.data.objects.remove(o,do_unlink=True)
def native_world(o):
 if o.parent:return native_world(o.parent)@o.matrix_parent_inverse@o.matrix_basis
 return o.matrix_basis.copy()
def load(role):
 if role in cache:return cache[role]
 with bpy.data.libraries.load(str(ROOT/'assets/prepared'/f'{role}.blend'),link=False) as (src,dst):dst.objects=src.objects
 obs=[o for o in dst.objects if o];world={o:native_world(o) for o in obs}
 wanted={a['name'] for a in audit[role]['objects']}
 c=bpy.data.collections.new('READY_ASSET_'+role)
 accepted=[]
 for o in obs:
  original=o.name
  # Blender can suffix a loaded name when an old scene object shares it.
  match=original if original in wanted else next((n for n in sorted(wanted,key=len,reverse=True) if original.startswith(n+'.')),None)
  if o.type not in ['MESH','CURVE','FONT','SURFACE'] or not match or o.hide_render:continue
  if role=='curtain' and 'Plane02' in match:
   o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.y>-1.8],context='VERTS');bm.to_mesh(o.data);bm.free();o.data.update()
  o.parent=None;o.matrix_basis=world[o];o.animation_data_clear();o['source_object_name']=match;o.name='SOURCE_'+role+'_'+match;c.objects.link(o);accepted.append(o)
  for mod in o.modifiers:
   if mod.type=='SUBSURF':mod.levels=min(mod.levels,1);mod.render_levels=min(mod.render_levels,1)
 c.asset_mark();c.asset_data.author=manifest[role]['author'];c.asset_data.description=manifest[role]['name']+' | '+manifest[role]['license']+' | '+manifest[role]['source_url'];c.use_fake_user=True
 cache[role]=(c,accepted)
 return cache[role]
def bbox(obs,R=None):
 R=R or Matrix.Identity(4);vs=[R@o.matrix_basis@Vector(v) for o in obs for v in o.bound_box]
 return [(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)]
def asset(role,label,group,center,dimensions,base,rot=(0,0,0),mirror=False,omit=(),uniform=None,only=()):
 c,source=load(role);source=[o for o in source if not any(t in o.get('source_object_name','') for t in omit) and (not only or any(t in o.get('source_object_name','') for t in only))]
 R=Matrix.Rotation(rot[2],4,'Z')@Matrix.Rotation(rot[1],4,'Y')@Matrix.Rotation(rot[0],4,'X')
 if mirror:R=R@Matrix.Diagonal((-1,1,1,1))
 bb=bbox(source,R);dims=[b-a for a,b in bb];sc=[uniform]*3 if uniform else [dimensions[i]/dims[i] if dimensions[i] else 1 for i in range(3)]
 T=Matrix.Translation((center[0],center[1],base))@Matrix.Diagonal((*sc,1))@Matrix.Translation((-(bb[0][0]+bb[0][1])/2,-(bb[1][0]+bb[1][1])/2,-bb[2][0]))@R
 instance=bpy.data.collections.new('LIB_'+label);groups[group].children.link(instance);copies={}
 for original in source:
  o=original.copy();o.data=original.data;o.parent=None;o.matrix_basis=T@original.matrix_basis;o.name='LIB_'+label+'_'+original.get('source_object_name',original.name);instance.objects.link(o)
  o['design_status']='PROPOSED_LIBRARY_INTERIOR';o['section']='RIGHT';o['level']=1 if group in ['Kitchen','Living_Dining','Entry','WC','Laundry','Lighting_Decor','Stair_Storage','Ground_Details'] else 2;o['library_role']=role;o['source_url']=manifest[role]['source_url'];o['license']=manifest[role]['license'];copies[original]=o
 for original,o in copies.items():
  for mod in o.modifiers:
   if hasattr(mod,'object') and mod.object in copies:mod.object=copies[mod.object]
 bbout=bbox(list(copies.values()));rec={'label':label,'role':role,'group':group,'level':next(iter(copies.values()))['level'],'source_url':manifest[role]['source_url'],'license':manifest[role]['license'],'bounds':bbout,'scale':sc,'objects':[o.name for o in copies.values()]};placed.append(rec)
 print('PLACED',label,flush=True);return list(copies.values())
P=math.pi;F=3.2
# Living and dining. Mirror the L model so the return follows the rear window.
erase(['Unified_L_sofa','L_sofa_','Coffee_table','Coffee_cup','Coffee_album','Coffee_tray','Vase','Dining_table','Table_leg','Chair_'],None)
asset('corner_sofa','Living_Corner_Sofa','Living_Dining',(9.245,10.335),(2.19,2.69,.91),0,rot=(0,0,-P/2),mirror=True)
asset('coffee_table','Living_Coffee_Table','Living_Dining',(8.54,10.11),(.67,.60,.43),.015)
asset('dining_table','Dining_Table','Living_Dining',(8.49,8.69),(1.56,.80,.775),0,omit=('Side Table',))
for x in [7.99,8.99]:asset('dining_chair',f'Dining_Chair_{x}','Living_Dining',(x,8.00),(.52,.56,.81),0,rot=(0,0,P))
asset('entry_bench','Dining_Bench','Living_Dining',(8.49,9.34),(1.38,.48,.47),0)
asset('tableware','Dining_Ceramics','Living_Dining',(8.40,8.69),(.30,.45,.12),.775)
asset('ceramic_vase','Living_Vase','Living_Dining',(8.59,10.12),(.13,.13,.18),.445)
erase(['Living_rug','Bedroom_rug','Entry_runner'])
asset('rug','Living_Rug','Living_Dining',(8.86,10.20),(2.60,2.12,.009),.002,rot=(0,0,P/2))
# Bedroom: retain the agreed rotated layout and south-wall wardrobe position.
erase(['Bed_','Headboard_channel','Bedside_cabinet','Bedside_drawer','Bedside_books','Bedroom_wardrobe_','Bedroom_art_','Bedroom_TV_bezel','Bedroom_TV_glass','Bedroom_soundbar'],'Bedroom')
asset('bed','Bedroom_Bed','Bedroom',(10.155,10.02),None,F+.008,rot=(0,0,-P/2),uniform=.90)
for x,mirror in [(9.205,False),(10.655,True)]:asset('wardrobe','Bedroom_Wardrobe_'+str(x),'Bedroom',(x,7.80),(1.45,.58,2.675),F,rot=(0,0,P),mirror=mirror)
for y in [8.78,11.32]:asset('bedside_table','Bedroom_Nightstand_'+str(y),'Bedroom',(11.05,y),(.36,.35,.48),F,rot=(0,0,-P/2))
asset('television','Bedroom_TV','Bedroom',(6.69,10.02),(.085,1.40,.81),F+1.16,rot=(P/2,0,P/2))
asset('rug','Bedroom_Rug','Bedroom',(9.95,10.05),(2.80,2.77,.009),F+.002)
asset('wall_art','Bedroom_Art','Bedroom',(11.36,10.10),(.025,1.25,.74),F+1.50,rot=(P/2,0,-P/2))
erase(['Bedroom_vanity_top','Bedroom_vanity_drawer','Vanity_leg','Vanity_tray','Vanity_perfume'],'Bedroom')
asset('vanity_desk','Bedroom_Vanity_Desk','Bedroom',(6.855,11.245),(.45,1.10,.75),F,rot=(0,0,P/2))
erase(['Vanity_stool'],'Bedroom')
asset('dining_chair','Bedroom_Vanity_Chair','Bedroom',(7.40,11.22),(.54,.50,.81),F,rot=(0,0,-P/2))
# Office: ready desks, four displays, two ergonomic chairs, real printer and weights.
erase(['Desk_1_','Desk_2_','Screen_code_line','Keyboard_key','PC_fan','Office_chair_','3D_Printer_','Dumbbell_handle','Dumbbell_weight'],'Office')
for k,y in enumerate([3.22,4.52],1):
 asset('desk_wooden',f'Office_Desk_{k}','Office',(11.055,y),(.65,1.19,.94),F)
 asset('office_chair',f'Office_Chair_{k}','Office',(10.08,y),(.64,.64,1.03),F,rot=(0,0,P/2))
 for j,yy in enumerate([y-.275,y+.275],1):asset('monitor',f'Office_Monitor_{k}_{j}','Office',(11.13,yy),(.13,.51,.39),F+.765,rot=(0,0,-P/2))
 asset('keyboard_mouse',f'Office_Keyboard_{k}','Office',(10.89,y),(.14,.44,.023),F+.755,rot=(0,0,-P/2))
for k,y in enumerate([3.22,4.52],1):asset('desk_lamp',f'Office_Task_Lamp_{k}','Office',(11.06,y-.44),None,F+.652,rot=(0,0,-P/2),uniform=.65)
asset('3d_printer','Office_3D_Printer','Office',(8.77,1.14),None,F+.875,uniform=.72)
for y in [3.0,3.36,3.72]:asset('dumbbell',f'Office_Weight_{y}','Office',(8.68,y),(.16,.30,.13),F+.70,rot=(0,0,P/2))
# Ready P wardrobe modules, not a single standalone cupboard.
erase(['P_wardrobe_'],'Wardrobe')
for y in [4.768333,5.665,6.561667]:asset('open_wardrobe','Closet_West_'+str(y),'Wardrobe',(5.765,y),(.55,.896667,2.675),F,rot=(0,0,P/2))
for label,y,rz in [('North',6.735,0),('South',4.595,P)]:asset('open_wardrobe','Closet_'+label,'Wardrobe',(6.475,y),(.87,.55,2.675),F,rot=(0,0,rz))
# Open shelves remain clear; hanging jeans are unsuitable folded shelf props.
asset('bathroom_mirror','Closet_Full_Mirror','Wardrobe',(6.889,6.28),(.015,.30,2.05),F+.35,rot=(-P/2,0,P/2))
# Kitchen modules and appliances; keep the source-sized continuous L worktop.
erase(['Base_','Return_drawers','Dishwasher_','Sink_','Induction_','Hob_touch','Hood_canopy','Hood_filter','Corner_prep_','Fridge_front','Fridge_split','Fridge_handle','Oven_steel','Oven_door','Oven_handle','Oven_control','Oven_knob','Microwave_','Corner_upper','Crockery_back','Crockery_side','Crockery_shelf','Crockery_plinth','Crockery_door','Crockery_pull','Stored_plate','Stored_bowl'],'Kitchen')
for label,y,d in [('Return',4.825,.45),('Sink',5.3725,.645),('Hob',6.6275,.965)]:
 asset('kitchen_cabinet','Kitchen_Base_'+label,'Kitchen',(10.07,y),(.64,d,.86),0,rot=(0,0,-P/2),omit=('Top_V3',))
asset('kitchen_cabinet','Kitchen_Corner_Prep','Kitchen',(9.87,4.26),(1.06,.68,.86),0,rot=(0,0,P),omit=('Top_V3',))
for y in [6.185,6.735]:asset('kitchen_cabinet','Kitchen_Crockery_'+str(y),'Kitchen',(8.255,y),(.55,.55,.86),0,rot=(0,0,P/2),omit=('Top_V3',))
asset('dishwasher','Kitchen_Dishwasher_45cm','Kitchen',(10.07,5.92),(.60,.45,.75),.10,rot=(0,0,-P/2))
asset('kitchen_sink','Kitchen_Window_Sink','Kitchen',(10.06,5.35),(.46,.62,None),.699,rot=(0,0,-P/2))
asset('induction_cooktop','Kitchen_Hob','Kitchen',(10.055,6.49),(.49,.59,.008),.911,rot=(0,0,-P/2))
asset('refrigerator','Kitchen_Fridge','Kitchen',(8.34,4.27),(.63,.64,1.88),.12,rot=(0,0,P))
asset('oven','Kitchen_Oven','Kitchen',(9.015,4.36),(.58,.58,.56),.68,rot=(0,0,P))
asset('microwave','Kitchen_Microwave','Kitchen',(9.015,4.40),(.57,.50,.38),1.36,rot=(0,0,P))
asset('range_hood','Kitchen_Hood','Kitchen',(10.15,6.49),(.44,.60,.105),1.76,rot=(P/2,0,-P/2))
asset('laundry_cabinet','Kitchen_Upper_Corner','Kitchen',(9.8675,4.095),(1.045,.34,1.335),1.54,rot=(P/2,0,P))
for w in bpy.context.window_manager.windows:w.view_layer=scene.view_layers['Ground_Design']
bpy.context.view_layer.update()
# Ready pantry carcasses replace the primitive refrigerator and oven housings.
erase(['Fridge_body','Fridge_upper_lower_front','OvenTower_body','OvenTower_upper_lower_front','Mixer_arch','Mixer_lever'],'Kitchen')
fridge_housing=asset('tall_cabinet','Kitchen_Fridge_Housing','Kitchen',(8.32,4.26),(.74,.68,2.875),0,rot=(0,0,P))
oven_housing=asset('tall_cabinet','Kitchen_Oven_Housing','Kitchen',(9.015,4.26),(.65,.68,2.875),0,rot=(0,0,P))
for obs,x,z,h,width in [(fridge_housing,8.34,1.055,1.95,.65),(oven_housing,9.015,.96,.60,.60),(oven_housing,9.015,1.55,.42,.59),(fridge_housing,8.34,2.45625,.8375,.65),(oven_housing,9.015,2.32625,1.0975,.60)]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,4.30,z));cutter=bpy.context.object;cutter.scale=(width,.98,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for target in obs:
  target.data=target.data.copy();mod=target.modifiers.new('Fitted appliance opening','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.context.view_layer.objects.active=target;bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.data.objects.remove(cutter,do_unlink=True)
asset('kitchen_cabinet','Kitchen_Fridge_Upper_Storage','Kitchen',(8.34,4.27),(.65,.64,.8375),2.0375,rot=(0,0,P))
asset('kitchen_cabinet','Kitchen_Oven_Upper_Storage','Kitchen',(9.015,4.27),(.60,.64,1.0975),1.7775,rot=(0,0,P))
# Shorter, wider island / crockery block: 550 x 1100 mm, clear of the fridge swing.
top=bpy.data.objects['Crockery_oak_top'];top.location=(8.255,6.46,.875);top.dimensions=(.585,1.135,.03)
bpy.context.view_layer.update()
# Clear a correct sink aperture in the retained dimensioned countertop.
worktop=bpy.data.objects['Kitchen_CONTINUOUS_L_WORKTOP']
bpy.ops.mesh.primitive_cube_add(size=1,location=(10.06,5.35,.90));cut=bpy.context.object;cut.scale=(.415,.58,.32);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for o in [worktop]+list(bpy.data.collections['LIB_Kitchen_Base_Sink'].objects):
 if o.type!='MESH':continue
 o.data=o.data.copy()
 mod=o.modifiers.new('Fitted sink aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.context.view_layer.objects.active=o
 try:bpy.ops.object.modifier_apply(modifier=mod.name)
 except:pass
bpy.data.objects.remove(cut,do_unlink=True)
erase(['Living_wall_TV_'],'Stair_Storage')
asset('television','Living_TV','Stair_Storage',(6.79,9.65),(.08,1.40,.81),1.0,rot=(P/2,0,P/2))
erase(['Floating_media_console','Media_drawer','Media_books','TV_wall_mount'],'Stair_Storage')
asset('media_console','Living_Media_Console','Stair_Storage',(6.84,9.65),(.37,1.65,.50),0,rot=(0,0,P/2))
# Ready sanitary fittings in the existing compact room envelopes.
erase(['Upper_bathtub','Bath_drain','Bath_wall_spout','Bath_mixer','Bath_bridge','Bath_tray','Bath_candle','Upper_vanity_carcass','Upper_vanity_drawer','Upper_vanity_stone','Upper_vanity_basin','Upper_vanity_spout','Upper_basin_control','Upper_vanity_oval_mirror','Upper_mirror_brass','Upper_WC_bowl','Upper_WC_seat','Upper_WC_pedestal','Upper_flush_plate','Folded_bath_towel'],'Upper_Bath')
asset('bathtub','Upper_Bath_Tub','Upper_Bath',(10.97,6.425),(.78,1.70,.831),F+.025,rot=(0,0,P/2))
asset('bathroom_basin','Upper_Bath_Vanity','Upper_Bath',(9.75,5.765),(1.10,.52,.56),F+.34,rot=(-P/2,0,0))
asset('bathroom_mirror','Upper_Bath_Mirror','Upper_Bath',(9.75,5.517),(1.05,.015,.85),F+1.12,rot=(-P/2,0,0))
asset('toilet','Upper_Bath_Toilet','Upper_Bath',(8.90,6.80),(.395,.64,.93),F+.16,rot=(P/2,0,0))
asset('towel','Upper_Bath_Towels','Upper_Bath',(9.69,7.00),(.36,.15,.085),F+1.695)
erase(['Ground_shower_tray','Ground_linear_drain','Drain_slots','Shower_glass','Shower_screen','Ground_shower_','Ground_rain_head','Compact_ground_','Ground_basin_mixer','Ground_basin_mirror','WC_bowl','WC_seat','Flush_plate'],'WC')
asset('shower','Ground_Shower','WC',(5.94,4.37),(.87,.87,2.09),.01,rot=(0,0,P/2))
asset('bathroom_basin','Ground_Compact_Vanity','WC',(5.66,5.69),(.30,.56,.49),.40,rot=(-P/2,0,-P/2))
asset('bathroom_mirror','Ground_Vanity_Mirror','WC',(5.515,5.69),(.012,.51,.76),1.10,rot=(-P/2,0,-P/2))
asset('toilet','Ground_Toilet','WC',(5.94,6.41),(.39,.62,.93),.16,rot=(P/2,0,0))
# Entrance and laundry also use ready furniture.
erase(['Entry_wardrobe','Wardrobe_door','Wardrobe_pull'],'Entry')
for y in [1.0825,2.8075]:asset('wardrobe','Entry_Wardrobe_'+str(y),'Entry',(5.80,y),(.60,1.725,2.875),0,rot=(0,0,P/2))
asset('rug','Entry_Rug','Entry',(7.10,2.05),(.72,2.45,.009),.002)
erase(['Washer','Dryer','Folded_towels'],'Laundry')
asset('washing_machine','Laundry_Washer','Laundry',(8.99,3.46),(.59,.60,.84),.02)
asset('dryer','Laundry_Dryer','Laundry',(9.64,3.46),(.59,.60,.84),.02)
asset('towel','Laundry_Towels','Laundry',(9.4,3.42),(.31,.30,.11),.91)
erase(['Shoe_bench','Bench_cushion'],'Entry')
asset('entry_bench','Entry_Bench','Entry',(7.70,.47),(.90,.48,.47),0)
# Library lamps replace crude decorative discs; light emitters retain their coordinates.
erase(['Dining_pendant_shade','Dining_pendant_stem','Dining_pendant_wire','Bedroom_ceiling_shade','Bedroom_ceiling_stem','Office_ceiling_shade','Office_ceiling_stem'])
for label,group,x,y,z,h in [('Dining1','Living_Dining',7.99,8.69,2.02,.82),('Dining2','Living_Dining',8.99,8.69,2.02,.82),('Bedroom','Bedroom',9.72,9.62,F+2.22,.43),('Office','Office',9.75,3.1,F+2.25,.40)]:asset('pendant_lamp','Pendant_'+label,group,(x,y),(.43,.43,h),z,rot=(P,0,0))
# Native models for plants and fine domestic details.
for prefixes,group,xy,z,size in [(['Office_floor_plant'],'Office',(9.70,2.30),F,.58),(['Bathroom_small_plant'],'Upper_Bath',(10.18,7.0),F+1.705,.19),(['Sideboard_ceramic'],'Kitchen',(8.255,6.80),.89,.20)]:
 erase(prefixes,group);asset('potted_plant','Plant_'+group,group,xy,(size,size,size*.90),z)
asset('potted_plant','Bedroom_Plant','Bedroom',(6.93,11.42),(.16,.16,.18),F+.75)
asset('books','Bedroom_Books','Bedroom',(6.87,10.85),(.21,.20,.20),F+.75)
asset('wall_art','Living_Art','Living_Dining',(10.36,8.28),(.025,1.0,.70),1.34,rot=(P/2,0,-P/2))
erase(['Living_art_frame','Living_art_canvas'],'Living_Dining')
# Ready curtains gathered to the sides, preserving balcony/terrace door access.
erase(['Curtain_','Bedroom_curtain_fold'])
for group,level,x,width in [('Living_Dining',1,6.72,.25),('Living_Dining',1,9.27,.26),('Bedroom',2,7.70,.26),('Bedroom',2,10.31,.35)]:asset('curtain','Curtain_'+group+'_'+str(x),group,(x,11.70),(width,.14,2.62),(level-1)*3.2+.04,rot=(0,0,P/2),omit=('Plane01',))
# Complete ready-made furniture replacement, including storage and all decorative fixtures.
erase(['Printer_bench','Printer_cabinet_front','Printer_tools_tray','Printer_manuals','Dumbbell_rack','Office_bookcase','Office_library','Office_storage_box','Desk_notebook','Desk_coffee_mug','Office_balcony_curtain','Office_fitness_mirror'],'Office')
asset('printer_sideboard','Office_Printer_Sideboard','Office',(8.77,1.40),(.58,1.38,.875),F,rot=(0,0,P/2))
asset('printer_sideboard','Office_Weight_Cabinet','Office',(8.68,3.37),(.36,1.16,.70),F,rot=(0,0,P/2))
shelves=asset('bookcase','Office_Bookcase','Office',(9.51,.395),(1.08,.32,2.28),F,rot=(0,0,P))
levels=sorted({round((o.matrix_basis@poly.center).z,3) for o in shelves for poly in o.data.polygons if poly.normal.z>.95 and poly.area>.004 and (o.matrix_basis@poly.center).z>F+.10})
print('BOOKCASE_SHELF_LEVELS',levels,flush=True)
for k,x in [(0,9.22),(2,9.74)]:
 z=levels[min(k,len(levels)-1)] if levels else F+.67+k*.35
 asset('books','Office_Books_'+str(k),'Office',(x,.40),(.26,.20,.25),z)
plant_z=levels[-2] if len(levels)>1 else F+1.87
asset('potted_plant','Office_Shelf_Plant','Office',(9.71,.40),(.24,.22,.27),plant_z)
asset('bathroom_mirror','Office_Fitness_Mirror','Office',(8.477,3.37),(.016,1.00,1.70),F+.62,rot=(-P/2,0,-P/2))
for y,w in [(.30,.15),(2.28,.27)]:asset('curtain','Office_Curtain_'+str(y),'Office',(10.35,y),(.14,w,2.62),F+.035,omit=('Plane01',))
erase(['Understair_shelf','Understair_storage_back','Storage_manuals','Storage_basket'],'Stair_Storage')
under_bookcase=asset('bookcase','Understair_Bookcase','Stair_Storage',(5.675,8.98),(.35,.46,1.70),.03,rot=(0,0,P/2))
asset('kitchen_cabinet','Understair_Drawer_Cabinet','Stair_Storage',(5.675,9.65),(.35,.50,.80),.03,rot=(0,0,P/2))
asset('storage_basket','Understair_Basket','Stair_Storage',(5.70,10.20),(.28,.34,.25),.03)
under_shelves=sorted(set(round((o.matrix_basis@poly.center).z,3) for o in under_bookcase for poly in o.data.polygons if poly.normal.z>.95 and poly.area>.004))
asset('books','Understair_Books','Stair_Storage',(5.67,8.98),(.20,.22,.19),under_shelves[1],rot=(0,0,P/2))
erase(['Laundry_upper'],'Laundry')
asset('laundry_cabinet','Laundry_Full_Upper_Storage','Laundry',(9.43,3.59),(1.88,.34,1.375),1.50,rot=(P/2,0,0))
erase(['Bedside_pendant_'],'Bedroom')
for y in [8.82,11.20]:asset('pendant_lamp','Bedroom_Bedside_Pendant_'+str(y),'Bedroom',(10.94,y),(.22,.22,1.455),F+1.22,rot=(P,0,0))
erase(['Ceiling_light','Pendant_wire','Pendant_shade','Pendant_brass'],'Lighting_Decor')
for group,x,y,w in [('Entry',7.10,1.7,.38),('Kitchen',9.18,5.3,.42),('Living_Dining',8.25,10.4,.42),('WC',5.94,5.68,.30),('Laundry',9.4,3.3,.28)]:asset('ceiling_light','Ground_Flush_'+group,group,(x,y),(w,w,.092),2.785)
erase(['Upper_bath_ceiling_shade','Upper_bath_ceiling_stem','Bathroom_sconce','Bathroom_towel_rail','Towel_rail_bar','Upper_bath_towel','Bath_toiletry'],'Upper_Bath')
asset('ceiling_light','Upper_Bath_Flush','Upper_Bath',(9.75,6.4),(.34,.34,.092),F+2.59)
for x in [9.06,10.44]:asset('sconce','Upper_Bath_Sconce_'+str(x),'Upper_Bath',(x,5.56),(.12,.12,.49),F+1.44,rot=(P/2,0,P))
asset('radiator','Upper_Bath_Towel_Radiator','Upper_Bath',(8.515,6.89),(.075,.38,1.04),F+.62,rot=(P/2,0,P/2))
asset('towel','Upper_Bath_Hanging_Towel','Upper_Bath',(8.535,6.89),(.070,.26,.05),F+1.66)
erase(['Upper_hall_runner','Upper_hall_ceiling_shade','Upper_hall_ceiling_stem'],'Upper_Hall')
asset('rug','Upper_Hall_Runner','Upper_Hall',(7.62,5.90),(.58,2.08,.009),F+.002)
asset('ceiling_light','Upper_Hall_Flush','Upper_Hall',(7.61,5.70),(.28,.28,.092),F+2.59)
asset('ceiling_light','Closet_Flush','Wardrobe',(6.475,5.65),(.25,.25,.092),F+2.59)
erase(['Entry_books','Entry_key_tray','Entry_keyring','Entry_greenery','Media_books_spine'],'Ground_Details')
asset('potted_plant','Entry_Ready_Plant','Entry',(7.45,.43),(.18,.18,.21),.47)
asset('books','Entry_Ready_Books','Entry',(7.78,.42),(.20,.17,.18),.47)
erase(['Art_relief'],'Living_Dining')
erase(['Corner_cutting_board','Knife_blade','Knife_handle','Lime','Sideboard_tray'],'Kitchen')
asset('kitchen_accessories','Kitchen_Cutting_Boards','Kitchen',(9.62,4.26),(.25,.32,.025),.913)
erase(['Shower_bottle','Ground_towel','Ground_WC_brush'],'WC')
asset('bath_accessories','Ground_Vanity_Soap','WC',(5.56,5.86),(.055,.055,.16),.89,only=('Lotion Dispenser',))
asset('bath_accessories','Upper_Vanity_Soap','Upper_Bath',(10.17,5.57),(.06,.06,.17),F+.90,only=('Lotion Dispenser',))
asset('bath_accessories','Upper_Vanity_Cup','Upper_Bath',(10.06,5.57),(.055,.055,.10),F+.90,only=('Tumbler',))
asset('bath_accessories','Upper_Vanity_Tray','Upper_Bath',(9.38,5.57),(.16,.07,.015),F+.90,only=('Tray',))
asset('bath_accessories','Upper_Bath_Tissues','Upper_Bath',(9.39,7.0),(.12,.12,.15),F+1.705,only=('Tissue Cover',))
asset('bath_accessories','Upper_Bath_Bin','Upper_Bath',(8.65,5.65),(.18,.18,.23),F,omit=('Tumbler','Tray','Tissue Cover','Lotion Dispenser'))
erase(['Bath_linen_shelf'],'Upper_Bath')
asset('kitchen_cabinet','Upper_Bath_Linen_Shelf','Upper_Bath',(9.78,7.015),(1.07,.16,.025),F+1.68,only=('Top_V3',))
# Keep proposed wiring coordinates aligned with the relocated desk.
points=json.loads((ROOT/'data/electrical_points.json').read_text(encoding='utf8'))
for a in points:
 if a['id']=='E2_035_SOCKET':
  new_y=10.95;delta=new_y-bpy.data.objects[a['id']].location.y;a['y_m']=new_y
  for o in bpy.data.objects:
   if o.name.startswith(a['id']):o.location.y+=delta
for k,(x,purpose) in enumerate([(7.99,'Dining pendant 1'),(8.99,'Dining pendant 2')]):
 for a in points:
  if a.get('purpose')==purpose:
   base=bpy.data.objects.get(a['id']);dx=x-base.location.x if base else 0;dy=8.69-base.location.y if base else 0;a['x_m']=x;a['y_m']=8.69
   for o in bpy.data.objects:
    if o.name.startswith(a['id']):o.location.x+=dx;o.location.y+=dy
 lamps=sorted([o for o in bpy.data.objects if o.type=='LIGHT' and o.name.startswith('Dining_pendant')],key=lambda o:o.name)
 if k<len(lamps):lamps[k].location.x=x;lamps[k].location.y=8.69
(ROOT/'data/electrical_points.json').write_text(json.dumps(points,indent=2),encoding='utf8')
# Calibrated finishes rather than placeholder furniture geometry remain custom.

# Correct author-supplied missing auxiliary images rather than leaving pink shaders.
missing=[]
for im in list(bpy.data.images):
 if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists():
  missing.append(im.name)
  for m in bpy.data.materials:
   if m.use_nodes:
    for node in list(m.node_tree.nodes):
     if node.type=='TEX_IMAGE' and node.image==im:m.node_tree.nodes.remove(node)
  bpy.data.images.remove(im)
# Real PBR finishes for fixed geometry; projected UVs preserve metric grain scales.
def pbr(name,slug,tint=(1,1,1)):
 m=bpy.data.materials.new(name);m.use_nodes=True;ns=m.node_tree.nodes;ls=m.node_tree.links;p=ns.get('Principled BSDF');m.diffuse_color=(*tint,1)
 for typ in ['diff','rough','nor_gl']:
  path=next((ROOT/'assets/materials').glob(slug+'_'+typ+'.*'));im=bpy.data.images.load(str(path),check_existing=True);node=ns.new('ShaderNodeTexImage');node.image=im
  if typ!='diff':im.colorspace_settings.name='Non-Color'
  if typ=='diff':mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.75 if slug=='white_plaster_02' else 0;mix.inputs[2].default_value=(*tint,1);ls.new(node.outputs['Color'],mix.inputs[1]);ls.new(mix.outputs[0],p.inputs['Base Color'])
  elif typ=='rough':ls.new(node.outputs['Color'],p.inputs['Roughness'])
  else:n=ns.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.08;ls.new(node.outputs['Color'],n.inputs['Color']);ls.new(n.outputs[0],p.inputs['Normal'])
 return m
def assign(o,m,scale=.5):
 if o.type!='MESH':return
 o.data.materials.clear();o.data.materials.append(m)
 uv=o.data.uv_layers.get('LibraryMetricUV') or o.data.uv_layers.new(name='LibraryMetricUV')
 for p in o.data.polygons:
  dominant=max(range(3),key=lambda i:abs(p.normal[i]));axes={0:(1,2),1:(0,2),2:(0,1)}[dominant]
  for i in p.loop_indices:
   v=o.matrix_basis@o.data.vertices[o.data.loops[i].vertex_index].co;uv.data[i].uv=(v[axes[0]]*scale,v[axes[1]]*scale)
wood=pbr('LIBRARY_PBR_Oak_Floor','wooden_floor_02');wood.diffuse_color=(.40,.27,.17,1);stone=pbr('LIBRARY_PBR_Warm_Stone','marble_01',(.88,.81,.70));plaster=pbr('LIBRARY_PBR_Warm_Plaster','white_plaster_02',(.94,.91,.85))
for o in bpy.data.objects:
 if o.name.startswith('R_') and o.name.endswith('_FLOOR_FINISH'):
  if 'BEDROOM' in o.name or 'WARDROBE' in o.name:assign(o,wood)
  elif 'L1_' in o.name or 'BATHROOM' in o.name:assign(o,stone)
 if any(c.name in ['R_L1_WALLS','R_L2_WALLS'] for c in o.users_collection):assign(o,plaster)
 if o.name.startswith(('Kitchen_CONTINUOUS','Corner_stone','Hob_stone','Corner_east_splash','Crockery_oak_top','Upper_bath_')) and o.type=='MESH' and not o.name.startswith('Upper_bath_towel'):assign(o,stone)
# Harmonise ready cabinet finish without losing metal fittings and detailed topology.
for role,col in [('kitchen_cabinet',(.54,.50,.43)),('wardrobe',(.59,.55,.47)),('open_wardrobe',(.45,.32,.20)),('tall_cabinet',(.54,.50,.43))]:
 _,obs=cache[role]
 for o in obs:
  for m in o.data.materials:
   if not m or not m.use_nodes:continue
   p=m.node_tree.nodes.get('Principled BSDF')
   if p and p.inputs['Metallic'].default_value<.5:
    if role in ['kitchen_cabinet','tall_cabinet']:
     for link in list(p.inputs['Base Color'].links):m.node_tree.links.remove(link)
    if not p.inputs['Base Color'].is_linked:p.inputs['Base Color'].default_value=(*col,1);m.diffuse_color=(*col,1)
# Warm practical emitters for the closet and two ready desk lamps.
for name,g,x,y,z,power in [('Closet_light','Wardrobe',6.42,5.65,5.80,100),('Office_task_light_1','Office',10.95,2.78,4.32,30),('Office_task_light_2','Office',10.95,4.08,4.32,30)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=(1,.86,.72);d.size=.22;o=bpy.data.objects.new(name,d);groups[g].objects.link(o);o.location=(x,y,z)
# Soft fill across the open wardrobe shelves, without changing source geometry.
d=bpy.data.lights.new('Closet_front_fill','AREA');d.energy=75;d.color=(1,.90,.79);d.shape='RECTANGLE';d.size=1.1;d.size_y=1.3;o=bpy.data.objects.new('Closet_front_fill',d);groups['Wardrobe'].objects.link(o);o.location=(6.78,5.65,F+1.94);o.rotation_euler.y=P/2
# Pack downloaded assets and all reference drawings for an offline, portable project.
bpy.ops.file.pack_all()
(ROOT/'data/placements.json').write_text(json.dumps(placed,indent=2),encoding='utf8')
(ROOT/'data/build_report.json').write_text(json.dumps({'status':'BUILT','ready_asset_types_used':len(cache),'ready_asset_placements':len(placed),'missing_auxiliary_maps_repaired':missing,'custom_retained':['Structural house shell and stairs','Source-sized continuous L countertop and island worktop','Stair TV partition and storage door','Architectural finishes, door panels and MEP point markers'],'dishwasher_nominal_width_m':.45,'backup_unchanged':True},indent=2),encoding='utf8')
# Create a local Asset Browser library alongside the finished project.
bpy.data.libraries.write(str(ROOT/'Ready_Furniture_Library.blend'),{c for c,_ in cache.values()},fake_user=True,compress=True)
scene['interior_revision']='LIBRARY 2.0 Fitted furniture and revised layout';scene['model_variant']='Separate variant; intermediate original preserved'
for screen in bpy.data.screens:
 for a in screen.areas:
  if a.type=='VIEW_3D':a.spaces.active.overlay.show_overlays=False
scene.render.engine='BLENDER_EEVEE_NEXT';scene.display.shading.color_type='MATERIAL'
for w in bpy.context.window_manager.windows:w.view_layer=scene.view_layers['Upper_Design']
scene.camera=bpy.data.objects['INTERIOR4_UPPER_OVERVIEW']

for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.shading.type='SOLID';area.spaces.active.shading.use_scene_lights=False;area.spaces.active.shading.use_scene_world=False
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'House_Library_Design.blend'),compress=True)
print('LIBRARY_DESIGN_BUILT',len(placed),flush=True)
