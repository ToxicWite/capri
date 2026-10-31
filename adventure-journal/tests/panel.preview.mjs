// Renders the built panel in Chromium with a mocked tavo runtime, exercises
// the main controls and saves screenshots. Usage: node tests/panel.preview.mjs
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BUILD = path.join(ROOT, 'build', 'adventure-journal');
const OUT = path.join(ROOT, 'docs', 'screenshots');
fs.mkdirSync(OUT, { recursive: true });

const panelHtml = fs.readFileSync(path.join(BUILD, 'ui', 'panel.html'), 'utf8');

const SAMPLE = {
  en: {
    location: 'Old mill by the river', time: 'Night, day 3', conditions: 'Bruised left arm',
    stats: [{ name: 'HP', value: 85, max: 100 }, { name: 'Mana', value: 20, max: 50 }, { name: 'Gold', value: 35 }],
    inventory: [{ name: 'Rope', qty: 1, note: '' }, { name: 'Healing potion', qty: 2, note: 'Restores 20 HP' }],
    quests: [{ title: 'Find the miller', status: 'active', note: 'He vanished at night' }, { title: 'Reach the village', status: 'done', note: '' }],
    relations: [{ name: 'Lyra', attitude: 'wary', value: 10, note: 'Hides something' }, { name: 'Bandit chief', attitude: 'hostile', value: -70, note: '' }],
    change: [{ key: 'change.stat', params: { name: 'HP', from: 85, to: 70 } }, { key: 'change.itemAdd', params: { name: 'Old key', qty: 1 } }],
  },
  ru: {
    location: 'Старая мельница у реки', time: 'Ночь, третий день', conditions: 'Ушиб левой руки',
    stats: [{ name: 'Здоровье', value: 85, max: 100 }, { name: 'Мана', value: 20, max: 50 }, { name: 'Золото', value: 35 }],
    inventory: [{ name: 'Верёвка', qty: 1, note: '' }, { name: 'Зелье лечения', qty: 2, note: 'Восстанавливает 20 здоровья' }],
    quests: [{ title: 'Найти мельника', status: 'active', note: 'Пропал ночью' }, { title: 'Добраться до деревни', status: 'done', note: '' }],
    relations: [{ name: 'Лира', attitude: 'настороженна', value: 10, note: 'Что-то скрывает' }, { name: 'Главарь разбойников', attitude: 'враждебен', value: -70, note: '' }],
    change: [{ key: 'change.stat', params: { name: 'Здоровье', from: 85, to: 70 } }, { key: 'change.itemAdd', params: { name: 'Старый ключ', qty: 1 } }],
  },
  'zh-CN': {
    location: '河边的旧磨坊', time: '第三天夜里', conditions: '左臂淤伤',
    stats: [{ name: '生命', value: 85, max: 100 }, { name: '法力', value: 20, max: 50 }, { name: '金币', value: 35 }],
    inventory: [{ name: '绳子', qty: 1, note: '' }, { name: '治疗药水', qty: 2, note: '恢复 20 点生命' }],
    quests: [{ title: '寻找磨坊主', status: 'active', note: '他在夜里失踪了' }, { title: '抵达村庄', status: 'done', note: '' }],
    relations: [{ name: '莉拉', attitude: '警惕', value: 10, note: '似乎在隐瞒什么' }, { name: '强盗头子', attitude: '敌对', value: -70, note: '' }],
    change: [{ key: 'change.stat', params: { name: '生命', from: 85, to: 70 } }, { key: 'change.itemAdd', params: { name: '旧钥匙', qty: 1 } }],
  },
};

function state(locale, withPending) {
  const s = SAMPLE[locale];
  const data = { status: { location: s.location, time: s.time, conditions: s.conditions }, stats: s.stats, inventory: s.inventory, quests: s.quests, relations: s.relations };
  return {
    schema: 1, template: 'fantasy', sections: ['status', 'stats', 'inventory', 'quests', 'relations'],
    ...JSON.parse(JSON.stringify(data)),
    pending: withPending ? {
      messageId: 7, hash: 'x', changes: s.change, at: new Date().toISOString(),
      data: { ...JSON.parse(JSON.stringify(data)), stats: [{ ...s.stats[0], value: 70 }, s.stats[1], s.stats[2]], inventory: [...s.inventory, { name: s.change[1].params.name, qty: 1, note: '' }] },
    } : null,
    undo: [{ messageId: 5, data }], processed: {}, lastUpdateAt: '2026-10-31T19:42:00.000Z', rev: 3, summary: '',
  };
}

function page(locale, seed, answers) {
  const catalog = fs.readFileSync(path.join(BUILD, 'locales', locale + '.json'), 'utf8');
  return `<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  :root { --tavo-inset-top-bar: 56px; --tavo-inset-bottom-input: 64px; }
  body { margin: 0; background: #1b1d22 linear-gradient(#2a2f39, #15171b); height: 100vh; font-family: sans-serif; }
  .chat { padding: 70px 14px; color: #ddd; } .bubble { background: #2b313c; padding: 10px 12px; border-radius: 12px; margin: 8px 0; max-width: 80%; }
  .topbar { position: fixed; top: 0; left: 0; right: 0; height: 56px; background: #111; } .composer { position: fixed; bottom: 0; left: 0; right: 0; height: 64px; background: #111; }
</style>
<script>
  window.__vars = { chat: { adventureJournal: ${JSON.stringify(seed)} }, global: {} };
  window.__answers = ${JSON.stringify(answers || [])};
  window.__toasts = [];
  const catalog = ${catalog};
  var tavo = {
    plugin: {
      config: { get: (k) => ({ showButton: true, defaultTemplate: 'fantasy' })[k] ?? null, all: () => ({ showButton: true, defaultTemplate: 'fantasy' }) },
      i18n: {
        locale: ${JSON.stringify(locale)}, requestedLocale: ${JSON.stringify(locale)},
        t(key, params) { let s = catalog[key] ?? key; for (const k in (params || {})) s = s.split('{' + k + '}').join(String(params[k])); return s; },
        onChange() { return () => {}; },
      },
    },
    variable: {
      async get(n, scope = 'chat') { const v = window.__vars[scope][n]; return v == null ? null : JSON.parse(JSON.stringify(v)); },
      async set(n, v, scope = 'chat') { window.__vars[scope][n] = JSON.parse(JSON.stringify(v)); },
    },
    ui: { getInsets: () => ({ topSafe: 0, topBar: 56, bottomInput: 64, bottomSafe: 0 }), onInsetsChanged: () => () => {} },
    utils: {
      toast(t) { window.__toasts.push(t); },
      async ask(q) { return window.__answers.shift() ?? { status: 'cancelled' }; },
      async select() { return window.__answers.shift() ?? null; },
    },
  };
</script></head><body>
<div class="topbar"></div>
<div class="chat"><div class="bubble">…</div><div class="bubble" style="margin-left:auto">…</div></div>
<div class="composer"></div>
${panelHtml}
</body></html>`;
}

async function journal(p) {
  return p.evaluate(() => window.__vars.chat.adventureJournal);
}

const browser = await chromium.launch();
try {
  for (const locale of ['ru', 'en', 'zh-CN']) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 2 });
    const p = await ctx.newPage();
    const errors = [];
    p.on('pageerror', (e) => errors.push(e.message));
    await p.setContent(page(locale, state(locale, true), []));
    await p.waitForSelector('#aj-fab:not([hidden])');
    assert.equal(await p.textContent('#aj-badge'), '2', 'badge shows pending count');
    await p.click('#aj-fab');
    await p.waitForSelector('#aj-panel:not([hidden])');
    await p.screenshot({ path: path.join(OUT, `panel-status-${locale}.png`) });

    // Stats tab, then +/- buttons.
    await p.click('.aj-tab >> nth=1');
    await p.screenshot({ path: path.join(OUT, `panel-stats-${locale}.png`) });
    await p.click('.aj-item >> nth=0 >> button >> nth=0');
    await p.waitForFunction(() => window.__vars.chat.adventureJournal.stats[0].value === 84);

    // Apply pending changes.
    await p.click('#aj-pending .aj-primary');
    await p.waitForFunction(() => !window.__vars.chat.adventureJournal.pending);
    let j = await journal(p);
    assert.equal(j.stats[0].value, 70, 'pending applied');
    assert.equal(j.inventory.length, 3);
    assert.equal(j.undo.length, 2);

    // Relations tab.
    await p.click('.aj-tab >> nth=4');
    await p.screenshot({ path: path.join(OUT, `panel-relations-${locale}.png`) });

    // Undo restores the pre-apply state.
    await p.click('#aj-foot button');
    await p.waitForFunction(() => window.__vars.chat.adventureJournal.undo.length === 1);
    j = await journal(p);
    assert.equal(j.inventory.length, 2, 'undo removed applied item');

    // Quests tab with grouped statuses.
    await p.click('.aj-tab >> nth=3');
    await p.screenshot({ path: path.join(OUT, `panel-quests-${locale}.png`) });

    // Drag the launcher: it moves, stays in bounds and does not toggle the panel.
    await p.click('#aj-close');
    const box = await p.locator('#aj-fab').boundingBox();
    await p.mouse.move(box.x + 20, box.y + 20);
    await p.mouse.down();
    await p.mouse.move(box.x - 150, box.y + 900, { steps: 8 });
    await p.mouse.up();
    const moved = await p.locator('#aj-fab').boundingBox();
    assert.ok(await p.isHidden('#aj-panel'), 'drag does not open the panel');
    assert.ok(moved.y + moved.height <= 780 - 64, 'launcher stays above the composer');
    await p.waitForFunction(() => !!(window.__vars.global.adventureJournalUi || {}).pos);

    assert.deepEqual(errors, [], 'no page errors');
    await ctx.close();
    console.log('ok panel', locale);
  }

  // Adding an item through the native ask dialog.
  const ctx = await browser.newContext({ viewport: { width: 390, height: 780 } });
  const p = await ctx.newPage();
  await p.setContent(page('en', state('en', false), [{ status: 'answered', answer: 'Lantern', source: 'custom' }]));
  await p.click('#aj-fab');
  await p.click('.aj-tab >> nth=2');
  await p.click('.aj-add');
  await p.waitForFunction(() => window.__vars.chat.adventureJournal.inventory.length === 3);
  assert.equal((await journal(p)).inventory[2].name, 'Lantern');
  assert.equal(await p.isHidden('#aj-badge'), true, 'no badge without pending changes');
  console.log('ok add item');

  // Untrusted names are rendered as text, never as HTML.
  const evil = state('en', false);
  evil.inventory = [{ name: '<img src=x onerror="window.__pwned=1">', qty: 1, note: '' }];
  await p.setContent(page('en', evil, []));
  await p.click('#aj-fab');
  await p.click('.aj-tab >> nth=2');
  assert.equal(await p.evaluate(() => window.__pwned), undefined);
  assert.equal(await p.locator('.aj-body img').count(), 0);
  console.log('ok escaping');
  await ctx.close();
} finally {
  await browser.close();
}
