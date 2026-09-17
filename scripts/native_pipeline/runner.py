"""Execute bounded native Blender pipelines through the existing headless runner."""

from __future__ import annotations

import hashlib
import json
import math
import os
import signal
import subprocess
from pathlib import Path

import agent_runtime

from .journal import (
    begin_attempt,
    collapse_attempts,
    finish_attempt,
    latest_attempt_by_step,
    pipeline_lock,
    read_journal,
)
from .manifest import ManifestError, load_manifest


EVIDENCE_SCOPE = "execution postconditions and declared artifact hashes"
DEFAULT_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
RUNTIME_FILES = (
    "scripts/headless-run.sh",
    "scripts/agent-run-headless.py",
    "scripts/agent_runtime.py",
    "scripts/native-pipeline.py",
    "scripts/native_pipeline/__init__.py",
    "scripts/native_pipeline/manifest.py",
    "scripts/native_pipeline/journal.py",
    "scripts/native_pipeline/runner.py",
)


class PipelineError(RuntimeError):
    """Raised when a native pipeline cannot safely continue."""


def sha256_file(path: os.PathLike[str] | str) -> str:
    """Hash current file bytes; receipts never rely on mtime/size identity alone."""
    source = Path(path)
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_identity(path: Path, repo_root: Path) -> dict:
    return {
        "path": path.relative_to(repo_root).as_posix(),
        "sha256": sha256_file(path),
    }


def runtime_identity(repo_root: os.PathLike[str] | str) -> dict:
    """Bind the launcher/runtime files and exact Blender executable bytes."""
    root = Path(repo_root).resolve()
    files = {}
    for relative in RUNTIME_FILES:
        path = root / relative
        if not path.is_file():
            raise PipelineError(f"runtime dependency is missing: {relative}")
        files[relative] = _relative_identity(path, root)

    blender = Path(os.environ.get("BLENDER_BIN", DEFAULT_BLENDER)).resolve()
    if not blender.is_file() or not os.access(blender, os.X_OK):
        raise PipelineError(
            f"Blender binary is missing or not executable: {blender} "
            "(set BLENDER_BIN to override)"
        )
    files["blender"] = {"path": str(blender), "sha256": sha256_file(blender)}
    return files


def _script_identity(step: dict, repo_root: Path) -> dict:
    path = repo_root / step["script"]
    return _relative_identity(path, repo_root)


def _project_inputs(step: dict, repo_root: Path) -> tuple[dict, dict]:
    absolute: dict[str, str] = {}
    hashes: dict[str, dict] = {}
    for relative in step["inputs"]:
        path = (repo_root / relative).resolve()
        if not path.is_file():
            raise PipelineError(f"declared project input disappeared: {relative}")
        absolute[relative] = str(path)
        hashes[f"project:{relative}"] = {
            "path": relative,
            "sha256": sha256_file(path),
        }
    return absolute, hashes


def _artifact_inputs(
    step: dict,
    executed: dict[str, dict],
    run_dir: Path,
) -> tuple[dict, dict]:
    absolute: dict[str, str] = {}
    hashes: dict[str, dict] = {}
    for reference in step["artifact_inputs"]:
        producer, output_name = reference.split(":", 1)
        producer_attempt = executed.get(producer)
        if producer_attempt is None:
            raise PipelineError(
                f"step {step['id']} needs artifact {reference}, but producer {producer} "
                "has no executed attempt"
            )
        recorded = (producer_attempt.get("outputs") or {}).get(output_name)
        if not isinstance(recorded, dict):
            raise PipelineError(f"executed producer {producer} lacks recorded artifact {output_name}")
        path_text = recorded.get("path")
        recorded_hash = recorded.get("sha256")
        if not isinstance(path_text, str) or not isinstance(recorded_hash, str):
            raise PipelineError(f"artifact receipt is incomplete: {reference}")
        path = (run_dir / path_text).resolve()
        try:
            path.relative_to(run_dir.resolve())
        except ValueError as exc:
            raise PipelineError(f"artifact receipt escapes run directory: {reference}") from exc
        if not path.is_file() or path.is_symlink():
            raise PipelineError(f"artifact is missing or is not an owned regular file: {reference}")
        actual_hash = sha256_file(path)
        if actual_hash != recorded_hash:
            raise PipelineError(f"artifact bytes changed since execution receipt: {reference}")
        absolute[reference] = str(path)
        hashes[f"artifact:{reference}"] = {
            "path": path_text,
            "sha256": actual_hash,
        }
    return absolute, hashes


def _input_context(
    step: dict,
    repo_root: Path,
    run_dir: Path,
    executed: dict[str, dict],
) -> tuple[dict, dict]:
    project_paths, project_hashes = _project_inputs(step, repo_root)
    artifact_paths, artifact_hashes = _artifact_inputs(step, executed, run_dir)
    context = {"project": project_paths, "artifacts": artifact_paths}
    hashes = dict(project_hashes)
    hashes.update(artifact_hashes)
    return context, hashes


def _check_postconditions(payload: dict, required: list[str]) -> dict:
    postconditions = payload.get("postconditions")
    if not isinstance(postconditions, dict) or not postconditions:
        raise PipelineError("AGENT_OK has no measured postconditions")
    measured = {}
    for key in required:
        if key not in postconditions:
            raise PipelineError(f"AGENT_OK is missing required postcondition: {key}")
        value = postconditions[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise PipelineError(f"required postcondition {key!r} must be numeric, not bool")
        if not math.isfinite(float(value)):
            raise PipelineError(f"required postcondition {key!r} must be finite")
        measured[key] = value
    return measured


def _collect_outputs(step: dict, attempt_dir: Path, run_dir: Path) -> dict:
    outputs = {}
    attempt_root = attempt_dir.resolve()
    for relative in step["outputs"]:
        path = attempt_dir / relative
        if path.is_symlink():
            raise PipelineError(f"declared output must not be a symlink: {relative}")
        resolved = path.resolve()
        try:
            resolved.relative_to(attempt_root)
        except ValueError as exc:
            raise PipelineError(f"declared output escaped its attempt directory: {relative}") from exc
        if not resolved.is_file():
            raise PipelineError(f"declared output was not produced: {relative}")
        outputs[relative] = {
            "path": resolved.relative_to(run_dir.resolve()).as_posix(),
            "sha256": sha256_file(resolved),
            "bytes": resolved.stat().st_size,
        }
    return outputs


def _write_log(path: Path, text: str) -> str:
    path.write_text(text, encoding="utf-8")
    return path.name


def _terminate_process_group(proc: subprocess.Popen) -> tuple[str, str]:
    """Terminate only the disposable headless process group spawned by this runner."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        return proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return proc.communicate()


def _launch_step(
    *,
    step: dict,
    attempt: dict,
    repo_root: Path,
    run_dir: Path,
    inputs: dict,
) -> tuple[str, dict]:
    attempt_dir = run_dir / attempt["output_dir"]
    attempt_dir.mkdir(parents=True, exist_ok=False)

    env = os.environ.copy()
    env.update(
        {
            # The native pipeline contract always uses the audited runtime wrapper
            # and factory startup. Parent-shell debug overrides must not leak in.
            "HEADLESS_RAW": "0",
            "HEADLESS_KEEP_ADDONS": "0",
            "DESIGN_OS_OUTPUT_DIR": str(attempt_dir.resolve()),
            "DESIGN_OS_INPUTS_JSON": json.dumps(inputs, sort_keys=True),
            "DESIGN_OS_PIPELINE_ID": attempt["pipeline_id"],
            "DESIGN_OS_STEP_ID": step["id"],
            "DESIGN_OS_ATTEMPT_ID": attempt["attempt_id"],
            "DESIGN_OS_RUN_DIR": str(run_dir.resolve()),
        }
    )
    command = ["bash", str(repo_root / "scripts/headless-run.sh"), str(repo_root / step["script"])]
    proc = subprocess.Popen(
        command,
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    timed_out = False
    interrupted = None
    try:
        stdout, stderr = proc.communicate(timeout=step["timeout_seconds"])
    except subprocess.TimeoutExpired:
        timed_out = True
        stdout, stderr = _terminate_process_group(proc)
    except BaseException as exc:
        # A Ctrl-C or local controller exception after launch cannot be allowed to
        # leave the disposable Blender child running with an untracked outcome.
        interrupted = exc
        stdout, stderr = _terminate_process_group(proc)

    try:
        stdout_log = _write_log(attempt_dir / "stdout.log", stdout)
        stderr_log = _write_log(attempt_dir / "stderr.log", stderr)
    except OSError as exc:
        return "unknown", {
            "returncode": proc.returncode,
            "scope": EVIDENCE_SCOPE,
            "error": {
                "type": type(exc).__name__,
                "message": f"headless process completed but execution logs could not be persisted: {exc}",
            },
        }
    common = {
        "returncode": proc.returncode,
        "stdout_log": stdout_log,
        "stderr_log": stderr_log,
        "scope": EVIDENCE_SCOPE,
    }
    if interrupted is not None:
        common["error"] = {
            "type": type(interrupted).__name__,
            "message": (
                "controller was interrupted after headless launch; the child process group "
                "was terminated and the attempt remains unknown"
            ),
        }
        return "unknown", common
    if timed_out:
        common["error"] = {
            "type": "TimeoutUnknown",
            "message": (
                f"headless process exceeded {step['timeout_seconds']}s after launch; "
                "the attempt outcome is unknown and must not be replayed automatically"
            ),
        }
        return "unknown", common

    tag, payload = agent_runtime.parse_sentinel(stdout)
    common["sentinel"] = tag or "MISSING"
    if tag == agent_runtime.SENTINEL_FAIL:
        common["error"] = payload.get("error") if isinstance(payload, dict) else {
            "type": "AgentFailure",
            "message": "AGENT_FAIL had no parseable payload",
        }
        return "failed", common
    if tag != agent_runtime.SENTINEL_OK:
        common["error"] = {
            "type": "MissingSentinelUnknown",
            "message": "headless process returned without an authoritative AGENT_OK/AGENT_FAIL sentinel",
        }
        return "unknown", common
    if proc.returncode != 0:
        common["error"] = {
            "type": "SentinelExitDisagreement",
            "message": f"AGENT_OK was observed but headless launcher exited {proc.returncode}",
        }
        return "unknown", common
    if not isinstance(payload, dict):
        common["error"] = {
            "type": "BadSentinelUnknown",
            "message": "AGENT_OK payload was not parseable",
        }
        return "unknown", common

    try:
        required = _check_postconditions(payload, step["required_postconditions"])
        outputs = _collect_outputs(step, attempt_dir, run_dir)
    except PipelineError as exc:
        common["error"] = {"type": type(exc).__name__, "message": str(exc)}
        common["postconditions"] = payload.get("postconditions") or {}
        return "failed", common
    common["postconditions"] = payload["postconditions"]
    common["required_postconditions"] = required
    common["outputs"] = outputs
    return "executed", common


def _current_output_hashes(attempt: dict, run_dir: Path) -> dict:
    recorded = attempt.get("outputs")
    if not isinstance(recorded, dict):
        raise PipelineError(f"executed attempt {attempt['attempt_id']} has no output receipt")
    current = {}
    for name, row in recorded.items():
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise PipelineError(f"bad output receipt on {attempt['attempt_id']}: {name}")
        path = (run_dir / row["path"]).resolve()
        try:
            path.relative_to(run_dir.resolve())
        except ValueError as exc:
            raise PipelineError(f"output receipt escapes run directory: {name}") from exc
        if not path.is_file() or path.is_symlink():
            raise PipelineError(f"recorded output is missing or not a regular file: {name}")
        current[name] = sha256_file(path)
    return current


def _validate_resume_receipt(
    *,
    attempt: dict,
    step: dict,
    manifest: dict,
    repo_root: Path,
    run_dir: Path,
    runtime: dict,
    input_hashes: dict,
) -> None:
    if attempt.get("state") != "executed":
        raise PipelineError(
            f"step {step['id']} has unresolved state {attempt.get('state')!r}; "
            "resume will not retry it. Inspect the run and use a new run directory for deliberate recovery."
        )
    expected_script = _script_identity(step, repo_root)
    comparisons = {
        "manifest": (attempt.get("manifest_sha256"), manifest["_sha256"]),
        "script": (attempt.get("script"), expected_script),
        "runtime": (attempt.get("runtime_identity"), runtime),
        "inputs": (attempt.get("input_sha256"), input_hashes),
    }
    for label, (old, current) in comparisons.items():
        if old != current:
            raise PipelineError(
                f"cannot resume step {step['id']}: {label} identity changed; use a new run directory"
            )
    recorded_outputs = attempt.get("outputs") or {}
    if set(recorded_outputs) != set(step["outputs"]):
        raise PipelineError(f"cannot resume step {step['id']}: declared outputs changed")
    current_hashes = _current_output_hashes(attempt, run_dir)
    for name, actual in current_hashes.items():
        if recorded_outputs[name].get("sha256") != actual:
            raise PipelineError(
                f"cannot resume step {step['id']}: output bytes changed for {name}; use a new run directory"
            )


def _validate_existing_run(records: list[dict], manifest: dict) -> None:
    """Reject a run directory bound to any other pipeline or manifest bytes."""
    known_steps = {step["id"] for step in manifest["steps"]}
    for attempt in collapse_attempts(records):
        if attempt.get("pipeline_id") != manifest["pipeline_id"]:
            raise PipelineError(
                "run directory contains attempt evidence for a different pipeline; "
                "use a new run directory"
            )
        if attempt.get("manifest_sha256") != manifest["_sha256"]:
            raise PipelineError(
                "run directory contains attempt evidence from different manifest bytes; "
                "resume is refused before launching any step"
            )
        if attempt.get("step_id") not in known_steps:
            raise PipelineError(
                f"run directory contains attempt for unknown step {attempt.get('step_id')!r}; "
                "use a new run directory"
            )


def _post_launch_identity_drift(
    *,
    attempt: dict,
    step: dict,
    repo_root: Path,
    run_dir: Path,
    executed: dict[str, dict],
) -> dict:
    """Rehash the step script and caller-declared inputs after child completion."""
    drift: dict[str, dict] = {}
    try:
        current_script = _script_identity(step, repo_root)
    except OSError as exc:
        drift["script"] = {"before": attempt.get("script"), "after_error": str(exc)}
    else:
        if current_script != attempt.get("script"):
            drift["script"] = {"before": attempt.get("script"), "after": current_script}

    try:
        _context, current_inputs = _input_context(step, repo_root, run_dir, executed)
    except (OSError, PipelineError) as exc:
        drift["inputs"] = {
            "before": attempt.get("input_sha256"),
            "after_error": str(exc),
        }
    else:
        if current_inputs != attempt.get("input_sha256"):
            drift["inputs"] = {
                "before": attempt.get("input_sha256"),
                "after": current_inputs,
            }
    before_runtime = {
        key: value
        for key, value in (attempt.get("runtime_identity") or {}).items()
        if key != "blender"
    }
    try:
        current_runtime = {
            relative: _relative_identity(repo_root / relative, repo_root)
            for relative in RUNTIME_FILES
        }
    except OSError as exc:
        drift["runtime_sources"] = {
            "before": before_runtime,
            "after_error": str(exc),
        }
    else:
        if current_runtime != before_runtime:
            drift["runtime_sources"] = {
                "before": before_runtime,
                "after": current_runtime,
            }
    return drift


def check_pipeline(
    manifest_path: os.PathLike[str] | str,
    *,
    repo_root: os.PathLike[str] | str,
) -> dict:
    """Validate manifest and bind current local source/runtime identities without executing Blender."""
    root = Path(repo_root).resolve()
    manifest = load_manifest(manifest_path, root)
    runtime = runtime_identity(root)
    rows = []
    for step in manifest["steps"]:
        _paths, hashes = _project_inputs(step, root)
        rows.append(
            {
                "id": step["id"],
                "script": _script_identity(step, root),
                "project_inputs": hashes,
                "artifact_inputs": list(step["artifact_inputs"]),
                "depends_on": list(step["depends_on"]),
                "outputs": list(step["outputs"]),
                "required_postconditions": list(step["required_postconditions"]),
            }
        )
    return {
        "ok": True,
        "pipeline_id": manifest["pipeline_id"],
        "manifest_sha256": manifest["_sha256"],
        "steps": rows,
        "runtime_identity": runtime,
        "scope": "static manifest, declared source/input and runtime byte identities only",
    }


def run_pipeline(
    manifest_path: os.PathLike[str] | str,
    *,
    run_dir: os.PathLike[str] | str,
    repo_root: os.PathLike[str] | str,
    resume: bool = False,
) -> dict:
    """Run untouched steps sequentially; resume only reuses hash-matching executed attempts."""
    root = Path(repo_root).resolve()
    run_root = Path(run_dir).resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(manifest_path, root)
    runtime = runtime_identity(root)
    journal_path = run_root / "journal.jsonl"

    with pipeline_lock(run_root):
        records = read_journal(journal_path)
        if records:
            _validate_existing_run(records, manifest)
        latest = latest_attempt_by_step(records)
        if records and not resume:
            raise PipelineError(
                f"run directory already contains attempt evidence: {run_root}; "
                "use --resume for pending steps or choose a new run directory"
            )

        executed: dict[str, dict] = {}
        report_steps: list[dict] = []
        for step in manifest["steps"]:
            missing_dep = next((dep for dep in step["depends_on"] if dep not in executed), None)
            if missing_dep:
                raise PipelineError(
                    f"step {step['id']} cannot start because dependency {missing_dep} is not executed"
                )
            inputs, input_hashes = _input_context(step, root, run_root, executed)
            previous = latest.get(step["id"])
            if previous is not None:
                if not resume:
                    raise PipelineError(f"step {step['id']} already has attempt evidence")
                _validate_resume_receipt(
                    attempt=previous,
                    step=step,
                    manifest=manifest,
                    repo_root=root,
                    run_dir=run_root,
                    runtime=runtime,
                    input_hashes=input_hashes,
                )
                executed[step["id"]] = previous
                report_steps.append(
                    {
                        "id": step["id"],
                        "state": "executed",
                        "attempt_id": previous["attempt_id"],
                        "reused": True,
                        "scope": EVIDENCE_SCOPE,
                    }
                )
                continue

            # A resume may launch only a never-attempted, still-pending step.
            attempt = begin_attempt(
                journal_path,
                pipeline_id=manifest["pipeline_id"],
                step_id=step["id"],
                manifest_sha256=manifest["_sha256"],
                script=_script_identity(step, root),
                runtime_identity=runtime,
                input_sha256=input_hashes,
                output_base=f"steps/{step['id']}",
                declared_outputs=step["outputs"],
                required_postconditions=step["required_postconditions"],
            )
            try:
                state, result = _launch_step(
                    step=step,
                    attempt=attempt,
                    repo_root=root,
                    run_dir=run_root,
                    inputs=inputs,
                )
            except OSError as exc:  # no child could be launched from this controller call
                result = {
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                    "scope": EVIDENCE_SCOPE,
                }
                state = "failed"
            except BaseException as exc:  # uncertainty after durable start
                result = {
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                    "scope": EVIDENCE_SCOPE,
                }
                state = "unknown"
            if state == "executed":
                drift = _post_launch_identity_drift(
                    attempt=attempt,
                    step=step,
                    repo_root=root,
                    run_dir=run_root,
                    executed=executed,
                )
                if drift:
                    state = "unknown"
                    result = dict(result)
                    result["identity_drift"] = drift
                    result["error"] = {
                        "type": "IdentityDriftUnknown",
                        "message": (
                            "step script or caller-declared inputs changed after launch; "
                            "the execution receipt cannot be bound to one stable source identity"
                        ),
                    }
            finished = finish_attempt(
                journal_path,
                attempt["attempt_id"],
                state=state,
                result=result,
            )
            report_steps.append(
                {
                    "id": step["id"],
                    "state": state,
                    "attempt_id": attempt["attempt_id"],
                    "reused": False,
                    "scope": EVIDENCE_SCOPE,
                }
            )
            if state != "executed":
                return {
                    "ok": False,
                    "pipeline_id": manifest["pipeline_id"],
                    "manifest_sha256": manifest["_sha256"],
                    "steps": report_steps,
                    "blocked_on": step["id"],
                    "state": state,
                    "error": finished.get("error"),
                    "scope": EVIDENCE_SCOPE,
                }
            executed[step["id"]] = {**attempt, **finished}

        return {
            "ok": True,
            "pipeline_id": manifest["pipeline_id"],
            "manifest_sha256": manifest["_sha256"],
            "steps": report_steps,
            "state": "executed",
            "scope": EVIDENCE_SCOPE,
        }


def status_pipeline(run_dir: os.PathLike[str] | str) -> dict:
    """Read-only attempt status. It deliberately makes no quality/readiness inference."""
    root = Path(run_dir).resolve()
    journal_path = root / "journal.jsonl"
    records = read_journal(journal_path)
    attempts = []
    for attempt in collapse_attempts(records):
        attempts.append(
            {
                "pipeline_id": attempt.get("pipeline_id"),
                "step_id": attempt.get("step_id"),
                "attempt_id": attempt.get("attempt_id"),
                "attempt_number": attempt.get("attempt_number"),
                "state": attempt.get("state"),
                "scope": attempt.get("scope", EVIDENCE_SCOPE),
            }
        )
    return {
        "ok": True,
        "run_dir": str(root),
        "attempts": attempts,
        "record_count": len(records),
        "scope": "journaled execution state only; no geometry, visual or manufacture readiness inference",
    }
