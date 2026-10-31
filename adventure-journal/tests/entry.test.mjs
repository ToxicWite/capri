// Runs the built entry.js against the mock runtime: node --test tests/
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createTavo, loadEntry } from './mock-tavo.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BUILD = path.join(ROOT, 'build', 'adventure-journal');

function setup(opts = {}) {
  const env = createTavo({ catalogDir: path.join(BUILD, 'locales'), ...opts });
  loadEntry(env, path.join(BUILD, 'entry.js'));
  return env;
}

const PATCH = JSON.stringify({
  location: 'Old mill',
  stats: { HP: 85, Gold: 35 },
  add_items: [{ name: 'Rope', qty: 1 }],
  quests: [{ title: 'Find the miller', status: 'active', note: 'He vanished at night' }],
  relations: [{ name: 'Lyra', attitude: 'wary', value: 10 }],
});

async function reply(env, text, answer) {
  env.addMessage('user', 'I go to the mill.');
  const m = env.addMessage('assistant', text);
  if (answer !== undefined) env.tavo._state.answers.generate.push(answer);
  await env.emit('message:added', { chatId: 1, change: 'added', message: m });
  return m;
}

test('creates a localized journal from the default template', async () => {
  const env = setup({ locale: 'ru' });
  await env.emit('chat:opened', { chatId: 1 });
  const j = env.journal();
  assert.equal(j.template, 'fantasy');
  assert.deepEqual(j.stats.map((s) => s.name), ['Здоровье', 'Мана', 'Золото']);
});

test('auto mode applies model changes and reports them', async () => {
  const env = setup();
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'You took 15 damage but found 15 gold and a rope.', '```json\n' + PATCH + '\n```');
  const j = env.journal();
  assert.equal(j.status.location, 'Old mill');
  assert.equal(j.stats.find((s) => s.name === 'HP').value, 85);
  assert.equal(j.stats.find((s) => s.name === 'Gold').value, 35);
  assert.deepEqual(j.inventory, [{ name: 'Rope', qty: 1, note: '' }]);
  assert.equal(j.quests[0].title, 'Find the miller');
  assert.equal(j.relations[0].value, 10);
  assert.equal(j.undo.length, 1);
  assert.match(j.summary, /HP 85\/100/);
  assert.ok(env.tavo._state.log.toasts.some((t) => t.includes('HP: 100 → 85')));
  const { prompt, options } = env.tavo._state.log.prompts[0];
  assert.match(prompt, /same language as the story/);
  assert.match(prompt, /You took 15 damage/);
  assert.equal(options.context, false);
  assert.equal(options.timeout, 45000);
});

test('generation:prepare injects the journal without touching empty journals', async () => {
  const env = setup({ config: { defaultTemplate: 'custom', customStats: '' } });
  await env.emit('chat:opened', { chatId: 1 });
  let ev = await env.emit('generation:prepare', { text: 'Hello' });
  assert.equal(ev.text, 'Hello');
  await reply(env, 'story', PATCH);
  ev = await env.emit('generation:prepare', { text: 'Hello' });
  assert.match(ev.text, /^<adventure_journal>/);
  assert.match(ev.text, /Location: Old mill/);
  assert.match(ev.text, /Hello$/);
});

test('injection can be switched off', async () => {
  const env = setup({ config: { injectState: false } });
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', PATCH);
  const ev = await env.emit('generation:prepare', { text: 'Hello' });
  assert.equal(ev.text, 'Hello');
});

test('a regenerated reply rolls back its changes and is read again', async () => {
  const env = setup();
  await env.emit('chat:opened', { chatId: 1 });
  const m = await reply(env, 'You took 15 damage.', JSON.stringify({ stats: { HP: 85 } }));
  assert.equal(env.journal().stats[0].value, 85);

  // Metadata-only update with identical content: nothing happens.
  await env.emit('message:updated', { message: { ...m } });
  assert.equal(env.tavo._state.log.prompts.length, 1);

  m.content = 'You dodge the blow but lose 5 HP.';
  env.tavo._state.answers.generate.push(JSON.stringify({ stats: { HP: 95 } }));
  await env.emit('message:updated', { message: { ...m } });
  assert.equal(env.journal().stats[0].value, 95);
  assert.equal(env.journal().undo.length, 1);
});

test('deleting a reply reverts what it changed', async () => {
  const env = setup();
  await env.emit('chat:opened', { chatId: 1 });
  const m = await reply(env, 'story', PATCH);
  await env.emit('message:deleted', { message: { id: m.id } });
  const j = env.journal();
  assert.equal(j.inventory.length, 0);
  assert.equal(j.stats[0].value, 100);
  assert.equal(j.status.location, '');
});

test('confirm mode stores proposed changes instead of applying them', async () => {
  const env = setup({ config: { updateMode: 'confirm' } });
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', PATCH);
  const j = env.journal();
  assert.equal(j.inventory.length, 0);
  assert.ok(j.pending);
  assert.equal(j.pending.data.inventory[0].name, 'Rope');
  assert.ok(j.pending.changes.length >= 5);
});

test('manual mode never calls the model by itself', async () => {
  const env = setup({ config: { updateMode: 'manual' } });
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', PATCH);
  assert.equal(env.tavo._state.log.prompts.length, 0);
  env.tavo._state.answers.generate.push(PATCH);
  await env.emit('sidebar:update-now');
  assert.equal(env.journal().inventory[0].name, 'Rope');
});

test('updateEvery batches several replies into one request', async () => {
  const env = setup({ config: { updateEvery: 2 } });
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'first reply');
  assert.equal(env.tavo._state.log.prompts.length, 0);
  await reply(env, 'second reply', PATCH);
  assert.equal(env.tavo._state.log.prompts.length, 1);
  const { prompt } = env.tavo._state.log.prompts[0];
  assert.match(prompt, /first reply/);
  assert.match(prompt, /second reply/);
});

test('unreadable model output leaves the journal unchanged', async () => {
  const env = setup();
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', 'Sorry, I cannot do that.');
  assert.equal(env.journal().undo.length, 0);
  assert.ok(env.tavo._state.log.toasts.some((t) => /unreadable/.test(t)));
});

test('model errors are reported, not thrown', async () => {
  const env = setup();
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', new Error('No API configured'));
  assert.ok(env.tavo._state.log.toasts.some((t) => /No API configured/.test(t)));
});

test('undo restores the previous state', async () => {
  const env = setup();
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', PATCH);
  await env.emit('sidebar:undo-update');
  assert.equal(env.journal().inventory.length, 0);
  assert.equal(env.journal().stats[0].value, 100);
});

test('switching template can keep entries', async () => {
  const env = setup();
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', PATCH);
  env.tavo._state.answers.select.push('horror');
  env.tavo._state.answers.ask.push({ status: 'answered', answer: 'keep', source: 'option' });
  await env.emit('sidebar:choose-template');
  const j = env.journal();
  assert.equal(j.template, 'horror');
  assert.equal(j.inventory[0].name, 'Rope');
  assert.deepEqual(j.sections, ['status', 'stats', 'quests', 'inventory', 'relations']);
});

test('switching template fresh uses the custom stats setting', async () => {
  const env = setup({ config: { customStats: 'Ammo=12/30; Fuel=40' } });
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', PATCH);
  env.tavo._state.answers.select.push('custom');
  env.tavo._state.answers.ask.push({ status: 'answered', answer: 'fresh', source: 'option' });
  await env.emit('sidebar:choose-template');
  const j = env.journal();
  assert.equal(j.template, 'custom');
  assert.deepEqual(j.stats, [{ name: 'Ammo', value: 12, max: 30 }, { name: 'Fuel', value: 40 }]);
  assert.equal(j.inventory.length, 0);
  // The fresh start can be undone.
  await env.emit('sidebar:undo-update');
  assert.equal(env.journal().inventory[0].name, 'Rope');
});

test('dice roll appends a localized result to the input', async () => {
  const env = setup({ locale: 'zh-CN' });
  await env.emit('chat:opened', { chatId: 1 });
  env.tavo._state.answers.select.push('2d6', '0');
  await env.emit('inputActions:roll-dice');
  assert.match(env.input, /^\*🎲 生命检定（100），2d6：\d\+\d = \d+\*$/);
});

test('stats are clamped to their maximum and quests change status', async () => {
  const env = setup();
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', PATCH);
  await reply(env, 'healed and found the miller', JSON.stringify({
    stats: { HP: 140 },
    quests: [{ title: 'find the MILLER', status: 'done' }],
    remove_items: [{ name: 'rope' }],
  }));
  const j = env.journal();
  assert.equal(j.stats[0].value, 100);
  assert.equal(j.quests.length, 1);
  assert.equal(j.quests[0].status, 'done');
  assert.equal(j.inventory.length, 0);
});

test('export produces an importable file', async () => {
  const env = setup();
  await env.emit('chat:opened', { chatId: 1 });
  await reply(env, 'story', PATCH);
  await env.emit('sidebar:export-journal');
  const out = env.tavo.file.exported[0];
  assert.equal(out.name, 'adventure-journal.json');
  const data = JSON.parse(out.content);
  assert.equal(data.format, 'adventure-journal');
  assert.equal(data.inventory[0].name, 'Rope');
});
