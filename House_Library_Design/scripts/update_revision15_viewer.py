from pathlib import Path
import json,struct,base64
R=Path(__file__).resolve().parents[1];path=R.parent/'House_Browser_Viewer/House_Viewer.html';h=path.read_text();start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:])
def read(b):
 n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);off=20+n;return g,b[off+8:off+8+struct.unpack_from('<I',b,off)[0]]
def write(g,b):
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\0'*((-len(b))%4);return struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b
g,b=read(base64.b64decode(d['models']['1']));v,c=read((R/'exports/revision15_replacements.glb').read_bytes());offset=len(b);b+=c
names=json.loads((R/'data/revision15_report.json').read_text())['removed_objects']+[n.get('name') for n in v['nodes']]
remove={i for i,n in enumerate(g['nodes']) if n.get('name') in names}
assert remove
for scene in g['scenes']:scene['nodes']=[i for i in scene['nodes'] if i not in remove]
keys=['bufferViews','accessors','images','samplers','textures','materials','meshes','nodes'];off={k:len(g.get(k,[])) for k in keys}
for x in v.get('bufferViews',[]):x['buffer']=0;x['byteOffset']=x.get('byteOffset',0)+offset
for x in v.get('accessors',[]):
 if 'bufferView' in x:x['bufferView']+=off['bufferViews']
for x in v.get('images',[]):
 if 'bufferView' in x:x['bufferView']+=off['bufferViews']
for x in v.get('textures',[]):
 if 'source' in x:x['source']+=off['images']
 if 'sampler' in x:x['sampler']+=off['samplers']
def textures(x):
 if isinstance(x,dict):
  for k,z in x.items():
   if k.endswith('Texture') and isinstance(z,dict) and 'index' in z:z['index']+=off['textures']
   else:textures(z)
 elif isinstance(x,list):
  for z in x:textures(z)
for x in v.get('materials',[]):textures(x)
for m in v.get('meshes',[]):
 for p in m['primitives']:
  p['attributes']={k:i+off['accessors'] for k,i in p['attributes'].items()}
  if 'indices' in p:p['indices']+=off['accessors']
  if 'material' in p:p['material']+=off['materials']
for n in v.get('nodes',[]):
 if 'mesh' in n:n['mesh']+=off['meshes']
 if 'children' in n:n['children']=[i+off['nodes'] for i in n['children']]
 n.setdefault('extras',{}).update(viewer_walls=False,floor=1)
for k in keys:g.setdefault(k,[]).extend(v.get(k,[]))
g['scenes'][0]['nodes'].extend(i+off['nodes'] for i in v['scenes'][v.get('scene',0)]['nodes']);g['buffers']=[{'byteLength':len(b)}]
g['scenes'][0].setdefault('extras',{})['interior_revision']='LIBRARY 15.0 Concealed hood with storage'
for k in ['extensionsUsed','extensionsRequired']:
 if v.get(k):g[k]=list(set(g.get(k,[])+v[k]))
model=write(g,b);d['models']['1']=base64.b64encode(model).decode();(R.parent/'House_Browser_Viewer/House_Floor_1.glb').write_bytes(model)
path.write_text(h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:]);print('REVISION15_BROWSER_MERGED',len(model),len(v['nodes']))
