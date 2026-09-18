#!/usr/bin/env python3
"""Copy the DC-01 R02 delivery media into this published folder at web sizes.

Stills and renders become progressive JPEG q88; vectors, STL, 3MF, CAD sources and
the two archives are copied as they are. Run from the repository root:

    python3 docs/reviews/dc-01/r02/build-media.py [--source builds/desktop-companion/delivery/R02]

Writes `media-manifest.json` next to the page: every published file with its byte
size and SHA-256, so the page's numbers stay traceable to the delivered bytes.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent  # holds the shared builders
OUT = None  # set from --out: the revision directory this run publishes into
JPEG_QUALITY = "88"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def to_jpeg(source, target, width):
    """Convert one PNG to a progressive JPEG bounded by `width` pixels."""
    target.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["magick", str(source), "-resize", f"{width}x{width}>", "-strip",
         "-interlace", "Plane", "-quality", JPEG_QUALITY, str(target)],
        capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"magick failed on {source}: {result.stderr.strip()}")
    return target


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="delivered package directory")
    parser.add_argument("--out", required=True, help="revision directory to publish into, e.g. docs/reviews/dc-01/r03")
    parser.add_argument("--renders", default=None,
                        help="directory holding the per-part clay renders (PNG)")
    args = parser.parse_args()

    global OUT
    OUT = Path(args.out).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    src = Path(args.source).resolve()
    if not src.is_dir():
        raise SystemExit(f"source package not found: {src}")
    renders = Path(args.renders).resolve() if args.renders else OUT / "parts-source"

    published = []

    # 1. Scene stills and the three detail views: 1920 px JPEG.
    for name in ["assembled", "exploded", "catalog", "button", "print-layout"]:
        published.append(to_jpeg(src / "stills" / f"{name}.png", OUT / "media" / f"{name}.jpg", 1920))
    for name in ["arm", "ear", "interior"]:
        published.append(to_jpeg(src / "stills" / "details" / f"{name}.png",
                                 OUT / "media" / f"detail-{name}.jpg", 1920))

    # 2. Electronics previews: schematic sheet and both copper layers, plus the vectors.
    for name in ["desktop-companion", "carrier-front", "carrier-back"]:
        published.append(to_jpeg(src / "electronics" / "previews" / f"{name}.png",
                                 OUT / "media" / f"pcb-{name}.jpg", 2200))
        published.append(copy(src / "electronics" / "previews" / f"{name}.svg",
                              OUT / "cad" / f"{name}.svg"))
    for name in ["desktop-companion-PTH-drl_map", "desktop-companion-NPTH-drl_map"]:
        published.append(copy(src / "electronics" / "fabrication-candidate" / f"{name}.svg",
                              OUT / "cad" / f"{name}.svg"))

    # 3. Print plates: the two verification renders and both core 3MF files.
    for name in ["plate-01-PETG", "plate-02-TPU"]:
        published.append(to_jpeg(src / "print" / "verification" / f"{name}.png",
                                 OUT / "media" / f"{name}.jpg", 1600))
        published.append(copy(src / "print" / "plates" / f"{name}.3mf", OUT / "print" / f"{name}.3mf"))

    # 4. One clay render and one STL per gated part.
    manifest = json.loads((src / "print" / "package-manifest.json").read_text())
    stl_dir = OUT / "stl"
    for part in manifest["parts"]:
        part_id = part["id"]
        published.append(to_jpeg(renders / f"{part_id}.png", OUT / "media" / "parts" / f"{part_id}.jpg", 1100))
        stl_source = src / "print" / part["stl"]
        if not stl_source.exists():  # the package keeps the STL set inside the kit archive
            stl_source = stl_dir / f"{part_id}.stl"
        published.append(copy(stl_source, stl_dir / f"{part_id}.stl"))

    # 5. Gerber X2 and Excellon candidates travel as one archive, unreleased for fabrication.
    gerber_zip = OUT / "cad" / "gerber-excellon.zip"
    gerber_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(gerber_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted((src / "electronics" / "fabrication-candidate").iterdir()):
            if item.is_file():
                archive.write(item, item.name)
    published.append(gerber_zip)

    # 6. Media, archives, CAD sources and the documents the page cites.
    published.append(copy(src / "dc01-native-animatic.mp4", OUT / "dc01-native-animatic.mp4"))
    published.append(copy(src / "DC01-P03-print-kit.zip", OUT / "DC01-P03-print-kit.zip"))
    for name in ["desktop-companion.kicad_sch", "desktop-companion.kicad_pcb",
                 "desktop-companion.kicad_pro", "desktop-companion.net", "DC.kicad_sym"]:
        published.append(copy(src / "electronics" / "cad" / name, OUT / "cad" / name))
    for name in ["README.md", "SHA256SUMS", "snapshot.json"]:
        published.append(copy(src / name, OUT / name))
    published.append(copy(src / "electronics" / "README.md", OUT / "electronics-README.md"))
    published.append(copy(src / "electronics" / "bench-validation.md", OUT / "bench-validation.md"))
    published.append(copy(src / "electronics" / "delivery-audit.json", OUT / "electronics-audit.json"))
    published.append(copy(src / "electronics" / "system-wiring.csv", OUT / "system-wiring.csv"))
    published.append(copy(src / "electronics" / "system-bom.csv", OUT / "system-bom.csv"))
    published.append(copy(src / "electronics" / "carrier-bom.csv", OUT / "carrier-bom.csv"))
    published.append(copy(src / "print" / "README.md", OUT / "print" / "README.md"))
    published.append(copy(src / "print" / "package-manifest.json", OUT / "print" / "package-manifest.json"))
    published.append(copy(src / "print" / "package-check.json", OUT / "print" / "package-check.json"))

    # Record the source as a repository-relative path: no machine path in a published file.
    try:
        source_label = str(src.relative_to(HERE.parents[2]))
    except ValueError:
        source_label = src.name

    records = []
    for path in published:
        records.append({
            "path": str(path.relative_to(OUT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    total = sum(r["bytes"] for r in records)
    (OUT / "media-manifest.json").write_text(json.dumps(
        {"source_package": source_label, "files": len(records), "bytes": total, "published": records},
        indent=1) + "\n")
    print(f"published {len(records)} files, {total / 1048576:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
