# Темы Tavo: справочник

Выжимка из официальной документации (проверено по Tavo 1.6.0):
- https://docs.tavoai.dev/en/guides/theme/
- https://docs.tavoai.dev/en/guides/theme-development-guide/
- https://docs.tavoai.dev/en/guides/theme-development/
- https://docs.tavoai.dev/en/guides/mcp-server/
- https://docs.tavoai.dev/en/guides/javascript-api/ (раздел «Chat Themes»)

## Из чего состоит тема

| Часть | Что задаёт |
|---|---|
| Display mode | `message` или `visualNovel` (+ доля высоты пузыря в VN, 0.25–1.0) |
| Message style | `bubble` или `flat`; цвет, blur, радиус, выравнивание пузырей |
| Background | цвет, картинка, её прозрачность, или аватар персонажа как фон |
| Fonts | стили текста user/character: основной текст, «тон» (`**…**`, `(…)`), цитаты |
| Avatars | видимость аватара и имени, радиус; отдельно для групповых чатов |
| Composer (`console`) | фон, blur, радиус, цвет кнопки отправки, текст, placeholder |
| Thinking / status bar | только через API/архив, в редакторе отдельного пункта нет |
| Custom CSS | доп. стили, работают **только при включённом Advanced Rendering** |
| Assets | файлы внутри темы (фон, текстуры для CSS) |

Тему можно сделать вообще без CSS. Официальные темы только для чтения, перед правкой их копируют.
Тема общая для всех чатов, к которым она привязана. Созданная тема к чату автоматически не применяется.

## Три способа сделать тему

1. **Вручную в приложении**: боковая панель → More → Themes → создать/скопировать → настроить → Preview → Save → применить к тестовому чату.
2. **AI-агент + MCP**: More → Settings → Creator → MCP Server → Access range (Local network, если агент на другом устройстве) → включить → «Copy full connection config» → отправить агенту.
   Инструменты: `tavo_theme_create` (`theme.customCss`), `tavo_theme_update` (`id`, `patch.customCss`); схемы в `tavo://schemas/*`, документация в `tavo://docs/tools`. Bearer-токен никому не показывать.
3. **Офлайн `.thm`-архив** (без MCP): собрать ZIP и импортировать через «Import theme». См. ниже.

## Формат `.thm`

ZIP с расширением `.thm`. В корне **сразу** `theme.json` (UTF-8), без обёртывающей папки; картинки в одноуровневой `assets/`.

```
soft-night.thm
├── theme.json
└── assets/
    └── paper.png
```

- Минимум: `{"spec": "tavo_theme_v1", "name": "..."}`; `name` от 1 до 40 UTF-16-символов после trim.
- CSS хранится строкой в `custom_css`; отдельный `.css`-файл не подхватывается.
- Ссылка на ассет в CSS и в `background.image` выглядит как `theme/assets/<имя>`. Пробелы и не-ASCII в имени URL-кодируются (кодируется только имя файла).
- Для фона-картинки нужно `background.charAvatar: false`, иначе приоритет у аватара.
- Запрещено: вложенные папки в `assets/`, любые другие каталоги, симлинки, `..`, абсолютные пути, дубликаты, `__MACOSX/`, имена с `:*?"<>|`, имена, отличающиеся только регистром, зарезервированные имена Windows.
- Лимиты: 256 MiB сжатого архива, 1 GiB распакованного, до 64 файлов в корне, до 4096 ассетов.
- Только ZIP (Deflate), не 7z/RAR. Следить, чтобы не получилось `name.thm.zip`.

### Поля `theme.json` (snake_case в архиве!)

| Поле | Значения |
|---|---|
| `display_mode` | `message` / `visualNovel` |
| `visual_novel_bubble_height_ratio` | 0.25–1.0 (по умолчанию 0.6) |
| `bubble_display_type` | `bubble` / `flat` |
| `custom_css` | строка CSS |
| `background` | `charAvatar` (bool), `image` (string/null), `imageOpacity` (0–1), `color` |
| `user_bubble`, `character_bubble` | `color`, `blur` 0–100, `radius` 0–50, `alignment` `left`/`right` |
| `user_bubble_font`, `character_bubble_font` | см. объект шрифта ниже |
| `user_avatar`, `character_avatar`, `group_user_avatar`, `group_character_avatar` | `avatar` (bool), `name` (bool), `radius` 0–100 |
| `thinking`, `status_bar` | `fontSize` 1–100, `fontWeight` 100–900, `color`, `backgroundColor` |
| `console` | `color`, `blur`, `radius` 0–50, `sendColor`, `fontSize`, `fontWeight`, `fontColor`, `placeholderColor` |

Объект шрифта:
- `textStyle`, `toneTextStyle`, `quoteTextStyle` → `fontFamily` (string/null), `fontSize` (16), `fontWeight` (400), `fontStyle` (`normal`/`italic`), `color` (у tone/quote можно `null`, тогда цвет наследуется);
- `toneHighlight`, `quoteHighlight` (bool, по умолчанию true);
- `toneDelimiters` (по умолчанию `["**","()","（）"]`), `quoteDelimiters` (по умолчанию `["“”","「」","\"\""]`);
- `toneSymbol` (`none`), `quoteSymbol` (`""`).

Подвох: если объект `user_bubble` не указан, пузырь пользователя будет справа. Если указан без `alignment`, будет `left`. Поэтому лучше прописывать всё явно, взяв за основу полный пример.

### Цвета: три разных формата

| Где | Формат | Пример (#202838, непрозрачный) |
|---|---|---|
| `theme.json` (архив) | десятичное целое 0xAARRGGBB | `4280297528` |
| TavoJS / MCP | строка `#AARRGGBB` | `"#FF202838"` |
| CSS | обычный CSS | `#202838`, `rgba(32,40,56,.8)` |

Перевод: `int("FF202838", 16)` → `4280297528`.

### Имена полей: архив и API

| Архив | TavoJS / MCP |
|---|---|
| `custom_css` | `customCss` |
| `user_bubble` | `userBubble` |
| `background.charAvatar` | `background.useAvatar` |
| `background.imageOpacity` | `background.opacity` |

Ответ MCP/TavoJS нельзя сохранить как `theme.json` без конвертации.

## Custom CSS

- Только сам CSS: без `<style>`, HTML и markdown-ограждений.
- Применяется после базовых стилей и может их перебивать. Если изменение базовой настройки не видно, причина, скорее всего, в CSS.
- Стилизует только сообщения, аватары и веб-композер. Настройки, меню и системные диалоги не затрагивает, внутрь iframe не проникает.
- Через API строка `customCss` **целиком заменяет** старую: не передать поле → старое сохраняется, `""` → очистка, `null` → невалидно.

### Публичные селекторы (полный список)

| Селектор | Цель |
|---|---|
| `.tavo-bubble` / `.tavo-user-bubble` / `.tavo-character-bubble` | пузыри (фон, рамка, тень) |
| `.tavo-bubble-content` / `.tavo-user-bubble-content` / `.tavo-character-bubble-content` | контейнеры содержимого (типографика) |
| `.tavo-bubble-content-body` | тело содержимого |
| `.tavo-message-divider` | разделитель в flat-режиме (у последнего сообщения скрыт) |
| `.tavo-action-bar-button`, `.tavo-action-bar-button-group` | кнопки тулбара и их общий фон (пункты меню сюда не входят) |
| `.tavo-message-content` | текст сообщения |
| `.tavo-message-attachments` | вложения |
| `.tavo-message-reasoning`, `.tavo-message-reasoning > summary` | блок рассуждений и его заголовок |
| `.tavo-avatar` | все аватары |
| `.tavo-user-avatar, .tavo-group-user-avatar` | аватары пользователя |
| `.tavo-character-avatar, .tavo-group-character-avatar` | аватары персонажа |
| `.tavo-speaker-name` | имя говорящего |
| `.tavo-composer`, `.tavo-composer-shell`, `.tavo-composer-input` | поле ввода |
| `.tavo-composer-add-icon` / `-send-icon` / `-stop-icon` / `-voice-icon` | иконки (это картинки: `color` на них не действует, работают size/opacity/filter) |

Старые `.tav-*` аналоги поддерживаются для совместимости. Все остальные классы, CSS-переменные и DOM-структура внутренние, опираться на них нельзя.

## Ассеты

- В редакторе: Custom styles → Assets → Import → «Copy address» копирует готовый `url("theme/assets/...")`.
- При совпадении имени файл переименовывается в `name (1).png`, поэтому всегда используется возвращённый адрес.
- Переименование или удаление ассета не обновляет ссылки в `customCss` (только `background.image`).
- Внешние URL картинок и шрифтов в CSS в `.thm` не упаковываются.
- TavoJS: `tavo.theme.assets.list/import/export/rename/delete`. `import` принимает только `files/chat/<name>` или HTTP(S)-URL.

## Проверка перед публикацией

Короткие и длинные сообщения, код, вложения; user, character и групповой чат; раскрытые рассуждения; открытая клавиатура, генерация, запись голоса; телефон и десктоп; режимы bubble и flat.
Затем экспорт → импорт отдельной копией («save as new») → повторная проверка.

## Публикация

Tavo Hub → Themes → My themes → загрузить `.thm` → Publish. В описании указать, что нужен Advanced Rendering, и перечислить протестированные режимы и устройства.

## Эталон

Официальный пример: https://docs.tavoai.dev/static/examples/themes/soft-night.thm
(`theme.json` + `assets/paper.png`). Его `theme.json` лежит в `docs/examples/soft-night.theme.json`.
