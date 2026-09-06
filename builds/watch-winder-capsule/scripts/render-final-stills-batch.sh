#!/usr/bin/env bash
# Render every final still as its own headless GPU job (one image per Blender process keeps
# each run short and resumable). Usage: bash render-final-stills-batch.sh [samples] [threshold]
# Log: renders/final/batch.log — last line per job is the AGENT_OK/AGENT_FAIL sentinel.
set -u
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
BUILD="$ROOT/builds/watch-winder-capsule"
SAMPLES="${1:-2048}"; THR="${2:-0.01}"
LOG="$BUILD/renders/final/batch.log"; mkdir -p "$BUILD/renders/final"
STATES="hero rear open hero-right front profile top rear-quarter lid-half open-seated macro-dial macro-knob macro-hinge macro-guilloche macro-controls macro-usb"
JOBS=""; for s in $STATES; do JOBS="$JOBS $s-graphite.png"; done; JOBS="$JOBS hero-graphite-f8-inspection.png"
echo "BATCH START $(date +%FT%T) samples=$SAMPLES thr=$THR" >> "$LOG"
for f in $JOBS; do
  [ -s "$BUILD/renders/final/$f" ] && { echo "SKIP $f (exists)" >> "$LOG"; continue; }
  t0=$(date +%s)
  line=$(cd "$ROOT" && HEADLESS_KEEP_ADDONS=1 bash scripts/headless-run.sh --blend "$BUILD/watch-winder-capsule.blend" \
        "$BUILD/scripts/pass-20-final-renders.py" -- "$SAMPLES" "$THR" GPU "$f" 2>&1 | grep '^AGENT_' | tail -1)
  echo "JOB $f $(( $(date +%s) - t0 ))s ${line:0:160}" >> "$LOG"
done
echo "BATCH END $(date +%FT%T)" >> "$LOG"
