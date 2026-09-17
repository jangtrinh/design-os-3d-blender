"""Execution-state controls for the bounded native pipeline runner."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import sys

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from native_pipeline import runner  # noqa: E402
from native_pipeline.journal import begin_attempt, finish_attempt  # noqa: E402
from native_pipeline.manifest import load_manifest  # noqa: E402
from native_pipeline.runner import PipelineError  # noqa: E402


class TempRepo:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="native-runner-repo-")
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir()
        for relative in runner.RUNTIME_FILES:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {relative}\n", encoding="utf-8")
        self.blender = self.root / "fake-blender"
        self.blender.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        self.blender.chmod(0o755)
        (self.root / "step.py").write_text("# fixture step\n", encoding="utf-8")
        (self.root / "input.txt").write_text("v1\n", encoding="utf-8")

    def close(self):
        self.temp.cleanup()

    def manifest(self, *, with_input=False):
        data = {
            "version": 1,
            "pipeline_id": "runner-fixture",
            "steps": [
                {
                    "id": "build",
                    "script": "step.py",
                    "depends_on": [],
                    "inputs": ["input.txt"] if with_input else [],
                    "artifact_inputs": [],
                    "outputs": ["artifact.json"],
                    "required_postconditions": ["artifact_bytes"],
                    "timeout_seconds": 30,
                }
            ],
        }
        path = self.root / "pipeline.json"
        path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        return path

    def two_step_manifest(self):
        (self.root / "inspect.py").write_text("# inspect fixture\n", encoding="utf-8")
        data = {
            "version": 1,
            "pipeline_id": "runner-chain",
            "steps": [
                {
                    "id": "build",
                    "script": "step.py",
                    "depends_on": [],
                    "inputs": [],
                    "artifact_inputs": [],
                    "outputs": ["artifact.json"],
                    "required_postconditions": ["artifact_bytes"],
                    "timeout_seconds": 30,
                },
                {
                    "id": "inspect",
                    "script": "inspect.py",
                    "depends_on": ["build"],
                    "inputs": [],
                    "artifact_inputs": ["build:artifact.json"],
                    "outputs": ["artifact.json"],
                    "required_postconditions": ["artifact_bytes"],
                    "timeout_seconds": 30,
                },
            ],
        }
        path = self.root / "pipeline-chain.json"
        path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        return path


def executed_launch(*, step, attempt, repo_root, run_dir, inputs):
    attempt_dir = run_dir / attempt["output_dir"]
    attempt_dir.mkdir(parents=True, exist_ok=False)
    artifact = attempt_dir / "artifact.json"
    artifact.write_text(json.dumps(inputs, sort_keys=True), encoding="utf-8")
    return "executed", {
        "returncode": 0,
        "scope": runner.EVIDENCE_SCOPE,
        "postconditions": {"artifact_bytes": artifact.stat().st_size},
        "required_postconditions": {"artifact_bytes": artifact.stat().st_size},
        "outputs": {
            "artifact.json": {
                "path": artifact.relative_to(run_dir).as_posix(),
                "sha256": runner.sha256_file(artifact),
                "bytes": artifact.stat().st_size,
            }
        },
    }


class RunnerStateTest(unittest.TestCase):
    def setUp(self):
        self.repo = TempRepo()
        self.run_temp = tempfile.TemporaryDirectory(prefix="native-runner-run-")
        self.run_dir = Path(self.run_temp.name) / "run"
        self.env = mock.patch.dict(os.environ, {"BLENDER_BIN": str(self.repo.blender)})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.run_temp.cleanup()
        self.repo.close()

    def test_unknown_attempt_is_never_retried_by_resume(self):
        manifest = self.repo.manifest()
        with mock.patch.object(
            runner,
            "_launch_step",
            return_value=("unknown", {"error": {"type": "TimeoutUnknown"}, "scope": runner.EVIDENCE_SCOPE}),
        ) as first_launch:
            first = runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root)
        self.assertFalse(first["ok"])
        self.assertEqual(first["state"], "unknown")
        self.assertEqual(first_launch.call_count, 1)

        with mock.patch.object(runner, "_launch_step", side_effect=AssertionError("must not launch")) as retry:
            with self.assertRaisesRegex(PipelineError, "will not retry"):
                runner.run_pipeline(
                    manifest,
                    run_dir=self.run_dir,
                    repo_root=self.repo.root,
                    resume=True,
                )
        self.assertEqual(retry.call_count, 0)

    def test_failed_attempt_is_never_retried_by_resume(self):
        manifest = self.repo.manifest()
        with mock.patch.object(
            runner,
            "_launch_step",
            return_value=("failed", {"error": {"type": "AssertionError"}, "scope": runner.EVIDENCE_SCOPE}),
        ):
            first = runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root)
        self.assertEqual(first["state"], "failed")
        with mock.patch.object(runner, "_launch_step") as retry:
            with self.assertRaisesRegex(PipelineError, "will not retry"):
                runner.run_pipeline(
                    manifest,
                    run_dir=self.run_dir,
                    repo_root=self.repo.root,
                    resume=True,
                )
        self.assertEqual(retry.call_count, 0)

    def test_running_crash_state_is_never_retried_by_resume(self):
        manifest_path = self.repo.manifest()
        manifest = load_manifest(manifest_path, self.repo.root)
        step = manifest["steps"][0]
        runtime_identity = runner.runtime_identity(self.repo.root)
        begin_attempt(
            self.run_dir / "journal.jsonl",
            pipeline_id=manifest["pipeline_id"],
            step_id=step["id"],
            manifest_sha256=manifest["_sha256"],
            script=runner._script_identity(step, self.repo.root),
            runtime_identity=runtime_identity,
            input_sha256={},
            output_base="steps/build",
            declared_outputs=step["outputs"],
            required_postconditions=step["required_postconditions"],
        )
        with mock.patch.object(runner, "_launch_step") as retry:
            with self.assertRaisesRegex(PipelineError, "will not retry"):
                runner.run_pipeline(
                    manifest_path,
                    run_dir=self.run_dir,
                    repo_root=self.repo.root,
                    resume=True,
                )
        self.assertEqual(retry.call_count, 0)

    def test_executed_attempt_is_reused_only_when_hashes_still_match(self):
        manifest = self.repo.manifest(with_input=True)
        with mock.patch.object(runner, "_launch_step", side_effect=executed_launch) as launch:
            first = runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root)
        self.assertTrue(first["ok"])
        self.assertEqual(launch.call_count, 1)

        with mock.patch.object(runner, "_launch_step") as resume_launch:
            resumed = runner.run_pipeline(
                manifest,
                run_dir=self.run_dir,
                repo_root=self.repo.root,
                resume=True,
            )
        self.assertTrue(resumed["ok"])
        self.assertTrue(resumed["steps"][0]["reused"])
        self.assertEqual(resume_launch.call_count, 0)

        (self.repo.root / "input.txt").write_text("v2\n", encoding="utf-8")
        with mock.patch.object(runner, "_launch_step") as drift_launch:
            with self.assertRaisesRegex(PipelineError, "inputs identity changed"):
                runner.run_pipeline(
                    manifest,
                    run_dir=self.run_dir,
                    repo_root=self.repo.root,
                    resume=True,
                )
        self.assertEqual(drift_launch.call_count, 0)

    def test_output_drift_blocks_resume(self):
        manifest = self.repo.manifest()
        with mock.patch.object(runner, "_launch_step", side_effect=executed_launch):
            runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root)
        artifact = next(self.run_dir.glob("steps/build/attempt-*/artifact.json"))
        artifact.write_text("tampered\n", encoding="utf-8")
        with mock.patch.object(runner, "_launch_step") as launch:
            with self.assertRaisesRegex(PipelineError, "output bytes changed"):
                runner.run_pipeline(
                    manifest,
                    run_dir=self.run_dir,
                    repo_root=self.repo.root,
                    resume=True,
                )
        self.assertEqual(launch.call_count, 0)

    def test_resume_reuses_executed_dependency_and_launches_only_untouched_pending_step(self):
        manifest_path = self.repo.two_step_manifest()
        manifest = load_manifest(manifest_path, self.repo.root)
        build = manifest["steps"][0]
        runtime_identity = runner.runtime_identity(self.repo.root)
        input_context, input_hashes = runner._input_context(
            build, self.repo.root, self.run_dir, {}
        )
        start = begin_attempt(
            self.run_dir / "journal.jsonl",
            pipeline_id=manifest["pipeline_id"],
            step_id="build",
            manifest_sha256=manifest["_sha256"],
            script=runner._script_identity(build, self.repo.root),
            runtime_identity=runtime_identity,
            input_sha256=input_hashes,
            output_base="steps/build",
            declared_outputs=build["outputs"],
            required_postconditions=build["required_postconditions"],
        )
        state, result = executed_launch(
            step=build,
            attempt=start,
            repo_root=self.repo.root,
            run_dir=self.run_dir,
            inputs=input_context,
        )
        self.assertEqual(state, "executed")
        finish_attempt(
            self.run_dir / "journal.jsonl",
            start["attempt_id"],
            state="executed",
            result=result,
        )

        seen_inputs = []

        def launch_pending(**kwargs):
            seen_inputs.append(kwargs["inputs"])
            return executed_launch(**kwargs)

        with mock.patch.object(runner, "_launch_step", side_effect=launch_pending) as launch:
            resumed = runner.run_pipeline(
                manifest_path,
                run_dir=self.run_dir,
                repo_root=self.repo.root,
                resume=True,
            )
        self.assertTrue(resumed["ok"])
        self.assertEqual(launch.call_count, 1)
        self.assertTrue(resumed["steps"][0]["reused"])
        self.assertFalse(resumed["steps"][1]["reused"])
        self.assertEqual(set(seen_inputs[0]["artifacts"]), {"build:artifact.json"})
        artifact_path = Path(seen_inputs[0]["artifacts"]["build:artifact.json"])
        self.assertTrue(artifact_path.is_file())

    def test_script_and_runtime_drift_each_block_resume(self):
        manifest = self.repo.manifest()
        with mock.patch.object(runner, "_launch_step", side_effect=executed_launch):
            runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root)

        (self.repo.root / "step.py").write_text("# changed\n", encoding="utf-8")
        with self.assertRaisesRegex(PipelineError, "script identity changed"):
            runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root, resume=True)

        # Restore script to the original bytes so the runtime identity is the only change.
        (self.repo.root / "step.py").write_text("# fixture step\n", encoding="utf-8")
        (self.repo.root / "scripts/agent_runtime.py").write_text("# changed runtime\n", encoding="utf-8")
        with self.assertRaisesRegex(PipelineError, "runtime identity changed"):
            runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root, resume=True)

        (self.repo.root / "scripts/agent_runtime.py").write_text(
            "# scripts/agent_runtime.py\n", encoding="utf-8"
        )
        pipeline_runner = self.repo.root / "scripts/native_pipeline/runner.py"
        pipeline_runner.write_text("# changed pipeline evaluator\n", encoding="utf-8")
        with self.assertRaisesRegex(PipelineError, "runtime identity changed"):
            runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root, resume=True)

    def test_manifest_byte_drift_blocks_resume(self):
        manifest = self.repo.manifest()
        with mock.patch.object(runner, "_launch_step", side_effect=executed_launch):
            runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["steps"][0]["timeout_seconds"] = 31
        manifest.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")
        with mock.patch.object(runner, "_launch_step") as launch:
            with self.assertRaisesRegex(PipelineError, "different manifest bytes"):
                runner.run_pipeline(
                    manifest,
                    run_dir=self.run_dir,
                    repo_root=self.repo.root,
                    resume=True,
                )
        self.assertEqual(launch.call_count, 0)

    def test_changed_manifest_with_entirely_new_step_ids_still_launches_zero_children(self):
        manifest = self.repo.manifest()
        with mock.patch.object(
            runner,
            "_launch_step",
            return_value=("unknown", {"error": {"type": "TimeoutUnknown"}, "scope": runner.EVIDENCE_SCOPE}),
        ):
            runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root)

        (self.repo.root / "new.py").write_text("# new step\n", encoding="utf-8")
        changed = {
            "version": 1,
            "pipeline_id": "runner-fixture",
            "steps": [
                {
                    "id": "entirely-new",
                    "script": "new.py",
                    "depends_on": [],
                    "inputs": [],
                    "artifact_inputs": [],
                    "outputs": ["new.json"],
                    "required_postconditions": ["count"],
                    "timeout_seconds": 30,
                }
            ],
        }
        manifest.write_text(json.dumps(changed, sort_keys=True), encoding="utf-8")
        with mock.patch.object(runner, "_launch_step") as launch:
            with self.assertRaisesRegex(PipelineError, "different manifest bytes"):
                runner.run_pipeline(
                    manifest,
                    run_dir=self.run_dir,
                    repo_root=self.repo.root,
                    resume=True,
                )
        self.assertEqual(launch.call_count, 0)

    def test_midrun_script_and_declared_input_drift_prevents_executed_receipt(self):
        manifest = self.repo.manifest(with_input=True)

        def drifting_launch(**kwargs):
            state, result = executed_launch(**kwargs)
            (self.repo.root / "step.py").write_text("# mid-run script drift\n", encoding="utf-8")
            (self.repo.root / "input.txt").write_text("mid-run input drift\n", encoding="utf-8")
            return state, result

        with mock.patch.object(runner, "_launch_step", side_effect=drifting_launch):
            result = runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "unknown")
        self.assertEqual(result["error"]["type"], "IdentityDriftUnknown")

        with mock.patch.object(runner, "_launch_step") as launch:
            with self.assertRaisesRegex(PipelineError, "will not retry"):
                runner.run_pipeline(
                    manifest,
                    run_dir=self.run_dir,
                    repo_root=self.repo.root,
                    resume=True,
                )
        self.assertEqual(launch.call_count, 0)

    def test_required_postconditions_are_numeric_finite_and_not_bool(self):
        good = {"postconditions": {"count": 2, "ratio": 0.5}}
        self.assertEqual(runner._check_postconditions(good, ["count"]), {"count": 2})
        for bad in (True, "2", float("inf"), float("nan")):
            with self.assertRaises(PipelineError):
                runner._check_postconditions({"postconditions": {"count": bad}}, ["count"])
        with self.assertRaisesRegex(PipelineError, "missing"):
            runner._check_postconditions({"postconditions": {"other": 1}}, ["count"])
        with self.assertRaisesRegex(PipelineError, "no measured"):
            runner._check_postconditions({"postconditions": {}}, ["count"])

    def test_timeout_kills_only_spawned_disposable_process_group_and_records_unknown(self):
        launcher = self.repo.root / "scripts/headless-run.sh"
        launcher.write_text(
            "#!/bin/bash\n"
            "sleep 30 &\n"
            "child=$!\n"
            "printf '%s\\n' \"$child\" > \"$DESIGN_OS_OUTPUT_DIR/child.pid\"\n"
            "wait \"$child\"\n",
            encoding="utf-8",
        )
        data = json.loads(self.repo.manifest().read_text(encoding="utf-8"))
        data["steps"][0]["timeout_seconds"] = 1
        manifest = self.repo.root / "timeout-pipeline.json"
        manifest.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")

        result = runner.run_pipeline(manifest, run_dir=self.run_dir, repo_root=self.repo.root)
        self.assertFalse(result["ok"])
        self.assertEqual(result["state"], "unknown")
        pid_path = next(self.run_dir.glob("steps/build/attempt-*/child.pid"))
        child_pid = int(pid_path.read_text(encoding="utf-8").strip())
        with self.assertRaises(ProcessLookupError):
            os.kill(child_pid, 0)

    def test_missing_declared_output_fails_execution_contract(self):
        attempt_dir = self.run_dir / "steps/build/attempt-0001"
        attempt_dir.mkdir(parents=True)
        step = {"outputs": ["artifact.json"]}
        with self.assertRaisesRegex(PipelineError, "not produced"):
            runner._collect_outputs(step, attempt_dir, self.run_dir)


@unittest.skipUnless(Path(runner.DEFAULT_BLENDER).exists(), "Blender 5.2 executable not installed")
class RealBlenderPipelineTest(unittest.TestCase):
    def manifest(self, fixture: str, directory: Path):
        data = {
            "version": 1,
            "pipeline_id": "real-blender-fixture",
            "steps": [
                {
                    "id": "build",
                    "script": f"tests/native-pipeline/fixtures/{fixture}",
                    "depends_on": [],
                    "inputs": [],
                    "artifact_inputs": [],
                    "outputs": ["artifact.json"],
                    "required_postconditions": ["artifact_bytes"],
                    "timeout_seconds": 60,
                }
            ],
        }
        path = directory / f"{fixture}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_real_blender_executes_artifact_and_forged_print_fails_control(self):
        with tempfile.TemporaryDirectory(prefix="native-real-blender-") as raw:
            root = Path(raw)
            with mock.patch.dict(
                os.environ,
                {"HEADLESS_RAW": "1", "HEADLESS_KEEP_ADDONS": "1"},
            ):
                valid = runner.run_pipeline(
                    self.manifest("valid_artifact.py", root),
                    run_dir=root / "valid-run",
                    repo_root=REPO,
                )
            self.assertTrue(valid["ok"], valid)
            self.assertEqual(valid["state"], "executed")
            artifact = root / "valid-run/steps/build/attempt-0001/artifact.json"
            self.assertTrue(artifact.is_file())
            payload = json.loads(artifact.read_text(encoding="utf-8"))
            self.assertEqual(payload["headless_raw"], "0")
            self.assertEqual(payload["headless_keep_addons"], "0")

            forged = runner.run_pipeline(
                self.manifest("forged_artifact.py", root),
                run_dir=root / "forged-run",
                repo_root=REPO,
            )
            self.assertFalse(forged["ok"])
            self.assertEqual(forged["state"], "failed")
            self.assertIn("postcondition", forged["error"]["message"])


if __name__ == "__main__":
    unittest.main()
