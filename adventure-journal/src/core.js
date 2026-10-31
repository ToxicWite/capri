// Adventure Journal core: shared by entry.js and the chat panel.
// The build script inlines this file into both, so it must stay a classic script
// without imports and must not touch the DOM.

var AJ = (function () {
  var VAR = 'adventureJournal';
  var UI_VAR = 'adventureJournalUi';
  var SCHEMA = 1;
  var MAX_UNDO = 6;
  var SECTIONS = ['status', 'stats', 'inventory', 'quests', 'relations'];

  // Genre templates. Labels live in the locale catalogs under
  // sec.<template>.<section> and stat.<template>.<id>.
  var TEMPLATES = {
    fantasy: {
      sections: ['status', 'stats', 'inventory', 'quests', 'relations'],
      stats: [
        { id: 'hp', value: 100, max: 100 },
        { id: 'mana', value: 50, max: 50 },
        { id: 'gold', value: 20 },
      ],
      focus: 'health, magic, money, gear, loot, quests, factions and companions',
    },
    scifi: {
      sections: ['status', 'stats', 'inventory', 'quests', 'relations'],
      stats: [
        { id: 'health', value: 100, max: 100 },
        { id: 'energy', value: 100, max: 100 },
        { id: 'credits', value: 500 },
      ],
      focus: 'health, energy, credits, cargo and gear, missions, crew and contacts',
    },
    romance: {
      sections: ['status', 'relations', 'quests', 'inventory', 'stats'],
      stats: [
        { id: 'mood', value: 70, max: 100 },
        { id: 'confidence', value: 50, max: 100 },
      ],
      focus: 'feelings, relationship progress, trust, shared plans, promises, keepsakes and gifts',
    },
    slice: {
      sections: ['status', 'stats', 'quests', 'relations', 'inventory'],
      stats: [
        { id: 'money', value: 1000 },
        { id: 'energy', value: 100, max: 100 },
        { id: 'mood', value: 70, max: 100 },
      ],
      focus: 'money, energy, mood, plans and to-dos, people, belongings',
    },
    horror: {
      sections: ['status', 'stats', 'quests', 'inventory', 'relations'],
      stats: [
        { id: 'health', value: 100, max: 100 },
        { id: 'sanity', value: 100, max: 100 },
      ],
      focus: 'health, sanity, supplies, clues and unsolved mysteries, survivors and threats',
    },
    custom: {
      sections: ['status', 'stats', 'inventory', 'quests', 'relations'],
      stats: [],
      focus: '',
    },
  };

  function clone(v) {
    return v == null ? v : JSON.parse(JSON.stringify(v));
  }

  function str(v, max) {
    if (v == null) return '';
    var s = String(v).replace(/\s+/g, ' ').trim();
    return max && s.length > max ? s.slice(0, max) : s;
  }

  function num(v) {
    if (typeof v === 'number' && isFinite(v)) return v;
    if (typeof v === 'string' && v.trim() !== '' && isFinite(Number(v))) return Number(v);
    return null;
  }

  function sameName(a, b) {
    return str(a).toLowerCase() === str(b).toLowerCase();
  }

  function findBy(list, field, name) {
    for (var i = 0; i < list.length; i++) {
      if (sameName(list[i][field], name)) return i;
    }
    return -1;
  }

  // "HP=100/100; Gold=20; Reputation" -> [{name, value, max}]
  function parseCustomStats(text) {
    var out = [];
    String(text || '').split(/[;\n,]+/).forEach(function (part) {
      var m = part.match(/^\s*([^=:]+?)\s*(?:[=:]\s*(-?\d+(?:\.\d+)?)\s*(?:\/\s*(-?\d+(?:\.\d+)?))?)?\s*$/);
      if (!m || !str(m[1])) return;
      var stat = { name: str(m[1], 40), value: m[2] != null ? Number(m[2]) : 0 };
      if (m[3] != null) stat.max = Number(m[3]);
      out.push(stat);
    });
    return out.slice(0, 20);
  }

  function templateIds() {
    return Object.keys(TEMPLATES);
  }

  // t: i18n translate function, cfg: plugin config values.
  function createState(templateId, t, cfg) {
    var tpl = TEMPLATES[templateId] ? templateId : 'fantasy';
    var def = TEMPLATES[tpl];
    var stats;
    if (tpl === 'custom') {
      stats = parseCustomStats(cfg && cfg.customStats);
    } else {
      stats = def.stats.map(function (s) {
        var stat = { name: t('stat.' + tpl + '.' + s.id), value: s.value };
        if (s.max != null) stat.max = s.max;
        return stat;
      });
    }
    return {
      schema: SCHEMA,
      template: tpl,
      sections: def.sections.slice(),
      status: { location: '', time: '', conditions: '' },
      stats: stats,
      inventory: [],
      quests: [],
      relations: [],
      pending: null,
      undo: [],
      processed: {},
      lastUpdateAt: null,
      rev: 0,
      summary: '',
    };
  }

  function normalize(state) {
    if (!state || typeof state !== 'object' || state.schema !== SCHEMA) return null;
    var s = state;
    s.template = TEMPLATES[s.template] ? s.template : 'fantasy';
    s.sections = Array.isArray(s.sections) ? s.sections.filter(function (x) { return SECTIONS.indexOf(x) >= 0; }) : TEMPLATES[s.template].sections.slice();
    s.status = s.status && typeof s.status === 'object' ? s.status : {};
    ['location', 'time', 'conditions'].forEach(function (k) { s.status[k] = str(s.status[k], 300); });
    ['stats', 'inventory', 'quests', 'relations', 'undo'].forEach(function (k) {
      if (!Array.isArray(s[k])) s[k] = [];
    });
    if (!s.processed || typeof s.processed !== 'object') s.processed = {};
    s.rev = num(s.rev) || 0;
    return s;
  }

  // Compact text injected into the model request and exposed as a macro.
  function summarize(state, t) {
    if (!state) return '';
    var lines = [];
    var st = state.status || {};
    if (st.location) lines.push(t('sum.location') + ': ' + st.location);
    if (st.time) lines.push(t('sum.time') + ': ' + st.time);
    if (st.conditions) lines.push(t('sum.conditions') + ': ' + st.conditions);
    if (state.stats.length) {
      lines.push(t('sum.stats') + ': ' + state.stats.map(function (s) {
        return s.name + ' ' + s.value + (s.max != null ? '/' + s.max : '');
      }).join(', '));
    }
    if (state.inventory.length) {
      lines.push(t('sum.inventory') + ': ' + state.inventory.map(function (i) {
        return i.name + (i.qty > 1 ? ' ×' + i.qty : '');
      }).join(', '));
    }
    var active = state.quests.filter(function (q) { return q.status === 'active'; });
    if (active.length) {
      lines.push(t('sum.quests') + ': ' + active.map(function (q) {
        return q.title + (q.note ? ' (' + q.note + ')' : '');
      }).join('; '));
    }
    if (state.relations.length) {
      lines.push(t('sum.relations') + ': ' + state.relations.map(function (r) {
        var bits = [r.attitude, r.value != null ? String(r.value) : ''].filter(Boolean).join(', ');
        return r.name + (bits ? ' (' + bits + ')' : '');
      }).join('; '));
    }
    return lines.join('\n');
  }

  function isEmpty(state) {
    if (!state) return true;
    var st = state.status || {};
    return !st.location && !st.time && !st.conditions && !state.stats.length &&
      !state.inventory.length && !state.quests.length && !state.relations.length;
  }

  function languageRule(cfg, appLocale) {
    if (cfg && cfg.contentLanguage === 'app') {
      return 'Write every new name, title, note and status text in the language with locale code "' +
        (appLocale || 'en') + '".';
    }
    return 'Write every new name, title, note and status text in the same language as the story messages.';
  }

  // Builds the hidden extraction prompt. The prompt stays in English; visible output
  // language is constrained explicitly by languageRule().
  function buildPrompt(state, messages, cfg, appLocale) {
    var tpl = TEMPLATES[state.template] || TEMPLATES.fantasy;
    var focus = state.template === 'custom' ? str(cfg && cfg.customFocus, 500) : tpl.focus;
    var current = {
      status: state.status,
      stats: state.stats,
      inventory: state.inventory,
      quests: state.quests,
      relations: state.relations,
    };
    var transcript = messages.map(function (m) {
      var who = m.role === 'user' ? 'PLAYER' : 'STORY';
      return '[' + who + ']\n' + str(m.content, 6000);
    }).join('\n\n');
    return [
      'You maintain the state journal of an interactive story. Read the CURRENT JOURNAL and the NEW MESSAGES, then report only what changed in the NEW MESSAGES.',
      focus ? 'Track especially: ' + focus + '.' : '',
      'Track: the player character\'s location, in-story time, conditions (injuries, effects, outfit), numeric stats, inventory items, quests/goals, and relationships with other characters.',
      'Rules:',
      '- Only record changes that actually happen in the NEW MESSAGES. Do not invent anything. Intentions and plans are not changes unless they create a goal.',
      '- Reuse the exact existing names of stats, items, quests and characters when they refer to the same thing.',
      '- Stats: give the new absolute value. Only use stat names that already exist, unless a new numeric resource clearly appears.',
      '- Items: add_items for gained items, remove_items for lost, used up or given away items.',
      '- Quests: status is "active", "done" or "failed". Include a quest only if it is new or its status/note changed.',
      '- Relations: "attitude" is a short phrase, "value" is a number from -100 (hostile) to 100 (devoted).',
      '- Keep notes under 15 words.',
      '- ' + languageRule(cfg, appLocale),
      'Reply with JSON only, no markdown, using only the keys that changed:',
      '{"location":"","time":"","conditions":"","stats":{"Name":0},"add_items":[{"name":"","qty":1,"note":""}],"remove_items":[{"name":"","qty":1}],"quests":[{"title":"","status":"active","note":""}],"relations":[{"name":"","attitude":"","value":0,"note":""}]}',
      'If nothing changed, reply {}.',
      '',
      'CURRENT JOURNAL:',
      JSON.stringify(current),
      '',
      'NEW MESSAGES:',
      transcript,
    ].filter(function (x) { return x !== ''; }).join('\n');
  }

  function parseResponse(text) {
    if (typeof text !== 'string') return null;
    var s = text.replace(/```(?:json)?/gi, '').trim();
    var start = s.indexOf('{');
    var end = s.lastIndexOf('}');
    if (start < 0 || end < start) return null;
    try {
      var obj = JSON.parse(s.slice(start, end + 1));
      return obj && typeof obj === 'object' && !Array.isArray(obj) ? obj : null;
    } catch (e) {
      return null;
    }
  }

  function arr(v) {
    return Array.isArray(v) ? v : [];
  }

  // Applies a parsed patch. Returns { state, changes } where changes are
  // { key, params } entries for localized display. Does not mutate the input.
  function applyPatch(state, patch) {
    var next = clone(state);
    var changes = [];
    if (!patch) return { state: next, changes: changes };

    ['location', 'time', 'conditions'].forEach(function (k) {
      if (patch[k] == null) return;
      var v = str(patch[k], 300);
      if (v && v !== next.status[k]) {
        changes.push({ key: 'change.' + k, params: { value: v } });
        next.status[k] = v;
      }
    });

    if (patch.stats && typeof patch.stats === 'object' && !Array.isArray(patch.stats)) {
      Object.keys(patch.stats).slice(0, 30).forEach(function (name) {
        var v = num(patch.stats[name]);
        if (v == null || !str(name)) return;
        var i = findBy(next.stats, 'name', name);
        if (i < 0) {
          next.stats.push({ name: str(name, 40), value: v });
          changes.push({ key: 'change.statNew', params: { name: str(name, 40), value: v } });
          return;
        }
        var stat = next.stats[i];
        if (stat.max != null) v = Math.min(v, stat.max);
        if (v !== stat.value) {
          changes.push({ key: 'change.stat', params: { name: stat.name, from: stat.value, to: v } });
          stat.value = v;
        }
      });
    }

    arr(patch.add_items).slice(0, 30).forEach(function (it) {
      var name = str(it && it.name, 60);
      if (!name) return;
      var qty = Math.max(1, Math.round(num(it.qty) || 1));
      var i = findBy(next.inventory, 'name', name);
      if (i >= 0) {
        next.inventory[i].qty = (next.inventory[i].qty || 1) + qty;
        if (it.note) next.inventory[i].note = str(it.note, 120);
      } else {
        next.inventory.push({ name: name, qty: qty, note: str(it.note, 120) });
      }
      changes.push({ key: 'change.itemAdd', params: { name: name, qty: qty } });
    });

    arr(patch.remove_items).slice(0, 30).forEach(function (it) {
      var name = str(it && it.name, 60);
      var i = findBy(next.inventory, 'name', name);
      if (i < 0) return;
      var item = next.inventory[i];
      var qty = it.qty == null ? item.qty : Math.max(1, Math.round(num(it.qty) || 1));
      item.qty = (item.qty || 1) - qty;
      if (item.qty <= 0) next.inventory.splice(i, 1);
      changes.push({ key: 'change.itemRemove', params: { name: item.name, qty: qty } });
    });

    arr(patch.quests).slice(0, 20).forEach(function (q) {
      var title = str(q && q.title, 100);
      if (!title) return;
      var status = ['active', 'done', 'failed'].indexOf(q.status) >= 0 ? q.status : 'active';
      var i = findBy(next.quests, 'title', title);
      if (i < 0) {
        next.quests.push({ title: title, status: status, note: str(q.note, 160) });
        changes.push({ key: 'change.questNew', params: { title: title } });
        return;
      }
      var quest = next.quests[i];
      if (quest.status !== status) {
        changes.push({ key: 'change.quest.' + status, params: { title: quest.title } });
        quest.status = status;
      }
      if (q.note && str(q.note, 160) !== quest.note) {
        quest.note = str(q.note, 160);
        changes.push({ key: 'change.questNote', params: { title: quest.title, note: quest.note } });
      }
    });

    arr(patch.relations).slice(0, 20).forEach(function (r) {
      var name = str(r && r.name, 60);
      if (!name) return;
      var value = num(r.value);
      if (value != null) value = Math.max(-100, Math.min(100, Math.round(value)));
      var i = findBy(next.relations, 'name', name);
      if (i < 0) {
        next.relations.push({ name: name, attitude: str(r.attitude, 60), value: value, note: str(r.note, 160) });
        changes.push({ key: 'change.relNew', params: { name: name } });
        return;
      }
      var rel = next.relations[i];
      if (value != null && value !== rel.value) {
        changes.push({ key: 'change.relValue', params: { name: rel.name, from: rel.value == null ? '—' : rel.value, to: value } });
        rel.value = value;
      }
      if (r.attitude && str(r.attitude, 60) !== rel.attitude) {
        rel.attitude = str(r.attitude, 60);
        changes.push({ key: 'change.relAttitude', params: { name: rel.name, value: rel.attitude } });
      }
      if (r.note) rel.note = str(r.note, 160);
    });

    return { state: next, changes: changes };
  }

  function stripMeta(state) {
    return {
      status: state.status,
      stats: state.stats,
      inventory: state.inventory,
      quests: state.quests,
      relations: state.relations,
    };
  }

  // Saves the current contents before an update so it can be undone or reverted
  // when the source message is regenerated or deleted.
  function pushUndo(state, messageId) {
    state.undo.push({ messageId: messageId == null ? null : messageId, data: clone(stripMeta(state)) });
    if (state.undo.length > MAX_UNDO) state.undo.splice(0, state.undo.length - MAX_UNDO);
  }

  function restore(state, entry) {
    var d = entry.data;
    state.status = d.status;
    state.stats = d.stats;
    state.inventory = d.inventory;
    state.quests = d.quests;
    state.relations = d.relations;
  }

  function undoLast(state) {
    var entry = state.undo.pop();
    if (!entry) return false;
    restore(state, entry);
    if (entry.messageId != null) delete state.processed[String(entry.messageId)];
    state.pending = null;
    return true;
  }

  // Reverts every update made from messageId onward. Returns true if reverted.
  function revertMessage(state, messageId) {
    var idx = -1;
    for (var i = 0; i < state.undo.length; i++) {
      if (String(state.undo[i].messageId) === String(messageId)) { idx = i; break; }
    }
    if (idx < 0) {
      if (state.pending && String(state.pending.messageId) === String(messageId)) {
        state.pending = null;
        return true;
      }
      return false;
    }
    restore(state, state.undo[idx]);
    state.undo.slice(idx).forEach(function (u) {
      if (u.messageId != null) delete state.processed[String(u.messageId)];
    });
    state.undo = state.undo.slice(0, idx);
    state.pending = null;
    return true;
  }

  // Short content fingerprint, used to tell a regenerated message from a
  // metadata-only update of the same message id.
  function hash(text) {
    var h = 5381;
    var s = String(text || '');
    for (var i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0;
    return (h >>> 0).toString(36) + '.' + s.length.toString(36);
  }

  function trimProcessed(state) {
    var keys = Object.keys(state.processed);
    if (keys.length <= 200) return;
    keys.sort(function (a, b) { return Number(a) - Number(b); });
    keys.slice(0, keys.length - 200).forEach(function (k) { delete state.processed[k]; });
  }

  function markProcessed(state, messageId, contentHash) {
    if (messageId == null) return;
    state.processed[String(messageId)] = contentHash || '1';
    trimProcessed(state);
  }

  // Commits a computed result into the stored state.
  function commit(state, result, messageId, t, contentHash) {
    pushUndo(state, messageId);
    restore(state, { data: stripMeta(result.state) });
    markProcessed(state, messageId, contentHash);
    state.pending = null;
    state.lastUpdateAt = new Date().toISOString();
    state.summary = summarize(state, t);
    return state;
  }

  // Switches the genre template. keep=true keeps all entries and only changes
  // the layout and labels; otherwise starts a fresh journal. Both are undoable.
  function switchTemplate(state, templateId, keep, t, cfg) {
    var next = createState(templateId, t, cfg);
    if (keep) {
      pushUndo(state, null);
      state.template = next.template;
      state.sections = next.sections;
      if (!state.stats.length) state.stats = next.stats;
      state.summary = summarize(state, t);
      return state;
    }
    next.rev = state.rev;
    next.undo = state.undo.slice();
    next.processed = state.processed;
    if (!isEmpty(state)) {
      next.undo.push({ messageId: null, data: clone(stripMeta(state)) });
      if (next.undo.length > MAX_UNDO) next.undo.splice(0, next.undo.length - MAX_UNDO);
    }
    next.summary = summarize(next, t);
    return next;
  }

  function formatChange(c, t) {
    return t(c.key, c.params || {});
  }

  return {
    VAR: VAR,
    UI_VAR: UI_VAR,
    SECTIONS: SECTIONS,
    TEMPLATES: TEMPLATES,
    templateIds: templateIds,
    clone: clone,
    str: str,
    num: num,
    parseCustomStats: parseCustomStats,
    createState: createState,
    normalize: normalize,
    summarize: summarize,
    isEmpty: isEmpty,
    buildPrompt: buildPrompt,
    parseResponse: parseResponse,
    applyPatch: applyPatch,
    stripMeta: stripMeta,
    pushUndo: pushUndo,
    undoLast: undoLast,
    revertMessage: revertMessage,
    commit: commit,
    hash: hash,
    markProcessed: markProcessed,
    formatChange: formatChange,
    switchTemplate: switchTemplate,
  };
})();
