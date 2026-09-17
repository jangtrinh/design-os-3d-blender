"""Contract tests for bounded native pipeline manifests."""

import json
from pathlib import Path
import tempfile
import unittest

import sys

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from native_pipeline.manifest import ManifestError, load_manifest, validate_manifest  # noqa: E402


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="native-manifest-")
        self.root = Path(self.temp.name)
        (self.root / "steps").mkdir()
        (self.root / "steps/a.py").write_text("# a\n", encoding="utf-8")
        (self.root / "steps/b.py").write_text("# b\n", encoding="utf-8")
        (self.root / "input.json").write_text("{}\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self):
        return {
            "version": 1,
            "pipeline_id": "fixture",
            "steps": [
                {
                    "id": "a",
                    "script": "steps/a.py",
                    "depends_on": [],
                    "inputs": ["input.json"],
                    "artifact_inputs": [],
                    "outputs": ["model.blend"],
                    "required_postconditions": ["part_count"],
                    "timeout_seconds": 30,
                },
                {
                    "id": "b",
                    "script": "steps/b.py",
                    "depends_on": ["a"],
                    "inputs": [],
                    "artifact_inputs": ["a:model.blend"],
                    "outputs": ["model.blend"],
                    "required_postconditions": ["part_count"],
                    "timeout_seconds": 30,
                },
            ],
        }

    def test_same_output_basename_is_valid_across_step_owned_directories(self):
        manifest = validate_manifest(self.manifest(), self.root)
        self.assertEqual(manifest["steps"][0]["outputs"], ["model.blend"])
        self.assertEqual(manifest["steps"][1]["outputs"], ["model.blend"])
        self.assertEqual(manifest["steps"][1]["artifact_inputs"], ["a:model.blend"])

    def test_output_alias_duplicate_is_rejected_within_one_step(self):
        data = self.manifest()
        data["steps"][0]["outputs"] = ["proof/data.json", "proof//data.json"]
        with self.assertRaisesRegex(ManifestError, "duplicates"):
            validate_manifest(data, self.root)

    def test_artifact_must_be_declared_by_a_dependency(self):
        data = self.manifest()
        data["steps"][1]["artifact_inputs"] = ["a:missing.blend"]
        with self.assertRaisesRegex(ManifestError, "undeclared output"):
            validate_manifest(data, self.root)

    def test_dependency_must_appear_earlier(self):
        data = self.manifest()
        data["steps"][0]["depends_on"] = ["b"]
        with self.assertRaisesRegex(ManifestError, "topological"):
            validate_manifest(data, self.root)

    def test_project_input_path_escape_is_rejected(self):
        data = self.manifest()
        data["steps"][0]["inputs"] = ["../outside.json"]
        with self.assertRaisesRegex(ManifestError, "escapes"):
            validate_manifest(data, self.root)

    def test_required_postconditions_cannot_be_empty(self):
        data = self.manifest()
        data["steps"][0]["required_postconditions"] = []
        with self.assertRaisesRegex(ManifestError, "at least one"):
            validate_manifest(data, self.root)

    def test_declared_outputs_cannot_be_empty(self):
        data = self.manifest()
        data["steps"][0]["outputs"] = []
        with self.assertRaisesRegex(ManifestError, "at least one"):
            validate_manifest(data, self.root)

    def test_pipeline_log_filenames_are_reserved_outputs(self):
        for name in ("stdout.log", "stderr.log", "./stdout.log"):
            data = self.manifest()
            data["steps"][0]["outputs"] = [name]
            with self.subTest(name=name), self.assertRaisesRegex(ManifestError, "reserved"):
                validate_manifest(data, self.root)

    def test_manifest_hash_binds_exact_source_bytes(self):
        path = self.root / "pipeline.json"
        path.write_text(json.dumps(self.manifest()), encoding="utf-8")
        first = load_manifest(path, self.root)
        path.write_text(json.dumps(self.manifest(), indent=2), encoding="utf-8")
        second = load_manifest(path, self.root)
        self.assertNotEqual(first["_sha256"], second["_sha256"])


if __name__ == "__main__":
    unittest.main()
