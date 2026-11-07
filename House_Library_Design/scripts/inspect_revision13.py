from pathlib import Path
import bpy,json
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
bpy.context.view_layer.update()
for o in bpy.context.view_layer.objects:
 if o.type!='MESH':continue
 v=[o.matrix_world@Vector(c) for c in o.bound_box];b=[[min(c[i] for c in v),max(c[i] for c in v)] for i in range(3)]
 if b[0][1]>9.34 and b[0][0]<10.4 and b[1][0]<4.60 and b[1][1]>3.92 and b[2][0]>.86 and b[2][1]<1.54:print(o.name,[[round(x,4) for x in a] for a in b], [m.name if m else None for m in o.data.materials])
print('KITCHEN ELECTRICAL',[(r['id'],r.get('x_m'),r.get('y_m'),r.get('height_aff_m')) for r in json.loads((R/'data/electrical_points.json').read_text(encoding='utf8')) if r.get('room')=='Kitchen'])
