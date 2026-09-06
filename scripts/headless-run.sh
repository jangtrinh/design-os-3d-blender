#!/bin/bash
# Run a bpy payload in a fresh headless Blender and report the truth about it.
#
# Usage:
#   scripts/headless-run.sh [--blend <file.blend>] <script.py> [file.blend] [-- args...]
#
# The exit code is decided by the LAST sentinel line the payload printed on
# stdout (AGENT_OK -> 0, AGENT_FAIL -> 1/2/3), because Blender's own exit code
# is unreliable in both directions. When the payload prints no sentinel we fall
# back to Blender's exit code and say so on stderr.
#
# Exit codes: 0 pass - 1 requirement/assert failed - 2 invalid input
#             (missing script or Blender binary) - 3 execution error.
#
# Env:
#   BLENDER_BIN            override the Blender executable
#   HEADLESS_KEEP_ADDONS=1 keep user prefs/add-ons (drops --factory-startup)
#
# NOTE: not `set -e`. We must inspect Blender's exit code, not die on it.
set -uo pipefail

BLENDER="${BLENDER_BIN:-/Applications/Blender.app/Contents/MacOS/Blender}"

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

die_input() { # message -> exit 2 (invalid/incomplete input)
  printf 'headless-run.sh: %s\n' "$1" >&2
  exit 2
}

BLEND_FILE=""
SCRIPT=""
FORWARD=()
HAVE_FORWARD=0

# --- argument parsing -------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage; exit 0 ;;
    --blend)
      [[ $# -ge 2 ]] || die_input "--blend needs a file argument"
      BLEND_FILE="$2"; shift 2 ;;
    --)
      shift; if [[ $# -gt 0 ]]; then FORWARD=("$@"); HAVE_FORWARD=1; fi; break ;;
    *)
      if [[ -z "$SCRIPT" ]]; then
        SCRIPT="$1"
      elif [[ -z "$BLEND_FILE" && "$1" == *.blend ]]; then
        BLEND_FILE="$1"   # legacy positional form: <script.py> <file.blend>
      else
        die_input "unexpected argument: $1 (use -- to forward args to the payload)"
      fi
      shift ;;
  esac
done

[[ -n "$SCRIPT" ]] || die_input "usage: headless-run.sh [--blend f.blend] <script.py> [-- args]"
[[ -f "$SCRIPT" && -r "$SCRIPT" ]] || die_input "script not found or unreadable: $SCRIPT"
[[ -n "$BLEND_FILE" ]] && { [[ -f "$BLEND_FILE" && -r "$BLEND_FILE" ]] || die_input "blend file not found or unreadable: $BLEND_FILE"; }
[[ -x "$BLENDER" ]] || die_input "Blender binary not executable: $BLENDER (set BLENDER_BIN)"

# --- build the Blender command ---------------------------------------------
# (payload path was validated above; the launcher re-validates and reports exit 2)
ARGS=()
[[ "${HEADLESS_KEEP_ADDONS:-0}" == "1" ]] || ARGS+=("--factory-startup")
ARGS+=("--disable-autoexec" "-b")
[[ -n "$BLEND_FILE" ]] && ARGS+=("$BLEND_FILE")
# --python-exit-code must precede --python; it is the backstop for an error that
# escapes agent_runtime itself (syntax error, import failure) so such a run
# cannot exit 0.
# Default: run the payload THROUGH agent_runtime (same namespace/traceback/sentinel
# as MCP `rt.run_file`). HEADLESS_RAW=1 runs the payload file directly (legacy).
LAUNCHER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agent-run-headless.py"
if [[ "${HEADLESS_RAW:-0}" == "1" ]]; then
  ARGS+=("--python-exit-code" "3" "--python" "$SCRIPT")
  [[ "$HAVE_FORWARD" == "1" ]] && ARGS+=("--" "${FORWARD[@]}")
else
  ARGS+=("--python-exit-code" "3" "--python" "$LAUNCHER" "--" "$SCRIPT")
  [[ "$HAVE_FORWARD" == "1" ]] && ARGS+=("${FORWARD[@]}")
fi

LOG="$(mktemp -t headless-run)"
trap 'rm -f "$LOG"' EXIT

# stdout is teed so we can scan for the sentinel; stderr passes through as-is.
"$BLENDER" "${ARGS[@]}" | tee "$LOG"
BLENDER_RC="${PIPESTATUS[0]}"

# --- decide by the LAST sentinel line ---------------------------------------
SENTINEL="$(grep -E '^(AGENT_OK|AGENT_FAIL) ' "$LOG" | tail -n 1)"

if [[ "$SENTINEL" == AGENT_OK\ * ]]; then
  # agent_runtime always exits 0 behind a genuine AGENT_OK, so a nonzero Blender
  # exit here means the two disagree (a forged sentinel, or a legacy payload that
  # printed its own). Resolve a disagreement pessimistically.
  if [[ "$BLENDER_RC" != "0" ]]; then
    printf 'headless-run.sh: AGENT_OK but Blender exited %s; refusing to report success\n' "$BLENDER_RC" >&2
    exit "$BLENDER_RC"
  fi
  exit 0
elif [[ "$SENTINEL" == AGENT_FAIL\ * ]]; then
  # Trust agent_runtime's own exit code when it made it out; else generic error.
  case "$BLENDER_RC" in
    1|2|3) exit "$BLENDER_RC" ;;
    *)     exit 3 ;;
  esac
else
  printf 'headless-run.sh: no AGENT_OK/AGENT_FAIL sentinel in stdout; falling back to Blender exit %s (unreliable)\n' "$BLENDER_RC" >&2
  exit "$BLENDER_RC"
fi
