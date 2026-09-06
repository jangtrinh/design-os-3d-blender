#!/usr/bin/env bash
# Export the curated public tree of this project into the design-os-3d-blender
# repository checkout, then verify it standalone (catalog + three test suites).
#
#   bash scripts/export-public-repo.sh [/path/to/design-os-3d-blender]
#
# Cut rules (kept in one place so the public repo never drifts by accident):
#   - skills, knowledge, docs, specs, scripts, tests: everything except caches
#   - research/: markdown only (no tools/ checkouts, venvs or media)
#   - img2threejs: vendored without .git/.cache (Apache-2.0 license file kept)
#   - builds/: only the curated robot-arm demo + the catalog example scripts;
#     never frames, draft videos, *.log, snapshots or zip kits
#   - plans/: nothing except the knowledge pipeline receipt
# Exit: 0 verified · 1 verification failed · 2 bad input.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST="${1:-$SRC/../design-os-3d-blender}"
[[ -d "$DST/.git" ]] || { echo "export-public-repo: $DST is not a git checkout" >&2; exit 2; }
DST="$(cd "$DST" && pwd)"
[[ "$SRC" != "$DST" ]] || { echo "export-public-repo: run the PROJECT copy of this script (SRC == DST: $SRC)" >&2; exit 2; }
RS=(rsync -a --exclude '.DS_Store' --exclude '__pycache__' --exclude '*.pyc' --exclude '*.blend1')

cd "$SRC"
"${RS[@]}" AGENTS.md CLAUDE.md .project-agent.md "$DST/"
"${RS[@]}" knowledge docs specs scripts tests "$DST/"
"${RS[@]}" --delete --exclude 'tools' --include '*/' --include '*.md' --exclude '*' research/ "$DST/research/"
"${RS[@]}" --delete .agents/rules .agents/workflows "$DST/.agents/"; cp .agents/mcp_config.json "$DST/.agents/"
for s in blender-agent-core blender-image-to-3d blender-knowledge-workbench img2threejs; do
  "${RS[@]}" --delete --exclude '.git' --exclude '.cache' ".agents/skills/$s" "$DST/.agents/skills/"
  "${RS[@]}" --delete --exclude '.git' --exclude '.cache' ".claude/skills/$s" "$DST/.claude/skills/"
done

# --- curated demo builds ------------------------------------------------------
A=builds/robot-arm-original-refined; P=builds/robot-arm-print-assembly; V=builds/robot-arm-v2-engineered
mkdir -p "$DST/$A/video" "$DST/$A/renders" "$DST/$P/video" "$DST/$P/renders" "$DST/$V" "$DST/builds/fpv-drone-native"
cp "$A"/README.md "$A"/plan.md "$A"/arm-original-refined.blend "$DST/$A/"
"${RS[@]}" --delete --exclude '*.log' "$A/reports" "$A/scripts" "$DST/$A/"
cp "$A"/renders/*.png "$A"/renders/*.jpg "$DST/$A/renders/" 2>/dev/null || true
cp "$A"/video/arm-step-by-step-refined.mp4 "$DST/$A/video/"
cp "$P"/README.md "$P"/plan.md "$P"/parts-list.csv "$P"/assembly-steps.csv "$P"/arm-print-plates.blend "$P"/arm-step-assembly-corrected.blend "$DST/$P/"
"${RS[@]}" --delete --exclude '*.log' "$P/parts" "$P/plates" "$P/reports" "$P/scripts" "$DST/$P/"
cp "$P"/video/arm-step-by-step.mp4 "$P"/video/assembly-animatic.mp4 "$DST/$P/video/"
cp "$P"/renders/plates-overview0001.png "$P"/renders/plates-final0001.png "$P"/renders/assembly-1429-METAL.png "$P"/renders/assembly-0320-METAL.png "$DST/$P/renders/"
# files the knowledge catalog cites as execution examples (must exist for `check`)
python3 - "$SRC" "$DST" <<'PY'
import json, os, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
for rel in json.load(open(os.path.join(src, "knowledge/catalog-config.json")))["examples"]:
    rel = rel if isinstance(rel, str) else rel["path"]
    os.makedirs(os.path.dirname(os.path.join(dst, rel)), exist_ok=True)
    shutil.copy2(os.path.join(src, rel), os.path.join(dst, rel))
PY
# plans/ is internal history (journals, audit reports with quoted owner messages) and is
# not published; only the pipeline receipt the catalog tooling reads is carried over.
rm -rf "$DST/plans/260905-2356-blender-workflow-audit"
mkdir -p "$DST/plans/knowledge-updates"
cp plans/knowledge-updates/last-publication.json "$DST/plans/knowledge-updates/"
find "$DST" -name '.DS_Store' -delete

# --- verify standalone --------------------------------------------------------
cd "$DST"
python3 scripts/blender-knowledge.py check >/dev/null || { echo "export-public-repo: catalog check FAILED in $DST" >&2; exit 1; }
for suite in tests/execution tests/production-gate tests/knowledge; do
  python3 -m unittest discover -s "$suite" >/dev/null 2>&1 || { echo "export-public-repo: $suite FAILED in $DST" >&2; exit 1; }
done
if grep -rIlE 'sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH) PRIVATE' . --exclude-dir=.git >/dev/null; then
  echo "export-public-repo: secret-looking string found; refusing" >&2; exit 1
fi
# Published text is English-only (owner rule 2026-09-06); Vietnamese diacritics anywhere in
# shipped Markdown/JSON/Python/shell fail the export. Vendored img2threejs is exempt.
# Letters unique to Vietnamese orthography (é/ý/à… are skipped: Bézier, Křivánek, Lévy appear in bibliographies).
VN='[ăâđêôơưĂÂĐÊÔƠƯạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỵỷỹ]'
if VNHITS="$(grep -rlP "$VN" . --include='*.md' --include='*.json' --include='*.py' --include='*.sh' --exclude-dir=.git --exclude-dir=img2threejs | grep -v 'scripts/knowledge-query.py\|scripts/export-public-repo.sh')"; then
  echo "export-public-repo: Vietnamese text remains in published files:" >&2; echo "$VNHITS" >&2; exit 1
fi
echo "export-public-repo: verified $(git -C "$DST" status --porcelain | wc -l | tr -d ' ') changed paths in $DST — review with 'git -C $DST status', then commit and push"
