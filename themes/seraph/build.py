"""Сборка темы «Seraph» для Tavo — изящный ангел в темноте.

Чёрная пустота и мягкий свет сверху, золотой нимб с гравюрными лучами и
звездой, под ним поднятые крылья из перьев-гравюры со свечением, искры
и опадающие перья. Тёмный мрамор и золото.

Запуск: python3 themes/seraph/build.py
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
BONE = (226, 222, 212)
GOLD = (201, 170, 110)


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def feather(d, x, y, ang, length, width, shade):
    """Перо: вытянутый лист с остриём, тёмный контур, стержень и штриховка."""
    c, s_ = math.cos(ang), math.sin(ang)
    pts = []
    for i in range(21):  # одна сторона, потом другая
        t = i / 20
        half = width * math.sin(math.pi * min(1, t * 1.15)) ** 0.7 * (1 - 0.25 * t)
        pts.append((t * length, half))
    outline = pts + [(length * 1.04, 0)] + [(px, -py) for px, py in reversed(pts)]
    poly = [(x + px * c - py * s_, y + px * s_ + py * c) for px, py in outline]
    d.polygon(poly, fill=(shade, shade - 2, shade - 6, 255), outline=(8, 8, 10, 255))
    d.line([(x, y), (x + length * c, y + length * s_)], fill=(30, 30, 34, 230), width=1)
    for k in range(3, 18, 2):  # штриховка по одной стороне — тень
        t = k / 20
        half = width * math.sin(math.pi * min(1, t * 1.15)) ** 0.7 * (1 - 0.25 * t)
        bx, by = x + t * length * c, y + t * length * s_
        d.line([(bx, by), (bx - half * 0.9 * s_ + length * 0.06 * c, by + half * 0.9 * c + length * 0.06 * s_)],
               fill=(40, 40, 46, 170), width=1)


def wing(img, root, direction, rng, scale=1.0):
    """Поднятое крыло: дуга вверх-наружу, ярусы перьев свисают вниз и веером наружу."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rx, ry = root

    def arm(t):
        return (rx + direction * 300 * t * scale, ry - (260 * math.sin(t * math.pi / 2) - 40 * t * t) * scale)

    # ярусы: (число, длина, ширина, отступ вниз, светлота) — от дальних маховых к ближним кроющим
    tiers = [(15, 230, 30, 10, 196), (13, 150, 28, 40, 214), (12, 90, 24, 64, 228), (10, 48, 18, 82, 238)]
    for n, length, width, drop, shade in tiers:
        for i in range(n):
            t = 0.04 + 0.96 * i / (n - 1)
            ax, ay = arm(t)
            ay += drop * scale * (1 - 0.6 * t)
            ang = math.radians(90 - direction * (8 + 72 * t))
            ln = length * scale * (0.7 + 0.6 * t if length > 200 else 0.85 + 0.25 * t) * rng.uniform(0.94, 1.04)
            feather(d, ax, ay, ang, ln, width * scale * 0.5, shade + rng.randint(-6, 6))
    glow = layer.filter(ImageFilter.GaussianBlur(14))
    ga = glow.split()[3].point(lambda v: int(v * 0.35))
    glow = Image.new("RGBA", img.size, (235, 228, 210, 0))
    glow.putalpha(ga)
    img.alpha_composite(glow)
    img.alpha_composite(layer)


def star(d, x, y, r, color, points=4, inner=0.28):
    pts = []
    for k in range(points * 2):
        a = -math.pi / 2 + k * math.pi / points
        rr = r if k % 2 == 0 else r * inner
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    d.polygon(pts, fill=color)


def make_background():
    rng = random.Random(7)
    yy, xx = np.mgrid[0:H, 0:W]
    arr = np.zeros((H, W, 3))
    # мягкий тёплый свет сверху
    cone = np.clip(1 - np.abs(xx - W / 2) / (W * 0.22 + yy * 0.32), 0, 1) ** 1.5
    fall = np.exp(-yy / 1200)
    arr += np.array([74, 72, 70]) * (cone * fall)[..., None]
    for _ in range(12):
        off = rng.uniform(-0.3, 0.3)
        ray = np.exp(-((xx - W / 2 - off * yy) / (6 + yy * 0.03)) ** 2) * fall * rng.uniform(0.12, 0.32)
        arr += np.array([66, 62, 56]) * ray[..., None]
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")

    cx, hy, wy = W / 2, 330, 600
    # нимб: лучи-гравюра, кольца, звезда в центре
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    for k in range(96):
        a = k * math.tau / 96
        r1, r2 = 132, (220 if k % 2 == 0 else 180) + (30 if k % 8 == 0 else 0)
        hd.line([(cx + math.cos(a) * r1, hy + math.sin(a) * r1), (cx + math.cos(a) * r2, hy + math.sin(a) * r2)],
                fill=GOLD + (70 if k % 2 else 110,), width=1)
    for r, wdt, a in [(118, 3, 230), (108, 1, 140), (126, 1, 110)]:
        hd.ellipse([cx - r, hy - r, cx + r, hy + r], outline=GOLD + (a,), width=wdt)
    glow = halo.filter(ImageFilter.GaussianBlur(10))
    img.alpha_composite(glow)
    img.alpha_composite(halo)
    sd = ImageDraw.Draw(img)
    soft = Image.new("RGBA", img.size, (0, 0, 0, 0))
    star(ImageDraw.Draw(soft), cx, hy, 60, (255, 240, 210, 140), 8, 0.35)
    img.alpha_composite(soft.filter(ImageFilter.GaussianBlur(14)))
    star(sd, cx, hy, 34, (255, 246, 226, 255), 4, 0.18)
    star(sd, cx, hy, 20, GOLD + (255,), 4, 0.18)
    # крылья под нимбом
    wing(img, (cx - 24, wy), -1, rng, 1.05)
    wing(img, (cx + 24, wy), 1, rng, 1.05)

    # звёзды-искры и опадающие перья
    d = ImageDraw.Draw(img)
    for _ in range(30):
        x, y = rng.uniform(30, W - 30), rng.uniform(40, H - 60)
        r = rng.choice([2, 3, 3, 4, 6])
        star(d, x, y, r, (232, 226, 210, rng.randint(90, 200)))
    for _ in range(9):
        x, y = rng.uniform(80, W - 80), rng.uniform(900, 1820)
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        feather(ImageDraw.Draw(layer), x, y, rng.uniform(0, math.tau), rng.uniform(40, 70), rng.uniform(7, 10), 220)
        layer.putalpha(layer.split()[3].point(lambda v: int(v * 0.35)))
        img.alpha_composite(layer)

    arr = np.asarray(img.convert("RGB"), dtype=np.float64)
    nr = np.random.default_rng(2)
    arr += ((nr.random((H, W)) > 0.9985) * cone * 150)[..., None]
    arr += nr.normal(0, 3, (H, W))[..., None]
    vign = np.clip(1.2 - np.hypot((xx / W - 0.5) * 1.3, (yy / H - 0.4) * 0.9), 0.2, 1)
    arr *= (vign * 0.85)[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(ASSETS / "seraph.jpg", quality=90, optimize=True)


def make_marble():
    """Тайл тёмного мрамора с тонкими светлыми прожилками, бесшовный."""
    s = 320
    nr = np.random.default_rng(5)
    yy, xx = np.mgrid[0:s, 0:s]
    noise = np.zeros((s, s))
    for f, a in [(2, 1.0), (4, 0.5), (8, 0.25), (16, 0.12)]:
        g = nr.normal(0, 1, (f, f))
        g = np.tile(g, (2, 2))
        up = np.asarray(Image.fromarray(((g + 3) * 40).clip(0, 255).astype(np.uint8)).resize((s * 2, s * 2), Image.BICUBIC), dtype=np.float64)
        noise += (up[s // 2:s // 2 + s, s // 2:s // 2 + s] / 255 - 0.5) * a
    vein = np.abs(np.sin((xx + yy * 0.6) / s * math.tau * 2 + noise * 6))
    vein = (1 - vein) ** 18
    base = np.array([34, 34, 38]) + (noise * 14)[..., None]
    arr = base + np.array([150, 150, 156]) * vein[..., None] * 0.28
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    img.putalpha(235)
    img.save(ASSETS / "marble.png", optimize=True)


def make_feather_strip():
    """Бесшовная полоса светлых перьев, которые опускаются над полем ввода."""
    w, h = 640, 240
    rng = random.Random(9)
    full = Image.new("RGBA", (w, h * 3), (0, 0, 0, 0))
    for _ in range(9):
        x, y = rng.uniform(20, w - 20), rng.uniform(0, h)
        ang, ln, wd = rng.uniform(1.0, 2.2), rng.uniform(28, 42), rng.uniform(5, 7)
        for k in range(3):
            layer = Image.new("RGBA", full.size, (0, 0, 0, 0))
            feather(ImageDraw.Draw(layer), x, y + k * h, ang, ln, wd, 236)
            layer.putalpha(layer.split()[3].point(lambda v: int(v * 0.8)))
            full.alpha_composite(layer)
    full.crop((0, h, w, 2 * h)).save(ASSETS / "feathers.png", optimize=True)


def make_svgs():
    g = "#c9aa6e"
    # уголок рамки: золотая звезда в углу, линии тают по кромкам
    corner = ('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">'
              '<defs><linearGradient id="h" x1="0" x2="1"><stop offset="0" stop-color="#c9aa6e" stop-opacity="0.8"/>'
              '<stop offset="1" stop-color="#c9aa6e" stop-opacity="0"/></linearGradient>'
              '<linearGradient id="v" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#c9aa6e" stop-opacity="0.8"/>'
              '<stop offset="1" stop-color="#c9aa6e" stop-opacity="0"/></linearGradient></defs>'
              '<path d="M14,1 L120,1" stroke="url(#h)" stroke-width="1.2"/>'
              '<path d="M1,14 L1,120" stroke="url(#v)" stroke-width="1.2"/>'
              f'<path d="M8,0 L9.6,6.4 L16,8 L9.6,9.6 L8,16 L6.4,9.6 L0,8 L6.4,6.4 Z" fill="{g}"/></svg>')
    (ASSETS / "star-corner.svg").write_text(corner, encoding="utf-8")
    divider = ('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="30" viewBox="0 0 640 30">'
               '<defs><linearGradient id="a" x1="0" x2="1"><stop offset="0" stop-color="#c9aa6e" stop-opacity="0"/>'
               '<stop offset="1" stop-color="#c9aa6e" stop-opacity="0.7"/></linearGradient>'
               '<linearGradient id="b" x1="0" x2="1"><stop offset="0" stop-color="#c9aa6e" stop-opacity="0.7"/>'
               '<stop offset="1" stop-color="#c9aa6e" stop-opacity="0"/></linearGradient></defs>'
               '<path d="M20,15 L298,15" stroke="url(#a)"/><path d="M342,15 L620,15" stroke="url(#b)"/>'
               f'<circle cx="320" cy="15" r="11" fill="none" stroke="{g}" stroke-width="0.8" opacity="0.7"/>'
               f'<path d="M320,5 L322.2,12.8 L330,15 L322.2,17.2 L320,25 L317.8,17.2 L310,15 L317.8,12.8 Z" fill="{g}"/></svg>')
    (ASSETS / "divider.svg").write_text(divider, encoding="utf-8")


def font(color, tone, quote):
    def style(c, it=False, weight=500):
        return {"fontFamily": None, "fontSize": 18, "fontWeight": weight,
                "fontStyle": "italic" if it else "normal", "color": c}
    return {
        "textStyle": style(color),
        "toneTextStyle": style(tone, True),
        "quoteTextStyle": style(quote, False, 600),
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
        "name": "Seraph",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {
            "charAvatar": False,
            "image": "theme/assets/seraph.jpg",
            "imageOpacity": 1,
            "color": argb("#08080A"),
        },
        "user_bubble": {"color": argb("#0B0B0D", 0xEB), "blur": 0, "radius": 0, "alignment": "right"},
        "character_bubble": {"color": argb("#222226", 0xF0), "blur": 0, "radius": 0, "alignment": "left"},
        "user_bubble_font": font(argb("#D8D4CA"), argb("#8E8C86"), argb("#F2EEE4")),
        "character_bubble_font": font(argb("#E2DED4"), argb("#9C9A94"), argb("#F4EFE2")),
        "console": {
            "color": argb("#0B0B0D", 0xF2),
            "blur": 6,
            "radius": 0,
            "sendColor": argb("#C9AA6E"),
            "fontSize": 18,
            "fontWeight": 500,
            "fontColor": argb("#E2DED4"),
            "placeholderColor": argb("#77756F"),
        },
        "thinking": {"fontSize": 15, "fontWeight": 500, "color": argb("#9C9A94"), "backgroundColor": argb("#111113", 0xE6)},
        "status_bar": {"fontSize": 13, "fontWeight": 600, "color": argb("#C9AA6E"), "backgroundColor": argb("#111113", 0xE6)},
        "user_avatar": dict(avatar),
        "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar),
        "group_character_avatar": dict(avatar),
    }


def main():
    ASSETS.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_background()
    make_marble()
    make_feather_strip()
    make_svgs()
    m = manifest((HERE / "style.css").read_text(encoding="utf-8"))
    (HERE / "theme.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = DIST / "seraph.thm"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "theme.json", "theme.json")
        for f in sorted(ASSETS.iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
