from pathlib import Path
import bpy,json,math
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Upper_Design']
p=json.loads((R/'data/placements.json').read_text());points=json.loads((R/'data/electrical_points.json').read_text())
# The tall wardrobe replaces the narrow bookcase; keep its corner clear.
a=next(a for a in p if a['label']=='Child_Bookcase')
for n in a['objects']:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
p.remove(a)
for label in ['Upper_Vanity_Soap','Upper_Vanity_Cup','Upper_Vanity_Tray']:
 a=next(a for a in p if a['label']==label);b=a['bounds'];dx=(sum(b[0])/2-9.75)*(.8/1.1-1)
 for n in a['objects']:bpy.data.objects[n].location.x+=dx
changes={'E2_080_SOCKET':dict(x_m=8.319,y_m=1.1,face='W',height_aff_m=1.10),'E2_081_DATA':dict(x_m=8.319,y_m=1.6,face='W',height_aff_m=1.10),'E2_083_SWITCH':dict(x_m=7.23)}
angles={'E':0,'N':math.pi/2,'W':math.pi,'S':-math.pi/2}
for pt in points:
 if pt['id'] not in changes:continue
 new=changes[pt['id']];old=Vector((pt['x_m'],pt['y_m'],3.2+pt['height_aff_m']));pos=Vector((new.get('x_m',pt['x_m']),new.get('y_m',pt['y_m']),3.2+new.get('height_aff_m',pt['height_aff_m'])));H=Matrix.Translation(pos)@Matrix.Rotation(angles[new.get('face',pt['face'])]-angles[pt['face']],4,'Z')@Matrix.Translation(-old)
 for o in bpy.data.objects:
  if o.name==pt['id'] or o.name.startswith(pt['id']+'_'):o.matrix_basis=H@o.matrix_basis
 pt.update(new)
for a in p:
 vs=[bpy.data.objects[n].matrix_basis@Vector(v) for n in a['objects'] for v in bpy.data.objects[n].bound_box];a['bounds']=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
(R/'data/placements.json').write_text(json.dumps(p,indent=2));(R/'data/electrical_points.json').write_text(json.dumps(points,indent=2))
s['interior_revision']='LIBRARY 4.0 Lower stair access and corrected room layouts';bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True);print('REVISION4_FINISHED',flush=True)
