from pathlib import Path
import bpy,json
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
bpy.context.view_layer.update()
def bb(o):
 vs=[o.matrix_world@Vector(v) for v in o.bound_box];return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
r=[]
for o in bpy.context.view_layer.objects:
 if o.type=='MESH' and (any(k in o.name.lower() for k in ['laundry','crockery_oak','decorative_panel','stair_wall','living_tv']) or (o.name.startswith('R_') and 8<sum(bb(o)[0])/2<10.9 and 2<sum(bb(o)[1])/2<4)):
  r.append({'name':o.name,'bounds':bb(o),'materials':[m.name for m in o.data.materials if m],'collections':[c.name for c in o.users_collection]})
(R/'data/revision7_scene_audit.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
