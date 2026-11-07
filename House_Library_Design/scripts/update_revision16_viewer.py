from pathlib import Path
import json,base64,struct
R=Path(__file__).resolve().parents[1];path=R.parent/'House_Browser_Viewer/House_Viewer.html';h=path.read_text(encoding='utf8');start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:]);r=json.loads((R/'data/revision16_report.json').read_text())
def read(b):
 n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);off=20+n;return g,b[off+8:off+8+struct.unpack_from('<I',b,off)[0]]
def write(g,b):
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4);return struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b
for floor in ['1','2']:
 g,b=read(base64.b64decode(d['models'][floor]));v,c=read((R/'exports'/f'revision16_floor{floor}.glb').read_bytes());offset=len(b);b+=c
 names=set(r['changed_objects'][floor]+r['removed_objects']);names.update(['LIB_Door_STORAGE','LIB_Kitchen_Hood']if floor=='1'else['LIB_Door_L2_FRONT_BEDROOM_DOOR','LIB_Door_L2_SIDE_BEDROOM_DOOR','LIB_Plant_Office']);remove={i for i,n in enumerate(g['nodes'])if n.get('name')in names}
 assert remove
 for scene in g['scenes']:scene['nodes']=[i for i in scene['nodes']if i not in remove]
 for node in g['nodes']:
  if 'children'in node:node['children']=[i for i in node['children']if i not in remove]
 keys=['bufferViews','accessors','images','samplers','textures','materials','meshes','nodes'];off={k:len(g.get(k,[]))for k in keys}
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
    if k.endswith('Texture')and isinstance(z,dict)and'index'in z:z['index']+=off['textures']
    else:textures(z)
  elif isinstance(x,list):
   for z in x:textures(z)
 for x in v.get('materials',[]):
  textures(x)
  if x.get('name')=='R14 Warm walnut reference':x.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=[.25,.14,.08,1]
 for m in v.get('meshes',[]):
  for p in m['primitives']:
   p['attributes']={k:i+off['accessors']for k,i in p['attributes'].items()}
   if 'indices'in p:p['indices']+=off['accessors']
   if 'material'in p:p['material']+=off['materials']
 roots=v['scenes'][v.get('scene',0)]['nodes']
 for i,n in enumerate(v.get('nodes',[])):
  if floor=='2'and i in roots:
   if 'matrix'in n:n['matrix'][13]-=3.2
   else:n.setdefault('translation',[0,0,0])[1]-=3.2
  if 'mesh'in n:n['mesh']+=off['meshes']
  if 'children'in n:n['children']=[i+off['nodes']for i in n['children']]
  n.setdefault('extras',{}).update(viewer_walls=False,floor=int(floor),revision=16)
  for role,names_in_role in r['pantry_roles'].items():
   if n.get('name')in names_in_role:n['extras']['pantry_role']=role
 for k in keys:g.setdefault(k,[]).extend(v.get(k,[]))
 g['scenes'][0]['nodes'].extend(i+off['nodes']for i in roots);g['buffers']=[{'byteLength':len(b)}];g['scenes'][0].setdefault('extras',{})['interior_revision']='LIBRARY16 wall-side doors and matching kitchen'
 for k in ['extensionsUsed','extensionsRequired']:
  if v.get(k):g[k]=list(set(g.get(k,[])+v[k]))
 model=write(g,b);d['models'][floor]=base64.b64encode(model).decode();(R.parent/'House_Browser_Viewer'/f'House_Floor_{floor}.glb').write_bytes(model)
 print('FLOOR_UPDATED',floor,len(v['nodes']))
path.write_text(h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:],encoding='utf8')
