"""Merge revision 18 replacements without rebuilding historical room geometry."""
from pathlib import Path
import json,sys,copy,shutil
from open_stair_exit_viewer import read_glb,write_glb
ROOT=Path(__file__).resolve().parents[1]
report=json.loads((ROOT/'House_Library_Design/data/revision18_report.json').read_text())
for floor in (1,2):
 path=ROOT/f'House_Browser_Viewer/House_Floor_{floor}.glb'
 backup=ROOT/f'.local-preview/pre-revision18/House_Floor_{floor}.glb'
 if not backup.exists():shutil.copy2(path,backup)
 g,b=read_glb(backup.read_bytes());v,c=read_glb((ROOT/f'House_Library_Design/exports/revision18_floor{floor}.glb').read_bytes())
 names=set(report['moved_objects'])|set(report['stair_objects'])|{'PART_R_STAIRS','R3_Stair_Landing_Threshold',f'R18_Ceiling_L{floor}'}
 if floor==2:names.update(report.get('hall_replacement_objects',[]));names.add('PART_DESIGN_Upper_Hall')
 removed={i for i,n in enumerate(g['nodes']) if n.get('name') in names or n.get('name','').startswith(('LIB_Dining','LIB_Pendant_Dining')) and floor==1}
 for scene in g['scenes']:scene['nodes']=[i for i in scene['nodes'] if i not in removed]
 for n in g['nodes']:
  if 'children'in n:n['children']=[i for i in n['children'] if i not in removed]
 roots=v['scenes'][v.get('scene',0)]['nodes']
 stair_ids=[i for i,n in enumerate(v['nodes']) if n.get('name') in report['stair_objects']]
 v['nodes'].append({'name':'PART_R_STAIRS','children':stair_ids,'extras':{'level':floor}})
 roots[:]=[i for i in roots if i not in stair_ids]+[len(v['nodes'])-1]
 if floor==2 and report.get('hall_replacement_objects'):
  hall_ids=[i for i,n in enumerate(v['nodes']) if n.get('name') in report['hall_replacement_objects']]
  v['nodes'].append({'name':'PART_DESIGN_Upper_Hall','children':hall_ids})
  roots[:]=[i for i in roots if i not in hall_ids]+[len(v['nodes'])-1]
 keys=['bufferViews','accessors','images','samplers','textures','materials','meshes','nodes'];off={k:len(g.get(k,[])) for k in keys}
 offset=(len(b)+3)&~3;b+=b'\0'*(offset-len(b));b+=c
 for x in v.get('bufferViews',[]):x['buffer']=0;x['byteOffset']=x.get('byteOffset',0)+offset
 for x in v.get('accessors',[]):
  if 'bufferView'in x:x['bufferView']+=off['bufferViews']
 for x in v.get('images',[]):
  if 'bufferView'in x:x['bufferView']+=off['bufferViews']
 for x in v.get('textures',[]):
  if 'source'in x:x['source']+=off['images']
  if 'sampler'in x:x['sampler']+=off['samplers']
 def textures(x):
  if isinstance(x,dict):
   for k,z in x.items():
    if k.endswith('Texture') and isinstance(z,dict) and 'index'in z:z['index']+=off['textures']
    else:textures(z)
  elif isinstance(x,list):
   for z in x:textures(z)
 for x in v.get('materials',[]):textures(x)
 for m in v.get('meshes',[]):
  for p in m['primitives']:
   p['attributes']={k:i+off['accessors'] for k,i in p['attributes'].items()}
   if 'indices'in p:p['indices']+=off['accessors']
   if 'material'in p:p['material']+=off['materials']
 for i,n in enumerate(v['nodes']):
  if floor==2 and i in roots:
   if 'matrix'in n:n['matrix'][13]-=3.2
   else:n.setdefault('translation',[0,0,0])[1]-=3.2
  if 'mesh'in n:n['mesh']+=off['meshes']
  if 'children'in n:n['children']=[j+off['nodes'] for j in n['children']]
  n.setdefault('extras',{}).update(level=floor,revision=18)
 for k in keys:g.setdefault(k,[]).extend(v.get(k,[]))
 g['scenes'][0]['nodes'].extend(i+off['nodes'] for i in roots)
 g['scenes'][0].setdefault('extras',{})['interior_revision']='LIBRARY 18.0 ceilings and stair turn'
 for k in ['extensionsUsed','extensionsRequired']:
  if v.get(k):g[k]=sorted(set(g.get(k,[])+v[k]))
 path.write_bytes(write_glb(g,b));print('UPDATED',floor,'removed',len(removed),'new',len(v['nodes']))

template=ROOT/'House_Browser_Viewer/viewer_template.html'
s=template.read_text(encoding='utf8')
import re
s=re.sub(r'<button id="plan">.*?</button>','',s,count=1)
s=s.replace('Ke("plan").onclick=()=>{Ma="plan",Cs(Ke("rooms").value),Ke("plan").classList.add("active"),Ke("orbit").classList.remove("active")};','')
s=s.replace(',Ke("plan").classList.remove("active")','')
s=s.replace('Зрізати високі стіни','Зрізати стіни та стелі')
template.write_text(s,encoding='utf8')
