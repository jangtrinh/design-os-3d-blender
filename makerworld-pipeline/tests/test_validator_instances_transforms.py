"""Two check-level probes not covered by test_validator_checks.py:

1. Multi-instance build items (phase-06 review B1): duplicated <item
   objectid="X"> entries must each contribute a separate placement, not
   collapse to one. Probe copies tests/fixtures/two-plate-ams.3mf and
   replaces 3D/3dmodel.model + Metadata/model_settings.config (same
   copy-then-mutate pattern as test_validator_checks.py::_rewrite_zip) --
   never written to disk as a fixture.
2. Transform math discrimination (phase-06 review M2): a 90deg-about-Z
   rotation build item whose world bbox is hand-derived here (independent
   of bambu_3mf_geometry.apply_transform_12), checked on exact min/max --
   widths alone are invariant under a row/column transpose of a pure
   rotation matrix, so only absolute position discriminates the mutant
   (see report for the mutation run).
"""
import io
import os
import sys
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import bambu_checks as checks  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
TWO_PLATE = os.path.join(FIXTURES, "two-plate-ams.3mf")


def _box_mesh_xml(object_id, dims):
    """Inline <object> with an axis-aligned box from (0,0,0) to dims,
    8 vertices, minimal triangles (topology is irrelevant to the checks
    under test -- only vertex positions are read)."""
    lx, ly, lz = dims
    corners = [
        (x, y, z)
        for x in (0, lx) for y in (0, ly) for z in (0, lz)
    ]
    verts = "".join(f'<vertex x="{x}" y="{y}" z="{z}"/>' for x, y, z in corners)
    tris = "".join(
        f'<triangle v1="{a}" v2="{b}" v3="{c}"/>'
        for a, b, c in ((0, 1, 2), (3, 4, 5), (6, 7, 0))
    )
    return (
        f'<object id="{object_id}" type="model"><mesh>'
        f"<vertices>{verts}</vertices><triangles>{tris}</triangles>"
        f"</mesh></object>"
    )


def _model_xml(objects_xml, items_xml):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xmlns="http://schemas.microsoft.com/'
        '3dmanufacturing/core/2015/02">'
        f"<resources>{objects_xml}</resources>"
        f"<build>{items_xml}</build></model>"
    ).encode("utf-8")


def _model_settings_xml(object_names, instances_by_plate):
    """object_names: {id: name}. instances_by_plate: {plater_id: [(oid, instance_id)]}."""
    object_blocks = "".join(
        f'<object id="{oid}"><metadata key="name" value="{name}"/></object>'
        for oid, name in object_names.items()
    )
    plate_blocks = []
    for plater_id, pairs in instances_by_plate.items():
        instances = "".join(
            "<model_instance>"
            f'<metadata key="object_id" value="{oid}"/>'
            f'<metadata key="instance_id" value="{inst}"/>'
            "</model_instance>"
            for oid, inst in pairs
        )
        plate_blocks.append(
            f'<plate><metadata key="plater_id" value="{plater_id}"/>'
            f'<metadata key="thumbnail_file" value="Metadata/plate_{plater_id}.png"/>'
            f"{instances}</plate>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?><config>'
        + object_blocks + "".join(plate_blocks) + "</config>"
    ).encode("utf-8")


def _probe_zip(model_xml_bytes, model_settings_xml_bytes):
    """Copy TWO_PLATE, replacing its geometry-bearing members with the
    bytes given (kept local, not imported, to avoid coupling to a
    sibling test module's private helper)."""
    with zipfile.ZipFile(TWO_PLATE) as zf:
        members = {name: zf.read(name) for name in zf.namelist()}
    for name in list(members):
        if name.startswith("3D/Objects/") or name == "3D/_rels/3dmodel.model.rels":
            del members[name]
    members["3D/3dmodel.model"] = model_xml_bytes
    members["Metadata/model_settings.config"] = model_settings_xml_bytes
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in members.items():
            out.writestr(name, data)
    buf.seek(0)
    return buf


class MultiInstanceBuildItemsTests(unittest.TestCase):
    """Object 4 is placed twice (instance 0 and a +250mm-in-X duplicate,
    instance 1) alongside single-instance objects 2 and 6, all on plate 1.
    4 build items total, 3 distinct objectids."""

    @classmethod
    def setUpClass(cls):
        objects_xml = (
            _box_mesh_xml("2", (5, 5, 5))
            + _box_mesh_xml("4", (10, 10, 10))
            + _box_mesh_xml("6", (3, 3, 3))
        )
        # instance 0 of object 4 sits at x=-100; the duplicate (instance 1)
        # is the same object shifted +250mm in X, per the review's repro.
        items_xml = (
            '<item objectid="2" transform="1 0 0 0 1 0 0 0 1 0 0 0" printable="1"/>'
            '<item objectid="4" transform="1 0 0 0 1 0 0 0 1 -100 20 0" printable="1"/>'
            '<item objectid="4" transform="1 0 0 0 1 0 0 0 1 150 20 0" printable="1"/>'
            '<item objectid="6" transform="1 0 0 0 1 0 0 0 1 300 300 0" printable="1"/>'
        )
        settings_xml = _model_settings_xml(
            {"2": "A", "4": "B", "6": "C"},
            {"1": [("2", 0), ("4", 0), ("4", 1), ("6", 0)]},
        )
        cls.buf = _probe_zip(_model_xml(objects_xml, items_xml), settings_xml)

    def _zf(self):
        self.buf.seek(0)
        return zipfile.ZipFile(self.buf)

    def test_n_items_counts_every_build_item_not_every_objectid(self):
        with self._zf() as zf:
            result = checks.check_build_items_placed(zf)
        self.assertEqual(result["status"], "PASS")
        # HAND-DERIVED: 4 <item> elements (2, 4x2, 6), 3 distinct objectids.
        # Pre-fix (dict keyed by objectid) this measures 3.
        self.assertEqual(result["measured"]["n_items"], 4)

    def test_per_plate_bbox_includes_both_instances_of_the_duplicated_object(self):
        with self._zf() as zf:
            result = checks.check_per_plate_bbox_mm(zf, expect=None)
        b = result["measured"]["plates"]["1"]
        # HAND-DERIVED (independent of code under test): obj2 x[0,5] y[0,5]
        # z[0,5]; obj4 inst0 x[-100,-90] y[20,30] z[0,10]; obj4 inst1
        # x[150,160] y[20,30] z[0,10]; obj6 x[300,303] y[300,303] z[0,3].
        # combined: x[-100,303]=403  y[0,303]=303  z[0,10]=10
        self.assertAlmostEqual(b["max_x"] - b["min_x"], 403.0, places=3)
        self.assertAlmostEqual(b["max_y"] - b["min_y"], 303.0, places=3)
        self.assertAlmostEqual(b["max_z"] - b["min_z"], 10.0, places=3)

    def test_duplicate_instances_on_one_plate_is_not_flagged_multi_plate(self):
        with self._zf() as zf:
            result = checks.check_plate_membership(zf)
        # Pre-fix: two <model_instance> for object_id=4 on the SAME plate
        # were mistaken for the same object appearing on two DIFFERENT
        # plates ("object(s) on more than one plate: ['4']").
        self.assertEqual(result["status"], "PASS", result["note"])

    def test_bed_fit_180_is_false_for_the_true_403mm_footprint(self):
        with self._zf() as zf:
            result = checks.check_bed_fit(zf)
        self.assertFalse(result["measured"]["plates"]["1"]["fits_180"])


class RotationTransformTests(unittest.TestCase):
    """One object rotated 90deg about Z (row-vector 12-float transform)
    plus a translation. Local box x[0,20] y[0,10] z[0,5] is non-square in
    X/Y so a row/column transpose of the rotation block changes the
    ABSOLUTE min/max on X and Y -- widths alone stay 10/20 either way,
    since transpose of a pure rotation is itself a rotation and preserves
    per-axis extents (verified min/max required, not just width)."""

    def test_world_bbox_matches_hand_derived_90deg_rotation(self):
        # Row-vector transform row0=(0,1,0)=image of +X, row1=(-1,0,0)=
        # image of +Y, row2=(0,0,1)=image of Z, translation (100,50,0):
        # world_x=-y+100, world_y=x+50, world_z=z. Local corners x in
        # {0,20}, y in {0,10}, z in {0,5} give world_x in [90,100],
        # world_y in [50,70], world_z in [0,5].
        objects_xml = _box_mesh_xml("2", (20, 10, 5))
        items_xml = '<item objectid="2" transform="0 1 0 -1 0 0 0 0 1 100 50 0" printable="1"/>'
        settings_xml = _model_settings_xml({"2": "A"}, {"1": [("2", 0)]})
        buf = _probe_zip(_model_xml(objects_xml, items_xml), settings_xml)
        with zipfile.ZipFile(buf) as zf:
            result = checks.check_per_plate_bbox_mm(zf, expect=None)
        b = result["measured"]["plates"]["1"]
        self.assertAlmostEqual(b["min_x"], 90.0, places=6)
        self.assertAlmostEqual(b["max_x"], 100.0, places=6)
        self.assertAlmostEqual(b["min_y"], 50.0, places=6)
        self.assertAlmostEqual(b["max_y"], 70.0, places=6)
        self.assertAlmostEqual(b["min_z"], 0.0, places=6)
        self.assertAlmostEqual(b["max_z"], 5.0, places=6)


if __name__ == "__main__":
    unittest.main()
