"""Tests for the format-faithful Bambu-like 3MF fixture generator.

Two groups:
  1. Self-consistency: a generated fixture is a valid ZIP, has the required
     member set, build-item/object counts match, every component target
     resolves, and the recorded `.expected.json` bbox matches an INDEPENDENT
     bbox reader (re-implemented here, not imported from tools/) within
     0.01mm.
  2. Structural diff against a real Bambu Studio 3MF (SKIP when
     BAMBU_REAL_3MF is unset). Compares tag sets, attribute-key sets, and
     `metadata key=` name sets between the generated fixture and the real
     file. Values and geometry are never compared -- only shape/structure.

The real 3MF file path only ever reaches this module through the
BAMBU_REAL_3MF environment variable (never hardcoded), per the Native Asset
Policy: the file itself is never committed to this repository.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "makerworld-pipeline" / "tools" / "make_bambu_like_fixture.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
STL_A = REPO_ROOT / "builds" / "watch-winder-capsule" / "parts" / "finger_tab.stl"
STL_B = REPO_ROOT / "builds" / "watch-winder-capsule" / "parts" / "hinge_fixed.stl"

NS = {
    "m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
    "p": "http://schemas.microsoft.com/3dmanufacturing/production/2015/06",
}
IDENTITY = "1 0 0 0 1 0 0 0 1 0 0 0"


def _run_generator(args):
    return subprocess.run(
        [sys.executable, str(GENERATOR), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def _sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _local_name(tag):
    return tag.split("}")[-1] if "}" in tag else tag


def _collect_structural_facts(zip_path):
    """Scan a 3MF for structural facts only: tag names, attribute-key sets
    per tag, `metadata key=` names, and normalized ZIP member name patterns
    (digits collapsed to N so `plate_1.png`/`plate_2.png` compare equal)."""
    zf = zipfile.ZipFile(zip_path)
    member_patterns = set()
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        # Normalize only the basename, never the directory (collapsing the
        # whole path would mangle the literal "3D" directory into "ND").
        # Under 3D/Objects/ the mesh NAME itself is caller-chosen (Sphere,
        # Cube, finger_tab, ...) so the whole basename is wildcarded, not
        # just its digits; elsewhere (plate_1.png, top_1.png) only the
        # per-plate index digit varies, so only digits are collapsed.
        directory, _, basename = name.rpartition("/")
        if directory == "3D/Objects":
            normalized_basename = "*.model"
        else:
            normalized_basename = re.sub(r"\d+", "N", basename)
        member_patterns.add(f"{directory}/{normalized_basename}" if directory else normalized_basename)

    tag_names = set()
    attr_keys_by_tag = {}
    metadata_key_names = set()
    for member in zf.namelist():
        if not (member.endswith(".model") or member.endswith(".config")):
            continue
        try:
            root = ET.fromstring(zf.read(member))
        except ET.ParseError:
            continue  # non-XML config (e.g. JSON project_settings) -- skip
        for el in root.iter():
            tag = _local_name(el.tag)
            tag_names.add(tag)
            attr_keys_by_tag.setdefault(tag, set()).update(el.attrib.keys())
            if tag == "metadata" and "key" in el.attrib:
                metadata_key_names.add(el.attrib["key"])
    return {
        "member_patterns": member_patterns,
        "tag_names": tag_names,
        "attr_keys_by_tag": attr_keys_by_tag,
        "metadata_key_names": metadata_key_names,
    }


def _apply12(vertex, matrix):
    """Apply a 3MF 12-float column-major transform to a local vertex."""
    x, y, z = vertex
    return (
        matrix[0] * x + matrix[3] * y + matrix[6] * z + matrix[9],
        matrix[1] * x + matrix[4] * y + matrix[7] * z + matrix[10],
        matrix[2] * x + matrix[5] * y + matrix[8] * z + matrix[11],
    )


def _independent_world_bbox_per_plate(zf, root):
    """Re-derive per-plate world bbox straight from the 3MF core spec:
    resolve <component> targets, apply the build <item> transform, then
    group by plate via model_settings.config. Deliberately NOT calling into
    tools/ -- this is a from-scratch reader so the test can catch a bug in
    the generator's own transform math, not just echo it."""

    def local_verts(el_root):
        return {
            o.attrib["id"]: [
                (float(v.attrib["x"]), float(v.attrib["y"]), float(v.attrib["z"]))
                for v in o.findall(".//m:vertex", NS)
            ]
            for o in el_root.findall(".//m:object", NS)
        }

    world_local = {}
    for obj in root.findall(".//m:resources/m:object", NS):
        oid = obj.attrib["id"]
        comp = obj.find(".//m:component", NS)
        ctrans = [float(t) for t in comp.attrib.get("transform", IDENTITY).split()]
        target = comp.attrib[f"{{{NS['p']}}}path"].lstrip("/")
        target_root = ET.fromstring(zf.read(target))
        verts = local_verts(target_root)[comp.attrib["objectid"]]
        world_local[oid] = [_apply12(v, ctrans) for v in verts]

    build_xform = {
        item.attrib["objectid"]: [float(x) for x in item.attrib.get("transform", IDENTITY).split()]
        for item in root.findall(".//m:build/m:item", NS)
    }
    world_placed = {
        oid: [_apply12(v, build_xform[oid]) for v in verts]
        for oid, verts in world_local.items()
        if oid in build_xform
    }

    ms_root = ET.fromstring(zf.read("Metadata/model_settings.config"))
    per_plate = {}
    for plate in ms_root.findall(".//plate"):
        pid = plate.find("./metadata[@key='plater_id']").attrib["value"]
        oids = [
            mi.find("./metadata[@key='object_id']").attrib["value"]
            for mi in plate.findall("./model_instance")
        ]
        pts = [pt for oid in oids for pt in world_placed.get(oid, [])]
        xs, ys, zs = [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
        per_plate[pid] = {
            "min_x": min(xs), "max_x": max(xs),
            "min_y": min(ys), "max_y": max(ys),
            "min_z": min(zs), "max_z": max(zs),
        }
    return per_plate


class SelfConsistencyTests(unittest.TestCase):
    """Group 1: generated fixture is internally coherent."""

    def _check_fixture(self, fixture_path, expected_path):
        self.assertTrue(fixture_path.exists(), f"missing fixture: {fixture_path}")
        self.assertTrue(expected_path.exists(), f"missing sidecar: {expected_path}")
        zf = zipfile.ZipFile(fixture_path)
        names = set(zf.namelist())
        for required in (
            "[Content_Types].xml",
            "_rels/.rels",
            "3D/3dmodel.model",
            "3D/_rels/3dmodel.model.rels",
        ):
            self.assertIn(required, names, f"{fixture_path.name} missing required member {required}")

        root = ET.fromstring(zf.read("3D/3dmodel.model"))
        items = root.findall(".//m:build/m:item", NS)
        objects = root.findall(".//m:resources/m:object", NS)
        self.assertEqual(len(items), len(objects), "build item count must equal object count")
        self.assertGreater(len(items), 0, "fixture must contain at least one object")

        for comp in root.findall(".//m:component", NS):
            target = comp.attrib[f"{{{NS['p']}}}path"].lstrip("/")
            self.assertIn(target, names, f"component target {target} not present in ZIP")

        expected = json.loads(expected_path.read_text())
        recomputed = _independent_world_bbox_per_plate(zf, root)
        self.assertEqual(set(recomputed.keys()), set(expected["plates"].keys()))
        for plate_id, plate_expected in expected["plates"].items():
            got = recomputed[plate_id]
            for key, want in plate_expected["bbox_mm"].items():
                self.assertAlmostEqual(
                    got[key], want, delta=0.01,
                    msg=f"{fixture_path.name} plate {plate_id} {key}: got {got[key]} want {want}",
                )

    def test_single_plate_fixture_is_self_consistent(self):
        self._check_fixture(
            FIXTURES_DIR / "single-plate.3mf",
            FIXTURES_DIR / "single-plate.3mf.expected.json",
        )

    def test_two_plate_ams_fixture_is_self_consistent(self):
        self._check_fixture(
            FIXTURES_DIR / "two-plate-ams.3mf",
            FIXTURES_DIR / "two-plate-ams.3mf.expected.json",
        )

    def test_generation_is_deterministic(self):
        self.assertTrue(STL_A.exists(), f"expected repo STL missing: {STL_A}")
        with tempfile.TemporaryDirectory() as tmp:
            out1 = Path(tmp) / "a.3mf"
            out2 = Path(tmp) / "b.3mf"
            r1 = _run_generator(["--out", str(out1), "--stl", str(STL_A)])
            self.assertEqual(r1.returncode, 0, f"stdout={r1.stdout}\nstderr={r1.stderr}")
            r2 = _run_generator(["--out", str(out2), "--stl", str(STL_A)])
            self.assertEqual(r2.returncode, 0, f"stdout={r2.stdout}\nstderr={r2.stderr}")
            self.assertEqual(_sha256_of(out1), _sha256_of(out2), "two runs must yield identical sha256")

    def test_cli_rejects_missing_stl(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "f.3mf"
            result = _run_generator(["--out", str(out), "--stl", str(Path(tmp) / "nope.stl")])
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(out.exists())


class StructuralDiffAgainstRealBambuTests(unittest.TestCase):
    """Group 2: structural diff vs a real Bambu Studio 3MF. SKIPs without
    BAMBU_REAL_3MF. Compares structure only -- see fixtures/README.md
    'Known gaps' for every deliberate, documented omission below."""

    KNOWN_GAP_MEMBER_PATTERNS = {
        "Metadata/cut_information.xml",
        "Metadata/top_N.png",
        "Metadata/pick_N.png",
    }
    KNOWN_GAP_TAGS = {"assemble", "assemble_item"}
    KNOWN_GAP_METADATA_KEYS = {
        "source_file", "source_object_id", "source_volume_id",
        "source_offset_x", "source_offset_y", "source_offset_z",
        "top_file", "pick_file", "plater_name", "locked",
    }

    @unittest.skipUnless(os.environ.get("BAMBU_REAL_3MF"), "BAMBU_REAL_3MF not set; skipping real-file diff")
    def test_structural_diff_against_real(self):
        real_path = os.environ["BAMBU_REAL_3MF"]
        self.assertTrue(Path(real_path).exists(), f"BAMBU_REAL_3MF points to missing file: {real_path}")
        real_facts = _collect_structural_facts(real_path)
        gen_facts = _collect_structural_facts(FIXTURES_DIR / "two-plate-ams.3mf")

        gap_patterns = real_facts["member_patterns"] - gen_facts["member_patterns"]
        self.assertEqual(
            gap_patterns, self.KNOWN_GAP_MEMBER_PATTERNS,
            f"undocumented ZIP member gap: {gap_patterns - self.KNOWN_GAP_MEMBER_PATTERNS}",
        )

        gap_tags = real_facts["tag_names"] - gen_facts["tag_names"]
        self.assertEqual(
            gap_tags, self.KNOWN_GAP_TAGS,
            f"undocumented tag gap: {gap_tags - self.KNOWN_GAP_TAGS}",
        )

        gap_keys = real_facts["metadata_key_names"] - gen_facts["metadata_key_names"]
        self.assertEqual(
            gap_keys, self.KNOWN_GAP_METADATA_KEYS,
            f"undocumented metadata key gap: {gap_keys - self.KNOWN_GAP_METADATA_KEYS}",
        )

        invented_tags = gen_facts["tag_names"] - real_facts["tag_names"]
        self.assertEqual(invented_tags, set(), f"generator invented tags real Bambu Studio never emits: {invented_tags}")

        invented_keys = gen_facts["metadata_key_names"] - real_facts["metadata_key_names"]
        self.assertEqual(invented_keys, set(), f"generator invented metadata keys: {invented_keys}")

        invented_patterns = gen_facts["member_patterns"] - real_facts["member_patterns"]
        self.assertEqual(invented_patterns, set(), f"generator invented ZIP members: {invented_patterns}")

        for tag in gen_facts["tag_names"]:
            invented_attrs = gen_facts["attr_keys_by_tag"].get(tag, set()) - real_facts["attr_keys_by_tag"].get(tag, set())
            self.assertEqual(invented_attrs, set(), f"generator invented attribute keys on <{tag}>: {invented_attrs}")


if __name__ == "__main__":
    unittest.main()
