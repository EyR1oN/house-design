from pathlib import Path
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));s=bpy.context.scene
for w in bpy.context.window_manager.windows:w.view_layer=s.view_layers['Upper_Design']
bpy.context.view_layer.update();wall=bpy.data.objects['R3_Stair_Landing_Closure']
bpy.ops.mesh.primitive_cube_add(size=1,location=(6.555,7.53,4.30));cut=bpy.context.object;cut.scale=(.30,1.002,2.202);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);mod=wall.modifiers.new('Unobstructed stair exit','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.context.view_layer.objects.active=wall;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
bpy.ops.mesh.primitive_cube_add(size=1,location=(6.57,7.53,3.19));o=bpy.context.object;o.name='R3_Stair_Landing_Threshold'
for c in list(o.users_collection):c.objects.unlink(o)
bpy.data.collections['DESIGN_Upper_Hall'].objects.link(o);o.scale=(.16,1.00,.02);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(bpy.data.materials['LIBRARY_PBR_Warm_Stone'])
vs=[wall.matrix_basis@v.co for v in wall.data.vertices];fs=[list(p.vertices) for p in wall.data.polygons];tree=BVHTree.FromPolygons(vs,fs)
assert tree.ray_cast(Vector((6.40,7.53,4.20)),Vector((1,0,0)),.4)[0] is None,'Stair exit blocked'
r=json.loads((R/'data/revision3_report.json').read_text());r['stair_landing']={'opening_width_m':1.0,'headroom_m':2.2,'threshold_top_m':3.2,'unobstructed':True};(R/'data/revision3_report.json').write_text(json.dumps(r,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True);print('STAIR_EXIT_CLEAR')
