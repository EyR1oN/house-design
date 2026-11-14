"""Add the existing inter-floor slab to the compact upper GLB and rebuild the viewer.

Run House_Library_Design/scripts/export_interfloor_structure.py in Blender first.
This migration changes the web export only; the Blender master is left untouched.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'automation'))

from build_viewer import build as build_viewer
from compact_viewer_models import compact, read_glb, remap_texture_fields, write_glb

VIEWER = ROOT / 'House_Browser_Viewer'
PROJECT = ROOT / 'House_Library_Design'
PATCH = ROOT / '.local-preview' / 'interfloor-structure.glb'
UPPER_GLB = VIEWER / 'House_Floor_2.glb'
HOUSE_HTML = VIEWER / 'House_Viewer.html'
SLAB_NODES = {'R_L2_STRUCTURAL_SLAB', 'R_L2_SCREED'}
FLOOR_OFFSET_M = 3.2


def active_node_indices(document):
    nodes = document.get('nodes', [])
    active = set()

    def visit(index):
        if index in active:
            return
        if not isinstance(index, int) or index < 0 or index >= len(nodes):
            raise ValueError(f'Invalid node reference: {index}')
        active.add(index)
        for child in nodes[index].get('children', []):
            visit(child)

    scene_index = document.get('scene', 0)
    for index in document['scenes'][scene_index].get('nodes', []):
        visit(index)
    return active


def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise ValueError(f'Expected exactly one {label}, found {count}.')
    return source.replace(old, new, 1)


def replace_region(source, start_marker, end_marker, replacement, label):
    start = source.find(start_marker)
    if start < 0:
        raise ValueError(f'Missing {label} start marker.')
    end = source.find(end_marker, start + len(start_marker))
    if end < 0:
        raise ValueError(f'Missing {label} end marker.')
    return source[:start] + replacement + source[end:]


def update_viewer_template():
    path = VIEWER / 'viewer_template.html'
    source = path.read_text(encoding='utf-8')
    if 'const FLOOR_OFFSET = Number(Gu.floorOffset) || 3.2;' in source:
        raise RuntimeError('The whole-house viewer controller is already installed.')

    camera_controller = '''function Cs(i="all") {
  const [x, floorY, z, distance] = Tl[va][i] || Tl[va].all;
  const y = floorY + (va === 2 ? FLOOR_OFFSET : 0);
  rn.target.set(x, y, z);
  if (Ma === "plan") {
    xn.position.set(x, y + distance, z + .001);
    xn.up.set(0, 0, -1);
  } else {
    xn.up.set(0, 1, 0);
    xn.position.set(x + distance * .53, y + distance * .68, z + distance * .68);
  }
  xn.lookAt(rn.target);
  rn.update();
  Bi = true;
}
'''
    source = replace_region(source, 'function Cs(i="all"){', 'function Ju()', camera_controller, 'camera fitter')

    clipping_controller = '''function Ju() {
  Zu.constant = Number(Ke("height").value) + (va === 2 ? FLOOR_OFFSET : 0);
  for (const [floorText, root] of Object.entries(ya)) {
    if (!root) continue;
    const shouldClip = Ku && Number(floorText) === va;
    root.traverse(node => {
      if (!node.isMesh || !(node.userData.viewer_walls || node.userData.viewer_clip_with_walls)) return;
      for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
        material.clippingPlanes = shouldClip ? [Zu] : [];
        material.needsUpdate = true;
      }
    });
  }
  Bi = true;
}
'''
    source = replace_region(source, 'function Ju()', 'function o0(i)', clipping_controller, 'floor-aware wall clipping')

    loader = '''let floorRequest = 0;
const floorLoads = {};
const FLOOR_OFFSET = Number(Gu.floorOffset) || 3.2;

async function loadFloor(i) {
  await new Promise(resolve => setTimeout(resolve, 30));
  const root = await new Promise((resolve, reject) => s0.parse(o0(Gu.models[i]), "", gltf => resolve(gltf.scene), reject));
  root.position.y = i === 2 ? FLOOR_OFFSET : 0;
  root.traverse(mesh => {
    if (!mesh.isMesh) return;
    mesh.frustumCulled = true;
    if (mesh.parent?.userData.viewer_clip_with_walls) mesh.userData.viewer_clip_with_walls = true;
    if (mesh.userData.viewer_walls || mesh.userData.viewer_clip_with_walls) {
      mesh.material = Array.isArray(mesh.material)
        ? mesh.material.map(material => material.clone()) : mesh.material.clone();
    }
    for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      material.envMapIntensity = .55;
      material.side = Vt;
    }
  });
  if (i === 2) {
    const duplicateStairs = root.getObjectByName("PART_R_STAIRS");
    if (duplicateStairs) duplicateStairs.visible = false;
  }
  ya[i] = root;
  return root;
}

async function ensureFloor(i) {
  if (ya[i]) return ya[i];
  floorLoads[i] ??= loadFloor(i).catch(error => {
    delete ya[i];
    throw error;
  }).finally(() => { delete floorLoads[i]; });
  return floorLoads[i];
}

async function loadAllFloors() {
  // Parse sequentially to keep the peak memory lower on portable laptops.
  await ensureFloor(1);
  await ensureFloor(2);
  return ya;
}

async function El(i) {
  const request = ++floorRequest;
  Ke("loading").hidden = false;
  Ke("loading").textContent = "Завантажую обидва поверхи…";
  try {
    await loadAllFloors();
    if (request !== floorRequest) return;

    va = i;
    for (const floor of [1, 2]) {
      const root = ya[floor];
      root.position.y = floor === 2 ? FLOOR_OFFSET : 0;
      root.visible = floor === 1 || i === 2;
      if (root.parent !== Ln) Ln.add(root);
    }
    Rs = ya[i];
    window.HOUSE_ELECTRICAL_MODE?.applyToFloor(Rs);
    Ju();
    Cs();
    Ke("rooms").innerHTML = Object.keys(Tl[i]).map(room => `<option value="${room}">${r0[room]}</option>`).join("");
    document.querySelectorAll("[data-floor]").forEach(button => button.classList.toggle("active", Number(button.dataset.floor) === i));
    Ke("loading").hidden = true;
    Ke("status").textContent = (i === 1 ? "Перший" : "Другий") + " поверх · обидва поверхи завантажені";
    window.VIEWER_READY = true;
  } catch (error) {
    if (request !== floorRequest) return;
    console.error(error);
    Ke("loading").textContent = "Не вдалося відкрити 3D. Нижче доступні всі рендери кімнат.";
    window.VIEWER_ERROR = String(error);
  }
}
'''
    source = replace_region(
        source,
        'let floorRequest = 0;',
        'document.querySelectorAll("[data-floor]").forEach(i=>i.onclick=()=>El(Number(i.dataset.floor)))',
        loader,
        'all-floors loader',
    )
    source = replace_once(
        source,
        'Zu.constant=Number(i.target.value)',
        'Zu.constant=Number(i.target.value)+(va===2?FLOOR_OFFSET:0)',
        'floor-relative cut height',
    )
    source = replace_once(source, 'showFloor:El,fit:Cs', 'showFloor:El,loadAllFloors,fit:Cs', 'walk-mode floor loader API')
    path.write_text(source, encoding='utf-8', newline='\n')


def merge_patch():
    if not PATCH.is_file():
        raise FileNotFoundError(f'Run the Blender exporter first: {PATCH}')
    base, base_binary = read_glb(UPPER_GLB)
    patch, patch_binary = read_glb(PATCH)
    patch_active = active_node_indices(patch)
    patch_names = {patch['nodes'][index].get('name') for index in patch_active}
    if patch_names != SLAB_NODES:
        raise ValueError(f'Unexpected structural patch nodes: {sorted(patch_names)}')
    patch_roots = list(patch['scenes'][patch.get('scene', 0)].get('nodes', []))
    if len(patch_roots) != 2 or len(patch_active) != 2:
        raise ValueError('Expected a flat patch with exactly two structural meshes.')

    # Remove previous copies first so rerunning this migration does not create overlaps.
    remove = {index for index, node in enumerate(base['nodes']) if node.get('name') in SLAB_NODES}
    for scene in base.get('scenes', []):
        scene['nodes'] = [index for index in scene.get('nodes', []) if index not in remove]
    for node in base.get('nodes', []):
        if 'children' in node:
            node['children'] = [index for index in node['children'] if index not in remove]
    if remove:
        base, base_binary, _ = compact(base, base_binary, expected_pivots=0)

    # Blender source coordinates are world Z-up. The viewer stores floor 2 locally,
    # so offset these new root nodes by -3.2 m; the viewer later places that root at +3.2 m.
    for index in patch_roots:
        node = patch['nodes'][index]
        if node.get('children'):
            raise ValueError('Structural patch nodes must remain flat GLB roots.')
        translation = list(node.get('translation', [0, 0, 0]))
        translation[1] -= FLOOR_OFFSET_M
        node['translation'] = translation
        node['extras'] = {**node.get('extras', {}), 'level': 2, 'revision': 27}

    keys = ('bufferViews', 'accessors', 'images', 'samplers', 'textures', 'materials', 'meshes', 'nodes')
    offsets = {key: len(base.get(key, [])) for key in keys}
    base_binary = bytearray(base_binary)
    binary_offset = (len(base_binary) + 3) & ~3
    base_binary.extend(b'\0' * (binary_offset - len(base_binary)))
    patch_buffer_length = patch.get('buffers', [{}])[0].get('byteLength', len(patch_binary))
    if patch_buffer_length > len(patch_binary):
        raise ValueError('Structural patch buffer exceeds its GLB binary chunk.')
    base_binary.extend(patch_binary[:patch_buffer_length])

    for view in patch.get('bufferViews', []):
        view['buffer'] = 0
        view['byteOffset'] = view.get('byteOffset', 0) + binary_offset
    for accessor in patch.get('accessors', []):
        if 'bufferView' in accessor:
            accessor['bufferView'] += offsets['bufferViews']
        for part in ('indices', 'values'):
            sparse = accessor.get('sparse', {}).get(part)
            if sparse:
                sparse['bufferView'] += offsets['bufferViews']
    for image in patch.get('images', []):
        if 'bufferView' in image:
            image['bufferView'] += offsets['bufferViews']
    for texture in patch.get('textures', []):
        if 'source' in texture:
            texture['source'] += offsets['images']
        if 'sampler' in texture:
            texture['sampler'] += offsets['samplers']
    texture_map = {index: index + offsets['textures'] for index in range(len(patch.get('textures', [])))}
    for material in patch.get('materials', []):
        remap_texture_fields(material, texture_map)
    for mesh in patch.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            primitive['attributes'] = {name: index + offsets['accessors'] for name, index in primitive['attributes'].items()}
            if 'indices' in primitive:
                primitive['indices'] += offsets['accessors']
            if 'material' in primitive:
                primitive['material'] += offsets['materials']
            for target in primitive.get('targets', []):
                for name, index in target.items():
                    target[name] = index + offsets['accessors']
    for node in patch.get('nodes', []):
        if 'mesh' in node:
            node['mesh'] += offsets['meshes']
        if 'children' in node:
            node['children'] = [index + offsets['nodes'] for index in node['children']]
    for key in keys:
        base.setdefault(key, []).extend(patch.get(key, []))
    base['scenes'][base.get('scene', 0)]['nodes'].extend(index + offsets['nodes'] for index in patch_roots)
    for extension_key in ('extensionsUsed', 'extensionsRequired'):
        if patch.get(extension_key):
            base[extension_key] = sorted(set(base.get(extension_key, [])) | set(patch[extension_key]))
    base.setdefault('scenes', [])[base.get('scene', 0)].setdefault('extras', {})['interior_revision'] = 'LIBRARY 27.0 whole-house floor connection'
    base['buffers'][0]['byteLength'] = len(base_binary)

    base, base_binary, _ = compact(base, base_binary, expected_pivots=0)
    active = active_node_indices(base)
    names = [base['nodes'][index].get('name') for index in active]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate active upper-floor node names after slab merge.')
    if not SLAB_NODES.issubset(set(names)):
        raise ValueError('The upper GLB is missing its concrete slab or screed.')

    temporary = UPPER_GLB.with_suffix('.interfloor.tmp')
    temporary.write_bytes(write_glb(base, base_binary))
    temporary.replace(UPPER_GLB)
    return {'upper_floor_node_count': len(active), 'added_nodes': sorted(SLAB_NODES), 'floor_offset_m': FLOOR_OFFSET_M}


def main():
    template = (VIEWER / 'viewer_template.html').read_text(encoding='utf-8')
    if 'function Cs(i="all"){let[' in template:
        update_viewer_template()
    elif 'const FLOOR_OFFSET = Number(Gu.floorOffset) || 3.2;' not in template:
        raise ValueError('Viewer template has an unknown controller version; refusing a blind edit.')

    model_report = merge_patch()
    build_viewer(HOUSE_HTML)
    report = {
        'revision': 27,
        'purpose': 'Load both floors, hide the upper floor in the first-floor view, and show the full lower floor beneath the second floor.',
        'interfloor_structure': ['R_L2_STRUCTURAL_SLAB', 'R_L2_SCREED'],
        'source_master_modified': False,
        'upper_viewer_glb_updated': True,
        'both_floors_embedded': True,
        'upper_stair_duplicate_hidden': True,
        'first_person_uses_both_levels': True,
        'floor_aware_cutaway': True,
        **model_report,
    }
    report_path = PROJECT / 'data' / 'revision27_report.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
