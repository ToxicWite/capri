"""Сборка темы «Specimen» и плагина «Specimen Lab» для Tavo.

Личная тема Токио из картинок, выбранных Claude в её Pinterest. Картинки чужие,
поэтому лежат в private/ (в git не идут) и сборка тоже кладётся в private/dist/.
В Hub эту версию не публиковать.

Ночная лаборатория: тёмная гравюра со змеями за стеклом, сообщения — предметные
стёкла. Плагин добавляет УФ-лампу (линзу, под которой чат светится в негативе и
проступают спрятанные экспонаты), питомца-пушистика и шкаф с найденными экспонатами.

Запуск: python themes/specimen/build.py
"""
import json
import math
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
SRC = HERE / "private"
FONTS = HERE / "fonts"
OUT = SRC / "dist"
THEME = OUT / "theme"
PLUGIN = OUT / "plugin"

W, H = 1080, 1920

# Экспонаты, спрятанные в темноте: где лежат на скрытом слое (доли экрана) и как называются
SPECIMENS = [
    {"id": "cat",   "file": "cat-orig.jpg",   "name": "Felis lucens",        "x": 0.70, "y": 0.20, "w": 0.44, "mode": "glow"},
    {"id": "fish",  "file": "fish-orig.jpg",  "name": "Gymnocorymbus vitreus", "x": 0.27, "y": 0.40, "w": 0.56, "mode": "glow"},
    {"id": "ribs",  "file": "ribs.jpg",       "name": "Thorax humanus",      "x": 0.55, "y": 0.56, "w": 0.46, "mode": "bones"},
    {"id": "wings", "file": "wings-orig.png", "name": "Angelus oblitus",     "x": 0.26, "y": 0.78, "w": 0.46, "mode": "oval"},
    {"id": "mint",  "file": "mint-orig.jpg",  "name": "Cervulus menthae",    "x": 0.74, "y": 0.84, "w": 0.44, "mode": "oval"},
]


def argb(hex_rgb, alpha=0xFF):
    return (alpha << 24) | int(hex_rgb.lstrip("#"), 16)


def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def make_background():
    """Змеиная гравюра, притушенная почти до черноты: за стеклом, в глубине."""
    img = cover(Image.open(SRC / "snakes.jpg").convert("RGB"), W, H)
    arr = np.asarray(img, dtype=np.float64)
    gray = arr.mean(axis=2, keepdims=True)
    arr = gray + (arr - gray) * 0.8                      # чуть меньше цвета
    yy, xx = np.mgrid[0:H, 0:W]
    vign = np.clip(1.25 - np.hypot((xx / W - 0.5) * 1.3, (yy / H - 0.42) * 1.0), 0.15, 1)
    veil = 1 - 0.35 * np.exp(-((yy / H - 0.62) / 0.25) ** 2)   # темнее под сообщениями
    arr = arr * (vign * veil * 0.42)[..., None]
    arr += np.random.default_rng(7).normal(0, 2.5, (H, W))[..., None]
    Image.fromarray(arr.clip(0, 255).astype(np.uint8)).save(THEME / "assets" / "lab.jpg", quality=86, optimize=True)


def specimen_rgba(spec, width):
    img = Image.open(SRC / spec["file"]).convert("RGB")
    img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    a = np.asarray(img, dtype=np.float64)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    oval = np.clip(1.6 - 1.6 * np.hypot((xx / w - 0.5) * 2, (yy / h - 0.5) * 2), 0, 1)
    lum = a.max(axis=2)
    if spec["mode"] == "glow":        # на чёрном фоне: светится только сам экспонат
        alpha = np.clip((lum - 18) / 90, 0, 1) * oval
    elif spec["mode"] == "bones":     # белые кости на сером: оставляем только кости
        alpha = np.clip((lum - 120) / 70, 0, 1) * oval
    else:                              # пёстрый фон: мягкий овал
        alpha = oval ** 1.3
    return Image.fromarray(np.dstack([a, alpha * 255]).astype(np.uint8), "RGBA")


def make_hidden_layer():
    """Скрытый слой: виден только сквозь УФ-линзу."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for s in SPECIMENS:
        piece = specimen_rgba(s, round(W * s["w"]))
        layer.alpha_composite(piece, (round(W * s["x"] - piece.width / 2), round(H * s["y"] - piece.height / 2)))
    layer.save(PLUGIN / "ui" / "hidden.webp", quality=82, method=6)
    # карточки для шкафа
    for s in SPECIMENS:
        img = Image.open(SRC / s["file"]).convert("RGB")
        side = min(img.size)
        img = img.crop(((img.width - side) // 2, (img.height - side) // 2, (img.width + side) // 2, (img.height + side) // 2))
        img.resize((240, 240), Image.LANCZOS).save(PLUGIN / "ui" / f"card-{s['id']}.jpg", quality=86)


def make_theme(css):
    avatar = {"avatar": True, "radius": 6, "name": True}

    def font(color, tone, quote):
        def style(c, it=False, weight=400):
            return {"fontFamily": None, "fontSize": 16, "fontWeight": weight,
                    "fontStyle": "italic" if it else "normal", "color": c}
        return {"textStyle": style(color), "toneTextStyle": style(tone, True), "quoteTextStyle": style(quote, False, 500),
                "toneHighlight": True, "toneDelimiters": ["**", "()", "（）"], "toneSymbol": "none",
                "quoteHighlight": True, "quoteDelimiters": ["“”", "«»", "„“", "\"\""], "quoteSymbol": "\"\""}

    return {
        "spec": "tavo_theme_v1",
        "name": "Specimen",
        "display_mode": "message",
        "visual_novel_bubble_height_ratio": 0.6,
        "bubble_display_type": "bubble",
        "custom_css": css,
        "background": {"charAvatar": False, "image": "theme/assets/lab.jpg", "imageOpacity": 1, "color": argb("#07080A")},
        "user_bubble": {"color": argb("#160A12", 0xE0), "blur": 6, "radius": 3, "alignment": "right"},
        "character_bubble": {"color": argb("#0A1214", 0xE0), "blur": 6, "radius": 3, "alignment": "left"},
        "user_bubble_font": font(argb("#F1DCE8"), argb("#C27BA6"), argb("#FF8FD0")),
        "character_bubble_font": font(argb("#DCEFEE"), argb("#7FB9B6"), argb("#B8FF6A")),
        "console": {"color": argb("#090C0E", 0xF0), "blur": 10, "radius": 3, "sendColor": argb("#5FF2E6"),
                    "fontSize": 16, "fontWeight": 400, "fontColor": argb("#DCEFEE"), "placeholderColor": argb("#4F6A6C")},
        "thinking": {"fontSize": 13, "fontWeight": 400, "color": argb("#7FB9B6"), "backgroundColor": argb("#090C0E", 0xE6)},
        "status_bar": {"fontSize": 12, "fontWeight": 500, "color": argb("#5FF2E6"), "backgroundColor": argb("#090C0E", 0xE6)},
        "user_avatar": dict(avatar), "character_avatar": dict(avatar),
        "group_user_avatar": dict(avatar), "group_character_avatar": dict(avatar),
    }


def main():
    for d in (THEME / "assets", PLUGIN / "ui"):
        d.mkdir(parents=True, exist_ok=True)
    make_background()
    make_hidden_layer()
    for f in FONTS.glob("*.woff2"):
        (THEME / "assets" / f.name).write_bytes(f.read_bytes())
    (THEME / "assets" / "plex-OFL.txt").write_bytes((FONTS / "plex-OFL.txt").read_bytes())
    css = (HERE / "style.css").read_text(encoding="utf-8")
    (THEME / "theme.json").write_text(json.dumps(make_theme(css), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    thm = OUT / "specimen.thm"
    with zipfile.ZipFile(thm, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(THEME / "theme.json", "theme.json")
        for f in sorted((THEME / "assets").iterdir()):
            z.write(f, f"assets/{f.name}")
    print(f"{thm} ({thm.stat().st_size // 1024} KiB)")
    # плагин: исходники из plugin/ плюс картинки, сделанные выше
    src = HERE / "plugin"
    for f in src.rglob("*"):
        if f.is_file():
            dst = PLUGIN / f.relative_to(src)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(f.read_bytes())
    (PLUGIN / "ui" / "pet.webp").write_bytes((SRC / "pet.webp").read_bytes())
    tpg = OUT / "specimen-lab.tpg"
    with zipfile.ZipFile(tpg, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PLUGIN.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(PLUGIN).as_posix())
    print(f"{tpg} ({tpg.stat().st_size // 1024} KiB)")


if __name__ == "__main__":
    main()
