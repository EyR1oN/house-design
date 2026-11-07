from pathlib import Path
import json,re,base64,struct,zipfile,hashlib
R=Path(__file__).resolve().parents[1]
changed=['Ground_Plan','Kitchen','Kitchen_Reverse','Living_Dining','Kitchen_Hood','Kitchen_Hood_Storage']
views=json.loads((R/'data/gallery_views.json').read_text(encoding='utf8'))
for pair in [['Kitchen_Hood','Кухня · прихована витяжка'],['Kitchen_Hood_Storage','Кухня · полиці біля повітроводу']]:
 if pair[0] not in dict(views):views.append(pair)
for name in changed:assert (R/'previews'/f'{name}.png').exists(),name
(R/'data/gallery_views.json').write_text(json.dumps(views,ensure_ascii=False,indent=2),encoding='utf8')
p=R/'Design_Gallery.html';g=p.read_text(encoding='utf8');g=re.sub(r'дизайн, редакція \d+','дизайн, редакція 15',g)
for name,title in views[-2:]:
 if f'id="{name}"' not in g:g=g.replace('</nav>',f'<a href="#{name}">{title}</a></nav>').replace('</main>',f'<section id="{name}"><h2>{title}</h2><p>Вбудована витяжка з доступом знизу; зберігання відокремлене від сервісного каналу. На фото полиць фасади тимчасово приховані.</p><img src="previews/{name}.png" alt="{title}"></section></main>')
p.write_text(g,encoding='utf8')
text='''

## Редакція 15 — витяжка в шафці, 28 жовтня 2026

Відкриту бібліотечну витяжку й металевий димохід замінено узагальненим вбудованим блоком знизу шафки. Шафка 900 × 350 × 1115 мм, низ на 1760 мм, верх 2875 мм. Два фасади в тон кухні; шість полиць у двох відділеннях по боках від окремого центрального сервісного каналу. Корисна ширина відділень близько 164 та 464 мм, глибина полиць 296 мм. Повітровід 150 мм показаний лише в межах шафки, його фактична траса не спроєктована. Розетка за правим фасадом доступна, полиці не проходять крізь неї. Фільтр та кнопки доступні знизу. Знімна центральна накладка забезпечує доступ до повітроводу.

Для дверцят потрібен обмежувач до 85°, щоб виступаюча ручка не зачіпала перегородку; 91 положення перевірене для кожного полотна. Це ескіз меблів під майбутню вбудовану витяжку, не рішення для закривання старої камінної витяжки. Конкретний прилад, монтаж, допустимі зазори, вентиляційний канал і навантаження підбирати за інструкцією виробника. Принцип зберігання біля вбудованої витяжки: https://www.bosch-home.com/ae/en/specials/ventilation/built-in-solutions .

Планування кухні, острів, стіл, кутова поворотна комора й усі інші кімнати збережені. Master закритий; окремі фото Kitchen_Hood і Kitchen_Hood_Storage (на другому фасади й сервісна накладка приховані лише під час рендера). Браузерна модель й фото синхронізовані. Резервна копія редакції 14 — House_Library_Revision14_Backup. refine_revision15.py вже застосовано, повторно не запускати. Перевірки: data/revision15_verification.json та data/revision15_browser_verification.json.
'''
for p in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 t=p.read_text(encoding='utf8').replace('завершена редакція 14','завершена редакція 15').replace('продовжуй з редакції 14','продовжуй з редакції 15');t=re.sub(r'дизайн, редакція \d+','дизайн, редакція 15',t)
 if '## Редакція 15' not in t:t+=text
 p.write_text(t,encoding='utf8')
path=R.parent/'House_Browser_Viewer/House_Viewer.html';h=path.read_text(encoding='utf8');start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:])
for name,title in views:
 if name in changed:
  photo=next((q for q in d['photos'] if q['title']==title),None)
  if photo is None:photo={'title':title};d['photos'].append(photo)
  photo.update(image=base64.b64encode((R/'previews'/f'{name}.png').read_bytes()).decode(),mime='image/png')
h=h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:];path.write_text(h,encoding='utf8')
r=json.loads((R/'data/revision15_report.json').read_text());b=base64.b64decode(d['models']['1']);n=struct.unpack_from('<I',b,12)[0];gl=json.loads(b[20:20+n]);active=[gl['nodes'][i]for i in gl['scenes'][0]['nodes']];names=[o.get('name')for o in active]
assert len(names)==len(set(names))
assert all(n not in names for n in r['removed_objects'])
assert all(n in names for n in r['new_objects'])
assert sum(o.get('extras',{}).get('pantry_role')=='pivot'for o in active)==20
assert len(d['photos'])==len(views)==36
assert [q['title']for q in d['photos']]==[title for name,title in views]
for name,title in views:
 if name in changed:assert base64.b64decode(next(q['image']for q in d['photos']if q['title']==title))==(R/'previews'/f'{name}.png').read_bytes()
for floor in ['1','2']:
 data=base64.b64decode(d['models'][floor]);assert struct.unpack_from('<I',data,8)[0]==len(data);assert data==(R.parent/'House_Browser_Viewer'/f'House_Floor_{floor}.glb').read_bytes()
assert (R.parent/'House_Browser_Viewer/House_Floor_2.glb').read_bytes()==(R.parent/'House_Library_Revision14_Backup/House_Floor_2.glb').read_bytes()
for v in gl['bufferViews']:assert v.get('byteOffset',0)+v['byteLength']<=gl['buffers'][0]['byteLength']
for m in gl['meshes']:
 for p in m['primitives']:
  assert all(0<=i<len(gl['accessors'])for i in p['attributes'].values())
  if 'material'in p:assert p['material']<len(gl['materials'])
with zipfile.ZipFile(R.parent/'House_Browser_Viewer.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in (R.parent/'House_Browser_Viewer').iterdir():
  if f.is_file():z.write(f,'House_Browser_Viewer/'+f.name)
with zipfile.ZipFile(R.parent/'House_Browser_Viewer.zip')as z:assert z.testzip()is None
(R/'data/revision15_browser_verification.json').write_text(json.dumps({'passed':True,'photos':36,'replaced_hood_nodes':len(r['removed_objects']),'new_nodes':len(r['new_objects']),'embedded_models_match':True,'upper_floor_unchanged':True,'zip_crc_verified':True,'pantry_motion_nodes_preserved':20,'browser_ui':'Not interactively tested; GLB active scene and photos verified'},indent=2),encoding='utf8')
manifest=[{'path':str(f.relative_to(R)).replace('\\','/'),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in R.rglob('*') if f.is_file()and f.name!='portable_manifest.json'and f.suffix!='.blend1'];(R/'data/portable_manifest.json').write_text(json.dumps(manifest,indent=2))
print('REVISION15_DELIVERY_VERIFIED 36 photos, GLB synchronized, upper floor unchanged, zip valid')
