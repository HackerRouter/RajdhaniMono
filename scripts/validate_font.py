#!/usr/bin/env python3
"""Independent structural, shaping, rasterizer, and sanitizer checks."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import subprocess
import unicodedata

import freetype
from fontTools.ttLib import TTFont
import uharfbuzz as hb

CELL = 520
ZERO_WIDTH = {0x0300, 0x0301, 0x0302, 0x0303, 0x0304, 0x0306,
              0x0307, 0x0308, 0x030A, 0x030B, 0x030C, 0x0326,
              0x0327, 0x0328, 0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}
STYLES = {"Light": 300, "Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700}


def shape(font_bytes, text):
    font = hb.Font(hb.Face(font_bytes))
    font.scale = (1000, 1000)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, "calt": True})
    return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]


def check(root, style, weight, ots, require_fontconfig=False):
    path = root / "fonts/ttf" / f"RajdhaniMono-{style}.ttf"
    font_bytes = path.read_bytes()
    f = TTFont(path, checkChecksums=2)
    cmap, glyphs = f.getBestCmap(), f["glyf"]
    assert f["head"].unitsPerEm == 1000
    assert f["OS/2"].version >= 4 and f["OS/2"].fsSelection & 128
    assert f["OS/2"].usWeightClass == weight
    assert f["post"].isFixedPitch == 1 and f["OS/2"].panose.bProportion == 9
    assert f["OS/2"].xAvgCharWidth == CELL
    assert f["hhea"].advanceWidthMax == CELL
    assert f["hhea"].ascent == 930 and f["hhea"].descent == -270
    assert f["hhea"].lineGap == f["OS/2"].sTypoLineGap == 0
    assert {ord(c) for c in "Il1O0MWmw"}.issubset(cmap)
    assert set(range(0x20, 0x7F)).issubset(cmap)
    assert set(range(0x2500, 0x25A0)).issubset(cmap)
    assert {0x0218, 0x0219, 0x021A, 0x021B}.issubset(cmap)
    assert not any(0x0900 <= cp <= 0x097F for cp in cmap)
    assert not any(unicodedata.east_asian_width(chr(cp)) in ("W", "F") for cp in cmap)
    for cp, name in cmap.items():
        expected = 0 if cp in ZERO_WIDTH else CELL
        assert f["hmtx"][name][0] == expected, (hex(cp), name, f["hmtx"][name])
        g = glyphs[name]
        if g.numberOfContours:
            assert g.yMin >= -270 and g.yMax <= 930, (name, g.yMin, g.yMax)
            if expected:
                assert 0 <= g.xMin <= g.xMax <= CELL, (name, g.xMin, g.xMax)
            assert f["hmtx"][name][1] == g.xMin, (name, "incorrect lsb")
    # Preserve the upright stems while narrowing m's counters.
    original = TTFont(root / "sources/rajdhani" / f"Rajdhani-{style}.ttf")
    def stems(g):
        xs = sorted({a[0] for a, b in zip(g.coordinates, list(g.coordinates)[1:])
                     if a[0] == b[0] and abs(a[1]-b[1]) > 200})
        return [b-a for a, b in zip(xs[::2], xs[1::2])]
    # Underscore and text-decoration metadata follow the original horizontal stroke.
    underline = glyphs[cmap[ord("_")]]
    hyphen = original["glyf"]["hyphen"]
    thickness = underline.yMax-underline.yMin
    assert thickness == max(30, hyphen.yMax-hyphen.yMin)
    assert f["post"].underlineThickness == thickness
    assert underline.xMin == 0 and underline.xMax == CELL
    for n in ["m", "M"]:
        assert stems(original["glyf"][n]) == stems(glyphs[n]), (n, "stem compression")
    ascii_text = "".join(chr(cp) for cp in range(0x20, 0x7F))
    shaped = shape(font_bytes, ascii_text)
    assert len(shaped) == 95 and all(g and advance == CELL and not x and not y
                                    for g, advance, x, y in shaped)
    samples = ["-> => != == === !== <= >= fi ffi AV To",
               "MWmw Il1 O0 @#% 0123456789",
               "┌────┬────┐│░▒▓█│└────┴────┘",
               "╔════╦════╗║▄▀▌▐║╚════╩════╝",
               "←↑→↓ ↔ ⇒ ∀ ∃ ∑ ∞ ∈ √ ∩ ∪ ≤ ≥ ≠",
               "café naïve Ångström Țară Știință",
               "Ī Í Ì Î Ï Ĩ Į İ ĺ ľ"]
    for text in samples:
        s = shape(font_bytes, text)
        assert sum(a for _, a, _, _ in s) == len(text)*CELL, text
        assert all(g for g, _, _, _ in s), (text, "missing glyph")
    for text in ["café naïve Ångström Țară Știință", "Ī Í Ì Î Ï Ĩ Į İ ĺ ľ"]:
        assert shape(font_bytes, text) == shape(font_bytes, unicodedata.normalize("NFD", text))
    for text in ["x\u0301", "b\u0302", "j\u0301", "I\u0301", "a\u0326"]:
        s = shape(font_bytes, text)
        assert sum(a for _, a, _, _ in s) == CELL and all(g for g, _, _, _ in s), text
        if len(s) > 1:
            assert s[-1][1] == 0 and s[-1][2] == -CELL//2, (text, s)
    for text in ["a\u200Bb", "a\u200Cb", "a\u200Db", "a\u2060b", "a\uFEFFb"]:
        assert sum(a for _, a, _, _ in shape(font_bytes, text)) == 2*CELL
    # Full blocks meet the exact ascent, descent, and adjacent cell edges.
    g = glyphs[cmap[0x2588]]
    assert (g.xMin, g.yMin, g.xMax, g.yMax) == (0, -270, CELL, 930)
    horizontal, vertical = glyphs[cmap[0x2500]], glyphs[cmap[0x2502]]
    assert horizontal.xMin == 0 and horizontal.xMax == CELL
    assert vertical.yMin == -270 and vertical.yMax == 930
    # Rasterize every encoded glyph at actual small and larger screen sizes.
    face = freetype.Face(str(path))
    rasterized = 0
    for size in [12, 16, 20, 32]:
        face.set_pixel_sizes(0, size)
        for cp in cmap:
            face.load_char(cp, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
            rasterized += 1
    web_path = root / "fonts/woff2" / f"RajdhaniMono-{style}.woff2"
    web = TTFont(web_path, checkChecksums=2)
    assert web.getBestCmap() == cmap and web["hmtx"].metrics == f["hmtx"].metrics
    fc_scan = shutil.which("fc-scan")
    fontconfig_spacing = None
    if fc_scan:
        fc = subprocess.check_output([fc_scan, "--format", "%{spacing}", str(path)], text=True)
        assert fc.strip() == "100", (style, fc)
        fontconfig_spacing = 100
    elif require_fontconfig:
        raise RuntimeError("fc-scan is required for this check; install Fontconfig first")
    sanitizers = []
    if ots:
        for p in [path, web_path]:
            result = subprocess.run([str(ots), str(p)], capture_output=True, text=True)
            assert result.returncode == 0, (p.name, result.stdout, result.stderr)
            sanitizers.append({"file": p.name, "result": "passed"})
    return {"style": style, "weight": weight, "codepoints": len(cmap),
            "glyphs": len(f.getGlyphOrder()), "cell_advance": CELL,
            "ascii_shaping": "95/95 fixed advances, zero positioning offsets",
            "fontconfig_spacing": fontconfig_spacing, "nfc_nfd": "passed", "stem_preservation": "passed",
            "terminal_cell_edges": "passed", "underscore_thickness": thickness, "rasterized_glyph_sizes": rasterized,
            "raster_sizes_px": [12, 16, 20, 32], "woff2_roundtrip": "passed",
            "ots": sanitizers, "sha256": hashlib.sha256(font_bytes).hexdigest()}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--ots", type=Path)
    p.add_argument("--require-fontconfig", action="store_true",
                   help="Fail rather than skip if fc-scan is unavailable")
    args = p.parse_args()
    root = args.root.resolve()
    data = {"release": "0.2", "date": "2026-10-09",
            "status": "passed", "tests": [check(root, s, w, args.ots, args.require_fontconfig) for s, w in STYLES.items()]}
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports/validation.json").write_text(json.dumps(data, indent=2)+"\n")
    print(f"PASS: {len(data['tests'])} weights, "
          f"{sum(x['rasterized_glyph_sizes'] for x in data['tests'])} glyph rasterizations")


if __name__ == "__main__":
    main()
