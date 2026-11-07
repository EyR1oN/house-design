from pathlib import Path
import json,base64,struct
R=Path(__file__).resolve().parents[1]
def data(path):
 h=path.read_text();start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,_=json.JSONDecoder().raw_decode(h[start:]);b=base64.b64decode(d['models']['1']);n=struct.unpack_from('<I',b,12)[0];return d,json.loads(b[20:20+n])
a,old=data(R.parent/'House_Library_Revision5_Backup/House_Viewer.html');b,new=data(R.parent/'House_Browser_Viewer/House_Viewer.html');assert a['models']['2']==b['models']['2'];count=0
for i,(x,y) in enumerate(zip(old['nodes'],new['nodes'])):
 if x!=y:
  count+=1;assert x['name'].startswith(('LIB_Dining_Table','LIB_Dining_Chair','LIB_Dining_Ceramics','LIB_Pendant_Dining'));field='matrix' if 'matrix' in x else 'translation';index=14 if field=='matrix' else 2;assert abs(y[field][index]-x.get(field,[0,0,0])[index]-.32)<1e-6
assert count==10
(R/'data/revision6_browser_verification.json').write_text(json.dumps({'passed':True,'moved_nodes':count,'unchanged_second_floor':True,'other_nodes_unchanged':True},indent=2));print('BROWSER_SHIFT_VERIFIED',count)
