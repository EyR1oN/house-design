from pathlib import Path
import bpy,json
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Upper_Design']
bpy.context.view_layer.update()
p=json.loads((R/'data/placements.json').read_text(encoding='utf8'))
for l in ['Bedroom_Makeup_Vanity','Bedroom_Wall_Makeup_Mirror']:
 for n in next(r for r in p if r['label']==l)['objects']:
  o=bpy.data.objects[n];v=[o.matrix_world@Vector(c) for c in o.bound_box];print(n,[[round(min(c[i] for c in v),3),round(max(c[i] for c in v),3)] for i in range(3)],[m.name if m else None for m in o.data.materials])
