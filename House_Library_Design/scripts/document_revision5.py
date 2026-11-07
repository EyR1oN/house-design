from pathlib import Path
import json,hashlib,base64
R=Path(__file__).resolve().parents[1];a=json.loads((R/'data/revision5_selected_table.json').read_text(encoding='utf-8-sig'));f=R/'assets/dining_table_four_legs.blend';m=json.loads((R/'data/library_manifest.json').read_text());m.append({'role':'dining_table_four_legs','id':a['id'],'asset_base_id':a['assetBaseId'],'name':a['displayName'],'author':a['author'].get('fullName','Duy Ngo'),'license':a['license'],'source_url':'https://www.blenderkit.com/asset-gallery-detail/'+a['assetBaseId']+'/','file':'assets/dining_table_four_legs.blend','bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'status':'DOWNLOADED'});(R/'data/library_manifest.json').write_text(json.dumps(m,indent=2))
credit='\n- Arlos Dining Table — Duy Ngo; BlenderKit, royalty_free. https://www.blenderkit.com/asset-gallery-detail/'+a['assetBaseId']+'/ (редакція 5; стіл адаптовано до 1560 × 800 × 775 мм).\n'
for p in [R/'ASSET_CREDITS.md',R.parent/'House_Browser_Viewer/ASSET_CREDITS.md']:
 with p.open('a',encoding='utf-8') as w:w.write(credit)
text='\n## Редакція 5 — обідня зона, 4 жовтня 2026\n\nСтарий стіл із центральною опорою замінено на бібліотечний Arlos Dining Table на чотирьох ніжках, 1560 × 800 × 775 мм. Лавку прибрано; на її місці два стільці тієї самої бібліотечної моделі, разом чотири. Стіл, стільці, посуд і підвіси зміщені на 250 мм до кухні. Архітектуру й інші меблі збережено. Резервна копія попереднього master, даних, рендерів і HTML: House_Library_Revision4_Backup у корені пакета. Поточний master уже містить редакцію 5; скрипт refine_revision5.py не запускати повторно поверх нього.\n'
for p in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 with p.open('a',encoding='utf-8') as w:w.write(text)
