(() => {
  const api = window.VIEWER_TEST;
  if (!api) return;

  const Vector3 = api.Vector3;
  const scene = api.scene;
  const camera = api.camera;
  const renderer = api.renderer;
  const button = document.querySelector('#walk-toggle');
  const help = document.querySelector('#walk-help');
  const status = document.querySelector('#status');
  const fovControl = document.createElement('label');
  fovControl.id = 'walk-fov-control';
  fovControl.innerHTML = 'Поле зору <span id="walk-fov-value">85°</span><input id="walk-fov" type="range" min="65" max="95" value="85" step="1">';
  button.insertAdjacentElement('afterend', fovControl);
  const sidebarModeStyle = document.createElement('style');
  sidebarModeStyle.textContent = `
    body.walk-mode aside > p{display:none!important}
    #walk-fov-control{display:none;margin:10px 0 4px;font-size:13px}
    body.walk-mode #walk-fov-control{display:block}
    #walk-fov-value{float:right;font-variant-numeric:tabular-nums;color:#665a46}
    #walk-fov{display:block;width:100%;margin:8px 0 0;accent-color:#665a46}
  `;
  document.head.append(sidebarModeStyle);
  const fovSlider = fovControl.querySelector('#walk-fov');
  const fovValue = fovControl.querySelector('#walk-fov-value');
  fovSlider.addEventListener('input', () => {
    walkFov = Number(fovSlider.value);
    fovValue.textContent = `${walkFov}°`;
    if (active) {
      camera.fov = walkFov;
      camera.updateProjectionMatrix();
      api.markDirty();
    }
  });
  const cellSize = 0.5;
  const playerRadius = 0.19;
  const eyeHeight = 1.62;
  const playerHeight = 1.78;
  const floorOffset = 3.2;
  const keyState = new Set();

  let active = false;
  let initializing = false;
  let savedClip = true;
  let savedFov = camera.fov;
  let floorModels = [];
  let duplicatedStairs = [];
  let surfaces = new Map();
  let walls = new Map();
  let obstacles = new Map();
  let feetY = 0;
  let yaw = 0;
  let pitch = 0;
  let previousTime = 0;
  let dragLooking = false;
  let lastPointerX = 0;
  let lastPointerY = 0;
  let walkFov = 85;

  const cellKey = (x, z) => `${x},${z}`;
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  function addToGrid(grid, minX, maxX, minZ, maxZ, item) {
    const x0 = Math.floor(minX / cellSize);
    const x1 = Math.floor(maxX / cellSize);
    const z0 = Math.floor(minZ / cellSize);
    const z1 = Math.floor(maxZ / cellSize);
    for (let x = x0; x <= x1; x++) {
      for (let z = z0; z <= z1; z++) {
        const key = cellKey(x, z);
        if (!grid.has(key)) grid.set(key, []);
        grid.get(key).push(item);
      }
    }
  }

  function triangleIndices(mesh) {
    const position = mesh.geometry.attributes.position;
    const index = mesh.geometry.index;
    const count = index ? index.count : position.count;
    const triangles = [];
    for (let offset = 0; offset + 2 < count; offset += 3) {
      triangles.push(index
        ? [index.getX(offset), index.getX(offset + 1), index.getX(offset + 2)]
        : [offset, offset + 1, offset + 2]);
    }
    return triangles;
  }

  function worldPoint(mesh, position, index) {
    return new Vector3(position.getX(index), position.getY(index), position.getZ(index))
      .applyMatrix4(mesh.matrixWorld);
  }

  function addSurfaceTriangle(a, b, c) {
    const triangle = {
      a: { x: a.x, y: a.y, z: a.z },
      b: { x: b.x, y: b.y, z: b.z },
      c: { x: c.x, y: c.y, z: c.z },
    };
    const minX = Math.min(a.x, b.x, c.x);
    const maxX = Math.max(a.x, b.x, c.x);
    const minZ = Math.min(a.z, b.z, c.z);
    const maxZ = Math.max(a.z, b.z, c.z);
    addToGrid(surfaces, minX, maxX, minZ, maxZ, triangle);
  }

  function wallSegments(mesh, merged) {
    const position = mesh.geometry.attributes.position;
    const a = new Vector3();
    const b = new Vector3();
    const c = new Vector3();
    for (const ids of triangleIndices(mesh)) {
      a.copy(worldPoint(mesh, position, ids[0]));
      b.copy(worldPoint(mesh, position, ids[1]));
      c.copy(worldPoint(mesh, position, ids[2]));
      const ux = b.x - a.x;
      const uy = b.y - a.y;
      const uz = b.z - a.z;
      const vx = c.x - a.x;
      const vy = c.y - a.y;
      const vz = c.z - a.z;
      const nx = uy * vz - uz * vy;
      const ny = uz * vx - ux * vz;
      const nz = ux * vy - uy * vx;
      const length = Math.hypot(nx, ny, nz);
      if (!length || Math.abs(ny) / length > 0.2) continue;

      const unique = [];
      for (const point of [a, b, c]) {
        if (!unique.some(other => Math.hypot(point.x - other.x, point.z - other.z) < 0.015)) {
          unique.push(point);
        }
      }
      if (unique.length !== 2) continue;
      const [p, q] = unique;
      const segmentLength = Math.hypot(q.x - p.x, q.z - p.z);
      if (segmentLength < 0.025) continue;
      const first = `${Math.round(p.x * 50)},${Math.round(p.z * 50)}`;
      const second = `${Math.round(q.x * 50)},${Math.round(q.z * 50)}`;
      const key = first < second ? `${first}|${second}` : `${second}|${first}`;
      const existing = merged.get(key);
      if (existing) {
        existing.minY = Math.min(existing.minY, a.y, b.y, c.y);
        existing.maxY = Math.max(existing.maxY, a.y, b.y, c.y);
      } else {
        merged.set(key, {
          ax: p.x, az: p.z, bx: q.x, bz: q.z,
          minY: Math.min(a.y, b.y, c.y),
          maxY: Math.max(a.y, b.y, c.y),
        });
      }
    }
  }

  function addObstacleBox(mesh) {
    const geometry = mesh.geometry;
    if (!geometry.boundingBox) geometry.computeBoundingBox();
    if (!geometry.boundingBox) return;
    const box = geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld);
    const width = box.max.x - box.min.x;
    const depth = box.max.z - box.min.z;
    const height = box.max.y - box.min.y;
    if (height < 0.34 || width < 0.055 || depth < 0.055 || width > 4.5 || depth > 4.5) return;
    if (box.max.y < 0.05 || box.min.y > floorOffset + 2.8) return;
    const item = { minX: box.min.x, maxX: box.max.x, minZ: box.min.z, maxZ: box.max.z, minY: box.min.y, maxY: box.max.y };
    addToGrid(obstacles, item.minX, item.maxX, item.minZ, item.maxZ, item);
  }

  function isPartOf(mesh, name) {
    for (let node = mesh; node; node = node.parent) {
      if (node.name === name || node.userData?.name === name) return true;
    }
    return false;
  }

  function isDoorPart(mesh) {
    for (let node = mesh; node; node = node.parent) {
      if (`${node.name || ''} ${node.userData?.name || ''}`.toLowerCase().includes('door')) return true;
    }
    return false;
  }

  function isDesignPart(mesh) {
    for (let node = mesh; node; node = node.parent) {
      if (`${node.name || ''} ${node.userData?.name || ''}`.includes('PART_DESIGN_')) return true;
    }
    return false;
  }

  function buildNavigation() {
    surfaces = new Map();
    walls = new Map();
    obstacles = new Map();
    const wallMap = new Map();

    for (const { root, floor } of floorModels) {
      root.updateMatrixWorld(true);
      root.traverse(mesh => {
        if (!mesh.isMesh || !mesh.geometry?.attributes?.position) return;
        // These combined second-floor room meshes contain both walls and
        // furnishings. Their bounding boxes cover whole rooms and falsely
        // seal the doors, so use their actual vertical faces as wall lines.
        if (mesh.userData.viewer_walls || (floor === 2 && isDesignPart(mesh))) {
          wallSegments(mesh, wallMap);
          return;
        }
        const isFloor = isPartOf(mesh, `PART_R_L${floor}_FLOOR`);
        const isStairs = isPartOf(mesh, 'PART_R_STAIRS');
        const isSharedStairs = floor === 1 && isStairs;
        if (isFloor || isSharedStairs) {
          const position = mesh.geometry.attributes.position;
          for (const ids of triangleIndices(mesh)) {
            const a = worldPoint(mesh, position, ids[0]);
            const b = worldPoint(mesh, position, ids[1]);
            const c = worldPoint(mesh, position, ids[2]);
            const ux = b.x - a.x;
            const uy = b.y - a.y;
            const uz = b.z - a.z;
            const vx = c.x - a.x;
            const vy = c.y - a.y;
            const vz = c.z - a.z;
            const normalY = uz * vx - ux * vz;
            const normalLength = Math.hypot(uy * vz - uz * vy, normalY, ux * vy - uy * vx);
            if (normalLength && normalY / normalLength > 0.55) addSurfaceTriangle(a, b, c);
          }
          return;
        }
        if (isStairs) return;
        // Door leaves and frames are modeled as closed bounding boxes even
        // when the rendered leaf is open; let the wall opening define passage.
        if (isDoorPart(mesh)) return;
        addObstacleBox(mesh);
      });
    }

    for (const segment of wallMap.values()) {
      addToGrid(walls,
        Math.min(segment.ax, segment.bx), Math.max(segment.ax, segment.bx),
        Math.min(segment.az, segment.bz), Math.max(segment.az, segment.bz), segment);
    }
  }

  function surfaceAt(x, z, referenceY, rise = 0.23, drop = 0.34) {
    const candidates = surfaces.get(cellKey(Math.floor(x / cellSize), Math.floor(z / cellSize))) || [];
    let best = null;
    for (const { a, b, c } of candidates) {
      const denominator = (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z);
      if (Math.abs(denominator) < 1e-9) continue;
      const u = ((b.z - c.z) * (x - c.x) + (c.x - b.x) * (z - c.z)) / denominator;
      const v = ((c.z - a.z) * (x - c.x) + (a.x - c.x) * (z - c.z)) / denominator;
      const w = 1 - u - v;
      if (u < -1e-5 || v < -1e-5 || w < -1e-5) continue;
      const y = u * a.y + v * b.y + w * c.y;
      if (y > referenceY + rise || y < referenceY - drop) continue;
      if (best === null || y > best) best = y;
    }
    return best;
  }

  function nearbyItems(grid, x, z, radius) {
    const found = new Set();
    const x0 = Math.floor((x - radius) / cellSize);
    const x1 = Math.floor((x + radius) / cellSize);
    const z0 = Math.floor((z - radius) / cellSize);
    const z1 = Math.floor((z + radius) / cellSize);
    for (let ix = x0; ix <= x1; ix++) {
      for (let iz = z0; iz <= z1; iz++) {
        for (const item of grid.get(cellKey(ix, iz)) || []) found.add(item);
      }
    }
    return found;
  }

  function blockedByWall(x, z, y) {
    for (const wall of nearbyItems(walls, x, z, playerRadius)) {
      if (wall.maxY < y + 0.12 || wall.minY > y + playerHeight) continue;
      const dx = wall.bx - wall.ax;
      const dz = wall.bz - wall.az;
      const lengthSquared = dx * dx + dz * dz;
      const t = lengthSquared ? clamp(((x - wall.ax) * dx + (z - wall.az) * dz) / lengthSquared, 0, 1) : 0;
      if (Math.hypot(x - (wall.ax + t * dx), z - (wall.az + t * dz)) < playerRadius) return true;
    }
    return false;
  }

  function blockedByFurniture(x, z, y) {
    for (const box of nearbyItems(obstacles, x, z, playerRadius)) {
      if (box.maxY < y + 0.12 || box.minY > y + playerHeight) continue;
      const closestX = clamp(x, box.minX, box.maxX);
      const closestZ = clamp(z, box.minZ, box.maxZ);
      if (Math.hypot(x - closestX, z - closestZ) < playerRadius) return true;
    }
    return false;
  }

  function positionAllowed(x, z, referenceY) {
    const support = surfaceAt(x, z, referenceY);
    if (support === null || blockedByWall(x, z, support) || blockedByFurniture(x, z, support)) return null;
    return support;
  }

  function findSpawn(floor) {
    const base = floor === 2 ? { x: 8, z: -5.2, y: floorOffset } : { x: 8, z: -5.2, y: 0 };
    const candidates = [];
    for (let x = 5.6; x <= 11.2; x += 0.2) {
      for (let z = -12; z <= -0.2; z += 0.2) {
        const y = surfaceAt(x, z, base.y, 0.25, 0.3);
        if (y !== null) candidates.push({ x, z, y, distance: (x - base.x) ** 2 + (z - base.z) ** 2 });
      }
    }
    const probes = [[0.48, 0], [-0.48, 0], [0, 0.48], [0, -0.48],
      [0.34, 0.34], [0.34, -0.34], [-0.34, 0.34], [-0.34, -0.34]];
    for (const candidate of candidates) {
      if (blockedByWall(candidate.x, candidate.z, candidate.y)
        || blockedByFurniture(candidate.x, candidate.z, candidate.y)) continue;
      candidate.clearance = 0;
      candidate.cardinalClearance = 0;
      for (let i = 0; i < probes.length; i++) {
        const [dx, dz] = probes[i];
        const y = positionAllowed(candidate.x + dx, candidate.z + dz, candidate.y);
        if (y === null || Math.abs(y - candidate.y) > 0.24) continue;
        candidate.clearance++;
        if (i < 4) candidate.cardinalClearance++;
      }
    }
    const freeCandidates = candidates.filter(candidate => Number.isFinite(candidate.clearance));
    freeCandidates.sort((a, b) =>
      b.cardinalClearance - a.cardinalClearance
      || b.clearance - a.clearance
      || a.distance - b.distance);
    const openCandidate = freeCandidates.find(candidate => candidate.cardinalClearance >= 3 && candidate.clearance >= 5)
      || freeCandidates[0];
    if (openCandidate) return openCandidate;
    throw new Error(`Не знайшов вільне місце на ${floor}-му поверсі (${candidates.length} точок підлоги перевірено).`);
  }

  function lockPointer() {
    if (document.pointerLockElement === renderer.domElement) return;
    try {
      const result = renderer.domElement.requestPointerLock();
      if (result?.catch) result.catch(() => {});
    } catch (_) {}
  }

  async function waitForViewer() {
    const started = performance.now();
    while (!window.VIEWER_READY && !window.VIEWER_ERROR) {
      if (performance.now() - started > 120000) throw new Error('Початковий 3D-перегляд не завершив завантаження.');
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    if (window.VIEWER_ERROR) throw new Error(window.VIEWER_ERROR);
  }

  function updatePointerState() {
    const locked = document.pointerLockElement === renderer.domElement;
    if (!locked) keyState.clear();
    help.hidden = !active || locked;
    if (active) {
      status.textContent = locked
        ? 'WASD або стрілки — рух · Q/E — поворот · миша — огляд · Shift — повільніше · Esc — курсор'
        : 'WASD — рух · Q/E — поворот · курсор по 3D або права кнопка + рух — огляд · кнопка вище — вихід';
      if (!locked) help.textContent = 'W/A/S/D або стрілки — рухатися, Q/E — повертатися ліворуч/праворуч, Shift — повільніше. Для огляду веди курсор по 3D; тачпадом можна також затиснути праву кнопку й тягнути.';
    }
    api.markDirty();
  }

  async function enterWalk() {
    if (active || initializing) return;
    initializing = true;
    button.disabled = true;
    const selected = Number(document.querySelector('[data-floor].active')?.dataset.floor || 1);
    savedClip = document.querySelector('#cut')?.checked ?? true;
    savedFov = camera.fov;
    help.hidden = false;
    help.textContent = 'Готую будинок для прогулянки…';
    status.textContent = 'Завантажую обидва поверхи та сходи…';
    button.textContent = 'Завантажую…';
    document.body.classList.add('walk-mode');
    lockPointer();

    try {
      await waitForViewer();
      await api.showFloor(selected);
      await api.showFloor(selected === 1 ? 2 : 1);
      const lower = api.models[1];
      const upper = api.models[2];
      if (!lower || !upper) throw new Error('Не вдалося завантажити обидва поверхи.');

      lower.position.y = 0;
      upper.position.y = floorOffset;
      duplicatedStairs = [];
      upper.traverse(node => {
        if (node.name === 'PART_R_STAIRS') {
          duplicatedStairs.push({ node, visible: node.visible });
          node.visible = false;
        }
      });
      scene.add(lower, upper);
      floorModels = [{ root: lower, floor: 1 }, { root: upper, floor: 2 }];
      scene.updateMatrixWorld(true);
      buildNavigation();

      const spawn = findSpawn(selected);
      feetY = spawn.y;
      camera.position.set(spawn.x, feetY + eyeHeight, spawn.z);
      camera.fov = walkFov;
      camera.updateProjectionMatrix();
      const defaultYaw = selected === 2 ? Math.PI : 0;
      const target = { x: 8, z: -5.2 };
      yaw = Math.hypot(spawn.x - target.x, spawn.z - target.z) < 0.25
        ? defaultYaw
        : Math.atan2(target.x - spawn.x, target.z - spawn.z) + Math.PI;
      pitch = 0;
      camera.rotation.order = 'YXZ';
      camera.rotation.set(pitch, yaw, 0);
      api.controls.enabled = false;
      api.setCut(false);
      for (const { root } of floorModels) {
        root.traverse(node => {
          if (node.isMesh && node.userData.viewer_walls) {
            for (const material of Array.isArray(node.material) ? node.material : [node.material]) {
              material.clippingPlanes = [];
              material.needsUpdate = true;
            }
          }
        });
      }
      api.setInternalMode('walk');
      active = true;
      previousTime = performance.now();
      button.textContent = 'Вийти з прогулянки';
      updatePointerState();
    } catch (error) {
      active = false;
      if (document.pointerLockElement === renderer.domElement) document.exitPointerLock();
      scene.remove(...floorModels.map(item => item.root));
      if (api.models[2]) api.models[2].position.y = 0;
      for (const { node, visible } of duplicatedStairs) node.visible = visible;
      duplicatedStairs = [];
      floorModels = [];
      document.body.classList.remove('walk-mode');
      api.controls.enabled = true;
      api.setInternalMode('orbit');
      api.setCut(savedClip);
      camera.fov = savedFov;
      camera.updateProjectionMatrix();
      help.hidden = true;
      button.textContent = 'Прогулянка по будинку';
      status.textContent = 'Не вдалося підготувати режим прогулянки.';
      console.error(error);
      try { await api.showFloor(selected); } catch (_) {}
    } finally {
      initializing = false;
      button.disabled = false;
      api.markDirty();
    }
  }

  async function exitWalk() {
    if (!active) return;
    const selected = feetY >= floorOffset / 2 ? 2 : 1;
    active = false;
    keyState.clear();
    if (document.pointerLockElement === renderer.domElement) document.exitPointerLock();
    scene.remove(...floorModels.map(item => item.root));
    const upper = api.models[2];
    if (upper) upper.position.y = 0;
    for (const { node, visible } of duplicatedStairs) node.visible = visible;
    duplicatedStairs = [];
    floorModels = [];
    api.controls.enabled = true;
    api.setInternalMode('orbit');
    api.setCut(savedClip);
    camera.fov = savedFov;
    camera.updateProjectionMatrix();
    document.body.classList.remove('walk-mode');
    button.textContent = 'Прогулянка по будинку';
    help.hidden = true;
    await api.showFloor(selected);
    api.markDirty();
  }

  function attemptPosition(x, z) {
    const support = positionAllowed(x, z, feetY);
    if (support === null) return false;
    feetY = support;
    camera.position.set(x, feetY + eyeHeight, z);
    return true;
  }

  function move(dx, dz) {
    const distance = Math.hypot(dx, dz);
    const steps = Math.max(1, Math.ceil(distance / 0.055));
    const stepX = dx / steps;
    const stepZ = dz / steps;
    let changed = false;
    for (let i = 0; i < steps; i++) {
      const nextX = camera.position.x + stepX;
      const nextZ = camera.position.z + stepZ;
      if (attemptPosition(nextX, nextZ)) {
        changed = true;
      } else {
        const movedX = attemptPosition(nextX, camera.position.z);
        const movedZ = attemptPosition(camera.position.x, nextZ);
        changed ||= movedX || movedZ;
      }
    }
    return changed;
  }

  function update(deltaTime) {
    if (!active) return false;
    const forwardInput = Number(keyState.has('KeyW') || keyState.has('ArrowUp'))
      - Number(keyState.has('KeyS') || keyState.has('ArrowDown'));
    const rightInput = Number(keyState.has('KeyD') || keyState.has('ArrowRight'))
      - Number(keyState.has('KeyA') || keyState.has('ArrowLeft'));
    const turnInput = Number(keyState.has('KeyQ')) - Number(keyState.has('KeyE'));
    if (!forwardInput && !rightInput && !turnInput) return false;
    if (turnInput) {
      yaw += turnInput * 1.8 * deltaTime;
      camera.rotation.set(pitch, yaw, 0, 'YXZ');
    }
    if (!forwardInput && !rightInput) return true;
    const magnitude = Math.hypot(forwardInput, rightInput);
    const speed = keyState.has('ShiftLeft') || keyState.has('ShiftRight') ? 0.9 : 2.35;
    const distance = speed * deltaTime / magnitude;
    const dx = -Math.sin(yaw) * forwardInput * distance + Math.cos(yaw) * rightInput * distance;
    const dz = -Math.cos(yaw) * forwardInput * distance - Math.sin(yaw) * rightInput * distance;
    return move(dx, dz) || Boolean(turnInput);
  }

  button.addEventListener('click', () => active ? void exitWalk() : void enterWalk());
  renderer.domElement.addEventListener('click', () => {
    if (active && document.pointerLockElement !== renderer.domElement) lockPointer();
  });
  function applyLook(deltaX, deltaY) {
    yaw -= deltaX * 0.0022;
    pitch = clamp(pitch - deltaY * 0.0022, -1.38, 1.38);
    camera.rotation.set(pitch, yaw, 0, 'YXZ');
    api.markDirty();
  }
  document.addEventListener('pointerlockchange', updatePointerState);
  document.addEventListener('mousemove', event => {
    if (!active) return;
    if (document.pointerLockElement === renderer.domElement) {
      applyLook(event.movementX, event.movementY);
    } else if (dragLooking) {
      applyLook(event.clientX - lastPointerX, event.clientY - lastPointerY);
      lastPointerX = event.clientX;
      lastPointerY = event.clientY;
    } else if (event.target === renderer.domElement) {
      // Touchpads can fail to acquire pointer lock in some browser contexts.
      // Track the pointer while it remains over the 3D view as a fallback.
      applyLook(event.movementX || 0, event.movementY || 0);
    }
  });
  renderer.domElement.addEventListener('pointerdown', event => {
    if (!active || document.pointerLockElement === renderer.domElement || event.button !== 2) return;
    event.preventDefault();
    dragLooking = true;
    lastPointerX = event.clientX;
    lastPointerY = event.clientY;
    try { renderer.domElement.setPointerCapture(event.pointerId); } catch (_) {}
  });
  document.addEventListener('pointerup', () => { dragLooking = false; });
  document.addEventListener('pointercancel', () => { dragLooking = false; });
  renderer.domElement.addEventListener('contextmenu', event => {
    if (active) event.preventDefault();
  });
  document.addEventListener('keydown', event => {
    if (!active || !['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyQ', 'KeyE', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ShiftLeft', 'ShiftRight'].includes(event.code)) return;
    if (event.target instanceof HTMLElement && event.target.closest('input,button,select,textarea')) return;
    event.preventDefault();
    keyState.add(event.code);
  });
  document.addEventListener('keyup', event => keyState.delete(event.code));
  window.addEventListener('blur', () => keyState.clear());

  window.HOUSE_WALK = {
    get active() { return active; },
    update() {
      const now = performance.now();
      const deltaTime = Math.min((now - previousTime) / 1000, 0.05);
      previousTime = now;
      return update(deltaTime);
    },
  };
})();
