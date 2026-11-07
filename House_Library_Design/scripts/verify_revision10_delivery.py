from pathlib import Path
import json,base64,struct,zipfile
R=Path(__file__).resolve().parents[1];h=(R.parent/'House_Browser_Viewer/House_Viewer.html').read_text(encoding='utf8');start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:]);views=json.loads((R/'data/gallery_views.json').read_text(encoding='utf8'));assert [x['title'] for x in d['photos']]==[title for name,title in views]
changed=['Ground_Plan', 'Laundry', 'Laundry_Reverse']
for photo,(name,title) in zip(d['photos'],views):
 if name in changed:assert base64.b64decode(photo['image'])==(R/'previews'/f'{name}.png').read_bytes()
for floor in ['1','2']:
 b=base64.b64decode(d['models'][floor]);assert struct.unpack_from('<I',b,8)[0]==len(b);assert b==(R.parent/'House_Browser_Viewer'/f'House_Floor_{floor}.glb').read_bytes()
with zipfile.ZipFile(R.parent/'House_Browser_Viewer.zip') as z:assert z.testzip() is None
(R/'data/revision10_browser_verification.json').write_text(json.dumps({'passed':True,'updated_renders':len(changed),'total_renders':33,'utf8_titles_verified':True,'embedded_models_match_glb':True,'zip_crc_verified':True,'interactive_browser_check':'Not performed; local file tab unavailable through browser automation'},indent=2),encoding='utf8');print('REVISION10_DELIVERY_VERIFIED')
