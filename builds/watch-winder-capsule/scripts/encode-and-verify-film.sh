#!/bin/bash
# Encode renders/film/frames/frame_####.png -> renders/film/watch-winder-capsule-film-1080p.mp4 (24 fps, H.264 CRF 18)
# and verify: frame count, size, duration, decode errors, 12-frame contact sheet. Exit 1 on any mismatch.
set -uo pipefail
B="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FR="$B/renders/film/frames"; OUT="$B/renders/film/watch-winder-capsule-film-1080p.mp4"
EXPECT="${1:-385}"; FPS=24
n=$(ls "$FR"/frame_*.png 2>/dev/null | wc -l | tr -d ' ')
[[ "$n" == "$EXPECT" ]] || { echo "FRAME_COUNT_MISMATCH have=$n expect=$EXPECT"; exit 1; }
ffmpeg -hide_banner -loglevel error -y -framerate $FPS -start_number 1 -i "$FR/frame_%04d.png" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart "$OUT" || { echo "ENCODE_FAILED"; exit 1; }
read -r w h frames dur < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,nb_frames:format=duration -of csv=p=0 "$OUT" | tr ',\n' '  ')
dec_err=$(ffmpeg -v error -i "$OUT" -f null - 2>&1 | wc -l | tr -d ' ')
echo "VIDEO $OUT ${w}x${h} frames=$frames duration=${dur}s decode_errors=$dec_err sha256=$(shasum -a 256 "$OUT" | cut -c1-16)"
[[ "$frames" == "$EXPECT" && "$w" == "1920" && "$h" == "1080" && "$dec_err" == "0" ]] || { echo "VERIFY_FAILED"; exit 1; }
mkdir -p "$B/renders/film/check"
for f in 1 37 73 121 181 229 241 277 313 349 385; do
  ffmpeg -v error -y -i "$OUT" -vf "select=eq(n\,$((f-1)))" -vframes 1 "$B/renders/film/check/decoded_$(printf %04d $f).png"
done
magick montage "$B"/renders/film/check/decoded_*.png -tile 4x3 -geometry 480x270+4+4 -background gray20 "$B/renders/film/film-contact-sheet.png"
echo "FILM_VERIFIED $OUT"
