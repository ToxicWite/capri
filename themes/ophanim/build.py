"""Сборка темы «Ophanim» для Tavo — библейски точный ангел.

«А ободья у них — высоки и страшны были они; ободья их у всех четырёх
вокруг полны были глаз» (Иез. 1:18).

Чёрная пустота, холодный свет сверху, два скрещённых кольца в глазах и
крылья, нарисованные штриховкой как гравюра. Монохром, золото — только нимб.

Запуск: python3 themes/ophanim/build.py
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


def eye(d, x, y, r, ang=0.0, open_=1.0, ink=(14, 14, 16), paper=BONE, line=2):
    """Глаз-гравюра: миндалина, радужка с кольцами, зрачок, блик, ресницы."""
    c, s = math.cos(ang), math.sin(ang)

    def tr(px, py):
        return (x + px * c - py * s, y + px * s + py * c)

    hh = r * 0.55 * open_
    top = [tr(-r + 2 * r * t / 24, -hh * math.sin(math.pi * t / 24)) for t in range(25)]
    bot = [tr(r - 2 * r * t / 24, hh * math.sin(math.pi * t / 24)) for t in range(25)]
    d.polygon(top + bot, fill=paper)
    if open_ > 0.15:
        ir = min(r * 0.42, hh * 1.05)
        d.ellipse([x - ir, y - ir, x + ir, y + ir], fill=(60, 60, 64), outline=ink, width=line)
        d.ellipse([x - ir * 0.7, y - ir * 0.7, x + ir * 0.7, y + ir * 0.7], outline=(140, 140, 146), width=max(1, line // 2))
        d.ellipse([x - ir * 0.42, y - ir * 0.42, x + ir * 0.42, y + ir * 0.42], fill=ink)
        d.ellipse([x - ir * 0.5 + ir * 0.2, y - ir * 0.5, x - ir * 0.15, y - ir * 0.15], fill=paper)
        # нижнее веко поверх радужки
        d.polygon(bot + [tr(r, hh * 1.6), tr(-r, hh * 1.6)], fill=None)
    d.line(top, fill=ink, width=line + 1)
    d.line(bot, fill=ink, width=line)
    for k in range(7):  # ресницы
        t = 4 + k * 2.6
        px, py = r * (-1 + 2 * t / 24), -hh * math.sin(math.pi * t / 24)
        d.line([tr(px, py), tr(px * 1.05, py - r * 0.18)], fill=ink, width=max(1, line - 1))


def ring_eyes(img, cx, cy, rx, ry, rot, n, size, rng, band):
    """Кольцо офанима: эллиптический обод со штриховкой и глазами по окружности."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cr, sr = math.cos(rot), math.sin(rot)

    def pt(t, k=1.0):
        x, y = rx * k * math.cos(t), ry * k * math.sin(t)
        return (cx + x * cr - y * sr, cy + x * sr + y * cr)

    steps = 360
    outer = [pt(math.tau * i / steps, 1 + band) for i in range(steps)]
    inner = [pt(math.tau * i / steps, 1 - band) for i in range(steps)]
    # обод: светлая полоса и поперечная штриховка
    for i in range(steps):
        d.polygon([outer[i], outer[(i + 1) % steps], inner[(i + 1) % steps], inner[i]], fill=(150, 148, 142, 255))
    for i in range(0, steps, 2):
        d.line([outer[i], inner[i]], fill=(40, 40, 44, 200), width=1)
    d.line(outer + [outer[0]], fill=(12, 12, 14, 255), width=3)
    d.line(inner + [inner[0]], fill=(12, 12, 14, 255), width=3)
    for i in range(n):
        t = math.tau * i / n + rng.uniform(-0.05, 0.05)
        x, y = pt(t)
        ang = math.atan2(y - cy, x - cx) + math.pi / 2
        eye(d, x, y, size * rng.uniform(0.85, 1.1), ang, open_=rng.uniform(0.55, 1.0), line=2)
    img.alpha_composite(layer)


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
    """Крыло-гравюра: дуга «руки» вверх-наружу, с неё свисают ярусы перьев."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rx, ry = root

    def arm(t):  # точка на дуге крыла, t от плеча (0) до кончика (1)
        a = math.radians(200 - 150 * t) if direction < 0 else math.radians(-20 + 150 * t)
        a = math.radians(-160 + 120 * t) if direction < 0 else math.radians(-20 - 120 * t)
        return (rx + direction * (300 * t) * scale, ry - (math.sin(t * math.pi * 0.9) * 170 + t * 60) * scale)

    # ярусы: (число перьев, длина, ширина, отступ вниз, светлота) — от дальних к ближним
    tiers = [(13, 250, 26, 0, 168), (12, 165, 24, 30, 192), (11, 95, 20, 55, 212), (10, 50, 15, 75, 228)]
    for n, length, width, drop, shade in tiers:
        for i in range(n):
            t = 0.05 + 0.95 * i / (n - 1)
            ax, ay = arm(t)
            ay += drop * scale * (1 - t * 0.5)
            ang = math.radians(90 + direction * (-20 + 95 * t))  # к кончику перья разворачиваются наружу
            ln = length * scale * (0.75 + 0.5 * t if length > 200 else 1) * rng.uniform(0.92, 1.05)
            feather(d, ax, ay, ang, ln, width * scale * 0.5, shade + rng.randint(-8, 8))
    img.alpha_composite(layer)


def make_background():
    rng = random.Random(1)
    yy, xx = np.mgrid[0:H, 0:W]
    arr = np.zeros((H, W, 3))
    # холодный свет сверху: конус лучей
    cone = np.clip(1 - np.abs(xx - W / 2) / (W * 0.2 + yy * 0.35), 0, 1) ** 1.6
    fall = np.exp(-yy / 1100)
    arr += np.array([70, 72, 78]) * (cone * fall)[..., None]
    for _ in range(14):  # отдельные лучи
        off = rng.uniform(-0.35, 0.35)
        ray = np.exp(-((xx - W / 2 - off * yy) / (6 + yy * 0.03)) ** 2) * fall * rng.uniform(0.15, 0.4)
        arr += np.array([60, 62, 66]) * ray[..., None]
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")

    cx, cy = W / 2, 520
    wing(img, (cx - 150, cy - 30), -1, rng, 1.05)
    wing(img, (cx + 150, cy - 30), 1, rng, 1.05)
    # нимб
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse([cx - 175, cy - 175, cx + 175, cy + 175], outline=GOLD + (200,), width=3)
    hd.ellipse([cx - 165, cy - 165, cx + 165, cy + 165], outline=GOLD + (90,), width=1)
    glow = halo.filter(ImageFilter.GaussianBlur(8))
    img.alpha_composite(glow)
    img.alpha_composite(halo)
    ring_eyes(img, cx, cy, 230, 95, math.radians(25), 12, 22, rng, 0.1)
    ring_eyes(img, cx, cy, 230, 95, math.radians(-25), 12, 22, rng, 0.1)
    # центральный глаз
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 56, cy - 56, cx + 56, cy + 56], fill=(18, 18, 20, 255), outline=BONE + (255,), width=3)
    eye(d, cx, cy, 44, 0, 1.0, line=3)

    # глаза в темноте ниже — еле видны
    for _ in range(0):
        ex, ey = rng.uniform(60, W - 60), rng.uniform(1000, 1850)
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        eye(ImageDraw.Draw(layer), ex, ey, rng.uniform(18, 28), rng.uniform(-0.3, 0.3), rng.uniform(0.2, 0.9),
            ink=(10, 10, 12), paper=(70, 70, 74), line=1)
        a = layer.split()[3].point(lambda v: int(v * rng.uniform(0.25, 0.5)))
        layer.putalpha(a)
        img.alpha_composite(layer)

    # пыль в луче, зерно, виньетка, приглушить для чтения
    arr = np.asarray(img.convert("RGB"), dtype=np.float64)
    nr = np.random.default_rng(2)
    dust = (nr.random((H, W)) > 0.9985) * cone * 160
    arr += dust[..., None]
    arr += nr.normal(0, 3, (H, W))[..., None]
    vign = np.clip(1.2 - np.hypot((xx / W - 0.5) * 1.3, (yy / H - 0.4) * 0.9), 0.2, 1)
    arr *= (vign * 0.82)[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(ASSETS / "ophanim.jpg", quality=90, optimize=True)


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
    arr = base + np.array([150, 150, 156]) * vein[..., None] * 0.55
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
    img.putalpha(235)
    img.save(ASSETS / "marble.png", optimize=True)


def make_eye_strips():
    """Полосы глаз над полем ввода: закрытые (покой) и открытые (генерация)."""
    for name, op in (("eyes-closed.png", 0.0), ("eyes-open.png", 1.0)):
        w, h = 640, 60
        rng = random.Random(9)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for i in range(8):
            x = 40 + i * 80 + rng.uniform(-6, 6)
            y = 30 + rng.uniform(-5, 5)
            r = rng.uniform(22, 26)
            if op == 0:
                pts = [(x - r + 2 * r * t / 20, y + r * 0.18 * math.sin(math.pi * t / 20)) for t in range(21)]
                d.line(pts, fill=BONE + (150,), width=2)
                for k in range(5):
                    px, py = pts[3 + k * 3]
                    d.line([(px, py), (px - 1, py + 5)], fill=BONE + (120,), width=1)
            else:  # чистая миндалина: белок, радужка, зрачок, блик
                hh = r * 0.5
                top = [(x - r + 2 * r * t / 20, y - hh * math.sin(math.pi * t / 20)) for t in range(21)]
                bot = [(x + r - 2 * r * t / 20, y + hh * math.sin(math.pi * t / 20)) for t in range(21)]
                d.polygon(top + bot, fill=BONE + (235,))
                ir = hh * 0.95
                d.ellipse([x - ir, y - ir, x + ir, y + ir], fill=(70, 70, 76, 255))
                d.ellipse([x - ir * 0.5, y - ir * 0.5, x + ir * 0.5, y + ir * 0.5], fill=(8, 8, 10, 255))
                d.ellipse([x - ir * 0.55, y - ir * 0.6, x - ir * 0.15, y - ir * 0.2], fill=BONE + (255,))
                d.line(top, fill=(8, 8, 10, 255), width=3)
                d.line(bot, fill=(8, 8, 10, 255), width=2)
        img.save(ASSETS / name, optimize=True)


def make_svgs():
    b = "#e2ded4"
    # уголок: медальон с глазом, от него — тонкие линии рамки вправо и вниз
    corner = ('<svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 56 56">'
              f'<path d="M22,11 L56,11 M11,22 L11,56" stroke="{b}" stroke-width="1" opacity="0.55"/>'
              f'<path d="M24,15 L44,15 M15,24 L15,44" stroke="{b}" stroke-width="0.7" opacity="0.35"/>'
              f'<circle cx="11" cy="11" r="10" fill="#1a1a1d" stroke="{b}" stroke-width="1.1"/>'
              f'<circle cx="11" cy="11" r="7.6" fill="none" stroke="#c9aa6e" stroke-width="0.6" opacity="0.8"/>'
              f'<path d="M4.5,11 Q11,5.5 17.5,11 Q11,16.5 4.5,11 Z" fill="{b}"/>'
              '<circle cx="11" cy="11" r="2.6" fill="#1a1a1d"/><circle cx="10.1" cy="10.1" r="0.8" fill="#e2ded4"/></svg>')
    (ASSETS / "wing-corner.svg").write_text(corner, encoding="utf-8")
    # маленький глаз перед именем
    eye_svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="14" viewBox="0 0 24 14">'
               f'<path d="M1,7 Q12,-3 23,7 Q12,17 1,7 Z" fill="none" stroke="{b}" stroke-width="1.3"/>'
               f'<circle cx="12" cy="7" r="3.4" fill="{b}"/><circle cx="12" cy="7" r="1.5" fill="#111"/></svg>')
    (ASSETS / "eye.svg").write_text(eye_svg, encoding="utf-8")
    divider = ('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="30" viewBox="0 0 640 30">'
               '<defs><linearGradient id="a" x1="0" x2="1"><stop offset="0" stop-color="#e2ded4" stop-opacity="0"/>'
               '<stop offset="1" stop-color="#e2ded4" stop-opacity="0.6"/></linearGradient>'
               '<linearGradient id="b" x1="0" x2="1"><stop offset="0" stop-color="#e2ded4" stop-opacity="0.6"/>'
               '<stop offset="1" stop-color="#e2ded4" stop-opacity="0"/></linearGradient></defs>'
               '<path d="M20,15 L290,15" stroke="url(#a)"/><path d="M350,15 L620,15" stroke="url(#b)"/>'
               f'<circle cx="320" cy="15" r="11" fill="none" stroke="#c9aa6e" stroke-width="1"/>'
               f'<path d="M308,15 Q320,6 332,15 Q320,24 308,15 Z" fill="none" stroke="{b}" stroke-width="1.2"/>'
               f'<circle cx="320" cy="15" r="3" fill="{b}"/></svg>')
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
        "name": "Ophanim",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {
            "charAvatar": False,
            "image": "theme/assets/ophanim.jpg",
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
    make_eye_strips()
    make_svgs()
    m = manifest((HERE / "style.css").read_text(encoding="utf-8"))
    (HERE / "theme.json").write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out = DIST / "ophanim.thm"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "theme.json", "theme.json")
        for f in sorted(ASSETS.iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
