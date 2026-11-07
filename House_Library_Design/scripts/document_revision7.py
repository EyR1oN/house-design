from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];verification=json.loads((R/'data/revision7_verification.json').read_text());verification['revision']=7;p=json.loads((R/'data/placements.json').read_text());verification['placements']=len(p);verification['ready_model_types']=len(set(x['role'] for x in p));(R/'data/verification.json').write_text(json.dumps(verification,indent=2))
text='''

## Редакція 7 — телевізійна стіна, острівець, пральня-комора

- Коричневу декоративну бібліотечну панель за телевізором видалено. Оздоблення продовжує штукатурку існуючої сходової стіни; біля сходового отвору десять вертикальних дубових рейок. Полотно стіни й обидва сходові проходи збережено.
- Острівець: корпус 1300 × 700 × 860 мм, стільниця 1335 × 735 мм. Розширення на 150 мм на схід до кухонної стільниці й на 200 мм на південь до холодильника. Північний край біля обідніх стільців і західний край не зміщені. Робочий прохід 1052,5 мм; консервативна дуга відкривання холодильника 0–110° не перетинає острівець, зазор від змодельованої дуги близько 492 мм. Це перевірка поточної моделі, не специфікація обраного холодильника.
- Пральня 1940 × 1200 мм: усе основне обладнання на східній стіні навпроти дверей, фасадами до входу. Пралка внизу, сушарка зверху, між ними 30-мм модель з’єднувального комплекту; реальний комплект обирати за сумісністю конкретних машин. Верхня закрита шафка, поруч три окремі вентильовані овочеві секції й невелика стільниця. Окремі секції для картоплі й цибулі; побутову хімію тримати у верхньому закритому відділенні. Температуру й вологість для фактичного зберігання продуктів перевіряти на місці.
- Над коморними секціями — узагальнена модель настінного газового котла 440 × 352 × 720 мм, із доступним фронтом. Газові й водяні патрубки та верхній приєднувальний патрубок показані лише як пропозиції. Модель котла не обрана для закупівлі; газова розводка, конденсат, вентиляція і димохід не спроєктовані й не підтверджені. Для просторового резерву використані сервісні габарити прикладу Vaillant ecoTEC plus; це не підтвердження відповідності місцевим вимогам: https://professional.vaillant.co.uk/downloads/product-manuals/ecotec-plus-1/ecotec-plus-combi-and-system-installation-instructions-2422739.pdf
- Розетки пралки та сушарки перенесені у доступну зону північної стіни, таблиця підключення пралки оновлена. Усі точки залишаються PROPOSED.
- Виправлено стару камеру пральні, яка стояла за південною стіною й давала чорний кадр; тепер камера розташована біля входу всередині кімнати.
- Перевірки: data/revision7_verification.json та data/verification.json, 16 перевірок пройшли. Попередня редакція збережена в House_Library_Revision6_Backup. Скрипт refine_revision7.py вже застосовано один раз; повторно не запускати поверх поточного master.
'''
for path in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 h=path.read_text();h+=text
 if path.name=='README.md':h=h.replace('# Будинок — бібліотечний дизайн, редакція 4','# Будинок — бібліотечний дизайн, редакція 7')
 else:h=h.replace('У моделі вже завершена редакція 4','У моделі вже завершена редакція 7').replace('продовжуй з редакції 4','продовжуй з редакції 7').replace('редагований master, редакція 4','редагований master, редакція 7')
 path.write_text(h)
path=R/'Design_Gallery.html';h=path.read_text().replace('дизайн, редакція 6','дизайн, редакція 7');path.write_text(h)
# Adapt finishing script for all views affected by this revision.
h=(R/'scripts/finish_revision5_viewer.py').read_text().replace("changed=['Ground_Plan','Living_Dining','Living','Living_TV','Kitchen','Kitchen_Reverse']","changed=['Ground_Plan','Living_TV','Laundry','Laundry_Reverse','Kitchen','Kitchen_Reverse','Living','Living_Dining','Stair_Entry','Ground_Hall_Reverse']");h=h.replace("assert sum(n.startswith('LIB_Dining_Chair') for n in active)==4;","assert sum(n.startswith('LIB_Dining_Chair') for n in active)==4;assert 'LIB_Stair_Decorative_Panel' not in active;assert 'LIB_Laundry_Full_Upper_Storage' not in active;assert 'R7_Gas_Boiler_Body' in active;")
(R/'scripts/finish_revision7_viewer.py').write_text(h)
print('REVISION7_DOCUMENTED')
