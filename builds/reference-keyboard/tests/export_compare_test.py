"""Focused regression/probe for reference-keyboard export surface comparison."""
import json
import math
import sys
import unittest
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector

BUILD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BUILD / "scripts"))
import export_compare as ec  # noqa: E402

Q_MM = 1e-5


def _qv(v):
    return tuple(int(round(float(c) / Q_MM)) for c in v)


def _tri_counter(entry):
    verts = entry["surface"]["vertices_mm"]
    return Counter(tuple(sorted(_qv(verts[i]) for i in face))
                   for face in entry["surface"]["triangles"])


def _vert_counter(entry):
    return Counter(_qv(v) for v in entry["surface"]["vertices_mm"])


def _vertex_match_max(a, b):
    targets = {}
    for p in b["surface"]["vertices_mm"]:
        targets.setdefault(_qv(p), []).append(tuple(float(c) for c in p))
    distances = []
    for p in a["surface"]["vertices_mm"]:
        p = tuple(float(c) for c in p)
        choices = targets.get(_qv(p), ())
        if choices:
            distances.append(min(_norm(_sub(p, q)) for q in choices))
    return max(distances) if distances else None


def _sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def _norm(v):
    return math.sqrt(_dot(v, v))


def _point_triangle_distance(p, a, b, c):
    """Double-precision closest distance, Real-Time Collision Detection §5.1.5."""
    ab, ac, ap = _sub(b, a), _sub(c, a), _sub(p, a)
    d1, d2 = _dot(ab, ap), _dot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return _norm(ap)
    bp = _sub(p, b)
    d3, d4 = _dot(ab, bp), _dot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return _norm(bp)
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        return _norm(_sub(p, tuple(a[i] + v * ab[i] for i in range(3))))
    cp = _sub(p, c)
    d5, d6 = _dot(ab, cp), _dot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return _norm(cp)
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        return _norm(_sub(p, tuple(a[i] + w * ac[i] for i in range(3))))
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        bc = _sub(c, b)
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return _norm(_sub(p, tuple(b[i] + w * bc[i] for i in range(3))))
    denom = 1.0 / (va + vb + vc)
    v, w = vb * denom, vc * denom
    q = tuple(a[i] + ab[i] * v + ac[i] * w for i in range(3))
    return _norm(_sub(p, q))


def probe_r02():
    root = BUILD / "runs" / "verification-r02" / "steps" / "export" / "attempt-0001"
    source = json.loads((root / "source-surfaces.json").read_text())
    assert bpy.ops.import_scene.gltf(filepath=str(root / "keyboard.glb")) == {"FINISHED"}
    bpy.context.scene.frame_set(1)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for name in ("RK_BASE", "RK_PCB"):
        expected = source["frames"]["1"]["objects"][name]
        actual = ec._capture_object(bpy.data.objects[name], depsgraph)
        src_tris, act_tris = _tri_counter(expected), _tri_counter(actual)
        src_verts, act_verts = _vert_counter(expected), _vert_counter(actual)
        av = actual["surface"]["vertices_mm"]
        af = actual["surface"]["triangles"]
        by_sig = {}
        for idx, face in enumerate(af):
            sig = tuple(sorted(_qv(av[i]) for i in face))
            by_sig.setdefault(sig, []).append(idx)
        sv = expected["surface"]["vertices_mm"]
        sf = expected["surface"]["triangles"]
        target = ec._bvh(av, af)
        samples = min(len(sf), ec.MAX_SAMPLES)
        ids = [0] if samples == 1 else [round(i * (len(sf) - 1) / (samples - 1))
                                        for i in range(samples)]
        worst = None
        for face_idx in ids:
            face = sf[face_idx]
            p = tuple(sum(float(sv[i][axis]) for i in face) / 3.0 for axis in range(3))
            hit = target.find_nearest(Vector(p))
            row = (float(hit[3]), face_idx, p, hit)
            worst = row if worst is None or row[0] > worst[0] else worst
        distance, face_idx, p, hit = worst
        face = sf[face_idx]
        sig = tuple(sorted(_qv(sv[i]) for i in face))
        matches = by_sig.get(sig, [])
        stable = None
        if matches:
            tri = af[matches[0]]
            coords = [tuple(float(c) for c in av[i]) for i in tri]
            stable = _point_triangle_distance(p, *coords)
        print("PROBE " + json.dumps({
            "object": name,
            "source_vertices": len(sv), "glb_vertices": len(av),
            "vertex_signatures_equal": src_verts == act_verts,
            "source_only_vertices": sum((src_verts - act_verts).values()),
            "glb_only_vertices": sum((act_verts - src_verts).values()),
            "source_to_glb_vertex_max_mm": _vertex_match_max(expected, actual),
            "glb_to_source_vertex_max_mm": _vertex_match_max(actual, expected),
            "triangle_signatures_equal": src_tris == act_tris,
            "source_only_triangles": sum((src_tris - act_tris).values()),
            "glb_only_triangles": sum((act_tris - src_tris).values()),
            "worst_sample_face": face_idx, "bvh_mm": distance,
            "bvh_hit_face": int(hit[2]), "matching_face_count": len(matches),
            "matching_triangle_distance_mm": stable,
            "centroid_mm": p, "bvh_hit_mm": list(hit[0]),
        }))


def _entry(verts, faces):
    return {"triangle_count": len(faces), "bbox_mm": ec._bbox(verts),
            "surface": {"vertices_mm": verts, "triangles": faces}}


class ExportCompareTest(unittest.TestCase):
    def test_correspondence_passes_and_half_mm_translation_fails(self):
        src = _entry([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                     [[0, 1, 2]])
        same = _entry([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                      [[2, 1, 0]])
        good = ec._compare_object("same", src, same)
        self.assertTrue(good["pass"])
        self.assertEqual(good["surface_method"], "quantized_triangle_correspondence")
        self.assertEqual(good["surface_max_error_mm"], 0.0)

        moved = _entry([[0.0, 0.0, 0.5], [2.0, 0.0, 0.5], [0.0, 1.0, 0.5]],
                       [[0, 1, 2]])
        bad = ec._compare_object("moved", src, moved)
        self.assertFalse(bad["pass"])
        self.assertEqual(bad["surface_method"], "sampled_bvh")
        self.assertAlmostEqual(bad["surface_max_error_mm"], 0.5, places=5)


if __name__ == "__main__":
    if "--probe-r02" in sys.argv:
        probe_r02()
    else:
        unittest.main(argv=[sys.argv[0]])
