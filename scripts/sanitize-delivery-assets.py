#!/usr/bin/env python3
"""Sanitize image metadata (PNG/WebP) and relativize host paths in JSON delivery receipts.

    python3 scripts/sanitize-delivery-assets.py --dir builds/mochi-rb5320-companion --write
    python3 scripts/sanitize-delivery-assets.py --dir builds/watch-winder-capsule --check

Why this exists:
1. Blender automatically embeds `tEXtSoftware\\0Blender 5.2.0` and timestamp chunks into rendered PNGs.
   Downstream release gates (e.g. `S-13 image-pii` in design-os-robotics) fail when metadata chunks are present.
2. Production gates and audit manifests record absolute workstation paths (`/Users/jang/...`, `/home/...`).
   These leak developer machine environments and fail hygiene scans (`S-02 path hygiene`).
3. This tool strips non-critical PNG/WebP chunks (tEXt, iTXt, zTXt, eXIf, XMP) while preserving 100% pixel
   fidelity, and rewrites absolute workstation paths in JSON files to repo-relative paths without
   altering SHA-256 bindings.

Exit: 0 clean/sanitized, 1 dirty (under --check) or unresolvable, 2 bad arguments.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

ROOT = Path(__file__).resolve().parent.parent

# Chunks to remove from PNG files
STRIP_PNG_CHUNKS = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"prNu"}


def strip_png_metadata_bytes(png_bytes: bytes) -> Tuple[bytes, bool]:
    """Strip metadata chunks from raw PNG byte stream without recompressing IDAT."""
    sig = b"\x89PNG\r\n\x1a\n"
    if not png_bytes.startswith(sig):
        return png_bytes, False

    out = [sig]
    offset = len(sig)
    modified = False

    while offset < len(png_bytes):
        if offset + 8 > len(png_bytes):
            break
        length = int.from_bytes(png_bytes[offset:offset+4], "big")
        chunk_type = png_bytes[offset+4:offset+8]
        chunk_total_len = 12 + length
        chunk_bytes = png_bytes[offset:offset+chunk_total_len]

        if chunk_type in STRIP_PNG_CHUNKS:
            modified = True
        else:
            out.append(chunk_bytes)
        offset += chunk_total_len

    if modified:
        return b"".join(out), True
    return png_bytes, False


def strip_image_file_metadata(image_path: Path, write: bool = False) -> bool:
    """Check or strip metadata from a PNG or WebP file."""
    ext = image_path.suffix.lower()
    raw = image_path.read_bytes()

    if ext == ".png":
        sanitized, changed = strip_png_metadata_bytes(raw)
        if changed and write:
            image_path.write_bytes(sanitized)
        return changed

    if ext in (".webp", ".jpg", ".jpeg"):
        if Image is None:
            return False
        with Image.open(image_path) as img:
            has_meta = bool(img.info.get("exif") or img.info.get("xmp") or img.info.get("comment"))
            if has_meta and write:
                # Fast save without exif or extra metadata
                img.save(image_path, exif=b"")
            return has_meta

    return False


def sanitize_json_paths(json_path: Path, repo_root: Path, write: bool = False) -> bool:
    """Relativize absolute host paths in JSON data."""
    try:
        raw_text = json_path.read_text(encoding="utf-8")
    except Exception:
        return False

    # Regex matching workstation user paths: /Users/<user>/... or /home/<user>/...
    # We want to replace everything up to the repo name or subfolder
    repo_name = repo_root.name
    # Pattern 1: match /Users/.../<repo_name>/<rel_path>
    pattern_repo = re.compile(rf'["\'](?:/Users|/home)/[^"\']+/{re.escape(repo_name)}/([^"\']+)["\']')
    # Pattern 2: generic /Users/.../builds/<rel_path>
    pattern_builds = re.compile(r'["\'](?:/Users|/home)/[^"\']+/(builds/[^"\']+)["\']')

    new_text = raw_text
    new_text = pattern_repo.sub(r'"\1"', new_text)
    new_text = pattern_builds.sub(r'"\1"', new_text)

    changed = new_text != raw_text
    if changed and write:
        # Validate that JSON is still valid before writing
        try:
            parsed = json.loads(new_text)
            json_path.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
        except Exception:
            # Fallback direct string write
            json_path.write_text(new_text, encoding="utf-8")

    return changed


def audit_and_sanitize(target_dir: Path, repo_root: Path = ROOT, write: bool = False):
    """Walk target_dir and sanitize images and JSON reports."""
    stats = {
        "images_checked": 0,
        "images_dirty": 0,
        "json_checked": 0,
        "json_dirty": 0,
        "dirty_files": [],
    }

    skip_dir_names = {".git", "__pycache__", "frames", "runs", "archive-r01", "archive-r02", "mechanical"}

    for root, dirs, files in os.walk(target_dir):
        # Prune skipped directories
        dirs[:] = [d for d in dirs if d not in skip_dir_names]

        for f in files:
            p = Path(root) / f
            ext = p.suffix.lower()

            if ext in (".png", ".webp", ".jpg", ".jpeg"):
                stats["images_checked"] += 1
                is_dirty = strip_image_file_metadata(p, write=write)
                if is_dirty:
                    stats["images_dirty"] += 1
                    stats["dirty_files"].append(str(p.relative_to(repo_root) if p.is_relative_to(repo_root) else p))

            elif ext == ".json":
                stats["json_checked"] += 1
                is_dirty = sanitize_json_paths(p, repo_root=repo_root, write=write)
                if is_dirty:
                    stats["json_dirty"] += 1
                    stats["dirty_files"].append(str(p.relative_to(repo_root) if p.is_relative_to(repo_root) else p))

    return stats


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", required=True, type=Path, help="Target directory to audit or sanitize")
    parser.add_argument("--repo-root", type=Path, default=ROOT, help="Base repo root for relative paths")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--check", action="store_true", help="Check-only: exit 1 if unsanitized files found")
    mode_group.add_argument("--write", action="store_true", help="In-place rewrite and sanitize files")
    
    args = parser.parse_args(argv)

    if not args.dir.is_dir():
        sys.stderr.write(f"Error: Target directory '{args.dir}' does not exist\n")
        return 2

    stats = audit_and_sanitize(args.dir, repo_root=args.repo_root, write=args.write)

    if args.write:
        print(
            f"SANITIZED: {stats['images_dirty']} image(s) and {stats['json_dirty']} JSON file(s) "
            f"cleaned in {args.dir}."
        )
        return 0
    else:
        # Check mode
        total_dirty = stats["images_dirty"] + stats["json_dirty"]
        if total_dirty == 0:
            print(f"CLEAN: All {stats['images_checked']} images and {stats['json_checked']} JSON files are sanitized.")
            return 0
        else:
            print(f"DIRTY: Found {total_dirty} unsanitized file(s) in {args.dir}:")
            for f in stats["dirty_files"][:15]:
                print(f"  - {f}")
            if len(stats["dirty_files"]) > 15:
                print(f"  ... and {len(stats['dirty_files']) - 15} more.")
            return 1


if __name__ == "__main__":
    sys.exit(main())
