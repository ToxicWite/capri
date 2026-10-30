"""Сборка темы «Spores» (The Last of Us Part I) для Tavo.

Заражённый подвал: оливково-серый бетон, рыжие наросты кордицепса,
холодный луч фонарика, в котором висят споры.

Запуск: python3 themes/tlou-spores/build.py
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

WALL = (38, 42, 34)
FUNGUS = (168, 82, 30)
FUNGUS_LIGHT = (226, 146, 70)
FUNGUS_DARK = (52, 24, 10)
SPORE = (214, 186, 110)
BEAM = (226, 232, 220)
FIREFLY = (222, 244, 128)


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def cordyceps(d, rng, cx, cy, spread, n):
    """Колония кордицепса: паутина отростков и бугристые «шляпки»."""
    for _ in range(n // 2):
        a = rng.uniform(0, math.tau)
        length = rng.uniform(spread * 0.6, spread * 1.6)
        x, y = cx, cy
        for _ in range(6):
            nx = x + math.cos(a) * length / 6
            ny = y + math.sin(a) * length / 6
            d.line([(x, y), (nx, ny)], fill=FUNGUS_DARK + (200,), width=rng.randint(1, 3))
            x, y, a = nx, ny, a + rng.uniform(-0.5, 0.5)
    for _ in range(n):
        x = cx + rng.gauss(0, spread / 3.4)
        y = cy + rng.gauss(0, spread / 4.0)
        k = max(0.35, 1 - math.hypot(x - cx, y - cy) / spread)
        r = rng.uniform(7, 22) * k
        d.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=FUNGUS_DARK + (255,))
        d.ellipse([x - r * 0.85, y - r * 0.75, x + r * 0.7, y + r * 0.35], fill=FUNGUS + (255,))
        d.ellipse([x - r * 0.5, y - r * 0.6, x + r * 0.1, y - r * 0.1], fill=FUNGUS_LIGHT + (200,))


def make_background():
    w, h = 900, 1950
    rng = random.Random(31)
    nr = np.random.default_rng(31)

    # Бетонная стена: пятна сырости и подтёки
    base = np.ones((h, w, 3)) * np.array(WALL)
    stains = nr.normal(0, 1, (h // 30 + 1, w // 30 + 1))
    stains = np.asarray(Image.fromarray(((stains + 3) * 40).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255
    base *= (0.7 + 0.5 * stains)[..., None]
    for _ in range(40):
        x = rng.uniform(0, w)
        y0 = rng.uniform(0, h * 0.6)
        ln = rng.uniform(100, 600)
        ww = rng.uniform(4, 16)
        xs = slice(int(max(0, x - ww)), int(min(w, x + ww)))
        base[int(y0):int(min(h, y0 + ln)), xs] *= 0.82
    img = Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)

    # Дверной проём и пол
    d.rectangle([150, 380, 420, 1300], fill=(10, 11, 9, 255))
    d.rectangle([150, 380, 420, 396], fill=(60, 64, 54, 255))
    d.rectangle([0, 1420, w, h], fill=(26, 28, 23, 255))
    for i in range(14):
        y = 1420 + int(530 * (i / 14) ** 1.6)
        d.line([(0, y), (w, y)], fill=(18, 20, 16, 255), width=2)

    # Колонии кордицепса
    fungus = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fungus)
    for cx, cy, sp, n in [(840, 260, 200, 220), (40, 1520, 230, 260), (420, 390, 110, 90), (790, 1400, 150, 140), (90, 110, 110, 90)]:
        cordyceps(fd, rng, cx, cy, sp, n)
    img = Image.alpha_composite(img, fungus)

    # Луч фонарика снизу справа вверх-влево
    beam = Image.new("L", (w, h), 0)
    bd = ImageDraw.Draw(beam)
    bd.polygon([(780, 1950), (900, 1880), (260, 520), (40, 760)], fill=110)
    beam = beam.filter(ImageFilter.GaussianBlur(70))
    img = Image.composite(Image.new("RGBA", (w, h), BEAM + (255,)), img, beam.point(lambda v: int(v * 0.8)))

    # Споры: густо в луче, редко вне его
    spores = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(spores)
    bpx = beam.load()
    for _ in range(9000):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        inside = bpx[int(x), int(y)] / 110
        if rng.random() > 0.08 + inside * 0.9:
            continue
        r = rng.choice([0.7, 1.0, 1.3, 1.8, 2.4])
        sd.ellipse([x - r, y - r, x + r, y + r], fill=SPORE + (int(60 + 180 * inside),))
    spores = Image.alpha_composite(spores.filter(ImageFilter.GaussianBlur(1.2)), spores)
    img = Image.alpha_composite(img, spores)

    # Зерно, затемнение середины и виньетка
    arr = np.asarray(img.convert("RGB"), dtype=np.float64)
    arr += nr.normal(0, 4, arr.shape[:2])[..., None]
    yy, xx = np.mgrid[0:h, 0:w]
    vign = np.clip(1.25 - np.hypot((xx / w - 0.5) * 1.5, (yy / h - 0.5) * 1.1), 0, 1) ** 1.4
    veil = 1 - 0.25 * np.exp(-((yy / h - 0.5) ** 2) / 0.05)
    arr *= (vign * veil)[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(ASSETS / "spore-room.png", optimize=True)


def make_spore_tile():
    """Тайл 160×160 с парящими спорами для пузырей персонажа."""
    s = 160
    rng = random.Random(9)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(26):
        x, y = rng.uniform(0, s), rng.uniform(0, s)
        r = rng.choice([0.8, 1.1, 1.5, 2.0])
        for dx in (-s, 0, s):
            for dy in (-s, 0, s):
                d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=SPORE + (rng.randint(70, 160),))
    img.filter(ImageFilter.GaussianBlur(0.6)).save(ASSETS / "spores.png", optimize=True)


def make_fungus_corner():
    """Нарост кордицепса, растущий из правого нижнего угла сообщения."""
    w, h = 220, 140
    rng = random.Random(4)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cordyceps(d, rng, w - 20, h - 10, 70, 40)
    img.resize((w // 2, h // 2), Image.LANCZOS).save(ASSETS / "cordyceps.png", optimize=True)


def make_fireflies():
    """Четыре кадра светлячков для полосы над полем ввода."""
    w, h = 720, 72
    rng = random.Random(17)
    flies = [(rng.uniform(30, w - 30), rng.uniform(26, h - 26)) for _ in range(7)]
    for f in range(4):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d, gd = ImageDraw.Draw(img), ImageDraw.Draw(glow)
        for i, (x, y) in enumerate(flies):
            on = (i + f) % 3 != 0
            x += math.sin(f * 1.6 + i) * 6
            y += math.cos(f * 1.3 + i * 2) * 4
            a = 255 if on else 60
            gd.ellipse([x - 13, y - 13, x + 13, y + 13], fill=FIREFLY + (a // 2,))
            d.ellipse([x - 3.4, y - 3.4, x + 3.4, y + 3.4], fill=FIREFLY + (a,))
        glow = glow.filter(ImageFilter.GaussianBlur(6))
        Image.alpha_composite(glow, img).resize((w // 2, h // 2), Image.LANCZOS).save(ASSETS / f"fireflies-{f}.png", optimize=True)


def font(color, tone, quote):
    def style(c, italic=False, weight=400):
        return {"fontFamily": None, "fontSize": 16, "fontWeight": weight,
                "fontStyle": "italic" if italic else "normal", "color": c}
    return {
        "textStyle": style(color),
        "toneTextStyle": style(tone, italic=True),
        "quoteTextStyle": style(quote, weight=500),
        "toneHighlight": True,
        "toneDelimiters": ["**", "()", "（）"],
        "toneSymbol": "none",
        "quoteHighlight": True,
        "quoteDelimiters": ["“”", "「」", "\"\"", "«»"],
        "quoteSymbol": "\"\"",
    }


def manifest(css):
    avatar = {"avatar": True, "radius": 4, "name": True}
    return {
        "spec": "tavo_theme_v1",
        "name": "TLOU // Spores",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {
            "charAvatar": False,
            "image": "theme/assets/spore-room.png",
            "imageOpacity": 1,
            "color": argb("#0B0D0A"),
        },
        "user_bubble": {"color": argb("#1C2018", 0xF0), "blur": 0, "radius": 4, "alignment": "right"},
        "character_bubble": {"color": argb("#0B0D0A", 0xEB), "blur": 4, "radius": 4, "alignment": "left"},
        "user_bubble_font": font(argb("#E6DCC6"), argb("#A69C84"), argb("#FFFFFF")),
        "character_bubble_font": font(argb("#D8D4C4"), argb("#9C9A86"), argb("#F0D79A")),
        "console": {
            "color": argb("#141612", 0xF2),
            "blur": 8,
            "radius": 26,
            "sendColor": argb("#D6BA6E"),
            "fontSize": 16,
            "fontWeight": 400,
            "fontColor": argb("#E6DCC6"),
            "placeholderColor": argb("#7A7A68"),
        },
        "thinking": {"fontSize": 14, "fontWeight": 400, "color": argb("#B9B39C"), "backgroundColor": argb("#0B0D0A", 0xE6)},
        "status_bar": {"fontSize": 13, "fontWeight": 500, "color": argb("#D6BA6E"), "backgroundColor": argb("#0B0D0A", 0xE6)},
        "user_avatar": dict(avatar),
        "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar),
        "group_character_avatar": dict(avatar),
    }


def main():
    ASSETS.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_background()
    make_spore_tile()
    make_fungus_corner()
    make_fireflies()

    m = manifest((HERE / "style.css").read_text(encoding="utf-8"))
    (HERE / "theme.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = DIST / "tlou-spores.thm"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "theme.json", "theme.json")
        for f in sorted(ASSETS.iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
