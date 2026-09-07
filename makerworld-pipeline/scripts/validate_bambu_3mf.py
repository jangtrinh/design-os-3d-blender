#!/usr/bin/env python3
"""Validate a Bambu-Studio-shaped .3mf project file: 10 structural checks,
each reported PASS/FAIL/SKIP/INFO with a measured value. No score, no
verdict theatre -- SKIP is a first-class, honest result (e.g. an unsliced
project has no slice_info).

Exit codes: 0 = no FAIL among non-SKIP checks, 1 = at least one check
FAILED, 2 = input unreadable (not a ZIP / file does not exist / not a
valid 3MF container at all).
"""
from __future__ import annotations

import argparse
import json
import sys

import bambu_3mf_reader as reader
import bambu_checks as checks


def _parse_bed(bed_str):
    parts = bed_str.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("--bed must be X,Y,Z in mm, e.g. 180,180,180")
    try:
        return tuple(float(p) for p in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"--bed values must be numeric: {exc}") from exc


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Validate a Bambu-Studio-shaped .3mf project file (no score, PASS/FAIL/SKIP/INFO only)."
    )
    parser.add_argument("file", help="path to the .3mf file to validate")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON instead of a table")
    parser.add_argument("--expect", metavar="FILE",
                         help="a .expected.json sidecar (per-plate bbox ground truth) to diff per_plate_bbox_mm against")
    parser.add_argument("--bed", type=_parse_bed, default=(180.0, 180.0, 180.0),
                         help="bed volume X,Y,Z in mm for the informational bed_fit check (default 180,180,180)")
    return parser


def _run_one(check_fn, zf, expect, bed):
    """Run a single check, converting ANY exception (missing member the
    check assumed present, malformed XML/JSON it did not expect, etc.)
    into a FAIL row instead of crashing the whole CLI. A check with a
    dependency it cannot satisfy is a legitimate FAIL, not a stack trace."""
    check_id = check_fn.__name__[len("check_"):]
    try:
        if check_fn is checks.check_per_plate_bbox_mm:
            return check_fn(zf, expect=expect)
        if check_fn is checks.check_bed_fit:
            return check_fn(zf, bed_mm=bed)
        return check_fn(zf)
    except Exception as exc:  # noqa: BLE001 -- any check failure is a FAIL row, never a crash
        return {"id": check_id, "status": "FAIL", "note": f"check could not run: {exc}", "measured": {}}


def run_checks(path, expect=None, bed=(180.0, 180.0, 180.0)):
    """Returns (checks_list, exit_code). Raises reader.UnreadableInputError
    for the exit-2 case; caller handles that."""
    with reader.open_zip_safely(path) as zf:
        results = [_run_one(check_fn, zf, expect, bed) for check_fn in checks.CHECK_ORDER]
    exit_code = 1 if any(r["status"] == "FAIL" for r in results) else 0
    return results, exit_code


def summarize(results):
    summary = {"pass": 0, "fail": 0, "skip": 0}
    for r in results:
        status = r["status"].lower()
        if status in summary:
            summary[status] += 1
        # INFO is neither pass, fail, nor skip -- it never affects exit code
        # or the summary counters (it is not one of the three tallied kinds).
    return summary


def print_json(path, results):
    payload = {"file": path, "checks": results, "summary": summarize(results)}
    print(json.dumps(payload, indent=1, default=str))


def print_table(path, results):
    print(f"validate_bambu_3mf: {path}")
    width = max(len(r["id"]) for r in results)
    for r in results:
        print(f"  {r['id']:<{width}}  {r['status']:<5}  {r['note']}")
    summary = summarize(results)
    print(f"summary: pass={summary['pass']} fail={summary['fail']} skip={summary['skip']}")


def main(argv=None):
    args = build_arg_parser().parse_args(argv)

    expect = None
    if args.expect:
        try:
            with open(args.expect, encoding="utf-8") as fh:
                expect = json.load(fh)
        except OSError as exc:
            print(f"cannot read --expect file: {exc}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as exc:
            print(f"--expect file is not valid JSON: {exc}", file=sys.stderr)
            return 2

    try:
        results, exit_code = run_checks(args.file, expect=expect, bed=args.bed)
    except reader.UnreadableInputError as exc:
        if args.json:
            print(json.dumps({"file": args.file, "checks": [], "summary": {"pass": 0, "fail": 0, "skip": 0},
                               "error": str(exc)}))
        else:
            print(f"cannot read {args.file} as a 3MF/ZIP container: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print_json(args.file, results)
    else:
        print_table(args.file, results)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
