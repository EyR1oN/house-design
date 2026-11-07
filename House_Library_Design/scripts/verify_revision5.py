from pathlib import Path
import bpy,json,hashlib
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene;s['interior_revision']='LIBRARY 5.0 Four-legged dining table and four chairs'
p=json.loads((R/'data/placements.json').read_text());checks=[]
def check(n,v):checks.append({'check':n,'passed':bool(v)});assert v,n
check('Four dining chairs',len([r for r in p if r['label'].startswith('Dining_Chair')])==4)
check('Bench removed',not any(o.name.startswith('LIB_Dining_Bench') for o in bpy.data.objects))
check('Old pedestal table removed',not any(o.name.startswith(('LIB_Dining_Table_Table Stand','LIB_Dining_Table_Fluted','LIB_Dining_Table_Under')) for o in bpy.data.objects))
check('All placement objects present',all(n in bpy.data.objects for r in p for n in r['objects']))
check('Textures packed',all(i.packed_file for i in bpy.data.images if i.source=='FILE' and i.users>0))
# Four separated foot clusters below tabletop in the original library leg mesh.
legs=next(o for o in bpy.data.objects if o.name.startswith('LIB_Dining_Table_Leg'))
pts=[legs.matrix_world@v.co for v in legs.data.vertices];low=[v for v in pts if v.z<.1];mid=(8.49,8.44)
check('Four leg corners reach floor',all(any((v.x-mid[0])*sx>0 and (v.y-mid[1])*sy>0 for v in low) for sx in [-1,1] for sy in [-1,1]))
# Confirm changes are limited to requested furnishings and lamps.
old=json.loads((R.parent/'House_Library_Revision4_Backup/data/placements.json').read_text());cur={r['label']:r for r in p}
check('Other placement bounds unchanged',all(cur[r['label']]['bounds']==r['bounds'] for r in old if not r['label'].startswith(('Dining','Pendant_Dining'))))
original={o.name:([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')}
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(R.parent/'House_Library_Revision4_Backup/House_Library_Design.blend'))
check('Architecture unchanged',all(original[o.name]==([tuple(v.co) for v in o.data.vertices],len(o.data.polygons)) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('R_')))
(R/'data/revision5_verification.json').write_text(json.dumps({'passed':True,'checks':checks},indent=2))
bpy.ops.wm.open_mainfile(filepath=str(R/'Ready_Furniture_Library.blend'))
with bpy.data.libraries.load(str(R/'assets/prepared/dining_table_four_legs.blend'),link=False) as (src,dst):dst.collections=src.collections
for c in dst.collections:
 if c:c.name='Arlos Dining Table - Four Legs';bpy.context.scene.collection.children.link(c);c.asset_mark();c.asset_data.description='BlenderKit Arlos Dining Table; Duy Ngo; royalty_free; four legs'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Ready_Furniture_Library.blend'),compress=True)
print('REVISION5_VERIFIED',len(checks))
