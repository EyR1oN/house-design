from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
s=(R/'scripts/update_revision8_viewer.py').read_text(encoding='utf8').replace('revision8','revision9').replace('REVISION8','REVISION9')
s=s.replace("names=json.loads((R/'data/revision9_report.json').read_text())['removed_objects']", "names=json.loads((R/'data/revision9_report.json').read_text())['removed_objects']+[n.get('name') for n in v['nodes']]")
s=s.replace('assert len(remove)==len(names),(len(remove),len(names))','assert remove')
s=s.replace('LIBRARY 8.0 Plain TV wall and large north-wall bulk pantry','LIBRARY 9.0 Clear centre and aligned end-wall laundry storage')
(R/'scripts/update_revision9_viewer.py').write_text(s,encoding='utf8')
changed=['Ground_Plan','Laundry','Laundry_Reverse','Laundry_Storage']
s=(R/'scripts/finish_revision8_viewer.py').read_text(encoding='utf8')
a=s.index('changed=');b=s.index('\n',a);s=s[:a]+'changed='+repr(changed)+s[b:]
s='\n'.join(line for line in s.split('\n') if not line.startswith("d['photos'].append"))
s=s.replace("assert 'R8_Potato_Sack' in active","assert 'R9_Potato_Sack' in active;assert not any(n.startswith('R8_Bulk_Pantry') for n in active)")
(R/'scripts/finish_revision9_viewer.py').write_text(s,encoding='utf8')
s=(R/'scripts/verify_revision8_delivery.py').read_text(encoding='utf8').replace('revision8','revision9').replace('REVISION8','REVISION9')
a=s.index('changed=');b=s.index('\n',a);s=s[:a]+'changed='+repr(changed)+s[b:]
(R/'scripts/verify_revision9_delivery.py').write_text(s,encoding='utf8')
s=(R/'scripts/render_revision8_storage.py').read_text(encoding='utf8')
a=s.index('for o in bpy.context.view_layer.objects:');b=s.index('bpy.ops.mesh.primitive_cube_add',a)
s=s[:a]+"for o in bpy.context.view_layer.objects:\n if o.type=='MESH' and (not o.name.startswith('R9_') or o.name.startswith(('R9_Tower','R9_Pantry_Sliding','R9_Potato_Vent_Front','R9_Potato_Pull','R9_Vegetable_Vent_Front','R9_Vegetable_Pull'))):o.hide_render=True\n"+s[b:]
s=s.replace('o.location=(9.0,2.2,1.34)','o.location=(8.2,3.552,1.34)').replace('Vector((9.0,3.6,1.34))','Vector((10.01,3.552,1.34))')
(R/'scripts/render_revision9_storage.py').write_text(s,encoding='utf8')
print('REVISION9_DELIVERY_SCRIPTS_READY')
