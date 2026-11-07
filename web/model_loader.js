// Download only the selected floor. Gzip changes transport size, never geometry.
window.loadHouseModel = async function (floor) {
  const item = window.HOUSE_DATA.models[String(floor)];
  if (!item || !Array.isArray(item.parts)) throw new Error('Модель поверху відсутня.');
  if (typeof DecompressionStream === 'undefined') {
    throw new Error('Для перегляду потрібен актуальний Chrome, Edge, Firefox або Safari.');
  }
  let completed = 0;
  const parts = await Promise.all(item.parts.map(async (url) => {
    const response = await fetch(url, { cache: 'force-cache' });
    if (!response.ok) throw new Error('Не вдалося завантажити поверх. Оновіть сторінку.');
    const part = await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
    completed += part.byteLength;
    const status = document.getElementById('loading');
    if (status) status.textContent = 'Завантажую ' + floor + ' поверх: ' + Math.round(completed / item.bytes * 100) + '%';
    return part;
  }));
  const result = new Uint8Array(parts.reduce((size, part) => size + part.byteLength, 0));
  let offset = 0;
  for (const part of parts) { result.set(new Uint8Array(part), offset); offset += part.byteLength; }
  if (result.byteLength !== item.bytes) throw new Error('Модель завантажилась не повністю.');
  const hash = await crypto.subtle.digest('SHA-256', result);
  const digest = Array.from(new Uint8Array(hash), value => value.toString(16).padStart(2, '0')).join('');
  if (digest !== item.sha256) throw new Error('Помилка цілісності моделі. Оновіть сторінку.');
  return result.buffer;
};
