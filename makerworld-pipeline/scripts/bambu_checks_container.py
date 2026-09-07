"""Container/geometry/placement checks (phase-04 checks 1-5): container_zip,
bambu_project_layout, geometry_resolved, build_items_placed,
plate_membership. See bambu_checks_plates.py for checks 6-10."""
from __future__ import annotations

import xml.etree.ElementTree as ET

import bambu_3mf_geometry as geom
import bambu_3mf_reader as reader
from bambu_checks_common import result


def check_container_zip(zf, max_uncompressed_bytes=reader.DEFAULT_MAX_UNCOMPRESSED_BYTES,
                         max_ratio=reader.DEFAULT_MAX_COMPRESSION_RATIO):
    report = reader.zip_safety_report(zf, max_uncompressed_bytes, max_ratio)
    measured = {
        "n_entries": report["n_entries"],
        "total_uncompressed_bytes": report["total_uncompressed_bytes"],
    }
    if report["problems"]:
        return result("container_zip", "FAIL", "; ".join(report["problems"]), measured)
    return result("container_zip", "PASS", "valid ZIP, no path traversal, under size cap", measured)


def check_bambu_project_layout(zf):
    members = reader.read_required_members(zf)
    rels = reader.read_root_rels(zf)
    problems = []
    if members["missing"]:
        problems.append("missing: " + ", ".join(members["missing"]))
    if rels is None:
        problems.append(f"missing or unparseable {reader.ROOT_RELS_PATH}")
    elif not any(r["target"] == "/" + reader.MODEL_PATH for r in rels):
        problems.append(f"{reader.ROOT_RELS_PATH} has no relationship targeting {reader.MODEL_PATH}")
    measured = {"present": members["present"], "missing": members["missing"],
                "rels_ok": rels is not None}
    if problems:
        return result("bambu_project_layout", "FAIL", "; ".join(problems), measured)
    return result("bambu_project_layout", "PASS", "required members + OPC rels present", measured)


def check_geometry_resolved(zf):
    try:
        root = geom.read_model_xml(zf)
    except (ET.ParseError, KeyError) as exc:
        return result("geometry_resolved", "FAIL", f"cannot parse {geom.MODEL_PATH}: {exc}",
                       {"total_vertices": 0})
    resolved = geom.resolve_geometry(zf, root)
    unresolved = [oid for oid, g in resolved.items() if g["kind"] == "unresolved"]
    total_vertices = sum(len(g["vertices"]) for g in resolved.values())
    measured = {"objects_resolved": len(resolved) - len(unresolved),
                "objects_total": len(resolved), "total_vertices": total_vertices}
    if unresolved or total_vertices == 0:
        note = f"unresolved object ids: {unresolved}" if unresolved else "0 vertices resolved"
        return result("geometry_resolved", "FAIL", note, measured)
    return result("geometry_resolved", "PASS",
                   f"{len(resolved)} objects resolved, {total_vertices} vertices total", measured)


def check_build_items_placed(zf):
    root = geom.read_model_xml(zf)
    resource_ids = set(geom.model_objects_by_id(root).keys())
    items = geom.read_build_items(root)
    if not items:
        return result("build_items_placed", "FAIL", "no <build><item> entries found", {"n_items": 0})
    bad = []
    for item in items:
        oid = item["objectid"]
        label = f'{oid} (instance {item["instance_id"]})'
        if oid not in resource_ids:
            bad.append(f"{label}: no matching <object id=\"{oid}\">")
        elif item["transform"] is None:
            bad.append(f"{label}: missing/malformed 12-float transform")
    measured = {"n_items": len(items)}
    if bad:
        return result("build_items_placed", "FAIL", "; ".join(bad), measured)
    return result("build_items_placed", "PASS", f"{len(items)} build items, all resolvable + transformed", measured)


def check_plate_membership(zf):
    """Every placed (object_id, instance_id) pair belongs to exactly one
    plate. Compares MULTISETS of (object_id, instance_id) pairs, not sets
    of bare object_ids: two <model_instance> entries for the same
    object_id on the SAME plate (a duplicated part) are two distinct
    pairs and must not be reported as "on more than one plate"."""
    root = geom.read_model_xml(zf)
    build_pairs = {(item["objectid"], item["instance_id"]) for item in geom.read_build_items(root)}
    settings = reader.read_model_settings(zf)
    all_plate_pairs = [
        (inst["object_id"], inst["instance_id"])
        for plate in settings["plates"]
        for inst in plate["instances"]
    ]
    seen = set()
    duplicates = set()
    for pair in all_plate_pairs:
        (duplicates if pair in seen else seen).add(pair)
    orphan_build_items = sorted(build_pairs - seen)
    dangling_plate_refs = sorted(seen - build_pairs)
    problems = []
    if duplicates:
        problems.append(f"instance(s) on more than one plate: {sorted(duplicates)}")
    if orphan_build_items:
        problems.append(f"placed but not on any plate: {orphan_build_items}")
    if dangling_plate_refs:
        problems.append(f"plate references object not placed by <build>: {dangling_plate_refs}")
    measured = {"plates": len(settings["plates"]), "objects_total": len(seen)}
    if problems:
        return result("plate_membership", "FAIL", "; ".join(problems), measured)
    return result("plate_membership", "PASS", "every placed object belongs to exactly one plate", measured)
