from pathlib import Path
import bpy,json,math
from mathutils import Matrix,Vector
R=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'House_Library_Design.blend'));p=json.loads((R/'data/placements.json').read_text());a=next(a for a in p if a['label']=='Child_Wardrobe');c=Vector([sum(x)/2 for x in a['bounds']]);H=Matrix.Translation(c)@Matrix.Rotation(math.pi,4,'Z')@Matrix.Translation(-c)
for n in a['objects']:o=bpy.data.objects[n];o.matrix_basis=H@o.matrix_basis;o['front_faces_child_room']=True
bpy.ops.wm.save_as_mainfile(filepath=str(R/'House_Library_Design.blend'),compress=True);print('WARDROBE_FRONT_FACES_ROOM')
