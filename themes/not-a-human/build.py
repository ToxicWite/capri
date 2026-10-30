"""Сборка темы «No, I'm Not a Human» для Tavo в двух версиях: с надписями и без.

Визуальный язык игры: монохромная ночная бирюза, зерно, вид «через глазок»
со скруглённой тёмной виньеткой, чёрные плашки реплик, синий CRT-экран,
ромбики энергии с молнией.

Запуск: python3 themes/not-a-human/build.py
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
DIST = HERE.parent.parent / "dist"

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Ночная палитра игры: от чёрного через болотную бирюзу к бледному «трупному»
NIGHT_RAMP = [(0.0, (0, 4, 4)), (0.25, (4, 22, 21)), (0.5, (14, 60, 56)),
              (0.75, (44, 140, 130)), (1.0, (190, 245, 236))]


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def colorize(lum):
    """Яркость 0..1 -> бирюзовый монохром ночной сцены."""
    out = np.zeros(lum.shape + (3,))
    for (t0, c0), (t1, c1) in zip(NIGHT_RAMP, NIGHT_RAMP[1:]):
        m = (lum >= t0) & (lum <= t1)
        k = ((lum - t0) / (t1 - t0))[m][:, None]
        out[m] = np.array(c0) + (np.array(c1) - np.array(c0)) * k
    return out


def make_background():
    """Ночь с крыльца: панельки, столб, тропинка и бледная фигура вдали."""
    w, h = 900, 1950
    rng = random.Random(21)
    L = Image.new("L", (w, h), 0)  # рисуем яркостью, красим потом
    d = ImageDraw.Draw(L)
    horizon = int(h * 0.47)

    # Небо с дымкой у горизонта
    for y in range(horizon):
        d.line([(0, y), (w, y)], fill=int(20 + 75 * (y / horizon) ** 2.0))

    # Панельные дома
    x = -30
    while x < w:
        bw, bh = rng.randint(140, 260), rng.randint(140, 300)
        top = horizon - bh
        d.rectangle([x, top, x + bw, horizon], fill=36)
        for wy in range(top + 12, horizon - 8, 18):
            for wx in range(x + 10, x + bw - 10, 16):
                if rng.random() < 0.06:
                    d.rectangle([wx, wy, wx + 7, wy + 9], fill=rng.randint(120, 190))
        x += bw + rng.randint(30, 120)

    # Земля, кусты, тропинка к крыльцу
    d.rectangle([0, horizon, w, h], fill=26)
    bushes = Image.new("L", (w, h), 0)
    bd = ImageDraw.Draw(bushes)
    for _ in range(90):
        cx = rng.choice([rng.uniform(-60, w * 0.36), rng.uniform(w * 0.64, w + 60)])
        cy = rng.uniform(horizon - 20, horizon + 260)
        r = rng.uniform(30, 90)
        bd.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6], fill=255)
    bushes = bushes.filter(ImageFilter.GaussianBlur(10))
    L.paste(8, mask=bushes)
    d.polygon([(w * 0.47, horizon + 4), (w * 0.53, horizon + 4), (w * 0.78, h * 0.72), (w * 0.22, h * 0.72)], fill=52)

    # Столб с проводами
    px0 = int(w * 0.68)
    d.rectangle([px0, horizon - 420, px0 + 7, horizon + 30], fill=8)
    d.rectangle([px0 - 40, horizon - 400, px0 + 47, horizon - 394], fill=8)
    for dy in (-400, -380):
        d.line([(px0, horizon + dy), (w, horizon + dy + 70)], fill=10, width=2)
        d.line([(px0, horizon + dy), (0, horizon + dy + 120)], fill=10, width=2)

    # Бледная фигура на тропинке: длинная, слишком худая
    fig = Image.new("L", (w, h), 0)
    fd = ImageDraw.Draw(fig)
    fx, fy = w * 0.505, horizon + 120
    fd.ellipse([fx - 9, fy - 92, fx + 9, fy - 70], fill=230)
    fd.polygon([(fx - 12, fy - 68), (fx + 12, fy - 68), (fx + 9, fy - 10), (fx - 9, fy - 10)], fill=215)
    fd.line([(fx - 12, fy - 64), (fx - 19, fy + 22)], fill=210, width=4)
    fd.line([(fx + 12, fy - 64), (fx + 19, fy + 22)], fill=210, width=4)
    fd.line([(fx - 5, fy - 12), (fx - 6, fy + 40)], fill=205, width=6)
    fd.line([(fx + 5, fy - 12), (fx + 6, fy + 40)], fill=205, width=6)
    L = Image.composite(fig, L, fig.point(lambda v: 255 if v else 0)).filter(ImageFilter.GaussianBlur(0.8))
    glow = fig.filter(ImageFilter.GaussianBlur(18)).point(lambda v: v // 4)
    L = Image.fromarray(np.maximum(np.asarray(L), np.asarray(glow)))
    d = ImageDraw.Draw(L)

    # Доски крыльца на переднем плане
    porch = int(h * 0.74)
    d.rectangle([0, porch, w, h], fill=62)
    y, step = porch, 26
    while y < h:
        d.line([(0, y), (w, y)], fill=18, width=3)
        y += step
        step = int(step * 1.18)
    for i in range(-6, 7):
        d.line([(w / 2 + i * 40, porch), (w / 2 + i * 260, h)], fill=40, width=2)

    # Дверной косяк слева, на него падает свет из дома
    d.rectangle([0, 0, 70, h], fill=24)
    d.rectangle([70, 0, 92, h], fill=170)
    d.rectangle([92, 0, 104, h], fill=10)

    lum = np.asarray(L, dtype=np.float64) / 255

    # Постеризация + зерно
    nr = np.random.default_rng(7)
    lum = np.clip(lum ** 0.8 + nr.normal(0, 0.05, lum.shape), 0, 1)
    lum = np.round(lum * 12) / 12

    # Скруглённая «глазковая» виньетка, как в кадре игры
    yy, xx = np.mgrid[0:h, 0:w]
    nx, ny = (xx / w - 0.5) * 2, (yy / h - 0.5) * 2
    r = (np.abs(nx) ** 4 + np.abs(ny) ** 4) ** 0.25
    vign = np.clip(1.4 - r * 0.95, 0, 1) ** 1.3
    rgb = colorize(lum) * vign[..., None]
    img = Image.fromarray(rgb.astype(np.uint8)).quantize(colors=48, method=Image.Quantize.MEDIANCUT)
    img.save(ASSETS / "night-porch.png", optimize=True)


def diamond(d, x, y, s, full):
    """Ромбик энергии с молнией внутри."""
    c = (240, 240, 236, 255) if full else (120, 130, 128, 140)
    pts = [(x + s / 2, y), (x + s, y + s / 2), (x + s / 2, y + s), (x, y + s / 2)]
    d.polygon(pts, outline=c, width=max(2, s // 12))
    bolt = [(x + s * .56, y + s * .2), (x + s * .36, y + s * .54), (x + s * .5, y + s * .54),
            (x + s * .42, y + s * .82), (x + s * .66, y + s * .44), (x + s * .52, y + s * .44)]
    d.polygon(bolt, fill=c if full else (0, 0, 0, 0), outline=c)


def make_energy():
    """Ряд энергии: energy-5.png (все пять ромбиков) ... energy-0.png (пусто)."""
    s, gap = 48, 14
    fw = 5 * s + 4 * gap
    for left in range(6):
        img = Image.new("RGBA", (fw + 4, s + 4), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for i in range(5):
            diamond(d, 2 + i * (s + gap), 2, s, full=i < left)
        img.resize(((fw + 4) // 2, (s + 4) // 2), Image.LANCZOS).save(ASSETS / f"energy-{left}.png", optimize=True)


def make_static():
    """Тайл телевизионных помех для синего экрана."""
    nr = np.random.default_rng(3)
    a = nr.integers(0, 2, (64, 64)) * nr.integers(20, 75, (64, 64))
    img = np.zeros((64, 64, 4), dtype=np.uint8)
    img[..., :3] = 255
    img[..., 3] = a
    Image.fromarray(img).resize((128, 128), Image.NEAREST).save(ASSETS / "static.png", optimize=True)


def make_ticker():
    """Бегущая строка экстренного вещания (только версия с надписями)."""
    text = "STAY CALM  ·  DO NOT LEAVE THE HOUSE DURING THE DAY  ·  LOOK FOR THE SIGNS  ·  "
    font = ImageFont.truetype(FONT_BOLD, 26)
    w = int(font.getlength(text))
    img = Image.new("RGBA", (w, 34), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((0, 2), text, font=font, fill=(255, 255, 255, 235))
    img.save(ASSETS / "ticker.png", optimize=True)
    disp_h = 10
    return round(w * disp_h / 34), disp_h


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


def manifest(name, css):
    avatar = {"avatar": True, "radius": 0, "name": True}
    return {
        "spec": "tavo_theme_v1",
        "name": name,
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {
            "charAvatar": False,
            "image": "theme/assets/night-porch.png",
            "imageOpacity": 1,
            "color": argb("#000404"),
        },
        # Чёрные плашки, как реплики в игре
        "user_bubble": {"color": argb("#0E1514", 0xF2), "blur": 0, "radius": 0, "alignment": "right"},
        "character_bubble": {"color": argb("#000000", 0xEB), "blur": 0, "radius": 0, "alignment": "left"},
        "user_bubble_font": font(argb("#E9E4DA"), argb("#9A9A92"), argb("#FFFFFF")),
        "character_bubble_font": font(argb("#6FE0D4"), argb("#3F9C92"), argb("#A8F5EC")),
        "console": {
            "color": argb("#1B33C8"),
            "blur": 0,
            "radius": 14,
            "sendColor": argb("#FFFFFF"),
            "fontSize": 16,
            "fontWeight": 500,
            "fontColor": argb("#FFFFFF"),
            "placeholderColor": argb("#A9B6FF"),
        },
        "thinking": {"fontSize": 14, "fontWeight": 400, "color": argb("#4FB5AA"), "backgroundColor": argb("#000000", 0xE6)},
        "status_bar": {"fontSize": 13, "fontWeight": 500, "color": argb("#6FE0D4"), "backgroundColor": argb("#000000", 0xE6)},
        "user_avatar": dict(avatar),
        "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar),
        "group_character_avatar": dict(avatar),
    }


def package(out_name, theme_name, css, assets):
    m = manifest(theme_name, css)
    out = DIST / out_name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("theme.json", json.dumps(m, ensure_ascii=False, indent=2) + "\n")
        for a in assets:
            z.write(ASSETS / a, f"assets/{a}")
    print(f"{out} ({out.stat().st_size // 1024} KiB)")
    return m


def main():
    ASSETS.mkdir(exist_ok=True)
    DIST.mkdir(exist_ok=True)
    make_background()
    make_energy()
    make_static()
    tw, th = make_ticker()

    base_css = (HERE / "style.css").read_text(encoding="utf-8")
    labels_css = (HERE / "labels.css").read_text(encoding="utf-8")
    labels_css = labels_css.replace("TICKER_W", str(tw)).replace("TICKER_H", str(th))
    common = ["night-porch.png", "static.png"] + [f"energy-{i}.png" for i in range(6)]

    package("not-a-human-silent.thm", "No, I'm Not a Human // Silent", base_css, common)
    labeled = package("not-a-human.thm", "No, I'm Not a Human // Visitor Check",
                      base_css + "\n" + labels_css, common + ["ticker.png"])
    (HERE / "theme.json").write_text(json.dumps(labeled, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
