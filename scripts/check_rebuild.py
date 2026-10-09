#!/usr/bin/env python3
"""Rebuild from pinned inputs and compare every distributed font byte."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args().root.resolve()
    (root / "build").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="repro-", dir=root / "build") as directory:
        target = Path(directory)
        shutil.copytree(root / "sources", target / "sources")
        subprocess.run([sys.executable, str(root / "scripts/build_font.py"),
                        "--root", str(target)], check=True)
        originals = sorted((root / "fonts").rglob("*.ttf")) + sorted((root / "fonts").rglob("*.woff2"))
        rebuilt = sorted((target / "fonts").rglob("*.ttf")) + sorted((target / "fonts").rglob("*.woff2"))
        if len(originals) != 10 or len(rebuilt) != 10:
            raise RuntimeError("Expected exactly five TTF and five WOFF2 files")
        for font in originals:
            other = target / font.relative_to(root)
            if font.read_bytes() != other.read_bytes():
                raise RuntimeError(f"Rebuild differs: {font.relative_to(root)}")
    print("PASS: all five TTF and five WOFF2 files rebuild byte-for-byte")


if __name__ == "__main__":
    main()
