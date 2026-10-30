"""Сборка темы «The Library of Babel» для Tavo.

«Вселенная (которую другие называют Библиотекой) состоит из огромного,
возможно, бесконечного числа шестигранных галерей, с широкими вентиляционными
колодцами, огороженными невысокими перилами». — Х. Л. Борхес

Фон — взгляд вниз, в колодец: ярусы шестигранных галерей, по пять полок
на стену, лампы-«сферические плоды» в углах, тёплый свет в бесконечной глубине.

Запуск: python3 themes/library-of-babel/build.py
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

INK = (18, 13, 8)
GILT = (201, 166, 107)
LAMP = (255, 206, 140)
SPINES = [(112, 38, 30), (92, 58, 32), (78, 74, 44), (48, 62, 66), (150, 108, 52),
          (168, 146, 106), (40, 44, 70), (120, 84, 46), (66, 34, 40)]

# Борхес: двадцать две буквы, точка, запятая и пробел
ALPHABET = "abcdefghijlmnopqrstuvxz"[:22] + ".," + " "


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def hexagon(cx, cy, r):
    return [(cx + r * math.cos(math.pi / 3 * i), cy + r * math.sin(math.pi / 3 * i)) for i in range(6)]


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def shade(c, k, fog, glow=LAMP):
    """Цвет корешка с учётом глубины: светлее и туманнее к центру колодца."""
    base = [v * k for v in c]
    return tuple(int(base[i] + (glow[i] * 0.55 - base[i]) * fog) for i in range(3))


def make_background():
    w, h = 900, 1950
    cx, cy = w / 2, h * 0.5
    rng = random.Random(1941)  # год «Сада расходящихся тропок»
    img = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(img)

    r0, q = 1500.0, 0.8
    rings = []
    r = r0
    while r > 6:
        rings.append(r)
        r *= q
    n = len(rings)

    for k in range(n - 1):
        R, Rin = rings[k], rings[k + 1]
        depth = k / (n - 1)
        bright = 0.35 + 0.65 * depth
        fog = depth ** 2.2
        outer, inner = hexagon(cx, cy, R), hexagon(cx, cy, Rin)
        # стена яруса — тёмное дерево
        for i in range(6):
            A, B, a, b = outer[i], outer[(i + 1) % 6], inner[i], inner[(i + 1) % 6]
            d.polygon([A, B, b, a], fill=shade((22, 15, 9), bright, fog))
            # пять полок на стену, корешки книг на каждой
            for j in range(5):
                t0, t1 = 0.1 + j * 0.172, 0.1 + (j + 1) * 0.172 - 0.045
                u = 0.04
                while u < 0.96:
                    sw = rng.uniform(0.014, 0.03)
                    if u + sw > 0.96:
                        break
                    if rng.random() < 0.9:
                        top = t0 + rng.choice([0, 0, 0.01, 0.02, 0.03])
                        col = shade(rng.choice(SPINES), bright * rng.uniform(0.75, 1.1), fog)
                        p1 = lerp(lerp(A, B, u), lerp(a, b, u), top)
                        p2 = lerp(lerp(A, B, u + sw), lerp(a, b, u + sw), top)
                        p3 = lerp(lerp(A, B, u + sw), lerp(a, b, u + sw), t1)
                        p4 = lerp(lerp(A, B, u), lerp(a, b, u), t1)
                        d.polygon([p1, p2, p3, p4], fill=col)
                    u += sw + rng.uniform(0.0015, 0.003)
                # доска полки
                d.line([lerp(A, a, t1 + 0.02), lerp(B, b, t1 + 0.02)],
                       fill=shade((96, 66, 38), bright, fog), width=max(1, int(R * 0.01)))
        # перила по краю яруса: тёмная балка и золотистый поручень
        d.line(outer + [outer[0]], fill=shade((30, 20, 12), bright, fog), width=max(2, int(R * 0.03)))
        d.line(outer + [outer[0]], fill=shade(GILT, bright, fog), width=max(1, int(R * 0.007)))

    # лампы — «сферические плоды» в углах каждого яруса
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    dots = []
    for k in range(1, n - 1):
        R = rings[k]
        lr = max(1.2, R * 0.012)
        for x, y in hexagon(cx, cy, R * 0.97):
            gd.ellipse([x - lr * 3, y - lr * 3, x + lr * 3, y + lr * 3], fill=tuple(int(v * 0.45) for v in LAMP))
            dots.append((x, y, lr))
    glow = glow.filter(ImageFilter.GaussianBlur(12))
    img = Image.fromarray(np.clip(np.asarray(img, dtype=np.int32) + np.asarray(glow, dtype=np.int32), 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for x, y, lr in dots:
        d.ellipse([x - lr, y - lr, x + lr, y + lr], fill=(255, 236, 200))

    # свет из бесконечной глубины
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.hypot(xx - cx, yy - cy)
    arr = np.asarray(img, dtype=np.float64)
    core = np.exp(-(dist / 120) ** 2)[..., None]
    arr = arr * (1 - core * 0.6) + np.array(LAMP) * core * 0.85

    # виньетка, лёгкое затемнение (текст на полях должен читаться), зерно
    vign = np.clip(1.15 - (dist / (h * 0.62)) ** 1.6, 0.15, 1)
    arr *= (0.85 * vign)[..., None]
    arr += np.random.default_rng(3).normal(0, 4, (h, w))[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(ASSETS / "shaft.jpg", quality=88, optimize=True)


def make_paper():
    """Тайл старой бумаги 256×256: волокна, пятна, бесшовный."""
    s = 256
    nr = np.random.default_rng(7)
    big = nr.normal(0, 1, (s, s))
    tile = np.tile(big, (3, 3))
    blur = np.asarray(Image.fromarray(((tile + 4) * 30).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)), dtype=np.float64)[s:2 * s, s:2 * s]
    fine = nr.normal(0, 1, (s, s))
    base = np.array([239, 227, 200], dtype=np.float64)
    arr = base[None, None, :] * (1 + (blur - blur.mean()) / 255 * 0.5)[..., None] + (fine * 3)[..., None]
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    rng = random.Random(5)
    for _ in range(35):  # волокна
        x, y = rng.uniform(0, s), rng.uniform(0, s)
        a = rng.uniform(0, math.pi)
        ln = rng.uniform(6, 22)
        d.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], fill=(226, 212, 182), width=1)
    img.save(ASSETS / "paper.png", optimize=True)


def make_glyphs(name, seed, size, color):
    """Полоса случайных книг: строка из 25 символов Борхеса, бесшовная по X."""
    rng = random.Random(seed)
    text = "".join(rng.choice(ALPHABET) for _ in range(150)) + " "
    font = ImageFont.truetype(str(FONTS / "EBGaramond-Italic.ttf"), size)
    w = int(font.getlength(text))
    hgt = int(size * 1.5)
    img = Image.new("RGBA", (w, hgt), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((0, int(size * 0.1)), text, font=font, fill=color)
    img.save(ASSETS / name, optimize=True)
    return w, hgt


def hex_svg_path(cx, cy, r):
    pts = hexagon(cx, cy, r)
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"


def make_ornaments():
    """Векторные орнаменты: шестигранная виньетка и разделитель."""
    g = "#c9a66b"
    mark = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="60" height="24" viewBox="0 0 60 24">'
        f'<path d="M4,12 L22,12" stroke="{g}" stroke-width="0.8" stroke-linecap="round"/>'
        f'<path d="M38,12 L56,12" stroke="{g}" stroke-width="0.8" stroke-linecap="round"/>'
        f'<path d="{hex_svg_path(30, 12, 7)}" fill="none" stroke="{g}" stroke-width="1"/>'
        f'<path d="{hex_svg_path(30, 12, 3.2)}" fill="{g}"/>'
        f'<circle cx="2.5" cy="12" r="1.2" fill="{g}"/><circle cx="57.5" cy="12" r="1.2" fill="{g}"/>'
        "</svg>"
    )
    (ASSETS / "hex-mark.svg").write_text(mark, encoding="utf-8")
    # разделитель: тонкие линии, три шестигранника, точки-лампы
    parts = [
        f'<path d="M10,14 L250,14" stroke="url(#f)" stroke-width="0.8"/>',
        f'<path d="M390,14 L630,14" stroke="url(#f2)" stroke-width="0.8"/>',
    ]
    for x, r, filled in [(290, 6, False), (320, 9, False), (350, 6, False), (320, 4, True)]:
        parts.append(f'<path d="{hex_svg_path(x, 14, r)}" fill="{g if filled else "none"}" stroke="{g}" stroke-width="1"/>')
    for x in (268, 372):
        parts.append(f'<circle cx="{x}" cy="14" r="1.6" fill="#ffce8c"/>')
    divider = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="28" viewBox="0 0 640 28">'
        '<defs><linearGradient id="f" x1="0" x2="1"><stop offset="0" stop-color="#c9a66b" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#c9a66b" stop-opacity="0.9"/></linearGradient>'
        '<linearGradient id="f2" x1="0" x2="1"><stop offset="0" stop-color="#c9a66b" stop-opacity="0.9"/>'
        '<stop offset="1" stop-color="#c9a66b" stop-opacity="0"/></linearGradient></defs>'
        + "".join(parts) + "</svg>"
    )
    (ASSETS / "divider.svg").write_text(divider, encoding="utf-8")


def font(color, tone, quote, italic=False):
    def style(c, it=False, weight=400):
        return {"fontFamily": None, "fontSize": 17, "fontWeight": weight,
                "fontStyle": "italic" if it else "normal", "color": c}
    return {
        "textStyle": style(color, italic),
        "toneTextStyle": style(tone, True),
        "quoteTextStyle": style(quote, italic, 500),
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
        "name": "The Library of Babel",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {
            "charAvatar": False,
            "image": "theme/assets/shaft.jpg",
            "imageOpacity": 1,
            "color": argb("#120D08"),
        },
        # Персонаж — печатная страница, вы — пометки на полях
        "user_bubble": {"color": argb("#120D08", 0x99), "blur": 6, "radius": 2, "alignment": "right"},
        "character_bubble": {"color": argb("#EFE3C8"), "blur": 0, "radius": 2, "alignment": "left"},
        "user_bubble_font": font(argb("#E8D9B8"), argb("#C9A66B"), argb("#F6EBD2"), italic=True),
        "character_bubble_font": font(argb("#2A1F14"), argb("#6B5A44"), argb("#1A1209")),
        "console": {
            "color": argb("#1E150D", 0xF0),
            "blur": 10,
            "radius": 6,
            "sendColor": argb("#C9A66B"),
            "fontSize": 17,
            "fontWeight": 400,
            "fontColor": argb("#E8D9B8"),
            "placeholderColor": argb("#8A7656"),
        },
        "thinking": {"fontSize": 14, "fontWeight": 400, "color": argb("#B9A27A"), "backgroundColor": argb("#120D08", 0xCC)},
        "status_bar": {"fontSize": 13, "fontWeight": 500, "color": argb("#C9A66B"), "backgroundColor": argb("#120D08", 0xE6)},
        "user_avatar": dict(avatar),
        "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar),
        "group_character_avatar": dict(avatar),
    }


def main():
    ASSETS.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_background()
    make_paper()
    make_ornaments()
    w1, h1 = make_glyphs("glyphs-a.png", 410, 30, (201, 166, 107, 150))
    w2, h2 = make_glyphs("glyphs-b.png", 80, 27, (232, 217, 184, 95))

    # Ширины полос нужны CSS для бесшовной прокрутки; в CSS они выводятся в 1/3 размера
    css = (HERE / "style.css").read_text(encoding="utf-8")
    css = (css.replace("GLYPHS_A_W", str(w1 // 3)).replace("GLYPHS_A_H", str(h1 // 3))
              .replace("GLYPHS_B_W", str(w2 // 3)).replace("GLYPHS_B_H", str(h2 // 3)))
    m = manifest(css)
    (HERE / "theme.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = DIST / "library-of-babel.thm"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "theme.json", "theme.json")
        for f in sorted(ASSETS.iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
