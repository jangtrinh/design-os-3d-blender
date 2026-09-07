"""In-Blender half of the production gate. Never run this against a live scene:
the export round trip wipes the file. scripts/production-gate.py always starts a
fresh --factory-startup -b process for it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy  # noqa: E402

from production_gate import (bed_fit, dimensions, export_roundtrip,  # noqa: E402
                             features_fasteners, meshprep, report,
                             spec as spec_mod, topology, walls_overhang)


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="production-gate(blender)")
    ap.add_argument("--scene", default=None)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--parts", default=None)
    ap.add_argument("--export-dir", default=None)
    return ap.parse_args(argv)


def sentinel(ok, exit_code, error=None, **post):
    if not ok and error is None:
        error = {"type": "GateFailure", "message": post.get("message", "gate failed"),
                 "traceback": None}
    payload = {"step": "production-gate",
               "postconditions": dict(post, exit_code=exit_code),
               "error": None if ok else error}
    print(("AGENT_OK " if ok else "AGENT_FAIL ") + json.dumps(payload, default=str))


def gate_part(part, spec, unchecked):
    obj = bpy.data.objects.get(part["object"])
    if obj is None or obj.type != "MESH":
        raise spec_mod.SpecError(
            "part %r: object %r is missing from the scene or is not a mesh"
            % (part["id"], part["object"]))
    bm = meshprep.evaluated_mm_bmesh(obj)
    checks, measured = [], {}
    c, m = topology.evaluate(bm, part.get("expected_shells", 1))
    checks += c
    measured.update(m)
    c, m = dimensions.bbox_checks(bm, part["target_dims_mm"], part["tol_mm"])
    checks += c
    measured.update(m)
    c, m = dimensions.transform_checks(obj)
    checks += c
    measured.update(m)
    c, m = dimensions.unit_checks(bpy.context.scene)
    checks += c
    measured.update(m)
    c, m = bed_fit.checks(bm, part, spec)
    checks += c
    measured.update(m)
    c, m = walls_overhang.wall_checks(bm, part.get("min_wall_mm"))
    checks += c
    measured.update(m)
    if part.get("min_wall_mm") is None:
        unchecked.append("part %s: no min_wall_mm declared" % part["id"])
    c, m = walls_overhang.overhang_checks(
        bm, part.get("orientation_up", "+z"), part.get("max_overhang_deg", 45.0),
        part.get("max_overhang_area_pct"))
    checks += c
    measured.update(m)
    if part.get("max_overhang_area_pct") is None:
        unchecked.append("part %s: overhang reported but not gated "
                         "(no max_overhang_area_pct)" % part["id"])
    c, m, u = features_fasteners.evaluate(bm, part.get("features"),
                                           part_dims_mm=part.get("target_dims_mm"))
    checks += c
    measured["features"] = m
    unchecked.extend(u)
    if not part.get("features"):
        unchecked.append("part %s: no features declared, so no bore was measured"
                         % part["id"])
    return obj, bm, {"id": part["id"], "object": part["object"],
                     "measured": measured,
                     "allowed": {"target_dims_mm": part["target_dims_mm"],
                                 "tol_mm": part["tol_mm"],
                                 "min_wall_mm": part.get("min_wall_mm"),
                                 "expected_shells": part.get("expected_shells", 1)},
                     "checks": checks}


def main(argv):
    started = time.time()
    args = parse_args(argv)
    unchecked, entries, results = [], [], []
    spec = spec_mod.load(args.spec)
    wanted = [p.strip() for p in args.parts.split(",")] if args.parts else None
    parts = spec_mod.select_parts(spec, wanted)
    if wanted:
        skipped = [p["id"] for p in spec["parts"] if p["id"] not in wanted]
        unchecked.extend("part %s: not selected by --parts" % s for s in skipped)
    keep = []
    for part in parts:
        obj, bm, res = gate_part(part, spec, unchecked)
        results.append(res)
        if args.export_dir:
            os.makedirs(args.export_dir, exist_ok=True)
            entries.append(export_roundtrip.export_part(bm, part, args.export_dir))
            keep.append((part, entries[-1], res))
        bm.free()
    if args.export_dir:
        for part, entry, res in keep:
            res["checks"].extend(export_roundtrip.verify_roundtrip(entry, part))
        with open(os.path.join(args.export_dir, "manifest.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(export_roundtrip.manifest(entries), fh, indent=2)
    else:
        unchecked.append("export round trip: not run (no --export-dir)")
    rep = report.assemble(args.scene, args.spec, spec, results, spec["units"],
                          bpy.app.version_string, report.standing_exclusions(spec),
                          unchecked, started)
    os.makedirs(os.path.dirname(os.path.abspath(args.report)) or ".", exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2, default=str)
    bad = bool(rep["failed"]) or bool(rep["required_checks_missing"])
    sentinel(not bad, 1 if bad else 0, report=os.path.abspath(args.report),
             failed=rep["failed"], parts=len(results),
             message="parts failed: %s" % ", ".join(rep["failed"]) if bad else "ok")
    return 1 if bad else 0


if __name__ == "__main__":
    _argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    try:
        code = main(_argv)
    except spec_mod.SpecError as exc:
        sentinel(False, 2, message=str(exc),
                 error={"type": "SpecError", "message": str(exc), "traceback": None})
        code = 2
    except Exception as exc:  # noqa: BLE001 - the gate must never die silently
        sentinel(False, 3, message=str(exc),
                 error={"type": type(exc).__name__, "message": str(exc),
                        "traceback": traceback.format_exc()})
        code = 3
    sys.exit(code)
