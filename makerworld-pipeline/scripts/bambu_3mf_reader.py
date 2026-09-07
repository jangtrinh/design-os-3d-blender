"""Structural reader for Bambu-Studio-shaped .3mf project files: container
safety, required-member presence, OPC rels, model-settings/project-settings/
slice-info parsing. Contains no PASS/FAIL judgement -- that lives in
bambu_checks.py. Geometry/transform math lives in bambu_3mf_geometry.py
(kept separate to stay under the project's 200-line-per-file guidance).

bbs_3mf.cpp constants this reader relies on (pinned, master branch,
fetched 2026-09-07 -- see researcher-260907-1114-bambu-3mf-oracle-tooling.md
Section 5): MODEL_FILE = "3D/3dmodel.model".
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
import zipfile

MODEL_PATH = "3D/3dmodel.model"
MODEL_SETTINGS_PATH = "Metadata/model_settings.config"
PROJECT_SETTINGS_PATH = "Metadata/project_settings.config"
SLICE_INFO_PATH = "Metadata/slice_info.config"
ROOT_RELS_PATH = "_rels/.rels"
REQUIRED_MEMBERS = (MODEL_PATH, MODEL_SETTINGS_PATH, PROJECT_SETTINGS_PATH)

# Defensive caps against a hostile/corrupt ZIP (zip-bomb style). These are
# NOT Bambu-spec values -- source: null, structural/defensive only.
DEFAULT_MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
DEFAULT_MAX_COMPRESSION_RATIO = 1000


class UnreadableInputError(Exception):
    """Input is not readable as a ZIP container at all (exit code 2)."""


def open_zip_safely(path):
    """Open path as a ZIP. Raises UnreadableInputError for anything that
    is not a ZIP at all (the exit-2 case); does NOT evaluate path
    traversal or size caps here -- that is check_container_zip's job."""
    try:
        return zipfile.ZipFile(path)
    except (FileNotFoundError, IsADirectoryError, PermissionError) as exc:
        raise UnreadableInputError(str(exc)) from exc
    except zipfile.BadZipFile as exc:
        raise UnreadableInputError(f"not a valid ZIP/3MF container: {exc}") from exc


def has_path_traversal(name):
    """True if a ZIP member name looks like it could escape an extraction
    root: absolute path, Windows drive/backslash, or a literal '..' path
    segment."""
    if name.startswith("/") or name.startswith("\\"):
        return True
    head = name.replace("\\", "/").split("/")[0]
    if len(head) == 2 and head[1] == ":":
        return True  # e.g. "C:evil.txt"
    parts = name.replace("\\", "/").split("/")
    return ".." in parts


def zip_safety_report(zf, max_uncompressed_bytes=DEFAULT_MAX_UNCOMPRESSED_BYTES,
                       max_ratio=DEFAULT_MAX_COMPRESSION_RATIO):
    """Scan the ZIP central directory (no decompression) for path
    traversal entries and an excessive claimed uncompressed size, either
    in total or for a single suspiciously-compressed entry."""
    problems = []
    total_uncompressed = 0
    for info in zf.infolist():
        if has_path_traversal(info.filename):
            problems.append(f"path traversal entry: {info.filename!r}")
        total_uncompressed += info.file_size
        if info.compress_size > 0:
            ratio = info.file_size / info.compress_size
            if ratio > max_ratio:
                problems.append(
                    f"entry {info.filename!r} compression ratio {ratio:.0f}x "
                    f"exceeds cap {max_ratio}x"
                )
    if total_uncompressed > max_uncompressed_bytes:
        problems.append(
            f"total uncompressed size {total_uncompressed} bytes exceeds "
            f"cap {max_uncompressed_bytes} bytes"
        )
    return {
        "problems": problems,
        "total_uncompressed_bytes": total_uncompressed,
        "n_entries": len(zf.infolist()),
    }


def read_required_members(zf):
    names = set(zf.namelist())
    present = [m for m in REQUIRED_MEMBERS if m in names]
    missing = [m for m in REQUIRED_MEMBERS if m not in names]
    return {"present": present, "missing": missing}


def read_root_rels(zf):
    """Parse _rels/.rels (OPC relationships). Returns None if missing or
    unparseable; otherwise a list of {id, type, target} dicts."""
    if ROOT_RELS_PATH not in zf.namelist():
        return None
    try:
        root = ET.fromstring(zf.read(ROOT_RELS_PATH))
    except ET.ParseError:
        return None
    rels_ns = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
    return [
        {
            "id": rel.attrib.get("Id"),
            "type": rel.attrib.get("Type"),
            "target": rel.attrib.get("Target"),
        }
        for rel in root.findall("r:Relationship", rels_ns)
    ]


def read_model_settings(zf):
    """Parse Metadata/model_settings.config. Returns
    {"objects": {id: {"name":.., "extruder":..}},
     "plates": [{"plater_id":.., "thumbnail_file":..,
                 "object_ids": [...],  # one entry per <model_instance>, may repeat an id for N instances
                 "instances": [{"object_id":.., "instance_id": int}, ...]}]}.
    instance_id defaults to 0 when the metadata key is absent (an
    old-format single-instance-per-object config)."""
    root = ET.fromstring(zf.read(MODEL_SETTINGS_PATH))
    objects = {}
    for obj in root.findall("object"):
        oid = obj.attrib.get("id")
        meta = {m.attrib["key"]: m.attrib.get("value") for m in obj.findall("metadata")}
        objects[oid] = {"name": meta.get("name"), "extruder": meta.get("extruder")}
    plates = []
    for plate in root.findall("plate"):
        meta = {m.attrib["key"]: m.attrib.get("value") for m in plate.findall("metadata")}
        instances = []
        for mi in plate.findall("model_instance"):
            obj_meta = mi.find("metadata[@key='object_id']")
            if obj_meta is None:
                continue
            inst_meta = mi.find("metadata[@key='instance_id']")
            raw_instance_id = inst_meta.attrib.get("value") if inst_meta is not None else "0"
            try:
                instance_id = int(raw_instance_id)
            except (TypeError, ValueError):
                instance_id = raw_instance_id  # leave as-is; comparison just won't match a build item
            instances.append({"object_id": obj_meta.attrib.get("value"), "instance_id": instance_id})
        plates.append({
            "plater_id": meta.get("plater_id"),
            "thumbnail_file": meta.get("thumbnail_file"),
            "object_ids": [inst["object_id"] for inst in instances],
            "instances": instances,
        })
    return {"objects": objects, "plates": plates}


def read_project_settings(zf):
    """Parse Metadata/project_settings.config as JSON. Raises
    json.JSONDecodeError to the caller on malformed JSON."""
    return json.loads(zf.read(PROJECT_SETTINGS_PATH).decode("utf-8"))


def read_slice_info(zf):
    """Parse Metadata/slice_info.config. Returns
    {"present": bool, "sliced": bool, "parse_error": str|None}.
    "sliced" follows bbs_3mf.cpp: a plate carries a per-object
    prediction/weight attribute (or a <filament> child) once actually
    sliced; header-only config means the project has never been sliced."""
    if SLICE_INFO_PATH not in zf.namelist():
        return {"present": False, "sliced": False, "parse_error": None}
    try:
        root = ET.fromstring(zf.read(SLICE_INFO_PATH))
    except ET.ParseError as exc:
        return {"present": True, "sliced": False, "parse_error": str(exc)}
    sliced = bool(root.findall(".//filament")) or any(
        "prediction" in obj.attrib or "weight" in obj.attrib
        for obj in root.iter("object")
    )
    return {"present": True, "sliced": sliced, "parse_error": None}
