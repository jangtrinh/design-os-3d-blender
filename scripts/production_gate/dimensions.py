"""Dimension, transform and unit predicates.

Promoted from builds/robot-arm-reference-v2/verify-fit-coupon.py (bbox
dimension asserts against a declared target) and made explicit about the two
traps that make a "correct" dimension a lie: unapplied object scale and a
non-metric / rescaled unit system.
"""
from __future__ import annotations

from . import meshprep
from .report import check

SCALE_EPS = 1e-4  # relative; 0.01% off unity is already an unapplied transform


def bbox_checks(bm, target_dims_mm, tol_mm, prefix=""):
    dims = meshprep.bbox_mm(bm)
    devs = [dims[k] - float(target_dims_mm[k]) for k in range(3)]
    worst = max(abs(d) for d in devs)
    status = "pass" if worst <= tol_mm else "fail"
    checks = [check(prefix + "bbox_dims_mm", status,
                    [round(d, 4) for d in dims],
                    {"target": [float(t) for t in target_dims_mm], "tol": tol_mm},
                    "world-space axis-aligned bounding box; deviation %s mm"
                    % [round(d, 4) for d in devs])]
    return checks, {"bbox_dims_mm": dims, "bbox_deviation_mm": devs}


def transform_checks(obj, prefix=""):
    """scale must be applied: a mesh half-size with object scale 2 measures
    correctly in world space but exports and prints wrong from local data."""
    sc = [round(float(v), 6) for v in obj.scale]
    applied = all(abs(v - 1.0) <= SCALE_EPS for v in sc)
    delta = [round(float(v), 6) for v in obj.delta_scale]
    delta_ok = all(abs(v - 1.0) <= SCALE_EPS for v in delta)
    return [
        check(prefix + "scale_applied", "pass" if applied and delta_ok else "fail",
              {"scale": sc, "delta_scale": delta}, {"scale": [1.0, 1.0, 1.0]},
              "object scale must be 1,1,1 (apply transforms) so local mesh data "
              "equals world geometry"),
    ], {"object_scale": sc, "object_delta_scale": delta}


def unit_checks(scene, prefix=""):
    us = scene.unit_settings
    sl = float(us.scale_length)
    system = us.system
    ok_scale = abs(sl - 1.0) <= 1e-9
    ok_system = system == "METRIC"
    return [
        check(prefix + "scene_unit_system", "pass" if ok_system else "fail",
              system, "METRIC", "non-metric units make every mm number a guess"),
        check(prefix + "scene_scale_length", "pass" if ok_scale else "fail", sl, 1.0,
              "1 Blender unit must be 1 metre; the gate converts with x1000"),
    ], {"unit_system": system, "scale_length": sl}
