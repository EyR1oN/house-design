# House Design — права секція будинку

Репозиторій: https://github.com/EyR1oN/house-design

Приватний робочий проєкт інтер’єру й архітектурної моделі. Поточна редакція **16**. Великі файли зберігаються через **Git LFS**.

## Відкрити

- Без Blender: `Відкрити 3D.html`, або `House_Browser_Viewer/House_Viewer.html` у Chrome/Edge. Усередині дві моделі поверхів і 36 рендерів; інтернет для перегляду не потрібний.
- Альбом: `House_Library_Design/Design_Gallery.html`.
- Редагування: `House_Library_Design/House_Library_Design.blend`, Blender 4.5.3 LTS. Текстури упаковані. `Ready_Furniture_Library.blend` — джерела меблів, а не головний будинок.
- Оригінальні креслення: `references/house_drawings.pdf`.

## Інший ноутбук

Встановіть Git, Git LFS і Blender 4.5.3 LTS. Клонуйте репозиторій і відкрийте його папку:

```powershell
git clone https://github.com/EyR1oN/house-design.git
cd house-design
```

Потім:

```powershell
git lfs install --local
git lfs pull
```

Переконайтеся, що завантажилися самі великі файли, а не короткі LFS-покажчики. GitHub ZIP не є рекомендованим способом отримання робочої копії з LFS; використовуйте clone.

Перед кожною роботою:

```powershell
git status
git pull --ff-only
git lfs pull
```

Після роботи: зберегти й закрити Blender; оновити потрібні дані, GLB, HTML, рендери та хендоф, потім:

```powershell
git add .
git commit -m "Describe the house update"
git push
```

Працюйте на одному ноутбуці за раз. .blend не зливається як текст; при конфлікті зберігайте обидві версії. Не застосовуйте примусове скидання або force push для синхронізації.

## Контекст і перевірки

Прочитайте `AGENTS.md`, `HOUSE_HANDOFF_UK.md`, `House_Library_Design/README.md` та `Design_Research/PLANNING_CONTEXT_UK.md`. Історичні build/refine-скрипти вже застосовані; не запускайте їх поверх поточного master.

Результати імпорту й перевірок: `MIGRATION_AUDIT_UK.md` та `House_Library_Design/data/import_audit.json`. Перевірка дверей редакції 16: `House_Library_Design/scripts/verify_revision16.py`; її базова таблиця редакції 15 включена у source/, тому повна резервна папка для неї не потрібна.

Blender-програма в Tools/, локальні резервні копії, ZIP, журнали та облікові дані не включаються в Git. Оригінальний переносний ZIP з редакцією 15 і Blender залишився на робочому столі першого ноутбука. Запускач `Відкрити Blender.cmd` підтримує локальну папку Tools/, змінну BLENDER_EXE або Blender у PATH.

Авторство й ліцензії моделей: `House_Library_Design/ASSET_CREDITS.md`. Бібліотечні активи не отримують нову відкриту ліцензію через збереження у цьому репозиторії. Інженерні точки — PROPOSED.


## Безпечна збірка 3D-переглядача

Готовий автономний HTML уже включений у репозиторій; після clone + LFS його можна відразу оглядати. Для повторного пакування з поточних GLB і фото потрібен Python 3.10+; сторонні Python-пакети й інтернет не потрібні:

```powershell
python automation/build_viewer.py
```

Або `Build-Viewer.ps1 -PythonPath <шлях-до-python.exe>`. Для тестової копії без зміни основного переглядача:

```powershell
python automation/build_viewer.py --output .local-preview/House_Viewer.html
```

Збірка читає обидва House_Floor_*.glb, gallery_views.json та відповідні previews/*.png. Дизайн, .blend, геометрію і рендери вона не змінює. Збережені рух кутової шафи, матеріали й керування переглядачем; втрачені LFS-файли зупиняють збірку до заміни результату. Шаблон інтерфейсу: House_Browser_Viewer/viewer_template.html.

Після заміни меблів у Blender потрібно перевірити їхню геометрію й опору, оновити відповідні дані та рендери, експортувати змінені GLB й лише тоді пакувати HTML. Сам git push не запускає Blender і не оновлює експорт. Для нових експортів зберігати pantry_role й 20 рухомих вузлів кутової шафи; Z другого поверху +3.2 м у Blender відповідає підлозі Y=0 у його окремому GLB.

Старий Rebuild_Library_Design.ps1 тепер навмисно зупиняє виконання: він раніше перебудовував початковий master поверх пізніших редакцій. Історичні build/refine-скрипти доступні як історія, але не є щоденною командою збірки.
