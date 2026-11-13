(() => {
  const api = window.VIEWER_TEST;
  const walkButton = document.querySelector('#walk-toggle');
  if (!api || !api.models || !walkButton) return;

  const button = document.createElement('button');
  button.id = 'electrical-toggle';
  button.className = 'wide';
  button.type = 'button';
  button.textContent = 'Режим електрика';
  button.setAttribute('aria-pressed', 'false');
  walkButton.insertAdjacentElement('afterend', button);

  const help = document.createElement('p');
  help.id = 'electrical-help';
  help.className = 'subtle';
  help.hidden = true;
  help.innerHTML = '<strong>Електроточки на сцені</strong><br>Розетки, вимикачі, підключення, точки вентилятора та світильники.<br>Меблі й декор приховані. Позиції електрики попередні — PROPOSED, не виконавча схема.';
  button.insertAdjacentElement('afterend', help);

  const style = document.createElement('style');
  style.textContent = `
    #electrical-help{margin:8px 0;padding:10px 11px;border-left:3px solid #b78743;background:#f0eadf;line-height:1.45}
    #electrical-help[hidden]{display:none!important}
    body.walk-mode #electrical-help:not([hidden]){display:block!important}
    body.electrical-mode #pantry-toggle{display:none!important}
    #electrical-toggle[aria-pressed="true"]{background:#665a46;color:#fff;border-color:#665a46}
  `;
  document.head.append(style);

  const changedVisibility = new Map();
  let enabled = false;

  function keepByName(name) {
    if (!name) return null;
    if (/^(?:Walls|PART_R_|PART_Electrical_|E[12]_)/.test(name)) return true;
    if (/^(?:R_STAIR_|R3_Stair_|R3_LED_|R7_TV_|R18_Ceiling_)/.test(name)) return true;
    if (name === 'Corner_LED_strip' || name === 'PART_DESIGN_Lighting_Decor') return true;
    if (/^LIB_Door_/i.test(name)) return true;
    if (/^LIB_.*(?:lamp|pendant|sconce|light)/i.test(name)) return true;
    if (/^(?:LIB_|PART_DESIGN_)/.test(name)) return false;
    return null;
  }

  function hideFurniture(node) {
    if (!node.name || node.name === 'Scene') return;
    if (changedVisibility.has(node)) return;
    changedVisibility.set(node, node.visible);
    node.visible = false;
  }

  function applyToModel(root) {
    if (!root || typeof root.traverse !== 'function') return;
    root.traverse(node => {
      let kind = keepByName(node.name);
      if (kind === null && node.parent) {
        let parent = node.parent;
        while (parent && kind === null) {
          kind = keepByName(parent.name);
          parent = parent.parent;
        }
      }
      if (kind === false || (kind === null && node.isMesh)) hideFurniture(node);
    });
  }

  function applyToLoadedModels() {
    const visited = new Set();
    for (const model of Object.values(api.models)) {
      if (!model || visited.has(model)) continue;
      visited.add(model);
      applyToModel(model);
    }
    api.markDirty?.();
  }

  const originalShowFloor = api.showFloor.bind(api);
  api.showFloor = async (...args) => {
    const result = await originalShowFloor(...args);
    if (enabled) applyToLoadedModels();
    return result;
  };

  function setEnabled(value) {
    enabled = value;
    if (enabled) {
      applyToLoadedModels();
    } else {
      for (const [node, visible] of changedVisibility) node.visible = visible;
      changedVisibility.clear();
      api.markDirty?.();
    }
    document.body.classList.toggle('electrical-mode', enabled);
    button.setAttribute('aria-pressed', String(enabled));
    button.textContent = enabled ? 'Вийти з режиму електрика' : 'Режим електрика';
    help.hidden = !enabled;
  }

  button.addEventListener('click', () => setEnabled(!enabled));
  window.HOUSE_ELECTRICAL_MODE = {
    get active() { return enabled; },
    setActive: setEnabled,
  };
})();
