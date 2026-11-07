from pathlib import Path
import json,base64,struct
R=Path(__file__).resolve().parents[1];h=(R.parent/'House_Browser_Viewer/House_Viewer.html').read_text();start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:]);b=base64.b64decode(d['models']['1']);n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);print([g['nodes'][i].get('name') for i in g['scenes'][0]['nodes']]);b=(R/'exports/revision7_replacements.glb').read_bytes();n=struct.unpack_from('<I',b,12)[0];v=json.loads(b[20:20+n]);print('NEW_NODE_COUNT',len(v['nodes']))
