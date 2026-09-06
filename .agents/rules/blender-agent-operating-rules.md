# Blender Agent Operating Rules (Antigravity)

This file exists so Google Antigravity (Gemini) agents follow the same
discipline as Claude Code / Codex on this repo, without changing how those
runtimes operate. If Antigravity truncates or skips loading anything else,
these 8 rules still apply.

## Canonical sources — read these first

- `AGENTS.md` (repo root) is the canonical operating file: mandatory loop,
  execution modes, verify ladder, failure map. This rules file restates its
  essentials only; `AGENTS.md` wins on any conflict.
- `.project-agent.md` (repo root) holds binding rules: tech stack, Native
  Asset Policy, precedence order. It outranks `AGENTS.md`.
- `.agents/skills/blender-agent-core/SKILL.md` is the detailed router/skill
  version of the same loop. Read it before any non-trivial Blender task.
- Precedence on conflict: `.project-agent.md` > `AGENTS.md` >
  `.agents/skills/*/SKILL.md` + references > `knowledge/` > `docs/`.

`<ROOT>` below means the absolute repo path on the machine currently running
(e.g. `/Users/jang/Products/Blender`).

## The 8 rules an agent must never violate

### 1. Contract before detail
A part that will be printed or manufactured needs `builds/<slug>/spec.json`
(schema `specs/build-spec.schema.json`) — dimensions with tolerances,
holes/bosses, fasteners, material/process, print orientation, min wall,
declared load case — written BEFORE any detailed geometry work starts.
Missing dimensions, payload, or duty cycle means the verdict is
`request-input`; do not guess and keep building.

### 2. Success is decided by the sentinel line, never by exit code or prose
Every pass ends with a numeric postcondition emitted as the LAST stdout line:
`AGENT_OK {json}` or `AGENT_FAIL {json}`. Read that line to decide outcome.
Blender's process exit code is unreliable in both directions. The transport
message "Code executed successfully" (or similar) is not evidence of
correctness — it only means the call returned, not that the mutation
succeeded. If a call times out after a mutation was already sent, treat the
outcome as unknown and re-read scene state before sending anything else.

### 3. Run payloads through the sanctioned entry points only
Two execution modes, both starting from `<ROOT>`:

- **Interactive (MCP, addon Connected in the Blender GUI):**
  ```python
  import sys; sys.path.insert(0, "<ROOT>/scripts")
  import agent_runtime as rt
  rt.run_file("<abs>/pass.py")
  ```
  Call this through the MCP `execute_blender_code` tool. Each call gets a
  fresh Python namespace — imports and `agent_runtime` must be re-established
  inside the payload every time; nothing persists between calls.

- **Headless (batch/fault-test/gate, no GUI):**
  ```bash
  bash scripts/headless-run.sh pass.py
  ```
  Runs with `--factory-startup`, sentinel-driven exit code.

Never invent a third execution path (raw `blender --python`, ad hoc sockets,
etc.) without checking `AGENTS.md` §4 first.

### 4. Verify ladder: numbers before pixels
Cheap to expensive, in this order — stop climbing once a step answers the
question:
1. Numeric asserts: `assert_exists`, `tri_count`, `world_bbox`,
   `has_material`, fcurve keys, plus the `AGENT_OK` postconditions.
2. `framing()` + `preview_render(engine="EEVEE"|"CYCLES")` + `frame_stats()`
   (fast, restores scene state).
3. Viewport screenshot — only for what a number cannot answer (composition,
   "does it look right") — and only after writing down the expectation and
   what would falsify it, BEFORE looking.
4. Low-sample Cycles preview.
5. Comparison sheet, when a reference image exists.
6. Turntable.
7. Production part: `scripts/production-gate.py` (rule 6) is mandatory and
   sits above this ladder, not instead of it.

Never report a build "done" without having run the last-step visual
verification for that build.

### 5. Verdicts and the fail-escalation counter
After every verify step, pick exactly one verdict:
- `continue` — met the bar, proceed to the next step.
- `refine-spec` — the root cause is the spec/plan, not the code; fix the
  spec first.
- `refine-code` — the spec is correct, the code diverges; fix the delta.
- `request-input` — a decision only the user can make.
- `stop` — change direction entirely; tell the user why.

Two failures at the same step on the same approach: change the approach's
CLASS (e.g. stop retrying `bpy.ops` and switch to the data API), do not repeat
the same fix with small tweaks. Three failures total on the same problem:
verdict is `request-input` — stop iterating alone.

### 6. Production gate before delivery
Any part destined for printing/manufacturing must pass:
```bash
python3 scripts/production-gate.py --scene <blend> --spec <spec.json> --report <out.json>
```
Exit code must be 0 before the part is considered deliverable. Attach the
report JSON to the build record. The gate proves topology/dimensions/
standards compliance — it does NOT prove load capacity, real-world fit, or
thermal duty; do not claim those from a passing gate.

### 7. Native Asset Construction Policy (hard rule, no exceptions from this file)
Production geometry and materials come only from Blender plus this
repository's own skills, knowledge, and scripts. Do not call, invoke, or
enable any tool that fetches, generates, or downloads vendor assets,
including but not limited to: PolyHaven search/download tools, Sketchfab
search/download tools, Hyper3D (Rodin) generation tools, Hunyuan3D generation
tools, or `set_texture` when it pulls a remote texture. An already-local
artifact may be used only when the user explicitly selects it, and only as a
frozen scaffold that gets copied into a self-contained rebuild, stripped of
vendor materials, repaired, and provenance-tagged — never as a live
dependency fetched again. Full policy: `.project-agent.md` and `AGENTS.md`.

### 8. One writer per GUI; never bridge headless to a live GUI
The Blender GUI (interactive/MCP mode) has exactly one writer at a time. Do
not run a headless process against the same `.blend` file that the GUI has
open, and do not have a headless script try to contact the MCP
socket/addon — headless and interactive are separate, non-overlapping
execution modes (rule 3). If an MCP tool call fails with a connection error,
report it to the user and ask them to open the addon; do not retry blindly
and do not fall back to headless on the same live file.

## Usable MCP tools (interactive mode)

Only these MCP `blender` tools are in scope for normal work:
- `execute_blender_code` — run a payload per rule 3.
- `get_object_info` — read one object's data.
- `get_viewport_screenshot` — step 3 of the verify ladder.
- `get_scene_info` — capped at the first 10 objects; for a full object list,
  query via `execute_blender_code` + bpy instead.

All other `blender` MCP tools (PolyHaven, Sketchfab, Hyper3D/Rodin, Hunyuan3D,
`set_texture` against a remote source) are forbidden by rule 7, regardless of
whether they appear in the tool list.

## If something here conflicts with AGENTS.md or .project-agent.md

Those two files win. This file is a portable restatement for a runtime that
may not load `AGENTS.md` automatically — treat any gap as a reason to go read
the canonical files, not as license to improvise.
