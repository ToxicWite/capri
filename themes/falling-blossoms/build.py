"""Сборка темы «花落 · Falling Blossoms» для Tavo — мягкий старый Китай.

Свиток: сверху и снизу тёмная парча с орнаментом хуэйвэнь, между ними
рисовая бумага с веткой цветущей сливы, строками Мэн Хаожаня
«夜来风雨声，花落知多少» («ночью шумели ветер и дождь — сколько цветов
опало?») с печатью «春晓», облаками сянъюнь и красным солнцем.

Иероглифы заранее отрисованы шрифтом Ma Shan Zheng (SIL OFL 1.1) в
src/poem.png и src/seal-chars.png, чтобы не возить в репозитории шрифт на 6 МБ.

Запуск: python3 themes/falling-blossoms/build.py
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
SRC = HERE / "src"
DIST = HERE.parent.parent / "dist"

W, H = 900, 1950
TOP, BOTTOM = 250, 1700
PAPER = (242, 232, 213)
INK = (43, 33, 24)
VERMILION = (200, 53, 43)
BROCADE = (31, 36, 51)
GOLD = (196, 164, 108)


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def huiwen_tile(size=48, color=(196, 164, 108, 40)):
    """Тайл орнамента 回: квадратная спираль."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s, w = size, 3
    pts = [(4, 4), (s - 4, 4), (s - 4, s - 4), (10, s - 4), (10, 10), (s - 10, 10), (s - 10, s - 10), (16, s - 10),
           (16, 16), (s - 16, 16), (s - 16, s - 16), (22, s - 16)]
    d.line(pts, fill=color, width=w)
    return img


def paper_texture(w, h, seed, base=PAPER):
    nr = np.random.default_rng(seed)
    blot = nr.normal(0, 1, (h // 40 + 2, w // 40 + 2))
    blot = np.asarray(Image.fromarray(((blot + 3) * 40).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), dtype=np.float64)
    arr = np.array(base, dtype=np.float64)[None, None, :] * (1 + (blot - blot.mean()) / 255 * 0.06)[..., None]
    arr += nr.normal(0, 2.5, (h, w))[..., None]
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for _ in range(int(w * h / 900)):  # волокна рисовой бумаги
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, math.pi)
        ln = rng.uniform(4, 18)
        d.line([(x, y), (x + math.cos(a) * ln, y + math.sin(a) * ln)], fill=(226, 214, 190, 120), width=1)
    return img


def blossom(d, x, y, r, rng, open_=True):
    """Цветок сливы: пять лепестков, светлая серединка, тычинки."""
    if not open_:
        d.ellipse([x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45], fill=VERMILION + (255,))
        return
    rot = rng.uniform(0, math.tau)
    for k in range(5):
        a = rot + k * math.tau / 5
        px, py = x + math.cos(a) * r * 0.55, y + math.sin(a) * r * 0.55
        shade = rng.randint(-15, 15)
        col = (min(255, VERMILION[0] + 20 + shade), VERMILION[1] + 10 + shade, VERMILION[2] + 10 + shade, 255)
        d.ellipse([px - r * 0.5, py - r * 0.5, px + r * 0.5, py + r * 0.5], fill=col)
    d.ellipse([x - r * 0.3, y - r * 0.3, x + r * 0.3, y + r * 0.3], fill=(236, 170, 150, 255))
    for k in range(9):
        a = rng.uniform(0, math.tau)
        ex, ey = x + math.cos(a) * r * 0.5, y + math.sin(a) * r * 0.5
        d.line([(x, y), (ex, ey)], fill=(250, 236, 220, 255), width=1)
        d.ellipse([ex - 1.3, ey - 1.3, ex + 1.3, ey + 1.3], fill=(214, 168, 70, 255))


def branch(d, flowers, rng, x, y, angle, length, width, depth):
    """Ветка сливы: изломанная, сужающаяся, с отростками."""
    segs = rng.randint(3, 5)
    for _ in range(segs):
        nx = x + math.cos(angle) * length / segs
        ny = y + math.sin(angle) * length / segs
        for off in (-0.6, 0, 0.6):  # «сухая кисть»: несколько проходов
            d.line([(x + off, y), (nx + off, ny)], fill=(38, 28, 22, 235), width=max(1, int(width)))
        if depth < 3 and rng.random() < 0.45:
            branch(d, flowers, rng, nx, ny, angle + rng.choice([-1, 1]) * rng.uniform(0.5, 1.0),
                   length * 0.5, width * 0.6, depth + 1)
        if width < 7 and rng.random() < 0.55:
            flowers.append((nx + rng.uniform(-8, 8), ny + rng.uniform(-8, 8)))
        x, y = nx, ny
        angle += rng.uniform(-0.35, 0.35)
        width *= 0.82
    flowers.append((x, y))


def cloud(d, x, y, scale, rng):
    """Облако сянъюнь: лопасти с завитками, красный контур, тонкий хвост."""
    lobes = [(0, 0, 1.0), (-1.1, 0.15, 0.75), (1.0, 0.2, 0.7), (0.3, -0.45, 0.65), (-0.5, -0.35, 0.55)]
    r0 = 34 * scale
    for fill, grow in ((VERMILION + (255,), 3.5), ((246, 238, 222, 255), 0)):
        for lx, ly, lr in lobes:
            cx, cy, r = x + lx * r0 * 1.3, y + ly * r0, lr * r0 + grow
            d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=fill)
        d.rectangle([x - r0 * 2.2 - grow, y, x + r0 * 2.1 + grow, y + r0 * 0.55 + grow], fill=fill)
    for lx, ly, lr in lobes[:3]:  # завитки
        cx, cy, r = x + lx * r0 * 1.3, y + ly * r0, lr * r0 * 0.55
        for k in range(3):
            rr = r * (1 - k * 0.3)
            d.arc([cx - rr, cy - rr * 0.8, cx + rr, cy + rr * 0.8], 200 + k * 40, 520 - k * 30, fill=VERMILION + (255,), width=2)
    # хвост
    pts = []
    tx, ty = x + r0 * 2.1, y + r0 * 0.5
    for i in range(40):
        pts.append((tx + i * 9 * scale, ty + math.sin(i / 6 + rng.uniform(0, 0.2)) * 10 * scale))
    d.line(pts, fill=VERMILION + (255,), width=max(2, int(3 * scale)))


def make_background():
    rng = random.Random(689)  # год рождения Мэн Хаожаня
    img = paper_texture(W, H, 11)
    d = ImageDraw.Draw(img)

    # Ветка сливы, свисающая из-под верхней парчи справа
    flowers = []
    branch(d, flowers, rng, 930, TOP + 20, math.radians(150), 580, 17, 0)
    branch(d, flowers, rng, 880, TOP + 5, math.radians(112), 420, 10, 1)
    branch(d, flowers, rng, 760, TOP + 5, math.radians(160), 170, 7, 2)
    for i, (fx, fy) in enumerate(flowers):
        blossom(d, fx, fy, rng.uniform(13, 21), rng, open_=rng.random() > 0.25)

    # Опадающие лепестки
    for _ in range(40):
        px, py = rng.uniform(80, W - 40), rng.uniform(TOP + 200, BOTTOM - 260)
        pr = rng.uniform(4, 8)
        petal = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
        ImageDraw.Draw(petal).ellipse([20 - pr, 20 - pr * 0.6, 20 + pr, 20 + pr * 0.6], fill=VERMILION + (rng.randint(110, 190),))
        petal = petal.rotate(rng.uniform(0, 180))
        img.alpha_composite(petal, (int(px) - 20, int(py) - 20))

    # Стихи и печать (слева сверху)
    poem = Image.open(SRC / "poem.png").convert("L")
    ink = Image.new("RGBA", poem.size, INK + (0,))
    ink.putalpha(poem.point(lambda v: int(v * 0.85)))
    img.alpha_composite(ink, (60, TOP + 60))
    seal_chars = Image.open(SRC / "seal-chars.png").convert("L")
    seal = Image.new("RGBA", (56, 92), VERMILION + (235,))
    sd = ImageDraw.Draw(seal)
    sd.rectangle([3, 3, 52, 88], outline=(250, 236, 220, 255), width=2)
    white = Image.new("RGBA", seal_chars.size, (250, 236, 220, 255))
    white.putalpha(seal_chars)
    seal.alpha_composite(white, (6, 6))
    img.alpha_composite(seal, (78, TOP + 60 + poem.size[1] + 18))

    # Красное солнце с «пятнистым» краем и облака сянъюнь
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdw = ImageDraw.Draw(sun)
    sx, sy, sr = 250, 1395, 72
    sdw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=VERMILION + (255,))
    for _ in range(900):
        a, rr = rng.uniform(0, math.tau), sr + abs(rng.gauss(0, 6))
        sdw.point((sx + math.cos(a) * rr, sy + math.sin(a) * rr), fill=VERMILION + (rng.randint(80, 220),))
    img = Image.alpha_composite(img, sun)
    d = ImageDraw.Draw(img)
    cloud(d, 300, 1450, 1.0, rng)
    cloud(d, 640, 1300, 0.75, rng)
    cloud(d, 120, 1560, 0.6, rng)

    # Волны сэйгайха у нижнего края бумаги
    waves = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(waves)
    R = 30
    for row, y in enumerate(range(BOTTOM - 70, BOTTOM + R, R // 2)):
        for x in range(-R + (R if row % 2 else 0), W + R, R * 2):
            for k in range(4):
                rr = R - k * 7
                wd.ellipse([x - rr, y - rr, x + rr, y + rr], outline=VERMILION + (70,), width=2)
    img = Image.alpha_composite(img, waves)

    # Парча сверху и снизу, с орнаментом 回 и тонкими кантами
    tile = huiwen_tile()
    for y0, y1 in ((0, TOP), (BOTTOM, H)):
        band = Image.new("RGBA", (W, y1 - y0), BROCADE + (255,))
        for ty in range(0, y1 - y0, 48):
            for tx in range(0, W, 48):
                band.alpha_composite(tile, (tx, ty))
        img.alpha_composite(band, (0, y0))
        d = ImageDraw.Draw(img)
        edge = y1 if y0 == 0 else y0
        d.line([(0, edge), (W, edge)], fill=GOLD + (255,), width=3)
        inner = edge + (10 if y0 == 0 else -10)
        d.line([(0, inner), (W, inner)], fill=VERMILION + (255,), width=2)

    img.convert("RGB").save(ASSETS / "scroll.jpg", quality=90, optimize=True)


def make_paper_tile():
    paper_texture(256, 256, 3, base=(251, 246, 234)).save(ASSETS / "paper.png", optimize=True)


def make_petals():
    """Бесшовный тайл парящих лепестков для страниц персонажа."""
    s = 220
    rng = random.Random(8)
    full = Image.new("RGBA", (s * 3, s * 3), (0, 0, 0, 0))
    for _ in range(7):
        x, y = rng.uniform(0, s), rng.uniform(0, s)
        pr = rng.uniform(3.5, 6)
        petal = Image.new("RGBA", (30, 30), (0, 0, 0, 0))
        ImageDraw.Draw(petal).ellipse([15 - pr, 15 - pr * 0.55, 15 + pr, 15 + pr * 0.55], fill=VERMILION + (rng.randint(60, 110),))
        petal = petal.rotate(rng.uniform(0, 180))
        for dx in range(3):  # копии во все соседние клетки, чтобы края совпали
            for dy in range(3):
                full.alpha_composite(petal, (int(x) + dx * s - 15 + 15, int(y) + dy * s - 15 + 15))
    full.crop((s, s, 2 * s, 2 * s)).save(ASSETS / "petals.png", optimize=True)


def make_brush():
    """Мазок тушью сухой кистью для «письма» в поле ввода."""
    w, h = 1200, 80
    rng = random.Random(4)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k in range(26):  # волоски кисти
        y0 = 40 + rng.gauss(0, 7)
        pts = []
        for i in range(0, w + 1, 20):
            t = i / w
            pts.append((i, y0 + math.sin(t * 3.2 + k * 0.2) * 8 - t * 6))
        alpha = rng.randint(40, 120)
        width = rng.randint(2, 5)
        # сухая кисть: штрих рвётся
        seg = []
        for p in pts:
            if rng.random() < 0.12 and len(seg) > 1:
                d.line(seg, fill=INK + (alpha,), width=width)
                seg = []
            seg.append(p)
        if len(seg) > 1:
            d.line(seg, fill=INK + (alpha,), width=width)
    img.filter(ImageFilter.GaussianBlur(0.6)).save(ASSETS / "brush.png", optimize=True)


def make_svgs():
    v = "#c8352b"
    # уголок хуэйвэнь (левый верхний; правый нижний — поворот)
    corner = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40">'
              '<g transform="{t}" fill="none" stroke="' + v + '" stroke-width="2.4" stroke-linecap="square">'
              '<path d="M2,38 L2,2 L38,2"/><path d="M8,30 L8,8 L30,8"/>'
              '<path d="M8,20 L16,20 L16,14 L12,14"/><path d="M20,8 L20,16 L14,16"/></g></svg>')
    (ASSETS / "corner-tl.svg").write_text(corner.replace("{t}", ""), encoding="utf-8")
    (ASSETS / "corner-br.svg").write_text(corner.replace("{t}", "rotate(180 20 20)"), encoding="utf-8")
    # разделитель: облачный завиток между тонкими линиями
    divider = ('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="32" viewBox="0 0 640 32">'
               '<defs><linearGradient id="a" x1="0" x2="1"><stop offset="0" stop-color="' + v + '" stop-opacity="0"/>'
               '<stop offset="1" stop-color="' + v + '" stop-opacity="0.7"/></linearGradient>'
               '<linearGradient id="b" x1="0" x2="1"><stop offset="0" stop-color="' + v + '" stop-opacity="0.7"/>'
               '<stop offset="1" stop-color="' + v + '" stop-opacity="0"/></linearGradient></defs>'
               '<path d="M20,18 L282,18" stroke="url(#a)" stroke-width="1"/>'
               '<path d="M358,18 L620,18" stroke="url(#b)" stroke-width="1"/>'
               '<g fill="none" stroke="' + v + '" stroke-width="1.6" stroke-linecap="round">'
               '<path d="M290,22 C290,10 306,8 308,16 C309,22 300,22 301,17"/>'
               '<path d="M350,22 C350,10 334,8 332,16 C331,22 340,22 339,17"/>'
               '<path d="M304,24 C312,6 328,6 336,24"/><path d="M314,20 C318,14 322,14 326,20"/></g></svg>')
    (ASSETS / "divider.svg").write_text(divider, encoding="utf-8")


def font(color, tone, quote):
    def style(c, it=False, weight=400):
        return {"fontFamily": None, "fontSize": 17, "fontWeight": weight,
                "fontStyle": "italic" if it else "normal", "color": c}
    return {
        "textStyle": style(color),
        "toneTextStyle": style(tone, True),
        "quoteTextStyle": style(quote, False, 600),
        "toneHighlight": True,
        "toneDelimiters": ["**", "()", "（）"],
        "toneSymbol": "none",
        "quoteHighlight": True,
        "quoteDelimiters": ["“”", "«»", "„“", "「」", "\"\""],
        "quoteSymbol": "\"\"",
    }


def manifest(css):
    avatar = {"avatar": True, "radius": 100, "name": True}
    return {
        "spec": "tavo_theme_v1",
        "name": "花落 · Falling Blossoms",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {
            "charAvatar": False,
            "image": "theme/assets/scroll.jpg",
            "imageOpacity": 1,
            "color": argb("#F2E8D5"),
        },
        "user_bubble": {"color": argb("#F6E3D8", 0xF2), "blur": 0, "radius": 2, "alignment": "right"},
        "character_bubble": {"color": argb("#FBF6EA", 0xF5), "blur": 0, "radius": 2, "alignment": "left"},
        "user_bubble_font": font(argb("#2B2118"), argb("#8A6A58"), argb("#5A1A14")),
        "character_bubble_font": font(argb("#2B2118"), argb("#7A5C48"), argb("#8C2A20")),
        "console": {
            "color": argb("#F6EFE1", 0xF5),
            "blur": 0,
            "radius": 3,
            "sendColor": argb("#C8352B"),
            "fontSize": 17,
            "fontWeight": 400,
            "fontColor": argb("#2B2118"),
            "placeholderColor": argb("#9C8A76"),
        },
        "thinking": {"fontSize": 14, "fontWeight": 400, "color": argb("#6B5A4A"), "backgroundColor": argb("#FBF6EA", 0xE6)},
        "status_bar": {"fontSize": 13, "fontWeight": 500, "color": argb("#8C2A20"), "backgroundColor": argb("#FBF6EA", 0xE6)},
        "user_avatar": dict(avatar),
        "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar),
        "group_character_avatar": dict(avatar),
    }


def main():
    ASSETS.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_background()
    make_paper_tile()
    make_petals()
    make_brush()
    make_svgs()

    m = manifest((HERE / "style.css").read_text(encoding="utf-8"))
    (HERE / "theme.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = DIST / "falling-blossoms.thm"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "theme.json", "theme.json")
        for f in sorted(ASSETS.iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
