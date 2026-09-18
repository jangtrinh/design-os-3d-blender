#!/usr/bin/env python3
"""Report pass scripts that no pipeline manifest declares, and manifest steps with no script.

    python3 scripts/check-pass-coverage.py                      # every build under builds/
    python3 scripts/check-pass-coverage.py builds/reference-keyboard
    python3 scripts/check-pass-coverage.py --json builds/desktop-companion

Why this exists: CK-001 authored `pass-B-rotation.py` — the only check designed to prove a
rotated knob pose survives GLB export — reviewed it into the plan, and never ran it. No
manifest referenced it, no run directory existed, and nothing in the pipeline noticed. An
authored pass is not an executed pass.

A build may declare deliberate exceptions in `<build>/pass-coverage-allow.json`:

    {"unreferenced": {"pass-07-reopen.py": "run inline by pass-06, never a manifest step"}}

Every exception needs a reason string; an empty reason is a failure. Exit 0 clean,
1 when something is unreferenced or missing, 2 on bad input.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def manifest_scripts(build):
    """Every script path named by a step in any pipeline manifest of this build."""
    declared = {}
    for manifest in sorted(build.glob("*pipeline*.json")):
        try:
            data = json.loads(manifest.read_text())
        except json.JSONDecodeError as exc:
            declared.setdefault("__unreadable__", []).append((manifest.name, str(exc)))
            continue
        for step in data.get("steps", []):
            script = step.get("script")
            if script:
                declared.setdefault(Path(script).name, []).append(f"{manifest.name}:{step.get('id', '?')}")
    return declared


def audit(build):
    """One build: which authored passes are declared, which declared steps are missing."""
    authored = sorted(p.name for p in build.glob("pass-*.py"))
    declared = manifest_scripts(build)
    allow_file = build / "pass-coverage-allow.json"
    allowed = {}
    if allow_file.exists():
        allowed = json.loads(allow_file.read_text()).get("unreferenced", {})

    unreferenced, excused = [], []
    for name in authored:
        if name in declared:
            continue
        reason = allowed.get(name)
        if reason:
            excused.append((name, reason))
        else:
            unreferenced.append((name, "" if name in allowed else None))

    missing = [(name, sites) for name, sites in declared.items()
               if name != "__unreadable__" and not (build / name).exists()]
    return {
        "build": str(build.relative_to(ROOT)) if build.is_relative_to(ROOT) else str(build),
        "authored": authored,
        "declared": sorted(k for k in declared if k != "__unreadable__"),
        "unreferenced": [{"pass": n, "empty_reason": r == ""} for n, r in unreferenced],
        "excused": [{"pass": n, "reason": r} for n, r in excused],
        "missing_scripts": [{"pass": n, "declared_at": s} for n, s in missing],
        "unreadable_manifests": declared.get("__unreadable__", []),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("builds", nargs="*", help="build directories; default: every builds/* with pass scripts")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    if args.builds:
        targets = [Path(b).resolve() for b in args.builds]
        for target in targets:
            if not target.is_dir():
                print(f"check-pass-coverage: not a directory: {target}", file=sys.stderr)
                return 2
    else:
        targets = sorted(p for p in (ROOT / "builds").glob("*") if p.is_dir() and any(p.glob("pass-*.py")))

    results = [audit(t) for t in targets]
    failed = any(r["unreferenced"] or r["missing_scripts"] or r["unreadable_manifests"] for r in results)

    if args.json:
        print(json.dumps({"builds": results, "status": "FAIL" if failed else "PASS"}, indent=1))
        return 1 if failed else 0

    for r in results:
        print(f"{r['build']}: {len(r['authored'])} authored, {len(r['declared'])} declared by a manifest")
        for entry in r["unreferenced"]:
            note = " (allowlist entry has an empty reason)" if entry["empty_reason"] else ""
            print(f"  UNREFERENCED {entry['pass']} — authored but no manifest step runs it{note}")
        for entry in r["excused"]:
            print(f"  excused      {entry['pass']} — {entry['reason']}")
        for entry in r["missing_scripts"]:
            print(f"  MISSING      {entry['pass']} — declared at {', '.join(entry['declared_at'])}, file absent")
        for name, error in r["unreadable_manifests"]:
            print(f"  UNREADABLE   {name} — {error}")
    print("FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
