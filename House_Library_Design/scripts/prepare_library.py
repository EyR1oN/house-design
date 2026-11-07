from pathlib import Path
import bpy,json
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];dest=ROOT/'assets/prepared';dest.mkdir(exist_ok=True)
raw=ROOT/'data/library_raw_audit.json'
audit=json.loads((raw if raw.exists() else ROOT/'data/library_audit.json').read_text())
if not raw.exists():raw.write_text(json.dumps(audit,indent=2))
report=[]
for a in audit:
 role=a['role'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets'/f'{role}.blend'),load_ui=False)
 for o in bpy.context.scene.objects:
  for mod in o.modifiers:
   if mod.type=='SUBSURF':mod.levels=min(mod.levels,1);mod.render_levels=min(mod.render_levels,1)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();wanted={i['name'] for i in a['objects']};copies=[]
 c=bpy.data.collections.new('Stable_'+role)
 for o in list(bpy.context.scene.objects):
  if o.name not in wanted:continue
  me=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg);me.transform(o.matrix_world);me.update();n=bpy.data.objects.new(o.name+'_PREPARED',me);c.objects.link(n);copies.append((n,o.name))
 # Save geometry and its materials only; no drivers, helper bones or dependent rigs.
 clean=[];allvs=[]
 for o,name in copies:
  vs=[Vector(v) for v in o.bound_box];allvs+=vs;bb=[[float(min(v[i] for v in vs)),float(max(v[i] for v in vs))] for i in range(3)];clean.append({'name':o.name,'original_name':name,'type':'MESH','parent':None,'bounds':bb,'polygons':len(o.data.polygons),'materials':[m.name for m in o.data.materials if m]})
 a['objects']=clean;a['bounds']=[[float(min(v[i] for v in allvs)),float(max(v[i] for v in allvs))] for i in range(3)];a['dimensions']=[b-a for a,b in a['bounds']]
 bpy.data.libraries.write(str(dest/f'{role}.blend'),{c},fake_user=True,compress=True)
 report.append(a);print('PREPARED',role,sum(i['polygons'] for i in clean),a['dimensions'],flush=True)
(ROOT/'data/library_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('ALL_READY_MODELS_STABILISED',len(report),flush=True)
