#!/usr/bin/env python3
"""self_check.py — Deterministic offline self-check for design-os-3d-blender."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_JSON = (
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    ".factory-plugin/plugin.json",
    ".factory-plugin/marketplace.json",
)

REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "PRIVACY.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    "llms.txt",
    "docs/cookbook.md",
    "commands/doctor.md",
    "prompts/doctor.md",
)


def main() -> int:
    issues: list[str] = []
    for rel in REQUIRED_JSON:
        p = ROOT / rel
        if not p.is_file():
            issues.append(f"missing JSON manifest: {rel}")
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                issues.append(f"manifest is not a JSON object: {rel}")
        except Exception as exc:
            issues.append(f"invalid JSON in {rel}: {exc}")

    for rel in REQUIRED_FILES:
        p = ROOT / rel
        if not p.is_file() or p.stat().st_size == 0:
            issues.append(f"missing or empty required file: {rel}")

    skills = list((ROOT / "skills").glob("*/SKILL.md")) if (ROOT / "skills").is_dir() else []
    if not skills:
        issues.append("missing skills/<slug>/SKILL.md")

    if issues:
        for item in issues:
            print(f"FAIL: {item}", file=sys.stderr)
        return 1

    print("ok: design-os-3d-blender self-check passed (design-os-3d-blender)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
