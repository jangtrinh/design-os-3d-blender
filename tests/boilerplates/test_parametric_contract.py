"""Host-side contracts for bp_parametric_contract; no bpy or CAD kernel required."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "boilerplates" / "bp_parametric_contract.py"
spec = importlib.util.spec_from_file_location("bp_parametric_contract_target", MODULE_PATH)
assert spec is not None and spec.loader is not None
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def valid_contract(unit: str = "mm"):
    factor = 1.0 if unit == "mm" else 0.001
    return {
        "units": unit,
        "parameters": {"height": {"value": 30 * factor, "unit": unit, "min": 10 * factor, "max": 80 * factor}},
        "frames": {
            "base": {"parent": None, "origin": [0, 0, 0], "unit": unit, "axes": {"x": [2, 0, 0], "y": [0, 3, 0], "z": [0, 0, 4]}},
            "top": {"parent": "base", "origin": [0, 0, 30 * factor], "unit": unit, "axes": {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}},
        },
        "datums": {"top_center": {"frame": "base", "position": [0, 0, 30 * factor], "unit": unit}},
        "ports": {"mount": {"frame": "base", "kind": "mount", "roles": ["physical"]}},
        "roles": {"visual": ["body"], "collision": ["body_proxy"], "physical": ["body"]},
    }


class NormalizeContractTests(unittest.TestCase):
    def test_mm_and_m_normalize_to_same_si_values_and_fresh_dicts(self):
        raw = valid_contract("mm")
        before = copy.deepcopy(raw)
        mm = contract.normalize_contract(raw)
        metres = contract.normalize_contract(valid_contract("m"))
        self.assertEqual(raw, before)
        self.assertEqual(mm["parameters"]["height"]["values_si"], metres["parameters"]["height"]["values_si"])
        self.assertEqual(mm["frames"]["top"]["origin_m"], [0.0, 0.0, 0.03])
        self.assertEqual(mm["datums"]["top_center"]["position_m"], [0.0, 0.0, 0.03])
        self.assertEqual(mm["frames"]["base"]["axes"]["x"], [1.0, 0.0, 0.0])
        mm["roles"]["visual"].append("changed")
        self.assertNotIn("changed", contract.normalize_contract(raw)["roles"]["visual"])

    def test_numeric_parameters_reject_nonfinite_type_range_and_unknown_unit(self):
        for field, value, exc in (
            ("value", True, TypeError), ("value", float("nan"), ValueError),
            ("value", 100, ValueError), ("min", 90, ValueError), ("unit", "cm", ValueError),
        ):
            raw = valid_contract()
            raw["parameters"]["height"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(exc):
                contract.normalize_contract(raw)

    def test_frames_reject_unknown_parent_cycles_nonorthogonal_and_left_handed_basis(self):
        cases = []
        raw = valid_contract(); raw["frames"]["top"]["parent"] = "missing"; cases.append(raw)
        raw = valid_contract(); raw["frames"]["base"]["parent"] = "top"; cases.append(raw)
        raw = valid_contract(); raw["frames"]["base"]["axes"]["y"] = [1, 1, 0]; cases.append(raw)
        raw = valid_contract(); raw["frames"]["base"]["axes"]["z"] = [0, 0, -1]; cases.append(raw)
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                contract.normalize_contract(raw)

    def test_datums_ports_and_roles_are_reference_checked(self):
        raw = valid_contract(); raw["datums"]["top_center"]["frame"] = "missing"
        with self.assertRaises(ValueError): contract.normalize_contract(raw)
        raw = valid_contract(); raw["ports"]["mount"]["frame"] = "missing"
        with self.assertRaises(ValueError): contract.normalize_contract(raw)
        raw = valid_contract(); raw["ports"]["mount"]["roles"] = ["collisionless"]
        with self.assertRaises(ValueError): contract.normalize_contract(raw)
        raw = valid_contract(); raw["roles"]["manufacturing"] = ["body"]
        with self.assertRaises(ValueError): contract.normalize_contract(raw)

    def test_canonical_name_collisions_and_invalid_port_role_shapes_fail(self):
        for section, first, second in (
            ("parameters", "height", " height "),
            ("frames", "base", " base "),
            ("datums", "top_center", " top_center "),
            ("ports", "mount", " mount "),
            ("roles", "visual", " visual "),
        ):
            raw = valid_contract()
            raw[section][second] = copy.deepcopy(raw[section][first])
            with self.subTest(section=section), self.assertRaises(ValueError):
                contract.normalize_contract(raw)
        for bad in ("physical", {"physical": True}, ["physical", "physical"], []):
            raw = valid_contract(); raw["ports"]["mount"]["roles"] = bad
            with self.subTest(bad=bad), self.assertRaises((TypeError, ValueError)):
                contract.normalize_contract(raw)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="parametric-contract-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.normalized = contract.normalize_contract(valid_contract())

    def test_source_evidence_is_content_bound_root_bound_and_contract_bound(self):
        source = self.root / "model.py"
        source.write_text("SIZE = 1\n", encoding="utf-8")
        receipt = contract.bind_source_evidence(self.normalized, ["model.py"], self.root)
        self.assertEqual(receipt["files"][0]["path"], "model.py")
        self.assertTrue(contract.source_evidence_current(receipt, self.root, contract=self.normalized))
        source.unlink(); source.write_text("SIZE = 1\n", encoding="utf-8")
        self.assertTrue(contract.source_evidence_current(receipt, self.root))
        source.write_text("SIZE = 2\n", encoding="utf-8")
        self.assertFalse(contract.source_evidence_current(receipt, self.root))
        changed = copy.deepcopy(self.normalized); changed["roles"]["visual"] = ["other"]
        self.assertFalse(contract.source_evidence_current(receipt, self.root, contract=changed))

    def test_source_evidence_rejects_escape_missing_and_duplicates(self):
        source = self.root / "model.py"; source.write_text("pass\n", encoding="utf-8")
        with self.assertRaises(ValueError): contract.bind_source_evidence(self.normalized, ["model.py", "model.py"], self.root)
        with self.assertRaises(FileNotFoundError): contract.bind_source_evidence(self.normalized, ["missing.py"], self.root)
        outside = self.root.parent / (self.root.name + "-outside.py"); outside.write_text("pass\n", encoding="utf-8")
        self.addCleanup(outside.unlink)
        with self.assertRaises(ValueError): contract.bind_source_evidence(self.normalized, [outside], self.root)
        target = self.root / "actual.py"; target.write_text("pass\n", encoding="utf-8")
        alias = self.root / "alias.py"; alias.symlink_to(target)
        with self.assertRaises(ValueError): contract.bind_source_evidence(self.normalized, ["alias.py"], self.root)

    def test_export_evidence_hashes_exact_files_without_making_format_claims(self):
        output = self.root / "part.glb"; output.write_bytes(b"glb-bytes")
        scene_hash, spec_hash = "a" * 64, "B" * 64
        receipt = contract.bind_export_evidence(self.normalized, ["part.glb"], self.root, scene_sha256=scene_hash, spec_sha256=spec_hash)
        self.assertEqual(receipt["files"][0]["format"], "glb")
        self.assertEqual(receipt["scene_sha256"], scene_hash)
        self.assertEqual(receipt["spec_sha256"], spec_hash.lower())
        with self.assertRaises(ValueError):
            contract.bind_export_evidence(self.normalized, ["part.glb"], self.root, scene_sha256="bad")


if __name__ == "__main__":
    unittest.main(verbosity=2)
