#!/bin/bash
# Build the delivery comparison sheets from the concept crops and the final renders.
# Usage: bash make-delivery-sheets.sh [render_dir]   (default renders/final)
set -euo pipefail
B="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
R="${1:-$B/renders/final}"
OUT="$B/renders/sheets"; mkdir -p "$OUT"
row() { # label ref render out
  magick "$2" -resize x600 "$OUT/_ref.png"; magick "$3" -resize x600 "$OUT/_ren.png"
  magick montage -label "REFERENCE $1" "$OUT/_ref.png" -label "RENDER $1" "$OUT/_ren.png" -tile 2x1 -geometry +8+8 -background gray20 -fill white -pointsize 22 "$4"
}
row "hero" "$B/reference/concept-crop-hero-graphite.png" "$R/hero-graphite.png" "$OUT/row-hero.png"
row "rear" "$B/reference/concept-crop-rear.png" "$R/rear-graphite.png" "$OUT/row-rear.png"
row "open" "$B/reference/concept-crop-open.png" "$R/open-graphite.png" "$OUT/row-open.png"
magick "$B/reference/concept-crop-hero-walnut.png" -resize x600 "$OUT/_ref.png"
magick -size 900x600 xc:gray30 -fill white -pointsize 28 -gravity center -annotate 0 "walnut variant not rendered\n(owner 2026-09-06: matte plastic only;\nWW_MAT_WALNUT preset kept in file)" "$OUT/_ren.png"
magick montage -label "REFERENCE walnut" "$OUT/_ref.png" -label "RENDER walnut" "$OUT/_ren.png" -tile 2x1 -geometry +8+8 -background gray20 -fill white -pointsize 22 "$OUT/row-walnut.png"
magick "$OUT/row-hero.png" "$OUT/row-walnut.png" "$OUT/row-rear.png" "$OUT/row-open.png" -append "$OUT/four-view-concept-comparison.png"
rm -f "$OUT/_ref.png" "$OUT/_ren.png" 
ls "$OUT"/*.png | head; find "$B/renders/contact" -name '*.png' | sort | xargs -I{} echo {} > /dev/null
if ls "$B"/renders/contact/*.png >/dev/null 2>&1; then
  magick montage $(ls "$B"/renders/contact/*.png | sort) -tile 4x -geometry 384x256+4+4 -background gray20 "$OUT/azimuth-underside-contact-sheet.png"
fi
echo "SHEETS_DONE $OUT"
