from pathlib import Path
R=Path(__file__).resolve().parents[1]
source=(R/'scripts/update_revision5_viewer.py').read_text()
head='''from pathlib import Path
import json,struct,base64
R=Path(__file__).resolve().parents[1];path=R.parent/'House_Browser_Viewer/House_Viewer.html';h=path.read_text();start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:])
def read(b):
 n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);off=20+n;return g,b[off+8:off+8+struct.unpack_from('<I',b,off)[0]]
def write(g,b):
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b+=b'\\0'*((-len(b))%4);return struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b
g,b=read(base64.b64decode(d['models']['1']));v,c=read((R/'exports/revision7_replacements.glb').read_bytes());offset=len(b);b+=c
names=['LIB_Stair_Decorative_Panel','LIB_Kitchen_Crockery_6.185','LIB_Kitchen_Crockery_6.735','LIB_Laundry_Washer','LIB_Laundry_Dryer','LIB_Laundry_Towels','LIB_Laundry_Full_Upper_Storage','PART_DESIGN_Kitchen','PART_DESIGN_Laundry','PART_DESIGN_Living_Dining','PART_Electrical_L1']
remove={i for i,n in enumerate(g['nodes']) if n.get('name') in names}
assert len(remove)==len(names),(len(remove),len(names))
for scene in g['scenes']:scene['nodes']=[i for i in scene['nodes'] if i not in remove]
'''
body=source[source.index("keys=['bufferViews'"):source.index("g['scenes'][0].setdefault")]
tail='''g['scenes'][0].setdefault('extras',{})['interior_revision']='LIBRARY 7.0 TV continuous plaster and oak slats, larger island, stacked laundry pantry and proposed boiler'
for k in ['extensionsUsed','extensionsRequired']:
 if v.get(k):g[k]=list(set(g.get(k,[])+v[k]))
model=write(g,b);d['models']['1']=base64.b64encode(model).decode();(R.parent/'House_Browser_Viewer/House_Floor_1.glb').write_bytes(model)
path.write_text(h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:]);print('REVISION7_BROWSER_MERGED',len(model),len(v['nodes']))
'''
(R/'scripts/update_revision7_viewer.py').write_text(head+body+tail)
