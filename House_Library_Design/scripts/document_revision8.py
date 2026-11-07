from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
text='''

## Редакція 8 — без рейок за телевізором, більше комори

- Усі десять дубових рейок за телевізором прибрано. Залишилася суцільна стіна з оздобленням у тон існуючої сходової стіни. Острівець, обідня група й техніка пральні не змінені.
- На північній стіні пральні додано високу шафу приблизно 960 × 400 × 2620 мм (ручки виступають додатково). Нижній великий вентильований висувний відсік для мішка картоплі: корисний простір моделі 420 × 330 × 630 мм, геометричний об’єм близько 87 л. Це не гарантована маса завантаження чи специфікація несучої конструкції. Поруч два окремі вентильовані овочеві відсіки.
- У верхній частині п’ять рівнів полиць за двома закритими фасадами для закруток. У моделі розкладено 40 умовних банок, щоб перевірити розміщення; місткість залежить від реальних розмірів банок. Побутова хімія — у попередній верхній шафі над сушаркою, окремо від продуктів.
- Дверна дуга не перетинає нову шафу. Ширина вільної смуги біля неї 742 мм. Збережено розетки й 542 мм простору до фронту котла; газове й димохідне рішення залишаються незатвердженими пропозиціями редакції 7.
- Камеру Laundry_Reverse перенесено, бо її попереднє місце займала нова шафа. Для огляду внутрішнього наповнення додано окремий кадр Laundry_Storage: фасади й частина стіни приховані тільки під час фотопоказу; master збережений із закритими фасадами та повною архітектурою.
- Перевірки: data/revision8_verification.json, 15 перевірок пройшли. Попередня редакція — House_Library_Revision7_Backup. Скрипт refine_revision8.py вже застосовано один раз, повторно не запускати.
'''
for path in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 h=path.read_text(encoding='utf8')+text
 if path.name=='README.md':h=h.replace('дизайн, редакція 7','дизайн, редакція 8')
 else:h=h.replace('У моделі вже завершена редакція 7','У моделі вже завершена редакція 8').replace('продовжуй з редакції 7','продовжуй з редакції 8').replace('редагований master, редакція 7','редагований master, редакція 8')
 path.write_text(h,encoding='utf8')
views=json.loads((R/'data/gallery_views.json').read_text(encoding='utf8'));views.append(['Laundry_Storage','Комора · внутрішнє наповнення великої шафи']);(R/'data/gallery_views.json').write_text(json.dumps(views,ensure_ascii=False,indent=2),encoding='utf8')
path=R/'Design_Gallery.html';h=path.read_text(encoding='utf8').replace('дизайн, редакція 7','дизайн, редакція 8');h=h.replace('</main>','<section id="Laundry_Storage"><h2>Комора · внутрішнє наповнення великої шафи</h2><p>Фасади приховані лише для огляду полиць і нижніх відсіків.</p><a href="previews/Laundry_Storage.png"><img loading="lazy" src="previews/Laundry_Storage.png" alt="Комора · внутрішнє наповнення"></a></section></main>');path.write_text(h,encoding='utf8')
h=(R/'scripts/finish_revision7_viewer.py').read_text(encoding='utf8');h=h.replace("for photo,(name,title) in zip", "d['photos'].append({'title':'Комора · внутрішнє наповнення великої шафи','image':''})\nfor photo,(name,title) in zip");h=h.replace("'Ground_Hall_Reverse']","'Ground_Hall_Reverse','Laundry_Storage']");h=h.replace("assert len(d['photos'])==32","assert len(d['photos'])==33;assert not any(n.startswith('R7_TV_Oak_Slat_') for n in active);assert 'R8_Potato_Sack' in active");h=h.replace('32 photos','33 photos');(R/'scripts/finish_revision8_viewer.py').write_text(h,encoding='utf8')
print('REVISION8_DOCUMENTED')
