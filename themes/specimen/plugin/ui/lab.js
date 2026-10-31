// Specimen Lab: УФ-лампа над чатом, пушистик и шкаф найденных экспонатов.
(function () {
  var BASE = '/plugins/com.tokii.specimen-lab/ui/';
  var VAR = 'specimenLab';
  var HIDDEN_W = 1080;
  var HIDDEN_H = 1920;
  // Где спрятаны экспонаты на скрытом слое (доли его ширины и высоты)
  var SPECIMENS = [
    { id: 'cat', name: 'Felis lucens', x: 0.70, y: 0.20 },
    { id: 'fish', name: 'Gymnocorymbus vitreus', x: 0.27, y: 0.40 },
    { id: 'ribs', name: 'Thorax humanus', x: 0.55, y: 0.56 },
    { id: 'wings', name: 'Angelus oblitus', x: 0.26, y: 0.78 },
    { id: 'mint', name: 'Cervulus menthae', x: 0.74, y: 0.84 },
  ];
  var FIND_RADIUS = 34;  // px от центра лампы
  var FIND_HOLD = 700;   // мс над экспонатом

  var i18n = tavo.plugin.i18n;
  function t(key, params) { return i18n.t(key, params); }
  function $(id) { return document.getElementById(id); }

  var lamp = $('spl-lamp');
  var hiddenEl = $('spl-hidden');
  var modeEl = $('spl-mode');
  var pet = $('spl-pet');
  var say = $('spl-say');
  var cab = $('spl-cab');

  var state = { lamp: null, pet: null, mode: 'uv', found: {} };
  var insets = { topBar: 56, bottomInput: 80 };

  function cfg(key) {
    var v = tavo.plugin.config.get(key);
    return v !== false;
  }

  function toast(text) {
    try { tavo.utils.toast(text); } catch (e) { /* best-effort */ }
  }

  // ---------- Сохранение ----------
  var saveTimer = null;
  function save() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      tavo.variable.set(VAR, state, 'global').catch(function () {});
    }, 400);
  }

  // ---------- Геометрия ----------
  function bounds(w, h) {
    return {
      minX: 4,
      maxX: window.innerWidth - w - 4,
      minY: (insets.topBar || 0) + 4,
      maxY: window.innerHeight - (insets.bottomInput || 0) - h - 4,
    };
  }
  function clamp(pos, el) {
    var b = bounds(el.offsetWidth || 100, el.offsetHeight || 100);
    return {
      x: Math.max(b.minX, Math.min(b.maxX, pos.x)),
      y: Math.max(b.minY, Math.min(b.maxY, pos.y)),
    };
  }
  function place(el, pos) {
    el.style.left = pos.x + 'px';
    el.style.top = pos.y + 'px';
  }
  // Скрытый слой растянут на весь экран по принципу cover
  function layer() {
    var vw = window.innerWidth, vh = window.innerHeight;
    var s = Math.max(vw / HIDDEN_W, vh / HIDDEN_H);
    var w = HIDDEN_W * s, h = HIDDEN_H * s;
    return { w: w, h: h, x: (vw - w) / 2, y: (vh - h) / 2 };
  }

  // ---------- Лампа ----------
  function renderLamp() {
    var p = state.lamp;
    place(lamp, p);
    var L = layer();
    hiddenEl.style.backgroundSize = L.w + 'px ' + L.h + 'px';
    hiddenEl.style.backgroundPosition = (L.x - p.x - 2) + 'px ' + (L.y - p.y - 2) + 'px';
    lamp.classList.toggle('spl-xray', state.mode === 'xray');
    modeEl.textContent = t(state.mode === 'xray' ? 'ui.mode.xray' : 'ui.mode.uv');
    lookAtLamp();
    checkFind();
  }

  var nearId = null, nearSince = 0, findTimer = null;
  function checkFind() {
    var L = layer();
    var cx = state.lamp.x + lamp.offsetWidth / 2;
    var cy = state.lamp.y + lamp.offsetHeight / 2;
    var hit = null;
    SPECIMENS.forEach(function (s) {
      var sx = L.x + s.x * L.w, sy = L.y + s.y * L.h;
      if (Math.hypot(sx - cx, sy - cy) < FIND_RADIUS) hit = s;
    });
    var id = hit && !state.found[hit.id] ? hit.id : null;
    lamp.classList.toggle('spl-near', !!id);
    if (id !== nearId) {
      nearId = id;
      nearSince = Date.now();
      clearTimeout(findTimer);
      if (id) findTimer = setTimeout(function () { collect(hit); }, FIND_HOLD);
    }
  }

  function collect(s) {
    if (state.found[s.id]) return;
    state.found[s.id] = Date.now();
    nearId = null;
    lamp.classList.remove('spl-near');
    lamp.classList.remove('spl-flash');
    void lamp.offsetWidth;
    lamp.classList.add('spl-flash');
    hop();
    var n = Object.keys(state.found).length;
    toast(n === SPECIMENS.length ? t('ui.all') : t('ui.found', { name: s.name }));
    save();
    if (!cab.hidden) renderCabinet();
  }

  // ---------- Перетаскивание (палец, мышь, перо) ----------
  function draggable(el, key, onTap) {
    var drag = null;
    function start(x, y) {
      drag = { x: x, y: y, ox: state[key].x, oy: state[key].y, moved: false };
    }
    function move(x, y) {
      if (!drag) return;
      var dx = x - drag.x, dy = y - drag.y;
      if (!drag.moved && Math.hypot(dx, dy) < 6) return;
      drag.moved = true;
      el.classList.add('spl-dragging');
      state[key] = clamp({ x: drag.ox + dx, y: drag.oy + dy }, el);
      key === 'lamp' ? renderLamp() : (place(el, state[key]), lookAtLamp());
    }
    function end() {
      if (!drag) return;
      var tap = !drag.moved;
      drag = null;
      el.classList.remove('spl-dragging');
      if (tap) onTap(); else save();
    }
    el.addEventListener('touchstart', function (e) { var p = e.touches[0]; start(p.clientX, p.clientY); e.preventDefault(); }, { passive: false });
    el.addEventListener('touchmove', function (e) { var p = e.touches[0]; move(p.clientX, p.clientY); e.preventDefault(); }, { passive: false });
    el.addEventListener('touchend', function (e) { end(); e.preventDefault(); }, { passive: false });
    el.addEventListener('touchcancel', function () { drag = null; });
    el.addEventListener('mousedown', function (e) {
      start(e.clientX, e.clientY);
      function mm(ev) { move(ev.clientX, ev.clientY); }
      function mu() { document.removeEventListener('mousemove', mm); document.removeEventListener('mouseup', mu); end(); }
      document.addEventListener('mousemove', mm);
      document.addEventListener('mouseup', mu);
      e.preventDefault();
    });
  }

  // ---------- Пушистик ----------
  function lookAtLamp() {
    if (!state.pet || !state.lamp) return;
    var petCx = state.pet.x + pet.offsetWidth / 2;
    var lampCx = state.lamp.x + lamp.offsetWidth / 2;
    pet.classList.toggle('spl-left', lampCx < petCx - 10);
  }
  function hop() {
    pet.classList.remove('spl-hop');
    void pet.offsetWidth;
    pet.classList.add('spl-hop');
  }
  var sayTimer = null;
  function speak() {
    var n = 1 + Math.floor(Math.random() * 6);
    say.textContent = t('pet.' + n);
    say.hidden = false;
    clearTimeout(sayTimer);
    sayTimer = setTimeout(function () { say.hidden = true; }, 2200);
  }

  // ---------- Шкаф ----------
  function renderCabinet() {
    $('spl-cab-title').textContent = t('ui.cabinet');
    $('spl-cab-count').textContent = t('ui.count', { found: Object.keys(state.found).length, total: SPECIMENS.length });
    $('spl-hint').textContent = t('ui.hint');
    $('spl-close').textContent = t('ui.close');
    $('spl-reset').textContent = t('ui.reset');
    var grid = $('spl-grid');
    grid.textContent = '';
    SPECIMENS.forEach(function (s, i) {
      var found = state.found[s.id];
      var fig = document.createElement('figure');
      fig.className = 'spl-card' + (found ? '' : ' spl-missing');
      fig.style.margin = '0';
      var img = document.createElement('img');
      img.src = BASE + 'card-' + s.id + '.jpg';
      img.alt = '';
      var cap = document.createElement('figcaption');
      cap.textContent = 'Nº 0' + (i + 1) + ' ';
      var em = document.createElement('em');
      em.textContent = found ? s.name : t('ui.unknown');
      cap.appendChild(em);
      fig.appendChild(img);
      fig.appendChild(cap);
      grid.appendChild(fig);
    });
  }
  function toggleCabinet(open) {
    cab.hidden = !open;
    if (open) renderCabinet();
  }

  // ---------- Начальная раскладка ----------
  function defaults() {
    var vw = window.innerWidth, vh = window.innerHeight;
    return {
      lamp: { x: vw - 132 - 16, y: (insets.topBar || 56) + 90 },
      pet: { x: 12, y: vh - (insets.bottomInput || 80) - 64 - 10 },
    };
  }
  function applyVisibility() {
    lamp.hidden = !cfg('showLamp');
    pet.hidden = !cfg('showPet');
  }
  function layout() {
    var d = defaults();
    state.lamp = clamp(state.lamp || d.lamp, lamp);
    state.pet = clamp(state.pet || d.pet, pet);
    place(pet, state.pet);
    renderLamp();
  }

  draggable(lamp, 'lamp', function () {
    state.mode = state.mode === 'xray' ? 'uv' : 'xray';
    renderLamp();
    save();
  });
  draggable(pet, 'pet', function () {
    speak();
    hop();
    toggleCabinet(cab.hidden);
  });
  $('spl-close').addEventListener('click', function () { toggleCabinet(false); });
  $('spl-reset').addEventListener('click', async function () {
    var res = null;
    try {
      res = await tavo.utils.ask({
        question: t('ui.resetAsk'),
        options: [{ value: 'yes', label: t('ui.yes') }, { value: 'no', label: t('ui.no') }],
        allowOther: false,
      });
    } catch (e) { /* диалог недоступен — ничего не сбрасываем */ }
    if (!res || res.answer !== 'yes') return;
    state = { lamp: null, pet: null, mode: 'uv', found: {} };
    layout();
    renderCabinet();
    save();
  });

  window.addEventListener('resize', layout);
  if (tavo.ui && typeof tavo.ui.getInsets === 'function') {
    insets = tavo.ui.getInsets() || insets;
    tavo.ui.onInsetsChanged(function (i) { insets = i; layout(); });
  }
  i18n.onChange(function () {
    renderLamp();
    if (!cab.hidden) renderCabinet();
  });

  applyVisibility();
  layout();
  tavo.variable.get(VAR, 'global').then(function (saved) {
    if (saved && typeof saved === 'object') {
      state.found = saved.found || {};
      state.mode = saved.mode === 'xray' ? 'xray' : 'uv';
      if (saved.lamp) state.lamp = saved.lamp;
      if (saved.pet) state.pet = saved.pet;
      layout();
    }
  }).catch(function () {});
})();
