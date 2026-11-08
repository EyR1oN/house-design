"""Include every room floor outline in the exportable ceilings."""
from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
s=bpy.context.scene;report=json.loads((R/'data/revision18_report.json').read_text())
def clip(poly,axis,limit,less):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ia=a[axis]<=limit if less else a[axis]>=limit;ib=b[axis]<=limit if less else b[axis]>=limit
  if ia:out.append(a)
  if ia!=ib:out.append(a+(b-a)*((limit-a[axis])/(b[axis]-a[axis])))
 return out
coverage={}
for floor in (1,2):
 bpy.context.window.view_layer=s.view_layers['Ground_Design' if floor==1 else 'Upper_Design'];bpy.context.view_layer.update()
 sources=[o for o in bpy.data.collections[f'R_L{floor}_FLOOR'].objects if o.type=='MESH' and ('FINISHED_FLOOR' in o.name or 'FLOOR_FINISH' in o.name)]
 verts=[];faces=[];height=2.895 if floor==1 else 5.895
 def face(poly):
  if len(poly)<3:return
  start=len(verts);verts.extend((p.x,p.y,height) for p in poly);faces.append(tuple(range(start,start+len(poly))))
 for o in sources:
  for p in o.data.polygons:
   if (o.matrix_world.to_3x3()@p.normal).z<.9:continue
   poly=[o.matrix_world@o.data.vertices[i].co for i in p.vertices]
   if floor==1:face(clip(poly,1,7.43,True));face(clip(clip(poly,1,7.43,False),0,6.61,False))
   else:face(poly)
 if floor==2:
  from mathutils import Vector
  face([Vector((5.49,7.43,0)),Vector((6.61,7.43,0)),Vector((6.61,11.83,0)),Vector((5.49,11.83,0))])
 ceiling=bpy.data.objects[f'R18_Ceiling_L{floor}'];material=ceiling.data.materials[0]
 mesh=bpy.data.meshes.new(ceiling.name+'_complete');mesh.from_pydata(verts,[],faces);mesh.materials.append(material);ceiling.data=mesh
 coverage[str(floor)]=[o.name for o in sources]
 bpy.ops.object.select_all(action='DESELECT')
 names=report['stair_objects']+[ceiling.name]+(report['moved_objects'] if floor==1 else ['R3_Stair_Landing_Threshold'])
 for name in names:o=bpy.data.objects[name];o.hide_set(False);o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(R/f'exports/revision18_floor{floor}.glb'),use_selection=True,export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
report['ceiling_room_coverage']=coverage
(R/'data/revision18_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
print('CEILING_COVERAGE',json.dumps(coverage))
