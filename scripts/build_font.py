#!/usr/bin/env python3
"""Build the unofficial, Latin-focused Rajdhani Mono v0.2 family.

Font software and this build recipe are distributed under SIL OFL 1.1.
All upstream inputs are pinned and hashed in sources/manifest.json.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unicodedata

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.O_S_2f_2 import Panose
from fontTools.ttLib.removeOverlaps import removeOverlaps
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

UPM = 1000
CELL = 520
ASCENT, DESCENT = 930, -270
MARGIN = 20
STYLES = {"Light": 300, "Regular": 400, "Medium": 500,
          "SemiBold": 600, "Bold": 700}
BOX_DONORS = {"Light": "Thin", "Regular": "ExtraLight", "Medium": "Light",
              "SemiBold": "Regular", "Bold": "Bold"}
MARKS = {
    0x0300: "grave", 0x0301: "acute", 0x0302: "circumflex",
    0x0303: "tilde", 0x0304: "macron", 0x0306: "breve",
    0x0307: "dotaccent", 0x0308: "dieresis", 0x030A: "ring",
    0x030B: "hungarumlaut", 0x030C: "caron",
    0x0326: "commaaccent", 0x0327: "cedilla", 0x0328: "ogonek",
}
CONTROLS = {0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}
DONOR_RANGES = [(0x2190, 0x21FF), (0x2200, 0x22FF), (0x2300, 0x23FF),
                (0x2500, 0x25FF), (0x27E6, 0x27E7), (0x2B00, 0x2BFF),
                (0xE0A0, 0xE0A3), (0xE0B0, 0xE0B3)]


def flatten(font, name):
    glyphset = font.getGlyphSet()
    recording = DecomposingRecordingPen(glyphset)
    glyphset[name].draw(recording)
    pen = TTGlyphPen(None)
    recording.replay(pen)
    return pen.glyph()


def bounds(glyph):
    if not glyph.numberOfContours:
        return None
    glyph.recalcBounds(None)
    return glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax


def transform(glyph, sx=1, sy=1, dx=0, dy=0, clamp=False):
    out = copy.deepcopy(glyph)
    if out.numberOfContours:
        out.coordinates = type(out.coordinates)([
            (min(CELL, max(0, x*sx+dx)) if clamp else x*sx+dx,
             min(ASCENT, max(DESCENT, y*sy+dy)) if clamp else y*sy+dy)
            for x, y in out.coordinates])
        out.coordinates.toInt()
        out.recalcBounds(None)
    return out


def piecewise(x, knots):
    for (a, b), (c, d) in zip(knots, knots[1:]):
        if x <= c:
            return b+(x-a)*(d-b)/(c-a)
    a, b = knots[-2]
    c, d = knots[-1]
    return d+(x-c)*(d-b)/(c-a)


def fit_latin(glyph, name):
    b = bounds(glyph)
    if not b:
        return glyph
    lo, _, hi, _ = b
    ink = hi-lo
    target = CELL-2*MARGIN
    # Compress the counters of m/M while retaining the upright stem widths.
    # Detect upright stems from long vertical segments in the original outlines.
    if name in ("m", "M") and ink > target:
        verticals = sorted({a[0] for a, b in zip(glyph.coordinates,
                                               list(glyph.coordinates)[1:])
                            if a[0] == b[0] and abs(a[1]-b[1]) > 200})
        assert len(verticals) == (6 if name == "m" else 4), (name, verticals)
        windows = list(zip(verticals[::2], verticals[1::2]))
        assert windows[0][0] == lo and windows[-1][1] == hi, (name, windows)
        protected = sum(b-a for a, b in windows)
        gaps = sum(windows[i+1][0]-windows[i][1] for i in range(len(windows)-1))
        gap_scale = (target-protected)/gaps
        assert 0 < gap_scale < 1, (name, gap_scale)
        knots, cursor = [], MARGIN
        for i, (a, b) in enumerate(windows):
            if i:
                cursor += (a-windows[i-1][1])*gap_scale
            knots += [(a, cursor), (b, cursor+b-a)]
            cursor += b-a
        out = copy.deepcopy(glyph)
        out.coordinates = type(out.coordinates)([(piecewise(x, knots), y)
                                                 for x, y in out.coordinates])
        out.coordinates.toInt()
        out.recalcBounds(None)
        return out
    scale = min(1.0, target/ink) if ink else 1
    return transform(glyph, sx=scale, dx=(CELL-ink*scale)/2-lo*scale)


def rect(pen, x0, y0, x1, y1, radius=0):
    r = min(radius, (x1-x0)/2, (y1-y0)/2)
    pen.moveTo((x0+r, y0))
    pen.lineTo((x0, y0+r)) if not r else pen.qCurveTo((x0, y0), (x0, y0+r))
    pen.lineTo((x0, y1-r))
    pen.lineTo((x0+r, y1)) if not r else pen.qCurveTo((x0, y1), (x0+r, y1))
    pen.lineTo((x1-r, y1))
    pen.lineTo((x1, y1-r)) if not r else pen.qCurveTo((x1, y1), (x1, y1-r))
    pen.lineTo((x1, y0+r))
    pen.lineTo((x1-r, y0)) if not r else pen.qCurveTo((x1, y0), (x1-r, y0))
    pen.closePath()


def edited_glyph(existing, draw):
    pen = TTGlyphPen(None)
    if existing:
        existing.draw(pen, None)
    draw(pen)
    return pen.glyph()


def make_dotless_j(glyph):
    out = copy.deepcopy(glyph)
    coords, flags, ends = [], [], []
    start = 0
    for end in out.endPtsOfContours:
        points = list(out.coordinates[start:end+1])
        if min(y for x, y in points) < 510:
            coords.extend(points)
            flags.extend(out.flags[start:end+1])
            ends.append(len(coords)-1)
        start = end+1
    out.coordinates = type(out.coordinates)(coords)
    out.flags = type(out.flags)("B", flags)
    out.endPtsOfContours = ends
    out.numberOfContours = len(ends)
    out.recalcBounds(None)
    return out


def build_style(root, style, weight):
    source = TTFont(root / "sources/rajdhani" / f"Rajdhani-{style}.ttf")
    donor = TTFont(root / "sources/jetbrains-mono" / f"JetBrainsMono-{style}.ttf")
    box = TTFont(root / "sources/jetbrains-mono" / f"JetBrainsMono-{BOX_DONORS[style]}.ttf")
    original = source.getBestCmap()
    cmap = {cp: name for cp, name in original.items()
            if not 0x0900 <= cp <= 0x097F and cp < 0xE000}
    glyphs = {".notdef": fit_latin(flatten(source, ".notdef"), ".notdef")}
    metrics = {".notdef": (CELL, bounds(glyphs[".notdef"])[0])}
    raw = {}
    for cp, name in cmap.items():
        if name in glyphs:
            continue
        raw[name] = flatten(source, name)
        glyphs[name] = fit_latin(raw[name], name)
        b = bounds(glyphs[name])
        metrics[name] = (0 if cp in CONTROLS else CELL, b[0] if b else 0)

    stem = bounds(raw["I"])[2]-bounds(raw["I"])[0]
    radius = min(10, stem/5)
    center = CELL/2
    # Match horizontal stroke weight instead of using one thickness for every style.
    hyphen_box = bounds(raw["hyphen"])
    underline_thickness = max(30, hyphen_box[3]-hyphen_box[1])
    underline_bottom = -81-underline_thickness//2
    underline_top = underline_bottom+underline_thickness
    # New rails for I; a flagged top and foot for l; foot for 1; dotted 0.
    glyphs["I"] = edited_glyph(glyphs["I"], lambda p: (
        rect(p, center-160, 0, center+160, stem, radius),
        rect(p, center-160, 643-stem, center+160, 643, radius)))
    glyphs["l"] = edited_glyph(None, lambda p: (
        rect(p, CELL/2-stem/2, 0, CELL/2+stem/2, 703, radius),
        rect(p, center-130, 703-stem, center+stem/2, 703, radius),
        rect(p, center-stem/2, 0, center+130, stem, radius)))
    one = raw["one"]
    # The long right edge belongs to the numeral's upright stem.
    right = bounds(one)[2]
    one = transform(one, dx=CELL/2-(right-stem/2))
    glyphs["one"] = edited_glyph(one, lambda p: rect(p, center-160, 0, center+160, stem, radius))
    r = max(19, stem*0.42)
    def dot(p):
        cx, cy = CELL/2, 643/2
        p.moveTo((cx+r, cy))
        p.qCurveTo((cx+r, cy-r), (cx, cy-r))
        p.qCurveTo((cx-r, cy-r), (cx-r, cy))
        p.qCurveTo((cx-r, cy+r), (cx, cy+r))
        p.qCurveTo((cx+r, cy+r), (cx+r, cy))
        p.closePath()
    glyphs["zero"] = edited_glyph(glyphs["zero"], dot)
    glyphs["underscore"] = edited_glyph(None, lambda p: rect(p, 0, underline_bottom, CELL, underline_top))

    added_donors = []
    for a, b in DONOR_RANGES:
        for cp in range(a, b+1):
            if cp in cmap:
                continue
            # A single-cell font must not claim Unicode wide characters.
            if unicodedata.east_asian_width(chr(cp)) in ("W", "F"):
                continue
            font = box if 0x2500 <= cp <= 0x259F else donor
            donor_name = font.getBestCmap().get(cp)
            if not donor_name:
                continue
            name = f"donor{cp:04X}"
            g = flatten(font, donor_name)
            if 0x2500 <= cp <= 0x259F or 0xE0B0 <= cp <= 0xE0B3:
                # Donor endpoints extend beyond its cell to resist seams.
                # Clip to our exact cell for predictable terminal metrics.
                g = transform(g, sx=CELL/600, sy=(ASCENT-DESCENT)/1320,
                              dy=DESCENT+300*(ASCENT-DESCENT)/1320, clamp=True)
            elif 0xE0A0 <= cp <= 0xE0A3:
                g = transform(g, sx=CELL/600, sy=(ASCENT-DESCENT)/1320,
                              dy=DESCENT+300*(ASCENT-DESCENT)/1320)
            else:
                g = fit_latin(g, name)
                # Align borrowed arrows and operators with Rajdhani's cap centre.
                g = transform(g, sy=643/730)
            glyphs[name], cmap[cp] = g, name
            bnd = bounds(g)
            metrics[name] = (CELL, bnd[0] if bnd else 0)
            added_donors.append(cp)

    for cp in CONTROLS:
        name = cmap.get(cp, f"control{cp:04X}")
        cmap[cp], glyphs[name], metrics[name] = name, TTGlyphPen(None).glyph(), (0, 0)

    top_marks, bottom_marks = [], []
    for cp, source_name in MARKS.items():
        name = f"comb{cp:04X}"
        g = flatten(source, source_name)
        b = bounds(g)
        g = transform(g, dx=-(b[0]+b[2])/2)
        glyphs[name], cmap[cp], metrics[name] = g, name, (0, bounds(g)[0])
        (bottom_marks if cp >= 0x0326 else top_marks).append(name)

    # Carry the redesigned I/l through their precomposed accented forms.
    for cp, name in list(cmap.items()):
        decomp = unicodedata.normalize("NFD", chr(cp))
        if len(decomp) < 2 or decomp[0] not in ("I", "l"):
            continue
        if not all(ord(c) in MARKS for c in decomp[1:]):
            continue
        base_name = cmap[ord(decomp[0])]
        g = glyphs[base_name]
        for char in decomp[1:]:
            mark_cp = ord(char)
            shift_y = 0 if mark_cp >= 0x0326 else (133 if decomp[0] == "I" else 193)
            mark = transform(glyphs[f"comb{mark_cp:04X}"], dx=CELL/2, dy=shift_y)
            g = edited_glyph(g, lambda p, m=mark: m.draw(p, None))
        glyphs[name] = g

    # Complete the missing Romanian T/t comma-below pair using original outlines.
    for cp, base in [(0x021A, "T"), (0x021B, "t")]:
        name = f"uni{cp:04X}"
        below = transform(glyphs["comb0326"], dx=CELL/2)
        glyphs[name] = edited_glyph(glyphs[base], lambda p, g=below: g.draw(p, None))
        cmap[cp], metrics[name] = name, (CELL, bounds(glyphs[name])[0])

    glyphs["dotlessj"] = make_dotless_j(glyphs["j"])
    metrics["dotlessj"] = (CELL, bounds(glyphs["dotlessj"])[0])
    for name, g in glyphs.items():
        b = bounds(g)
        metrics[name] = (metrics[name][0], b[0] if b else 0)

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(list(glyphs))
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT, lineGap=0)
    family = "Rajdhani Mono"
    display_style = "SemiBold" if style == "SemiBold" else style
    legacy_family = family if style in ("Regular", "Bold") else f"{family} {display_style}"
    names = {
        "familyName": legacy_family,
        "styleName": "Bold" if style == "Bold" else "Regular",
        "typographicFamily": family, "typographicSubfamily": display_style,
        "uniqueFontIdentifier": f"0.200;RJMO;RajdhaniMono-{style}",
        "fullName": f"{family} {display_style}", "psName": f"RajdhaniMono-{style}",
        "version": "Version 0.200",
        "copyright": "Copyright (c) 2014 Indian Type Foundry. "
                     "Copyright 2020 The JetBrains Mono Project Authors. "
                     "Copyright 2026 Rajdhani Mono contributors.",
        "manufacturer": "Rajdhani Mono contributors (unofficial derivative)",
        "designer": "Original Rajdhani: Satya Rajpurohit, Jyotish Sonowal, "
                    "Shiva Nalleperumal. Terminal symbol outlines: JetBrains Mono Project Authors.",
        "description": "Unofficial Latin-focused, compact monospace derivative of Rajdhani. "
                       "520-unit cells; dotted zero; distinct I/l/1; terminal symbols. "
                       "Devanagari, CJK and Nerd Font icon sets are not included.",
        "licenseDescription": "SIL Open Font License, Version 1.1. See bundled OFL.txt and upstream notices.",
        "licenseInfoURL": "https://openfontlicense.org/",
    }
    fb.setupNameTable(names)
    panose = Panose()
    panose.bFamilyType, panose.bSerifStyle = 2, 11
    panose.bWeight, panose.bProportion = {300: 3, 400: 5, 500: 6, 600: 7, 700: 8}[weight], 9
    fb.setupOS2(version=4, sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0,
                usWinAscent=ASCENT, usWinDescent=-DESCENT, usWeightClass=weight,
                usWidthClass=5, xAvgCharWidth=CELL, sxHeight=510, sCapHeight=643,
                fsSelection=(1 << 7) | ((1 << 5) if style == "Bold" else (1 << 6)),
                achVendID="RJMO", fsType=0, panose=panose)
    fb.setupPost(isFixedPitch=1, italicAngle=0, underlinePosition=-81,
                 underlineThickness=underline_thickness, keepGlyphNames=True)
    fb.setupMaxp()
    fb.setupHead(fontRevision=0.200, macStyle=1 if style == "Bold" else 0,
                 created=3874348800, modified=3874348800)
    font = fb.font
    # Combine the new rails with stems without overlapping contours.
    removeOverlaps(font, glyphNames=["I", "l", "one", "zero"], removeHinting=True)
    features = ["languagesystem DFLT dflt;", "languagesystem latn dflt;"]
    features += [f"markClass {n} <anchor 0 0> @TOP;" for n in top_marks]
    features += [f"markClass {n} <anchor 0 0> @BOTTOM;" for n in bottom_marks]
    features += ["feature ccmp {",
                 f"  sub i' [{' '.join(top_marks)}] by dotlessi;",
                 f"  sub j' [{' '.join(top_marks)}] by dotlessj;", "} ccmp;",
                 "feature mark {"]
    seen = set()
    for cp, name in cmap.items():
        if name in seen or not unicodedata.category(chr(cp)).startswith("L"):
            continue
        seen.add(name)
        decomposed = unicodedata.normalize("NFD", chr(cp))
        base = original.get(ord(decomposed[0]), name)
        ymax = bounds(raw[base])[3] if base in raw and bounds(raw[base]) else 510
        anchor_y = max(0, ymax-510)
        features.append(f"  pos base {name} <anchor {CELL//2} {anchor_y}> mark @TOP "
                        f"<anchor {CELL//2} 0> mark @BOTTOM;")
    features += [f"  pos base dotlessj <anchor {CELL//2} 0> mark @TOP <anchor {CELL//2} 0> mark @BOTTOM;",
                 "} mark;"]
    addOpenTypeFeaturesFromString(font, "\n".join(features))
    font.recalcTimestamp = False
    font["OS/2"].recalcUnicodeRanges(font)
    unhinted = root / "build" / f"RajdhaniMono-{style}-unhinted.ttf"
    font.save(unhinted)
    output = root / "fonts/ttf" / f"RajdhaniMono-{style}.ttf"
    subprocess.run([sys.executable, "-m", "ttfautohint", "-n", "-l", "8", "-r", "36",
                    "-G", "50", "-D", "latn", "-a", "qsq", str(unhinted), str(output)], check=True)
    hinted = TTFont(output)
    hinted.recalcTimestamp = False
    hinted["head"].created = hinted["head"].modified = 3874348800
    # The unencoded ttfautohint helper is empty but still participates in metrics.
    for name, (advance, lsb) in list(hinted["hmtx"].metrics.items()):
        if name not in glyphs:
            hinted["hmtx"].metrics[name] = (CELL, lsb)
    hinted["OS/2"].xAvgCharWidth = CELL
    hinted.save(output)
    hinted.flavor = "woff2"
    hinted.save(root / "fonts/woff2" / f"RajdhaniMono-{style}.woff2")
    print(f"{style}: {len(cmap)} codepoints; {len(hinted.getGlyphOrder())} glyphs; "
          f"{len(added_donors)} borrowed symbols; {CELL}/{UPM} em")
    return {"style": style, "weight": weight, "codepoints": len(cmap),
            "glyphs": len(hinted.getGlyphOrder()), "borrowed_symbol_count": len(added_donors),
            "box_donor": BOX_DONORS[style], "advance": CELL,
            "underscore_thickness": underline_thickness}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / "sources/manifest.json").read_text())
    for record in manifest["files"]:
        path = root / record["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], path
    for p in ["build", "fonts/ttf", "fonts/woff2", "reports"]:
        (root / p).mkdir(parents=True, exist_ok=True)
    results = [build_style(root, style, weight) for style, weight in STYLES.items()]
    (root / "reports/build-summary.json").write_text(json.dumps(results, indent=2)+"\n")


if __name__ == "__main__":
    main()
