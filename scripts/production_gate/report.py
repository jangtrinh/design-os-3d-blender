"""Report assembly for the production gate (frozen schema, see plan.md)."""
from __future__ import annotations

import datetime
import hashlib
import os

from . import CHECKER_VERSION

SCHEMA_VERSION = 1
STATUS_ORDER = {"fail": 0, "pass": 1, "info": 2, "skip": 3}


def check(name, status, value=None, limit=None, note=""):
    """The one shape every predicate returns."""
    assert status in STATUS_ORDER, status
    return {"name": name, "status": status, "value": value, "limit": limit, "note": note}


def tol_check(name, value, target, tol, note=""):
    ok = value is not None and abs(value - target) <= tol
    return check(name, "pass" if ok else "fail", value,
                 {"target": target, "tol": tol}, note)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def part_status(checks):
    return "fail" if any(c["status"] == "fail" for c in checks) else "pass"


def assemble(scene, spec_path, spec, parts, units, blender_version, exclusions,
             unchecked, started, scene_sha=None, spec_sha=None):
    """parts: list of per-part dicts already carrying id/object/measured/checks."""
    for p in parts:
        p["status"] = part_status(p["checks"])
    failed = [p["id"] for p in parts if p["status"] == "fail"]
    checked = sorted({c["name"] for p in parts for c in p["checks"]
                      if c["status"] in ("pass", "fail")})
    required = spec.get("required_checks") or []
    missing_required = [r for r in required if r not in checked]
    for name in missing_required:
        unchecked.append("required_check %r never ran" % name)
    return {
        "schema_version": SCHEMA_VERSION,
        "inputs": {
            "scene": os.path.abspath(scene) if scene else None,
            "spec": os.path.abspath(spec_path),
            "scene_sha256": scene_sha or (sha256_file(scene) if scene and os.path.exists(scene) else None),
            "spec_sha256": spec_sha or sha256_file(spec_path),
        },
        "checker": {"version": CHECKER_VERSION, "blender": blender_version},
        "units": units,
        "parts": parts,
        "failed": failed,
        "required_checks_missing": missing_required,
        "exclusions": exclusions,
        "coverage": {"checked": checked, "unchecked": sorted(set(unchecked))},
        "duration_s": round(_now() - started, 3),
        "timestamp": datetime.datetime.now(datetime.timezone.utc)
                     .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def standing_exclusions(spec):
    """What the gate structurally does NOT prove, made visible in every report."""
    out = [
        "load capacity: not evaluated (no FEA, no coupon test)",
        "print success: not evaluated (no slicer run, no support/adhesion analysis)",
        "assembly fit: not evaluated (no mating-part interference study)",
        "thermal / creep behaviour: not evaluated",
        "surface finish and printer-specific shrinkage: not evaluated",
        "wall-thickness and overhang results are RAY SCREENS, not exhaustive proofs",
    ]
    for lc in spec.get("load_cases") or []:
        out.append("declared load_case not evaluated: %s" % lc)
    for ev in spec.get("physical_evidence") or []:
        out.append("physical evidence still owed: %s" % ev)
    return out


def _now():
    import time
    return time.time()
