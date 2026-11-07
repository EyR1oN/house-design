from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'scripts/update_revision11_viewer.py').read_text(encoding='utf8').replace('revision11','revision12').replace('REVISION11','REVISION12').replace("['models']['1']","['models']['2']").replace('floor=1','floor=2').replace('House_Floor_1.glb','House_Floor_2.glb').replace('LIBRARY 11.0 Right boiler, left appliances, shallow sidewall pantry','LIBRARY 12.0 Round bedroom mirror and six vanity drawers')
(R/'scripts/update_revision12_viewer.py').write_text(s,encoding='utf8')
s=(R/'scripts/finish_revision11_viewer.py').read_text(encoding='utf8');a=s.index('changed=');b=s.index('\n',a);s=s[:a]+"changed=['Upper_Plan','Bedroom','Bedroom_Desk','Bedroom_TV']"+s[b:]
# Existing floor-one validations remain valid; add separate upper-floor checks.
a=s.index('for scene in g[\'scenes\']:')
s=s[:a]+"upper=base64.b64decode(d['models']['2']);nn=struct.unpack_from('<I',upper,12)[0];gg=json.loads(upper[20:20+nn]);aa=[gg['nodes'][i].get('name','') for i in gg['scenes'][0]['nodes']];assert 'LIB_Bedroom_Wall_Makeup_Mirror' not in aa;assert 'LIB_Bedroom_Makeup_Vanity' not in aa;assert 'R12_Round_Mirror_Glass' in aa;assert sum(n.startswith('R12_Vanity_Drawer_Front') for n in aa)==6;assert len(aa)==len(set(aa));assert upper==(R.parent/'House_Browser_Viewer/House_Floor_2.glb').read_bytes()\n"+s[a:]
(R/'scripts/finish_revision12_viewer.py').write_text(s,encoding='utf8')
s=(R/'scripts/verify_revision11_delivery.py').read_text(encoding='utf8').replace('revision11','revision12').replace('REVISION11','REVISION12');a=s.index('changed=');b=s.index('\n',a);s=s[:a]+"changed=['Upper_Plan','Bedroom','Bedroom_Desk','Bedroom_TV']"+s[b:]
(R/'scripts/verify_revision12_delivery.py').write_text(s,encoding='utf8')
text='''

## Редакція 12 — туалетний столик у спальні

Збережено мармурову стільницю та дерев’яний кант бібліотечного туалетного столика (1100 × 480 мм). Старі металеві ніжки й перемичку замінено двома компактними тумбами по 220 мм завширшки, з трьома шухлядами кожна. Фасади теплі світло-сірі, тонкі металеві ручки; внутрішні боковини й дно шухляд змодельовані. Посередині 580 мм місця для сидіння. Крісло відцентроване по столику, з боків близько 40 мм до тумб.

Замість витягнутого прямокутного дзеркала — справжнє кругле поліроване дзеркало діаметром близько 800 мм із тонкою металевою рамкою (зовнішній діаметр 814 мм). Інші кімнати й косметика на стільниці збережені. Резервна копія — House_Library_Revision11_Backup. Модель, фото спальні, план другого поверху й верхній браузерний GLB синхронізовані. refine_revision12.py вже застосований; повторно не запускати. Перевірки — data/revision12_verification.json та data/revision12_browser_verification.json.
'''
for path in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 s=path.read_text(encoding='utf8').replace('дизайн, редакція 11','дизайн, редакція 12').replace('завершена редакція 11','завершена редакція 12').replace('продовжуй з редакції 11','продовжуй з редакції 12')
 if '## Редакція 12' not in s:s+=text
 path.write_text(s,encoding='utf8')
