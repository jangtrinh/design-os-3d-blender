"""Plate/settings/media checks (phase-04 checks 6-10): per_plate_bbox_mm,
bed_fit, settings_types, slice_info_present, thumbnail_present. See
bambu_checks_container.py for checks 1-5."""
from __future__ import annotations

import bambu_3mf_geometry as geom
import bambu_3mf_reader as reader
from bambu_checks_common import BBOX_TOLERANCE_MM, BED_180, BED_256, result

_SCALAR_TYPES = (str,)


def _plate_world_bboxes(zf):
    root = geom.read_model_xml(zf)
    local_geometry = geom.resolve_geometry(zf, root)
    build_items = geom.read_build_items(root)
    world = geom.world_vertices_by_instance(local_geometry, build_items)
    settings = reader.read_model_settings(zf)
    bboxes = {}
    for plate in settings["plates"]:
        pid = plate["plater_id"] or "?"
        points = [
            pt
            for inst in plate["instances"]
            for pt in world.get((inst["object_id"], inst["instance_id"]), [])
        ]
        if not points:
            bboxes[pid] = None
            continue
        xs, ys, zs = zip(*points)
        bboxes[pid] = {
            "object_ids": plate["object_ids"],
            "min_x": min(xs), "max_x": max(xs),
            "min_y": min(ys), "max_y": max(ys),
            "min_z": min(zs), "max_z": max(zs),
        }
    return bboxes


def check_per_plate_bbox_mm(zf, expect=None):
    bboxes = _plate_world_bboxes(zf)
    measured = {"plates": bboxes}
    if any(b is None for b in bboxes.values()):
        empty = [pid for pid, b in bboxes.items() if b is None]
        return result("per_plate_bbox_mm", "FAIL", f"plate(s) with no resolvable geometry: {empty}", measured)
    if expect is None:
        note = "; ".join(
            f"plate {pid}: dX={b['max_x']-b['min_x']:.3f} dY={b['max_y']-b['min_y']:.3f} "
            f"dZ={b['max_z']-b['min_z']:.3f} mm" for pid, b in bboxes.items()
        )
        return result("per_plate_bbox_mm", "INFO", note or "no plates", measured)
    diffs = []
    expected_plates = expect.get("plates", {})
    for pid, expected in expected_plates.items():
        actual = bboxes.get(pid)
        if actual is None:
            diffs.append(f"plate {pid}: missing in measured output")
            continue
        exp_box = expected["bbox_mm"]
        for key in ("min_x", "max_x", "min_y", "max_y", "min_z", "max_z"):
            if abs(actual[key] - exp_box[key]) > BBOX_TOLERANCE_MM:
                diffs.append(f"plate {pid} {key}: expected {exp_box[key]:.3f}, got {actual[key]:.3f}")
    if diffs:
        return result("per_plate_bbox_mm", "FAIL", "; ".join(diffs), measured)
    return result("per_plate_bbox_mm", "PASS", f"matches --expect within {BBOX_TOLERANCE_MM} mm", measured)


def _fits_sorted_xy(footprint_xy, bed_xy):
    """Sorted-footprint comparison (90 deg in-plane rotation allowed,
    diagonal placement is not) -- same rule as
    scripts/production_gate/bed_fit.py::_fits_xy, no brim margin (this
    checks already-placed final geometry, not a pre-print design screen)."""
    fp = sorted(footprint_xy)
    bed = sorted(bed_xy)
    return fp[0] < bed[0] and fp[1] < bed[1]


def check_bed_fit(zf, bed_mm=BED_180):
    """`bed_mm` (from --bed, default A1-mini 180^3) is evaluated as a
    THIRD fit alongside the two stock sizes -- fits_bed -- using the same
    sorted-footprint + height-under-Z rule as fits_180/fits_256, not just
    echoed back as bed_requested_mm."""
    bboxes = _plate_world_bboxes(zf)
    plates_out = {}
    for pid, b in bboxes.items():
        if b is None:
            plates_out[pid] = {"fits_180": None, "fits_256": None, "fits_bed": None}
            continue
        footprint = (b["max_x"] - b["min_x"], b["max_y"] - b["min_y"])
        height = b["max_z"] - b["min_z"]
        plates_out[pid] = {
            "footprint_mm": [round(v, 3) for v in footprint],
            "height_mm": round(height, 3),
            "fits_180": _fits_sorted_xy(footprint, BED_180[:2]) and height < BED_180[2],
            "fits_256": _fits_sorted_xy(footprint, BED_256[:2]) and height < BED_256[2],
            "fits_bed": _fits_sorted_xy(footprint, bed_mm[:2]) and height < bed_mm[2],
        }
    note = "; ".join(
        f"plate {pid}: fits A1-mini(180)={v['fits_180']} fits X1C/P1S(256)={v['fits_256']} "
        f"fits_requested_bed={v['fits_bed']}"
        for pid, v in plates_out.items()
    )
    return result("bed_fit", "INFO",
                   note + " -- informational only, never fails (no slicer ran; printer_model in "
                   "project_settings.config is the declared source of truth)",
                   {"plates": plates_out, "bed_requested_mm": list(bed_mm)})


def _bad_settings_keys(settings):
    bad = []
    for key, value in settings.items():
        if isinstance(value, _SCALAR_TYPES):
            continue
        if isinstance(value, list) and all(isinstance(v, _SCALAR_TYPES) for v in value):
            continue
        bad.append(key)
    return bad


def check_settings_types(zf):
    try:
        settings = reader.read_project_settings(zf)
    except Exception as exc:  # noqa: BLE001 -- report any parse failure as FAIL, not a crash
        return result("settings_types", "FAIL", f"project_settings.config is not valid JSON: {exc}", {})
    if not isinstance(settings, dict):
        return result("settings_types", "FAIL", "project_settings.config top level is not a JSON object", {})
    bad = _bad_settings_keys(settings)
    measured = {"n_keys": len(settings), "bad_keys": bad}
    if bad:
        return result("settings_types", "FAIL",
                       f"non-string-typed value(s), not written by Bambu Studio: {bad}", measured)
    return result("settings_types", "PASS", f"{len(settings)} keys, all scalars string-typed", measured)


def check_slice_info_present(zf):
    info = reader.read_slice_info(zf)
    if not info["present"]:
        return result("slice_info_present", "SKIP", f"{reader.SLICE_INFO_PATH} absent -- project not sliced", info)
    if info["parse_error"]:
        return result("slice_info_present", "FAIL", f"present but unparseable: {info['parse_error']}", info)
    if not info["sliced"]:
        return result("slice_info_present", "SKIP", "present, header-only -- project not yet sliced", info)
    return result("slice_info_present", "PASS", "present and parseable with slice results", info)


def check_thumbnail_present(zf):
    names = set(zf.namelist())
    settings = reader.read_model_settings(zf)
    missing = []
    for plate in settings["plates"]:
        pid = plate["plater_id"] or "?"
        thumb = plate["thumbnail_file"]
        if not thumb:
            missing.append(f"plate {pid}: no thumbnail_file key")
        elif thumb not in names:
            missing.append(f"plate {pid}: {thumb} not in archive")
    measured = {"plates_checked": len(settings["plates"]), "missing": missing}
    if missing:
        return result("thumbnail_present", "FAIL", "; ".join(missing), measured)
    return result("thumbnail_present", "PASS", f"{len(settings['plates'])} plate thumbnail(s) present", measured)
