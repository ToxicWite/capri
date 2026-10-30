"""Сборка темы «Invisible Cities» для Tavo — по «Невидимым городам» Итало Кальвино.

Марко Поло рассказывает Хубилай-хану о городах, которых, возможно, нет.
Фон — свиток тушью: Бавкида на сваях над облаками, горы в тумане,
Вальдрада, отражённая в озере.

Запуск: python3 themes/invisible-cities/build.py
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
INK = np.array([7, 10, 24], dtype=np.float64)
MIST = np.array([150, 164, 196], dtype=np.float64)
GOLD = (212, 175, 106)
LIGHT = (255, 214, 140)

# 55 городов Кальвино
CITIES = ("Diomira Isidora Dorothea Zaira Anastasia Tamara Zora Despina Zirma Isaura "
          "Maurilia Fedora Zoe Zenobia Euphemia Zobeide Hypatia Armilla Chloe Valdrada "
          "Olivia Sophronia Eutropia Zemrude Aglaura Octavia Ersilia Baucis Leandra Melania "
          "Esmeralda Phyllis Pyrrha Adelma Eudoxia Moriana Clarice Eusapia Beersheba Leonia "
          "Irene Argia Thekla Trude Olinda Laudomia Perinthia Procopia Raissa Andria "
          "Cecilia Marozia Penthesilea Theodora Berenice").split()


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def ridge(rng, base, amp, n=16):
    """Линия хребта: сумма синусов со случайными фазами."""
    x = np.arange(W)
    y = np.full(W, float(base))
    for k in range(1, n + 1):
        y += amp / k ** 0.95 * np.sin(x / W * math.pi * (k * rng.uniform(0.9, 1.8)) + rng.uniform(0, math.tau))
    # острые пики: «складка» синусоиды
    y -= amp * 0.35 * np.abs(np.sin(x / W * math.pi * rng.uniform(3, 5) + rng.uniform(0, math.tau)))
    return y


def roof_house(d, x, y, w, h, fill, rng, lit=0.35):
    """Домик с загнутыми кверху краями крыши."""
    d.rectangle([x, y, x + w, y + h], fill=fill)
    eave = w * 0.28
    d.polygon([(x - eave, y + 2), (x - eave * 0.6, y - 4), (x + w / 2, y - h * 0.55),
               (x + w + eave * 0.6, y - 4), (x + w + eave, y + 2)], fill=fill)
    for wx in range(int(x + 4), int(x + w - 4), 9):
        if rng.random() < lit:
            d.rectangle([wx, y + h * 0.35, wx + 4, y + h * 0.35 + 6], fill=LIGHT)


def make_background():
    rng = random.Random(1972)  # год выхода книги
    yy, xx = np.mgrid[0:H, 0:W]
    t = yy / H

    # Небо: глубокий индиго к сумеречному лазуриту, тёплая полоса у горизонта гор
    top, mid = np.array([9, 13, 36]), np.array([40, 52, 98])
    sky = top + (mid - top) * np.clip(t / 0.5, 0, 1)[..., None] ** 1.3
    sky += np.array([60, 40, 10]) * np.exp(-((t - 0.36) / 0.05) ** 2)[..., None] * 0.35
    img = sky.copy()

    # Луна с ореолом
    mx, my, mr = 690, 220, 58
    md = np.hypot(xx - mx, yy - my)
    img += np.array([255, 220, 160]) * (np.exp(-(md / 170) ** 2) * 0.22)[..., None]
    moon = md < mr
    img[moon] = np.array([240, 226, 190]) * (1 - 0.08 * ((xx[moon] - mx + 20) / mr) ** 2)[..., None]

    # Звёзды
    for _ in range(140):
        sx, sy = rng.randrange(W), rng.randrange(int(H * 0.34))
        img[sy, sx] = np.maximum(img[sy, sx], [200, 205, 230]) * rng.uniform(0.6, 1)

    pil = Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert("RGBA")

    # Бавкида: дома на сваях, сваи уходят в облака
    city = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(city)
    sil = (8, 11, 28, 255)
    cx0, platform = 200, 470
    for i in range(11):
        x = cx0 + i * 26 + rng.uniform(-4, 4)
        d.line([(x, platform), (x + rng.uniform(-3, 3), 700)], fill=sil, width=2)
    d.rectangle([cx0 - 20, platform - 4, cx0 + 290, platform + 4], fill=sil)
    x = cx0 - 10
    while x < cx0 + 260:
        w = rng.uniform(28, 52)
        h = rng.uniform(22, 46)
        roof_house(d, x, platform - 4 - h, w, h, sil, rng)
        x += w + rng.uniform(10, 22)
    # пагода в центре
    px = cx0 + 130
    for k, (w, h) in enumerate([(54, 26), (44, 22), (34, 18), (24, 14)]):
        roof_house(d, px - w / 2, platform - 60 - k * 30 - h, w, h, sil, rng, lit=0.5)
    d.line([(px, platform - 60 - 4 * 30 - 14), (px, platform - 60 - 4 * 30 - 46)], fill=sil, width=2)
    pil = Image.alpha_composite(pil, city)

    # Облачное море, в котором тонут сваи
    clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clouds)
    for _ in range(70):
        x, y = rng.uniform(-100, W + 100), rng.gauss(640, 34)
        r = rng.uniform(50, 140)
        a = rng.randint(70, 140)
        cd.ellipse([x - r, y - r * 0.35, x + r, y + r * 0.35], fill=(176, 186, 214, a))
    clouds = clouds.filter(ImageFilter.GaussianBlur(16))
    pil = Image.alpha_composite(pil, clouds)

    arr = np.asarray(pil.convert("RGB"), dtype=np.float64)

    # Горы тушью: каждый хребет растворяется в тумане книзу
    layers = [(760, 70, 0.62), (860, 90, 0.45), (980, 110, 0.28), (1110, 120, 0.12)]
    for base, amp, lift in layers:
        ry = ridge(rng, base, amp)
        depth = yy - ry[None, :]
        inside = depth >= 0
        alpha = np.clip(1 - depth / 230, 0, 1) ** 1.1 * inside
        col = INK + (MIST - INK) * lift
        # мазок: у гребня темнее
        col_map = col[None, None, :] * (0.82 + 0.18 * np.clip(depth / 60, 0, 1))[..., None]
        arr = arr * (1 - alpha[..., None]) + col_map * alpha[..., None]
        # туман под хребтом
        haze = np.exp(-((depth - 150) / 60) ** 2) * 0.18 * (depth > 0)
        arr = arr * (1 - haze[..., None]) + MIST[None, None, :] * haze[..., None]

    # Озеро
    shore = 1440
    near = np.exp(-np.clip(yy - shore, 0, None) / 160)[..., None]
    water = np.array([12, 18, 42]) * (1 - near) + np.array([58, 72, 120]) * near
    lake = yy >= shore
    arr[lake] = water[lake]

    # Вальдрада на дальнем берегу
    city = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(city)
    sil = (10, 13, 30, 255)
    x = -10
    while x < W:
        kind = rng.random()
        w = rng.uniform(30, 70)
        if kind < 0.18:  # кампанила
            h = rng.uniform(120, 190)
            d.rectangle([x, shore - h, x + 18, shore], fill=sil)
            d.polygon([(x - 2, shore - h), (x + 9, shore - h - 34), (x + 20, shore - h)], fill=sil)
            d.rectangle([x + 6, shore - h + 14, x + 12, shore - h + 26], fill=LIGHT)
            x += 18 + rng.uniform(6, 20)
            continue
        h = rng.uniform(40, 90)
        d.rectangle([x, shore - h, x + w, shore], fill=sil)
        if kind < 0.45:  # купол
            d.pieslice([x + w * 0.15, shore - h - w * 0.35, x + w * 0.85, shore - h + w * 0.35], 180, 360, fill=sil)
        for wy in range(int(shore - h + 10), shore - 8, 14):
            for wx in range(int(x + 5), int(x + w - 6), 10):
                if rng.random() < 0.22:
                    d.rectangle([wx, wy, wx + 4, wy + 6], fill=LIGHT)
        x += w + rng.uniform(-6, 10)
    c = np.asarray(city, dtype=np.float64)
    a = c[..., 3:4] / 255
    arr = arr * (1 - a) + c[..., :3] * a

    # Отражение города: зеркально, с рябью и затуханием
    refl_h = min(520, H - shore)
    src = arr[shore - refl_h:shore][::-1].copy()
    ca = a[shore - refl_h:shore][::-1, :, 0]
    for i in range(refl_h):
        shift = int(5 * math.sin(i * 0.21) + 3 * math.sin(i * 0.053))
        src[i] = np.roll(src[i], shift, axis=0)
        ca[i] = np.roll(ca[i], shift)
    fade = (np.clip(1 - np.arange(refl_h) / refl_h, 0, 1) ** 1.5 * 0.55)[:, None]
    ripple = (np.arange(refl_h) % 7 < 2)[:, None] * 0.5
    k = (ca * fade * (1 - ripple))[..., None]
    region = arr[shore:shore + refl_h]
    arr[shore:shore + refl_h] = region * (1 - k) + src * k

    # Лунная дорожка на воде
    for y in range(shore + 6, H, 5):
        wdt = 6 + (y - shore) * 0.06 + rng.uniform(-3, 6)
        x0 = mx + rng.uniform(-8, 8) - wdt / 2
        alpha = 0.55 * (1 - (y - shore) / (H - shore)) ** 0.8
        xs = slice(int(max(0, x0)), int(min(W, x0 + wdt)))
        arr[y:y + 2, xs] = arr[y:y + 2, xs] * (1 - alpha) + np.array(LIGHT) * alpha

    # Шёлк: тонкое плетение и зерно; лёгкое затемнение середины под сообщения
    weave = ((xx % 3 == 0) * 0.025 + (yy % 3 == 0) * 0.025)
    arr *= (1 - weave)[..., None]
    arr += np.random.default_rng(4).normal(0, 3.5, (H, W))[..., None]
    veil = 1 - 0.22 * np.exp(-((t - 0.55) / 0.2) ** 2)
    arr *= veil[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(ASSETS / "scroll.jpg", quality=88, optimize=True)


def make_silk():
    """Тайл шёлка для страниц Марко: диагональное плетение, полупрозрачное."""
    s = 64
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(-s, s * 2, 4):
        d.line([(i, 0), (i + s, s)], fill=(160, 180, 230, 16), width=1)
        d.line([(i + 2, 0), (i + 2 - s, s)], fill=(10, 14, 30, 22), width=1)
    img.save(ASSETS / "silk.png", optimize=True)


def make_svgs():
    g = "#d4af6a"
    corner = ('<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22">'
              '<g transform="{t}"><path d="M2,20 L2,6 Q2,2 6,2 L20,2" fill="none" stroke="' + g + '" stroke-width="1.3"/>'
              '<path d="M6,9 Q6,6 9,6" fill="none" stroke="' + g + '" stroke-width="1"/>'
              '<circle cx="2" cy="2" r="1.6" fill="' + g + '"/></g></svg>')
    for name, t in [("tl", ""), ("tr", "translate(22,0) scale(-1,1)"), ("bl", "translate(0,22) scale(1,-1)"),
                    ("br", "translate(22,22) scale(-1,-1)")]:
        (ASSETS / f"corner-{name}.svg").write_text(corner.replace("{t}", t), encoding="utf-8")

    # Печать хана: красный квадрат с абстрактным знаком
    seal = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
            '<rect x="1" y="1" width="22" height="22" rx="2" fill="#c8452c"/>'
            '<rect x="3.2" y="3.2" width="17.6" height="17.6" fill="none" stroke="#f3e2c8" stroke-width="1.2"/>'
            '<path d="M7,7 L17,7 M12,7 L12,17 M7,12 L17,12 M8,17 L16,17 M7,7 L7,10 M17,14 L17,17" '
            'stroke="#f3e2c8" stroke-width="1.4" stroke-linecap="square" fill="none"/></svg>')
    (ASSETS / "seal.svg").write_text(seal, encoding="utf-8")

    # Конь для шахматной доски
    knight = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
              '<path d="M6,21 L18,21 L18,19 L15.5,19 L15.5,15 C16.5,12.5 18.5,10.5 17.2,7.6 L14.2,4.2 '
              'L13.4,2 L11.6,3.9 C8.6,4.8 6.4,7.6 6.8,10.8 L9.8,10 L7.8,14 L8.6,19 L6,19 Z" fill="' + g + '"/>'
              '<circle cx="12.6" cy="6.6" r="0.9" fill="#0c0b10"/></svg>')
    (ASSETS / "knight.svg").write_text(knight, encoding="utf-8")

    # Разделитель: линия-река с луной
    divider = ('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="28" viewBox="0 0 640 28">'
               '<defs><linearGradient id="f" x1="0" x2="1"><stop offset="0" stop-color="' + g + '" stop-opacity="0"/>'
               '<stop offset="0.5" stop-color="' + g + '" stop-opacity="0.85"/><stop offset="1" stop-color="' + g + '" stop-opacity="0"/></linearGradient></defs>'
               '<path d="M20,16 Q120,10 220,16 T420,16 T620,16" fill="none" stroke="url(#f)" stroke-width="1"/>'
               '<circle cx="320" cy="12" r="5" fill="none" stroke="' + g + '" stroke-width="1"/>'
               '<circle cx="322" cy="11" r="4.2" fill="#0c0b10"/></svg>')
    (ASSETS / "divider.svg").write_text(divider, encoding="utf-8")


def city_rules():
    """Город для рассказа: число абзацев (1..10+), есть ли курсив и жирный.
    40 сочетаний разбросаны по 55 городам шагом 7 (взаимно просто с 55)."""
    base = ".tavo-character-bubble-content"
    rules = ["/* ---------- Города (сгенерировано build.py) ---------- */"]
    for k in range(1, 11):
        paras = f":has(p:nth-of-type({k}))" + (f":not(:has(p:nth-of-type({k + 1})))" if k < 10 else "")
        for em in (0, 1):
            for strong in (0, 1):
                flags = (":has(:is(em, i))" if em else ":not(:has(:is(em, i)))") + \
                        (":has(:is(strong, b))" if strong else ":not(:has(:is(strong, b)))")
                idx = (k - 1) * 4 + em * 2 + strong
                city = CITIES[(idx * 7 + 1) % len(CITIES)]
                rules.append(f'{base}{paras}{flags}::before {{ content: "{city}"; }}')
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
        "name": "Invisible Cities",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {
            "charAvatar": False,
            "image": "theme/assets/scroll.jpg",
            "imageOpacity": 1,
            "color": argb("#090D24"),
        },
        # Марко — синий шёлк, Хубилай — чёрный лак с печатью
        "user_bubble": {"color": argb("#0C0B10", 0xE6), "blur": 0, "radius": 3, "alignment": "right"},
        "character_bubble": {"color": argb("#121A3A", 0xE6), "blur": 4, "radius": 3, "alignment": "left"},
        "user_bubble_font": font(argb("#E8DCCB"), argb("#D0907E"), argb("#FFFFFF")),
        "character_bubble_font": font(argb("#E6E1D3"), argb("#9FB3D1"), argb("#F1D79B")),
        "console": {
            "color": argb("#0C0B10", 0xF0),
            "blur": 8,
            "radius": 4,
            "sendColor": argb("#D4AF6A"),
            "fontSize": 17,
            "fontWeight": 400,
            "fontColor": argb("#E8DCCB"),
            "placeholderColor": argb("#7D7A8C"),
        },
        "thinking": {"fontSize": 14, "fontWeight": 400, "color": argb("#9FB3D1"), "backgroundColor": argb("#090D24", 0xCC)},
        "status_bar": {"fontSize": 13, "fontWeight": 500, "color": argb("#D4AF6A"), "backgroundColor": argb("#090D24", 0xE6)},
        "user_avatar": dict(avatar),
        "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar),
        "group_character_avatar": dict(avatar),
    }


def main():
    ASSETS.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_background()
    make_silk()
    make_svgs()

    css = (HERE / "style.css").read_text(encoding="utf-8")
    css = css.replace("CITY_RULES", city_rules())
    m = manifest(css)
    (HERE / "theme.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = DIST / "invisible-cities.thm"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "theme.json", "theme.json")
        for f in sorted(ASSETS.iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
