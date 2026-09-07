"""One test per validator check (phase-04 requirement list, 10 checks).

Each test asserts on either a committed fixture (known-good ground truth
from tests/fixtures/*.expected.json, phase 03) or a deliberately broken
in-memory copy built by mutating one ZIP member (phase-04 step 1). The
broken copies are synthetic test doubles only -- never written to disk as
fixtures, never claimed to be real Bambu Studio output.

Real-file oracle test (per_plate_bbox_mm numeric agreement) is gated on
BAMBU_REAL_3MF and SKIPs when absent.
"""
import io
import json
import os
import re
import sys
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import bambu_3mf_reader as reader  # noqa: E402
import bambu_checks as checks  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
SINGLE = os.path.join(FIXTURES, "single-plate.3mf")
TWO_PLATE = os.path.join(FIXTURES, "two-plate-ams.3mf")
TWO_PLATE_EXPECTED = os.path.join(FIXTURES, "two-plate-ams.3mf.expected.json")


def _rewrite_zip(src_path, mutator):
    """Read src_path, apply mutator(dict[name->bytes]) in place, return
    bytes of a new in-memory ZIP with the mutated member set."""
    with zipfile.ZipFile(src_path) as zf:
        members = {name: zf.read(name) for name in zf.namelist()}
    mutator(members)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in members.items():
            out.writestr(name, data)
    buf.seek(0)
    return buf


class ContainerZipCheckTests(unittest.TestCase):
    def test_good_fixture_passes(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_container_zip(zf)
        self.assertEqual(result["status"], "PASS")

    def test_path_traversal_entry_fails(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as out:
            out.writestr("../evil.txt", b"x")
        buf.seek(0)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_container_zip(zf)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("evil.txt", result["note"])

    def test_uncompressed_size_cap_exceeded_fails(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
            out.writestr("big.bin", b"0" * 2000)
        buf.seek(0)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_container_zip(zf, max_uncompressed_bytes=1000)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("cap", result["note"].lower())

    def test_unreadable_input_raises_before_check(self):
        with self.assertRaises(reader.UnreadableInputError):
            reader.open_zip_safely(__file__)  # this .py file is not a zip


class BambuProjectLayoutCheckTests(unittest.TestCase):
    def test_good_fixture_passes(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_bambu_project_layout(zf)
        self.assertEqual(result["status"], "PASS")

    def test_missing_model_settings_fails(self):
        def drop_model_settings(members):
            del members["Metadata/model_settings.config"]

        buf = _rewrite_zip(TWO_PLATE, drop_model_settings)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_bambu_project_layout(zf)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("model_settings.config", result["note"])

    def test_missing_opc_rels_fails(self):
        def drop_rels(members):
            del members["_rels/.rels"]

        buf = _rewrite_zip(TWO_PLATE, drop_rels)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_bambu_project_layout(zf)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("_rels/.rels", result["note"])


class GeometryResolvedCheckTests(unittest.TestCase):
    def test_good_fixture_resolves_components_and_has_vertices(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_geometry_resolved(zf)
        self.assertEqual(result["status"], "PASS")
        self.assertGreater(result["measured"]["total_vertices"], 0)

    def test_stripped_objects_dir_fails(self):
        def strip_objects(members):
            for name in list(members):
                if name.startswith("3D/Objects/"):
                    del members[name]

        buf = _rewrite_zip(TWO_PLATE, strip_objects)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_geometry_resolved(zf)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["measured"]["total_vertices"], 0)

    def test_inline_mesh_object_resolves_without_components(self):
        # Root object with a <mesh> directly, no <components> wrapper --
        # the "inline meshes" half of check 3.
        model_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<model unit="millimeter" xmlns="http://schemas.microsoft.com/'
            b'3dmanufacturing/core/2015/02">'
            b"<resources><object id=\"9\" type=\"model\"><mesh>"
            b'<vertices><vertex x="0" y="0" z="0"/><vertex x="1" y="0" z="0"/>'
            b'<vertex x="0" y="1" z="0"/></vertices>'
            b'<triangles><triangle v1="0" v2="1" v3="2"/></triangles>'
            b"</mesh></object></resources>"
            b'<build><item objectid="9" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
            b"</build></model>"
        )

        def replace_root_model(members):
            members["3D/3dmodel.model"] = model_xml
            for name in list(members):
                if name.startswith("3D/Objects/") or name == "3D/_rels/3dmodel.model.rels":
                    del members[name]

        buf = _rewrite_zip(TWO_PLATE, replace_root_model)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_geometry_resolved(zf)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["measured"]["total_vertices"], 3)


class BuildItemsPlacedCheckTests(unittest.TestCase):
    def test_good_fixture_passes(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_build_items_placed(zf)
        self.assertEqual(result["status"], "PASS")

    def test_blanked_build_fails(self):
        def blank_build(members):
            xml = members["3D/3dmodel.model"].decode("utf-8")
            xml = re.sub(r"<build[^>]*>.*</build>", "<build/>", xml, flags=re.S)
            members["3D/3dmodel.model"] = xml.encode("utf-8")

        buf = _rewrite_zip(TWO_PLATE, blank_build)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_build_items_placed(zf)
        self.assertEqual(result["status"], "FAIL")

    def test_item_missing_transform_fails(self):
        def strip_transform(members):
            xml = members["3D/3dmodel.model"].decode("utf-8")
            xml = xml.replace(
                'transform="1 0 0 0 1 0 0 0 1 100 100 -0.499497"', ""
            )
            members["3D/3dmodel.model"] = xml.encode("utf-8")

        buf = _rewrite_zip(TWO_PLATE, strip_transform)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_build_items_placed(zf)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("transform", result["note"])


class PlateMembershipCheckTests(unittest.TestCase):
    def test_good_fixture_passes(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_plate_membership(zf)
        self.assertEqual(result["status"], "PASS")

    def test_orphan_build_item_not_on_any_plate_fails(self):
        def drop_from_plate(members):
            xml = members["Metadata/model_settings.config"].decode("utf-8")
            # Remove the entire <plate> block that references object_id 4.
            xml = re.sub(
                r"<plate>\s*<metadata key=\"plater_id\" value=\"2\"/>.*?</plate>",
                "",
                xml,
                flags=re.S,
            )
            members["Metadata/model_settings.config"] = xml.encode("utf-8")

        buf = _rewrite_zip(TWO_PLATE, drop_from_plate)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_plate_membership(zf)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("4", result["note"])


class PerPlateBboxCheckTests(unittest.TestCase):
    def test_no_expect_reports_info_with_measured_bboxes(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_per_plate_bbox_mm(zf, expect=None)
        self.assertEqual(result["status"], "INFO")
        self.assertIn("1", result["measured"]["plates"])
        self.assertIn("2", result["measured"]["plates"])

    def test_matches_expected_json_passes(self):
        with open(TWO_PLATE_EXPECTED) as fh:
            expect = json.load(fh)
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_per_plate_bbox_mm(zf, expect=expect)
        self.assertEqual(result["status"], "PASS")

    def test_mismatched_expected_json_fails(self):
        with open(TWO_PLATE_EXPECTED) as fh:
            expect = json.load(fh)
        expect["plates"]["1"]["bbox_mm"]["max_x"] += 50.0
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_per_plate_bbox_mm(zf, expect=expect)
        self.assertEqual(result["status"], "FAIL")


class BedFitCheckTests(unittest.TestCase):
    def test_always_info_never_fails(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_bed_fit(zf, bed_mm=(180.0, 180.0, 180.0))
        self.assertEqual(result["status"], "INFO")
        self.assertIn("fits_180", result["measured"]["plates"]["1"])
        self.assertIn("fits_256", result["measured"]["plates"]["1"])


class SettingsTypesCheckTests(unittest.TestCase):
    def test_good_fixture_passes(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_settings_types(zf)
        self.assertEqual(result["status"], "PASS")

    def test_retyped_int_value_fails(self):
        def retype(members):
            settings = json.loads(members["Metadata/project_settings.config"])
            settings["layer_height"] = 0.2  # was the string "0.2"
            members["Metadata/project_settings.config"] = json.dumps(settings).encode("utf-8")

        buf = _rewrite_zip(TWO_PLATE, retype)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_settings_types(zf)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("layer_height", result["note"])


class SliceInfoPresentCheckTests(unittest.TestCase):
    def test_unsliced_fixture_skips(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_slice_info_present(zf)
        self.assertEqual(result["status"], "SKIP")

    def test_missing_member_skips(self):
        def drop_slice_info(members):
            del members["Metadata/slice_info.config"]

        buf = _rewrite_zip(TWO_PLATE, drop_slice_info)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_slice_info_present(zf)
        self.assertEqual(result["status"], "SKIP")

    def test_synthetic_sliced_config_passes(self):
        # Synthetic test double only (never shipped as a fixture): adds the
        # bbs_3mf.cpp-documented per-object prediction/weight attributes
        # that mark a plate as actually sliced.
        def add_slice_result(members):
            members["Metadata/slice_info.config"] = (
                b'<?xml version="1.0" encoding="UTF-8"?><config>'
                b'<header><header_item key="X-BBL-Client-Type" value="slicer"/>'
                b'</header><plate><metadata key="index" value="1"/>'
                b'<object identify_id="1" prediction="120" weight="3.5"/>'
                b"</plate></config>"
            )

        buf = _rewrite_zip(TWO_PLATE, add_slice_result)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_slice_info_present(zf)
        self.assertEqual(result["status"], "PASS")

    def test_malformed_slice_info_fails(self):
        def corrupt(members):
            members["Metadata/slice_info.config"] = b"<not-xml"

        buf = _rewrite_zip(TWO_PLATE, corrupt)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_slice_info_present(zf)
        self.assertEqual(result["status"], "FAIL")


class ThumbnailPresentCheckTests(unittest.TestCase):
    def test_good_fixture_passes(self):
        with reader.open_zip_safely(TWO_PLATE) as zf:
            result = checks.check_thumbnail_present(zf)
        self.assertEqual(result["status"], "PASS")

    def test_deleted_thumbnail_file_fails(self):
        def drop_png(members):
            del members["Metadata/plate_1.png"]

        buf = _rewrite_zip(TWO_PLATE, drop_png)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_thumbnail_present(zf)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("plate_1.png", result["note"])


@unittest.skipUnless(os.environ.get("BAMBU_REAL_3MF"), "BAMBU_REAL_3MF not set")
class RealFileBboxOracleTests(unittest.TestCase):
    """Numeric agreement with the independent reference script, gated on
    the local-only real Bambu Studio 3MF (never committed to the repo)."""

    def test_plate_1_bbox_matches_reference_within_0_01mm(self):
        path = os.environ["BAMBU_REAL_3MF"]
        with reader.open_zip_safely(path) as zf:
            result = checks.check_per_plate_bbox_mm(zf, expect=None)
        plate1 = result["measured"]["plates"]["1"]
        dx = plate1["max_x"] - plate1["min_x"]
        dy = plate1["max_y"] - plate1["min_y"]
        dz = plate1["max_z"] - plate1["min_z"]
        # Reference: dX=106.296, dY=28.233, dZ=25.600 (reference-per-plate-bbox.py)
        self.assertAlmostEqual(dx, 106.296, delta=0.01)
        self.assertAlmostEqual(dy, 28.233, delta=0.01)
        self.assertAlmostEqual(dz, 25.600, delta=0.01)


if __name__ == "__main__":
    unittest.main()
