// Minimal in-memory imitation of the Tavo plugin runtime, covering only the
// APIs Adventure Journal uses. Lets tests run the built entry.js in Node.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

function get(obj, p) {
  return p.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

export function createTavo({ locale = 'en', config = {}, catalogDir }) {
  const catalogs = {};
  for (const f of fs.readdirSync(catalogDir)) {
    catalogs[f.replace(/\.json$/, '')] = JSON.parse(fs.readFileSync(path.join(catalogDir, f), 'utf8'));
  }
  const manifest = JSON.parse(fs.readFileSync(path.join(catalogDir, '..', 'manifest.json'), 'utf8'));
  const defaults = {};
  for (const f of manifest.contributes.settings.schema) {
    if (!f.key) continue;
    let d = f.default;
    if (d && typeof d === 'object' && d.$t) d = catalogs[locale][d.$t];
    defaults[f.key] = d ?? null;
  }

  const vars = { chat: {}, global: {} };
  const handlers = {};
  const log = { toasts: [], prompts: [], selects: [], asks: [] };
  const messages = [];
  let nextId = 100;
  let input = '';

  const tavo = {
    _state: { vars, handlers, log, messages, answers: { generate: [], select: [], ask: [] } },
    plugin: {
      on(type, fn) { (handlers[type] ||= []).push(fn); },
      onInputAction(id, fn) { this.on('inputActions:' + id, fn); },
      onSidebarAction(id, fn) { this.on('sidebar:' + id, fn); },
      onLastMessageAction(id, fn) { this.on('lastMessageActions:' + id, fn); },
      config: {
        get: (k) => (k in config ? config[k] : defaults[k] ?? null),
        all: () => ({ ...defaults, ...config }),
      },
      i18n: {
        get locale() { return locale; },
        get requestedLocale() { return locale; },
        t(key, params) {
          let s = catalogs[locale]?.[key] ?? catalogs.en?.[key] ?? key;
          for (const [k, v] of Object.entries(params || {})) s = s.split('{' + k + '}').join(String(v));
          return s;
        },
        onChange() { return () => {}; },
      },
    },
    variable: {
      async get(name, scope = 'chat') { const v = get(vars[scope], name); return v === undefined ? null : JSON.parse(JSON.stringify(v)); },
      async set(name, value, scope = 'chat') { vars[scope][name] = JSON.parse(JSON.stringify(value)); },
    },
    message: {
      async count() { return messages.length; },
      async find(range, filter = {}) {
        const start = Array.isArray(range) ? range[0] ?? 0 : range;
        return messages.slice(start).filter((m) => filter.hidden === undefined || m.hidden === filter.hidden).map((m) => ({ ...m }));
      },
      async get(id) { const m = messages.find((x) => x.id === id); return m ? { ...m } : null; },
    },
    input: {
      async get() { return input; },
      async set(v) { input = v; },
      async append(v) { input += v; },
    },
    async generate(prompt, options) {
      log.prompts.push({ prompt, options });
      const next = tavo._state.answers.generate.shift();
      if (next instanceof Error) throw next;
      return next ?? '{}';
    },
    utils: {
      toast(text) { log.toasts.push(text); },
      async select(options, title) { log.selects.push({ options, title }); return tavo._state.answers.select.shift() ?? null; },
      async ask(q) { log.asks.push(q); return tavo._state.answers.ask.shift() ?? { status: 'cancelled' }; },
    },
    file: {
      exported: [],
      async export(name, content) { this.exported.push({ name, content }); },
    },
  };

  return {
    tavo,
    get input() { return input; },
    addMessage(role, content) {
      const m = { id: nextId++, role, content, hidden: false };
      messages.push(m);
      return m;
    },
    async emit(type, payload = {}) {
      const event = { type, pluginId: manifest.id, at: new Date().toISOString(), ...payload };
      for (const fn of handlers[type] || []) await fn(event);
      return event;
    },
    journal() { return vars.chat.adventureJournal; },
  };
}

export function loadEntry(env, entryPath) {
  const code = fs.readFileSync(entryPath, 'utf8');
  const context = vm.createContext({ tavo: env.tavo, console, setTimeout, Date, Math, JSON, Promise });
  vm.runInContext(code, context, { filename: 'entry.js' });
  return context;
}
