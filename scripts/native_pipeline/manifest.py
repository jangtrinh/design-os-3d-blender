"""Validation for bounded native Blender pipeline manifests."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath


MAX_STEPS = 32
MAX_TIMEOUT_SECONDS = 3600
RESERVED_OUTPUTS = {"stdout.log", "stderr.log"}
PIPELINE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
STEP_KEYS = {
    "id",
    "script",
    "depends_on",
    "inputs",
    "artifact_inputs",
    "outputs",
    "required_postconditions",
    "timeout_seconds",
}


class ManifestError(ValueError):
    """Raised when a native-pipeline manifest is invalid."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _project_file(repo_root: Path, value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label} must be a non-empty project-relative path")
    raw = value.replace("\\", "/")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or raw.startswith("~/"):
        raise ManifestError(f"{label} escapes the project root: {value!r}")
    candidate = (repo_root / Path(*path.parts)).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise ManifestError(f"{label} escapes the project root: {value!r}") from exc
    if not candidate.is_file():
        raise ManifestError(f"{label} is missing or not a file: {value!r}")
    return path.as_posix()


def _output_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label} must be a non-empty path relative to the step output directory")
    raw = value.replace("\\", "/")
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or path.as_posix() in {"", "."}:
        raise ManifestError(f"{label} escapes the step output directory: {value!r}")
    if path.as_posix() in RESERVED_OUTPUTS:
        raise ManifestError(
            f"{label} uses reserved pipeline log filename: {path.as_posix()!r}"
        )
    return path.as_posix()


def _string_list(value: object, label: str, *, nonempty: bool = False) -> list[str]:
    if value is None:
        value = []
    if not isinstance(value, list):
        raise ManifestError(f"{label} must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ManifestError(f"{label} entries must be non-empty strings")
        if item in result:
            raise ManifestError(f"{label} contains duplicate entry: {item!r}")
        result.append(item)
    if nonempty and not result:
        raise ManifestError(f"{label} must contain at least one entry")
    return result


def _parse_artifact_ref(value: str, label: str) -> tuple[str, str]:
    if ":" not in value:
        raise ManifestError(f"{label} must use '<step-id>:<output-path>' syntax")
    step_id, output = value.split(":", 1)
    if not step_id or not output:
        raise ManifestError(f"{label} must use '<step-id>:<output-path>' syntax")
    return step_id, _output_path(output, label)


def validate_manifest(data: object, repo_root: os.PathLike[str] | str, *, max_steps: int = MAX_STEPS) -> dict:
    """Return a normalized manifest or raise ``ManifestError``.

    The list order is the execution order. Dependencies must point to earlier
    steps, which gives a bounded topological order without a graph scheduler.
    """
    root = Path(repo_root).resolve()
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be a JSON object")
    allowed_root = {"version", "pipeline_id", "steps"}
    extras = sorted(set(data) - allowed_root)
    if extras:
        raise ManifestError(f"unknown manifest fields: {', '.join(extras)}")
    if data.get("version") != 1:
        raise ManifestError("manifest version must be 1")
    pipeline_id = data.get("pipeline_id")
    if not isinstance(pipeline_id, str) or not PIPELINE_ID_RE.match(pipeline_id):
        raise ManifestError("pipeline_id must match [A-Za-z0-9][A-Za-z0-9._-]{0,79}")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ManifestError("steps must be a non-empty list")
    if len(steps) > max_steps:
        raise ManifestError(f"steps exceeds bounded limit {max_steps}")

    normalized_steps: list[dict] = []
    prior: dict[str, dict] = {}
    for index, raw_step in enumerate(steps):
        where = f"steps[{index}]"
        if not isinstance(raw_step, dict):
            raise ManifestError(f"{where} must be an object")
        extras = sorted(set(raw_step) - STEP_KEYS)
        if extras:
            raise ManifestError(f"{where} has unknown fields: {', '.join(extras)}")
        step_id = raw_step.get("id")
        if not isinstance(step_id, str) or not PIPELINE_ID_RE.match(step_id):
            raise ManifestError(f"{where}.id has invalid syntax")
        if step_id in prior:
            raise ManifestError(f"duplicate step id: {step_id}")

        script = _project_file(root, raw_step.get("script"), f"{where}.script")
        depends_on = _string_list(raw_step.get("depends_on", []), f"{where}.depends_on")
        for dep in depends_on:
            if dep not in prior:
                raise ManifestError(
                    f"{where}.depends_on references {dep!r} before it exists; "
                    "steps must already be in topological order"
                )

        inputs = [
            _project_file(root, item, f"{where}.inputs")
            for item in _string_list(raw_step.get("inputs", []), f"{where}.inputs")
        ]
        outputs = [
            _output_path(item, f"{where}.outputs")
            for item in _string_list(
                raw_step.get("outputs"), f"{where}.outputs", nonempty=True
            )
        ]
        if len(set(outputs)) != len(outputs):
            raise ManifestError(f"{where}.outputs contains duplicates after normalization")

        artifact_inputs = _string_list(
            raw_step.get("artifact_inputs", []), f"{where}.artifact_inputs"
        )
        normalized_artifacts: list[str] = []
        for ref in artifact_inputs:
            producer, output = _parse_artifact_ref(ref, f"{where}.artifact_inputs")
            if producer not in depends_on:
                raise ManifestError(
                    f"{where}.artifact_inputs reference {producer!r}, which is not in depends_on"
                )
            if output not in prior[producer]["outputs"]:
                raise ManifestError(
                    f"{where}.artifact_inputs references undeclared output {producer}:{output}"
                )
            normalized_artifacts.append(f"{producer}:{output}")

        required = _string_list(
            raw_step.get("required_postconditions"),
            f"{where}.required_postconditions",
            nonempty=True,
        )
        timeout = raw_step.get("timeout_seconds", 300)
        if isinstance(timeout, bool) or not isinstance(timeout, int):
            raise ManifestError(f"{where}.timeout_seconds must be an integer")
        if not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
            raise ManifestError(
                f"{where}.timeout_seconds must be between 1 and {MAX_TIMEOUT_SECONDS}"
            )

        step = {
            "id": step_id,
            "script": script,
            "depends_on": depends_on,
            "inputs": inputs,
            "artifact_inputs": normalized_artifacts,
            "outputs": outputs,
            "required_postconditions": required,
            "timeout_seconds": timeout,
        }
        normalized_steps.append(step)
        prior[step_id] = step

    return {"version": 1, "pipeline_id": pipeline_id, "steps": normalized_steps}


def load_manifest(path: os.PathLike[str] | str, repo_root: os.PathLike[str] | str) -> dict:
    """Read, hash, validate and return a normalized manifest."""
    manifest_path = Path(path).resolve()
    if not manifest_path.is_file():
        raise ManifestError(f"manifest is missing or not a file: {manifest_path}")
    raw = manifest_path.read_bytes()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid manifest JSON: {exc}") from exc
    normalized = validate_manifest(data, repo_root)
    normalized["_source_path"] = str(manifest_path)
    normalized["_sha256"] = hashlib.sha256(raw).hexdigest()
    return normalized
