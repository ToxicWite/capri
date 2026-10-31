"""Source of truth for the plugin's locale catalogs.

Each key maps to (en, ru, zh-CN). build.py writes locales/<tag>.json from this
table, so every catalog always has the same keys.
"""

DESCRIPTION_EN = """**Adventure Journal** keeps the state of your roleplay in one place and makes sure the AI remembers it.

### What it tracks
- 📍 **Status**: location, in-story time, conditions (injuries, effects, outfit)
- 📊 **Stats**: HP, mana, money, sanity… or your own
- 🎒 **Inventory**: items gained, used up and lost
- 🗺️ **Quests & goals**: active, completed, failed
- 💞 **Relationships**: attitude and a −100…+100 scale for every character

### How it works
1. After each AI reply the plugin asks the model what changed and updates the journal.
2. Before every reply the current state is quietly added to the request, so the story stays consistent.
3. Open the 📜 button to view and edit everything by hand.

### You choose
- **Genre template**: Fantasy, Sci-fi, Romance, Slice of life, Horror & mystery, or Custom with your own stats. Can be changed per chat.
- **Update mode**: automatic, with confirmation, or only on request.
- How often to update, whether to inject the state, the language of journal entries, timeout and token limit.

Rerolled or deleted replies roll their changes back automatically. Includes a 🎲 dice roller in the + menu, undo, and export/import of the journal.

Uses your chat's model API: each update is one extra short request."""

DESCRIPTION_RU = """**Журнал приключений** хранит состояние ролевой игры в одном месте и следит, чтобы ИИ его помнил.

### Что отслеживается
- 📍 **Статус**: место, время в истории, состояние (раны, эффекты, одежда)
- 📊 **Характеристики**: здоровье, мана, деньги, рассудок… или свои
- 🎒 **Инвентарь**: что получено, потрачено и потеряно
- 🗺️ **Квесты и цели**: активные, выполненные, проваленные
- 💞 **Отношения**: отношение и шкала от −100 до +100 для каждого персонажа

### Как это работает
1. После каждого ответа ИИ плагин спрашивает модель, что изменилось, и обновляет журнал.
2. Перед каждым ответом текущее состояние незаметно добавляется в запрос — история остаётся последовательной.
3. Кнопка 📜 открывает журнал: всё можно посмотреть и поправить вручную.

### Выбираете вы
- **Шаблон жанра**: фэнтези, научная фантастика, романтика, повседневность, хоррор и детектив или свой — со своими характеристиками. Можно менять для каждого чата.
- **Режим обновления**: автоматически, с подтверждением или только по запросу.
- Как часто обновлять, добавлять ли состояние в запрос, язык записей, тайм-аут и лимит токенов.

Если ответ перегенерирован или удалён, его изменения откатываются сами. Есть 🎲 броски кубиков в меню «+», отмена и экспорт/импорт журнала.

Использует API модели вашего чата: каждое обновление — один дополнительный короткий запрос."""

DESCRIPTION_ZH = """**冒险日志** 把角色扮演中的状态集中记录下来，并确保 AI 记得它们。

### 记录内容
- 📍 **状态**：地点、故事内时间、身体状况（伤势、效果、穿着）
- 📊 **属性**：生命、法力、金钱、理智……或自定义属性
- 🎒 **物品栏**：获得、消耗和丢失的物品
- 🗺️ **任务与目标**：进行中、已完成、已失败
- 💞 **人物关系**：每个角色的态度和 −100 到 +100 的好感度

### 工作方式
1. 每次 AI 回复后，插件询问模型发生了哪些变化并更新日志。
2. 每次回复前，当前状态会悄悄加入请求，让故事保持连贯。
3. 点击 📜 按钮即可查看并手动编辑所有内容。

### 由你选择
- **题材模板**：奇幻、科幻、恋爱、日常、恐怖与悬疑，或使用自定义属性。每个聊天可单独设置。
- **更新方式**：自动、需确认、或仅手动。
- 更新频率、是否注入状态、日志内容语言、超时和 token 上限。

重新生成或删除的回复会自动撤销其改动。还包括「+」菜单中的 🎲 掷骰、撤销以及日志导出/导入。

使用当前聊天的模型 API：每次更新会额外发送一个简短请求。"""

L = {
    "plugin.name": ("Adventure Journal", "Журнал приключений", "冒险日志"),
    "plugin.description": (DESCRIPTION_EN, DESCRIPTION_RU, DESCRIPTION_ZH),
    "releaseNotes.1_0_0": (
        "## First release\n\n- Journal panel with status, stats, inventory, quests and relationships\n- Six genre templates plus custom stats\n- Automatic, confirmed or manual updates\n- Dice roller, undo, export and import",
        "## Первый выпуск\n\n- Панель журнала: статус, характеристики, инвентарь, квесты и отношения\n- Шесть шаблонов жанров и свои характеристики\n- Обновление автоматически, с подтверждением или вручную\n- Броски кубиков, отмена, экспорт и импорт",
        "## 首个版本\n\n- 日志面板：状态、属性、物品栏、任务和人物关系\n- 六种题材模板及自定义属性\n- 自动、确认或手动更新\n- 掷骰、撤销、导出和导入",
    ),

    # Actions
    "actions.rollDice": ("Roll dice", "Бросить кубик", "掷骰子"),
    "actions.openJournal": ("Open journal", "Открыть журнал", "打开日志"),
    "actions.updateNow": ("Update journal now", "Обновить журнал сейчас", "立即更新日志"),
    "actions.updateFromMessage": ("Update journal", "Обновить журнал", "更新日志"),
    "actions.chooseTemplate": ("Choose genre template", "Выбрать шаблон жанра", "选择题材模板"),
    "actions.undo": ("Undo last journal change", "Отменить последнее изменение", "撤销上次日志改动"),
    "actions.export": ("Export journal", "Экспорт журнала", "导出日志"),
    "actions.import": ("Import journal", "Импорт журнала", "导入日志"),
    "actions.reset": ("Clear journal", "Очистить журнал", "清空日志"),
    "actions.resetButton": ("Reset 📜 button position", "Сбросить позицию кнопки 📜", "重置 📜 按钮位置"),

    # Settings
    "settings.info": (
        "The journal is kept per chat. Change the genre for one chat with the template chip in the journal panel or from the chat sidebar.",
        "Журнал хранится отдельно для каждого чата. Жанр конкретного чата можно сменить кнопкой шаблона в панели журнала или в боковом меню чата.",
        "日志按聊天分别保存。可在日志面板的模板按钮或聊天侧边栏中为单个聊天更换题材。",
    ),
    "settings.defaultTemplate": ("Default genre template for new chats", "Шаблон жанра по умолчанию для новых чатов", "新聊天的默认题材模板"),
    "settings.customStats": ("Custom template: stats", "Свой шаблон: характеристики", "自定义模板：属性"),
    "settings.customStats.desc": (
        "Used by the Custom template. Separate stats with semicolons. Format: Name=value or Name=value/max.",
        "Для шаблона «Свой». Разделяйте характеристики точкой с запятой. Формат: Название=значение или Название=значение/максимум.",
        "用于「自定义」模板。用分号分隔属性。格式：名称=数值 或 名称=数值/上限。",
    ),
    "settings.customStats.default": ("Health=100/100; Stamina=100/100; Coins=10", "Здоровье=100/100; Выносливость=100/100; Монеты=10", "生命=100/100; 体力=100/100; 金币=10"),
    "settings.customFocus": ("Custom template: what to track", "Свой шаблон: что отслеживать", "自定义模板：重点记录"),
    "settings.customFocus.desc": (
        "Optional hint for the AI, for example: reputation with factions, ship damage, spells learned.",
        "Необязательная подсказка для ИИ, например: репутация у фракций, повреждения корабля, выученные заклинания.",
        "可选，给 AI 的提示，例如：阵营声望、飞船损伤、已学法术。",
    ),
    "settings.updateMode": ("Update mode", "Режим обновления", "更新方式"),
    "settings.updateMode.desc": (
        "Automatic applies changes right away (you can undo). With confirmation shows proposed changes in the panel first. Manual updates only from the sidebar or the message button.",
        "«Автоматически» применяет изменения сразу (можно отменить). «С подтверждением» сначала показывает предложенные изменения в панели. «Вручную» — только из бокового меню или кнопкой под сообщением.",
        "「自动」立即应用改动（可撤销）。「需确认」先在面板中显示建议的改动。「手动」仅通过侧边栏或消息按钮更新。",
    ),
    "settings.updateMode.auto": ("Automatic", "Автоматически", "自动"),
    "settings.updateMode.confirm": ("With confirmation", "С подтверждением", "需确认"),
    "settings.updateMode.manual": ("Manual only", "Только вручную", "仅手动"),
    "settings.updateEvery": ("Update after every N AI replies", "Обновлять после каждых N ответов ИИ", "每 N 条 AI 回复更新一次"),
    "settings.updateEvery.desc": (
        "Higher values save tokens; the update then reads all replies since the last one.",
        "Чем больше значение, тем меньше расход токенов: обновление прочитает все ответы с прошлого раза.",
        "数值越大越省 token；更新时会读取自上次以来的所有回复。",
    ),
    "settings.injectState": ("Add the journal to AI requests", "Добавлять журнал в запросы к ИИ", "在 AI 请求中加入日志"),
    "settings.injectState.desc": (
        "Quietly adds a short summary of the journal to your next message for the model only. Turn off if you prefer the {{getvar::adventureJournal.summary}} macro in your preset.",
        "Незаметно добавляет краткую сводку журнала к вашему сообщению только для модели. Выключите, если хотите использовать макрос {{getvar::adventureJournal.summary}} в пресете.",
        "仅向模型悄悄附加日志摘要。若想在预设中使用 {{getvar::adventureJournal.summary}} 宏，可关闭此项。",
    ),
    "settings.contentLanguage": ("Language of journal entries", "Язык записей журнала", "日志内容语言"),
    "settings.contentLanguage.conversation": ("Same as the story", "Как в истории", "与故事相同"),
    "settings.contentLanguage.app": ("App language", "Язык приложения", "应用语言"),
    "settings.notify": ("Show a notice after each update", "Показывать уведомление после обновления", "每次更新后显示提示"),
    "settings.showButton": ("Show the 📜 button in chat", "Показывать кнопку 📜 в чате", "在聊天中显示 📜 按钮"),
    "settings.timeoutSec": ("Update timeout, seconds", "Тайм-аут обновления, секунд", "更新超时（秒）"),
    "settings.maxTokens": ("Max tokens per update", "Максимум токенов на обновление", "每次更新的最大 token 数"),

    # Templates
    "template.fantasy": ("Fantasy", "Фэнтези", "奇幻"),
    "template.fantasy.desc": ("HP, mana, gold, loot, quests, companions", "Здоровье, мана, золото, добыча, квесты, спутники", "生命、法力、金币、战利品、任务、同伴"),
    "template.scifi": ("Sci-fi", "Научная фантастика", "科幻"),
    "template.scifi.desc": ("Health, energy, credits, cargo, missions, crew", "Здоровье, энергия, кредиты, груз, миссии, экипаж", "生命、能量、信用点、货物、任务、船员"),
    "template.romance": ("Romance", "Романтика", "恋爱"),
    "template.romance.desc": ("Feelings and relationships first, plans, keepsakes", "В центре чувства и отношения, планы, памятные вещи", "以感情和关系为主，计划、纪念品"),
    "template.slice": ("Slice of life", "Повседневность", "日常"),
    "template.slice.desc": ("Money, energy, mood, to-dos, people", "Деньги, силы, настроение, дела, люди", "金钱、精力、心情、待办、人物"),
    "template.horror": ("Horror & mystery", "Хоррор и детектив", "恐怖与悬疑"),
    "template.horror.desc": ("Health, sanity, supplies, clues, survivors", "Здоровье, рассудок, припасы, улики, выжившие", "生命、理智、补给、线索、幸存者"),
    "template.custom": ("Custom", "Свой", "自定义"),
    "template.custom.desc": ("Your own stats from the plugin settings", "Свои характеристики из настроек плагина", "使用插件设置中的自定义属性"),

    # Starting stats
    "stat.fantasy.hp": ("HP", "Здоровье", "生命"),
    "stat.fantasy.mana": ("Mana", "Мана", "法力"),
    "stat.fantasy.gold": ("Gold", "Золото", "金币"),
    "stat.scifi.health": ("Health", "Здоровье", "生命"),
    "stat.scifi.energy": ("Energy", "Энергия", "能量"),
    "stat.scifi.credits": ("Credits", "Кредиты", "信用点"),
    "stat.romance.mood": ("Mood", "Настроение", "心情"),
    "stat.romance.confidence": ("Confidence", "Уверенность", "自信"),
    "stat.slice.money": ("Money", "Деньги", "金钱"),
    "stat.slice.energy": ("Energy", "Силы", "精力"),
    "stat.slice.mood": ("Mood", "Настроение", "心情"),
    "stat.horror.health": ("Health", "Здоровье", "生命"),
    "stat.horror.sanity": ("Sanity", "Рассудок", "理智"),

    # Section labels: defaults plus genre-specific overrides
    "sec.default.status": ("Status", "Статус", "状态"),
    "sec.default.stats": ("Stats", "Характеристики", "属性"),
    "sec.default.inventory": ("Inventory", "Инвентарь", "物品栏"),
    "sec.default.quests": ("Quests", "Квесты", "任务"),
    "sec.default.relations": ("Relationships", "Отношения", "关系"),
    "sec.scifi.inventory": ("Cargo & gear", "Груз и снаряжение", "货物与装备"),
    "sec.scifi.quests": ("Missions", "Миссии", "任务"),
    "sec.scifi.relations": ("Crew & contacts", "Экипаж и контакты", "船员与联系人"),
    "sec.romance.relations": ("Hearts", "Сердца", "心意"),
    "sec.romance.quests": ("Plans & promises", "Планы и обещания", "计划与承诺"),
    "sec.romance.inventory": ("Keepsakes", "Памятные вещи", "纪念品"),
    "sec.romance.stats": ("Feelings", "Чувства", "感受"),
    "sec.slice.quests": ("To-do & plans", "Дела и планы", "待办与计划"),
    "sec.slice.relations": ("People", "Люди", "人物"),
    "sec.slice.inventory": ("Belongings", "Вещи", "随身物品"),
    "sec.horror.quests": ("Clues & mysteries", "Улики и загадки", "线索与谜团"),
    "sec.horror.inventory": ("Supplies", "Припасы", "补给"),
    "sec.horror.relations": ("Survivors & threats", "Выжившие и угрозы", "幸存者与威胁"),

    # Summary labels (also used as status field labels)
    "sum.location": ("Location", "Место", "地点"),
    "sum.time": ("Time", "Время", "时间"),
    "sum.conditions": ("Conditions", "Состояние", "状况"),
    "sum.stats": ("Stats", "Характеристики", "属性"),
    "sum.inventory": ("Inventory", "Инвентарь", "物品"),
    "sum.quests": ("Active goals", "Активные цели", "进行中的目标"),
    "sum.relations": ("Relationships", "Отношения", "关系"),

    # Change descriptions
    "change.location": ("📍 {value}", "📍 {value}", "📍 {value}"),
    "change.time": ("🕰️ {value}", "🕰️ {value}", "🕰️ {value}"),
    "change.conditions": ("🩹 {value}", "🩹 {value}", "🩹 {value}"),
    "change.stat": ("{name}: {from} → {to}", "{name}: {from} → {to}", "{name}：{from} → {to}"),
    "change.statNew": ("New stat {name}: {value}", "Новая характеристика {name}: {value}", "新属性 {name}：{value}"),
    "change.itemAdd": ("+ {name} ×{qty}", "+ {name} ×{qty}", "+ {name} ×{qty}"),
    "change.itemRemove": ("− {name} ×{qty}", "− {name} ×{qty}", "− {name} ×{qty}"),
    "change.questNew": ("New quest: {title}", "Новый квест: {title}", "新任务：{title}"),
    "change.quest.active": ("Quest resumed: {title}", "Квест снова активен: {title}", "任务继续：{title}"),
    "change.quest.done": ("Quest completed: {title}", "Квест выполнен: {title}", "任务完成：{title}"),
    "change.quest.failed": ("Quest failed: {title}", "Квест провален: {title}", "任务失败：{title}"),
    "change.questNote": ("{title}: {note}", "{title}: {note}", "{title}：{note}"),
    "change.relNew": ("New acquaintance: {name}", "Новое знакомство: {name}", "新认识：{name}"),
    "change.relValue": ("{name}: {from} → {to}", "{name}: {from} → {to}", "{name}：{from} → {to}"),
    "change.relAttitude": ("{name} is now {value}", "{name}: теперь {value}", "{name} 现在{value}"),

    # Runtime messages
    "runtime.updating": ("📜 Updating the journal…", "📜 Обновляю журнал…", "📜 正在更新日志…"),
    "runtime.noChanges": ("📜 Nothing new for the journal", "📜 В журнале ничего не изменилось", "📜 日志没有新变化"),
    "runtime.noMessages": ("There are no messages to read yet", "Пока нет сообщений для чтения", "暂无可读取的消息"),
    "runtime.badResponse": ("📜 The model returned an unreadable answer. Try again or raise the token limit.", "📜 Модель вернула нечитаемый ответ. Попробуйте ещё раз или увеличьте лимит токенов.", "📜 模型返回了无法解析的内容。请重试或提高 token 上限。"),
    "runtime.updateFailed": ("📜 Journal update failed: {error}", "📜 Не удалось обновить журнал: {error}", "📜 日志更新失败：{error}"),
    "runtime.pending": ("📜 {count} proposed changes are waiting in the journal", "📜 В журнале ждут подтверждения изменения: {count}", "📜 日志中有 {count} 项待确认的改动"),
    "runtime.moreChanges": ("+{count} more", "и ещё {count}", "另有 {count} 项"),
    "runtime.reverted": ("📜 Changes from the deleted message were rolled back", "📜 Изменения из удалённого сообщения отменены", "📜 已撤销被删除消息带来的改动"),
    "runtime.nothingToUndo": ("Nothing to undo", "Нечего отменять", "没有可撤销的内容"),
    "runtime.undone": ("📜 Last journal change undone", "📜 Последнее изменение журнала отменено", "📜 已撤销上次日志改动"),
    "runtime.empty": ("The journal is empty", "Журнал пуст", "日志为空"),
    "runtime.imported": ("📜 Journal imported", "📜 Журнал импортирован", "📜 日志已导入"),
    "runtime.importInvalid": ("This file is not an Adventure Journal export", "Этот файл не является экспортом Журнала приключений", "该文件不是冒险日志的导出文件"),
    "runtime.buttonReset": ("The 📜 button is back in its default place", "Кнопка 📜 возвращена на место", "📜 按钮已回到默认位置"),
    "runtime.template.title": ("Genre template", "Шаблон жанра", "题材模板"),
    "runtime.template.keepQuestion": ("Keep the current journal entries?", "Сохранить текущие записи журнала?", "保留当前日志内容吗？"),
    "runtime.template.keep": ("Keep entries, change layout", "Сохранить записи, сменить вид", "保留内容，只换布局"),
    "runtime.template.fresh": ("Start a fresh journal", "Начать журнал заново", "重新开始日志"),
    "runtime.template.done": ("📜 Template: {name}", "📜 Шаблон: {name}", "📜 模板：{name}"),
    "runtime.reset.question": ("Clear the journal for this chat? You can undo this.", "Очистить журнал этого чата? Это можно отменить.", "清空此聊天的日志吗？此操作可撤销。"),
    "runtime.reset.yes": ("Clear", "Очистить", "清空"),
    "runtime.reset.no": ("Cancel", "Отмена", "取消"),
    "runtime.reset.done": ("📜 Journal cleared", "📜 Журнал очищен", "📜 日志已清空"),
    "runtime.dice.title": ("Which dice?", "Какой кубик?", "掷哪种骰子？"),
    "runtime.dice.statTitle": ("Check against a stat?", "Проверка по характеристике?", "按属性检定？"),
    "runtime.dice.noStat": ("No stat, just roll", "Без характеристики", "不检定，直接掷"),
    "runtime.dice.result": ("*🎲 {die}: {rolls} = {total}*", "*🎲 {die}: {rolls} = {total}*", "*🎲 {die}：{rolls} = {total}*"),
    "runtime.dice.resultStat": (
        "*🎲 {stat} check ({value}), {die}: {rolls} = {total}*",
        "*🎲 Проверка «{stat}» ({value}), {die}: {rolls} = {total}*",
        "*🎲 {stat}检定（{value}），{die}：{rolls} = {total}*",
    ),

    # Panel
    "ui.title": ("Adventure Journal", "Журнал приключений", "冒险日志"),
    "ui.open": ("Open the adventure journal", "Открыть журнал приключений", "打开冒险日志"),
    "ui.close": ("Close", "Закрыть", "关闭"),
    "ui.changeTemplate": ("Change genre template", "Сменить шаблон жанра", "更换题材模板"),
    "ui.loading": ("Loading the journal…", "Загружаю журнал…", "正在加载日志…"),
    "ui.notSet": ("Not set yet", "Пока не указано", "尚未设置"),
    "ui.edit": ("Edit", "Изменить", "编辑"),
    "ui.delete": ("Delete", "Удалить", "删除"),
    "ui.increase": ("Increase", "Увеличить", "增加"),
    "ui.decrease": ("Decrease", "Уменьшить", "减少"),
    "ui.yes": ("Yes", "Да", "是"),
    "ui.no": ("No", "Нет", "否"),
    "ui.undo": ("Undo", "Отменить", "撤销"),
    "ui.lastUpdate": ("Updated at {time}", "Обновлено в {time}", "更新于 {time}"),
    "ui.neverUpdated": ("Updates after the next AI reply", "Обновится после следующего ответа ИИ", "将在下一条 AI 回复后更新"),
    "ui.confirmDelete": ("Delete “{name}”?", "Удалить «{name}»?", "删除「{name}」？"),
    "ui.invalidNumber": ("Please enter a number, for example 10 or 10/100", "Введите число, например 10 или 10/100", "请输入数字，例如 10 或 10/100"),
    "ui.pending.title": ("Proposed changes: {count}", "Предложенные изменения: {count}", "建议的改动：{count}"),
    "ui.pending.apply": ("Apply", "Применить", "应用"),
    "ui.pending.dismiss": ("Dismiss", "Отклонить", "忽略"),
    "ui.empty.stats": ("No stats yet", "Характеристик пока нет", "暂无属性"),
    "ui.empty.inventory": ("Nothing here yet", "Здесь пока пусто", "这里还没有东西"),
    "ui.empty.quests": ("No goals yet", "Целей пока нет", "暂无目标"),
    "ui.empty.relations": ("No characters met yet", "Пока ни с кем не знакомы", "还没有认识的角色"),
    "ui.add.stat": ("Add stat", "Добавить характеристику", "添加属性"),
    "ui.add.statQuestion": ("New stat: name and value", "Новая характеристика: название и значение", "新属性：名称和数值"),
    "ui.add.statPlaceholder": ("Stamina=80/100", "Выносливость=80/100", "体力=80/100"),
    "ui.add.item": ("Add item", "Добавить предмет", "添加物品"),
    "ui.add.itemQuestion": ("Item name", "Название предмета", "物品名称"),
    "ui.add.quest": ("Add goal", "Добавить цель", "添加目标"),
    "ui.add.questQuestion": ("What is the goal?", "Какая цель?", "目标是什么？"),
    "ui.add.relation": ("Add character", "Добавить персонажа", "添加角色"),
    "ui.add.relationQuestion": ("Character name", "Имя персонажа", "角色名称"),
    "ui.stat.editValue": ("New value for {name} (value or value/max)", "Новое значение «{name}» (значение или значение/максимум)", "{name} 的新数值（数值 或 数值/上限）"),
    "ui.item.editNote": ("Note for {name}", "Заметка к «{name}»", "{name} 的备注"),
    "ui.quest.active": ("Active", "Активные", "进行中"),
    "ui.quest.done": ("Completed", "Выполненные", "已完成"),
    "ui.quest.failed": ("Failed", "Проваленные", "已失败"),
    "ui.quest.changeStatus": ("Change status", "Сменить статус", "更改状态"),
    "ui.quest.editNote": ("Note for {name}", "Заметка к «{name}»", "{name} 的备注"),
    "ui.rel.editValue": ("{name}: attitude from −100 to 100", "{name}: отношение от −100 до 100", "{name}：好感度 −100 到 100"),
}

LOCALES = ("en", "ru", "zh-CN")
