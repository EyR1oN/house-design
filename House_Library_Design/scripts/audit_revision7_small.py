from pathlib import Path
import bpy,json
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
for w in bpy.context.window_manager.windows:w.view_layer=bpy.context.scene.view_layers['Ground_Design']
bpy.context.view_layer.update()
for o in bpy.context.view_layer.objects:
 if o.type not in ['MESH','LIGHT']:continue
 b=[[min((o.matrix_world@Vector(v))[i] for v in o.bound_box),max((o.matrix_world@Vector(v))[i] for v in o.bound_box)] for i in range(3)] if o.type=='MESH' else [[v,v] for v in o.location]
 if (7.9<sum(b[0])/2<8.8 and 5.7<sum(b[1])/2<7.05) or 'E1_022' in o.name or 'E1_023' in o.name or 'Hinge' in o.name and 'Fridge' in o.name:print(o.name,b)
print('MATS',[(m.name,tuple(m.diffuse_color)) for m in bpy.data.materials if m.name in ['DESIGN_Oak','LIBRARY_PBR_Warm_Plaster']])
