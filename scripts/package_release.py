#!/usr/bin/env python3
"""Create a redistributable release with licenses, provenance, and recipes."""
import argparse
import hashlib
from pathlib import Path
import zipfile

TOP_LEVEL = ["README.md", "README.en.md", "LICENSE", "OFL.txt", "NOTICE.txt",
             "CHANGELOG.md", "CONTRIBUTING.md", "requirements.txt", "VERSION"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    destination = args.out_dir.resolve() if args.out_dir else root / "dist"
    destination.mkdir(parents=True, exist_ok=True)
    version = (root / "VERSION").read_text().strip()
    prefix = f"RajdhaniMono-v{version}"
    paths = [root / name for name in TOP_LEVEL]
    for directory in ["fonts", "sources", "docs", "reports"]:
        paths.extend(p for p in (root / directory).rglob("*") if p.is_file())
    paths.extend((root / "scripts").glob("*.py"))
    paths = sorted(set(paths))
    if not all(p.is_file() for p in paths):
        raise RuntimeError("A required release file is missing")
    hashes = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}\n"
                     for p in paths)
    archive = destination / f"{prefix}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for relative, data in [(p.relative_to(root).as_posix(), p.read_bytes()) for p in paths] + [("SHA256SUMS", hashes.encode())]:
            info = zipfile.ZipInfo(f"{prefix}/{relative}", date_time=(2026, 10, 9, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, data, compresslevel=9)
    with zipfile.ZipFile(archive) as packaged:
        if packaged.testzip() is not None:
            raise RuntimeError("Release archive integrity check failed")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(f"{digest}  {archive.name}\n")
    print(f"Created {archive.name} ({archive.stat().st_size:,} bytes)")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
