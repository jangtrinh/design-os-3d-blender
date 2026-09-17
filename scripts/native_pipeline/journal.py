"""Durable append-only attempt journal for native Blender pipelines."""

from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


TERMINAL_STATES = {"executed", "failed", "unknown"}


class JournalError(RuntimeError):
    """Raised for corrupt journals or concurrent writers."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_unlocked(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise JournalError(f"corrupt journal JSON at line {line_no}: {exc}") from exc
            if not isinstance(row, dict):
                raise JournalError(f"journal line {line_no} is not an object")
            records.append(row)
    return records


def read_journal(path: os.PathLike[str] | str) -> list[dict]:
    source = Path(path)
    if not source.exists():
        return []
    lock_path = source.with_name(source.name + ".lock")
    if not lock_path.is_file():
        raise JournalError(f"journal exists without its writer lock file: {source}")
    with lock_path.open("r") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_SH)
        try:
            return _read_unlocked(source)
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _journal_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def pipeline_lock(run_dir: os.PathLike[str] | str):
    """Hold the single-writer lock for an entire pipeline mutation."""
    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / ".pipeline.lock"
    with lock_path.open("a+") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise JournalError(f"pipeline already has an active writer: {root}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _append_unlocked(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(payload + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def begin_attempt(
    journal_path: os.PathLike[str] | str,
    *,
    pipeline_id: str,
    step_id: str,
    manifest_sha256: str,
    script: dict,
    runtime_identity: dict,
    input_sha256: dict,
    output_base: str,
    declared_outputs: list[str],
    required_postconditions: list[str],
) -> dict:
    """Append and fsync a `running` attempt before process launch."""
    path = Path(journal_path)
    with _journal_lock(path):
        records = _read_unlocked(path)
        numbers = [
            int(row.get("attempt_number", 0))
            for row in records
            if row.get("event") == "attempt_started" and row.get("step_id") == step_id
        ]
        number = max(numbers, default=0) + 1
        attempt_id = f"{step_id}-attempt-{number:04d}"
        output_dir = f"{output_base.rstrip('/')}/attempt-{number:04d}"
        record = {
            "schema": 1,
            "event": "attempt_started",
            "pipeline_id": pipeline_id,
            "step_id": step_id,
            "attempt_id": attempt_id,
            "attempt_number": number,
            "state": "running",
            "started_at": _now(),
            "manifest_sha256": manifest_sha256,
            "script": script,
            "runtime_identity": runtime_identity,
            "input_sha256": input_sha256,
            "output_dir": output_dir,
            "declared_outputs": list(declared_outputs),
            "required_postconditions": list(required_postconditions),
        }
        _append_unlocked(path, record)
        return record


def finish_attempt(
    journal_path: os.PathLike[str] | str,
    attempt_id: str,
    *,
    state: str,
    result: dict | None = None,
) -> dict:
    """Append a terminal event for one previously started attempt."""
    if state not in TERMINAL_STATES:
        raise JournalError(f"invalid terminal state: {state}")
    reserved = {
        "schema",
        "event",
        "pipeline_id",
        "step_id",
        "attempt_id",
        "attempt_number",
        "state",
        "finished_at",
    }
    if result and reserved.intersection(result):
        overlap = ", ".join(sorted(reserved.intersection(result)))
        raise JournalError(f"terminal result cannot overwrite journal identity fields: {overlap}")
    path = Path(journal_path)
    with _journal_lock(path):
        records = _read_unlocked(path)
        start = next(
            (
                row
                for row in records
                if row.get("event") == "attempt_started" and row.get("attempt_id") == attempt_id
            ),
            None,
        )
        if start is None:
            raise JournalError(f"attempt has no start record: {attempt_id}")
        if any(
            row.get("event") == "attempt_finished" and row.get("attempt_id") == attempt_id
            for row in records
        ):
            raise JournalError(f"attempt is already terminal: {attempt_id}")
        record = {
            "schema": 1,
            "event": "attempt_finished",
            "pipeline_id": start["pipeline_id"],
            "step_id": start["step_id"],
            "attempt_id": attempt_id,
            "attempt_number": start["attempt_number"],
            "state": state,
            "finished_at": _now(),
        }
        if result:
            record.update(result)
        _append_unlocked(path, record)
        return record


def collapse_attempts(records: list[dict]) -> list[dict]:
    """Return start records overlaid with their optional terminal record."""
    ordered: list[str] = []
    attempts: dict[str, dict] = {}
    for row in records:
        attempt_id = row.get("attempt_id")
        if not attempt_id:
            continue
        if row.get("event") == "attempt_started":
            if attempt_id in attempts:
                raise JournalError(f"duplicate attempt start: {attempt_id}")
            attempts[attempt_id] = dict(row)
            ordered.append(attempt_id)
        elif row.get("event") == "attempt_finished":
            if attempt_id not in attempts:
                raise JournalError(f"attempt finish precedes start: {attempt_id}")
            attempts[attempt_id].update(row)
        else:
            raise JournalError(f"unknown journal event: {row.get('event')!r}")
    return [attempts[attempt_id] for attempt_id in ordered]


def latest_attempt_by_step(records: list[dict]) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for attempt in collapse_attempts(records):
        latest[attempt["step_id"]] = attempt
    return latest
