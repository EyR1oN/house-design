(() => {
  const button = document.createElement('button');
  button.id = 'pantry-toggle';
  button.className = 'wide';
  button.textContent = 'Відкрити кутову шафу';
  document.querySelector('#photos-button').before(button);
  let amount = 0, busy = false, targets = [];
  const clamp = x => Math.max(0, Math.min(1, x));
  function collect() {
    const found = [];
    window.VIEWER_TEST.scene.traverse(node => {
      if (node.userData.pantry_role === 'front' || node.userData.pantry_role === 'rear') {
        node.userData.pantryClosedPosition ||= node.position.clone();
        found.push(node);
      }
    });
    if (found.length) targets = found;
    return targets;
  }
  function pose(u) {
    const front = clamp(u / .55), rear = clamp((u - .55) / .45);
    const lateral = clamp(rear / .8), approach = clamp((rear - .8) / .2);
    for (const node of targets) {
      node.position.copy(node.userData.pantryClosedPosition);
      if (node.userData.pantry_role === 'front') node.position.z -= .66 * front;
      else { node.position.x -= .60 * lateral; node.position.z -= .14 * approach; }
    }
    amount = u;
    const v = window.VIEWER_TEST;
    v.renderer.render(v.scene, v.camera);
  }
  function sync() {
    button.hidden = !document.querySelector('[data-floor="1"]').classList.contains('active');
    button.textContent = amount > .5 ? 'Закрити кутову шафу' : 'Відкрити кутову шафу';
  }
  button.onclick = () => {
    if (busy || !window.VIEWER_READY || !collect().length) return;
    busy = true; button.disabled = true;
    const from = amount, to = amount > .5 ? 0 : 1, start = performance.now();
    function frame(now) {
      const t = clamp((now - start) / 1400);
      pose(from + (to - from) * t);
      if (t < 1) requestAnimationFrame(frame);
      else { busy = false; button.disabled = false; sync(); }
    }
    requestAnimationFrame(frame);
  };
  new MutationObserver(sync).observe(document.querySelector('[data-floor="1"]'), {attributes: true, attributeFilter: ['class']});
  sync();
  window.CORNER_PANTRY = {
    setOpen(u) { if (!busy && collect().length) { pose(clamp(u)); sync(); } },
    getState() { return {amount, busy, movingObjects: targets.length}; }
  };
})();
