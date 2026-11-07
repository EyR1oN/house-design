from pathlib import Path
R=Path(__file__).resolve().parents[1]
for name in ['update_revision9_viewer.py','finish_revision9_viewer.py','verify_revision9_delivery.py']:
 s=(R/'scripts'/name).read_text(encoding='utf8').replace('revision9','revision10').replace('REVISION9','REVISION10').replace("'Laundry_Reverse', 'Laundry_Storage'","'Laundry_Reverse'").replace('LIBRARY 9.0 Clear centre and aligned end-wall laundry storage','LIBRARY 10.0 Boiler shifted toward entrance')
 (R/'scripts'/name.replace('revision9','revision10')).write_text(s,encoding='utf8')
text='''

## Редакція 10 — більше доступу до котла

Котел з усіма ескізними патрубками зміщено на 350 мм у бік входу вздовж північної стіни. Зазор від його боку до фасаду комори збільшено зі 164 до 514 мм. До змодельованої дверної дуги залишається 152 мм у плані; перед корпусом котла близько 834 мм. Пралка, сушарка й комора збережені. Розетки перенесено праворуч від котла, поза його корпусом і патрубками. Точка підключення перенесена разом із котлом; фактичні інженерні траси й монтажні зазори для конкретного котла залишаються непідтвердженими.

Оновлено модель, план поверху, два ракурси пральні, браузерний GLB і архів. Перевірки геометрії — data/revision10_verification.json; файлів переглядача — data/revision10_browser_verification.json. Попередня редакція — House_Library_Revision9_Backup. Скрипт refine_revision10.py вже застосовано, повторно не запускати.
'''
for path in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 s=path.read_text(encoding='utf8').replace('дизайн, редакція 9','дизайн, редакція 10').replace('завершена редакція 9','завершена редакція 10').replace('продовжуй з редакції 9','продовжуй з редакції 10')
 if '## Редакція 10' not in s:s+=text
 path.write_text(s,encoding='utf8')
