#!/usr/bin/env python3
"""Create offline HTML and raster specimens from the actual final font files."""
import base64
import argparse
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
root = parser.parse_args().root.resolve()
(root / "docs/images").mkdir(parents=True, exist_ok=True)
weights = {"Light": 300, "Regular": 400, "Medium": 500, "SemiBold": 600, "Bold": 700}
faces = []
for style, weight in weights.items():
    data = base64.b64encode((root / f"fonts/woff2/RajdhaniMono-{style}.woff2").read_bytes()).decode()
    faces.append(f"@font-face{{font-family:'Rajdhani Mono';font-style:normal;font-weight:{weight};"
                 f"src:url(data:font/woff2;base64,{data}) format('woff2');font-display:block;}}")
original = TTFont(root / "sources/rajdhani/Rajdhani-Regular.ttf")
original.flavor = "woff2"
buf = BytesIO()
original.save(buf)
data = base64.b64encode(buf.getvalue()).decode()
faces.append(f"@font-face{{font-family:'Rajdhani Original';font-weight:400;"
             f"src:url(data:font/woff2;base64,{data}) format('woff2');font-display:block;}}")
template = (root / "docs/templates/preview.html").read_text()
(root / "docs/preview.html").write_text(template.replace("__FONT_FACES__", "\n".join(faces)))

def font(style, size):
    return ImageFont.truetype(str(root / f"fonts/ttf/RajdhaniMono-{style}.ttf"), size)

bg, fg, muted, accent, surface = "#10171e", "#dfe8f1", "#a8b5c2", "#7de0cc", "#18222c"
image = Image.new("RGB", (1440, 1160), bg)
draw = ImageDraw.Draw(image)
draw.text((56, 34), "Rajdhani Mono", font=font("Medium", 80), fill=fg)
draw.text((60, 145), "v0.2   /   520-unit cells   /   5 weights   /   854 characters",
          font=ImageFont.load_default(size=22), fill=muted)
draw.text((60, 191), "MWmw  Il1  O0  @#%  0123456789", font=font("Regular", 60), fill=accent)
draw.line((60, 291, 1380, 291), fill="#344352", width=1)
draw.rounded_rectangle((56, 328, 956, 1028), radius=14, fill=surface)
draw.text((84, 350), "TERMINAL / MEDIUM 500 / 24 PX", font=ImageFont.load_default(size=19), fill=muted)
lines = ["~/projects/rajdhani-mono $ git status --short", " M build_font.py", "",
         "def normalize_width(text: str) -> int:",
         "    cells = [520 for char in text]", "    return sum(cells)", "",
         'const token = "Il1 | O0 | MWmw | {} [] ()";',
         "if (width !== 520 && count >= 0) {", "    console.log(`ready: ${count} glyphs`);", "}", "",
         "┌──────────────────────────────────────┐",
         "│ Rajdhani Mono   compact terminal     │",
         "├──────────────────────────────────────┤",
         "│ 0123456789  Il1  O0  MWmw  @#%       │",
         "│ → ← ↑ ↓ ↔ ⇒  ≤ ≥ ≠ ∑ ∞ √           │",
         "│ ░▒▓████████░░░░░░   56%              │",
         "└──────────────────────────────────────┘",
         "╔═══════════╦═══════════╗",
         "║  ABC xyz  ║  012 345  ║",
         "╚═══════════╩═══════════╝"]
lines = ["│"+line[1:-1].rstrip().ljust(38)+"│" if line.startswith("│") else line
         for line in lines]
for line in lines:
    if line.startswith("│"):
        assert len(line) == 40, (len(line), line)
for i, line in enumerate(lines):
    # Anchor each line to the font's real ascent/descent; no inserted row gaps.
    draw.text((86, 394+i*28.8), line, font=font("Medium", 24), fill=fg)
draw.text((1000, 350), "WEIGHT FAMILY", font=ImageFont.load_default(size=19), fill=muted)
for i, (style, weight) in enumerate(weights.items()):
    y = 390+i*116
    draw.text((1000, y), f"{style}  {weight}", font=ImageFont.load_default(size=17), fill=muted)
    draw.text((998, y+28), "Rajdhani", font=font(style, 42), fill=fg)
    draw.text((1000, y+78), "MWmw Il1 O0", font=font(style, 24), fill=accent)
draw.text((60, 1050), "Latin + terminal symbols. OFL 1.1. Unofficial derivative.",
          font=ImageFont.load_default(size=21), fill=muted)
draw.text((60, 1090), "Base: Indian Type Foundry / Rajdhani. Added symbols: JetBrains Mono.",
          font=ImageFont.load_default(size=19), fill=muted)
image.save(root / "docs/images/preview.png")

image = Image.new("RGB", (1440, 1330), "#f8f8f6")
draw = ImageDraw.Draw(image)
draw.text((45, 28), "Rajdhani Mono / native raster size checks", font=ImageFont.load_default(size=25), fill="#273441")
sample = "MWmw Il1 O0 0123456789 {} [] () <> / \\ _ | @#% fi ffi"
for i, size in enumerate([12, 16, 20, 32]):
    top = 100+i*298
    draw.text((45, top), f"{size} px", font=ImageFont.load_default(size=22), fill="#576574")
    for j, style in enumerate(weights):
        y = top+40+j*44
        draw.text((45, y), style, font=ImageFont.load_default(size=16), fill="#576574")
        draw.text((170, y), sample, font=font(style, size), fill="#273441")
image.save(root / "docs/images/size-check.png")
print("Preview HTML and two actual-font PNG specimens created")
