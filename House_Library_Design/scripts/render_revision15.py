from pathlib import Path
import os,sys
R=Path(__file__).resolve().parents[1];os.environ['HOUSE_RENDER_READONLY']='1'
s=(R/'scripts/render_library.py').read_text(encoding='utf8')
needle="selection=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(cams)"
s=s.replace(needle,"cams['Kitchen_Hood']=bpy.data.objects['R15_CAMERA_HOOD']\ncams['Kitchen_Hood_Storage']=bpy.data.objects['R15_CAMERA_HOOD']\n"+needle)
s=s.replace("s.render.filepath=str(ROOT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True);bg.inputs['Strength'].default_value=old_strength", "\n if name=='Kitchen_Hood_Storage':\n  for o in bpy.data.objects:\n   if o.name.startswith(('R15_Hood_Door_','R15_Removable_Duct_Service_Cover')):o.hide_render=True\n s.render.filepath=str(ROOT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True);bg.inputs['Strength'].default_value=old_strength\n if name=='Kitchen_Hood_Storage':\n  for o in bpy.data.objects:\n   if o.name.startswith(('R15_Hood_Door_','R15_Removable_Duct_Service_Cover')):o.hide_render=False")
exec(compile(s,str(R/'scripts/render_library.py'),'exec'))

