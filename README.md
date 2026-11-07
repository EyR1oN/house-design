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
