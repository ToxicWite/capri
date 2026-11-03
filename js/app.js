/* Capri · Norsk — личное приложение для норвежского */
(() => {
  'use strict';

  // ================= helpers =================
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const el = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };
  const shuffle = (a) => { a = [...a]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const pick = (a) => a[Math.floor(Math.random() * a.length)];
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const DAY = 86400000;
  const pad = (n) => String(n).padStart(2, '0');
  const dayKey = (d = new Date()) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const keyToDate = (k) => { const [y, m, d] = k.split('-').map(Number); return new Date(y, m - 1, d, 12); };
  const daysBetween = (a, b) => Math.round((keyToDate(b) - keyToDate(a)) / DAY);
  const plural = (n, one, few, many) => {
    const m10 = n % 10, m100 = n % 100;
    if (m10 === 1 && m100 !== 11) return one;
    if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
    return many;
  };

  // ================= state =================
  const STORE = 'capri-norsk-v1';
  const defaults = () => ({
    v: 1, xp: 0, goal: 50,
    hist: {},                       // { 'YYYY-MM-DD': xp }
    streak: { count: 0, best: 0, last: null, freezes: 0 },
    words: {},                      // id -> { b, due, c, w, t }
    fav: {},
    custom: [],
    ach: {},
    stats: { sessions: 0, perfect: 0, gender: 0, bestCombo: 0, answers: 0, right: 0 },
    best: {},                       // рекорды мини-игр
    settings: { sound: true, autoplay: true, rate: 0.85 },
    focus: null,
  });
  let S;
  try { S = Object.assign(defaults(), JSON.parse(localStorage.getItem(STORE) || '{}')); } catch { S = defaults(); }
  S.stats = Object.assign(defaults().stats, S.stats);
  S.settings = Object.assign(defaults().settings, S.settings);
  S.streak = Object.assign(defaults().streak, S.streak);
  const save = () => { try { localStorage.setItem(STORE, JSON.stringify(S)); } catch {} };

  // ================= words =================
  const CATS = window.CATEGORIES;
  let ALL = [], BY_ID = {};
  function parseWord(line, cat) {
    const [no, ru, exNo, exRu] = line.split('|').map((x) => x && x.trim());
    const m = no.match(/^(en|ei|et) (.+)$/);
    return {
      id: no, no, ru, exNo, exRu, cat,
      gender: m ? m[1] : null,
      bare: m ? m[2] : no.replace(/^å /, ''),
      pos: m ? 'noun' : no.startsWith('å ') ? 'verb' : 'other',
    };
  }
  function rebuildWords() {
    ALL = []; BY_ID = {};
    for (const c of CATS) for (const line of c.words) { const w = parseWord(line, c.id); if (!BY_ID[w.id]) { ALL.push(w); BY_ID[w.id] = w; } }
    for (const cw of S.custom) {
      const w = parseWord([cw.no, cw.ru, cw.exNo || '', cw.exRu || ''].join('|'), 'mine');
      w.custom = true;
      if (!BY_ID[w.id]) { ALL.push(w); BY_ID[w.id] = w; }
    }
  }
  rebuildWords();
  const catOf = (id) => id === 'mine' ? { id: 'mine', name: 'Mine ord', ru: 'Мои слова', icon: '🖋️' } : CATS.find((c) => c.id === id);

  // ================= SRS (лейтнер) =================
  const INTERVALS = [0, 1, 2, 4, 8, 16, 35, 90]; // дни
  const MAX_BOX = INTERVALS.length - 1;
  const rec = (id) => S.words[id];
  const box = (id) => (S.words[id] ? S.words[id].b : 0);
  const status = (id) => { const b = box(id); if (!S.words[id]) return 'new'; if (b >= 5) return 'mastered'; if (b >= 3) return 'known'; return 'learning'; };
  function grade(id, ok) {
    const r = S.words[id] || { b: 0, c: 0, w: 0 };
    if (ok) { r.b = Math.min(MAX_BOX, r.b + 1); r.c++; r.due = Date.now() + INTERVALS[r.b] * DAY - 3600000; }
    else { r.b = Math.max(1, r.b - 2); r.w++; r.due = Date.now() + 10 * 60000; }
    r.t = Date.now();
    S.words[id] = r;
  }
  const dueWords = () => ALL.filter((w) => S.words[w.id] && S.words[w.id].due <= Date.now()).sort((a, b) => S.words[a.id].due - S.words[b.id].due);
  const newWords = (cat) => ALL.filter((w) => !S.words[w.id] && (!cat || w.cat === cat));
  const learnedCount = () => ALL.filter((w) => box(w.id) >= 3).length;

  // ================= levels =================
  const LEVELS = ['Turist', 'Nykommer', 'Turgåer', 'Fjordfisker', 'Fjellgeit', 'Viking', 'Nordlysjeger', 'Skald', 'Jarl', 'Fjelltroll', 'Norne', 'Allfader'];
  const LEVELS_RU = ['турист', 'новичок', 'путник', 'рыбак фьордов', 'горная коза', 'викинг', 'охотница за сиянием', 'скальд', 'ярл', 'горный тролль', 'норна', 'всеотец'];
  function levelInfo(xp = S.xp) {
    let lvl = 1, need = 100, acc = 0;
    while (xp >= acc + need) { acc += need; lvl++; need = 100 + (lvl - 1) * 60; }
    const i = Math.min(lvl - 1, LEVELS.length - 1);
    return { lvl, name: lvl > LEVELS.length ? 'Legende' : LEVELS[i], ru: lvl > LEVELS.length ? 'легенда' : LEVELS_RU[i], into: xp - acc, need };
  }

  // ================= streak & xp =================
  function checkStreak() {
    const st = S.streak, today = dayKey();
    if (!st.last || st.count === 0) return;
    const gap = daysBetween(st.last, today);
    if (gap <= 1) return;
    const missed = gap - 1;
    if (st.freezes >= missed) {
      st.freezes -= missed;
      st.last = dayKey(new Date(Date.now() - DAY));
      setTimeout(() => toast('🧊', 'Стрик спасён!', `Ледяной оберег сработал (${missed})`), 800);
    } else { st.count = 0; }
    save();
  }
  function addXP(n) {
    const today = dayKey();
    const before = levelInfo().lvl;
    const goalBefore = (S.hist[today] || 0) >= S.goal;
    S.xp += n;
    S.hist[today] = (S.hist[today] || 0) + n;
    const st = S.streak;
    let extended = false;
    if (st.last !== today) {
      const yest = dayKey(new Date(Date.now() - DAY));
      st.count = st.last === yest ? st.count + 1 : 1;
      st.last = today; extended = true;
      st.best = Math.max(st.best, st.count);
      if (st.count % 7 === 0 && st.freezes < 2) { st.freezes++; setTimeout(() => toast('🧊', 'Ледяной оберег', 'Защитит стрик, если пропустишь день'), 1600); }
    }
    const after = levelInfo().lvl;
    if (after > before) { setTimeout(() => { toast('🌌', `Nivå ${after}!`, `Ты теперь ${levelInfo().name} — ${levelInfo().ru}`); sfx('level'); }, 500); }
    if (!goalBefore && S.hist[today] >= S.goal) setTimeout(() => toast('🎯', 'Dagens mål nådd!', 'Цель дня выполнена'), 300);
    save();
    return extended;
  }

  // ================= achievements =================
  const ACH = [
    { id: 'first', i: '👣', n: 'Første skritt', d: 'Первая тренировка', t: () => S.stats.sessions >= 1 },
    { id: 's3', i: '🔥', n: 'Gnist', d: 'Стрик 3 дня', t: () => S.streak.best >= 3 },
    { id: 's7', i: '🏕️', n: 'Bål', d: 'Стрик 7 дней', t: () => S.streak.best >= 7 },
    { id: 's30', i: '🌋', n: 'Vulkan', d: 'Стрик 30 дней', t: () => S.streak.best >= 30 },
    { id: 'w10', i: '🌱', n: 'Ordfrø', d: 'Выучить 10 слов', t: () => learnedCount() >= 10 },
    { id: 'w50', i: '🌲', n: 'Ordskog', d: 'Выучить 50 слов', t: () => learnedCount() >= 50 },
    { id: 'w150', i: '🏔️', n: 'Ordfjell', d: 'Выучить 150 слов', t: () => learnedCount() >= 150 },
    { id: 'w300', i: '👑', n: 'Ordkonge', d: 'Выучить 300 слов', t: () => learnedCount() >= 300 },
    { id: 'c10', i: '⚡', n: 'Flyt', d: 'Комбо ×10', t: () => S.stats.bestCombo >= 10 },
    { id: 'c25', i: '🌪️', n: 'Ustoppelig', d: 'Комбо ×25', t: () => S.stats.bestCombo >= 25 },
    { id: 'perfect', i: '💎', n: 'Feilfri', d: 'Тренировка без ошибок', t: () => S.stats.perfect >= 1 },
    { id: 'night', i: '🦉', n: 'Natteravn', d: 'Заниматься после 23:00', t: () => false },
    { id: 'early', i: '🐦', n: 'Morgenfugl', d: 'Заниматься до 7:00', t: () => false },
    { id: 'own1', i: '🖋️', n: 'Min egen', d: 'Добавить своё слово', t: () => S.custom.length >= 1 },
    { id: 'own20', i: '📜', n: 'Runeskriver', d: '20 своих слов', t: () => S.custom.length >= 20 },
    { id: 'g50', i: '⚖️', n: 'En eller et', d: '50 верных родов', t: () => S.stats.gender >= 50 },
    { id: 'xp1k', i: '✨', n: 'Tusen', d: '1000 XP', t: () => S.xp >= 1000 },
    { id: 'lvl6', i: '🪓', n: 'Viking', d: 'Достичь 6 уровня', t: () => levelInfo().lvl >= 6 },
    { id: 'lyn', i: '🌩️', n: 'Lynet', d: '20 очков в «Молнии»', t: () => (S.best.lyn || 0) >= 20 },
    { id: 'goal7', i: '🎯', n: 'Disiplin', d: '7 дней с выполненной целью', t: () => Object.values(S.hist).filter((x) => x >= S.goal).length >= 7 },
  ];
  function unlock(id) {
    if (S.ach[id]) return;
    S.ach[id] = Date.now();
    const a = ACH.find((x) => x.id === id);
    toast(a.i, `Ачивка: ${a.n}`, a.d); sfx('level');
  }
  function checkAch() {
    const h = new Date().getHours();
    if (S.stats.sessions > 0 && (h >= 23 || h < 4)) unlock('night');
    if (S.stats.sessions > 0 && h >= 4 && h < 7) unlock('early');
    for (const a of ACH) if (!S.ach[a.id] && a.t()) unlock(a.id);
    save();
  }

  // ================= audio =================
  let voice = null;
  function loadVoice() {
    if (!('speechSynthesis' in window)) return;
    const vs = speechSynthesis.getVoices();
    voice = vs.find((v) => /^nb/i.test(v.lang)) || vs.find((v) => /^no/i.test(v.lang)) || vs.find((v) => /^nn/i.test(v.lang)) || null;
  }
  if ('speechSynthesis' in window) { loadVoice(); speechSynthesis.onvoiceschanged = loadVoice; }
  function speak(text) {
    if (!('speechSynthesis' in window)) return;
    const t = String(text).replace(/…/g, '').replace(/\(.*?\)/g, '');
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(t);
    u.lang = voice ? voice.lang : 'nb-NO';
    if (voice) u.voice = voice;
    u.rate = S.settings.rate;
    speechSynthesis.speak(u);
  }
  let actx;
  function sfx(kind) {
    if (!S.settings.sound) return;
    try {
      actx = actx || new (window.AudioContext || window.webkitAudioContext)();
      const notes = { ok: [[660, 0], [990, 0.08]], bad: [[220, 0], [180, 0.12]], level: [[523, 0], [659, 0.1], [784, 0.2], [1046, 0.3]], tap: [[880, 0]], combo: [[784, 0], [1175, 0.07], [1568, 0.14]] }[kind] || [];
      const now = actx.currentTime;
      for (const [f, d] of notes) {
        const o = actx.createOscillator(), g = actx.createGain();
        o.type = kind === 'bad' ? 'triangle' : 'sine';
        o.frequency.value = f;
        g.gain.setValueAtTime(0.0001, now + d);
        g.gain.exponentialRampToValueAtTime(kind === 'tap' ? 0.05 : 0.16, now + d + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, now + d + (kind === 'level' ? 0.5 : 0.25));
        o.connect(g).connect(actx.destination);
        o.start(now + d); o.stop(now + d + 0.6);
      }
    } catch {}
  }
  const buzz = (p) => { try { navigator.vibrate && navigator.vibrate(p); } catch {} };

  // ================= ui bits =================
  function toast(icon, title, sub) {
    const t = el(`<div class="toast"><span class="ti">${icon}</span><div><b>${esc(title)}</b><span>${esc(sub || '')}</span></div></div>`);
    $('#toasts').appendChild(t);
    setTimeout(() => t.remove(), 3800);
  }
  function sparks(x, y, n = 18) {
    const colors = ['#6ef7c8', '#b18cff', '#ff5d8f', '#ffb45c', '#86d4ff'];
    for (let i = 0; i < n; i++) {
      const s = el('<i class="spark"></i>');
      const a = Math.random() * Math.PI * 2, r = 40 + Math.random() * 90;
      s.style.left = x + 'px'; s.style.top = y + 'px'; s.style.background = pick(colors);
      s.style.setProperty('--dx', Math.cos(a) * r + 'px'); s.style.setProperty('--dy', Math.sin(a) * r + 'px');
      document.body.appendChild(s); setTimeout(() => s.remove(), 1400);
    }
  }
  function xpFloat(x, y, n) {
    const f = el(`<div class="xp-float">+${n} XP</div>`);
    f.style.left = x - 30 + 'px'; f.style.top = y - 20 + 'px';
    document.body.appendChild(f); setTimeout(() => f.remove(), 1000);
  }
  function sheet(html, onMount) {
    const root = $('#sheet-root');
    const back = el('<div class="sheet-back"></div>');
    const sh = el(`<div class="sheet"><div class="inner"><div class="grab"></div>${html}</div></div>`);
    const close = () => { back.remove(); sh.remove(); };
    back.onclick = close;
    root.append(back, sh);
    onMount && onMount(sh, close);
    return close;
  }
  // подтверждение внутри приложения (системные confirm() работают не везде)
  function ask(title, text, okLabel, onOk, cancelLabel = 'Отмена') {
    sheet(`<h2>${esc(title)}</h2><p class="muted" style="margin:8px 0 0">${esc(text)}</p>
      <div class="detail-actions"><button class="btn" id="askNo">${esc(cancelLabel)}</button><button class="btn danger" id="askYes">${esc(okLabel)}</button></div>`, (sh, close) => {
      $('#askNo', sh).onclick = close;
      $('#askYes', sh).onclick = () => { close(); onOk(); };
    });
  }
  const art = (w) => w.gender ? `<span class="art ${w.gender}">${w.gender}</span>${esc(w.bare)}` : w.pos === 'verb' ? `<span class="art å">å</span>${esc(w.bare)}` : esc(w.no);
  const lvlBars = (id) => { const b = box(id); const cls = b >= 3 ? '' : 'learning'; return `<span class="lvl ${cls}">${[1, 2, 3, 4, 5].map((i) => `<i class="${b >= i ? 'on' : ''}"></i>`).join('')}</span>`; };

  // ================= routing =================
  let tab = 'home';
  const view = $('#view');
  $$('#tabbar button').forEach((b) => b.addEventListener('click', () => { sfx('tap'); go(b.dataset.tab); }));
  function go(t) {
    tab = t;
    $$('#tabbar button').forEach((b) => b.classList.toggle('active', b.dataset.tab === t));
    window.scrollTo(0, 0);
    ({ home: renderHome, dict: renderDict, games: renderGames, me: renderMe })[t]();
  }

  // ================= HOME =================
  function greeting() {
    const h = new Date().getHours();
    if (h < 5) return ['God natt', 'полуночница? 🌙'];
    if (h < 11) return ['God morgen', 'кофе и пара слов?'];
    if (h < 18) return ['God dag', 'время для норвежского'];
    if (h < 23) return ['God kveld', 'уютный вечер для слов'];
    return ['God natt', 'ещё чуть-чуть перед сном?'];
  }
  function wordOfDay() {
    const k = dayKey(); let hsh = 0; for (const c of k) hsh = (hsh * 31 + c.charCodeAt(0)) >>> 0;
    const pool = ALL.filter((w) => w.exNo) ;
    const fresh = ALL.filter((w) => !S.words[w.id]);
    const src = fresh.length ? fresh : ALL;
    // через день — слово с примером
    const list = hsh % 2 && pool.length ? pool : src;
    return list[hsh % list.length];
  }
  function sessionPlan(cat) {
    const due = dueWords().filter((w) => !cat || w.cat === cat);
    const nw = newWords(cat || S.focus || null);
    const nNew = due.length > 12 ? 2 : due.length > 6 ? 3 : 5;
    return { due: due.slice(0, 10), fresh: (nw.length ? nw : newWords()).slice(0, nNew) };
  }
  function renderHome() {
    checkStreak();
    const [g, sub] = greeting();
    const today = dayKey();
    const todayXP = S.hist[today] || 0;
    const pct = clamp(todayXP / S.goal, 0, 1);
    const L = levelInfo();
    const plan = sessionPlan();
    const st = S.streak;
    const alive = st.count > 0 && (st.last === today || daysBetween(st.last, today) <= 1);
    const wd = wordOfDay();
    const C = 2 * Math.PI * 48;
    const days = [...Array(7)].map((_, i) => { const d = new Date(Date.now() - (6 - i) * DAY); return { k: dayKey(d), l: ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'][d.getDay()] }; });
    const maxXP = Math.max(S.goal, ...days.map((d) => S.hist[d.k] || 0));

    view.innerHTML = `
      <header class="hello">
        <div>
          <div class="eyebrow">${esc(sub)}</div>
          <h1>${g.split(' ')[0]} <em>${g.split(' ').slice(1).join(' ')}</em></h1>
        </div>
        <div class="streak-pill ${alive ? '' : 'cold'}" id="streakPill"><span class="flame">🔥</span>${alive ? st.count : 0}${st.freezes ? `<span class="frost">🧊${st.freezes}</span>` : ''}</div>
      </header>

      <section class="hero">
        <div class="ring ${pct >= 1 ? 'done' : ''}">
          <svg width="112" height="112" viewBox="0 0 112 112">
            <defs><linearGradient id="auroraGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6ef7c8"/><stop offset=".6" stop-color="#86d4ff"/><stop offset="1" stop-color="#b18cff"/></linearGradient></defs>
            <circle class="ring-bg" cx="56" cy="56" r="48" fill="none" stroke-width="10"/>
            <circle class="ring-fg" cx="56" cy="56" r="48" fill="none" stroke-width="10" stroke-dasharray="${C}" stroke-dashoffset="${C}" id="ringFg"/>
          </svg>
          <div class="ring-label"><b>${todayXP}</b><span>из ${S.goal} XP</span></div>
        </div>
        <div>
          <div class="level-num">Nivå ${L.lvl}</div>
          <div class="level-name">${esc(L.name)}</div>
          <div class="muted small">${esc(L.ru)} · ещё ${L.need - L.into} XP</div>
          <div class="bar"><i style="width:${(L.into / L.need) * 100}%"></i></div>
        </div>
      </section>

      <button class="cta" id="startBtn">
        <div><b>Start økt</b><span>${plan.due.length ? `${plan.due.length} на повторение · ` : ''}${plan.fresh.length ? `${plan.fresh.length} ${plural(plan.fresh.length, 'новое слово', 'новых слова', 'новых слов')}` : 'свободная тренировка'}</span></div>
        <div class="go">→</div>
      </button>

      <div class="section-title"><h2>Dagens ord</h2><span class="muted">слово дня</span></div>
      <article class="card wotd" id="wotd">
        <div class="rune-bg">ᛟ</div>
        <div class="row between"><span class="label">${esc(catOf(wd.cat).icon)} ${esc(catOf(wd.cat).ru)}</span><button class="icon-btn" id="wotdSpeak">🔊</button></div>
        <div class="w">${art(wd)}</div>
        <div class="muted">${esc(wd.ru)}</div>
        ${wd.exNo ? `<div class="ex">${esc(wd.exNo)}<br>${esc(wd.exRu)}</div>` : ''}
      </article>

      <div class="section-title"><h2>Uka</h2><span class="muted">лучший стрик: ${st.best}</span></div>
      <article class="card">
        <div class="week">${days.map((d) => { const x = S.hist[d.k] || 0; return `<div class="d ${x >= S.goal ? 'on' : ''} ${d.k === today ? 'today' : ''}"><i style="height:${Math.max(6, (x / maxXP) * 70)}px"></i>${d.l}</div>`; }).join('')}</div>
      </article>

      <div class="section-title"><h2>Temaer</h2><span class="muted">выбери тему</span></div>
      <section class="topics">
        ${[...CATS, ...(S.custom.length ? [catOf('mine')] : [])].map((c) => {
          const ws = ALL.filter((w) => w.cat === c.id), k = ws.filter((w) => box(w.id) >= 3).length;
          return `<button class="topic ${k === ws.length ? 'complete' : ''}" data-cat="${c.id}"><span class="ic">${c.icon}</span><b>${esc(c.name)}</b><span class="muted">${esc(c.ru)} · ${k}/${ws.length}</span><div class="bar"><i style="width:${ws.length ? (k / ws.length) * 100 : 0}%"></i></div></button>`;
        }).join('')}
      </section>
    `;
    requestAnimationFrame(() => setTimeout(() => { const r = $('#ringFg'); if (r) r.style.strokeDashoffset = C * (1 - pct); }, 60));
    $('#startBtn').onclick = () => startLesson();
    $('#wotdSpeak').onclick = () => speak(wd.no);
    $('#wotd').onclick = (e) => { if (!e.target.closest('#wotdSpeak')) wordSheet(wd); };
    $$('.topic').forEach((b) => (b.onclick = () => topicSheet(b.dataset.cat)));
  }
  function topicSheet(cat) {
    const c = catOf(cat); const ws = ALL.filter((w) => w.cat === cat);
    const nw = ws.filter((w) => !S.words[w.id]).length;
    sheet(`
      <div class="row"><span style="font-size:40px">${c.icon}</span><div><h2>${esc(c.name)}</h2><div class="muted">${esc(c.ru)} · ${ws.length} слов, новых ${nw}</div></div></div>
      <div class="wlist" style="max-height:38vh;overflow:auto;margin-top:12px">${ws.map((w) => `<div class="witem"><div class="grow"><div class="no">${art(w)}</div><div class="ru">${esc(w.ru)}</div></div>${lvlBars(w.id)}</div>`).join('')}</div>
      <div style="display:grid;gap:10px;margin-top:16px">
        <button class="btn primary block" id="tLearn">Учить эту тему</button>
        <button class="btn block" id="tFocus">${S.focus === cat ? '★ Это моя основная тема' : 'Сделать основной темой'}</button>
      </div>`, (sh, close) => {
      $('#tLearn', sh).onclick = () => { close(); startLesson(cat); };
      $('#tFocus', sh).onclick = () => { S.focus = S.focus === cat ? null : cat; save(); close(); renderHome(); };
    });
  }

  // ================= DICTIONARY =================
  let dictFilter = 'all', dictQuery = '';
  function renderDict() {
    const counts = { m: ALL.filter((w) => box(w.id) >= 3).length, l: ALL.filter((w) => status(w.id) === 'learning').length, n: ALL.filter((w) => status(w.id) === 'new').length };
    view.innerHTML = `
      <header class="hello"><div><div class="eyebrow">ordbok</div><h1>Мой <em>словарик</em></h1></div></header>
      <section class="dict-summary">
        <div class="m"><b>${counts.m}</b><span>выучено</span></div>
        <div class="l"><b>${counts.l}</b><span>учу</span></div>
        <div class="n"><b>${counts.n}</b><span>новые</span></div>
      </section>
      <label class="search"><span>⌕</span><input id="q" placeholder="Søk… (норвежский или русский)" value="${esc(dictQuery)}" autocomplete="off" /></label>
      <div class="chips" id="chips">
        ${[['all', 'Все'], ['mine', '🖋️ Мои'], ['fav', '★ Избранное'], ['learning', 'Учу'], ['known', 'Выучено'], ...CATS.map((c) => [c.id, `${c.icon} ${c.ru}`])].map(([k, l]) => `<button class="chip ${dictFilter === k ? 'active' : ''}" data-f="${k}">${esc(l)}</button>`).join('')}
      </div>
      <div class="wlist" id="wlist"></div>
      <button class="fab" id="addBtn" aria-label="Добавить слово">+</button>
    `;
    const draw = () => {
      const q = dictQuery.trim().toLowerCase();
      let list = ALL.filter((w) => {
        if (dictFilter === 'mine') return w.custom;
        if (dictFilter === 'fav') return S.fav[w.id];
        if (dictFilter === 'learning') return status(w.id) === 'learning';
        if (dictFilter === 'known') return box(w.id) >= 3;
        if (dictFilter !== 'all') return w.cat === dictFilter;
        return true;
      });
      if (q) list = list.filter((w) => w.no.toLowerCase().includes(q) || w.ru.toLowerCase().includes(q));
      $('#wlist').innerHTML = list.length ? list.map((w) => `
        <button class="witem" data-id="${esc(w.id)}">
          <div class="grow"><div class="no">${art(w)} ${S.fav[w.id] ? '<span class="star">★</span>' : ''}</div><div class="ru">${esc(w.ru)}</div></div>
          ${lvlBars(w.id)}
        </button>`).join('') : `<div class="empty"><div class="big">${dictFilter === 'mine' ? '🖋️' : '🌫️'}</div>${dictFilter === 'mine' ? 'Тут будут твои слова.<br>Нажми «+», чтобы добавить первое.' : 'Ничего не нашлось'}</div>`;
      $$('.witem', $('#wlist')).forEach((b) => (b.onclick = () => wordSheet(BY_ID[b.dataset.id])));
    };
    draw();
    $('#q').oninput = (e) => { dictQuery = e.target.value; draw(); };
    $$('#chips .chip').forEach((c) => (c.onclick = () => { dictFilter = c.dataset.f; $$('#chips .chip').forEach((x) => x.classList.toggle('active', x === c)); draw(); }));
    $('#addBtn').onclick = () => addWordSheet();
  }
  function wordSheet(w) {
    const r = rec(w.id); const c = catOf(w.cat);
    const st = { new: 'новое', learning: 'учу', known: 'выучено', mastered: 'в долгой памяти' }[status(w.id)];
    const dueTxt = r ? (r.due <= Date.now() ? 'пора повторить' : `повтор через ${Math.max(1, Math.round((r.due - Date.now()) / DAY))} дн.`) : '';
    sheet(`
      <div class="row between"><span class="muted small">${c.icon} ${esc(c.ru)}${w.gender ? ` · род: <b class="art ${w.gender}">${w.gender}</b>${w.gender === 'ei' ? ' (можно en)' : ''}` : ''}</span><button class="icon-btn" id="dSpeak">🔊</button></div>
      <div class="detail-word">${art(w)}</div>
      <div style="font-size:18px;margin-top:6px">${esc(w.ru)}</div>
      ${w.exNo ? `<div class="card" style="margin-top:16px"><div>${esc(w.exNo)}</div><div class="muted small" style="margin-top:4px">${esc(w.exRu)}</div></div>` : ''}
      <div class="row" style="margin-top:16px">${lvlBars(w.id)}<span class="muted small">${st}${dueTxt ? ' · ' + dueTxt : ''}${r ? ` · ✓${r.c} ✗${r.w}` : ''}</span></div>
      <div class="detail-actions">
        <button class="btn" id="dFav">${S.fav[w.id] ? '★ В избранном' : '☆ В избранное'}</button>
        ${w.custom ? '<button class="btn danger" id="dDel">Удалить</button>' : `<button class="btn" id="dReset">${r ? 'Сбросить прогресс' : 'Пометить «знаю»'}</button>`}
      </div>`, (sh, close) => {
      if (S.settings.autoplay) speak(w.no);
      $('#dSpeak', sh).onclick = () => speak(w.no);
      $('#dFav', sh).onclick = () => { if (S.fav[w.id]) delete S.fav[w.id]; else S.fav[w.id] = 1; save(); close(); refresh(); };
      const del = $('#dDel', sh);
      if (del) del.onclick = () => ask(`Удалить «${w.no}»?`, 'Слово и его прогресс исчезнут из словарика.', 'Удалить', () => { S.custom = S.custom.filter((x) => x.no !== w.no); delete S.words[w.id]; delete S.fav[w.id]; rebuildWords(); save(); close(); refresh(); });
      const rs = $('#dReset', sh);
      if (rs) rs.onclick = () => { if (r) delete S.words[w.id]; else S.words[w.id] = { b: 5, c: 1, w: 0, due: Date.now() + 16 * DAY, t: Date.now() }; save(); close(); refresh(); };
    });
  }
  const refresh = () => go(tab);
  function addWordSheet() {
    sheet(`
      <h2>Новое слово 🖋️</h2>
      <p class="muted small" style="margin:6px 0 0">Существительное пиши с артиклем (en / ei / et), глагол — с «å». Так сработает игра «en eller et?».</p>
      <label class="field"><span>Norsk</span><input id="fNo" placeholder="en kanelbolle" autocomplete="off" autocapitalize="off" /></label>
      <div class="keys" style="justify-content:flex-start">${['æ', 'ø', 'å'].map((k) => `<button data-k="${k}">${k}</button>`).join('')}</div>
      <label class="field"><span>Перевод</span><input id="fRu" placeholder="булочка с корицей" autocomplete="off" /></label>
      <label class="field"><span>Пример (необязательно)</span><input id="fEx" placeholder="Jeg elsker kanelboller." autocomplete="off" autocapitalize="off" /></label>
      <label class="field"><span>Перевод примера</span><input id="fExRu" placeholder="Я обожаю булочки с корицей." autocomplete="off" /></label>
      <button class="btn primary block" id="fSave" style="margin-top:18px">Добавить в словарик</button>
    `, (sh, close) => {
      const no = $('#fNo', sh); let last = no;
      $$('input', sh).forEach((i) => i.addEventListener('focus', () => (last = i)));
      $$('.keys button', sh).forEach((b) => (b.onclick = (e) => { e.preventDefault(); insertAtCursor(last, b.dataset.k); }));
      setTimeout(() => no.focus(), 300);
      $('#fSave', sh).onclick = () => {
        const v = no.value.trim().replace(/\s+/g, ' '), ru = $('#fRu', sh).value.trim();
        if (!v || !ru) { toast('✍️', 'Заполни слово и перевод', ''); return; }
        if (BY_ID[v]) { toast('📚', 'Такое слово уже есть', v); return; }
        S.custom.push({ no: v, ru, exNo: $('#fEx', sh).value.trim(), exRu: $('#fExRu', sh).value.trim() });
        rebuildWords(); save(); close(); checkAch();
        toast('🖋️', 'Слово добавлено', `${v} — ${ru}`); sfx('ok');
        dictFilter = 'mine'; refresh();
      };
    });
  }
  function insertAtCursor(input, ch) {
    const s = input.selectionStart ?? input.value.length, e = input.selectionEnd ?? input.value.length;
    input.value = input.value.slice(0, s) + ch + input.value.slice(e);
    input.focus(); input.setSelectionRange(s + 1, s + 1);
    input.dispatchEvent(new Event('input'));
  }

  // ================= GAMES =================
  const GAMES = [
    { id: 'lyn', i: '🌩️', bg: 'rgba(134,212,255,.14)', n: 'Lynet', d: '60 секунд — сколько слов успеешь?', unit: 'очк.' },
    { id: 'kjonn', i: '⚖️', bg: 'rgba(255,93,143,.14)', n: 'En eller et?', d: 'Угадай род. Три ошибки — конец', unit: 'подряд' },
    { id: 'par', i: '🧩', bg: 'rgba(110,247,200,.14)', n: 'Par', d: 'Собери пары на скорость (3 раунда)', unit: 'сек', low: true },
    { id: 'lytt', i: '🎧', bg: 'rgba(177,140,255,.14)', n: 'Lytt', d: 'Услышь слово и найди его', unit: '/10' },
    { id: 'skriv', i: '⌨️', bg: 'rgba(255,180,92,.14)', n: 'Skriv', d: 'Напиши по-норвежски (с æ ø å)', unit: '/10' },
  ];
  function renderGames() {
    view.innerHTML = `
      <header class="hello"><div><div class="eyebrow">spill</div><h1>Мини-<em>игры</em></h1></div></header>
      <p class="muted" style="margin:10px 2px 0">Каждая игра даёт XP и поддерживает стрик 🔥</p>
      <section class="games">
        ${GAMES.map((g) => `<button class="game" data-g="${g.id}"><span class="gi" style="background:${g.bg}">${g.i}</span><div class="grow"><b>${g.n}</b><span class="muted">${g.d}</span></div>${S.best[g.id] != null ? `<span class="best">РЕКОРД ${S.best[g.id]} ${g.unit}</span>` : ''}</button>`).join('')}
      </section>
      <div class="section-title"><h2>Svak punkt</h2><span class="muted">слабые места</span></div>
      <button class="game" id="weak"><span class="gi" style="background:rgba(226,64,95,.14)">🩹</span><div class="grow"><b>Работа над ошибками</b><span class="muted">слова, в которых ты чаще ошибаешься</span></div></button>
    `;
    $$('.game[data-g]').forEach((b) => (b.onclick = () => startGame(b.dataset.g)));
    $('#weak').onclick = () => {
      const weak = ALL.filter((w) => rec(w.id) && rec(w.id).w > 0).sort((a, b) => (rec(b.id).w / (rec(b.id).c + 1)) - (rec(a.id).w / (rec(a.id).c + 1))).slice(0, 8);
      if (weak.length < 3) { toast('🌿', 'Пока ошибок мало', 'Сначала потренируйся немного'); return; }
      runSession({ title: 'Работа над ошибками', queue: weak.flatMap((w) => [ex(pick(['mcqNoRu', 'mcqRuNo', 'listen']), w), ex('type', w)]).sort(() => Math.random() - .5), srs: true });
    };
  }
  function pool(minBox = 0) {
    const seen = ALL.filter((w) => S.words[w.id] && box(w.id) >= minBox);
    return seen.length >= 12 ? seen : ALL.filter((w) => S.words[w.id]).concat(ALL.slice(0, 60)).filter((w, i, a) => a.indexOf(w) === i);
  }
  function startGame(id) {
    if (id === 'lyn') {
      const p = pool();
      runSession({ title: 'Lynet', game: 'lyn', timer: 60, endless: () => ex(Math.random() < .5 ? 'mcqNoRu' : 'mcqRuNo', pick(p)), fastNext: true });
    } else if (id === 'kjonn') {
      const nouns = ALL.filter((w) => w.gender);
      runSession({ title: 'En eller et?', game: 'kjonn', lives: 3, endless: () => ex('gender', pick(nouns)), fastNext: true });
    } else if (id === 'par') {
      const p = shuffle(pool()); runSession({ title: 'Par', game: 'par', stopwatch: true, queue: [0, 1, 2].map((i) => ({ type: 'match', words: p.slice(i * 5, i * 5 + 5) })) });
    } else if (id === 'lytt') {
      const p = shuffle(pool()).slice(0, 10); runSession({ title: 'Lytt', game: 'lytt', queue: p.map((w) => ex('listen', w)), srs: true });
    } else if (id === 'skriv') {
      const p = shuffle(pool(1).filter((w) => !w.no.includes('…'))).slice(0, 10); runSession({ title: 'Skriv', game: 'skriv', queue: p.map((w) => ex('type', w)), srs: true });
    }
  }

  // ================= ME =================
  function renderMe() {
    const L = levelInfo();
    const acc = S.stats.answers ? Math.round((S.stats.right / S.stats.answers) * 100) : 0;
    view.innerHTML = `
      <header class="hello"><div><div class="eyebrow">meg</div><h1>${esc(L.name)} <em>· ${L.lvl}</em></h1><div class="muted small" style="margin-top:4px">${esc(L.ru)} · ${S.xp} XP всего</div></div></header>
      <div class="bar" style="margin-top:14px"><i style="width:${(L.into / L.need) * 100}%"></i></div>
      <section class="stats">
        <div class="stat"><b style="color:var(--ember)">🔥 ${S.streak.count}</b><span>стрик (лучший ${S.streak.best})</span></div>
        <div class="stat"><b style="color:var(--mint)">${learnedCount()}</b><span>выучено слов из ${ALL.length}</span></div>
        <div class="stat"><b style="color:var(--violet)">${S.stats.sessions}</b><span>тренировок</span></div>
        <div class="stat"><b style="color:var(--ice)">${acc}%</b><span>точность ответов</span></div>
      </section>
      <div class="section-title"><h2>Merker</h2><span class="muted">${Object.keys(S.ach).length}/${ACH.length}</span></div>
      <section class="achs">${ACH.map((a) => `<div class="ach ${S.ach[a.id] ? 'got' : 'locked'}"><span class="ai">${a.i}</span><b>${esc(a.n)}</b><span>${esc(a.d)}</span></div>`).join('')}</section>
      <div class="section-title"><h2>Innstillinger</h2><span class="muted">настройки</span></div>
      <article class="card">
        <div class="setting"><div><b>Цель дня</b><div class="muted small">XP в день</div></div><div class="seg" id="goalSeg">${[20, 50, 100, 150].map((g) => `<button data-v="${g}" class="${S.goal === g ? 'active' : ''}">${g}</button>`).join('')}</div></div>
        <div class="setting"><div><b>Звуки</b><div class="muted small">дзынь за верный ответ</div></div><button class="toggle ${S.settings.sound ? 'on' : ''}" data-s="sound"></button></div>
        <div class="setting"><div><b>Автоозвучка</b><div class="muted small">произносить слова сразу</div></div><button class="toggle ${S.settings.autoplay ? 'on' : ''}" data-s="autoplay"></button></div>
        <div class="setting"><div><b>Скорость речи</b><div class="muted small">${voice ? 'голос: ' + esc(voice.name) : 'норвежский голос не найден — установи его в настройках телефона'}</div></div><div class="seg" id="rateSeg">${[[0.65, '🐢'], [0.85, '•'], [1, '🐇']].map(([v, l]) => `<button data-v="${v}" class="${S.settings.rate === v ? 'active' : ''}">${l}</button>`).join('')}</div></div>
      </article>
      <article class="card" style="display:grid;gap:10px">
        <button class="btn block" id="exp">⇩ Сохранить резервную копию</button>
        <button class="btn block" id="imp">⇧ Загрузить копию</button>
        <button class="btn danger block" id="reset">Начать всё заново</button>
      </article>
      <p class="muted small" style="text-align:center;margin-top:20px">Lykke til med norsken! 🇳🇴</p>
    `;
    $$('#goalSeg button').forEach((b) => (b.onclick = () => { S.goal = +b.dataset.v; save(); renderMe(); }));
    $$('#rateSeg button').forEach((b) => (b.onclick = () => { S.settings.rate = +b.dataset.v; save(); speak('Hei! Jeg lærer norsk.'); renderMe(); }));
    $$('.toggle[data-s]').forEach((b) => (b.onclick = () => { S.settings[b.dataset.s] = !S.settings[b.dataset.s]; save(); b.classList.toggle('on'); }));
    $('#exp').onclick = () => {
      const code = btoa(unescape(encodeURIComponent(JSON.stringify(S))));
      sheet(`<h2>Резервная копия</h2>
        <p class="muted small" style="margin:6px 0 0">Скопируй этот код и сохрани его в заметках. На другом устройстве нажми «Загрузить копию» и вставь его.</p>
        <label class="field"><span>Код прогресса</span><textarea id="bkOut" readonly rows="5">${code}</textarea></label>
        <button class="btn primary block" id="bkCopy" style="margin-top:14px">Скопировать код</button>`, (sh) => {
        const ta = $('#bkOut', sh);
        $('#bkCopy', sh).onclick = () => {
          const ok = () => toast('📋', 'Код скопирован', 'Сохрани его в заметках');
          const fallback = () => { ta.focus(); ta.select(); toast('👆', 'Код выделен', 'Нажми «Скопировать» в меню телефона'); };
          try { navigator.clipboard.writeText(code).then(ok, fallback); } catch { fallback(); }
        };
      });
    };
    $('#imp').onclick = () => {
      sheet(`<h2>Загрузить копию</h2>
        <p class="muted small" style="margin:6px 0 0">Вставь код прогресса или выбери файл копии. Текущий прогресс на этом устройстве заменится.</p>
        <label class="field"><span>Код прогресса</span><textarea id="bkIn" rows="5" placeholder="вставь код сюда"></textarea></label>
        <label class="field"><span>…или файл .json</span><input id="bkFile" type="file" accept="application/json,.json,.txt" /></label>
        <button class="btn primary block" id="bkLoad" style="margin-top:14px">Загрузить</button>`, (sh, close) => {
        const apply = (txt) => {
          try {
            txt = txt.trim();
            const d = JSON.parse(txt.startsWith('{') ? txt : decodeURIComponent(escape(atob(txt))));
            if (!d || typeof d.xp !== 'number') throw 0;
            S = Object.assign(defaults(), d); rebuildWords(); save(); close(); toast('✅', 'Копия загружена', ''); renderMe();
          } catch { toast('⚠️', 'Код не подошёл', 'Проверь, что скопирован целиком'); }
        };
        $('#bkLoad', sh).onclick = async () => { const f = $('#bkFile', sh).files[0]; apply(f ? await f.text() : $('#bkIn', sh).value); };
      });
    };
    $('#reset').onclick = () => ask('Стереть весь прогресс?', 'XP, стрик, слова и ачивки удалятся с этого устройства. Это нельзя отменить.', 'Стереть всё', () => { S = defaults(); rebuildWords(); save(); go('home'); });
  }

  // ================= EXERCISES =================
  const ex = (type, w) => ({ type, w });
  function distractors(w, field, n = 3) {
    const sameCat = shuffle(ALL.filter((x) => x.id !== w.id && x.cat === w.cat && x[field] !== w[field]));
    const other = shuffle(ALL.filter((x) => x.id !== w.id && x.cat !== w.cat && x[field] !== w[field]));
    const out = []; const seen = new Set([w[field]]);
    for (const x of [...sameCat, ...other]) { if (!seen.has(x[field])) { out.push(x); seen.add(x[field]); } if (out.length >= n) break; }
    return out;
  }
  const norm = (s) => s.toLowerCase().replace(/[.,!?¡¿"«»…]/g, '').replace(/\s+/g, ' ').trim();
  const stripArt = (s) => s.replace(/^(en|ei|et|å) /, '');
  const deacc = (s) => s.replace(/æ/g, 'ae').replace(/ø/g, 'o').replace(/å/g, 'a').replace(/é/g, 'e');
  function lev(a, b) {
    const m = a.length, n = b.length; const d = Array.from({ length: m + 1 }, (_, i) => [i, ...Array(n).fill(0)]);
    for (let j = 1; j <= n; j++) d[0][j] = j;
    for (let i = 1; i <= m; i++) for (let j = 1; j <= n; j++) d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    return d[m][n];
  }
  function checkTyped(input, w) {
    const a = norm(input), t = norm(w.no);
    if (!a) return { r: 'bad' };
    if (a === t) return { r: 'ok' };
    if (stripArt(a) === stripArt(t)) {
      if (w.gender === 'ei' && a.startsWith('en ')) return { r: 'ok' };
      return { r: 'ok', note: w.gender ? `Не забывай артикль: ${w.no}` : w.pos === 'verb' ? `С инфинитивом: ${w.no}` : `Правильно: ${w.no}` };
    }
    if (deacc(stripArt(a)) === deacc(stripArt(t))) return { r: 'almost', note: `Почти! Обрати внимание на буквы æ ø å: ${w.no}` };
    if (lev(stripArt(a), stripArt(t)) === 1 && stripArt(t).length > 3) return { r: 'almost', note: `Опечатка? Правильно: ${w.no}` };
    return { r: 'bad' };
  }
  const PRAISE = ['Riktig!', 'Supert!', 'Bra jobba!', 'Kjempebra!', 'Nydelig!', 'Helt rått!', 'Perfekt!', 'Strålende!'];
  const PRAISE_RU = ['Верно!', 'Супер!', 'Отличная работа!', 'Великолепно!', 'Прекрасно!', 'Огонь!', 'Идеально!', 'Блестяще!'];

  // ================= SESSION ENGINE =================
  function startLesson(cat) {
    const plan = sessionPlan(cat);
    let { due, fresh } = plan;
    if (!due.length && !fresh.length) { const p = pool(1); due = shuffle(p).slice(0, 8); }
    const q = [];
    for (const w of fresh) { q.push(ex('intro', w)); q.push(ex('mcqNoRu', w)); }
    const rev = due.map((w) => {
      const b = box(w.id);
      const types = b <= 1 ? ['mcqNoRu', 'mcqRuNo', 'listen'] : b <= 3 ? ['mcqRuNo', 'listen', 'type', 'gender'] : ['type', 'type', 'listen', 'gender', 'mcqRuNo'];
      let t = pick(types); if (t === 'gender' && !w.gender) t = 'mcqRuNo'; if (t === 'type' && w.no.includes('…')) t = 'mcqRuNo';
      return ex(t, w);
    });
    q.push(...shuffle(rev));
    const second = shuffle(fresh).map((w) => { let t = pick(['mcqRuNo', 'listen', w.gender ? 'gender' : 'mcqRuNo']); return ex(t, w); });
    q.push(...second);
    const mw = shuffle([...fresh, ...due]).slice(0, 5);
    if (mw.length >= 4) q.push({ type: 'match', words: mw });
    runSession({ title: cat ? catOf(cat).name : 'Økt', queue: q, srs: true, lesson: true });
  }

  function runSession(cfg) {
    const ov = $('#overlay');
    document.body.classList.add('in-session');
    ov.hidden = false;
    const st = { i: 0, xp: 0, combo: 0, bestCombo: 0, right: 0, wrong: 0, results: {}, retried: new Set(), lives: cfg.lives || 0, score: 0, startT: Date.now(), timeLeft: cfg.timer || 0, done: false, newIds: new Set() };
    const queue = cfg.queue ? [...cfg.queue] : [];
    let timerId = null;
    ov.innerHTML = `<div class="inner">
      <div class="s-top"><button class="icon-btn" id="sClose">✕</button><div class="s-prog"><i id="sProg"></i></div><div id="sMeta" class="combo"></div></div>
      <div class="s-body" id="sBody"></div></div>`;
    $('#sClose').onclick = () => {
      if (st.done || st.i === 0) return st.done ? close() : finish(true);
      ask('Выйти из тренировки?', 'Набранные XP и ответы сохранятся.', 'Выйти', () => finish(true), 'Продолжить');
    };

    if (cfg.timer) {
      timerId = setInterval(() => {
        st.timeLeft--; meta();
        if (st.timeLeft <= 0) { clearInterval(timerId); finish(); }
      }, 1000);
    }
    if (cfg.stopwatch) timerId = setInterval(meta, 250);

    function meta() {
      const m = $('#sMeta'); if (!m) return;
      if (cfg.timer) { m.className = 'timer' + (st.timeLeft <= 10 ? ' low' : ''); m.textContent = `${st.timeLeft}s`; $('#sProg').style.width = `${(1 - st.timeLeft / cfg.timer) * 100}%`; return; }
      if (cfg.lives) { m.className = 'lives'; m.textContent = '♥'.repeat(st.lives) + '♡'.repeat(cfg.lives - st.lives); $('#sProg').style.width = `${Math.min(100, st.score * 3)}%`; return; }
      if (cfg.stopwatch) { m.className = 'timer'; m.textContent = `${((Date.now() - st.startT) / 1000).toFixed(1)}s`; }
      else { m.className = 'combo'; m.textContent = st.combo >= 2 ? `🔥×${st.combo}` : ''; }
      $('#sProg').style.width = `${(st.i / Math.max(1, queue.length)) * 100}%`;
    }

    function next() {
      if (st.done) return;
      $('.feedback')?.remove();
      let item;
      if (cfg.endless) item = cfg.endless();
      else { if (st.i >= queue.length) return finish(); item = queue[st.i]; }
      meta();
      const body = $('#sBody'); body.innerHTML = '';
      render(item, body);
    }

    function answered(item, ok, opts = {}) {
      const w = item.w;
      if (ok) {
        st.combo++; st.right++; st.bestCombo = Math.max(st.bestCombo, st.combo);
        let gain = item.type === 'type' ? 15 : 10;
        if (st.combo > 0 && st.combo % 5 === 0) { gain += 10; sfx('combo'); const m = $('#sMeta'); m && (m.classList.remove('bump'), void m.offsetWidth, m.classList.add('bump')); } else sfx('ok');
        st.xp += gain; st.score++;
        if (opts.x) { xpFloat(opts.x, opts.y, gain); if (st.combo % 5 === 0) sparks(opts.x, opts.y); }
        buzz(15);
        if (item.type === 'gender') S.stats.gender++;
      } else {
        st.combo = 0; st.wrong++; sfx('bad'); buzz([30, 40, 30]);
        if (cfg.lives) st.lives--;
        // повторить ошибку в конце обычной сессии
        if (!cfg.endless && w && !st.retried.has(w.id)) { st.retried.add(w.id); queue.push(ex(item.type === 'intro' ? 'mcqNoRu' : item.type, w)); }
      }
      if (w && cfg.srs) { if (!(w.id in st.results)) st.results[w.id] = ok; else if (!ok) st.results[w.id] = false; }
      S.stats.answers++; if (ok) S.stats.right++;
      meta();
      if (cfg.lives && st.lives <= 0) { setTimeout(() => feedback(item, ok, opts, () => finish()), 0); return; }
      if (cfg.fastNext && ok) { st.i++; setTimeout(next, 380); return; }
      feedback(item, ok, opts, () => { st.i++; next(); });
    }

    function feedback(item, ok, opts, cb) {
      const w = item.w; const k = Math.floor(Math.random() * PRAISE.length);
      const almost = opts.almost;
      const cls = ok ? (almost ? 'almost' : 'ok') : 'bad';
      const title = ok ? (opts.note ? 'Riktig, men…' : `${PRAISE[k]} <span class="muted small" style="font-family:var(--sans)">${PRAISE_RU[k]}</span>`) : almost ? 'Nesten!' : 'Ikke helt…';
      const answer = w ? `<b>${art(w)}</b> — ${esc(w.ru)}${w.exNo ? `<span class="muted">${esc(w.exNo)} — ${esc(w.exRu)}</span>` : ''}` : '';
      const fb = el(`<div class="feedback ${cls}"><div class="inner"><h3>${title}</h3><p>${opts.note ? esc(opts.note) + '<br>' : ''}${ok && !opts.note ? '' : answer}</p><button class="btn block">${cfg.lives && st.lives <= 0 ? 'Итоги' : 'Дальше'}</button></div></div>`);
      document.body.appendChild(fb);
      const btn = $('button', fb);
      btn.onclick = () => { fb.remove(); cb(); };
      setTimeout(() => btn.focus(), 50);
      if (!ok && w && S.settings.autoplay) speak(w.no);
    }

    function render(item, body) {
      const w = item.w;
      if (item.type === 'intro') {
        st.newIds.add(w.id);
        body.innerHTML = `<div class="intro-card"><span class="badge">Nytt ord · новое слово</span>
          <div class="prompt">${art(w)}</div><div class="ru-big">${esc(w.ru)}</div>
          <div class="speak"><button id="sp">🔊</button></div>
          ${w.gender ? `<div class="muted small">род: <b class="art ${w.gender}">${w.gender}</b>${w.gender === 'ei' ? ' (в букмоле можно и en)' : ''}</div>` : ''}
          ${w.exNo ? `<div class="ex"><b>${esc(w.exNo)}</b>${esc(w.exRu)}</div>` : ''}</div>
          <div class="s-foot"><button class="btn primary block" id="go">Запомнила →</button></div>`;
        $('#sp').onclick = () => speak(w.exNo ? w.no : w.no);
        if (S.settings.autoplay) setTimeout(() => speak(w.no), 250);
        $('#go').onclick = () => { st.i++; next(); };
        return;
      }
      if (item.type === 'mcqNoRu' || item.type === 'mcqRuNo' || item.type === 'listen') {
        const field = item.type === 'mcqNoRu' ? 'ru' : 'no';
        const opts = shuffle([w, ...distractors(w, field)]);
        const head = item.type === 'mcqNoRu'
          ? `<div class="kicker">Что это значит?</div><div class="prompt">${art(w)}</div><div class="speak"><button id="sp">🔊</button></div>`
          : item.type === 'mcqRuNo'
            ? `<div class="kicker">Как сказать по-норвежски?</div><div class="prompt ru">${esc(w.ru)}</div><div style="height:22px"></div>`
            : `<div class="kicker">Lytt · что ты слышишь?</div><div class="speak" style="margin:26px 0 30px"><button id="sp" class="big">🔊</button></div>`;
        body.innerHTML = `${head}<div class="options">${opts.map((o) => `<button class="opt" data-id="${esc(o.id)}">${field === 'ru' ? esc(o.ru) : art(o)}</button>`).join('')}</div>`;
        const sp = $('#sp');
        if (sp) { sp.onclick = () => { speak(w.no); sp.classList.remove('playing'); void sp.offsetWidth; sp.classList.add('playing'); }; }
        if (item.type === 'listen' || (item.type === 'mcqNoRu' && S.settings.autoplay)) setTimeout(() => speak(w.no), 250);
        let locked = false;
        $$('.opt', body).forEach((b) => (b.onclick = (e) => {
          if (locked) return; locked = true;
          const ok = b.dataset.id === w.id;
          $$('.opt', body).forEach((x) => { if (x.dataset.id === w.id) x.classList.add('right'); else if (x === b) x.classList.add('wrong'); else x.classList.add('faded'); });
          if (ok && item.type !== 'mcqNoRu') speak(w.no);
          answered(item, ok, { x: e.clientX, y: e.clientY });
        }));
        return;
      }
      if (item.type === 'type') {
        body.innerHTML = `<div class="kicker">Напиши по-норвежски</div><div class="prompt ru">${esc(w.ru)}</div>
          <div class="hint" style="margin:0 0 18px">${w.gender ? 'существительное — с артиклем' : w.pos === 'verb' ? 'глагол — с «å»' : '&nbsp;'}</div>
          <form class="typer" id="tf"><input id="ti" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" placeholder="skriv her…" />
          <div class="keys">${['æ', 'ø', 'å'].map((k) => `<button type="button" data-k="${k}">${k}</button>`).join('')}</div>
          <div class="s-foot" style="margin-top:18px"><button class="btn violet block" type="submit">Проверить</button></div>
          <div class="hint"><button type="button" id="skip" style="color:var(--dim);text-decoration:underline">не знаю</button></div></form>`;
        const inp = $('#ti'); setTimeout(() => inp.focus(), 200);
        $$('.keys button', body).forEach((b) => (b.onclick = () => insertAtCursor(inp, b.dataset.k)));
        let locked = false;
        $('#skip').onclick = () => { if (locked) return; locked = true; inp.classList.add('wrong'); answered(item, false); };
        $('#tf').onsubmit = (e) => {
          e.preventDefault(); if (locked) return;
          const res = checkTyped(inp.value, w);
          if (res.r === 'bad' && !inp.value.trim()) return;
          locked = true; inp.blur();
          const r = inp.getBoundingClientRect();
          if (res.r === 'ok') { inp.classList.add('right'); speak(w.no); answered(item, true, { note: res.note, x: r.left + r.width / 2, y: r.top }); }
          else if (res.r === 'almost') { inp.classList.add('right'); speak(w.no); answered(item, true, { note: res.note, almost: true, x: r.left + r.width / 2, y: r.top }); }
          else { inp.classList.add('wrong'); answered(item, false); }
        };
        return;
      }
      if (item.type === 'gender') {
        body.innerHTML = `<div class="kicker">En eller et?</div>
          <div class="gender-word"><span class="blank">?</span>${esc(w.bare)}</div>
          <div class="muted" style="text-align:center;margin:-8px 0 28px">${esc(w.ru)}</div>
          <div class="gender-btns"><button class="opt" data-g="en">en</button><button class="opt" data-g="et">et</button></div>
          <div class="hint">слова рода «ei» тоже можно с «en»</div>`;
        let locked = false;
        $$('.opt', body).forEach((b) => (b.onclick = (e) => {
          if (locked) return; locked = true;
          const g = w.gender === 'ei' ? 'en' : w.gender;
          const ok = b.dataset.g === g;
          b.classList.add(ok ? 'right' : 'wrong');
          if (!ok) $(`.opt[data-g="${g}"]`, body).classList.add('right');
          $('.blank', body).textContent = w.gender; $('.blank', body).style.color = `var(--${w.gender})`;
          speak(w.no);
          answered(item, ok, { x: e.clientX, y: e.clientY });
        }));
        return;
      }
      if (item.type === 'match') {
        const ws = item.words;
        const L = shuffle(ws), R = shuffle(ws);
        body.innerHTML = `<div class="kicker" style="margin-bottom:18px">Собери пары</div>
          <div class="match"><div class="col">${L.map((x) => `<button class="opt" data-side="l" data-id="${esc(x.id)}">${art(x)}</button>`).join('')}</div>
          <div class="col">${R.map((x) => `<button class="opt" data-side="r" data-id="${esc(x.id)}">${esc(x.ru.split(/[;(]/)[0].trim())}</button>`).join('')}</div></div>`;
        let sel = null, left = ws.length, mistakes = 0;
        $$('.opt', body).forEach((b) => (b.onclick = (e) => {
          if (b.classList.contains('done')) return;
          if (b.dataset.side === 'l') speak(BY_ID[b.dataset.id].no);
          if (!sel || sel.dataset.side === b.dataset.side) { sel && sel.classList.remove('sel'); sel = b; b.classList.add('sel'); sfx('tap'); return; }
          if (sel.dataset.id === b.dataset.id) {
            [sel, b].forEach((x) => { x.classList.remove('sel'); x.classList.add('right', 'done'); });
            sfx('ok'); buzz(10); st.xp += 3; st.combo++; st.bestCombo = Math.max(st.bestCombo, st.combo); left--; sel = null;
            if (!left) { sparks(e.clientX, e.clientY); xpFloat(e.clientX, e.clientY, 3 * ws.length); if (!mistakes) st.xp += 5; st.right++; setTimeout(() => { st.i++; next(); }, 600); }
            meta();
          } else {
            const a = sel; [a, b].forEach((x) => x.classList.add('wrong'));
            sfx('bad'); buzz(30); mistakes++; st.combo = 0; meta();
            setTimeout(() => [a, b].forEach((x) => x.classList.remove('wrong', 'sel')), 450); sel = null;
          }
        }));
      }
    }

    function finish(aborted) {
      if (st.done) return; st.done = true;
      clearInterval(timerId);
      $('.feedback')?.remove();
      // SRS
      if (cfg.srs) for (const [id, ok] of Object.entries(st.results)) grade(id, ok);
      const elapsed = (Date.now() - st.startT) / 1000;
      let bonus = 0;
      const total = st.right + st.wrong;
      if (!aborted && cfg.lesson) { bonus += 10; if (st.wrong === 0 && total > 3) { bonus += 10; S.stats.perfect++; } }
      if (!aborted && cfg.game === 'par') { bonus += Math.max(0, Math.round(40 - elapsed / 2)); }
      st.xp += bonus;
      S.stats.bestCombo = Math.max(S.stats.bestCombo, st.bestCombo);
      let record = false;
      if (!aborted && cfg.game) {
        const val = cfg.game === 'par' ? Math.round(elapsed) : st.score;
        const prev = S.best[cfg.game];
        if (prev == null || (cfg.game === 'par' ? val < prev : val > prev)) { S.best[cfg.game] = val; record = prev != null; }
      }
      let extended = false;
      if (st.xp > 0) { S.stats.sessions++; extended = addXP(st.xp); }
      save(); checkAch();

      if (aborted && st.xp === 0) return close();
      const accPct = total ? Math.round((st.right / total) * 100) : 100;
      const icon = aborted ? '🌙' : accPct === 100 ? '💎' : accPct >= 80 ? '🌌' : accPct >= 50 ? '🔥' : '🌱';
      const msg = aborted ? ['Ha det!', 'Возвращайся скорее'] : accPct === 100 ? ['Feilfritt!', 'Без единой ошибки'] : accPct >= 80 ? ['Kjempebra!', 'Отличная тренировка'] : accPct >= 50 ? ['Bra jobba!', 'Хорошая работа'] : ['Øvelse gjør mester', 'Повторение — мать учения'];
      const gameLine = cfg.game ? (cfg.game === 'par' ? `Время: <b>${elapsed.toFixed(1)} c</b>` : `Счёт: <b>${st.score}</b>`) + (record ? ' · 🏆 новый рекорд!' : '') : '';
      $('#sBody').innerHTML = `<div class="result">
        <div class="big-ic">${icon}</div>
        <h1>${msg[0]}</h1><div class="muted">${msg[1]}</div>
        ${gameLine ? `<div style="margin-top:10px">${gameLine}</div>` : ''}
        <div class="tiles">
          <div class="tile xp"><b>+${st.xp}</b><span>XP</span></div>
          <div class="tile acc"><b>${accPct}%</b><span>точность</span></div>
          <div class="tile cb"><b>×${st.bestCombo}</b><span>комбо</span></div>
        </div>
        ${extended ? `<div class="streak-up">🔥 Стрик: ${S.streak.count} ${plural(S.streak.count, 'день', 'дня', 'дней')}!</div>` : ''}
        ${st.newIds.size ? `<div class="muted small" style="margin-bottom:14px">Новых слов: ${st.newIds.size} — повторим их завтра</div>` : ''}
      </div>
      <div class="s-foot" style="display:grid;gap:10px">
        <button class="btn primary block" id="again">${cfg.game ? 'Ещё раз' : 'Ещё тренировку'}</button>
        <button class="btn ghost block" id="home">Готово</button>
      </div>`;
      $('#sProg').style.width = '100%'; $('#sMeta').textContent = '';
      sfx('level');
      const r = $('.big-ic').getBoundingClientRect(); sparks(r.left + r.width / 2, r.top + r.height / 2, 30);
      $('#again').onclick = () => { close(); cfg.game ? startGame(cfg.game) : startLesson(); };
      $('#home').onclick = close;
    }
    function close() {
      clearInterval(timerId);
      $('.feedback')?.remove();
      ov.hidden = true; ov.innerHTML = '';
      document.body.classList.remove('in-session');
      if ('speechSynthesis' in window) speechSynthesis.cancel();
      go(tab);
    }
    next();
  }

  // keyboard: Enter → Дальше
  document.addEventListener('keydown', (e) => { if (e.key === 'Enter') { const b = $('.feedback button'); if (b) { e.preventDefault(); b.click(); } } });

  // ================= boot =================
  checkStreak();
  go('home');
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js').catch(() => {});
})();
