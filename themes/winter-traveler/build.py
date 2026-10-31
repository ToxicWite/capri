"""Сборка темы «If on a winter's night a traveler» для Tavo — по роману Итало Кальвино.

«Роман начинается на вокзале, пыхтит паровоз, шипение поршня застилает
начало главы, облако дыма скрывает часть первого абзаца».

Фон — зимний ночной вокзал: фонари, часы, окно буфета, поезд в пару, снег.

Запуск: python3 themes/winter-traveler/build.py
"""
import json
import math
import random
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
DIST = HERE.parent.parent / "dist"

W, H = 900, 1950
LAMP = (255, 205, 140)
SIL = (10, 13, 20)

# Десять начатых романов. Их названия складываются в одну фразу.
INCIPITS = [
    "If on a winter’s night a traveler",
    "Outside the town of Malbork",
    "Leaning from the steep slope",
    "Without fear of wind or vertigo",
    "Looks down in the gathering shadow",
    "In a network of lines that enlace",
    "In a network of lines that intersect",
    "On the carpet of leaves illuminated by the moon",
    "Around an empty grave",
    "What story down there awaits its end?",
]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def glow_at(arr, x, y, radius, color, strength):
    yy, xx = np.ogrid[0:H, 0:W]
    g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * radius ** 2)) * strength
    arr += np.array(color)[None, None, :] * g[..., None]


def make_background():
    rng = random.Random(1979)  # год выхода романа
    yy, xx = np.mgrid[0:H, 0:W]
    t = yy / H
    sky = np.array([16, 20, 32]) + np.array([14, 16, 22]) * np.clip(t / 0.55, 0, 1)[..., None]
    arr = sky.astype(np.float64)

    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    plat = 1280
    # навес вокзала: фермы и колонны
    d.rectangle([0, 150, W, 186], fill=SIL)
    for x in range(-40, W + 80, 120):
        d.line([(x, 186), (x + 60, 150)], fill=(22, 26, 36), width=4)
        d.line([(x + 60, 186), (x + 120, 150)], fill=(22, 26, 36), width=4)
    for x in (70, 470, 830):
        d.rectangle([x - 9, 186, x + 9, plat], fill=SIL)
        d.rectangle([x - 16, plat - 30, x + 16, plat], fill=SIL)
    # часы на колонне
    cx, cy = 470, 300
    d.ellipse([cx - 52, cy - 52, cx + 52, cy + 52], fill=(222, 214, 196), outline=SIL, width=8)
    for k in range(12):
        a = k * math.tau / 12
        d.line([(cx + math.cos(a) * 38, cy + math.sin(a) * 38), (cx + math.cos(a) * 46, cy + math.sin(a) * 46)], fill=SIL, width=3)
    d.line([(cx, cy), (cx + 2, cy - 34)], fill=SIL, width=4)          # почти полночь
    d.line([(cx, cy), (cx - 8, cy - 24)], fill=SIL, width=6)
    # здание вокзала справа с окном буфета
    d.rectangle([560, 520, W, plat], fill=(14, 17, 26))
    d.rectangle([620, 760, 820, 1000], fill=(70, 46, 24))
    for gx in range(620, 821, 50):
        d.line([(gx, 760), (gx, 1000)], fill=(14, 17, 26), width=5)
    d.line([(620, 880), (820, 880)], fill=(14, 17, 26), width=5)
    # поезд слева
    d.rectangle([0, 820, 430, plat - 20], fill=(12, 15, 22))
    for wx in range(30, 400, 90):
        d.rectangle([wx, 880, wx + 60, 940], fill=(90, 62, 30))
    d.rectangle([0, plat - 40, 430, plat - 20], fill=SIL)
    # платформа и рельсы
    d.rectangle([0, plat, W, H], fill=(20, 23, 30))
    for i in range(12):
        y = plat + int(670 * (i / 12) ** 1.7)
        d.line([(0, y), (W, y)], fill=(26, 30, 38), width=2)
    # фонари
    lamps = [(240, 520), (700, 470)]
    for lx, ly in lamps:
        d.rectangle([lx - 4, ly, lx + 4, plat], fill=SIL)
        d.polygon([(lx - 22, ly - 40), (lx + 22, ly - 40), (lx + 16, ly), (lx - 16, ly)], fill=(255, 220, 160))
        d.rectangle([lx - 26, ly - 46, lx + 26, ly - 40], fill=SIL)

    arr = np.asarray(img.convert("RGB"), dtype=np.float64)
    for lx, ly in lamps:
        glow_at(arr, lx, ly - 20, 120, LAMP, 0.35)
        glow_at(arr, lx, ly - 20, 30, LAMP, 0.6)
    glow_at(arr, 720, 880, 160, LAMP, 0.25)          # свет из буфета
    for wx in range(30, 400, 90):
        glow_at(arr, wx + 30, 910, 50, LAMP, 0.15)    # окна вагона

    # пар паровоза и туман
    steam = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(steam)
    for _ in range(80):
        x = rng.gauss(260, 150)
        y = rng.gauss(760, 160)
        r = rng.uniform(40, 120)
        sd.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=rng.randint(40, 90))
    for _ in range(60):
        x, y, r = rng.uniform(-100, W + 100), rng.gauss(plat, 50), rng.uniform(60, 160)
        sd.ellipse([x - r, y - r * 0.3, x + r, y + r * 0.3], fill=rng.randint(30, 60))
    s = np.asarray(steam.filter(ImageFilter.GaussianBlur(30)), dtype=np.float64)[..., None] / 255
    arr = arr * (1 - s * 0.8) + np.array([150, 156, 170]) * s * 0.8

    # снег: дальний мелкий и ближний крупный, размытый
    snow = Image.new("L", (W, H), 0)
    nd = ImageDraw.Draw(snow)
    for _ in range(700):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.choice([1, 1, 1.5, 2])
        nd.ellipse([x - r, y - r, x + r, y + r], fill=rng.randint(120, 220))
    big = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(big)
    for _ in range(40):
        x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(4, 8)
        bd.ellipse([x - r, y - r, x + r, y + r], fill=rng.randint(80, 140))
    flakes = np.maximum(np.asarray(snow, dtype=np.float64), np.asarray(big.filter(ImageFilter.GaussianBlur(3)), dtype=np.float64))
    arr = arr + flakes[..., None] / 255 * np.array([210, 216, 228]) * 0.8

    # приглушить, виньетка, затемнить середину под сообщения, зерно
    vign = np.clip(1.15 - np.hypot((xx / W - 0.5) * 1.2, (yy / H - 0.45) * 0.9), 0.25, 1)
    veil = 1 - 0.3 * np.exp(-((t - 0.6) / 0.22) ** 2)
    arr *= (vign * veil * 0.85)[..., None]
    arr += np.random.default_rng(3).normal(0, 3, (H, W))[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(ASSETS / "station.jpg", quality=88, optimize=True)


def make_snow_tile():
    """Бесшовный тайл снега для пузырей персонажа."""
    s = 240
    rng = random.Random(6)
    big = Image.new("RGBA", (s * 3, s * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    for _ in range(14):
        x, y, r = rng.uniform(0, s), rng.uniform(0, s), rng.choice([1.6, 2, 2.6, 3])
        a = rng.randint(70, 140)
        for dx in range(3):
            for dy in range(3):
                px, py = x + dx * s, y + dy * s
                d.ellipse([px - r, py - r, px + r, py + r], fill=(232, 236, 244, a))
    big.filter(ImageFilter.GaussianBlur(0.9)).crop((s, s, 2 * s, 2 * s)).save(ASSETS / "snow.png", optimize=True)


def make_steam():
    """Полоса пара, поднимающегося над полем ввода; бесшовная по вертикали и горизонтали."""
    w, h = 400, 200
    rng = random.Random(2)
    full = Image.new("L", (w * 3, h * 3), 0)
    d = ImageDraw.Draw(full)
    for _ in range(18):
        x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(25, 60)
        a = rng.randint(50, 110)
        for dx in range(3):
            for dy in range(3):
                px, py = x + dx * w, y + dy * h
                d.ellipse([px - r, py - r * 0.6, px + r, py + r * 0.6], fill=a)
    full = full.filter(ImageFilter.GaussianBlur(18)).crop((w, h, 2 * w, 2 * h))
    img = Image.new("RGBA", (w, h), (200, 206, 218, 0))
    img.putalpha(full)
    img.save(ASSETS / "steam.png", optimize=True)


def make_svgs():
    # ленточка-закладка: роман не дочитан
    ribbon = ('<svg xmlns="http://www.w3.org/2000/svg" width="14" height="44" viewBox="0 0 14 44">'
              '<path d="M0,0 L14,0 L14,44 L7,37 L0,44 Z" fill="#7a2630"/>'
              '<path d="M2,0 L2,40" stroke="#a8434d" stroke-width="0.8" opacity="0.7"/></svg>')
    (ASSETS / "ribbon.svg").write_text(ribbon, encoding="utf-8")
    divider = ('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="26" viewBox="0 0 640 26">'
               '<defs><linearGradient id="a" x1="0" x2="1"><stop offset="0" stop-color="#d8c9a8" stop-opacity="0"/>'
               '<stop offset="1" stop-color="#d8c9a8" stop-opacity="0.6"/></linearGradient>'
               '<linearGradient id="b" x1="0" x2="1"><stop offset="0" stop-color="#d8c9a8" stop-opacity="0.6"/>'
               '<stop offset="1" stop-color="#d8c9a8" stop-opacity="0"/></linearGradient></defs>'
               '<path d="M20,13 L296,13" stroke="url(#a)"/><path d="M344,13 L620,13" stroke="url(#b)"/>'
               '<g fill="#d8c9a8"><circle cx="306" cy="13" r="1.6"/><circle cx="320" cy="13" r="1.6"/>'
               '<circle cx="334" cy="13" r="1.6"/></g></svg>')
    (ASSETS / "divider.svg").write_text(divider, encoding="utf-8")


def chapter_rules():
    """Название главы по самому сообщению: число абзацев (1..5+) и есть ли курсив."""
    base = ".tavo-character-bubble-content"
    rules = ["/* ---------- Главы (сгенерировано build.py) ---------- */"]
    for k in range(1, 6):
        paras = f":has(p:nth-of-type({k}))" + (f":not(:has(p:nth-of-type({k + 1})))" if k < 5 else "")
        for em in (0, 1):
            flag = ":has(:is(em, i))" if em else ":not(:has(:is(em, i)))"
            i = (k - 1) * 2 + em
            title = INCIPITS[i].replace('"', '\\"')
            rules.append(f'{base}{paras}{flag}::before {{ content: "{ROMAN[i]}  ·  {title}"; }}')
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
        "name": "If on a winter's night",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {"charAvatar": False, "image": "theme/assets/station.jpg", "imageOpacity": 1, "color": argb("#10141E")},
        "user_bubble": {"color": argb("#1A1E28", 0xEB), "blur": 0, "radius": 2, "alignment": "right"},
        "character_bubble": {"color": argb("#1C1A18", 0xF0), "blur": 0, "radius": 2, "alignment": "left"},
        "user_bubble_font": font(argb("#D9DCE4"), argb("#9AA1B0"), argb("#F0F2F6")),
        "character_bubble_font": font(argb("#E6DCC6"), argb("#A89C86"), argb("#F3D9A6")),
        "console": {"color": argb("#14171F", 0xF2), "blur": 8, "radius": 3, "sendColor": argb("#D8C9A8"),
                    "fontSize": 17, "fontWeight": 400, "fontColor": argb("#E6DCC6"), "placeholderColor": argb("#7C7A76")},
        "thinking": {"fontSize": 14, "fontWeight": 400, "color": argb("#A89C86"), "backgroundColor": argb("#14171F", 0xE6)},
        "status_bar": {"fontSize": 13, "fontWeight": 500, "color": argb("#D8C9A8"), "backgroundColor": argb("#14171F", 0xE6)},
        "user_avatar": dict(avatar), "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar), "group_character_avatar": dict(avatar),
    }


def main():
    ASSETS.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_background()
    make_snow_tile()
    make_steam()
    make_svgs()
    css = (HERE / "style.css").read_text(encoding="utf-8").replace("CHAPTER_RULES", chapter_rules())
    m = manifest(css)
    (HERE / "theme.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = DIST / "winter-traveler.thm"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "theme.json", "theme.json")
        for f in sorted(ASSETS.iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
