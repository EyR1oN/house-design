from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'assets/dining_table_four_legs.blend'))
dg=bpy.context.evaluated_depsgraph_get();c=bpy.data.collections.new('Stable_dining_table_four_legs')
for o in list(bpy.context.scene.objects):
 if o.type!='MESH':continue
 me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg);me.transform(o.matrix_world);n=bpy.data.objects.new(o.name+'_PREPARED',me);c.objects.link(n)
bpy.data.libraries.write(str(R/'assets/prepared/dining_table_four_legs.blend'),{c},fake_user=True,compress=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
p=json.loads((R/'data/placements.json').read_text());a=json.loads((R/'data/revision5_selected_table.json').read_text(encoding='utf-8-sig'))
from mathutils import Vector,Matrix
import math,copy
def rec(l):return next(x for x in p if x['label']==l)
def obs(l):return [bpy.data.objects[n] for n in rec(l)['objects']]
def bounds(os):
 bpy.context.view_layer.update();vs=[o.matrix_world@Vector(v) for o in os for v in o.bound_box];return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
def move(l,d):
 for o in obs(l):o.matrix_world=Matrix.Translation(Vector(d))@o.matrix_world
old=rec('Dining_Table');container=bpy.data.objects[old['objects'][0]].users_collection[0]
for l in ['Dining_Table','Dining_Bench']:
 for o in obs(l):bpy.data.objects.remove(o,do_unlink=True)
p=[x for x in p if x['label']!='Dining_Bench']
with bpy.data.libraries.load(str(R/'assets/prepared/dining_table_four_legs.blend'),link=False) as (src,dst):dst.objects=src.objects
new=[o for o in dst.objects if o];old['objects']=[]
for o in new:container.objects.link(o);o.name='LIB_Dining_Table_'+o.name;old['objects'].append(o.name);o['source_object_name']=o.name
b=bounds(new);size=(1.56,.8,.775);center=(8.49,8.44,.3875)
H=Matrix.Translation(Vector(center))@Matrix.Diagonal((*[size[i]/(b[i][1]-b[i][0]) for i in range(3)],1))@Matrix.Translation(Vector([-sum(v)/2 for v in b]))
for o in new:o.matrix_world=H@o.matrix_world
old.update(source_url='https://www.blenderkit.com/asset-gallery-detail/'+a['assetBaseId']+'/',license=a['license'],scale=[size[i]/(b[i][1]-b[i][0]) for i in range(3)],asset_name=a['displayName'])
for l in ['Dining_Chair_7.99','Dining_Chair_8.99','Dining_Ceramics','Pendant_Dining1','Pendant_Dining2']:move(l,(0,-.25,0))
for k,x in enumerate([7.99,8.99],3):
 source=rec('Dining_Chair_'+str(x));r=copy.deepcopy(source);r['label']='Dining_Chair_'+str(k);r['objects']=[];p.append(r)
 c=bpy.data.collections.new('LIB_'+r['label']);bpy.data.collections['DESIGN_Living_Dining'].children.link(c)
 orig=obs(source['label']);b=bounds(orig);mid=Vector([sum(v)/2 for v in b]);target=Vector((x,9.13,mid.z));T=Matrix.Translation(target)@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation(-mid)
 for o in orig:n=o.copy();n.name='LIB_'+r['label']+'_Chair';c.objects.link(n);n.matrix_world=T@o.matrix_world;r['objects'].append(n.name)
for o in bpy.data.objects:
 if o.type=='LIGHT' and 'dining' in o.name.lower():o.location.y-=.25
for r in p:
 if r['label'].startswith(('Dining','Pendant_Dining')):r['bounds']=bounds(obs(r['label']))
assert len([r for r in p if r['label'].startswith('Dining_Chair')])==4
assert rec('Dining_Chair_7.99')['bounds'][1][0]-7.11>.35
assert all(i.packed_file for i in bpy.data.images if i.source=='FILE' and i.users>0)
(R/'data/placements.json').write_text(json.dumps(p,indent=2))
(R/'data/revision5_report.json').write_text(json.dumps({'revision':5,'table':a['displayName'],'table_size_m':size,'shift_toward_kitchen_m':.25,'chair_count':4,'kitchen_exit_gap_m':rec('Dining_Chair_7.99')['bounds'][1][0]-7.11},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
# Export only replacement furniture for merging into the existing browser model.
bpy.ops.object.select_all(action='DESELECT')
for r in p:
 if r['label'].startswith('Dining_Table') or r['label'] in ['Dining_Chair_3','Dining_Chair_4']:
  for o in obs(r['label']):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'exports/revision5_replacements.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False)
print('REVISION5_SAVED',flush=True)
