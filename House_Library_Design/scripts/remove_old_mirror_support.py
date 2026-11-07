from pathlib import Path
import bpy,bmesh,json
from mathutils import Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
p=json.loads((R/'data/placements.json').read_text());a=next(a for a in p if a['label']=='Bedroom_Makeup_Vanity')
for n in a['objects']:
 o=bpy.data.objects[n]
 if o.get('source_object_name')=='Circle_PREPARED':
  o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if (o.matrix_basis@v.co).z>3.968],context='VERTS');bm.to_mesh(o.data);bm.free();o.data.update()
vs=[bpy.data.objects[n].matrix_basis@Vector(v) for n in a['objects'] for v in bpy.data.objects[n].bound_box];a['bounds']=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
points=json.loads((R/'data/electrical_points.json').read_text());pt=next(x for x in points if x['id']=='E2_035_SOCKET');dy=11.71-pt['y_m']
for o in bpy.data.objects:
 if o.name==pt['id'] or o.name.startswith(pt['id']+'_'):o.location.y+=dy
pt['y_m']=11.71;(R/'data/electrical_points.json').write_text(json.dumps(points,indent=2))
(R/'data/placements.json').write_text(json.dumps(p,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
