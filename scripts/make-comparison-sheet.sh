#!/bin/bash
# Compose a single side-by-side comparison sheet: REFERENCE | RENDER.
# The agent judges each build pass from exactly ONE sheet (img2threejs pattern).
# Usage: scripts/make-comparison-sheet.sh <reference.png> <render.png> [out.png]
set -euo pipefail

REF="${1:?Usage: make-comparison-sheet.sh <reference> <render> [out]}"
RENDER="${2:?Missing render image}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${3:-$ROOT/output/comparison-sheet.png}"

mkdir -p "$(dirname "$OUT")"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# Normalize both to equal height so the pair reads at a glance
magick "$REF"    -resize x720 "$TMP_DIR/ref.png"
magick "$RENDER" -resize x720 "$TMP_DIR/render.png"

montage -label 'REFERENCE' "$TMP_DIR/ref.png" \
        -label 'RENDER'    "$TMP_DIR/render.png" \
        -tile 2x1 -geometry +10+10 \
        -background gray20 -fill white -pointsize 28 \
        "$OUT"

echo "SHEET_DONE $OUT"
