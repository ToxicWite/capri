#!/usr/bin/env python3
"""Builds the Adventure Journal plugin package.

Usage: python3 tools/build.py
Output: build/adventure-journal/ (unpacked) and dist/adventure-journal-<version>.tpg
"""
import json
import math
import re
import shutil
import sys
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "build" / "adventure-journal"
DIST = ROOT / "dist"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from locales import L, LOCALES  # noqa: E402


def fail(msg):
    print("ERROR:", msg)
    sys.exit(1)


def glen(s):
    # Approximate grapheme count: ignore combining marks and variation selectors.
    return sum(1 for ch in s if not unicodedata.combining(ch) and ch not in "️‍")


def write_locales():
    (OUT / "locales").mkdir(parents=True)
    for idx, tag in enumerate(LOCALES):
        catalog = {}
        for key, values in L.items():
            if len(values) != len(LOCALES):
                fail(f"{key}: expected {len(LOCALES)} translations")
            if not values[idx].strip():
                fail(f"{key}: empty {tag} translation")
            catalog[key] = values[idx]
        (OUT / "locales" / f"{tag}.json").write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def check_manifest(manifest):
    limits = []

    def walk(node, path):
        if isinstance(node, dict):
            if set(node.keys()) == {"$t"}:
                if node["$t"] not in L:
                    fail(f"manifest {path}: missing catalog key {node['$t']}")
                limits.append((path, node["$t"]))
                return
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(manifest, "manifest")
    for path, key in limits:
        if path.endswith(".description") and "settings" not in path:
            lo, hi, single = 1, 10000, False
        elif path.endswith("releaseNotes"):
            lo, hi, single = 1, 5000, False
        elif path == "manifest.name":
            lo, hi, single = 1, 64, True
        elif "inputActions" in path or "sidebar" in path or "lastMessageActions" in path:
            lo, hi, single = 1, 48, True
        elif path.endswith(".description") or path.endswith(".text"):
            lo, hi, single = 1, 500, False
        elif path.endswith(".default"):
            continue
        else:
            lo, hi, single = 1, 80, True
        for idx, tag in enumerate(LOCALES):
            value = L[key][idx]
            n = glen(value)
            if not lo <= n <= hi:
                fail(f"{path} [{tag}] length {n} outside {lo}-{hi}: {value[:40]}")
            if single and "\n" in value:
                fail(f"{path} [{tag}] must be single-line")

    ids = [a["id"] for group in ("inputActions", "sidebar", "lastMessageActions")
           for a in manifest["contributes"].get(group, [])]
    if len(ids) != len(set(ids)):
        fail("duplicate action ids")
    keys = [f["key"] for f in manifest["contributes"]["settings"]["schema"] if "key" in f]
    if len(keys) != len(set(keys)):
        fail("duplicate settings keys")
    return ids, keys


def check_code_keys(code):
    used = set(re.findall(r"\bt\('([A-Za-z0-9_.]+)'(?:\s*,|\))", code))
    missing = sorted(k for k in used if k not in L)
    if missing:
        fail("code uses missing catalog keys: " + ", ".join(missing))
    # Dynamic keys built from known prefixes.
    from_core = re.search(r"var TEMPLATES = \{(.*?)\n  \};", code, re.S).group(1)
    templates = re.findall(r"^    (\w+): \{", from_core, re.M)
    for tpl in templates:
        for k in (f"template.{tpl}", f"template.{tpl}.desc"):
            if k not in L:
                fail(f"missing {k}")
    for sec in ("status", "stats", "inventory", "quests", "relations"):
        if f"sec.default.{sec}" not in L:
            fail(f"missing sec.default.{sec}")
    for tpl, body in re.findall(r"^    (\w+): \{(.*?)^    \},", from_core, re.M | re.S):
        for sid in re.findall(r"id: '(\w+)'", body):
            if f"stat.{tpl}.{sid}" not in L:
                fail(f"missing stat.{tpl}.{sid}")
    for k in ("active", "done", "failed"):
        for prefix in ("change.quest.", "ui.quest."):
            if prefix + k not in L:
                fail(f"missing {prefix}{k}")
    for k in re.findall(r"key: 'change\.(\w+)'", code):
        if f"change.{k}" not in L:
            fail(f"missing change.{k}")
    return used


def draw_icon(path, kind, size):
    from PIL import Image, ImageDraw

    scale = 4
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink = (224, 168, 90, 255)
    if kind == "dice":
        pad = s * 0.14
        d.rounded_rectangle([pad, pad, s - pad, s - pad], radius=s * 0.16, outline=ink, width=int(s * 0.07))
        r = s * 0.065
        for cx, cy in ((0.33, 0.33), (0.5, 0.5), (0.67, 0.67), (0.67, 0.33), (0.33, 0.67)):
            d.ellipse([cx * s - r, cy * s - r, cx * s + r, cy * s + r], fill=ink)
    else:  # journal: a scroll with lines
        w = int(s * 0.07)
        d.rounded_rectangle([s * 0.22, s * 0.14, s * 0.78, s * 0.86], radius=s * 0.08, outline=ink, width=w)
        for y in (0.36, 0.5, 0.64):
            d.line([s * 0.34, y * s, s * 0.66, y * s], fill=ink, width=w)
        d.ellipse([s * 0.62, s * 0.68, s * 0.84, s * 0.9], fill=ink)
    img = img.resize((size, size), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def draw_cover(path):
    from PIL import Image, ImageDraw

    w, h = 1024, 1024
    img = Image.new("RGB", (w, h), (28, 24, 20))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        d.line([0, y, w, y], fill=(int(46 - 18 * k), int(36 - 14 * k), int(28 - 10 * k)))
    # Compass rose
    cx, cy = w / 2, h / 2
    gold = (224, 168, 90)
    for r, width in ((360, 6), (300, 3)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=gold, width=width)
    for i in range(16):
        a = i * math.pi / 8
        long_ray = i % 2 == 0
        r1 = 300 if long_ray else 220
        r0 = 70
        tip = (cx + r1 * math.cos(a), cy + r1 * math.sin(a))
        left = (cx + r0 * math.cos(a + 0.35), cy + r0 * math.sin(a + 0.35))
        right = (cx + r0 * math.cos(a - 0.35), cy + r0 * math.sin(a - 0.35))
        d.polygon([tip, left, (cx, cy), right], fill=gold if long_ray else (150, 110, 60))
    d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=(28, 24, 20), outline=gold, width=6)
    img.save(path, optimize=True)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
    check_manifest(manifest)
    write_locales()

    core = (SRC / "core.js").read_text(encoding="utf-8")
    entry_main = (SRC / "entry.main.js").read_text(encoding="utf-8")
    panel_main = (SRC / "panel.main.js").read_text(encoding="utf-8")
    check_code_keys(core + entry_main + panel_main)

    (OUT / "entry.js").write_text(core + "\n" + entry_main, encoding="utf-8")
    html = (SRC / "panel.html").read_text(encoding="utf-8")
    css = (SRC / "panel.css").read_text(encoding="utf-8")
    for marker, value in (("/*@@CSS@@*/", css), ("/*@@CORE@@*/", core), ("/*@@PANEL@@*/", panel_main)):
        if marker not in html:
            fail(f"panel.html is missing {marker}")
        html = html.replace(marker, value)
    if "</script" in (core + panel_main).replace("</script>\n", ""):
        fail("inlined script contains </script")
    (OUT / "ui").mkdir()
    (OUT / "ui" / "panel.html").write_text(html, encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    draw_icon(OUT / "icons" / "dice.png", "dice", 128)
    draw_icon(OUT / "icons" / "journal.png", "journal", 128)
    draw_cover(OUT / "cover.png")

    DIST.mkdir(exist_ok=True)
    tpg = DIST / f"adventure-journal-{manifest['version']}.tpg"
    if tpg.exists():
        tpg.unlink()
    with zipfile.ZipFile(tpg, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(OUT.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(OUT).as_posix())
    print(f"built {tpg.relative_to(ROOT)} ({tpg.stat().st_size // 1024} KB)")
    for f in sorted(OUT.rglob("*")):
        if f.is_file():
            print("  ", f.relative_to(OUT).as_posix(), f.stat().st_size)


if __name__ == "__main__":
    main()
