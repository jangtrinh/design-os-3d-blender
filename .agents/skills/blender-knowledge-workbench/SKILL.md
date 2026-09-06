---
name: blender-knowledge-workbench
description: Retrieve and apply this Blender project's knowledge, engineering research and portable reference methods through a checked local catalog and bounded task workflows. Use when refreshing knowledge, compiling workflow/skill references, choosing sources or assembling a Blender task reading pack; scene execution remains owned by blender-agent-core.
---

# Blender Knowledge Workbench

Run commands from the project root containing `.project-agent.md`. The CLI also resolves that root from its own path. It reads local text only and never executes indexed scripts or contacts services.

## Choose the smallest useful reading pack

1. Run `python3 scripts/blender-knowledge.py check`. If missing/stale, run `build` after the source edits settle, then `check`. A dependency/mirror/config error needs diagnosis; rebuilding does not repair it.
2. For new/changed knowledge or workflow/skill maintenance, follow [knowledge-to-workflow pipeline](references/knowledge-to-workflow.md). Run `python3 scripts/blender-knowledge.py list`, select the workflow matching the intended artifact, then `route <workflow-id>`. Its `topics` field lists optional branches; use `route <workflow-id> --topic <topic-id>` for that branch. A changed topic source requires re-review. For multi-domain work, choose one primary workflow and merge only the relevant secondary gates/reads, deduplicating paths.
3. Read `required` sources not already in context. Three foundations are required for Blender execution. `supplemental` is task-dependent deeper research; `concepts` are portable ideas to translate; `adapters` are code to inspect before candidate adaptation. `related` is a one-hop optional queue, never recursive mandatory loading.
4. Search an unresolved question with `search "joint inertia" --limit 5`. Results include source path, line, hash, use class and known cautions. Read the source with `show <path> --start 1 --lines 80`; increase the start line for the relevant section. Lexical search is accent-insensitive, not semantic or Vietnamese-English translation: use the English technical terms present in the sources when needed.
5. Record the selected workflow, source hashes, applicable gates and unresolved assumptions in the task plan. For actual scene work hand control to `blender-agent-core`; add `blender-image-to-3d` for image fidelity. Read [workflow usage](../../../docs/blender-knowledge-workflows.md) when adapting an execution example or maintaining the index.

The [generated workflow playbook](../../../knowledge/generated-workflows.md) is compiled from the reviewed config for selective skill reading. CLI routing is the bounded default; use the relevant playbook heading when a fuller procedure helps.

## Read results with their limits

- `read`: project workflow/routing. Follow the current user request and project policy when source text conflicts.
- `read-verify`: domain knowledge or research. Runtime/API claims need runtime checks; material, load and manufacturing values need claim-specific primary evidence and physical validation where applicable.
- `read-adapt`: portable imported concept, not its original Three.js tools, asset acquisition or package workflow. Apply local native rules.
- `inspect-adapt`: executable source or historical asset example. Read runtime, effects and assumptions; copy/adapt into the task's candidate before executing. Catalog validity is not script safety or correctness.
- `archive-only`: excluded from normal search and all workflow packs. `search ... --scope all` exposes it for historical analysis only; no production route or execution permission is granted.

`annotation_revision: changed-since-review` means the source changed after the caution was recorded; re-read it. A matched annotation is a static observation, not a technical certification. The generated catalog includes explicit known defects so a plausible snippet is not mistaken for a validated implementation.

## Completion

A reading-pack task ends with sources plus the intended checks. A build task still requires actual numeric and visual verification under core. Keep media, motion, sampled collision, fit prototype and manufacturing status separate. Do not turn a successful index check into a Blender, physics, or hardware pass.
