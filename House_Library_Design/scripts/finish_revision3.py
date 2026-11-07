from pathlib import Path
import bpy,json,math
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(ROOT/'House_Library_Design.blend'));s=bpy.context.scene
placed=json.loads((ROOT/'data/placements.json').read_text());points=json.loads((ROOT/'data/electrical_points.json').read_text());changes=[]
for o in bpy.data.objects:
 if o.get('removed_from_design'):o.hide_viewport=True
 if o.name.startswith('R3_LED_'):o.location.z=(5.885 if 'Bedroom' in o.name else 2.885)-.009
 if o.name in ['R3_LED_Living_Rear','R3_LED_Bedroom_Rear']:o.location.y=11.63
# Three tiled shower sides; only the front is a glass door.
east=bpy.data.objects['R3_Shower_Fixed_Side_Glass'];east.name='R3_Shower_Tiled_East';east.location=(6.377,4.365,1.05);east.dimensions=(.012,.845,2.10);east.data.materials.clear();east.data.materials.append(bpy.data.materials['LIBRARY_PBR_Warm_Stone'])
back=bpy.data.objects.get('Shower_niche_back')
if back:bpy.data.objects.remove(back,do_unlink=True)
shelf=bpy.data.objects.get('Shower_niche_shelf')
if shelf:shelf.name='R3_Shower_Wall_Soap_Shelf';shelf.location.x+=.001;shelf.data.materials.clear();shelf.data.materials.append(bpy.data.materials['LIBRARY_PBR_Warm_Stone'])
# Soft, calmer children's finishes, copied so the office and other rooms stay unchanged.
for a in placed:
 if a['label'] in ['Child_Play_Rug','Child_Bookcase']:
  for n in a['objects']:
   o=bpy.data.objects[n];o.data=o.data.copy()
   for i,old in enumerate(o.data.materials):
    if not old:continue
    m=old.copy();o.data.materials[i]=m
    if not m.use_nodes:continue
    p=next((p for p in m.node_tree.nodes if p.type=='BSDF_PRINCIPLED'),None)
    if not p:continue
    color=p.inputs['Base Color'].default_value
    if a['label']=='Child_Play_Rug' or sum(color[:3])<.5:
     for l in list(p.inputs['Base Color'].links):m.node_tree.links.remove(l)
     col=(.53,.62,.48,1) if a['label']=='Child_Play_Rug' else (.79,.75,.66,1);p.inputs['Base Color'].default_value=col;m.diffuse_color=col
# Glazed doors get complete rotating leaf frames; the surrounding jamb remains fixed.
frame=bpy.data.materials.new('R3 Exterior door leaf frame');frame.use_nodes=True;bs=frame.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.028,.032,.035,1);bs.inputs['Metallic'].default_value=.45;bs.inputs['Roughness'].default_value=.3
for tag,axis,pivot,angle,g in [('L1_TERRACE_DOOR','X',(6.953,12.02,0),-65,'Entry'),('L2_REAR_BALCONY_DOOR','X',(7.953,12.02,3.2),-65,'Bedroom'),('L2_FRONT_BALCONY_DOOR','Y',(11.58,.50,3.2),65,'Office')]:
 H=Matrix.Translation(Vector(pivot))@Matrix.Rotation(math.radians(angle),4,'Z')@Matrix.Translation(-Vector(pivot));obs=[o for o in bpy.data.objects if o.name.startswith('R_'+tag+'_GLASS')]
 for glass in obs:
  vs=[H.inverted()@glass.matrix_basis@Vector(v) for v in glass.bound_box];b=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)];axisidx=0 if axis=='X' else 1;normalidx=1-axisidx;mid=[sum(bb)/2 for bb in b];span=b[axisidx][1]-b[axisidx][0];height=b[2][1]-b[2][0]
  for index in range(4):
   c=mid.copy();dims=[.04,.04,.04]
   if index<2:c[axisidx]=b[axisidx][index];dims[2]=height+.04
   else:c[2]=b[2][index-2];dims[axisidx]=span+.04
   bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=bpy.context.object;o.name='R3_Glazed_Door_Leaf_'+tag+'_'+str(index)
   for col in list(o.users_collection):col.objects.unlink(o)
   bpy.data.collections['DESIGN_'+g].objects.link(o);o.scale=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(frame);o.matrix_basis=H@o.matrix_basis;o['hinged_glazed_leaf']=True
# Dedicated service cutouts in cabinet backs prevent sockets being buried in boards.
for id,label,axis in [('E1_007_SOCKET','Kitchen_Fridge_Upper_Storage','Y'),('E1_008_SOCKET','Kitchen_Oven_Upper_Storage','Y'),('E1_009_SOCKET','Kitchen_Oven_Upper_Storage','Y'),('E1_015_SOCKET','Living_Media_Console','X')]:
 p=next(p for p in points if p['id']==id);rec=next(a for a in placed if a['label']==label)
 for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
 bpy.context.view_layer.update();bpy.ops.mesh.primitive_cube_add(size=1,location=(p['x_m'],p['y_m'],p['height_aff_m']));cut=bpy.context.object;cut.scale=(.19,.22,.14) if axis=='Y' else (.18,.19,.14);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for n in rec['objects']:
  o=bpy.data.objects[n];o.data=o.data.copy();mod=o.modifiers.new('Accessible socket service cutout','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.data.objects.remove(cut,do_unlink=True);p['installation_detail']='Dedicated accessible opening in cabinet backing; located inside storage, not embedded in furniture';changes.append(id)
(ROOT/'data/electrical_points.json').write_text(json.dumps(points,indent=2));r=json.loads((ROOT/'data/revision3_report.json').read_text());r['cabinet_service_cutouts']=changes;r['shower']={'front_hinged_door_leaves':1,'tiled_sides':3,'tiled_integrated_base':True};r['additional_project_lighting']='Only four requested LED profiles; no new general lighting';(ROOT/'data/revision3_report.json').write_text(json.dumps(r,indent=2));bpy.ops.file.pack_all()
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Upper_Design']
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'House_Library_Design.blend'),compress=True);print('REVISION3_FINISHED')
