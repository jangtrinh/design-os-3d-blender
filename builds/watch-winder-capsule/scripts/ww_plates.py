"""Print-plate layout data + geometry for the watch-winder capsule (pure, no bpy).

Everything here is in MILLIMETRES; the caller converts once (1 BU = 1 m). The
ORIENTATIONS table is the design input from
plans/reports/researcher-260906-1334-print-plate-layout-watch-winder.md, but every
rotation was checked against the baked meshes in watch-winder-capsule-print.blend
before being written down (see reports/print-plates.json `measured`):
  * shell      opening + flat rim (r 52..54.5) at z max -> Rx180 puts the rim down;
  * cushion    keyed socket opens at -z (36 axis verts in the bottom 7 mm vs 1 at
               the top) -> Rx180 opens it upward;
  * knob/knurl/boss lie on local X (L side at x<0, inner face at the larger x)
               -> Ry(+90) drops the inner/boss face; the mirrored R uses Ry(-90);
  * rear_service_cover, visor, rotor_cup, liner, rim, guilloche, shaft, legs, feet,
               hinges, tab are already baked axis-aligned with the print-up face at
               +z (cover convex side up, visor dome up, cup mouth up) -> identity.
Tilts recommended by the research are recorded, never modelled: tilt is slicer-side.
"""
import math

from mathutils import Matrix, Vector

SPACING_MM = 6.0
MARGIN_MM = 8.0
PLATE_GAP_MM = 60.0
SLAB_THICKNESS_MM = 3.0

# bucket -> (x, y) plate mm. FDM = Bambu X1C class, resin = Elegoo Saturn-4-Ultra-12K class.
PLATE_SIZES = {
    "fdm-petg": (256.0, 256.0), "fdm-abs": (256.0, 256.0), "fdm-tpu": (256.0, 256.0),
    "sla-proxy": (218.0, 123.0), "sla-clear": (218.0, 123.0),
}
# bucket -> (process, material, look hex | None for the glass-like clear resin, roughness)
BUCKETS = {
    "fdm-petg": ("FDM 0.4 mm / 0.2 mm layers", "PETG (matte)", "#1A1D24", 0.58),
    "fdm-abs": ("FDM (enclosure)", "ABS (satin black)", "#101010", 0.45),
    "fdm-tpu": ("FDM TPU", "TPU 85A", "#202226", 0.75),
    "sla-proxy": ("SLA proxy", "grey resin (proxy for machined metal)", "#9A9A9A", 0.60),
    "sla-clear": ("SLA clear", "clear resin (proxy for formed PMMA)", None, 0.05),
}
# (instance, source object, bucket, mirror_x, rotation (axis, deg) | None, tilt deg, supports)
ORIENTATIONS = [
    ("shell", "WW_SHELL", "fdm-petg", False, ("X", 180.0), 0.0,
     "minimal, only under the hatch/USB bosses; rim-down needs a brim (PETG flat-plate warp)"),
    ("rear_service_cover", "WW_REAR_SERVICE_COVER", "fdm-petg", False, None, 0.0, "none"),
    ("rotor_cup", "WW_ROTOR_CUP", "fdm-abs", False, None, 0.0,
     "light supports on interior undercuts only; mouth up so the 78 mm cavity traps none"),
    ("inner_liner", "WW_INNER_LINER", "fdm-abs", False, None, 0.0, "none"),
    ("cushion", "WW_CUSHION", "fdm-tpu", False, ("X", 180.0), 0.0,
     "none; keyed socket opens upward so nothing is trapped in the 6.4 mm bore"),
    ("foot_01", "WW_FOOT_01", "fdm-tpu", False, None, 0.0, "none"),
    ("foot_02", "WW_FOOT_01", "fdm-tpu", False, None, 0.0, "none"),
    ("foot_03", "WW_FOOT_01", "fdm-tpu", False, None, 0.0, "none"),
    ("front_rim", "WW_FRONT_RIM", "sla-proxy", False, None, 12.0,
     "minimal edge supports; tilt breaks the flat plane against FEP suction"),
    ("guilloche", "WW_GUILLOCHE", "sla-proxy", False, None, 17.0,
     "minimal, edge-only; the 0.12 mm relief faces away from the supports"),
    ("knob_l", "WW_KNOB_L", "sla-proxy", False, ("Y", 90.0), 0.0, "minor supports at the base"),
    ("knob_r", "WW_KNOB_L", "sla-proxy", True, ("Y", -90.0), 0.0, "minor supports at the base"),
    ("knurl_l", "WW_KNURL_L", "sla-proxy", False, ("Y", 90.0), 0.0,
     "minor; knurl pitch resolves along print Z on a vertical axis"),
    ("knurl_r", "WW_KNURL_L", "sla-proxy", True, ("Y", -90.0), 0.0,
     "minor; knurl pitch resolves along print Z on a vertical axis"),
    ("knob_boss_l", "WW_KNOB_BOSS_L", "sla-proxy", False, ("Y", 90.0), 0.0, "minor"),
    ("knob_boss_r", "WW_KNOB_BOSS_L", "sla-proxy", True, ("Y", -90.0), 0.0, "minor"),
    ("shaft", "WW_SHAFT", "sla-proxy", False, None, 0.0,
     "small tip supports at one end; vertical keeps the 1 mm D-flat faithful"),
    ("leg_01", "WW_LEG_01", "sla-proxy", False, None, 7.0, "base supports"),
    ("leg_02", "WW_LEG_01", "sla-proxy", False, None, 7.0, "base supports"),
    ("leg_03", "WW_LEG_01", "sla-proxy", False, None, 7.0, "base supports"),
    ("hinge_fixed", "WW_HINGE_FIXED", "sla-proxy", False, None, 0.0,
     "minimal; flat on the 21.6 mm axis supports both clevis lugs without bridging"),
    ("hinge_moving", "WW_HINGE_MOVING", "sla-proxy", False, None, 0.0, "minimal"),
    ("finger_tab", "WW_FINGER_TAB", "sla-proxy", False, None, 0.0, "none"),
    ("visor", "WW_VISOR", "sla-clear", False, None, 25.0,
     "moderate edge supports away from the optical surface; drain holes at the tilted rim low point"),
]
FIELDS = ("instance", "source", "bucket", "mirror", "rotation", "recommended_tilt_deg", "supports_note")
# post-orientation bbox height (mm) the caller must confirm; tolerance 0.2 mm
EXPECTED_HEIGHT_MM = {"shell": 113.9, "cushion": 38.0, "knob_l": 8.0, "knob_r": 8.0,
                      "leg_01": 38.7, "leg_02": 38.7, "leg_03": 38.7}


def instances():
    """The 24 printable instances: 17 baked parts + 3 mirrors + 2 leg + 2 foot copies."""
    return [dict(zip(FIELDS, row)) for row in ORIENTATIONS]


def mirror_mesh(verts, faces):
    """x -> -x with reversed winding, so a mirrored part keeps outward normals."""
    return ([Vector((-v[0], v[1], v[2])) for v in verts],
            [tuple(reversed(tuple(f))) for f in faces])


def orient_mesh(verts, rotation):
    """Rotate a vertex list by (axis, degrees); `rotation` None returns a copy."""
    if rotation is None:
        return [Vector(v) for v in verts]
    axis, deg = rotation
    m = Matrix.Rotation(math.radians(deg), 3, axis)
    return [m @ Vector(v) for v in verts]


def drop_to_plate(verts):
    """Translate so the bbox min corner sits at the origin. Returns (verts, w, h, height)."""
    lo = Vector((min(v[0] for v in verts), min(v[1] for v in verts), min(v[2] for v in verts)))
    hi = Vector((max(v[0] for v in verts), max(v[1] for v in verts), max(v[2] for v in verts)))
    return [Vector(v) - lo for v in verts], hi.x - lo.x, hi.y - lo.y, hi.z - lo.z


def effective_margin(items, plate_w, plate_h, margin=MARGIN_MM):
    """Largest margin <= `margin` at which every item still fits in some 0/90 orientation.

    Shrinks when a part is wider than plate - 2*margin (the 112 mm front_rim on the
    123 mm resin axis); the caller MUST report a reduced margin rather than hide it.
    Raises when a part does not fit the plate at all — that is a spec problem.
    """
    m = float(margin)
    for pid, w, h in items:
        best = max(min((plate_w - a) / 2.0, (plate_h - b) / 2.0) for a, b in ((w, h), (h, w)))
        if best < 0:
            raise AssertionError(f"{pid} ({w:.1f}x{h:.1f} mm) does not fit a {plate_w}x{plate_h} mm plate")
        m = min(m, best)
    return max(0.0, round(m, 4))


def pack_shelf(items, plate_w, plate_h, margin, spacing=SPACING_MM):
    """Guillotine free-rectangle bin pack with 0/90 rotation only (no scipy).

    Each item is inflated by `spacing` on its +x/+y sides and placed into the free
    rectangle with the best short-side fit; the used rectangle is then split into a
    right and a top remainder (guillotine). Unlike a shelf packer this fills the region
    beside a tall part (the 112 mm front_rim on the 123 mm resin axis).
    items: [(id, w, h)] in mm. Returns (placements, overflow) where a placement is
    (id, x, y, w, h, rot90) and (x, y) is the part's min corner on the plate.
    """
    order = sorted(items, key=lambda it: (-max(it[1], it[2]), -it[1] * it[2], it[0]))
    free = [[margin, margin, plate_w - 2 * margin + spacing, plate_h - 2 * margin + spacing]]  # x, y, w, h
    placed, overflow = [], []
    for pid, w, h in order:
        best = None
        for pw, ph, rot in ((w, h, False), (h, w, True)):
            iw, ih = pw + spacing, ph + spacing
            for i, (fx, fy, fw, fh) in enumerate(free):
                if iw <= fw + 1e-9 and ih <= fh + 1e-9:
                    score = (min(fw - iw, fh - ih), max(fw - iw, fh - ih))
                    if best is None or score < best[0]:
                        best = (score, i, pw, ph, rot)
        if best is None:
            overflow.append((pid, w, h))
            continue
        _, i, pw, ph, rot = best
        fx, fy, fw, fh = free.pop(i)
        iw, ih = pw + spacing, ph + spacing
        placed.append((pid, fx, fy, pw, ph, rot))
        # guillotine split along the shorter leftover axis so the larger remainder stays whole
        if fw - iw < fh - ih:
            right, top = [fx + iw, fy, fw - iw, ih], [fx, fy + ih, fw, fh - ih]
        else:
            right, top = [fx + iw, fy, fw - iw, fh], [fx, fy + ih, iw, fh - ih]
        free += [r for r in (right, top) if r[2] > 1e-6 and r[3] > 1e-6]
        free = [a for a in free if not any(b is not a and a[0] >= b[0] and a[1] >= b[1]
                                           and a[0] + a[2] <= b[0] + b[2] and a[1] + a[3] <= b[1] + b[3] for b in free)]
    return placed, overflow


def pack_bucket(bucket, items, margin=MARGIN_MM, spacing=SPACING_MM):
    """Pack one material bucket onto as many identical plates as it needs (never mixes)."""
    pw, ph = PLATE_SIZES[bucket]
    m = effective_margin(items, pw, ph, margin)
    plates, rest, n = [], list(items), 0
    while rest:
        n += 1
        placed, rest = pack_shelf(rest, pw, ph, m, spacing)
        assert placed, f"{bucket}: nothing fits on an empty plate ({rest})"
        used = sum(w * h for _i, _x, _y, w, h, _r in placed)
        plates.append({"id": f"{bucket}-{n:02d}", "bucket": bucket, "size_mm": [pw, ph],
                       "margin_mm": m, "margin_requested_mm": float(margin),
                       "margin_reduced": m < margin - 1e-9, "spacing_mm": float(spacing),
                       "utilisation_pct": round(100.0 * used / (pw * ph), 2),
                       "placements": placed})
    return plates


def check_placements(plate, spacing=SPACING_MM):
    """The packer's own contract, re-checked on the built result: every part inside
    plate - margin, every pairwise XY bbox gap >= spacing. Returns (min_gap_mm, overlaps)."""
    pw, ph, m, parts = plate["size_mm"][0], plate["size_mm"][1], plate["margin_mm"], plate["parts"]
    for a in parts:
        x, y, w, h = a["position_mm"][0], a["position_mm"][1], a["bbox_mm"][0], a["bbox_mm"][1]
        assert m - 1e-6 <= x and x + w <= pw - m + 1e-6, (plate["id"], a["instance"], "x", x, w)
        assert m - 1e-6 <= y and y + h <= ph - m + 1e-6, (plate["id"], a["instance"], "y", y, h)
    gap, bad = 1e9, []
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            g = max(max(a["position_mm"][0] - b["position_mm"][0] - b["bbox_mm"][0],
                        b["position_mm"][0] - a["position_mm"][0] - a["bbox_mm"][0]),
                    max(a["position_mm"][1] - b["position_mm"][1] - b["bbox_mm"][1],
                        b["position_mm"][1] - a["position_mm"][1] - a["bbox_mm"][1]))
            gap = min(gap, round(g, 4))
            if g < spacing - 1e-6:
                bad.append([plate["id"], a["instance"], b["instance"], round(g, 4)])
    return gap, bad
