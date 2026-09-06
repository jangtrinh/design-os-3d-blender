#!/usr/bin/env bash
# Wait for the stills batch to finish (GPU free), then render the print-plate stills on GPU.
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"; BUILD="$ROOT/builds/watch-winder-capsule"; LOG="$BUILD/renders/final/batch.log"
until grep -q "BATCH END" "$LOG"; do sleep 20; done
t0=$(date +%s)
line=$(cd "$ROOT" && HEADLESS_KEEP_ADDONS=1 bash scripts/headless-run.sh --blend "$BUILD/watch-winder-capsule-plates.blend" \
      "$BUILD/scripts/pass-31-print-plates-render.py" -- "${1:-1024}" "${2:-0.01}" GPU 2>&1 | grep '^AGENT_' | tail -1)
echo "JOB plates-render $(( $(date +%s) - t0 ))s ${line:0:300}" >> "$LOG"
