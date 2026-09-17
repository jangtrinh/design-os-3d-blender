"""Durability and single-writer tests for native pipeline journals."""

from pathlib import Path
import tempfile
import unittest
import sys

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from native_pipeline.journal import (  # noqa: E402
    JournalError,
    begin_attempt,
    finish_attempt,
    latest_attempt_by_step,
    pipeline_lock,
    read_journal,
)


class JournalTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="native-journal-")
        self.run_dir = Path(self.temp.name)
        self.journal = self.run_dir / "journal.jsonl"

    def tearDown(self):
        self.temp.cleanup()

    def begin(self):
        return begin_attempt(
            self.journal,
            pipeline_id="fixture",
            step_id="build",
            manifest_sha256="m" * 64,
            script={"path": "step.py", "sha256": "s" * 64},
            runtime_identity={"blender": {"path": "/bin/blender", "sha256": "b" * 64}},
            input_sha256={},
            output_base="steps/build",
            declared_outputs=["artifact.json"],
            required_postconditions=["artifact_bytes"],
        )

    def test_start_is_durable_before_any_terminal_record(self):
        attempt = self.begin()
        records = read_journal(self.journal)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["state"], "running")
        self.assertEqual(records[0]["attempt_id"], attempt["attempt_id"])

        finish_attempt(
            self.journal,
            attempt["attempt_id"],
            state="executed",
            result={"scope": "execution postconditions and declared artifact hashes"},
        )
        records = read_journal(self.journal)
        self.assertEqual(len(records), 2)
        self.assertEqual(latest_attempt_by_step(records)["build"]["state"], "executed")

    def test_attempt_output_directories_are_immutable_by_number(self):
        first = self.begin()
        finish_attempt(self.journal, first["attempt_id"], state="failed")
        second = self.begin()
        self.assertNotEqual(first["attempt_id"], second["attempt_id"])
        self.assertNotEqual(first["output_dir"], second["output_dir"])

    def test_pipeline_lock_rejects_a_second_writer(self):
        with pipeline_lock(self.run_dir):
            with self.assertRaisesRegex(JournalError, "active writer"):
                with pipeline_lock(self.run_dir):
                    pass


if __name__ == "__main__":
    unittest.main()

