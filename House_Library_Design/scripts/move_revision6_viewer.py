from pathlib import Path
import json,base64,struct
R=Path(__file__).resolve().parents[1];path=R.parent/'House_Browser_Viewer/House_Viewer.html';h=path.read_text();start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:]);b=base64.b64decode(d['models']['1']);n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);rest=b[20+n:];changed=[]
for i in g['scenes'][0]['nodes']:
 node=g['nodes'][i];name=node.get('name','')
 if name.startswith(('LIB_Dining_Table','LIB_Dining_Chair','LIB_Dining_Ceramics','LIB_Pendant_Dining')):
  if 'matrix' in node:node['matrix'][14]+=.32
  else:node.setdefault('translation',[0,0,0])[2]+=.32
  changed.append(name)
assert len(changed)==10,(len(changed),changed)
g['scenes'][0].setdefault('extras',{})['interior_revision']='LIBRARY 6.0 Dining group 320mm closer to island, chair gap 122.5mm'
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b=struct.pack('<III',0x46546c67,2,20+len(j)+len(rest))+struct.pack('<II',len(j),0x4e4f534a)+j+rest
d['models']['1']=base64.b64encode(b).decode();(R.parent/'House_Browser_Viewer/House_Floor_1.glb').write_bytes(b);path.write_text(h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:]);print('BROWSER_MOVED',changed)
