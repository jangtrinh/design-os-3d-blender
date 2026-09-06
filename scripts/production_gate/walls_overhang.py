"""Wall thickness and overhang SCREENS.

Wall screen promoted from builds/robot-arm-print-assembly/scripts/audit-meshes.py
(ray from each face centroid along -normal, accepted only when the hit normal
opposes the source normal). Overhang promoted from
scripts/verify-3dprint-tolerances.py analyze_3dprint_geometry (face-area share
whose normal falls within max_overhang_deg of the build-down direction).

NEITHER IS A PROOF. The wall screen samples face centroids above an area
threshold, so a thin region with no sampled centroid is invisible to it, and a
narrow rib can read thicker than its true minimum. The overhang figure is a
geometric share of area, not a printability verdict; bridging, supports and
slicer settings are outside this gate entirely.
"""
from __future__ import annotations

import math

from . import meshprep
from .report import check

MIN_FACE_AREA_MM2 = 0.3   # same threshold as the promoted audit
MAX_RAY_MM = 50.0
EPS_MM = 1e-4


def wall_samples(bm):
    tri = meshprep.triangulated(bm)
    tree = meshprep.bvh(tri)
    out = []
    for f in tri.faces:
        if f.calc_area() < MIN_FACE_AREA_MM2:
            continue
        n = f.normal
        if n.length_squared == 0.0:
            continue
        pt = f.calc_center_median()
        hit, hn, _idx, dist = tree.ray_cast(pt - n * EPS_MM, -n, MAX_RAY_MM)
        if hit is not None and hn.dot(n) < -0.5:
            out.append(dist + EPS_MM)
    tri.free()
    out.sort()
    return out


def wall_checks(bm, min_wall_mm, prefix=""):
    samples = wall_samples(bm)
    measured = {"wall_ray_samples": len(samples),
                "wall_min_mm": samples[0] if samples else None,
                "wall_p01_mm": samples[int(len(samples) * 0.01)] if samples else None}
    if min_wall_mm is None:
        return [check(prefix + "wall_thickness_screen", "skip", measured, None,
                      "spec declares no min_wall_mm")], measured
    if not samples:
        return [check(prefix + "wall_thickness_screen", "fail", measured, min_wall_mm,
                      "no opposing-face ray hit; thickness could not be sampled at all"
                      )], measured
    ok = measured["wall_min_mm"] >= min_wall_mm
    return [check(prefix + "wall_thickness_screen", "pass" if ok else "fail",
                  {"min_mm": round(measured["wall_min_mm"], 4),
                   "p01_mm": round(measured["wall_p01_mm"], 4),
                   "samples": len(samples)},
                  {"min_wall_mm": min_wall_mm},
                  "SCREEN: centroid ray sampling of faces >= %g mm^2, not an "
                  "exhaustive thickness proof" % MIN_FACE_AREA_MM2)], measured


def overhang_checks(bm, orientation_up="+z", max_overhang_deg=45.0,
                    max_area_pct=None, prefix=""):
    up = meshprep.axis_vector(orientation_up)
    down = -up
    cos_t = math.cos(math.radians(max_overhang_deg))
    total = over = 0.0
    for f in bm.faces:
        a = f.calc_area()
        total += a
        n = f.normal
        if n.length_squared and n.normalized().dot(down) > cos_t:
            over += a
    pct = (over / total * 100.0) if total > 0 else 0.0
    measured = {"overhang_area_pct": pct, "orientation_up": orientation_up,
                "max_overhang_deg": max_overhang_deg}
    note = ("SCREEN: share of surface area whose normal is within %g deg of the "
            "build-down direction. Not a printability verdict." % max_overhang_deg)
    if max_area_pct is None:
        return [check(prefix + "overhang_area_pct", "info", round(pct, 3), None,
                      note + " No max_overhang_area_pct declared, so informational only."
                      )], measured
    return [check(prefix + "overhang_area_pct", "pass" if pct <= max_area_pct else "fail",
                  round(pct, 3), {"max_pct": max_area_pct}, note)], measured
