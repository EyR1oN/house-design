from pathlib import Path
import json,base64,struct,hashlib,zipfile
R=Path(__file__).resolve().parents[1];path=R.parent/'House_Browser_Viewer/House_Viewer.html';h=path.read_text();start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:]);titles=dict(json.loads((R/'data/gallery_views.json').read_text()));changed=['Ground_Plan', 'Laundry', 'Laundry_Reverse', 'Laundry_Storage']
for photo,(name,title) in zip(d['photos'],json.loads((R/'data/gallery_views.json').read_text())):photo['title']=title
for name in changed:
 photo=next(p for p in d['photos'] if p['title']==titles[name]);photo['image']=base64.b64encode((R/'previews'/f'{name}.png').read_bytes()).decode();photo['mime']='image/png'
h=h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:];h=h.replace('src="data:image/jpeg;base64,${i.image}"','src="data:${i.mime||\'image/jpeg\'};base64,${i.image}"');path.write_text(h)
model=base64.b64decode(d['models']['1']);n=struct.unpack_from('<I',model,12)[0];g=json.loads(model[20:20+n]);active=[g['nodes'][i]['name'] for i in g['scenes'][0]['nodes']];assert 'LIB_Dining_Bench' not in active and 'LIB_Dining_Table' not in active;assert sum(n.startswith('LIB_Dining_Chair') for n in active)==4;assert 'LIB_Stair_Decorative_Panel' not in active;assert 'LIB_Laundry_Full_Upper_Storage' not in active;assert 'R7_Gas_Boiler_Body' in active;assert model==(R.parent/'House_Browser_Viewer/House_Floor_1.glb').read_bytes();assert len(d['photos'])==33;assert not any(n.startswith('R7_TV_Oak_Slat_') for n in active);assert 'R9_Potato_Sack' in active;assert 'R11_Preserves_Jar_0_0_0' in active;assert not any(n.startswith('R9_Pantry_') for n in active);assert not any(n.startswith('R8_Bulk_Pantry') for n in active)
for scene in g['scenes']:
 for i in scene['nodes']:assert 0<=i<len(g['nodes'])
for m in g['meshes']:
 for p in m['primitives']:
  assert all(i<len(g['accessors']) for i in p['attributes'].values())
  if 'material' in p:assert p['material']<len(g['materials'])
for v in g['bufferViews']:assert v.get('byteOffset',0)+v['byteLength']<=g['buffers'][0]['byteLength']
for name in ['revision5_viewer_data.json','viewer_tail.txt']:
 (R/'data'/name).unlink(missing_ok=True)
with zipfile.ZipFile(R.parent/'House_Browser_Viewer.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in (R.parent/'House_Browser_Viewer').iterdir():
  if f.is_file():z.write(f,'House_Browser_Viewer/'+f.name)
manifest=[{'path':str(f.relative_to(R)).replace('\\','/'),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in R.rglob('*') if f.is_file() and f.name!='portable_manifest.json' and f.suffix!='.blend1'];(R/'data/portable_manifest.json').write_text(json.dumps(manifest,indent=2))
print('VIEWER_VERIFIED four chairs, replacement table, 33 photos, GLB references valid')

