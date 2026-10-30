"""Сборка темы «Not a Human» для Tavo в двух версиях: с надписями и без.

Запуск: python3 themes/not-a-human/build.py
"""
import json
import math
import random
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
DIST = HERE.parent.parent / "dist"

ABYSS = (4, 14, 12)
DEEP = (8, 34, 30)
TEAL = (63, 224, 208)
MINT = (143, 232, 200)
PALE = (207, 247, 234)
RED = (255, 59, 48)

MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def make_background():
    """Тёмная дверь в зелёной темноте: доски, растр, виньетка."""
    w, h = 900, 1950
    rng = random.Random(13)
    img = Image.new("RGB", (w, h), ABYSS)
    d = ImageDraw.Draw(img)
    # Дверное полотно с филёнками
    door = (110, 160, 790, 1950)
    d.rectangle(door, fill=(16, 50, 44))
    for x0, y0, x1, y1 in [(170, 240, 730, 820), (170, 900, 730, 1500), (170, 1580, 730, 1950)]:
        d.rectangle([x0, y0, x1, y1], outline=(34, 96, 84), width=10)
        d.rectangle([x0 + 22, y0 + 22, x1 - 22, y1 - 22], outline=(8, 28, 24), width=6)
    # Волокна дерева
    for _ in range(260):
        x = rng.uniform(door[0], door[2])
        y0 = rng.uniform(door[1], h)
        d.line([(x, y0), (x + rng.uniform(-6, 6), y0 + rng.uniform(80, 320))], fill=(24, 66, 58), width=1)
    # Глазок, из которого сочится свет
    cx, cy = 450, 560
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse([cx - 90, cy - 90, cx + 90, cy + 90], fill=(40, 150, 130))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img = Image.blend(img, Image.composite(glow, img, glow.convert("L")), 0.6)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(24, 64, 56), outline=(60, 120, 108), width=5)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(170, 255, 230))
    # Свет из щели под дверью
    for i in range(40):
        a = int(140 * (1 - i / 40))
        d.line([(110, h - 6 - i), (790, h - 6 - i)], fill=(int(30 * a / 140), int(120 * a / 140), int(100 * a / 140)))
    # Постеризация + полутоновый растр, как на коллаже
    img = img.quantize(colors=7, method=Image.Quantize.MEDIANCUT).convert("RGB")
    dots = Image.new("L", (w, h), 0)
    dd = ImageDraw.Draw(dots)
    lum = img.convert("L")
    for y in range(0, h, 9):
        for x in range(0 if (y // 9) % 2 == 0 else 4, w, 9):
            r = lum.getpixel((x, y)) / 255 * 4.2
            if r > 0.4:
                dd.ellipse([x - r, y - r, x + r, y + r], fill=85)
    img = Image.composite(Image.new("RGB", (w, h), TEAL), img, dots)
    # Сканлинии и виньетка
    px = img.load()
    for y in range(h):
        k = 0.82 if y % 4 == 0 else 1.0
        vy = (y / h - 0.45) ** 2
        for x in range(w):
            v = 1 - min(1, ((x / w - 0.5) ** 2 + vy) * 1.05)
            r, g, b = px[x, y]
            px[x, y] = (int(r * k * v), int(g * k * v), int(b * k * v))
    img.save(ASSETS / "door.png", optimize=True)


def make_halftone(name, base, dot, alpha, seed):
    """Тайл 128×128: полутоновый растр с неровностью, как у ксерокса."""
    s = 128
    rng = random.Random(seed)
    img = Image.new("RGBA", (s, s), base + (alpha,))
    d = ImageDraw.Draw(img)
    for y in range(0, s, 8):
        for x in range(0 if (y // 8) % 2 == 0 else 4, s, 8):
            r = rng.choice([0.6, 0.9, 1.2, 1.5])
            d.ellipse([x - r, y - r, x + r, y + r], fill=dot + (rng.randint(40, 110),))
    img.save(ASSETS / name, optimize=True)


def make_label(name, text, color, dot=None):
    """Маленькая надпись-картинка для угла CRT-экрана."""
    font = ImageFont.truetype(MONO_BOLD, 40)
    box = font.getbbox(text)
    pad = 30 if dot else 0
    w, h = box[2] + pad + 8, 52
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if dot:
        d.ellipse([2, 14, 24, 36], fill=dot + (255,))
    d.text((pad, 4), text, font=font, fill=color + (230,))
    img = img.resize((w // 2, h // 2), Image.LANCZOS)
    img.save(ASSETS / name, optimize=True)


def font(color, tone, quote):
    def style(c, italic=False, weight=400):
        return {"fontFamily": None, "fontSize": 16, "fontWeight": weight,
                "fontStyle": "italic" if italic else "normal", "color": c}
    return {
        "textStyle": style(color),
        "toneTextStyle": style(tone, italic=True),
        "quoteTextStyle": style(quote, weight=600),
        "toneHighlight": True,
        "toneDelimiters": ["**", "()", "（）"],
        "toneSymbol": "none",
        "quoteHighlight": True,
        "quoteDelimiters": ["“”", "「」", "\"\"", "«»"],
        "quoteSymbol": "\"\"",
    }


def manifest(name, css):
    avatar = {"avatar": True, "radius": 4, "name": True}
    return {
        "spec": "tavo_theme_v1",
        "name": name,
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {
            "charAvatar": False,
            "image": "theme/assets/door.png",
            "imageOpacity": 1,
            "color": argb("#040E0C"),
        },
        "user_bubble": {"color": argb("#8FE8C8", 0xF2), "blur": 0, "radius": 4, "alignment": "right"},
        "character_bubble": {"color": argb("#04100E", 0xEB), "blur": 6, "radius": 4, "alignment": "left"},
        "user_bubble_font": font(argb("#06201A"), argb("#1E5A4C"), argb("#000000")),
        "character_bubble_font": font(argb("#CFF7EA"), argb("#6FD6C0"), argb("#FFFFFF")),
        "console": {
            "color": argb("#04100E", 0xF2),
            "blur": 6,
            "radius": 18,
            "sendColor": argb("#3FE0D0"),
            "fontSize": 16,
            "fontWeight": 500,
            "fontColor": argb("#CFF7EA"),
            "placeholderColor": argb("#4F8F80"),
        },
        "thinking": {"fontSize": 14, "fontWeight": 400, "color": argb("#8FE8C8"), "backgroundColor": argb("#04100E", 0xE6)},
        "status_bar": {"fontSize": 13, "fontWeight": 600, "color": argb("#8FE8C8"), "backgroundColor": argb("#04100E", 0xE6)},
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
    make_halftone("halftone-dark.png", ABYSS, TEAL, 225, seed=2)
    make_halftone("halftone-mint.png", MINT, (20, 70, 60), 245, seed=4)
    make_label("on-air.png", "ON AIR", PALE, dot=RED)
    make_label("ch03.png", "CH-03", TEAL)

    base_css = (HERE / "style.css").read_text(encoding="utf-8")
    labels_css = (HERE / "labels.css").read_text(encoding="utf-8")
    common = ["door.png", "halftone-dark.png", "halftone-mint.png"]

    silent = package("not-a-human-silent.thm", "Not a Human // Silent", base_css, common)
    labeled = package("not-a-human.thm", "Not a Human // Visitor Check",
                      base_css + "\n" + labels_css, common + ["on-air.png", "ch03.png"])
    (HERE / "theme.silent.json").write_text(json.dumps(silent, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (HERE / "theme.json").write_text(json.dumps(labeled, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
