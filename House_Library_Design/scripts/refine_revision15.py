from pathlib import Path
import bpy,json,shutil,math
from mathutils import Vector
R=Path(__file__).resolve().parents[1];backup=R.parent/'House_Library_Revision14_Backup'
assert not backup.exists(),'Revision15 already started: inspect rather than reapply'
backup.mkdir()
for n in ['House_Library_Design.blend','README.md','Design_Gallery.html']:shutil.copy2(R/n,backup/n)
for n in ['data','previews']:shutil.copytree(R/n,backup/n)
shutil.copy2(R.parent/'HOUSE_HANDOFF_UK.md',backup/'HOUSE_HANDOFF_UK.md')
for n in ['House_Viewer.html','House_Floor_1.glb','House_Floor_2.glb']:shutil.copy2(R.parent/'House_Browser_Viewer'/n,backup/n)
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text(encoding='utf8'));row=next(r for r in p if r['label']=='Kitchen_Hood');removed=row['objects']+['Hood_chimney']
for n in removed:
 o=bpy.data.objects.get(n)
 if o:bpy.data.objects.remove(o,do_unlink=True)
group=bpy.data.collections['DESIGN_Kitchen'];white=bpy.data.materials['R7 Warm appliance enamel'];metal=bpy.data.materials['R7 Brushed warm metal'];dark=bpy.data.materials['R7 Graphite details'];new=[];doors=[];shelves=[]
def link(o,n,m):
 o.name='R15_'+n
 for c in list(o.users_collection):c.objects.unlink(o)
 group.objects.link(o);o.data.materials.append(m);o['level']=1;o['design_status']='PROPOSED_INTERIOR';new.append(o);return o
def box(n,c,size,m=white):
 bpy.ops.mesh.primitive_cube_add(size=1,location=c);o=link(bpy.context.object,n,m);o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);md=o.modifiers.new('Soft cabinet edges','BEVEL');md.width=min(.002,min(size)/4);md.segments=3;return o
# Front points west, X10.04. 900 wide,350 deep. Window ends Y6.10.
for y in [6.199,7.081]:box('Hood_Cabinet_Side_'+str(y),(10.215,y,2.3175),(.35,.018,1.115))
box('Hood_Cabinet_Top',(10.215,6.64,2.866),(.35,.864,.018))
# Lower appliance housing: visible only from underneath, no original chimney.
box('Integrated_Hood_Body',(10.215,6.49,1.841),(.31,.56,.15),metal)
box('Filter_Frame',(10.215,6.49,1.764),(.294,.544,.008),dark)
for i in range(16):box('Filter_Slat_'+str(i),(10.215,6.239+i*.033,1.759),(.264,.013,.005),metal)
for y in [6.233,6.747]:box('Hood_Underside_Light_'+str(y),(10.086,y,1.758),(.025,.025,.006),white)
for y in [6.43,6.47,6.51]:box('Hood_Underside_Button_'+str(y),(10.074,y,1.756),(.016,.018,.006),dark)
box('Hood_Concealing_Fascia',(10.049,6.64,1.839),(.018,.864,.158))
# Appliance deck is cut around the insert, with a useful closed cupboard above.
box('Bottom_Return_Long',(10.215,6.924,1.911),(.314,.296,.018))
box('Bottom_Return_Short',(10.215,6.209,1.911),(.314,.02,.018))
# Dedicated accessible service bay; shelving never intersects duct.
for y in [6.381,6.599]:box('Duct_Service_Bay_Side_'+str(y),(10.215,y,2.388),(.314,.018,.936))
box('Removable_Duct_Service_Cover',(10.073,6.49,2.388),(.018,.2,.936))
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.075,depth=.94,location=(10.285,6.49,2.39));link(bpy.context.object,'Concealed_150mm_Duct',metal)
for z in [2.015,2.425,2.775]:
 for side,ya,yb in [('Left',6.208,6.372),('Right',6.608,7.072)]:
  o=box('Storage_Shelf_'+side+'_'+str(z),(10.224,(ya+yb)/2,z),(.296,yb-ya,.018));shelves.append(o.name)
# Two flush fronts. Hardware opens away from the central meeting gap.
for i,(ya,yb) in enumerate([(6.192,6.634),(6.646,7.088)]):
 o=box('Hood_Door_'+str(i),(10.031,(ya+yb)/2,2.3945),(.018,yb-ya,.961));doors.append(o.name)
 y=yb-.045 if i==0 else ya+.045
 o=box('Hood_Door_Handle_'+str(i),(10.008,y,2.17),(.026,.018,.22),metal);doors.append(o.name)
# Socket remains on wall behind right-hand storage bay; shelves avoid it.
bpy.context.view_layer.update()
def bounds(os):
 v=[o.matrix_world@Vector(c) for o in os for c in o.bound_box];return [[min(c[i]for c in v),max(c[i]for c in v)]for i in range(3)]
row.update(objects=[o.name for o in new],bounds=bounds(new),role='integrated_hood_with_storage_cabinet',source_url='https://www.bosch-home.com/ae/en/specials/ventilation/built-in-solutions',license='original spatial design; generic appliance, not a specified product')
s['interior_revision']='LIBRARY 15.0 Concealed kitchen hood with side storage'
report={'revision':15,'removed_objects':removed,'new_objects':[o.name for o in new],'doors':doors,'shelves':shelves,'cabinet_m':[.9,.35,1.115],'bottom_z':1.76,'top_z':2.875,'storage_clear_m':{'left_width':.164,'right_width':.464,'depth':.296},'appliance_status':'Generic integrated insert; final appliance installation instructions and duct route require product selection','reference':'https://www.bosch-home.com/ae/en/specials/ventilation/built-in-solutions','socket':'E1_012 remains accessible behind right cupboard; shelves avoid its height'}
(R/'data/placements.json').write_text(json.dumps(p,indent=2),encoding='utf8');(R/'data/revision15_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
for name,pos,target in [('R15_CAMERA_HOOD',(8.50,5.45,2.12),(10.20,6.60,2.15))]:
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);bpy.data.collections['QA_CAMERAS'].objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=30
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in new:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision15_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION15_SAVED',len(new))
