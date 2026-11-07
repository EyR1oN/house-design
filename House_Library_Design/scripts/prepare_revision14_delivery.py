from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'scripts/update_revision13_viewer.py').read_text(encoding='utf8').replace('revision13','revision14').replace('REVISION13','REVISION14').replace('LIBRARY 13.0 Tall corner pantry with two-stage pull-out','LIBRARY 14.0 Oak pivot shelf door and rounded white corner shelves')
(R/'scripts/update_revision14_viewer.py').write_text(s,encoding='utf8')
s=(R/'scripts/finish_revision13_viewer.py').read_text(encoding='utf8').replace("'R13_Pantry_Pull_Front_Lower' in active","'R14_Pivot_Oak_Back' in active").replace("controls=(R/'scripts/pantry_viewer_controls.js').read_text(encoding='utf8')","old_controls=(R/'scripts/pantry_viewer_controls.js').read_text(encoding='utf8');h=h.replace('<script>'+old_controls+'</script>','')\ncontrols=(R/'scripts/pantry_pivot_controls.js').read_text(encoding='utf8')")
(R/'scripts/finish_revision14_viewer.py').write_text(s,encoding='utf8')
s=(R/'scripts/verify_revision13_delivery.py').read_text(encoding='utf8').replace('revision13','revision14').replace('REVISION13','REVISION14')
(R/'scripts/verify_revision14_delivery.py').write_text(s,encoding='utf8')
text='''

## Редакція 14 — шафа за точним скріншотом користувача

Попередній висувний варіант 13 замінено: тепер двері — це неглибокий дерев’яний стелаж, який трохи виходить уперед на 220 мм і повертається на 90° праворуч. Сім дерев’яних полиць утворюють шість відділень; внутрішня глибина блоку близько 180 мм, низькі дерев’яні бортики. Зовні білий фасад. За поворотним блоком сім білих полиць із заокругленим контуром, що використовують кут і мають виріз під дерев’яний блок. Висувні кошики, контейнери та старі напрямні прибрані. Відтворено вигляд і принцип зі скріншота codex-clipboard-7b4c8832-192d-4d51-8240-e93d8690b74e.png.

91 положення повороту перевірено точними повернутими контурами відносно тумб, техніки, каменю та острівця. Шафа не закриває підвіконня. Механізм залишається ескізом поворотно-висувної фурнітури: виробник меблів має підібрати та підтвердити вузли й навантаження. Вебкнопка тепер показує саме цей рух, не старе висування кошиків. Master закритий, відкритий ракурс Kitchen_Pantry_Open. Попередня редакція — House_Library_Revision13_Backup; refine_revision14.py вже застосовано. Перевірки: revision14_verification.json, revision14_browser_verification.json.
'''
for path in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 s=path.read_text(encoding='utf8').replace('дизайн, редакція 13','дизайн, редакція 14').replace('завершена редакція 13','завершена редакція 14').replace('продовжуй з редакції 13','продовжуй з редакції 14')
 if '## Редакція 14' not in s:s+=text
 path.write_text(s,encoding='utf8')
g=R/'Design_Gallery.html';s=g.read_text(encoding='utf8').replace('Передня секція висунута, полиці з глибини кута під’їхали до отвору.','Дерев’яна секція повернута назовні; за нею видно округлі білі полиці.');g.write_text(s,encoding='utf8')
print('REVISION14_DELIVERY_PREPARED')
