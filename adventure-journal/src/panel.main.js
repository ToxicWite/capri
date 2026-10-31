// Adventure Journal chat panel: floating launcher and editable journal view.
(function () {
  var i18n = tavo.plugin.i18n;
  var t = function (key, params) { return i18n.t(key, params); };
  var POLL_MS = 1500;
  var FAB = 46;
  var MARGIN = 8;

  var root = document.getElementById('aj-root');
  var fab = document.getElementById('aj-fab');
  var badge = document.getElementById('aj-badge');
  var panel = document.getElementById('aj-panel');
  var titleEl = document.getElementById('aj-title');
  var templateBtn = document.getElementById('aj-template');
  var closeBtn = document.getElementById('aj-close');
  var tabsEl = document.getElementById('aj-tabs');
  var pendingEl = document.getElementById('aj-pending');
  var bodyEl = document.getElementById('aj-body');
  var footEl = document.getElementById('aj-foot');

  var state = null;
  var ui = {};
  var open = false;
  var tab = null;
  var busy = false;
  var lastRev = -1;
  var lastOpenRequest = null;
  var lastResetAt = null;
  var pos = null;

  // ---- helpers ------------------------------------------------------------

  function h(tag, attrs, children) {
    var el = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        var v = attrs[k];
        if (v == null || v === false) return;
        if (k === 'text') el.textContent = v;
        else if (k === 'class') el.className = v;
        else if (k === 'style') el.setAttribute('style', v);
        else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), v);
        else el.setAttribute(k, v === true ? '' : v);
      });
    }
    (children || []).forEach(function (c) {
      if (c == null || c === false) return;
      el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return el;
  }

  function btn(label, onClick, cls, aria) {
    return h('button', {
      type: 'button',
      class: 'aj-small' + (cls ? ' ' + cls : ''),
      text: label,
      title: aria || null,
      'aria-label': aria || null,
      onclick: function (e) {
        e.stopPropagation();
        onClick();
      },
    });
  }

  function cfgAll() {
    return tavo.plugin.config.all();
  }

  function toast(text) {
    try { tavo.utils.toast(text); } catch (e) { /* best-effort */ }
  }

  async function ask(question, defaultValue, placeholder) {
    var res = await tavo.utils.ask({
      question: question,
      defaultValue: defaultValue == null || defaultValue === '' ? undefined : String(defaultValue),
      placeholder: placeholder || undefined,
    });
    if (!res || res.status !== 'answered') return null;
    return String(res.answer);
  }

  async function confirmAsk(question) {
    var res = await tavo.utils.ask({
      question: question,
      options: [
        { value: 'yes', label: t('ui.yes') },
        { value: 'no', label: t('ui.no') },
      ],
      allowOther: false,
    });
    return !!res && res.answer === 'yes';
  }

  // ---- storage ------------------------------------------------------------

  async function loadState() {
    return AJ.normalize(await tavo.variable.get(AJ.VAR));
  }

  async function saveState(next) {
    next.rev = (next.rev || 0) + 1;
    next.summary = AJ.summarize(next, t);
    await tavo.variable.set(AJ.VAR, next);
    state = next;
    lastRev = next.rev;
    render();
  }

  // Loads the freshest state, applies fn, saves. Guards against overlapping edits.
  async function mutate(fn) {
    if (busy) return;
    busy = true;
    try {
      var fresh = await loadState();
      if (!fresh) fresh = AJ.createState(tavo.plugin.config.get('defaultTemplate') || 'fantasy', t, cfgAll());
      var result = await fn(fresh);
      if (result === false) return;
      await saveState(result || fresh);
    } catch (e) {
      console.error('[adventure-journal]', e);
    } finally {
      busy = false;
    }
  }

  // ---- launcher position ----------------------------------------------------

  function insets() {
    if (tavo.ui && typeof tavo.ui.getInsets === 'function') {
      var i = tavo.ui.getInsets() || {};
      return {
        top: (i.topBar || 56) + MARGIN,
        bottom: (i.bottomInput || 72) + MARGIN,
      };
    }
    return { top: 64, bottom: 80 };
  }

  function clamp(p) {
    var b = insets();
    var w = window.innerWidth;
    var hgt = window.innerHeight;
    return {
      x: Math.min(Math.max(MARGIN, p.x), Math.max(MARGIN, w - FAB - MARGIN)),
      y: Math.min(Math.max(b.top, p.y), Math.max(b.top, hgt - FAB - b.bottom)),
    };
  }

  function defaultPos() {
    var b = insets();
    return { x: window.innerWidth - FAB - 12, y: b.top + 64 };
  }

  function placeFab() {
    var p = clamp(pos || defaultPos());
    fab.style.left = p.x + 'px';
    fab.style.top = p.y + 'px';
  }

  async function savePos() {
    try {
      var current = (await tavo.variable.get(AJ.UI_VAR, 'global')) || {};
      current.pos = pos ? { x: Math.round(pos.x), y: Math.round(pos.y) } : null;
      ui = current;
      await tavo.variable.set(AJ.UI_VAR, current, 'global');
    } catch (e) { /* position is cosmetic */ }
  }

  (function setupDrag() {
    var start = null;
    var moved = false;
    fab.addEventListener('pointerdown', function (e) {
      if (e.button != null && e.button !== 0) return;
      var rect = fab.getBoundingClientRect();
      start = { px: e.clientX, py: e.clientY, x: rect.left, y: rect.top };
      moved = false;
      try { fab.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
    });
    fab.addEventListener('pointermove', function (e) {
      if (!start) return;
      var dx = e.clientX - start.px;
      var dy = e.clientY - start.py;
      if (!moved && Math.abs(dx) + Math.abs(dy) < 8) return;
      moved = true;
      fab.classList.add('aj-dragging');
      pos = clamp({ x: start.x + dx, y: start.y + dy });
      placeFab();
    });
    function end() {
      if (!start) return;
      start = null;
      fab.classList.remove('aj-dragging');
      if (moved) savePos();
    }
    fab.addEventListener('pointerup', end);
    fab.addEventListener('pointercancel', end);
    fab.addEventListener('click', function (e) {
      if (moved) {
        e.preventDefault();
        moved = false;
        return;
      }
      setOpen(!open);
    });
    window.addEventListener('resize', placeFab);
    if (tavo.ui && typeof tavo.ui.onInsetsChanged === 'function') tavo.ui.onInsetsChanged(placeFab);
  })();

  // ---- rendering ------------------------------------------------------------

  function sectionLabel(section) {
    var tpl = state ? state.template : 'fantasy';
    var key = 'sec.' + tpl + '.' + section;
    var v = t(key);
    return v === key ? t('sec.default.' + section) : v;
  }

  function setOpen(value) {
    open = value;
    panel.hidden = !open;
    fab.setAttribute('aria-expanded', open ? 'true' : 'false');
    render();
  }

  function render() {
    var showButton = tavo.plugin.config.get('showButton') !== false;
    root.hidden = false;
    fab.hidden = !showButton || open;
    fab.setAttribute('aria-label', t('ui.open'));
    fab.title = t('ui.open');
    closeBtn.setAttribute('aria-label', t('ui.close'));
    closeBtn.title = t('ui.close');
    panel.setAttribute('aria-label', t('ui.title'));

    var pendingCount = state && state.pending ? state.pending.changes.length : 0;
    badge.hidden = !pendingCount;
    badge.textContent = pendingCount ? String(pendingCount) : '';

    if (!open) return;
    titleEl.textContent = t('ui.title');
    templateBtn.textContent = state ? t('template.' + state.template) + ' ▾' : '';
    templateBtn.title = t('ui.changeTemplate');
    templateBtn.hidden = !state;

    if (!state) {
      tabsEl.textContent = '';
      pendingEl.hidden = true;
      bodyEl.textContent = '';
      bodyEl.appendChild(h('div', { class: 'aj-empty', text: t('ui.loading') }));
      footEl.textContent = '';
      return;
    }

    var sections = state.sections.length ? state.sections : AJ.SECTIONS;
    if (sections.indexOf(tab) < 0) tab = sections[0];

    tabsEl.textContent = '';
    sections.forEach(function (s) {
      var count = s === 'status' ? null : (state[s] || []).length;
      tabsEl.appendChild(h('button', {
        type: 'button',
        class: 'aj-tab',
        role: 'tab',
        'aria-selected': s === tab ? 'true' : 'false',
        onclick: function () { tab = s; render(); },
      }, [sectionLabel(s), count ? h('span', { class: 'aj-count', text: String(count) }) : null]));
    });

    renderPending();
    bodyEl.textContent = '';
    ({ status: renderStatus, stats: renderStats, inventory: renderInventory, quests: renderQuests, relations: renderRelations })[tab]();
    renderFoot();
  }

  function renderPending() {
    var p = state.pending;
    pendingEl.textContent = '';
    pendingEl.hidden = !p;
    if (!p) return;
    pendingEl.appendChild(h('h4', { text: t('ui.pending.title', { count: p.changes.length }) }));
    pendingEl.appendChild(h('ul', null, p.changes.map(function (c) {
      return h('li', { text: AJ.formatChange(c, t) });
    })));
    pendingEl.appendChild(h('div', { class: 'aj-row-actions' }, [
      btn(t('ui.pending.apply'), function () {
        mutate(function (s) {
          if (!s.pending) return false;
          var pending = s.pending;
          var target = AJ.clone(s);
          target.status = pending.data.status;
          target.stats = pending.data.stats;
          target.inventory = pending.data.inventory;
          target.quests = pending.data.quests;
          target.relations = pending.data.relations;
          AJ.commit(s, { state: target }, pending.messageId, t, pending.hash);
          s.lastUpdateAt = new Date().toISOString();
        });
      }, 'aj-primary'),
      btn(t('ui.pending.dismiss'), function () {
        mutate(function (s) {
          if (!s.pending) return false;
          s.pending = null;
        });
      }),
    ]));
  }

  function renderFoot() {
    footEl.textContent = '';
    var when = state.lastUpdateAt ? new Date(state.lastUpdateAt) : null;
    var label = when && !isNaN(when.getTime())
      ? t('ui.lastUpdate', { time: when.toLocaleTimeString(i18n.locale, { hour: '2-digit', minute: '2-digit' }) })
      : t('ui.neverUpdated');
    footEl.appendChild(h('span', { text: label }));
    if (state.undo.length) {
      footEl.appendChild(btn('↶ ' + t('ui.undo'), function () {
        mutate(function (s) { return AJ.undoLast(s) ? s : false; });
      }));
    }
  }

  function empty(text) {
    bodyEl.appendChild(h('div', { class: 'aj-empty', text: text }));
  }

  function addButton(label, onClick) {
    bodyEl.appendChild(h('button', { type: 'button', class: 'aj-small aj-add', text: '+ ' + label, onclick: onClick }));
  }

  function removeAt(list, index) {
    return mutate(function (s) { s[list].splice(index, 1); });
  }

  function renderStatus() {
    ['location', 'time', 'conditions'].forEach(function (k) {
      var value = state.status[k];
      bodyEl.appendChild(h('div', { class: 'aj-field' }, [
        h('div', { class: 'aj-item-main' }, [
          h('div', { class: 'aj-field-label', text: t('sum.' + k) }),
          h('div', { class: 'aj-field-value' + (value ? '' : ' aj-placeholder'), text: value || t('ui.notSet') }),
        ]),
        btn('✎', async function () {
          var v = await ask(t('sum.' + k), value);
          if (v === null) return;
          mutate(function (s) { s.status[k] = AJ.str(v, 300); });
        }, null, t('ui.edit')),
      ]));
    });
  }

  function bar(value, max) {
    var pct = Math.max(0, Math.min(100, (value / max) * 100));
    return h('div', { class: 'aj-bar' }, [h('i', { style: 'width:' + pct + '%' })]);
  }

  function renderStats() {
    if (!state.stats.length) empty(t('ui.empty.stats'));
    state.stats.forEach(function (s, i) {
      bodyEl.appendChild(h('div', { class: 'aj-item' }, [
        h('div', { class: 'aj-item-main' }, [
          h('div', { class: 'aj-item-name', text: s.name }),
          s.max != null ? bar(s.value, s.max) : null,
        ]),
        btn('−', function () { mutate(function (st) { st.stats[i].value -= 1; }); }, null, t('ui.decrease')),
        h('span', { class: 'aj-value', text: s.value + (s.max != null ? ' / ' + s.max : '') }),
        btn('+', function () {
          mutate(function (st) {
            var stat = st.stats[i];
            stat.value = stat.max != null ? Math.min(stat.max, stat.value + 1) : stat.value + 1;
          });
        }, null, t('ui.increase')),
        btn('✎', async function () {
          var v = await ask(t('ui.stat.editValue', { name: s.name }), s.value + (s.max != null ? '/' + s.max : ''), '10/100');
          if (v === null) return;
          var parsed = AJ.parseCustomStats(s.name + '=' + v)[0];
          if (!parsed) return toast(t('ui.invalidNumber'));
          mutate(function (st) {
            st.stats[i].value = parsed.value;
            if (parsed.max != null) st.stats[i].max = parsed.max;
            else delete st.stats[i].max;
          });
        }, null, t('ui.edit')),
        btn('✕', async function () {
          if (await confirmAsk(t('ui.confirmDelete', { name: s.name }))) removeAt('stats', i);
        }, null, t('ui.delete')),
      ]));
    });
    addButton(t('ui.add.stat'), async function () {
      var v = await ask(t('ui.add.statQuestion'), '', t('ui.add.statPlaceholder'));
      if (v === null) return;
      var parsed = AJ.parseCustomStats(v);
      if (!parsed.length) return toast(t('ui.invalidNumber'));
      mutate(function (st) { st.stats = st.stats.concat(parsed); });
    });
  }

  function renderInventory() {
    if (!state.inventory.length) empty(t('ui.empty.inventory'));
    state.inventory.forEach(function (it, i) {
      bodyEl.appendChild(h('div', { class: 'aj-item' }, [
        h('div', { class: 'aj-item-main' }, [
          h('div', { class: 'aj-item-name', text: it.name }),
          it.note ? h('div', { class: 'aj-item-note', text: it.note }) : null,
        ]),
        btn('−', function () {
          mutate(function (s) {
            var item = s.inventory[i];
            item.qty = (item.qty || 1) - 1;
            if (item.qty <= 0) s.inventory.splice(i, 1);
          });
        }, null, t('ui.decrease')),
        h('span', { class: 'aj-value', text: '×' + (it.qty || 1) }),
        btn('+', function () { mutate(function (s) { s.inventory[i].qty = (s.inventory[i].qty || 1) + 1; }); }, null, t('ui.increase')),
        btn('✎', async function () {
          var note = await ask(t('ui.item.editNote', { name: it.name }), it.note);
          if (note === null) return;
          mutate(function (s) { s.inventory[i].note = AJ.str(note, 120); });
        }, null, t('ui.edit')),
      ]));
    });
    addButton(t('ui.add.item'), async function () {
      var name = await ask(t('ui.add.itemQuestion'));
      if (!name || !AJ.str(name)) return;
      mutate(function (s) {
        var r = AJ.applyPatch(s, { add_items: [{ name: name, qty: 1 }] });
        s.inventory = r.state.inventory;
      });
    });
  }

  var QUEST_ICONS = { active: '◯', done: '✓', failed: '✗' };

  function renderQuests() {
    if (!state.quests.length) empty(t('ui.empty.quests'));
    ['active', 'done', 'failed'].forEach(function (status) {
      var items = [];
      state.quests.forEach(function (q, i) { if (q.status === status) items.push({ q: q, i: i }); });
      if (!items.length) return;
      bodyEl.appendChild(h('div', { class: 'aj-group-title', text: t('ui.quest.' + status) }));
      items.forEach(function (entry) {
        var q = entry.q;
        var i = entry.i;
        bodyEl.appendChild(h('div', { class: 'aj-item aj-' + status }, [
          btn(QUEST_ICONS[status], async function () {
            var pick = await tavo.utils.select(['active', 'done', 'failed'].map(function (s) {
              return { value: s, label: QUEST_ICONS[s] + ' ' + t('ui.quest.' + s) };
            }), q.title, q.status);
            if (!pick) return;
            mutate(function (s) { s.quests[i].status = pick; });
          }, null, t('ui.quest.changeStatus')),
          h('div', { class: 'aj-item-main' }, [
            h('div', { class: 'aj-item-name', text: q.title }),
            q.note ? h('div', { class: 'aj-item-note', text: q.note }) : null,
          ]),
          btn('✎', async function () {
            var note = await ask(t('ui.quest.editNote', { name: q.title }), q.note);
            if (note === null) return;
            mutate(function (s) { s.quests[i].note = AJ.str(note, 160); });
          }, null, t('ui.edit')),
          btn('✕', async function () {
            if (await confirmAsk(t('ui.confirmDelete', { name: q.title }))) removeAt('quests', i);
          }, null, t('ui.delete')),
        ]));
      });
    });
    addButton(t('ui.add.quest'), async function () {
      var title = await ask(t('ui.add.questQuestion'));
      if (!title || !AJ.str(title)) return;
      mutate(function (s) {
        var r = AJ.applyPatch(s, { quests: [{ title: title, status: 'active' }] });
        s.quests = r.state.quests;
      });
    });
  }

  function relBar(value) {
    var v = Math.max(-100, Math.min(100, value));
    var left = v >= 0 ? 50 : 50 + v / 2;
    var width = Math.abs(v) / 2;
    return h('div', { class: 'aj-bar aj-rel' }, [
      h('i', { style: 'left:' + left + '%;width:' + width + '%;background:' + (v >= 0 ? 'var(--aj-good)' : 'var(--aj-bad)') }),
    ]);
  }

  function renderRelations() {
    if (!state.relations.length) empty(t('ui.empty.relations'));
    state.relations.forEach(function (r, i) {
      var sub = [r.attitude, r.note].filter(Boolean).join(' · ');
      bodyEl.appendChild(h('div', { class: 'aj-item' }, [
        h('div', { class: 'aj-item-main' }, [
          h('div', { class: 'aj-item-name', text: r.name }),
          sub ? h('div', { class: 'aj-item-note', text: sub }) : null,
          r.value != null ? relBar(r.value) : null,
        ]),
        r.value != null ? h('span', { class: 'aj-value', text: (r.value > 0 ? '+' : '') + r.value }) : null,
        btn('✎', async function () {
          var v = await ask(t('ui.rel.editValue', { name: r.name }), r.value == null ? '' : r.value, '-100 … 100');
          if (v === null) return;
          var n = AJ.num(v);
          if (n == null) return toast(t('ui.invalidNumber'));
          mutate(function (s) { s.relations[i].value = Math.max(-100, Math.min(100, Math.round(n))); });
        }, null, t('ui.edit')),
        btn('✕', async function () {
          if (await confirmAsk(t('ui.confirmDelete', { name: r.name }))) removeAt('relations', i);
        }, null, t('ui.delete')),
      ]));
    });
    addButton(t('ui.add.relation'), async function () {
      var name = await ask(t('ui.add.relationQuestion'));
      if (!name || !AJ.str(name)) return;
      mutate(function (s) {
        var r = AJ.applyPatch(s, { relations: [{ name: name, value: 0 }] });
        s.relations = r.state.relations;
      });
    });
  }

  // ---- template switch ------------------------------------------------------

  templateBtn.addEventListener('click', async function () {
    if (!state) return;
    var pick = await tavo.utils.select(AJ.templateIds().map(function (id) {
      return { value: id, label: t('template.' + id), description: t('template.' + id + '.desc') };
    }), t('runtime.template.title'), state.template);
    if (!pick || !AJ.TEMPLATES[pick]) return;
    var keep = false;
    if (!AJ.isEmpty(state)) {
      var res = await tavo.utils.ask({
        question: t('runtime.template.keepQuestion'),
        options: [
          { value: 'keep', label: t('runtime.template.keep') },
          { value: 'fresh', label: t('runtime.template.fresh') },
        ],
        allowOther: false,
      });
      if (!res || res.status !== 'answered') return;
      keep = res.answer === 'keep';
    }
    mutate(function (s) { return AJ.switchTemplate(s, pick, keep, t, cfgAll()); });
  });

  closeBtn.addEventListener('click', function () { setOpen(false); });

  // ---- sync -------------------------------------------------------------------

  async function poll() {
    try {
      var next = await loadState();
      var rev = next ? next.rev : -1;
      if (!busy && rev !== lastRev) {
        state = next;
        lastRev = rev;
        render();
      }
      var nextUi = (await tavo.variable.get(AJ.UI_VAR, 'global')) || {};
      if (lastOpenRequest === null) lastOpenRequest = nextUi.openRequest || 0;
      else if (nextUi.openRequest && nextUi.openRequest !== lastOpenRequest) {
        lastOpenRequest = nextUi.openRequest;
        setOpen(true);
      }
      if (lastResetAt === null) lastResetAt = nextUi.resetAt || 0;
      else if (nextUi.resetAt && nextUi.resetAt !== lastResetAt) {
        lastResetAt = nextUi.resetAt;
        pos = null;
        placeFab();
      }
      ui = nextUi;
    } catch (e) {
      // Chat transitions reject calls briefly; the next poll retries.
    }
  }

  async function init() {
    try {
      ui = (await tavo.variable.get(AJ.UI_VAR, 'global')) || {};
      pos = ui.pos || null;
    } catch (e) {
      ui = {};
    }
    lastOpenRequest = ui.openRequest || 0;
    lastResetAt = ui.resetAt || 0;
    placeFab();
    render();
    await poll();
    setInterval(poll, POLL_MS);
  }

  i18n.onChange(render);
  init();
})();
