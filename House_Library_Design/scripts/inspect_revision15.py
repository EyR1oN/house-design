import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Ground_Design']
bpy.context.view_layer.update()
for o in bpy.context.view_layer.objects:
 if o.type=='MESH':
  pts=[o.matrix_world@Vector(c) for c in o.bound_box];b=[[round(min(p[i] for p in pts),4),round(max(p[i] for p in pts),4)]for i in range(3)]
  if ('Hood' in o.name or 'hood' in o.name or (b[0][1]>9.7 and b[1][1]>6.0 and b[1][0]<7.12 and b[2][1]>1.55 and b[2][0]<2.9)):
   print('OBJECT',o.name,b,[m.name for m in o.data.materials])
