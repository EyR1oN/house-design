from pathlib import Path
import json,struct,base64,shutil
R=Path(__file__).resolve().parents[1];path=R.parent/'House_Browser_Viewer/House_Viewer.html';h=path.read_text(encoding='utf8');start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:])
b=base64.b64decode(d['models']['2']);n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);off=20+n;binary=b[off+8:off+8+struct.unpack_from('<I',b,off)[0]]
v=(R/'exports/revision12_replacements.glb').read_bytes();nn=struct.unpack_from('<I',v,12)[0];vg=json.loads(v[20:20+nn]);names={o.get('name') for o in vg['nodes']};active=g['scenes'][g.get('scene',0)]['nodes'];selected=[g['nodes'][i] for i in active if g['nodes'][i].get('name') in names]
assert len(selected)==len(names)==55
assert next(o for o in selected if o['name']=='R12_Vanity_Plinth_0')['translation'][1]>3,'Height fix already applied'
backup=R.parent/'House_Library_Revision12_Browser_Backup';backup.mkdir(exist_ok=False);shutil.copy2(path,backup/path.name);shutil.copy2(R.parent/'House_Browser_Viewer/House_Floor_2.glb',backup/'House_Floor_2.glb')
old_floor1=d['models']['1']
for o in selected:
 t=o.setdefault('translation',[0,0,0]);t[1]-=3.2;o.setdefault('extras',{})['viewer_height_normalized']=True
g['scenes'][0].setdefault('extras',{})['interior_revision']='LIBRARY 12.1 Bedroom vanity viewer floor height corrected'
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);model=struct.pack('<III',0x46546c67,2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
checks=[]
for o in selected:
 if o['name'].startswith('R12_Vanity_Plinth'):
  min_y=min(g['accessors'][p['attributes']['POSITION']]['min'][1] for p in g['meshes'][o['mesh']]['primitives'])+o['translation'][1];assert abs(min_y)<.002;checks.append({'object':o['name'],'floor_gap_m':min_y})
assert abs(next(o for o in selected if o['name']=='R12_Round_Mirror_Glass')['translation'][1]-1.48)<.001
d['models']['2']=base64.b64encode(model).decode();assert d['models']['1']==old_floor1
(R.parent/'House_Browser_Viewer/House_Floor_2.glb').write_bytes(model);path.write_text(h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:],encoding='utf8')
(R/'data/revision12_height_fix.json').write_text(json.dumps({'passed':True,'viewer_objects_corrected':len(selected),'offset_m':-3.2,'ground_contacts':checks,'blender_model_changed':False,'floor1_changed':False},indent=2),encoding='utf8')
text='\n\n### Виправлення 12.1 — висота меблів у вебпереглядачі\n\nБібліотечний GLB другого поверху має підлогу на Y=0, тоді як Blender master має її на Z=3.2 м. Під час додавання нових об’єктів редакції 12 бракувало нормалізації висоти. У вебмоделі всі 55 доданих об’єктів столика, дзеркала й крісла зміщено на -3.2 м. Обидва цоколі перевірені на контакт із підлогою (похибка менше 2 мм). Blender і рендери вже мали правильну висоту, тому їх не змінювали. Для наступних правок другого поверху нормалізувати висоту кореневих вузлів експортованого GLB на -3.2 м перед злиттям. Скрипт fix_revision12_viewer_height.py вже застосований, повторно не запускати.\n'
for p in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:p.write_text(p.read_text(encoding='utf8')+text,encoding='utf8')
print('VIEWER_HEIGHT_FIXED',len(selected),checks)
