#!/usr/bin/env python3
"""CLI: generate a format-faithful Bambu-like .3mf fixture from repo-owned
STL geometry, plus a `.expected.json` ground-truth sidecar.

Usage:
    python3 make_bambu_like_fixture.py --out <file.3mf> --stl <a.stl>
        [--stl <b.stl> ...] [--plates N]

Deterministic: fixed timestamps/uuids/zip metadata mean two runs with the
same inputs produce byte-identical output (same sha256). stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# Running as a plain script (not `python -m`), so sys.path[0] is this
# directory -- flat imports of sibling modules work without a package.
from bambu_3mf_writer import write_fixture
from stl_reader import read_stl


def _sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="output .3mf path")
    parser.add_argument(
        "--stl", action="append", required=True, dest="stl_paths",
        help="path to a repo-owned STL file; repeat for multiple objects",
    )
    parser.add_argument(
        "--plates", type=int, default=1,
        help="number of plates; objects are assigned round-robin (default: 1)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    if args.plates < 1:
        print(f"error: --plates must be >= 1, got {args.plates}", file=sys.stderr)
        return 2

    stl_entries = []
    for stl_path_str in args.stl_paths:
        stl_path = Path(stl_path_str)
        if not stl_path.is_file():
            print(f"error: STL file not found: {stl_path}", file=sys.stderr)
            return 2
        try:
            vertices, triangles = read_stl(str(stl_path))
        except ValueError as exc:
            print(f"error: could not read STL {stl_path}: {exc}", file=sys.stderr)
            return 2
        stl_entries.append({
            "name": stl_path.stem,
            "vertices": vertices,
            "triangles": triangles,
            "source_path": str(stl_path),
            "source_sha256": _sha256_of(stl_path),
        })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    expected = write_fixture(str(out_path), stl_entries, args.plates)

    sidecar_path = out_path.with_suffix(out_path.suffix + ".expected.json")
    sidecar_path.write_text(json.dumps(expected, indent=1, sort_keys=True) + "\n")

    print(f"wrote {out_path} and {sidecar_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
