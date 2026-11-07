from pathlib import Path
import json,base64,struct
R=Path(__file__).resolve().parents[1]
def fix(b):
 n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);off=20+n;binary=b[off+8:off+8+struct.unpack_from('<I',b,off)[0]];count=0
 for m in g.get('materials',[]):
  if m.get('name')=='R14 Warm walnut reference':m.setdefault('pbrMetallicRoughness',{})['baseColorFactor']=[.25,.14,.08,1];count+=1
 assert count>0
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
 return struct.pack('<III',0x46546c67,2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
path=R.parent/'House_Browser_Viewer/House_Viewer.html';h=path.read_text(encoding='utf8');start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:]);b=fix(base64.b64decode(d['models']['1']));d['models']['1']=base64.b64encode(b).decode();(R.parent/'House_Browser_Viewer/House_Floor_1.glb').write_bytes(b);path.write_text(h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:],encoding='utf8');p=R/'exports/revision14_replacements.glb';p.write_bytes(fix(p.read_bytes()));print('WALNUT_BROWSER_COLOUR_FIXED')
