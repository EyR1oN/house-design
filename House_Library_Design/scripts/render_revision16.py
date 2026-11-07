from pathlib import Path
import os,sys
R=Path(__file__).resolve().parents[1];os.environ['HOUSE_RENDER_READONLY']='1'
s=(R/'scripts/render_library.py').read_text(encoding='utf8').replace('from mathutils import Vector','from mathutils import Vector,Matrix\nimport math,json')
needle="selection=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(cams)"
s=s.replace(needle,"""cams['Kitchen_Hood']=bpy.data.objects['R15_CAMERA_HOOD']
cams['Kitchen_Hood_Storage']=bpy.data.objects['R15_CAMERA_HOOD']
cams['Kitchen_Pantry_Open']=bpy.data.objects['R13_CAMERA_PANTRY_OPEN']
cams['Office_Reverse'].location=(10.75,2.85,4.85)
cams['Office_Reverse'].rotation_euler=(Vector((8.65,4.80,4.20))-cams['Office_Reverse'].location).to_track_quat('-Z','Y').to_euler()
cams['Office_Reverse'].data.lens=21
"""+needle)
needle="s.render.filepath=str(ROOT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True);bg.inputs['Strength'].default_value=old_strength"
s=s.replace(needle,"""
 temporary_matrices={};hidden=[]
 if name=='Kitchen_Hood_Storage':
  for o in bpy.data.objects:
   if o.name.startswith(('R15_Hood_Door_','R15_Removable_Duct_Service_Cover')):hidden.append(o);o.hide_render=True
 if name=='Kitchen_Pantry_Open':
  rr=json.loads((ROOT/'data/revision14_report.json').read_text());pivot=Vector(rr['pivot_blender']);T=Matrix.Translation(Vector((0,.22,0)))@Matrix.Translation(pivot)@Matrix.Rotation(-math.pi/2,4,'Z')@Matrix.Translation(-pivot)
  for n in rr['motion_groups']['pivot']:
   o=bpy.data.objects[n];temporary_matrices[n]=o.matrix_world.copy();o.matrix_world=T@o.matrix_world
 s.render.filepath=str(ROOT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True);bg.inputs['Strength'].default_value=old_strength
 for n,M in temporary_matrices.items():bpy.data.objects[n].matrix_world=M
 for o in hidden:o.hide_render=False
""")
exec(compile(s,str(R/'scripts/render_library.py'),'exec'))
