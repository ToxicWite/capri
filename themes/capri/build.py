"""Сборка темы «Capri» для Tavo: генерирует ассеты, theme.json и capri.thm.

Запуск: python3 themes/capri/build.py
"""
import json
import math
import random
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
DIST = HERE.parent.parent / "dist"

# Палитра Капри
BLACK = (9, 7, 14)
RED = (255, 22, 68)
RED_DARK = (178, 10, 44)
GREEN = (43, 255, 106)
BLUE = (22, 76, 255)
VIOLET = (124, 58, 255)
INDIGO = (26, 18, 92)
ORANGE = (255, 154, 26)
WHITE = (255, 255, 255)


def argb(hex_rgb, alpha=0xFF):
    """'#RRGGBB' -> десятичное 0xAARRGGBB для theme.json."""
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def speckle(draw, w, h, n, color, rng, rmax=2.2, wrap=False):
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.choice([0.6, 0.8, 1.0, 1.2, 1.6, rmax])
        a = rng.randint(120, 255)
        c = color + (a,)
        offsets = [(0, 0)]
        if wrap:
            offsets = [(dx, dy) for dx in (-w, 0, w) for dy in (-h, 0, h)]
        for dx, dy in offsets:
            draw.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=c)


def shard(rng, cx, cy, length, angle, width):
    """Зазубренный осколок-луч, как силуэт Капри."""
    pts = [(cx, cy)]
    steps = rng.randint(3, 5)
    for i in range(1, steps + 1):
        t = i / steps
        a = angle + rng.uniform(-0.12, 0.12)
        d = length * t
        side = width * (1 - t) * rng.uniform(0.6, 1.3)
        px = cx + math.cos(a) * d + math.cos(a + math.pi / 2) * side
        py = cy + math.sin(a) * d + math.sin(a + math.pi / 2) * side
        pts.append((px, py))
    tip = (cx + math.cos(angle) * length * 1.08, cy + math.sin(angle) * length * 1.08)
    pts.append(tip)
    for i in range(steps, 0, -1):
        t = i / steps
        a = angle + rng.uniform(-0.12, 0.12)
        d = length * t * rng.uniform(0.8, 1.0)
        side = width * (1 - t) * rng.uniform(0.6, 1.3)
        px = cx + math.cos(a) * d - math.cos(a + math.pi / 2) * side
        py = cy + math.sin(a) * d - math.sin(a + math.pi / 2) * side
        pts.append((px, py))
    return pts


def make_background():
    w, h = 900, 1950
    rng = random.Random(77)
    img = Image.new("RGBA", (w, h), BLACK + (255,))
    px = img.load()
    # Ночное небо: чёрный сверху -> индиго -> фиолетовый к низу
    for y in range(h):
        t = y / h
        if t < 0.55:
            k = t / 0.55
            c = tuple(int(BLACK[i] + (INDIGO[i] - BLACK[i]) * k * 0.7) for i in range(3))
        else:
            k = (t - 0.55) / 0.45
            base = tuple(int(BLACK[i] + (INDIGO[i] - BLACK[i]) * 0.7) for i in range(3))
            c = tuple(int(base[i] + (VIOLET[i] * 0.55 - base[i]) * k) for i in range(3))
        for x in range(w):
            px[x, y] = c + (255,)

    # Красное «звёздное» облако-осколки сверху (фирменный глиттер Капри)
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    shards = []
    for _ in range(16):
        cx = rng.uniform(-100, w + 100)
        cy = rng.uniform(-200, 120)
        ang = rng.uniform(math.pi * 0.25, math.pi * 0.75)
        shards.append(shard(rng, cx, cy, rng.uniform(380, 820), ang, rng.uniform(50, 120)))
    # фиолетовая «сдвинутая» обводка
    for s in shards:
        d.polygon([(x + 9, y + 7) for x, y in s], fill=VIOLET + (230,))
    for s in shards:
        d.polygon(s, fill=RED + (255,))
    mask = layer.split()[3]
    glitter = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    speckle(ImageDraw.Draw(glitter), w, h, 5200, WHITE, rng)
    gl_mask = Image.composite(glitter, Image.new("RGBA", (w, h), (0, 0, 0, 0)), mask)
    layer = Image.alpha_composite(layer, gl_mask)
    # Чёрные осколки поверх
    d = ImageDraw.Draw(layer)
    for _ in range(9):
        cx = rng.uniform(0, w)
        cy = rng.uniform(-80, 60)
        ang = rng.uniform(math.pi * 0.3, math.pi * 0.7)
        d.polygon(shard(rng, cx, cy, rng.uniform(200, 460), ang, rng.uniform(16, 40)), fill=BLACK + (255,))
    # Зелёные «вспышки»
    for _ in range(5):
        x0 = rng.uniform(0, w)
        y0 = rng.uniform(80, 520)
        ww, hh = rng.uniform(30, 90), rng.uniform(60, 200)
        poly = [(x0, y0), (x0 + ww, y0 + 14), (x0 + ww * 0.8, y0 + hh), (x0 - 10, y0 + hh * 0.9)]
        d.polygon([(x + 6, y + 6) for x, y in poly], fill=VIOLET + (220,))
        d.polygon(poly, fill=GREEN + (255,))
    img = Image.alpha_composite(img, layer)

    # Звёзды/пыль по всему небу
    stars = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    speckle(ImageDraw.Draw(stars), w, h, 900, WHITE, rng, rmax=1.6)
    img = Image.alpha_composite(img, stars)

    # Силуэт ночного города внизу
    city = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(city)
    x = -20
    while x < w:
        bw = rng.randint(50, 150)
        bh = rng.randint(220, 640)
        top = h - bh
        d.rectangle([x, top, x + bw, h], fill=(6, 4, 14, 255))
        if rng.random() < 0.4:
            d.rectangle([x + bw // 2 - 2, top - rng.randint(40, 120), x + bw // 2 + 2, top], fill=(6, 4, 14, 255))
        for wy in range(top + 18, h - 10, 26):
            for wx in range(x + 10, x + bw - 12, 20):
                if rng.random() < 0.22:
                    col = rng.choice([VIOLET, VIOLET, (200, 90, 255), RED, GREEN])
                    d.rectangle([wx, wy, wx + 9, wy + 4], fill=col + (200,))
        x += bw + rng.randint(-10, 18)
    img = Image.alpha_composite(img, city)

    # Оранжевые языки пламени у самого низа
    fire = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(fire)
    for _ in range(14):
        cx = rng.uniform(0, w)
        poly = shard(rng, cx, h + 40, rng.uniform(140, 300), -math.pi / 2 + rng.uniform(-0.35, 0.35), rng.uniform(18, 34))
        d.polygon([(x + 5, y + 4) for x, y in poly], fill=RED + (230,))
        d.polygon(poly, fill=ORANGE + (255,))
    img = Image.alpha_composite(img, fire)

    # Затемняем середину, чтобы читались сообщения
    veil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vp = veil.load()
    for y in range(h):
        t = y / h
        a = int(150 * math.exp(-((t - 0.5) ** 2) / 0.06))
        for xx in range(w):
            vp[xx, y] = BLACK + (a,)
    img = Image.alpha_composite(img, veil)
    img.convert("RGB").save(ASSETS / "capri-night.png", optimize=True)


def make_tile(name, base, dot, n, seed, alpha=255):
    s = 256
    rng = random.Random(seed)
    img = Image.new("RGBA", (s, s), base + (alpha,))
    speckle(ImageDraw.Draw(img), s, s, n, dot, rng, rmax=1.8, wrap=True)
    img.save(ASSETS / name, optimize=True)


def make_teeth():
    """Зубастая ухмылка Капри: неровный белый зигзаг, как у неё на лице."""
    w, h = 120, 20
    k = 4
    big = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    ys = [30, 58, 24, 66, 20, 62, 28, 54, 22, 60, 34]
    pts = [(int(i * (w * k - 16) / (len(ys) - 1)) + 8, y) for i, y in enumerate(ys)]
    d.line([(x + 6, y + 6) for x, y in pts], fill=VIOLET + (255,), width=11, joint="curve")
    d.line(pts, fill=WHITE + (255,), width=11, joint="curve")
    big.resize((w, h), Image.LANCZOS).save(ASSETS / "teeth.png", optimize=True)


def make_eye():
    """Глаз Капри: зелёный зазубренный блок, чёрный ромб, синий зрачок."""
    s = 256
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    green = [(20, 40), (236, 14), (244, 226), (30, 240), (52, 140)]
    d.polygon([(x + 10, y + 8) for x, y in green], fill=VIOLET + (255,))
    d.polygon(green, fill=GREEN + (255,))
    d.polygon([(40, 128), (128, 52), (220, 128), (128, 206)], fill=BLACK + (255,))
    d.ellipse([72, 72, 184, 184], outline=GREEN + (255,), width=10)
    d.ellipse([92, 92, 164, 164], fill=BLUE + (255,))
    d.ellipse([114, 112, 140, 138], fill=WHITE + (255,))
    img.resize((64, 64), Image.LANCZOS).save(ASSETS / "eye.png", optimize=True)


def font(color, tone_color, quote_color):
    def style(c, italic=False, weight=400):
        return {"fontFamily": None, "fontSize": 16, "fontWeight": weight,
                "fontStyle": "italic" if italic else "normal", "color": c}
    return {
        "textStyle": style(color),
        "toneTextStyle": style(tone_color, italic=True, weight=500),
        "quoteTextStyle": style(quote_color, weight=600),
        "toneHighlight": True,
        "toneDelimiters": ["**", "()", "（）"],
        "toneSymbol": "none",
        "quoteHighlight": True,
        "quoteDelimiters": ["“”", "「」", "\"\"", "«»"],
        "quoteSymbol": "\"\"",
    }


def build_manifest():
    css = (HERE / "style.css").read_text(encoding="utf-8")
    avatar = {"avatar": True, "radius": 0, "name": True}
    return {
        "spec": "tavo_theme_v1",
        "name": "Capri // Project Capricorn",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {
            "charAvatar": False,
            "image": "theme/assets/capri-night.png",
            "imageOpacity": 1,
            "color": argb("#09070E"),
        },
        # Базовые цвета — запасной вариант без Advanced Rendering
        "user_bubble": {"color": argb("#B20A2C", 0xF2), "blur": 0, "radius": 6, "alignment": "right"},
        "character_bubble": {"color": argb("#09070E", 0xEB), "blur": 8, "radius": 6, "alignment": "left"},
        "user_bubble_font": font(argb("#FFF4F6"), argb("#FFD24A"), argb("#FFFFFF")),
        "character_bubble_font": font(argb("#E9E6FF"), argb("#B48CFF"), argb("#2BFF6A")),
        "console": {
            "color": argb("#09070E", 0xF0),
            "blur": 12,
            "radius": 4,
            "sendColor": argb("#2BFF6A"),
            "fontSize": 16,
            "fontWeight": 500,
            "fontColor": argb("#E9E6FF"),
            "placeholderColor": argb("#7C6BB0"),
        },
        "thinking": {"fontSize": 14, "fontWeight": 500, "color": argb("#2BFF6A"), "backgroundColor": argb("#09070E", 0xE6)},
        "status_bar": {"fontSize": 13, "fontWeight": 600, "color": argb("#2BFF6A"), "backgroundColor": argb("#09070E", 0xE6)},
        "user_avatar": dict(avatar),
        "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar),
        "group_character_avatar": dict(avatar),
    }


def main():
    ASSETS.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_background()
    make_tile("glitter-red.png", RED_DARK, WHITE, 70, seed=3)
    make_tile("static-black.png", BLACK, VIOLET, 14, seed=5, alpha=235)
    make_teeth()
    make_eye()

    manifest = build_manifest()
    (HERE / "theme.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    out = DIST / "capri.thm"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "theme.json", "theme.json")
        for f in sorted(ASSETS.iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
