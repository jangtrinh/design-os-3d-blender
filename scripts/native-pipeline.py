#!/usr/bin/env python3
"""CLI for bounded, durable native Blender headless pipelines."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from native_pipeline.journal import JournalError  # noqa: E402
from native_pipeline.manifest import ManifestError  # noqa: E402
from native_pipeline.runner import PipelineError, check_pipeline, run_pipeline, status_pipeline  # noqa: E402


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (REPO_ROOT / path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="validate manifest and bind local source/runtime identities")
    p_check.add_argument("manifest")

    p_run = sub.add_parser("run", help="run untouched steps through scripts/headless-run.sh")
    p_run.add_argument("manifest")
    p_run.add_argument("--run-dir", required=True)
    p_run.add_argument("--resume", action="store_true",
                       help="reuse matching executed attempts and run only never-attempted pending steps")

    p_status = sub.add_parser("status", help="read the append-only run journal")
    p_status.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "check":
            result = check_pipeline(_path(args.manifest), repo_root=REPO_ROOT)
        elif args.command == "run":
            result = run_pipeline(
                _path(args.manifest),
                run_dir=_path(args.run_dir),
                repo_root=REPO_ROOT,
                resume=args.resume,
            )
        else:
            result = status_pipeline(_path(args.run_dir))
    except (ManifestError, JournalError, PipelineError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": {"type": type(exc).__name__, "message": str(exc)}}))
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
