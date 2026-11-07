from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
s=(R/'scripts/update_revision11_viewer.py').read_text(encoding='utf8').replace('revision11','revision13').replace('REVISION11','REVISION13').replace('LIBRARY 11.0 Right boiler, left appliances, shallow sidewall pantry','LIBRARY 13.0 Tall corner pantry with two-stage pull-out')
needle="for n in v.get('nodes',[]):"
s=s.replace(needle,"motion=json.loads((R/'data/revision13_report.json').read_text())['motion_groups']\n"+needle)
s=s.replace("n.setdefault('extras',{}).update(viewer_walls=False,floor=1)","n.setdefault('extras',{}).update(viewer_walls=False,floor=1)\n for role,names_in_role in motion.items():\n  if n.get('name') in names_in_role:n['extras']['pantry_role']=role")
(R/'scripts/update_revision13_viewer.py').write_text(s,encoding='utf8')
views=json.loads((R/'data/gallery_views.json').read_text(encoding='utf8'));title='Кухня · відкрита кутова шафа'
if not any(r[0]=='Kitchen_Pantry_Open' for r in views):views.append(['Kitchen_Pantry_Open',title])
(R/'data/gallery_views.json').write_text(json.dumps(views,ensure_ascii=False,indent=2),encoding='utf8')
path=R/'Design_Gallery.html';h=path.read_text(encoding='utf8')
if 'id="Kitchen_Pantry_Open"' not in h:h=h.replace('</main>',f'<section id="Kitchen_Pantry_Open"><h2>{title}</h2><p>Передня секція висунута, полиці з глибини кута під’їхали до отвору. Просторовий ескіз механізму для подальшого підбору фурнітури.</p><a href="previews/Kitchen_Pantry_Open.png"><img loading="lazy" src="previews/Kitchen_Pantry_Open.png" alt="{title}"></a></section></main>')
path.write_text(h,encoding='utf8')
s=(R/'scripts/finish_revision12_viewer.py').read_text(encoding='utf8');a=s.index('changed=');b=s.index('\n',a);s=s[:a]+"changed=['Ground_Plan','Kitchen','Kitchen_Reverse','Living_Dining','Kitchen_Pantry_Open']"+s[b:]
s=s.replace("for photo,(name,title) in zip", "if len(d['photos'])==33:d['photos'].append({'title':'Кухня · відкрита кутова шафа','image':''})\nfor photo,(name,title) in zip",1).replace("len(d['photos'])==33","len(d['photos'])==34",1)
# Undo the replacement in the append guard only.
s=s.replace("if len(d['photos'])==34:d['photos'].append", "if len(d['photos'])==33:d['photos'].append").replace("assert len(d['photos'])==33","assert len(d['photos'])==34")
s=s.replace("for scene in g['scenes']:","assert 'LIB_Kitchen_Corner_Prep' not in active;assert 'LIB_Kitchen_Upper_Corner' not in active;assert 'R13_Pantry_Pull_Front_Lower' in active\nfor scene in g['scenes']:")
needle="h=h[:start]+json.dumps(d,separators=(',',':'))+h[start+end:];"
s=s.replace(needle,needle+"\ncontrols=(R/'scripts/pantry_viewer_controls.js').read_text(encoding='utf8')\nif 'id = \'pantry-toggle\'' not in h:h=h.replace('</body>','<script>'+controls+'</script></body>')\n")
(R/'scripts/finish_revision13_viewer.py').write_text(s,encoding='utf8')
s=(R/'scripts/verify_revision12_delivery.py').read_text(encoding='utf8').replace('revision12','revision13').replace('REVISION12','REVISION13').replace("'total_renders':33","'total_renders':34");a=s.index('changed=');b=s.index('\n',a);s=s[:a]+"changed=['Ground_Plan','Kitchen','Kitchen_Reverse','Living_Dining','Kitchen_Pantry_Open']"+s[b:]
(R/'scripts/verify_revision13_delivery.py').write_text(s,encoding='utf8')
text='''

## Редакція 13 — висока кутова шафа кухні

За двома зображеннями користувача місце для нарізання та верхню кутову шафу замінено високою коморою 1040 × 600 × 2875 мм. Корпус закінчується перед підвіконням (20 мм у моделі); залишок 60 мм до наступної тумби закритий кам’яною вставкою. Струмопровідна/монтажна частина лише ескізна. Дві колишні розетки переміщені у доступну верхню сервісну зону всередині шафи. Стару підсвітку кута прибрано. Дошки для нарізання перенесено на острівець.

Дві секції по сім полиць: передня висувається на 660 мм, тоді задня зміщується на 600 мм до отвору й на 140 мм уперед. Розділено рух напрямних і полиць; між відкритими полицями близько 160 мм. У моделі 56 умовних контейнерів. Перевірено 61 положення руху відносно духовки, холодильника, мийки, нижніх тумб, стільниці й острівця. Це просторовий ескіз індивідуального механізму, не копія серійного TANDEM і не підтвердження несучої здатності: висота й ширина нашого кутового отвору потребують окремого підбору фурнітури меблярем. Орієнтир принципу доступу: https://www.kesseboehmer.com/en/storage-solutions/kitchen/larder-units/tandem-family/tandem .

У вебпереглядач додано кнопку «Відкрити кутову шафу» з послідовним рухом, при закриванні рух відтворюється у зворотному порядку. Показ відкритої шафи — Kitchen_Pantry_Open. Master збережений у закритому стані. Резервна копія — House_Library_Revision12_Backup. Збережено виправлену висоту другого поверху 12.1. refine_revision13.py вже застосовано; повторно не запускати. Перевірки: data/revision13_verification.json і data/revision13_browser_verification.json.
'''
for path in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 s=path.read_text(encoding='utf8').replace('дизайн, редакція 12','дизайн, редакція 13').replace('завершена редакція 12','завершена редакція 13').replace('продовжуй з редакції 12','продовжуй з редакції 13')
 if '## Редакція 13' not in s:s+=text
 path.write_text(s,encoding='utf8')
print('REVISION13_DELIVERY_PREPARED')
