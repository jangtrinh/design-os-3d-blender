"""Orchestrates stl_reader + model_xml + config_writer + zip_writer into a
format-faithful Bambu-like .3mf fixture, plus the independently-checkable
`.expected.json` ground truth (per-plate object ids + bbox in mm).

Numbering convention mirrors the real Bambu 3MF observed this session: each
mesh gets an odd object id, wrapped by a `<components>` object at the next
even id (mesh=1 -> wrapper=2, mesh=3 -> wrapper=4, ...). The wrapper's
component transform is always identity; all world placement lives on the
<build><item> transform -- matching the real file exactly.
"""
from __future__ import annotations

import uuid

from config_writer import build_model_settings_xml, build_project_settings_json, build_slice_info_xml
from model_xml import build_model_rels_xml, build_object_model_xml, build_root_model_xml
from zip_writer import CONTENT_TYPES_XML, build_root_rels_xml, make_1x1_png, write_deterministic_zip

# Fixed namespace so uuid5() is 100% deterministic across runs/machines.
_UUID_NAMESPACE = uuid.UUID("6f1b2c3d-0000-4000-8000-00000000f1de")
_GENERATOR_APPLICATION = "makerworld-pipeline fixture-generator 1.0 (not Bambu Studio)"
_FIXED_DATE = "2026-01-01"
_BED_ROW_SPACING_MM = 50.0
_PLATE_SEPARATION_MM = 300.0
_ROW_CENTER_MM = 100.0


def _deterministic_uuid(seed: str) -> str:
    return str(uuid.uuid5(_UUID_NAMESPACE, seed))


def _bbox(vertices: list[tuple[float, float, float]]) -> dict[str, float]:
    xs, ys, zs = [v[0] for v in vertices], [v[1] for v in vertices], [v[2] for v in vertices]
    return {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys), "min_z": min(zs), "max_z": max(zs)}


def _translate(vertices: list[tuple[float, float, float]], t: tuple[float, float, float]) -> list[tuple[float, float, float]]:
    return [(v[0] + t[0], v[1] + t[1], v[2] + t[2]) for v in vertices]


def build_fixture(stl_entries: list[dict], plate_count: int) -> tuple[dict[str, bytes], dict]:
    """`stl_entries`: [{"name": str, "vertices": [...], "triangles": [...],
    "source_path": str, "source_sha256": str}] in the order objects should
    be assigned to plates (round-robin: object i -> plate (i % plate_count)).

    Returns (zip_members, expected) where `expected` is the ground truth
    written to the `.expected.json` sidecar.
    """
    if plate_count < 1:
        raise ValueError("plate_count must be >= 1")

    plate_object_counts: dict[int, int] = {}
    for i in range(len(stl_entries)):
        plate_index = i % plate_count
        plate_object_counts[plate_index] = plate_object_counts.get(plate_index, 0) + 1
    plate_seen: dict[int, int] = {}

    objects_meta = []  # for model_settings.config
    root_objects = []  # for 3dmodel.model
    zip_members: dict[str, bytes] = {}
    plates_instances: dict[str, list[dict]] = {}
    expected_plates: dict[str, dict] = {}
    identify_counter = 1

    for i, entry in enumerate(stl_entries):
        mesh_id = 2 * i + 1
        wrapper_id = 2 * i + 2
        plate_index = i % plate_count
        plate_id = str(plate_index + 1)
        slot_in_plate = plate_seen.get(plate_index, 0)
        plate_seen[plate_index] = slot_in_plate + 1
        n_in_plate = plate_object_counts[plate_index]

        object_path = f"/3D/Objects/{entry['name']}_{mesh_id}.model"
        zip_members[object_path.lstrip("/")] = build_object_model_xml(
            mesh_id, entry["vertices"], entry["triangles"]
        ).encode("utf-8")

        min_local_z = min(v[2] for v in entry["vertices"])
        tx = plate_index * _PLATE_SEPARATION_MM + _ROW_CENTER_MM + (slot_in_plate - (n_in_plate - 1) / 2) * _BED_ROW_SPACING_MM
        ty = _ROW_CENTER_MM
        tz = -min_local_z
        item_transform = [1, 0, 0, 0, 1, 0, 0, 0, 1, tx, ty, tz]

        root_objects.append({
            "wrapper_id": wrapper_id,
            "wrapper_uuid": _deterministic_uuid(f"wrapper-{wrapper_id}"),
            "mesh_id": mesh_id,
            "object_path": object_path,
            "item_uuid": _deterministic_uuid(f"item-{wrapper_id}"),
            "item_transform": item_transform,
        })

        objects_meta.append({
            "wrapper_id": wrapper_id,
            "mesh_id": mesh_id,
            "name": entry["name"],
            "extruder": str((i % 4) + 1),
        })

        instance_id = 0
        plates_instances.setdefault(plate_id, []).append({
            "object_id": wrapper_id,
            "instance_id": instance_id,
            "identify_id": identify_counter,
        })
        identify_counter += 1

        world_vertices = _translate(entry["vertices"], (tx, ty, tz))
        plate_bucket = expected_plates.setdefault(plate_id, {"object_ids": [], "vertices": []})
        plate_bucket["object_ids"].append(str(wrapper_id))
        plate_bucket["vertices"].extend(world_vertices)

    expected = {
        "generator": "make_bambu_like_fixture.py",
        "source_stls": [
            {"path": e["source_path"], "sha256": e["source_sha256"]} for e in stl_entries
        ],
        "plates": {
            pid: {"object_ids": data["object_ids"], "bbox_mm": _bbox(data["vertices"])}
            for pid, data in expected_plates.items()
        },
    }

    root_metadata = {
        "Application": _GENERATOR_APPLICATION,
        "BambuStudio:3mfVersion": "1",
        "CopyRight": "",
        "CreationDate": _FIXED_DATE,
        "Description": "",
        "Designer": "",
        "DesignerCover": "",
        "DesignerUserId": "",
        "License": "",
        "ModificationDate": _FIXED_DATE,
        "Origin": "",
        "Title": "",
    }
    build_uuid = _deterministic_uuid("build")
    zip_members["3D/3dmodel.model"] = build_root_model_xml(root_metadata, root_objects, build_uuid).encode("utf-8")
    zip_members["3D/_rels/3dmodel.model.rels"] = build_model_rels_xml(
        [o["object_path"] for o in root_objects]
    ).encode("utf-8")
    zip_members["[Content_Types].xml"] = CONTENT_TYPES_XML.encode("utf-8")

    thumbnail_target = "/Metadata/plate_1.png"
    zip_members["_rels/.rels"] = build_root_rels_xml(thumbnail_target).encode("utf-8")

    zip_members["Metadata/model_settings.config"] = build_model_settings_xml(
        objects_meta, plates_instances
    ).encode("utf-8")
    zip_members["Metadata/project_settings.config"] = build_project_settings_json(plate_count).encode("utf-8")
    zip_members["Metadata/slice_info.config"] = build_slice_info_xml("00.00.01.00").encode("utf-8")

    png_bytes = make_1x1_png()
    for plate_id in plates_instances:
        zip_members[f"Metadata/plate_{plate_id}.png"] = png_bytes

    return zip_members, expected


def write_fixture(out_path: str, stl_entries: list[dict], plate_count: int) -> dict:
    zip_members, expected = build_fixture(stl_entries, plate_count)
    write_deterministic_zip(out_path, zip_members)
    return expected
