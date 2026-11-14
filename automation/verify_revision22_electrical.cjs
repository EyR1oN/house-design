const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class SceneNode {
  constructor(name, options = {}) {
    this.name = name;
    this.isMesh = options.mesh ?? false;
    this.visible = options.visible ?? true;
    this.children = [];
    this.parent = null;
    for (const child of options.children ?? []) this.add(child);
  }
  add(child) { child.parent = this; this.children.push(child); return child; }
  traverse(fn) { fn(this); for (const child of this.children) child.traverse(fn); }
}

function makeFloor(level) {
  const root = new SceneNode('Scene');
  root.add(new SceneNode('Walls', { mesh: true }));
  root.add(new SceneNode(`PART_R_L${level}_FLOOR`, { mesh: true }));
  root.add(new SceneNode(`PART_Electrical_L${level}`, { mesh: true }));
  root.add(new SceneNode('R18_Ceiling_L2', { mesh: true }));
  if (level === 2) {
    root.add(new SceneNode('E2_080_SOCKET', { mesh: true }));
    root.add(new SceneNode('E2_082_SOCKET', { mesh: true }));
    root.add(new SceneNode('E2_083_SWITCH', { mesh: true }));
    root.add(new SceneNode('E2_084_SOCKET', { mesh: true }));
  } else {
    root.add(new SceneNode('E1_004_SWITCH', { mesh: true }));
  }
  root.add(new SceneNode('LIB_Door_room', { children: [new SceneNode('door_leaf', { mesh: true })] }));
  root.add(new SceneNode('LIB_Pendant_Office', { children: [new SceneNode('pendant_bulb', { mesh: true })] }));
  root.add(new SceneNode('LIB_Upper_Bath_Sconce', { mesh: true }));
  root.add(new SceneNode('LIB_Office_Task_Lamp_1', { mesh: true }));
  root.add(new SceneNode('LIB_Office_Task_Lamp_2', { mesh: true }));
  root.add(new SceneNode('LIB_Child_Bed', { mesh: true }));
  root.add(new SceneNode('LIB_Office_Chair', { mesh: true }));
  root.add(new SceneNode('PART_R_STAIRS', { mesh: true, visible: false }));
  return root;
}

const inserted = new Map();
function element(tag) {
  return {
    tag, style: {}, listeners: {}, hidden: false,
    setAttribute(key, value) { this[key] = value; },
    addEventListener(key, fn) { this.listeners[key] = fn; },
    insertAdjacentElement(_where, child) { inserted.set(child.id, child); },
    click() { this.listeners.click?.(); },
  };
}
const walkButton = element('button');
walkButton.id = 'walk-toggle';
const document = {
  body: { classList: { toggle() {}, add() {}, remove() {} } },
  head: { append() {} },
  createElement: element,
  querySelector(selector) { return selector === '#walk-toggle' ? walkButton : null; },
};
const api = {
  models: { 1: makeFloor(1) },
  async showFloor(level) { this.models[level] ??= makeFloor(level); return level; },
  markDirty() {},
};
const window = { VIEWER_TEST: api };
vm.runInNewContext(fs.readFileSync('House_Browser_Viewer/electrical_mode.js', 'utf8'), { window, document, Map, Set, String });

(async () => {
  const toggle = inserted.get('electrical-toggle');
  assert.ok(toggle, 'Electrical mode button is created');
  const nodes = {};
  api.models[1].traverse(n => { if (n.name) nodes[n.name] = n; });
  toggle.click();
  for (const name of ['Walls', 'PART_R_L1_FLOOR', 'PART_Electrical_L1', 'R18_Ceiling_L2', 'E1_004_SWITCH', 'door_leaf', 'pendant_bulb', 'LIB_Upper_Bath_Sconce']) {
    assert.equal(nodes[name].visible, true, `${name} remains visible in electrical mode`);
  }
  for (const name of ['LIB_Office_Task_Lamp_1', 'LIB_Office_Task_Lamp_2', 'LIB_Child_Bed', 'LIB_Office_Chair']) {
    assert.equal(nodes[name].visible, false, `${name} is hidden in electrical mode`);
  }
  await api.showFloor(2);
  const upper = {};
  api.models[2].traverse(n => { if (n.name) upper[n.name] = n; });
  for (const name of ['E2_080_SOCKET', 'E2_082_SOCKET', 'E2_083_SWITCH', 'E2_084_SOCKET', 'LIB_Pendant_Office', 'LIB_Upper_Bath_Sconce']) {
    assert.equal(upper[name].visible, true, `${name} remains visible after a floor change`);
  }
  for (const name of ['LIB_Office_Task_Lamp_1', 'LIB_Office_Task_Lamp_2', 'LIB_Child_Bed', 'LIB_Office_Chair']) {
    assert.equal(upper[name].visible, false, `${name} remains hidden after a floor change`);
  }
  toggle.click();
  assert.equal(nodes.LIB_Office_Task_Lamp_1.visible, true, 'First task lamp restores when leaving mode');
  assert.equal(nodes.LIB_Office_Task_Lamp_2.visible, true, 'Second task lamp restores when leaving mode');
  assert.equal(nodes.LIB_Child_Bed.visible, true, 'Furniture restores when leaving mode');
  assert.equal(nodes.PART_R_STAIRS.visible, false, 'Preexisting hidden state is preserved');
  const result = {
    revision: 22,
    office_task_lamps_hidden: true,
    stationary_lighting_visible: true,
    child_room_electrical_visible: true,
    furniture_restored: true,
    preexisting_visibility_preserved: true,
    visual_browser_screenshot: 'not captured; local file URL inspection is restricted in this session',
  };
  fs.writeFileSync('House_Library_Design/data/revision22_browser_verification.json', `${JSON.stringify(result, null, 2)}\n`);
  console.log(JSON.stringify(result));
})().catch(error => { console.error(error); process.exit(1); });
