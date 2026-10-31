// Adventure Journal entry script: hooks, actions and model-driven updates.

var i18n = tavo.plugin.i18n;

function t(key, params) {
  return i18n.t(key, params);
}

function cfg(key) {
  return tavo.plugin.config.get(key);
}

function cfgAll() {
  return tavo.plugin.config.all();
}

function toast(text) {
  try {
    tavo.utils.toast(text);
  } catch (e) {
    // Toasts are best-effort.
  }
}

function isRetryable(e) {
  return e && e.code === 'conflict' && e.details && e.details.reason === 'chat_runtime_not_ready';
}

// All state writes go through one queue so hooks never interleave.
var queue = Promise.resolve();

function serial(fn) {
  var run = queue.then(fn);
  queue = run.catch(function (e) {
    if (!isRetryable(e)) console.error('[adventure-journal]', e);
  });
  return run;
}

async function load() {
  return AJ.normalize(await tavo.variable.get(AJ.VAR));
}

async function save(state) {
  state.rev = (state.rev || 0) + 1;
  state.summary = AJ.summarize(state, t);
  await tavo.variable.set(AJ.VAR, state);
}

async function loadOrCreate() {
  var state = await load();
  if (state) return state;
  state = AJ.createState(cfg('defaultTemplate') || 'fantasy', t, cfgAll());
  await save(state);
  return state;
}

function isStoryMessage(message) {
  return message && message.role !== 'user' && message.role !== 'system' && !message.hidden;
}

// Recent visible messages ending at (and including) the target message.
async function recentMessages(targetId, pairs) {
  var count = await tavo.message.count();
  var take = Math.max(2, pairs * 2 + 1);
  var list = await tavo.message.find([Math.max(0, count - take - 4)], { hidden: false });
  list = list.filter(function (m) { return m.role === 'user' || m.role === 'assistant'; });
  if (targetId != null) {
    var idx = -1;
    for (var i = 0; i < list.length; i++) {
      if (String(list[i].id) === String(targetId)) idx = i;
    }
    if (idx >= 0) list = list.slice(0, idx + 1);
  }
  return list.slice(-take);
}

function timeoutMs() {
  var sec = Number(cfg('timeoutSec')) || 45;
  return Math.max(10, Math.min(180, sec)) * 1000;
}

async function askModel(state, messages) {
  var prompt = AJ.buildPrompt(state, messages, cfgAll(), i18n.locale);
  var options = {
    context: false,
    timeout: timeoutMs(),
    settings: {
      temperature: 0.2,
      maxCompletionTokens: Number(cfg('maxTokens')) || 700,
    },
  };
  var text = await tavo.generate(prompt, options);
  var patch = AJ.parseResponse(text);
  if (!patch) {
    var err = new Error('bad_response');
    err.code = 'bad_response';
    throw err;
  }
  return patch;
}

function changesPreview(changes) {
  var shown = changes.slice(0, 3).map(function (c) { return AJ.formatChange(c, t); });
  if (changes.length > 3) shown.push(t('runtime.moreChanges', { count: changes.length - 3 }));
  return shown.join(' · ');
}

// Runs one model update for the target message.
// opts.manual: started by the user; reports "nothing changed" and errors loudly.
async function runUpdate(target, opts) {
  opts = opts || {};
  var mode = cfg('updateMode') || 'auto';
  var state = await loadOrCreate();
  var every = opts.manual ? 1 : Math.max(1, Number(cfg('updateEvery')) || 1);
  var messages = await recentMessages(target ? target.id : null, every);
  if (!messages.length) {
    if (opts.manual) toast(t('runtime.noMessages'));
    return;
  }
  var source = target || messages[messages.length - 1];
  var contentHash = AJ.hash(source.content);

  if (opts.manual) toast(t('runtime.updating'));
  var patch;
  try {
    patch = await askModel(state, messages);
  } catch (e) {
    if (isRetryable(e)) throw e;
    toast(e && e.code === 'bad_response' ? t('runtime.badResponse') : t('runtime.updateFailed', { error: (e && e.message) || String(e) }));
    return;
  }

  // Reload: the user may have edited the journal while the model was working.
  state = await loadOrCreate();
  var result = AJ.applyPatch(state, patch);
  if (!result.changes.length) {
    AJ.markProcessed(state, source.id, contentHash);
    state.sinceUpdate = 0;
    await save(state);
    if (opts.manual) toast(t('runtime.noChanges'));
    return;
  }

  state.sinceUpdate = 0;
  if (mode === 'confirm') {
    state.pending = {
      messageId: source.id,
      hash: contentHash,
      changes: result.changes,
      data: AJ.stripMeta(result.state),
      at: new Date().toISOString(),
    };
    AJ.markProcessed(state, source.id, contentHash);
    await save(state);
    toast(t('runtime.pending', { count: result.changes.length }));
    return;
  }

  AJ.commit(state, result, source.id, t, contentHash);
  await save(state);
  if (cfg('notify') !== false) toast('📜 ' + changesPreview(result.changes));
}

// ---- Hooks ----------------------------------------------------------------

tavo.plugin.on('chat:opened', function () {
  return serial(loadOrCreate);
});

tavo.plugin.on('message:added', function (event) {
  var message = event.message;
  if (!isStoryMessage(message)) return;
  var mode = cfg('updateMode') || 'auto';
  if (mode === 'manual') return;
  return serial(async function () {
    var state = await loadOrCreate();
    if (state.processed[String(message.id)]) return;
    var every = Math.max(1, Number(cfg('updateEvery')) || 1);
    state.sinceUpdate = (state.sinceUpdate || 0) + 1;
    if (state.sinceUpdate < every) {
      await save(state);
      return;
    }
    await save(state);
    await runUpdate(message, {});
  });
});

// A regenerated or edited reply: undo what it changed and read it again.
tavo.plugin.on('message:updated', function (event) {
  var message = event.message;
  if (!message || message.id == null) return;
  return serial(async function () {
    var state = await load();
    if (!state) return;
    var seen = state.processed[String(message.id)];
    if (!seen || seen === AJ.hash(message.content)) return;
    if (!AJ.revertMessage(state, message.id)) delete state.processed[String(message.id)];
    await save(state);
    var mode = cfg('updateMode') || 'auto';
    if (mode !== 'manual' && isStoryMessage(message)) await runUpdate(message, {});
  });
});

tavo.plugin.on('message:deleted', function (event) {
  var message = event.message;
  if (!message || message.id == null) return;
  return serial(async function () {
    var state = await load();
    if (!state) return;
    if (AJ.revertMessage(state, message.id)) {
      await save(state);
      toast(t('runtime.reverted'));
    }
  });
});

tavo.plugin.on('generation:prepare', async function (event) {
  if (cfg('injectState') === false) return;
  var state;
  try {
    state = await load();
  } catch (e) {
    return;
  }
  if (!state || AJ.isEmpty(state)) return;
  var summary = AJ.summarize(state, t);
  event.text = [
    '<adventure_journal>',
    '[Current story state from the player\'s journal. Keep the story consistent with it. Do not mention the journal.]',
    summary,
    '</adventure_journal>',
    '',
    event.text,
  ].join('\n');
});

// ---- Actions ----------------------------------------------------------------

function rollDie(sides) {
  return 1 + Math.floor(Math.random() * sides);
}

var DICE = {
  d20: { count: 1, sides: 20 },
  d100: { count: 1, sides: 100 },
  '2d6': { count: 2, sides: 6 },
  d6: { count: 1, sides: 6 },
};

tavo.plugin.onInputAction('roll-dice', async function () {
  var state = await load();
  var options = Object.keys(DICE).map(function (k) { return { value: k, label: '🎲 ' + k }; });
  var die = await tavo.utils.select(options, t('runtime.dice.title'), 'd20');
  if (!die || !DICE[die]) return;
  var stat = null;
  if (state && state.stats.length) {
    var statOptions = [{ value: 'none', label: t('runtime.dice.noStat') }].concat(state.stats.map(function (s, i) {
      return { value: String(i), label: s.name, meta: String(s.value) };
    }));
    var pick = await tavo.utils.select(statOptions, t('runtime.dice.statTitle'), 'none');
    if (pick === null) return;
    if (pick !== 'none') stat = state.stats[Number(pick)] || null;
  }
  var spec = DICE[die];
  var rolls = [];
  for (var i = 0; i < spec.count; i++) rolls.push(rollDie(spec.sides));
  var total = rolls.reduce(function (a, b) { return a + b; }, 0);
  var text = stat
    ? t('runtime.dice.resultStat', { die: die, rolls: rolls.join('+'), total: total, stat: stat.name, value: stat.value })
    : t('runtime.dice.result', { die: die, rolls: rolls.join('+'), total: total });
  var current = await tavo.input.get();
  await tavo.input.append((current && !/\s$/.test(current) ? ' ' : '') + text);
});

tavo.plugin.onSidebarAction('open-journal', async function () {
  var ui = (await tavo.variable.get(AJ.UI_VAR, 'global')) || {};
  ui.openRequest = Date.now();
  await tavo.variable.set(AJ.UI_VAR, ui, 'global');
});

tavo.plugin.onSidebarAction('update-now', function () {
  return serial(function () { return runUpdate(null, { manual: true }); });
});

tavo.plugin.onLastMessageAction('update-from-message', async function (ctx) {
  var message = await tavo.message.get(ctx.messageId);
  if (!message) return;
  await serial(async function () {
    var state = await loadOrCreate();
    if (state.processed[String(message.id)]) {
      AJ.revertMessage(state, message.id);
      delete state.processed[String(message.id)];
      await save(state);
    }
    await runUpdate(message, { manual: true });
  });
});

tavo.plugin.onSidebarAction('choose-template', function () {
  return serial(async function () {
    var state = await loadOrCreate();
    var options = AJ.templateIds().map(function (id) {
      return { value: id, label: t('template.' + id), description: t('template.' + id + '.desc') };
    });
    var pick = await tavo.utils.select(options, t('runtime.template.title'), state.template);
    if (!pick || !AJ.TEMPLATES[pick]) return;
    var keep = false;
    if (!AJ.isEmpty(state)) {
      var answer = await tavo.utils.ask({
        question: t('runtime.template.keepQuestion'),
        options: [
          { value: 'keep', label: t('runtime.template.keep') },
          { value: 'fresh', label: t('runtime.template.fresh') },
        ],
        allowOther: false,
      });
      if (!answer || answer.status !== 'answered') return;
      keep = answer.answer === 'keep';
    }
    var next = AJ.switchTemplate(state, pick, keep, t, cfgAll());
    await save(next);
    toast(t('runtime.template.done', { name: t('template.' + pick) }));
  });
});

tavo.plugin.onSidebarAction('undo-update', function () {
  return serial(async function () {
    var state = await load();
    if (!state || !AJ.undoLast(state)) {
      toast(t('runtime.nothingToUndo'));
      return;
    }
    await save(state);
    toast(t('runtime.undone'));
  });
});

tavo.plugin.onSidebarAction('export-journal', async function () {
  var state = await load();
  if (!state) {
    toast(t('runtime.empty'));
    return;
  }
  var data = AJ.stripMeta(state);
  data.format = 'adventure-journal';
  data.version = 1;
  data.template = state.template;
  data.sections = state.sections;
  await tavo.file.export('adventure-journal.json', JSON.stringify(data, null, 2));
});

tavo.plugin.onSidebarAction('import-journal', function () {
  return serial(async function () {
    var files = await tavo.file.import({ extensions: ['json'] });
    var file = files && files[0];
    if (!file) return;
    var data;
    try {
      data = JSON.parse(await tavo.file.load(file.path));
    } catch (e) {
      data = null;
    }
    if (!data || data.format !== 'adventure-journal') {
      toast(t('runtime.importInvalid'));
      return;
    }
    var state = await loadOrCreate();
    AJ.pushUndo(state, null);
    var imported = AJ.normalize({
      schema: 1,
      template: data.template,
      sections: data.sections,
      status: data.status,
      stats: data.stats,
      inventory: data.inventory,
      quests: data.quests,
      relations: data.relations,
    });
    state.template = imported.template;
    state.sections = imported.sections;
    state.status = imported.status;
    state.stats = imported.stats;
    state.inventory = imported.inventory;
    state.quests = imported.quests;
    state.relations = imported.relations;
    state.pending = null;
    await save(state);
    toast(t('runtime.imported'));
  });
});

tavo.plugin.onSidebarAction('reset-journal', function () {
  return serial(async function () {
    var answer = await tavo.utils.ask({
      question: t('runtime.reset.question'),
      options: [
        { value: 'yes', label: t('runtime.reset.yes') },
        { value: 'no', label: t('runtime.reset.no') },
      ],
      allowOther: false,
    });
    if (!answer || answer.answer !== 'yes') return;
    var old = await load();
    var state = old
      ? AJ.switchTemplate(old, old.template, false, t, cfgAll())
      : AJ.createState(cfg('defaultTemplate') || 'fantasy', t, cfgAll());
    await save(state);
    toast(t('runtime.reset.done'));
  });
});

tavo.plugin.onSidebarAction('reset-button', async function () {
  var ui = (await tavo.variable.get(AJ.UI_VAR, 'global')) || {};
  ui.pos = null;
  ui.resetAt = Date.now();
  await tavo.variable.set(AJ.UI_VAR, ui, 'global');
  toast(t('runtime.buttonReset'));
});
