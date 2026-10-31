"""Сборка темы «Dictionary of the Khazars» для Tavo — по роману Милорада Павича.

Словарь из трёх книг — Красной, Зелёной и Жёлтой: три версии одной истории
о том, как хазары выбирали веру. Ни одна не врёт целиком, ни одна не права до конца.

Фон — ночной Каспий: на берегу силуэт хазарской крепости, низкая мутная луна,
а среди звёзд еле видны буквы — те, что принцесса Атех забыла.
Каждый ответ персонажа — словарная статья одной из трёх книг (по содержимому
сообщения), со своим цветом и вкладкой-указателем. Пока персонаж отвечает,
над полем ввода поднимаются и тают буквы.

Книги различаются только цветом, без религиозных символов.

Запуск: python themes/khazar-dictionary/build.py
"""
import json
import math
import random
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
FONTS = HERE / "fonts-src"
DIST = HERE.parent.parent / "dist"

W, H = 900, 1950
HORIZON = 1120
MOON = (236, 222, 186)
INK = (5, 7, 9)
PARCH = (228, 218, 196)

# Три книги: цвет текста/корешка и глубокий тон для подложки
BOOKS = [
    {"name": "The Red Book",    "color": "#B5574C", "rgb": "181, 87, 76"},
    {"name": "The Green Book",  "color": "#7FA383", "rgb": "127, 163, 131"},
    {"name": "The Yellow Book", "color": "#CDA956", "rgb": "205, 169, 86"},
]
# Статьи, которые есть во всех трёх книгах, и по одной своей у каждой
ENTRIES = [
    ["Ateh", "Kagan", "Khazar Polemic", "Brankovich, Avram"],
    ["Ateh", "Kagan", "Khazar Polemic", "Masudi, Yusuf"],
    ["Ateh", "Kagan", "Khazar Polemic", "Cohen, Samuel"],
]

GLYPHS = "ABCDEFGHIKLMNOPRSTVXZabdefghiklmnoprstuvzАБВГДЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯбвгджзлмнпфцчшщъыэюя"


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def glow_at(arr, x, y, radius, color, strength):
    yy, xx = np.ogrid[0:H, 0:W]
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * radius ** 2)) * strength
    arr += np.array(color)[None, None, :] * g[..., None]


def font_with(chars, size, path):
    """Шрифт и список символов, которые в нём реально есть."""
    from fontTools.ttLib import TTFont
    cmap = TTFont(path).getBestCmap()
    return ImageFont.truetype(str(path), size), [c for c in chars if ord(c) in cmap]


def make_background():
    rng = random.Random(1984)  # год выхода романа
    yy, xx = np.mgrid[0:H, 0:W]
    t = yy / H

    # небо: почти чёрное сверху, к горизонту зеленовато-серая дымка
    k = np.clip(yy / HORIZON, 0, 1) ** 2.2
    sky = np.array([6, 9, 12]) * (1 - k[..., None]) + np.array([24, 32, 34]) * k[..., None]
    # море: темнее неба, к низу совсем чёрное
    s = np.clip((yy - HORIZON) / (H - HORIZON), 0, 1)
    sea = np.array([14, 20, 22]) * (1 - s[..., None]) + np.array([4, 6, 8]) * s[..., None]
    arr = np.where((yy < HORIZON)[..., None], sky, sea).astype(np.float64)

    # звёзды — редкие и тусклые
    for _ in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, HORIZON - 120)
        b = rng.uniform(40, 150) * (1 - y / HORIZON * 0.6)
        r = rng.choice([1, 1, 1, 2])
        arr[int(y):int(y) + r, int(x):int(x) + r] += b

    # забытые буквы среди звёзд
    letters = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(letters)
    for _ in range(46):
        f, chars = font_with(GLYPHS, rng.randint(15, 30), FONTS / "Alegreya-Regular.ttf")
        x, y = rng.uniform(20, W - 40), rng.uniform(60, HORIZON - 260)
        ld.text((x, y), rng.choice(chars), font=f, fill=rng.randint(50, 110))
    lt = np.asarray(letters.filter(ImageFilter.GaussianBlur(0.8)), dtype=np.float64)[..., None] / 255
    arr += lt * np.array(PARCH) * 0.45

    # луна низко над морем, в дымке
    mx, my, mr = 640, 905, 44
    glow_at(arr, mx, my, 220, (90, 84, 70), 0.55)
    glow_at(arr, mx, my, 70, MOON, 0.35)
    moon = np.hypot(xx - mx, yy - my) < mr
    arr[moon] = arr[moon] * 0.2 + np.array(MOON) * 0.8
    # полосы облаков через луну
    haze = Image.new("L", (W, H), 0)
    hd = ImageDraw.Draw(haze)
    for _ in range(26):
        y = rng.gauss(900, 120)
        x = rng.uniform(-200, W)
        hd.ellipse([x, y - rng.uniform(5, 14), x + rng.uniform(260, 620), y + rng.uniform(5, 14)], fill=rng.randint(90, 200))
    hz = np.asarray(haze.filter(ImageFilter.GaussianBlur(10)), dtype=np.float64)[..., None] / 255
    arr = arr * (1 - hz * 0.7) + np.array([20, 26, 28]) * hz * 0.7

    # лунная дорожка: рваные горизонтальные блики
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    path = Image.new("L", (W, H), 0)
    pd = ImageDraw.Draw(path)
    for y in range(HORIZON + 4, H, 5):
        d = (y - HORIZON) / (H - HORIZON)
        spread = 30 + 260 * d
        for _ in range(rng.randint(1, 3)):
            cx = mx + rng.gauss(0, spread * 0.45)
            ln = rng.uniform(8, 40 + 90 * d)
            pd.line([(cx - ln / 2, y), (cx + ln / 2, y)], fill=int(rng.uniform(60, 180) * (1 - d) ** 1.4), width=1 + int(d * 3))
    p = np.asarray(path.filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float64)[..., None] / 255
    arr = np.asarray(img, dtype=np.float64) + p * np.array(MOON) * 0.55

    # мелкая рябь по всему морю
    rip = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(rip)
    for _ in range(900):
        y = rng.uniform(HORIZON + 6, H)
        x = rng.uniform(0, W)
        ln = rng.uniform(6, 30)
        rd.line([(x, y), (x + ln, y)], fill=rng.randint(20, 60))
    r = np.asarray(rip, dtype=np.float64)[..., None] / 255
    arr += r * np.array([120, 140, 140]) * 0.25

    # берег слева: мыс и крепость — кирпичные стены с башнями (рисуем маской)
    sil = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(sil)
    base = HORIZON - 58
    d.polygon([(0, base - 6), (60, base - 10), (390, base - 4), (450, HORIZON - 26),
               (530, HORIZON - 6), (580, HORIZON), (0, HORIZON)], fill=255)
    d.rectangle([40, base - 62, 360, base], fill=255)                       # стена
    for tx in (40, 140, 250, 350):                                          # башни
        d.rectangle([tx - 14, base - 96, tx + 14, base], fill=255)
        for m in range(-14, 14, 8):
            d.rectangle([tx + m, base - 104, tx + m + 4, base - 96], fill=255)
    for cx in range(54, 340, 10):                                           # зубцы стены
        d.rectangle([cx, base - 70, cx + 5, base - 62], fill=255)
    m = np.asarray(sil, dtype=np.float64)[..., None] / 255
    arr = arr * (1 - m) + np.array(INK) * m
    # отражение: перевёрнутый силуэт темнит воду, размытый и рваный
    band = 130
    refl = np.zeros((H, W))
    refl[HORIZON:HORIZON + band] = np.asarray(sil, dtype=np.float64)[HORIZON - band:HORIZON][::-1] / 255
    for y in range(HORIZON, HORIZON + band):
        refl[y] = np.roll(refl[y], rng.randint(-3, 3))
    refl = np.asarray(Image.fromarray((refl * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5)), dtype=np.float64) / 255
    arr *= (1 - refl * 0.6)[..., None]
    # одно окно в башне
    arr[base - 66:base - 59, 248:253] = (120, 92, 52)
    glow_at(arr, 250, base - 63, 18, (200, 150, 80), 0.25)

    # виньетка, затемнить середину под сообщения, зерно
    vign = np.clip(1.15 - np.hypot((xx / W - 0.5) * 1.2, (yy / H - 0.45) * 0.9), 0.3, 1)
    veil = 1 - 0.28 * np.exp(-((t - 0.62) / 0.24) ** 2)
    arr *= (vign * veil * 0.9)[..., None]
    arr += np.random.default_rng(5).normal(0, 3, (H, W))[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(ASSETS / "caspian.jpg", quality=88, optimize=True)


def make_letters_tile():
    """Бесшовный тайл рассыпанных букв: одни чёткие, другие уже расплываются."""
    w, h = 360, 240
    rng = random.Random(9)
    layers = []
    for blur in (0, 1.2, 2.6):
        full = Image.new("L", (w * 3, h * 3), 0)
        d = ImageDraw.Draw(full)
        for _ in range(9):
            f, chars = font_with(GLYPHS, rng.randint(14, 26), FONTS / "Alegreya-Regular.ttf")
            x, y = rng.uniform(0, w), rng.uniform(0, h)
            ch = rng.choice(chars)
            a = rng.randint(90, 170) if blur == 0 else rng.randint(60, 120)
            for dx in range(3):
                for dy in range(3):
                    d.text((x + dx * w, y + dy * h), ch, font=f, fill=a)
        if blur:
            full = full.filter(ImageFilter.GaussianBlur(blur))
        layers.append(np.asarray(full.crop((w, h, 2 * w, 2 * h)), dtype=np.float64))
    alpha = np.clip(np.maximum.reduce(layers), 0, 255).astype(np.uint8)
    img = Image.new("RGBA", (w, h), PARCH + (0,))
    img.putalpha(Image.fromarray(alpha))
    img.save(ASSETS / "letters.png", optimize=True)


def make_svgs():
    # разделитель: три ромба трёх книг
    colors = [b["color"] for b in BOOKS]
    divider = ('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="26" viewBox="0 0 640 26">'
               '<defs><linearGradient id="a" x1="0" x2="1"><stop offset="0" stop-color="#c9ae74" stop-opacity="0"/>'
               '<stop offset="1" stop-color="#c9ae74" stop-opacity="0.55"/></linearGradient>'
               '<linearGradient id="b" x1="0" x2="1"><stop offset="0" stop-color="#c9ae74" stop-opacity="0.55"/>'
               '<stop offset="1" stop-color="#c9ae74" stop-opacity="0"/></linearGradient></defs>'
               '<path d="M20,13 L290,13" stroke="url(#a)"/><path d="M350,13 L620,13" stroke="url(#b)"/>'
               + "".join(f'<path d="M{x},8 L{x + 5},13 L{x},18 L{x - 5},13 Z" fill="{c}"/>'
                         for x, c in zip((304, 320, 336), colors))
               + '</svg>')
    (ASSETS / "divider.svg").write_text(divider, encoding="utf-8")


def book_rules():
    """Книга и статья по самому сообщению: число абзацев (1..6+) и есть ли курсив."""
    base = ".tavo-character-bubble"
    rules = ["/* ---------- Книги и статьи (сгенерировано build.py) ---------- */"]
    for k in range(1, 7):
        paras = f":has(p:nth-of-type({k}))" + (f":not(:has(p:nth-of-type({k + 1})))" if k < 6 else "")
        for em in (0, 1):
            flag = ":has(:is(em, i))" if em else ":not(:has(:is(em, i)))"
            b = (k - 1) % 3
            entry = ENTRIES[b][((k - 1) // 3) * 2 + em]
            book = BOOKS[b]
            rules.append(
                f'{base}{paras}{flag} {{ --book: {book["color"]}; --book-rgb: {book["rgb"]}; '
                f'--entry: "{entry}  ·  {book["name"]}"; --tab: "{entry[0]}"; }}')
    return "\n".join(rules)


def font(color, tone, quote):
    def style(c, it=False, weight=400):
        return {"fontFamily": None, "fontSize": 17, "fontWeight": weight,
                "fontStyle": "italic" if it else "normal", "color": c}
    return {
        "textStyle": style(color),
        "toneTextStyle": style(tone, True),
        "quoteTextStyle": style(quote, False, 500),
        "toneHighlight": True,
        "toneDelimiters": ["**", "()", "（）"],
        "toneSymbol": "none",
        "quoteHighlight": True,
        "quoteDelimiters": ["“”", "«»", "„“", "\"\""],
        "quoteSymbol": "\"\"",
    }


def manifest(css):
    avatar = {"avatar": True, "radius": 100, "name": True}
    return {
        "spec": "tavo_theme_v1",
        "name": "Dictionary of the Khazars",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {"charAvatar": False, "image": "theme/assets/caspian.jpg", "imageOpacity": 1, "color": argb("#0A0E10")},
        "user_bubble": {"color": argb("#141A1C", 0xEB), "blur": 0, "radius": 2, "alignment": "right"},
        "character_bubble": {"color": argb("#171513", 0xF0), "blur": 0, "radius": 2, "alignment": "left"},
        "user_bubble_font": font(argb("#D6D9D4"), argb("#949C96"), argb("#EEF0EA")),
        "character_bubble_font": font(argb("#E4DAC4"), argb("#A3967E"), argb("#EBCF96")),
        "console": {"color": argb("#101517", 0xF2), "blur": 8, "radius": 2, "sendColor": argb("#C9AE74"),
                    "fontSize": 17, "fontWeight": 400, "fontColor": argb("#E4DAC4"), "placeholderColor": argb("#77766F")},
        "thinking": {"fontSize": 14, "fontWeight": 400, "color": argb("#A3967E"), "backgroundColor": argb("#101517", 0xE6)},
        "status_bar": {"fontSize": 13, "fontWeight": 500, "color": argb("#C9AE74"), "backgroundColor": argb("#101517", 0xE6)},
        "user_avatar": dict(avatar), "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar), "group_character_avatar": dict(avatar),
    }


def main():
    ASSETS.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_background()
    make_letters_tile()
    make_svgs()
    css = (HERE / "style.css").read_text(encoding="utf-8").replace("BOOK_RULES", book_rules())
    m = manifest(css)
    (HERE / "theme.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = DIST / "khazar-dictionary.thm"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "theme.json", "theme.json")
        for f in sorted(ASSETS.iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
