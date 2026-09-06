"""Measured hole features and their fastener-table conformance.

Ray-cast measurement promoted from builds/robot-arm-reference-v2/verify-fit-coupon.py,
which proves a bore is clear by asserting the axial surface probe returns None
and measures a seat by the depth of the first hit. Extended here with a radial
ring probe that measures the effective bore diameter, and with published table
lookups (scripts/production_gate/fastener_tables.py).

What it proves: the modelled bore has that measured diameter along the ring at
center_mm. What it does NOT prove: thread engagement, insert pull-out, printed
hole shrinkage, or that a real screw passes.
"""
from __future__ import annotations

import math

from . import fastener_tables, meshprep
from .report import check, tol_check

RING_RAYS = 24
MAX_RAY_MM = 200.0


def _basis(u):
    a = (1.0, 0.0, 0.0) if abs(u.x) < 0.9 else (0.0, 1.0, 0.0)
    from mathutils import Vector
    e1 = u.cross(Vector(a)).normalized()
    return e1, u.cross(e1).normalized()


def _ring(tree, center, u, e1, e2):
    """Radial first-hit distances (mm) from a point on the axis.

    A ray that leaves exactly through a vertex or an edge of the tessellated
    bore is rejected by every triangle it touches and flies on to the outer
    wall. That is a numerical artefact, not a wide hole, so each direction is
    sampled three times inside a small angular window and the MEDIAN is kept:
    one degenerate sample per direction cannot move the result, while a
    genuinely oval bore still shows its full spread. Directions are offset by
    half a step so the ring is never symmetric with the mesh.
    """
    step = 2.0 * math.pi / RING_RAYS
    out = []
    for k in range(RING_RAYS):
        base = step * (k + 0.5)
        samples = []
        for j in (-1, 0, 1):
            ang = base + j * step / 3.0
            d = (e1 * math.cos(ang) + e2 * math.sin(ang)).normalized()
            hit, _n, _i, dist = tree.ray_cast(center, d, MAX_RAY_MM)
            if hit is not None:
                samples.append(dist)
        if len(samples) == 3:
            out.append(sorted(samples)[1])
        elif samples:
            out.append(min(samples))
    return out


def _axial(tree, origin, direction):
    hit, _n, _i, dist = tree.ray_cast(origin, direction, MAX_RAY_MM)
    return None if hit is None else dist


def evaluate(bm, features, prefix="", part_dims_mm=None):
    from mathutils import Vector
    tri = meshprep.triangulated(bm)
    tree = meshprep.bvh(tri)
    span = max(meshprep.bbox_mm(bm)) + 10.0
    checks, measured, unchecked = [], {}, []
    for idx, feat in enumerate(features or []):
        fid = feat.get("id") or "f%d" % idx
        tag = "%sfeature_%s_" % (prefix, fid)
        if feat.get("type") != "hole":
            checks.append(check(tag + "measured", "skip", feat.get("type"), None,
                                "v1 measures type 'hole' only"))
            unchecked.append("feature %s of type %s is not measured in v1"
                             % (fid, feat.get("type")))
            continue
        u = meshprep.axis_vector(feat["axis"])
        c = Vector(tuple(float(v) for v in feat["center_mm"]))
        e1, e2 = _basis(u)
        nominal_r = float(feat["diameter_mm"]) / 2.0
        tol = float(feat["tol_mm"])
        margin = max(tol, 0.5)

        # --- bore clear / depth -------------------------------------------
        entry = None
        probes = {}
        for sign in (1.0, -1.0):
            origin = c + u * (span * sign)
            direction = -u * sign
            t_axis = _axial(tree, origin, direction)
            t_surf = _axial(tree, origin + e1 * (nominal_r + margin), direction)
            probes["%+d" % int(sign)] = {"axial_mm": t_axis, "surface_mm": t_surf}
            if t_surf is not None and (t_axis is None or t_axis > t_surf + 1e-3):
                entry = (sign, t_axis, t_surf)
        depth_declared = feat.get("depth_mm")
        if entry is None:
            checks.append(check(tag + "bore_clear", "fail", probes, None,
                                "the axial probe hit material at the hole centre "
                                "before the surrounding surface: no bore here"))
        elif depth_declared is None:
            through = all(p["axial_mm"] is None for p in probes.values())
            checks.append(check(tag + "bore_clear", "pass" if through else "fail",
                                probes, {"expect": "no axial hit (through hole)"},
                                "a through hole must let the axial ray exit from "
                                "both sides"))
        else:
            sign, t_axis, t_surf = entry
            depth = None if t_axis is None else (t_axis - t_surf)
            checks.append(tol_check(tag + "depth_mm", depth, float(depth_declared), tol,
                                    "measured from the entry surface to the first "
                                    "axial hit (the bore floor)"))
        # --- material around the bore -------------------------------------
        around = []
        for k in range(4):
            ang = math.pi / 2.0 * k
            off = (e1 * math.cos(ang) + e2 * math.sin(ang)) * (nominal_r + margin)
            around.append(_axial(tree, c + off + u * span, -u) is not None)
        checks.append(check(tag + "material_around", "pass" if all(around) else "fail",
                            around, {"expect": [True] * 4},
                            "axial probes at radius %.3f mm must find material on all "
                            "four sides; a breakout reads as a missing wall"
                            % (nominal_r + margin)))
        # --- measured diameter --------------------------------------------
        radii = _ring(tree, c, u, e1, e2)
        if len(radii) < RING_RAYS:
            checks.append(check(tag + "diameter_mm", "fail",
                                {"hits": len(radii), "of": RING_RAYS}, None,
                                "the radial ring at center_mm did not find a wall in "
                                "every direction"))
            dia = None
        else:
            dia = 2.0 * sum(radii) / len(radii)
            checks.append(tol_check(tag + "diameter_mm", round(dia, 4),
                                    float(feat["diameter_mm"]), tol,
                                    "mean of %d radial first-hit distances at "
                                    "center_mm; roundness span %.4f mm"
                                    % (RING_RAYS, (max(radii) - min(radii)) * 2.0)))
        measured[fid] = {"measured_diameter_mm": dia, "probes": probes,
                         "ring_hits": len(radii),
                         "ring_min_r_mm": min(radii) if radii else None,
                         "ring_max_r_mm": max(radii) if radii else None}
        # --- fastener table ------------------------------------------------
        fst = feat.get("fastener")
        if fst:
            expected, source, note = fastener_tables.expected_hole_diameter(fst)
            if expected is None:
                checks.append(check(tag + "fastener_table", "skip", None, None,
                                    "%s | table_source: %s" % (note, source)))
                unchecked.append("feature %s: %s" % (fid, note))
            else:
                ok = abs(float(feat["diameter_mm"]) - expected) <= tol
                checks.append(check(tag + "fastener_table", "pass" if ok else "fail",
                                    float(feat["diameter_mm"]),
                                    {"table_value_mm": expected, "tol": tol},
                                    "%s | table_source: %s" % (note, source)))
            if fst.get("standard") == "heatset":
                need, src = fastener_tables.heatset_min_depth(fst.get("size"))
                if need is not None:
                    have = feat.get("depth_mm")
                    origin = "declared depth_mm"
                    if have is None and part_dims_mm:
                        # No depth declared: the most material a through-hole can
                        # offer is the part thickness along the hole axis. Gate on
                        # that so an insert deeper than the plate cannot pass.
                        ax = "xyz".find(str(feat.get("axis", "z")).lower())
                        if ax >= 0 and ax < len(part_dims_mm):
                            have = float(part_dims_mm[ax])
                            origin = "derived from target_dims_mm along axis %s" % feat.get("axis")
                    checks.append(check(
                        tag + "heatset_depth", "info" if have is None else
                        ("pass" if have >= need else "fail"), have,
                        {"min_depth_mm": need},
                        "table_source: %s | %s" % (src, origin if have is not None else
                                                 "no depth_mm and no target_dims, not gated")))
    tri.free()
    return checks, measured, unchecked
