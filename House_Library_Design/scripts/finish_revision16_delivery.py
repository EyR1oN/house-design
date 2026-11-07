from pathlib import Path
import json,re,base64,struct,zipfile,hashlib,math
R=Path(__file__).resolve().parents[1];changed=['Ground_Plan','Upper_Plan','Office_Reverse','Child_Storage','Kitchen_Hood','Office','Kitchen','Kitchen_Hood_Storage','Kitchen_Pantry_Open','Living_TV','Kitchen_Reverse','Living_Dining','Upper_Hall','Upper_Hall_Reverse','Ground_Hall_Reverse']
views=json.loads((R/'data/gallery_views.json').read_text(encoding='utf8'));oldviews=dict(views);renames={'Office_Reverse':'Кабінет · вхід і відкривання дверей'};views=[[n,renames.get(n,t)]for n,t in views]
for n in changed:assert(R/'previews'/f'{n}.png').exists()
(R/'data/gallery_views.json').write_text(json.dumps(views,ensure_ascii=False,indent=2),encoding='utf8')
p=R/'Design_Gallery.html';g=p.read_text(encoding='utf8');g=re.sub(r'дизайн, редакція \d+','дизайн, редакція 16',g)
for n,t in renames.items():g=g.replace(oldviews[n],t)
p.write_text(g,encoding='utf8')
text='''

## Редакція 16 — двері до стін, вільний прохід і колір кухні, 28 жовтня 2026

Підлогову рослину Plant_Office повністю прибрано. Двері кабінету перенавішено на протилежний (північний) одвірок: відчиняються всередину до стіни ванної. Двері дитячої перенавішено на східний одвірок: всередину до правої бічної стіни. Кожні показані відкритими на 90°. Так полотна не виходять у коридор і не перетинають його спільну зону. До крісла кабінету від відкритих дверей приблизно 496 мм; це місцевий зазор між предметами, не нормативна ширина проходу. Дверні прорізи й стіни не змінені. Ручки, петлі, замки та коробки перенесені разом із зміною навішування. Модель не є специфікацією реальної фурнітури.

Двері комори під сходами відчиняються назовні у вітальню на 90° замість усередину; петлі залишаються біля південного одвірка. 91 положення полотен і ручок кожних дверей перевірено відносно змодельованих меблів і сусідніх стін; контакт петель із місцем кріплення в одвірку допустимий. Вимикачі доступні. Пропоновану низьку розетку E2_084_SOCKET у дитячій зміщено по тій самій стіні з Y3.43 до Y2.95, щоб не залишати її за відкритими дверима; electrical_points.json синхронізовано.

У шафці витяжки та зовнішніх деталях кутової комори білий матеріал замінено точним існуючим Main_Slot.001 із шафки над холодильником (Base Color 0.54/0.50/0.43). Стільниці, техніка й дерев’яний поворотний стелаж залишені зі своїми матеріалами. Внутрішні світлі полиці цих шаф також узгоджені з новим кольором. В інших кімнатах спільний білий матеріал не змінювався.

У вебкопії прибрано агреговані старі вузли дверей, рослини та залишок старої відкритої витяжки LIB_Kitchen_Hood, який не збігався за назвою з частинами у Blender. Оновлені вузли другого поверху нормалізовані на -3.2 м; попередній туалетний столик залишається на підлозі. Збережено 20 рухомих вузлів кутової шафи й контролер. Оновлені 15 ракурсів/планів, окрема камера Office_Reverse тепер показує вхід із кімнати. Master і вебмоделі відповідають редакції 16. Резервна копія — House_Library_Revision15_Backup. refine_revision16.py та refine_revision16_socket.py вже застосовані; повторно не запускати. Перевірки: data/revision16_verification.json і data/revision16_browser_verification.json.
'''
for p in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 t=p.read_text(encoding='utf8').replace('завершена редакція 15','завершена редакція 16').replace('продовжуй з редакції 15','продовжуй з редакції 16');t=re.sub(r'дизайн, редакція \d+','дизайн, редакція 16',t)
 if '## Редакція 16'not in t:t+=text
 p.write_text(t,encoding='utf8')
path=R.parent/'House_Browser_Viewer/House_Viewer.html';h=path.read_text(encoding='utf8');start=h.index('window.HOUSE_DATA=')+len('window.HOUSE_DATA=');d,end=json.JSONDecoder().raw_decode(h[start:])
for photo,(n,t)in zip(d['photos'],views):
 photo['title']=t
 if n in changed:photo.update(image=base64.b64encode((R/'previews'/f'{n}.png').read_bytes()).decode(),mime='image/png')
path.write_text(h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:],encoding='utf8')
r=json.loads((R/'data/revision16_report.json').read_text());checks={};heights={}
for floor in ['1','2']:
 b=base64.b64decode(d['models'][floor]);assert b==(R.parent/'House_Browser_Viewer'/f'House_Floor_{floor}.glb').read_bytes();assert struct.unpack_from('<I',b,8)[0]==len(b);g=json.loads(b[20:20+struct.unpack_from('<I',b,12)[0]]);active=[g['nodes'][i]for i in g['scenes'][0]['nodes']];names=[n.get('name')for n in active];lookup={n.get('name'):n for n in active};assert len(names)==len(set(names));assert all(n in names for n in r['changed_objects'][floor]);assert all(n not in names for n in r['removed_objects']);assert 'LIB_Kitchen_Hood'not in names and 'LIB_Door_STORAGE'not in names and 'LIB_Plant_Office'not in names
 if floor=='2':assert all(n not in names for n in ['LIB_Door_L2_FRONT_BEDROOM_DOOR','LIB_Door_L2_SIDE_BEDROOM_DOOR'])
 if floor=='1':assert sum(n.get('extras',{}).get('pantry_role')=='pivot'for n in active)==20
 for v in g['bufferViews']:assert v.get('byteOffset',0)+v['byteLength']<=g['buffers'][0]['byteLength']
 for door in r['doors']:
  if str(door['level'])!=floor:continue
  name=next(n for n in door['moving']if 'Door.001'in n);node=lookup[name];q=node.get('rotation',[0,0,0,1]);x,y,z,w=q;t=node.get('translation',[0,0,0]);sc=node.get('scale',[1,1,1]);ry=[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)];ys=[]
  for prim in g['meshes'][node['mesh']]['primitives']:
   a=g['accessors'][prim['attributes']['POSITION']]
   for xx in [a['min'][0],a['max'][0]]:
    for yy in [a['min'][1],a['max'][1]]:
     for zz in [a['min'][2],a['max'][2]]:ys.append(t[1]+sum(ry[i]*sc[i]*[xx,yy,zz][i]for i in range(3)))
  heights[name]=min(ys);assert abs(min(ys)-.006)<.003,(name,min(ys))
 if floor=='1':
  reference=lookup['LIB_Kitchen_Fridge_Upper_Storage'];refmat=g['materials'][g['meshes'][reference['mesh']]['primitives'][0]['material']]['pbrMetallicRoughness']['baseColorFactor']
  for name in r['color_objects']:
   node=lookup[name]
   for prim in g['meshes'][node['mesh']]['primitives']:
    col=g['materials'][prim['material']]['pbrMetallicRoughness']['baseColorFactor'];assert all(abs(a-b)<.0001 for a,b in zip(col,refmat)),(name,col,refmat)
 checks[f'floor{floor}_active_nodes']=len(active)
assert len(d['photos'])==len(views)==36
for photo,(n,t)in zip(d['photos'],views):
 assert photo['title']==t
 if n in changed:assert base64.b64decode(photo['image'])==(R/'previews'/f'{n}.png').read_bytes()
with zipfile.ZipFile(R.parent/'House_Browser_Viewer.zip','w',zipfile.ZIP_DEFLATED)as z:
 for f in(R.parent/'House_Browser_Viewer').iterdir():
  if f.is_file():z.write(f,'House_Browser_Viewer/'+f.name)
with zipfile.ZipFile(R.parent/'House_Browser_Viewer.zip')as z:assert z.testzip()is None
checks.update(passed=True,revision=16,updated_photos=len(changed),embedded_models_match=True,zip_crc_verified=True,door_floor_heights=heights,exact_kitchen_finish_match=True,browser_ui='Not interactively tested; GLB scene geometry, materials, floor heights and photos checked')
(R/'data/revision16_browser_verification.json').write_text(json.dumps(checks,indent=2),encoding='utf8')
manifest=[{'path':str(f.relative_to(R)).replace('\\','/'),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}for f in R.rglob('*')if f.is_file()and f.name!='portable_manifest.json'and f.suffix!='.blend1'];(R/'data/portable_manifest.json').write_text(json.dumps(manifest,indent=2))
print('REVISION16_DELIVERY_VERIFIED',checks)
