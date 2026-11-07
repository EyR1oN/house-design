from pathlib import Path
import bpy
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'))
collections=[c for c in bpy.data.collections if c.name.startswith('READY_ASSET_')]
for c in collections:
 path=R/'assets/previews'/(c.name.replace('READY_ASSET_','')+'.png')
 if path.exists():
  with bpy.context.temp_override(id=c):bpy.ops.ed.lib_id_load_custom_preview(filepath=str(path))
bpy.context.scene.cycles.device='CPU';bpy.ops.file.pack_all();bpy.data.libraries.write(str(R/'Ready_Furniture_Library.blend'),set(collections),fake_user=True,compress=True)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True)
print('CATALOG_PREVIEWS_EMBEDDED',len(collections))
