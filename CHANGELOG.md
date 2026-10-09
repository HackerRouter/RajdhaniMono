# Changelog

## 0.2 — 2026-10-09

- Reduce the fixed character advance from 560 to 520 units, approximately 7.1%.
- Reduce minimum side margins from 40 to 20 units while preserving Latin letter sizes.
- Match underscore thickness to each weight's horizontal stroke: 30, 44, 61, 80, and 102 units.
- Synchronize text-decoration thickness metadata with the underscore outline.
- Recenter the custom `I/l/1` outlines and combining-accent anchors in the narrower cell.
- Adapt terminal symbols to the new cell width and regenerate TrueType hints.
- Validate all five TTF and five WOFF2 files with shaping, rasterization, Fontconfig, and OpenType Sanitizer checks.

## 0.1 — 2026-10-09

- Create five static weights from Rajdhani with a 560-unit fixed advance.
- Redesign `I/l/1` for distinct forms and add a centre dot to zero.
- Preserve the upright stems of `m/M` while narrowing their counters.
- Add terminal, block, arrow, mathematical, and Powerline symbols from JetBrains Mono.
- Add fourteen combining accents and the Romanian `Ț/ț` pair.
- Provide installable TTF fonts, WOFF2 webfonts, offline specimens, and pinned source inputs.
