from pathlib import Path
R=Path(__file__).resolve().parents[1]
path=R.parent/'HOUSE_HANDOFF_UK.md';b=path.read_bytes();m5='## Редакція 5'.encode('cp1251');m6='## Редакція 6'.encode('utf8');a=b.find(m5);z=b.find(m6,a)
if a>=0 and z>a:b=b[:a]+b[a:z].decode('cp1251').encode('utf8')+b[z:]
path.write_bytes(b)
(R/'README.md').write_text('''# Будинок — бібліотечний дизайн, редакція 7

Головний редагований файл: House_Library_Design.blend. Blender 4.5.3 LTS: C:/Tetiana/Tools/blender-4.5.3-windows-x64/blender.exe. У корені пакета є Відкрити Blender.cmd.

Текстури упаковані. Design_Gallery.html показує рендери, сусідня папка House_Browser_Viewer містить автономний вебпереглядач. Бібліотека: Ready_Furniture_Library.blend, підготовлені активи — assets/prepared. Авторство та ліцензії — ASSET_CREDITS.md і data/library_manifest.json.

Не запускати історичні скрипти створення й попередніх редакцій поверх поточного master. Перед новими змінами зберігати резервну копію. Для продовження прочитати HOUSE_HANDOFF_UK.md у корені пакета.

Редакція 5: Arlos Dining Table на чотирьох ніжках, замість лавки два додаткові стільці; обідню групу посунуто на 250 мм до кухні. Редакція 6: додаткове зміщення на 320 мм, зазор стільця до острівця 122,5 мм. Редакція 7 описана нижче.

Розетки, інженерні точки та котел позначають пропозиції для планування; MEP_AS_BUILT не заповнюється припущеннями.
''',encoding='utf8')
print('DOC_ENCODING_REPAIRED')
