from pathlib import Path
R=Path(__file__).resolve().parents[1]
for name in ['update_revision9_viewer.py','finish_revision9_viewer.py','verify_revision9_delivery.py']:
 s=(R/'scripts'/name).read_text(encoding='utf8').replace('revision9','revision11').replace('REVISION9','REVISION11').replace('LIBRARY 9.0 Clear centre and aligned end-wall laundry storage','LIBRARY 11.0 Right boiler, left appliances, shallow sidewall pantry')
 s=s.replace("assert 'R9_Potato_Sack' in active", "assert 'R9_Potato_Sack' in active;assert 'R11_Preserves_Jar_0_0_0' in active;assert not any(n.startswith('R9_Pantry_') for n in active)")
 (R/'scripts'/name.replace('revision9','revision11')).write_text(s,encoding='utf8')
s=(R/'scripts/render_revision9_storage.py').read_text(encoding='utf8')
a=s.index('for o in bpy.context.view_layer.objects:');b=s.index('bpy.ops.mesh.primitive_cube_add',a)
s=s[:a]+"for o in bpy.context.view_layer.objects:\n if o.type=='MESH' and (not o.name.startswith('R11_') or o.name.startswith(('R11_Boiler_Bin','R11_Side_Pantry_Sliding','R11_Side_Vegetable_Vent','R11_Side_Vegetable_Pull'))):o.hide_render=True\n"+s[b:]
s=s.replace('o.location=(8.2,3.552,1.34)','o.location=(8.81,2.2,1.34)').replace('Vector((10.01,3.552,1.34))','Vector((8.81,3.66,1.34))')
(R/'scripts/render_revision11_storage.py').write_text(s,encoding='utf8')
text='''

## Редакція 11 — котел праворуч, техніка ліворуч, бічна комора

Навпроти входу пралка й сушарка зміщені ліворуч на 480 мм; котел праворуч на східній стіні у вказаному користувачем куті. Вихід для вентиляції/димових газів прив’язаний лише за описом користувача: призначення отвору, сумісність котла та інженерні траси ще не підтверджені. Котел не захований у меблі. Під його ескізними патрубками 270 мм до стільниці низької комори. Там збережено глибокий картопляний відсік і два овочеві ящики.

Стару високу торцеву комору замінено бічною шафою: корпус 640 × 250 × 2590 мм. Вона коротша за попередню пропозицію, щоб залишити місце для відкривання люків; геометричний запас при консервативному виносі дверцят техніки на 550 мм лише 5 мм, тому фактичну техніку та її петлі перевірити перед виготовленням. Верхні фасади розсувні; п’ять рівнів полиць, два ряди по шість умовних банок, разом 60. Унизу два неглибокі вентильовані відсіки. Над сушаркою окреме господарське зберігання. Ширина вільної зони біля комори близько 879 мм з урахуванням ручок, до корпуса — 935 мм. Перед висунутим глибоким ящиком залишається 624 мм.

Двері входу не перетинають нові меблі. Розетки на відкритій ділянці північної стіни між коморою та технікою. Інші кімнати збережені. Резервна копія — House_Library_Revision10_Backup. Скрипт refine_revision11.py вже застосований; не повторювати. Перевірки моделі: data/revision11_verification.json. Оновлені план, два ракурси пральні, внутрішнє наповнення бічної комори, вебмодель та архів. Ні місткість, ні монтажне рішення не є специфікацією реальних виробів.
'''
for path in [R/'README.md',R.parent/'HOUSE_HANDOFF_UK.md']:
 s=path.read_text(encoding='utf8').replace('дизайн, редакція 10','дизайн, редакція 11').replace('завершена редакція 10','завершена редакція 11').replace('продовжуй з редакції 10','продовжуй з редакції 11')
 if '## Редакція 11' not in s:s+=text
 path.write_text(s,encoding='utf8')
