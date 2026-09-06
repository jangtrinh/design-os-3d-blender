"""Manifold / shell / volume predicates.

Promoted from knowledge/60-pipeline/3d-printing.md print_audit (non-manifold,
non-contiguous, wire, loose, zero-area, BVH self-intersection, shell flood fill,
signed volume) and builds/robot-arm-print-assembly/scripts/audit-meshes.py
(component walk). Kept non-destructive: the source mesh is never rewritten, and
no clean-up ops run before counting, so a defect cannot be silently repaired.
"""
from __future__ import annotations

from . import meshprep
from .report import check

ZERO_AREA_MM2 = 1e-8  # mm^2; a triangle this small is degenerate at print scale


def _self_intersection_pairs(bm, limit=200):
    tri = meshprep.triangulated(bm)
    tree = meshprep.bvh(tri)
    pairs = set()
    for i, j in tree.overlap(tree):
        if i == j:
            continue
        a, b = (i, j) if i < j else (j, i)
        if (a, b) in pairs:
            continue
        fa, fb = tri.faces[a], tri.faces[b]
        if {v.index for v in fa.verts} & {v.index for v in fb.verts}:
            continue  # face-adjacent pairs always "overlap"; not a defect
        pairs.add((a, b))
        if len(pairs) >= limit:
            break
    tri.free()
    return sorted(pairs)


def _shells(bm):
    seen, shells = set(), 0
    for f in bm.faces:
        if f.index in seen:
            continue
        shells += 1
        stack = [f]
        seen.add(f.index)
        while stack:
            cur = stack.pop()
            for e in cur.edges:
                for nf in e.link_faces:
                    if nf.index not in seen:
                        seen.add(nf.index)
                        stack.append(nf)
    return shells


def evaluate(bm, expected_shells=1, prefix=""):
    """-> (checks, measured). bm must already be world-space mm."""
    non_manifold = [e.index for e in bm.edges if not e.is_manifold]
    non_contig = [e.index for e in bm.edges if e.is_manifold and not e.is_contiguous]
    wire_e = [e.index for e in bm.edges if e.is_wire]
    loose_v = [v.index for v in bm.verts if not v.link_edges]
    zero_area = [f.index for f in bm.faces if f.calc_area() <= ZERO_AREA_MM2]
    pairs = _self_intersection_pairs(bm)
    shells = _shells(bm)
    volume = bm.calc_volume(signed=True)  # mm^3
    area = sum(f.calc_area() for f in bm.faces)
    measured = {
        "non_manifold_edges": len(non_manifold), "non_contiguous_edges": len(non_contig),
        "wire_edges": len(wire_e), "loose_verts": len(loose_v),
        "zero_area_faces": len(zero_area), "self_intersection_pairs": len(pairs),
        "shells": shells, "signed_volume_mm3": volume, "surface_area_mm2": area,
        "triangle_estimate": len(bm.faces),
        "sample_non_manifold_edges": non_manifold[:10],
        "sample_self_intersections": [list(p) for p in pairs[:10]],
    }
    z = lambda name, n, note: check(prefix + name, "pass" if n == 0 else "fail", n, 0, note)
    checks = [
        z("non_manifold_edges", len(non_manifold),
          "edges not shared by exactly two faces; the solid is not watertight"),
        z("non_contiguous_edges", len(non_contig),
          "manifold edges whose two faces disagree on winding: inverted normals"),
        z("wire_edges", len(wire_e), "edges with no face"),
        z("loose_verts", len(loose_v), "vertices with no edge"),
        z("zero_area_faces", len(zero_area),
          "faces at or below %g mm^2" % ZERO_AREA_MM2),
        z("self_intersection_pairs", len(pairs),
          "non-adjacent triangle pairs whose bounds overlap (BVH); capped at 200"),
        check(prefix + "shells", "pass" if shells == expected_shells else "fail",
              shells, expected_shells, "separate closed surfaces"),
        check(prefix + "signed_volume_positive", "pass" if volume > 0 else "fail",
              volume, {"min_exclusive": 0.0},
              "negative or zero volume means the surface is inverted or open"),
    ]
    return checks, measured
