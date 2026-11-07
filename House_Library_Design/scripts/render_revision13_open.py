from pathlib import Path
import os
R=Path(__file__).resolve().parents[1];os.environ['HOUSE_RENDER_READONLY']='1'
s=(R/'scripts/render_library.py').read_text(encoding='utf8')
needle="selection=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(cams)"
s=s.replace(needle,"""cams['Kitchen_Pantry_Open']=bpy.data.objects['R13_CAMERA_PANTRY_OPEN']
for o in bpy.data.objects:
 if o.get('pantry_role')=='front':o.location.y+=.66
 elif o.get('pantry_role')=='rear':o.location.x-=.60;o.location.y+=.14
selection=['Kitchen_Pantry_Open']""")
exec(compile(s,str(R/'scripts/render_library.py'),'exec'))
