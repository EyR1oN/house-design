from pathlib import Path
import os
R=Path(__file__).resolve().parents[1];os.environ['HOUSE_RENDER_READONLY']='1'
s=(R/'scripts/render_library.py').read_text(encoding='utf8');needle="selection=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(cams)"
s=s.replace('from mathutils import Vector','from mathutils import Vector,Matrix\nimport math,json')
s=s.replace(needle,"""cams['Kitchen_Pantry_Open']=bpy.data.objects['R13_CAMERA_PANTRY_OPEN']
rr=json.loads((ROOT/'data/revision14_report.json').read_text(encoding='utf8'));pivot=Vector(rr['pivot_blender']);T=Matrix.Translation(Vector((0,.22,0)))@Matrix.Translation(pivot)@Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Translation(-pivot)
for n in rr['motion_groups']['pivot']:
 o=bpy.data.objects[n];o.matrix_world=T@o.matrix_world
selection=['Kitchen_Pantry_Open']""")
exec(compile(s,str(R/'scripts/render_library.py'),'exec'))
