from pathlib import Path
import json,base64,struct,zipfile
R=Path(__file__).resolve().parents[1];h=(R.parent/'House_Browser_Viewer/House_Viewer.html').read_text(encoding='utf8');start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:]);views=json.loads((R/'data/gallery_views.json').read_text(encoding='utf8'));assert [x['title'] for x in d['photos']]==[title for name,title in views]
bb=base64.b64decode(d['models']['1']);nn=struct.unpack_from('<I',bb,12)[0];gg=json.loads(bb[20:20+nn]);active=[gg['nodes'][i] for i in gg['scenes'][0]['nodes']];names=[x.get('name') for x in active]
assert len(names)==len(set(names));assert not any(n.startswith(('R13_Carrier','R13_Food','R13_Tray')) for n in names);assert sum(x.get('extras',{}).get('pantry_role')=='pivot' for x in active)==20
assert h.count("button.id='pantry-toggle'")==1
assert json.loads((R/'data/revision14_controller_verification.json').read_text(encoding='utf8'))['passed']
changed=['Ground_Plan','Kitchen','Kitchen_Reverse','Living_Dining','Kitchen_Pantry_Open']
for photo,(name,title) in zip(d['photos'],views):
 if name in changed:assert base64.b64decode(photo['image'])==(R/'previews'/f'{name}.png').read_bytes()
for floor in ['1','2']:
 b=base64.b64decode(d['models'][floor]);assert struct.unpack_from('<I',b,8)[0]==len(b);assert b==(R.parent/'House_Browser_Viewer'/f'House_Floor_{floor}.glb').read_bytes()
with zipfile.ZipFile(R.parent/'House_Browser_Viewer.zip') as z:assert z.testzip() is None
(R/'data/revision14_browser_verification.json').write_text(json.dumps({'passed':True,'updated_renders':len(changed),'total_renders':34,'utf8_titles_verified':True,'embedded_models_match_glb':True,'zip_crc_verified':True,'interactive_browser_check':'Not performed; local file tab unavailable through browser automation'},indent=2),encoding='utf8');print('REVISION14_DELIVERY_VERIFIED')
