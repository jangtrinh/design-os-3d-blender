"""Bed-fit preflight: does a part's measured footprint (plus brim margin) and
height fit inside a target printer's build volume, in the orientation it is
modelled?

Uses meshprep.bbox_mm (already the oracle for dimensions.py) -- no slicer, no
new geometry sampling. This is a DESIGN-TIME SCREEN, not print-success
evidence: report.standing_exclusions already states no slicer ran.
"""
from __future__ import annotations

from . import meshprep
from .report import check

# X1C / P1S / A1 share this bed; the largest common Bambu bed (controller
# ruling 2026-09-07: existing builds must not newly fail the gate).
DEFAULT_VOLUME_MM = (256.0, 256.0, 256.0)
DEFAULT_BRIM_MARGIN_MM = 5.0
# A1 mini's smaller bed; informational compatibility check only.
A1_MINI_VOLUME_MM = (180.0, 180.0, 180.0)


def _resolve(part, spec, field, default):
    """part override > spec > default."""
    if field in part:
        return part[field], "part"
    if field in spec:
        return spec[field], "spec"
    return default, "default"


def _fits_xy(footprint_xy, usable_xy):
    """Sorted-footprint comparison: a 90 deg in-plane rotation is allowed
    (the slicer may swap X/Y), diagonal placement is not. Strict '<' so a
    footprint exactly flush with the usable edge is not called a fit."""
    fp = sorted(footprint_xy)
    us = sorted(usable_xy)
    return fp[0] < us[0] and fp[1] < us[1]


def checks(bm, part, spec, prefix=""):
    dims = meshprep.bbox_mm(bm)
    footprint_xy, height = dims[:2], dims[2]
    volume, vol_source = _resolve(part, spec, "print_volume_mm", list(DEFAULT_VOLUME_MM))
    margin, _margin_source = _resolve(part, spec, "brim_margin_mm", DEFAULT_BRIM_MARGIN_MM)
    volume = [float(v) for v in volume]
    margin = float(margin)
    usable_xy = [volume[0] - 2.0 * margin, volume[1] - 2.0 * margin]
    fp_ok = _fits_xy(footprint_xy, usable_xy)
    ht_ok = height < volume[2]
    measured = {"bed_volume_mm": volume, "footprint_mm": [round(d, 4) for d in dims],
                "brim_margin_mm": margin}
    out = [
        check(prefix + "bed_fit_footprint_mm", "pass" if fp_ok else "fail",
              [round(d, 4) for d in footprint_xy],
              {"bed_xy_mm": volume[:2], "brim_margin_mm": margin,
               "usable_xy_mm": [round(u, 4) for u in usable_xy]},
              "sorted footprint vs sorted usable bed X/Y (bed minus 2x brim margin); "
              "90 deg in-plane rotation allowed, diagonal placement is not; "
              "no slicer ran, this is a design-time SCREEN"),
        check(prefix + "bed_fit_height_mm", "pass" if ht_ok else "fail",
              round(height, 4), {"bed_z_mm": volume[2]},
              "part height (Z axis, not swappable) vs bed Z; no slicer ran"),
        check(prefix + "bed_fit_volume_source", "info", vol_source, None,
              "print_volume_mm resolved from %s (part override > spec > "
              "default %s)" % (vol_source, list(DEFAULT_VOLUME_MM))),
    ]
    a1_usable_xy = [A1_MINI_VOLUME_MM[0] - 2.0 * margin, A1_MINI_VOLUME_MM[1] - 2.0 * margin]
    a1_ok = _fits_xy(footprint_xy, a1_usable_xy) and height < A1_MINI_VOLUME_MM[2]
    out.append(check(
        prefix + "bed_fit_a1_mini_compatible", "info", a1_ok,
        {"bed_mm": list(A1_MINI_VOLUME_MM), "brim_margin_mm": margin},
        "informational only, never fails the gate: does footprint + brim "
        "margin and height fit an A1 mini (%s mm) bed"
        % (list(A1_MINI_VOLUME_MM),)))
    return out, measured
