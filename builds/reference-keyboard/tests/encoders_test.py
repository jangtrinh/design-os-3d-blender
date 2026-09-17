"""Numerical fixture for the PEC11R encoder/carrier constructor."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import tempfile
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(REPO / "scripts"))
SPEC = importlib.util.spec_from_file_location("reference_keyboard_encoders", ROOT / "scripts" / "encoders.py")
enc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(enc)
layout = json.loads((ROOT / "layout.json").read_text())


def clean():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def bbox(obj):
    pts = [v.co for v in obj.data.vertices]
    lo = [min(v[i] for v in pts) for i in range(3)]
    hi = [max(v[i] for v in pts) for i in range(3)]
    return [hi[i] - lo[i] for i in range(3)], lo, hi


def audit(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    result = {
        "nonmanifold": sum(not e.is_manifold for e in bm.edges),
        "noncontiguous": sum(e.is_manifold and not e.is_contiguous for e in bm.edges),
        "loose": sum(not v.link_edges for v in bm.verts),
        "zero": sum(f.calc_area() <= 1e-14 for f in bm.faces),
        "volume": bm.calc_volume(signed=True),
    }
    bm.free()
    return result


def assert_solid(obj):
    a = audit(obj)
    assert a["nonmanifold"] == a["noncontiguous"] == a["loose"] == a["zero"] == 0, (obj.name, a)
    assert a["volume"] > 0, (obj.name, a)


def ray_z(obj, x, y):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    tree = BVHTree.FromBMesh(bm, epsilon=0.0)
    hit = tree.ray_cast(Vector((x, y, 0.020)), Vector((0, 0, -1)), 0.020)
    bm.free()
    return None if hit[0] is None else float(hit[0].z)


def ray_y(obj, x, z):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    tree = BVHTree.FromBMesh(bm, epsilon=0.0)
    hit = tree.ray_cast(Vector((x, 0.003, z)), Vector((0, -1, 0)), 0.006)
    bm.free()
    return None if hit[0] is None else float(hit[0].y)


clean()
assert bpy.app.version[:2] == (5, 2), bpy.app.version_string
checkpoint_tmp = tempfile.TemporaryDirectory(prefix="encoder-checkpoints-")
enc.mechanics.CHECKPOINTS = Path(checkpoint_tmp.name)
enc.mechanics.SEQ = 0
for i, (x, y) in enumerate(layout["knobs_mm"], 1):
    knob = bpy.data.objects.new(f"RK_KNOB_{i}", None)
    knob.location = (x / 1000, y / 1000, 0)
    bpy.context.scene.collection.objects.link(knob)

objects = enc.build(layout)
assert len(objects) == 125, len(objects)
assert enc.SOURCE_SHA256 == "ac88f657e611bc82fe79b102426fb5abcb7f40740540f0c681727e2d74784491"
assert len(list(Path(checkpoint_tmp.name).glob("*.blend"))) == 55

tol = 2e-6
for i in range(1, 6):
    body = bpy.data.objects[f"RK_ENCODER_BODY_{i}"]
    shaft = bpy.data.objects[f"RK_ENCODER_SHAFT_{i}"]
    bushing = bpy.data.objects[f"RK_ENCODER_BUSHING_{i}"]
    washer = bpy.data.objects[f"RK_ENCODER_WASHER_{i}"]
    nut = bpy.data.objects[f"RK_ENCODER_NUT_{i}"]
    carrier = bpy.data.objects[f"RK_ENCODER_CARRIER_{i}"]
    for obj in (body, shaft, bushing, washer, nut, carrier):
        assert_solid(obj)

    dims, lo, hi = bbox(body)
    assert all(abs(a - b) < tol for a, b in zip(dims, (0.0125, 0.0134, 0.0055))), dims
    assert abs(lo[2] - 0.0051) < tol and abs(hi[2] - 0.0106) < tol

    _, _, shaft_hi = bbox(shaft)
    assert abs(shaft_hi[2] - 0.0256) < tol, shaft_hi
    top = [v.co for v in shaft.data.vertices if v.co.z > 0.020]
    lower = [v.co for v in shaft.data.vertices if v.co.z < 0.0187]
    assert max(v.y for v in top) <= 0.001501, max(v.y for v in top)
    assert max(v.y for v in lower) >= 0.00299, max(v.y for v in lower)

    assert abs(nut["bushing_projection_above_nut_m"] - 0.0015) < 1e-9
    assert abs(carrier["knob_bottom_clearance_m"] - 0.0004) < 1e-9
    assert abs(carrier["edge_ligament_x_m"] - 0.0009) < 1e-9
    assert abs(body["neighbor_body_edge_clearance_mm"] - 7.5) < 1e-6
    assert ray_z(carrier, 0.0, 0.0) is None
    for dx, dy in ((-enc.RISER_X_M, -enc.RISER_Y_M), (enc.RISER_X_M, -enc.RISER_Y_M),
                   (-enc.RISER_X_M, enc.RISER_Y_M), (enc.RISER_X_M, enc.RISER_Y_M)):
        assert ray_z(carrier, dx, dy) is None, (i, dx, dy)
    assert abs(ray_z(carrier, 0.005, 0.0) - enc.CARRIER_HIGH_Z_M) < tol
    constraints = [c for c in shaft.constraints if c.type == "COPY_ROTATION"]
    assert len(constraints) == 1 and constraints[0].target.name == f"RK_KNOB_{i}"
    assert constraints[0].use_z and not constraints[0].use_x and not constraints[0].use_y

    wd, wlo, whi = bbox(washer)
    assert abs(wd[0] - 0.012) < 2e-5 and abs(wd[1] - 0.012) < 2e-5
    assert abs(wlo[2] - 0.0116) < tol and abs(whi[2] - 0.0121) < tol
    _, nlo, nhi = bbox(nut)
    assert abs(nlo[2] - 0.0121) < tol and abs(nhi[2] - 0.0141) < tol

    for k, (dx, dy) in enumerate(((-enc.RISER_X_M, -enc.RISER_Y_M),
                                  (enc.RISER_X_M, -enc.RISER_Y_M),
                                  (-enc.RISER_X_M, enc.RISER_Y_M),
                                  (enc.RISER_X_M, enc.RISER_Y_M))):
        riser = bpy.data.objects[f"RK_ENCODER_RISER_{i}_{k}"]
        screw = bpy.data.objects[f"RK_ENCODER_CARRIER_SCREW_{i}_{k}"]
        assert_solid(riser)
        assert_solid(screw)
        assert abs(ray_z(riser, 0.0, 0.0) - enc.RISER_TAP_LOW_Z_M) < tol
        assert riser["attachment_method"].startswith("bonded brass standoff prototype")
        sd, slo, shi = bbox(screw)
        assert abs(sd[0] - enc.FASTENER_HEAD_D_M) < 2e-5
        assert abs(slo[2] - enc.RISER_TAP_LOW_Z_M) < tol
        assert abs(shi[2] - enc.FASTENER_HEAD_HIGH_Z_M) < tol
        radial_clearance = math.hypot(dx, dy) - enc.FASTENER_HEAD_D_M / 2 - 0.008
        assert radial_clearance > 0.0002, radial_clearance
    board = bpy.data.objects[f"RK_ENCODER_DAUGHTERBOARD_{i}"]
    bd, _, _ = bbox(board)
    assert all(abs(a - b) < tol for a, b in zip(bd, (0.014, 0.001, 0.0065))), bd
    for label, dx in zip(("A", "C", "B"), (-0.0025, 0.0, 0.0025)):
        assert ray_y(board, dx, 0.00625) is None, (i, label)
        pad = bpy.data.objects[f"RK_ENCODER_PAD_{i}_{label}"]
        assert_solid(pad)
    for side in ("L", "R"):
        tab = bpy.data.objects[f"RK_ENCODER_BOARD_SUPPORT_{i}_{side}"]
        assert_solid(tab)
        _, _, thi = bbox(tab)
        assert abs(thi[2] - 0.0035) < tol
        assert tab["attachment_method"].startswith("bonded chassis support tab prototype")

# Global fit arithmetic: rear carrier stays inside ±43 mm acrylic inner wall;
# 20 mm encoder spacing leaves 0.4 mm between 19.6 mm carrier plates.
rear = [p for p in layout["knobs_mm"] if p[1] == 35]
assert max(p[1] + enc.CARRIER_Y_M * 500 for p in rear) == 42.5
assert abs(min(rear[j + 1][0] - rear[j][0] for j in range(len(rear) - 1)) -
           enc.CARRIER_X_M * 1000 - 0.4) < 1e-9

# The current knob receiver contract accepts the actual D shaft with 0.15 mm
# flat-direction clearance and 2.4 mm nominal axial reserve.
assert abs(enc.KNOB_D_FLAT_Y_M - enc.FLAT_Y_M - 0.00015) < 1e-9
assert abs(enc.KNOB_RECEIVER_TOP_Z_M - enc.SHAFT_TIP_Z_M - 0.0024) < 1e-9
assert enc.FLAT_START_Z_M < enc.KNOB_D_START_Z_M
assert abs(enc.CARRIER_X_M / 2 -
           (enc.RISER_X_M + enc.CARRIER_FASTENER_CLEARANCE_D_M / 2) - 0.0009) < 1e-9
assert abs((enc.RISER_X_M - enc.RISER_RADIUS_M) - enc.BODY_X_M / 2 - 0.0005) < 1e-9
assert enc.PLATE_CLEARANCE_D_M == 0.0164
assert (enc.MAIN_PCB_CLEARANCE_X_M, enc.MAIN_PCB_CLEARANCE_Y_M) == (0.0204, 0.0166)
for obj in objects:
    assert obj.type == "MESH", obj.name
    assert_solid(obj)

# Negative control: name collision is rejected before partial encoder creation.
clean()
foreign_mesh = bpy.data.meshes.new("FOREIGN")
foreign_mesh.from_pydata([(0, 0, 0)], [], [])
foreign = bpy.data.objects.new("RK_ENCODER_BODY_1", foreign_mesh)
bpy.context.scene.collection.objects.link(foreign)
try:
    enc.build(layout)
    raise AssertionError("encoder build accepted an existing owned name")
except ValueError as exc:
    assert "overwrite existing objects" in str(exc)
assert bpy.data.objects["RK_ENCODER_BODY_1"].data is foreign_mesh

print("encoders fixture PASS", {
    "objects": 125,
    "checkpoints": 55,
    "mount_plane_mm": enc.MOUNT_Z_M * 1000,
    "body_bottom_mm": enc.BODY_BOTTOM_Z_M * 1000,
    "shaft_tip_mm": enc.SHAFT_TIP_Z_M * 1000,
    "bushing_projection_mm": (enc.BUSHING_TOP_Z_M - enc.NUT_HIGH_Z_M) * 1000,
    "carrier_to_knob_gap_mm": (enc.KNOB_BOTTOM_Z_M - enc.CARRIER_HIGH_Z_M) * 1000,
    "neighbor_body_clearance_mm": 7.5,
    "carrier_edge_ligament_mm": 0.9,
    "carrier_neighbor_gap_mm": 0.4,
})
checkpoint_tmp.cleanup()
