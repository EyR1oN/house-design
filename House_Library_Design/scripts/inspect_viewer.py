from pathlib import Path
import json,struct,base64
R=Path(__file__).resolve().parents[1];h=(R.parent/'House_Browser_Viewer/House_Viewer.html').read_text();start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:]);print('PHOTO_SAMPLE',[(p.keys(),p.get('title')) for p in d['photos'][:3]])
b=base64.b64decode(d['models']['1']);n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);print('DINING_NODES',[(i,v) for i,v in enumerate(g['nodes']) if 'Dining' in v.get('name','')]);print('EXTENSIONS',g.get('extensionsUsed'));print('SCENES',g['scenes'])
