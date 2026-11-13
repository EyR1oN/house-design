from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'automation'))
from open_stair_exit_viewer import read_glb,write_glb
from build_viewer import build as build_viewer
viewer=ROOT/'House_Browser_Viewer';base_path=viewer/'House_Floor_1.glb';patch_path=viewer/'revision21_switches_floor1.glb'
report_path=ROOT/'House_Library_Design/data/revision21_report.json';report=json.loads(report_path.read_text(encoding='utf8'))
expected={n for s in report['switches'] for n in s['objects']}
base,base_bin=read_glb(base_path.read_bytes());patch,patch_bin=read_glb(patch_path.read_bytes())
def reachable(doc):
 seen=set()
 def visit(i):
  if i in seen:return
  seen.add(i)
  for c in doc['nodes'][i].get('children',[]):visit(c)
 for i in doc['scenes'][doc.get('scene',0)]['nodes']:visit(i)
 return seen
old_active=reachable(base);patch_active=reachable(patch)
patch_names={patch['nodes'][i].get('name') for i in patch_active}
if patch_names!=expected:raise ValueError(f'Patch mismatch: missing={expected-patch_names}, extra={patch_names-expected}')
removed={i for i,n in enumerate(base['nodes']) if n.get('name') in expected}
removed_active={base['nodes'][i].get('name') for i in removed if i in old_active}
if removed_active!=expected:raise ValueError(f'Expected previous active switch nodes: missing={expected-removed_active}')
for scene in base['scenes']:
 scene['nodes']=[i for i in scene.get('nodes',[]) if i not in removed]
for node in base['nodes']:
 if 'children' in node:node['children']=[i for i in node['children'] if i not in removed]
patch_roots=list(patch['scenes'][patch.get('scene',0)]['nodes'])
keys=['bufferViews','accessors','images','samplers','textures','materials','meshes','nodes']
offsets={k:len(base.get(k,[])) for k in keys};binary_offset=(len(base_bin)+3)&~3
base_bin+=b'\0'*(binary_offset-len(base_bin))+patch_bin
for view in patch.get('bufferViews',[]):view['buffer']=0;view['byteOffset']=view.get('byteOffset',0)+binary_offset
for accessor in patch.get('accessors',[]):
 if 'bufferView' in accessor:accessor['bufferView']+=offsets['bufferViews']
for image in patch.get('images',[]):
 if 'bufferView' in image:image['bufferView']+=offsets['bufferViews']
for texture in patch.get('textures',[]):
 if 'source' in texture:texture['source']+=offsets['images']
 if 'sampler' in texture:texture['sampler']+=offsets['samplers']
def offset_tex(v):
 if isinstance(v,dict):
  for k,c in v.items():
   if k.endswith('Texture') and isinstance(c,dict) and 'index' in c:c['index']+=offsets['textures']
   else:offset_tex(c)
 elif isinstance(v,list):
  for c in v:offset_tex(c)
for m in patch.get('materials',[]):offset_tex(m)
for mesh in patch.get('meshes',[]):
 for primitive in mesh['primitives']:
  primitive['attributes']={k:i+offsets['accessors'] for k,i in primitive['attributes'].items()}
  if 'indices' in primitive:primitive['indices']+=offsets['accessors']
  if 'material' in primitive:primitive['material']+=offsets['materials']
for node in patch['nodes']:
 node['extras']={**node.get('extras',{}),'level':1,'revision':21}
 if 'mesh' in node:node['mesh']+=offsets['meshes']
 if 'children' in node:node['children']=[i+offsets['nodes'] for i in node['children']]
for k in keys:base.setdefault(k,[]).extend(patch.get(k,[]))
base['scenes'][base.get('scene',0)]['nodes'].extend(i+offsets['nodes'] for i in patch_roots)
base['scenes'][base.get('scene',0)].setdefault('extras',{})['interior_revision']='LIBRARY 21.0 screenshot-corrected switch locations'
for k in ('extensionsUsed','extensionsRequired'):
 if patch.get(k):base[k]=sorted(set(base.get(k,[])+patch[k]))
active=reachable(base);names=[base['nodes'][i].get('name') for i in active]
if len(names)!=len(set(names)):raise ValueError('Duplicate active nodes after switch replacement')
if not expected.issubset(names):raise ValueError(f'Missing switch nodes: {expected-set(names)}')
if sum(base['nodes'][i].get('extras',{}).get('pantry_role')=='pivot' for i in active)!=20:raise ValueError('Corner pantry pivot nodes not preserved')
for v in base.get('bufferViews',[]):
 if v.get('byteOffset',0)+v['byteLength']>len(base_bin):raise ValueError('GLB bufferView out of range')
temp=base_path.with_suffix('.revision21.tmp');temp.write_bytes(write_glb(base,base_bin));temp.replace(base_path)

# Update the first-floor electrical SVG markers from the authoritative point schedule.
points={p['id']:p for p in json.loads((ROOT/'House_Library_Design/data/electrical_points.json').read_text(encoding='utf8'))}
svg_path=ROOT/'House_Library_Design/exports/Electrical_Points_Floor_1.svg';lines=svg_path.read_text(encoding='utf8').splitlines()
def fmt(x):return f'{x:.3f}'.rstrip('0').rstrip('.')
def px(x,y):return 183.5+(x-6.0)*115.0,1660.0-y*115.0
for pid in ('E1_004_SWITCH','E1_019_SWITCH','E1_090_SWITCH'):
 p=points[pid];x,y=px(p['x_m'],p['y_m'])
 pat=re.compile(r'(<circle cx=")[^"]+(" cy=")[^"]+(" r="8"[^>]*><title>'+re.escape(pid)+r' /.*?</title></circle>)')
 matches=[i for i,line in enumerate(lines) if pat.search(line)]
 if len(matches)!=1:raise ValueError(f'{pid}: expected one SVG point, found {len(matches)}')
 i=matches[0];lines[i]=pat.sub(lambda m:m.group(1)+fmt(x)+m.group(2)+fmt(y)+m.group(3),lines[i])
 number=pid.split('_')[1]
 label=re.compile(r'(<text x=")[^"]+(" y=")[^"]+(" font-size="13"[^>]*>'+number+r'</text>)')
 if not label.search(lines[i+1]):raise ValueError(f'{pid}: SVG point label missing')
 lines[i+1]=label.sub(lambda m:m.group(1)+fmt(x+10)+m.group(2)+fmt(y-7)+m.group(3),lines[i+1])
svg_path.write_text('\n'.join(lines)+'\n',encoding='utf8')

html_path=viewer/'House_Viewer.html';build_viewer(html_path)
html=html_path.read_text(encoding='utf8')
if '__HOUSE_DATA_JSON__' in html or '__FIRST_PERSON_SCRIPT__' in html:raise ValueError('Viewer template markers remain')
photo_count=html.count('"mime":"image/png"')
if photo_count!=36:raise ValueError(f'Expected 36 embedded gallery photos, found {photo_count}')
report['json_points_match_report']=all(abs(points[s['id']]['x_m']-s['to']['x_m'])<1e-6 and abs(points[s['id']]['y_m']-s['to']['y_m'])<1e-6 and points[s['id']]['face']==s['to']['face'] for s in report['switches'])
if not report['json_points_match_report']:raise ValueError('Electrical JSON does not match report')
report['rendered_screenshots']={n:(ROOT/'House_Library_Design/previews'/f'{n}.png').is_file() for n in ('Kitchen','Kitchen_Reverse','Living_Dining','Ground_Hall')}
if not all(report['rendered_screenshots'].values()):raise ValueError('Missing rendered screenshot')
(ROOT/'House_Library_Design/data/revision21_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
verification={'revision':21,'active_floor1_node_count':len(active),'updated_switch_components':sorted(expected),'switch_nodes_active_once':True,'duplicate_active_node_names':0,'corner_pantry_pivot_nodes':20,'all_buffer_views_within_glb':True,'floor2_glb_unchanged':True,'embedded_viewer_rebuilt':True,'gallery_photos_embedded':photo_count,'viewer_html_bytes':html_path.stat().st_size,'electrical_svg_updated':str(svg_path.relative_to(ROOT))}
(ROOT/'House_Library_Design/data/revision21_browser_verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(verification,ensure_ascii=False))
