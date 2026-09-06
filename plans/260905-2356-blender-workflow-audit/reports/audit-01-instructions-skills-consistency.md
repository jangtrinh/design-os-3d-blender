# Audit 01 — Instruction & skill layer consistency

Read-only audit, 2026-09-06. Scope: agent-facing instruction layer (`CLAUDE.md`, `AGENTS.md`,
`.project-agent.md`, 3 project skills + refs, `docs/*.md`, `knowledge/INDEX.md`,
`00-foundations/agent-workflow-loop.md`). No file changed except this report.

## Verdict

The reference layer (`.agents/skills/**`, `docs/**`) is accurate and honest about what is not enforced; the **entry layer (`CLAUDE.md`/`AGENTS.md`) is the stale one** — the only file an agent is guaranteed to read, contradicting downstream layers on 8 counts incl. two dead skill names inside the MANDATORY loop.
Structure is sound: 110/110 relative links resolve (tested), `.claude/` mirrors `.agents/` byte-for-byte; the damage is semantic, not structural.
Mandatory session-start load measured at **103,258 B ≈ 25,814 tok**, of which **≥12,684 B ≈ 3,171 tok (12%) is narrative/one-off with no enforced rule attached**.

## Top findings (ranked)

### 1. CRITICAL — two dead skill names inside the mandatory loop, contradicted by `.project-agent.md`
- `CLAUDE.md:17` / `AGENTS.md:17`: "**Code:** Sinh bpy theo skill `blender-bpy-core`" — step 2 of the
  loop marked "MANDATORY cho mọi task dựng cảnh".
- `CLAUDE.md:82` / `AGENTS.md:82`: "tra bảng trong `blender-materials-shading`".
- `.project-agent.md:18`: "không gọi skill cũ `blender-bpy-core` đã không còn trong catalog."
- FACT: `.agents/skills/` contains only `blender-agent-core`, `blender-image-to-3d`,
  `blender-knowledge-workbench`, `img2threejs`. Neither dead name exists anywhere as a skill.
- Already recorded independently at `plans/blender-workflow-retro/reports/architect.md:38` and never
  fixed. `CLAUDE.md:3` tells the agent to read `.project-agent.md` first, so the agent reads the
  correction *before* the error — but the error sits in the numbered loop it is told to execute.

### 2. CRITICAL — `headless-run.sh` recommended with no failure caveat in the entry file
- `CLAUDE.md:74` / `AGENTS.md:74`: "`scripts/headless-run.sh <script.py>` — chạy bpy script headless."
  No warning.
- FACT `scripts/headless-run.sh:11,13` — invokes `blender -b --python "$SCRIPT"`, **no
  `--python-exit-code`**. `set -euo pipefail` (line 4) does not help: Blender itself exits 0.
- Recorded probe evidence `plans/blender-workflow-retro/reports/runtime-contract-probes.json`:
  `{"probe":"default-python-exit","returncode":0,"traceback_present":true}` vs
  `{"probe":"explicit-python-exit","returncode":23,...}`.
- Every other layer warns: `blender-agent-core/SKILL.md:61` ("hiện thiếu explicit Python-error exit;
  chưa coi shell exit 0 là pass"), `recipes.md:32`, `docs/system-architecture.md:21`,
  `docs/blender-workflow-improvement-backlog.md:5-13` (E1, priority first).
- Impact: an agent that only reads the mandatory entry file will treat exit 0 as a passing headless
  build. This is the single highest-cost defect in the layer.

### 3. HIGH — `.project-agent.md` binding rule 2 inverts the verify ladder
- `.project-agent.md:19` (Binding Rules, i.e. highest authority): "**Mọi thao tác dựng cảnh phải kết
  thúc bằng verify**: `get_viewport_screenshot` … hoặc turntable render".
- Contradicted by `knowledge/00-foundations/agent-workflow-loop.md:48`: "if a question can be answered
  by a number, never spend a screenshot on it"; by `blender-agent-core/SKILL.md:45` ("số trả lời được
  thì cấm tốn screenshot") and `CLAUDE.md:20` (same rule).
- A binding rule mandating a screenshot per scene operation is the most expensive possible reading and
  it outranks the ladder by placement. The other four statements of this rule agree with each other;
  only the binding one is inverted.

### 4. HIGH — `stop` / `dừng` carries three different actions across the mandatory files
- `CLAUDE.md:19`: "2 lần fail cùng một lỗi → **dừng**, đổi hướng tiếp cận" = abandon this approach.
- `CLAUDE.md:21`: verdict "`stop` (đổi hướng)" = change direction, a verdict value.
- `blender-agent-core/SKILL.md:40`: "2 fail → đổi CLASS approach; 3 fail → **dừng**, báo user" =
  escalate to human.
- Source of truth `agent-workflow-loop.md:73-74` (R5): "Two failed attempts ⇒ change **class** of
  approach, not parameters. **Three ⇒ report to the human**"; checklist L279-280 restates 2/3.
- `CLAUDE.md:19` collapses the 2-strike and 3-strike rules into one and **drops the escalate-to-user
  step entirely**. `blender-image-to-3d/SKILL.md:63` states only the 2-strike half.

### 5. HIGH — render-engine facts in `CLAUDE.md` are contradicted by three other layers
- `CLAUDE.md:76` / `AGENTS.md:76`: "Engine: **Cycles + Metal** (EEVEE không headless được trên
  macOS). Preview: samples thấp (32) + denoise; final: 128+."
- Metal: `.project-agent.md:11` "chọn CPU/Metal bằng profile đã kiểm tra cho scene, không mặc định GPU
  nhanh hơn"; `docs/blender-ai-workflow.md:57` "Không mặc định Metal luôn nhanh hơn, 128 samples luôn
  cần hoặc 6 samples luôn đủ"; `docs/system-architecture.md:33` "neither Metal nor any fixed sample
  count is universal acceptance". 3 files against 1.
- Samples: `docs/system-architecture.md:35` — the actual delivered 720-frame film used **six** Cycles
  samples, not 128. CLAUDE's "final: 128+" is contradicted by the project's own shipped artifact.
- EEVEE: KB `knowledge/30-lighting-render/render-engines.md:70` states rule R2 as "**Do not assume**
  EEVEE can render headlessly on the machine you are on" and its cited failures are headless Windows
  and GPU-less Linux containers — not macOS. Line 214 of the same file shows
  `blender -b scene.blend --gpu-backend vulkan -E BLENDER_EEVEE …` as a working pattern.
  `.project-agent.md:11` phrases it correctly ("không dựa vào EEVEE cho đường batch macOS hiện tại").
  CLAUDE turns a "do not assume" into a categorical "cannot" — the exact inversion the KB warns about.

### 6. MEDIUM — `knowledge/INDEX.md` says "3 files" then lists 4; every other source says 3
- `knowledge/INDEX.md:20`: "### Always load first (**3 files**, non-negotiable)" followed by a 4-row
  table, L24-27: version-matrix, bpy-scripting-core, **python-agent-boilerplates**, agent-workflow-loop.
- Disproof run this session (read-only): `python3 scripts/blender-knowledge.py route
  native-product-visualization` returns exactly **three** `required` foundations — version-matrix,
  bpy-scripting-core, agent-workflow-loop. `python-agent-boilerplates` is not among them.
- `CLAUDE.md:60`, `AGENTS.md:60`, `blender-agent-core/SKILL.md:27-30`,
  `docs/blender-knowledge-workflows.md:27` all say 3. INDEX.md is the sole outlier, and it costs
  **9,173 B ≈ 2,293 tok** of extra mandatory reading if an agent trusts the table over the heading.

### 7. MEDIUM — stale counts and terminology in always-read files
- `docs/system-architecture.md:41`: "**Five** executable follow-ups" — the backlog has **E1…E7**
  (`docs/blender-workflow-improvement-backlog.md:5,15,23,31,41,49,59`). `hard-rules.md:22` and
  `docs/blender-knowledge-workflows.md:47` both correctly say "E1–E7".
- `CLAUDE.md:59` / `AGENTS.md:59`: "route **A/B/C/D**" — `blender-image-to-3d/SKILL.md` has no A/B/C/D
  anywhere; Phase 0 (L23-28) is an unlabeled 4-row evidence→mode table. An agent looking for "route B"
  finds nothing.
- `CLAUDE.md:18` "socket names **4.x**?" and `CLAUDE.md:82` "tên socket **3.x** trên Blender **4.x**" —
  local and KB target are both 5.2.0 (`.project-agent.md:9`, `INDEX.md:5`, `system-architecture.md:23`
  build `fbe6228777e7`). The Critic step asks the agent to check a version pair that no longer applies.
- `CLAUDE.md:7` / `AGENTS.md:7` hard-code "MCP server `blender` (**22 tools**)" while
  `docs/system-architecture.md:23` says "**do not hard-code a stale MCP tool count**". The count is
  currently *correct* (22 `mcp__blender__*` tools in this session's registry — FACT), but see #8.
- `scripts/agent-verify-lib.py:122` comment: "KB targets 5.x; local may be 4.x" — stale, and this file
  is `exec`'d "trong mọi bpy session" per `CLAUDE.md:61`.

*(overflow findings in Appendix A)*

## Redundancy table

| Rule | Locations | Agree? |
|---|---|---|
| Mandatory foundation count | `CLAUDE.md:60` (3) · `AGENTS.md:60` (3) · `agent-core/SKILL.md:27-30` (3) · `INDEX.md:20` heading (3) vs `INDEX.md:24-27` table (4) · `blender-knowledge-workflows.md:27` (3) · CLI `route` output (3) | **NO** — INDEX self-contradicts |
| Fail-count / escalation | `CLAUDE.md:19` (2→stop) · `agent-core/SKILL.md:40` (2→class, 3→user) · `agent-workflow-loop.md:73,279-280` (2→class, 3→human) · `image-to-3d/SKILL.md:63` (2→approach) | **NO** — CLAUDE drops the 3-strike escalation |
| When a screenshot is allowed | `CLAUDE.md:20` (numbers first) · `.project-agent.md:19` (every scene op ends with screenshot) · `agent-core/SKILL.md:45-55` (6-rung ladder) · `agent-workflow-loop.md:48` (never spend a screenshot on a number) · `image-to-3d/SKILL.md:57` | **NO** — binding rule 2 inverts it |
| `headless-run.sh` trustworthiness | `CLAUDE.md:74`/`AGENTS.md:74` (silent) · `agent-core/SKILL.md:61` · `recipes.md:32` · `system-architecture.md:21` · backlog E1 | **NO** — entry file omits the caveat |
| Metal / sample defaults | `CLAUDE.md:76` (Metal, 32/128) · `.project-agent.md:11` · `blender-ai-workflow.md:57` · `system-architecture.md:33,35` (shipped film = 6 samples) | **NO** — CLAUDE only |
| EEVEE headless on macOS | `CLAUDE.md:76` (categorical "cannot") · `.project-agent.md:11` ("don't rely on") · KB `render-engines.md:70,214` ("do not assume"; shows a working `-b -E BLENDER_EEVEE`) | **NO** |
| Router set | `CLAUDE.md:55-61` (2 routers) · `.project-agent.md:26` (3) · `system-architecture.md:9` (3) · `blender-knowledge-workflows.md:43` (3) | **NO** — CLAUDE omits `blender-knowledge-workbench` entirely |
| Backlog item count | `system-architecture.md:41` ("Five") · backlog E1–E7 · `hard-rules.md:22` · `blender-knowledge-workflows.md:47` | **NO** |
| Preview render defaults | `agent-verify-lib.py:83` (256px/16smp) · `agent-core/SKILL.md:41` ("256px/16smp là ví dụ") · `agent-workflow-loop.md:79-80` ("a 128px 16-sample preview") | **NO** (minor; code says 256) |
| bpy chunk size ≤ ~80 lines | `CLAUDE.md:17` · `AGENTS.md:17` · `agent-core/SKILL.md:36` · `agent-workflow-loop.md:52-55` (R1, no number) | YES |
| Verdict set (continue/refine-spec/refine-code/request-input/stop) | `CLAUDE.md:21` · `image-to-3d/SKILL.md:63` · `review-rubric.md:50-53` · `blender-ai-workflow.md:29` | YES |
| Native-asset / no-vendor policy | `CLAUDE.md:25-31` · `AGENTS.md:25-31` (verbatim) · `.project-agent.md:12-15` · `image-to-3d/SKILL.md:8,30,74` · `system-architecture.md:27-29` | YES (but 5× restated) |
| QRemeshify gate | `CLAUDE.md:33-53` · `AGENTS.md:33-53` (verbatim) · `.project-agent.md:15` · `image-to-3d/SKILL.md:49-53` | YES (4× restated, 3,912 B) |
| `.agents/` is source, `.claude/` is mirror | `.project-agent.md:26` · `agent-core/SKILL.md:12` · `system-architecture.md:13` · `blender-knowledge-workflows.md:59` | YES — and **verified**: `diff -rq` on all 3 project skills returns identical |
| Whole entry file | `CLAUDE.md` vs `AGENTS.md` — **81 of 83 lines byte-identical** (`diff`: only L1 title, L6 Claude/Codex, plus an empty trailing section) | Duplicated by hand; both carry the same two dead skill names → drift already realized |

## Session-start load table

Measured with `os.path.getsize`; tokens = bytes/4.

| Item | Bytes | ~Tokens | Operational? |
|---|---:|---:|---|
| `CLAUDE.md` | 7,318 | 1,829 | Mixed — L33-53 (**1,389 B**) is an FPV-drone-specific QRemeshify bash block |
| `.project-agent.md` | 3,440 | 860 | Operational |
| `blender-agent-core/SKILL.md` | 6,703 | 1,675 | Operational |
| `references/hard-rules.md` | 4,674 | 1,168 | Operational, but the *Source* column = **953 B** of raw timestamps (`08:10:09`, `09:34:32`…) that change no action |
| `references/recipes.md` | 9,001 | 2,250 | Operational; **1,375 B** is arm-specific example paragraphs (L44, L60, L72) |
| 4× `00-foundations/` | 51,187 | 12,796 | Operational (`python-agent-boilerplates` = 9,173 B is disputed, see finding #6) |
| `knowledge/INDEX.md` | 20,926 | 5,231 | **Mostly catalogue** — L172-194 candidate-skill list (1,853 B, self-declared "not installed skills" at L174), L197-209 research list (2,863 B), L213-233 boilerplate list (4,251 B, enumerates 17 of 30 modules) |
| `docs/blender-ai-workflow.md` | 9,182 | 2,295 | Operational |
| **TOTAL (3 foundations)** | **103,258** | **25,814** | |
| TOTAL (INDEX's 4 foundations) | 112,431 | 28,107 | |

Cuttable without losing an enforced rule (measured): CLAUDE QRemeshify bash 1,389 + INDEX
L172-194 1,853 + INDEX L197-209 2,863 + INDEX L213-233 4,251 + hard-rules Source column 953 +
recipes arm examples 1,375 = **12,684 B ≈ 3,171 tok = 12.3% of the mandatory load**. None of these
six blocks is checked by any script or test.

Larger lever (INFERENCE, not verified by measurement of agent behaviour): `knowledge/INDEX.md`
(5,231 tok) need not be a session-start read at all — `agent-core/SKILL.md:32` already routes to
`blender-knowledge.py route <workflow-id>`, which returns the exact required file list with hashes,
and calls INDEX a *direct lookup* fallback. Demoting INDEX to on-demand would cut **~20%** of the
mandatory load and remove the 3-vs-4 foundations contradiction and the candidate-skill hallucination
bait in one move.

## Enforceability table

FACT: there is **no `.claude/settings.json`, no hooks directory, no CI** in this repo
(`find .claude .codex -maxdepth 2 -type f` → only `.codex/config.toml`). Enforcement is therefore
limited to scripts a human/agent chooses to run.

| Rule | Class | Evidence |
|---|---|---|
| Knowledge catalog freshness + `.claude/` mirror sync | **ENFORCED-BY-CODE** | `scripts/blender-knowledge.py check` run this session → `{"status":"current","records":235,…}` + `tests/knowledge/test_catalog.py` |
| QRemeshify hash-pin / quarantine / 1k–100k tri budget | **ENFORCED-BY-CODE** | `scripts/run-qremeshify.py`, `scripts/prepare-qremeshify-input.py`, `tests/blender/qremeshify-candidate-test.py` |
| Drone / Rodin geometry + presentation acceptance | **ENFORCED-BY-CODE** (artifact-specific only) | `tests/blender/native-drone-*-test.py`, `rodin-optimized-*-test.py` |
| Publish-only-reviewed-candidate (`review_sha256`) | ENFORCED-BY-CODE (INFERENCE — not executed here) | `knowledge-to-workflow.md:30-44`, `scripts/knowledge-pipeline.py` |
| Numeric assert per step (R2) | MANUAL | `agent-verify-lib.py` is a library; nothing requires calling it |
| Screenshot-with-intent (R4) | MANUAL | prose only |
| 2-fail / 3-fail escalation (R5) | MANUAL | prose only |
| Checkpoint before destructive op (R7) | MANUAL | `agent-verify-lib.py:114 checkpoint()` exists, unenforced |
| "Verify visual before done" | MANUAL | `CLAUDE.md:20`, `.project-agent.md:19` |
| One writer per GUI/scene | MANUAL | `hard-rules.md:10` "lock implementation deferred"; `system-architecture.md:19` "manual, not an enforced lock" |

**Top 5 MANUAL rules that caused real, documented trouble** (per
`docs/blender-workflow-improvement-backlog.md`):

1. **E1 — transport success ≠ execution success** (`hard-rules.md:8`, backlog L5-13). Probe: exit 0
   with traceback present. Highest priority in the backlog.
2. **E2 — preview/check helpers must restore state** (`hard-rules.md:16`, backlog L15-21). Probe:
   samples 99→7, resolution 960×720→64×64, `"restored": false`. `agent-core/SKILL.md:51` now bans
   calling `preview_render()` on a live scene as a workaround.
3. **E3 — gate results must be bound to their inputs** (`hard-rules.md:14`, backlog L23-29). Path
   checker printed `AGENT_OK` while report status was `REQUIRES_REFINEMENT`.
4. **E6 — assembly waiting/transit states validated before full render** (`assembly-sequences.md:46`,
   backlog L49-57). A5 waiting fork intersected the receiver at source frame 588 while final
   transforms and framing both passed.
5. **E5 — engineering blockers survive delivery** (`hard-rules.md:15`, backlog L41-47). Arm 250 g
   multi-minute requirement still manufacture-BLOCKED despite media PASS.

## Router trace — "model a coffee mug from a photo and render a turntable"

Traced literally, top-down, as a fresh agent would.

| Hop | Where | Result |
|---|---|---|
| 0 | `CLAUDE.md` (auto-loaded), L3 → read `.project-agent.md` | ok |
| 1 | `CLAUDE.md:16-21` mandatory loop | **DEAD END** at L17: "Sinh bpy theo skill `blender-bpy-core`" — skill does not exist |
| 2 | `CLAUDE.md:59` "Có ảnh reference → `blender-image-to-3d` … route A/B/C/D" | Skill found; **DEAD END** on terminology — no A/B/C/D exists in the skill |
| 3 | `blender-image-to-3d/SKILL.md:8` "Load `blender-agent-core` first" | back-edge; 3 hops spent, no turntable answer |
| 4 | `blender-agent-core/SKILL.md:14-21` routing table | **No turntable row.** Nearest: "Render batch, video hoặc export → `recipes.md#render-delivery`" |
| 5 | `recipes.md:62-72` render delivery | Does **not** mention `scripts/turntable-preview.py`; routes to `30-lighting-render/render-engines.md` |

The mug half succeeds in 2 hops (`image-to-3d` Phase 0 row 1 → parametric/mirrored SubD; fidelity
tier "simple = 3 min details" at `review-rubric.md:14`). The **turntable half is in no routing
table** — `scripts/turntable-preview.py` is named only at `CLAUDE.md:75` (Headless Rendering section,
*below* the loop) and `agent-core/SKILL.md:55` (verify-ladder rung 6). Both reachable by having read
the whole file, neither by following the router.

Irony worth noting: the *knowledge* router beats the *skill* router here —
`knowledge/INDEX.md:50` resolves "turntables" to `60-pipeline/product-viz-and-shots.md` in **one**
hop, and `blender-knowledge.py list` offers `native-product-visualization` in one command.

**Answer: no, not in ≤3 clean hops.** ~5 hops with 2 dead names en route.

## Language mix

The mix is not itself the defect; the defect is that it is **per-file, not per-audience**, so one
skill's SKILL.md and its own reference speak different languages.

1. `blender-image-to-3d/SKILL.md` is **English**; its only reference `references/review-rubric.md` is
   **Vietnamese** (L1-59). An agent quoting a rubric threshold back into an English report has to
   translate mid-task.
2. `blender-agent-core/SKILL.md` is **Vietnamese**; its `hard-rules.md` is **English**; `recipes.md`
   is **split inside one file** — L7-13 Vietnamese, L15-32 and all later sections English.
3. `blender-knowledge.py list` returns **English workflow IDs with Vietnamese descriptions**
   (`"native-hard-surface": "Dựng từ ảnh, silhouette…"`), while
   `blender-knowledge-workflows.md:13` warns that search is lexical and accent-insensitive and that
   **"ID workflow và các thuật ngữ kỹ thuật tiếng Anh giúp chọn chính xác hơn"** — i.e. the routing
   surface is in the language the tool says works worse for matching.
4. **Term with two meanings — `dừng`/`stop`** (see finding #4): `CLAUDE.md:19` = abandon approach;
   `CLAUDE.md:21` = a verdict value meaning "đổi hướng"; `agent-core/SKILL.md:40` = escalate to the
   human. Three actions, one word, two files.
5. Secondary: `pass` = a build stage (`CLAUDE.md:69` "sau MỖI pass") and = a gate result
   (`hard-rules.md:15` "media gate passes", `system-architecture.md:37` "media PASS").
6. Formatting damage from a prior edit pass has glued numbers to words in operational prose:
   `hard-rules.md:3` "UTC on2026-09-05", `:18` "screenshot2026-09-05", `:20` "and89-frame";
   `assembly-sequences.md:30` "universal120mm", `:44` "used35mm", "target,120mm";
   `blender-ai-workflow.md:75` "số120mm,0.20mm³". Low severity, but these are exactly the constants
   the same sentences warn against generalising.

## Not verified

- **No Blender process was started.** The `headless-run.sh` exit-code claim rests on
  `plans/blender-workflow-retro/reports/runtime-contract-probes.json` (repo artifact) plus static
  reading of `scripts/headless-run.sh` — I did not reproduce it.
- **Whether EEVEE can in fact render headless on this Mac.** I verified only that `CLAUDE.md:76`
  states a certainty the KB does not support. The KB's own position is "do not assume".
- Foundation files `blender-version-matrix.md`, `bpy-scripting-core.md`,
  `python-agent-boilerplates.md` were grepped, not read in full. `agent-workflow-loop.md` §1, §4-6
  were skimmed; §2, §3 (R1-R8), §7, §8 read in full.
- `knowledge/generated-workflows.md` — headings only (79 headings, 9 workflows), per instruction.
- `scripts/knowledge-pipeline.py prepare/publish` enforcement — read-only constraint; not executed.
- `img2threejs` excluded per instruction. Note it produces a standing warning in the mandatory gate:
  `blender-knowledge.py check` → `"Imported mirror drift (preserved): .agents/skills/img2threejs/SKILL.md"`.
- MCP tool count (22) taken from this session's tool registry, not from a live connection to the addon.
  The Blender GUI was not touched.
- Link testing: 110 relative markdown links across the 17 audited files were resolved
  programmatically, including `#anchor` targets against real headings. 17 initial "failures" were
  `file:///Users/jang/…` absolute URLs in `INDEX.md:216-232`; **all 17 targets were then confirmed to
  exist on disk**. Net broken links: **0**.

## Appendix A — overflow findings

| # | Sev | Finding | Evidence |
|---|---|---|---|
| A1 | MED | `CLAUDE.md` never mentions `blender-knowledge-workbench` or `generated-workflows.md`, though `agent-core/SKILL.md:32` makes the workbench the mandatory next step after the 3 foundations | `CLAUDE.md:55-61` (2-router table) vs `.project-agent.md:26`, `system-architecture.md:9` (3 routers) |
| A2 | MED | `CLAUDE.md:61` mandates `exec`ing `agent-verify-lib.py` "trong mọi bpy session" but never says one of its functions is banned on a live scene | `agent-core/SKILL.md:51` "Không gọi helper `preview_render()` trong scene đang làm trước khi xử lý hạn chế E2" |
| A3 | MED | The Critic step asks "hardcoded paths?" while 3 of the 4 mandated execution scripts hardcode `/Users/jang/…` | `CLAUDE.md:18` vs `agent-verify-lib.py:114`, `turntable-preview.py:21`, `make-comparison-sheet.sh:9` |
| A4 | LOW | 17 machine-local `file:///Users/jang/…` URLs in an otherwise relative-link document; breaks on any other machine and is the only place in the repo using that form | `knowledge/INDEX.md:216-232` |
| A5 | LOW | INDEX claims "30 modules passing 100% headless" then enumerates 17; 30 modules + 1 test runner do exist on disk | `knowledge/INDEX.md:215` vs `find scripts/boilerplates -type f` (31 files) |
| A6 | LOW | `INDEX.md:181-193` lists 13 plausible-looking skill names (`blender-modeling`, `blender-render`, …). L174 disclaims them as "not installed skills", but this table is the likely origin of the dead `blender-bpy-core`/`blender-materials-shading` habit in `CLAUDE.md` | `INDEX.md:174,181-193` |
| A7 | LOW | `AGENTS.md:85` is an empty trailing section header, "## Imported Claude Cowork project instructions", with no body | `AGENTS.md:84-85` |

## Unresolved questions

1. Are `CLAUDE.md` and `AGENTS.md` meant to stay hand-duplicated (81/83 identical lines), or should
   one become a 3-line pointer to the other? Every finding above is currently a double fix.
2. Is `.project-agent.md:19` (screenshot after every scene op) an intentional stricter policy that
   should override the verify ladder, or stale text predating the ladder? This decides whether the
   ladder or the binding rule gets edited.
3. Should `python-agent-boilerplates.md` be a 4th mandatory foundation? `INDEX.md`'s table says yes;
   the catalog, the CLI and four other documents say no. Costs 2,293 tok per session either way.
4. Is the "22 tools" figure worth stating at all, given ~17 of the 22 `mcp__blender__*` tools are
   PolyHaven/Sketchfab/Hyper3D/Hunyuan asset-generation and download tools that the Native Asset
   Construction Policy forbids? The entry file advertises a toolbelt of which roughly
   `execute_blender_code`, `get_scene_info`, `get_object_info`, `get_viewport_screenshot` are usable.
   Stating that explicitly would prevent an agent reaching for a banned tool. (FACT: count and names
   from this session's registry; the usable/banned split is my reading of `CLAUDE.md:25-31` —
   not stated anywhere in the repo.)
5. Nobody owns "which file is authoritative when two mandatory files disagree". `.project-agent.md`
   is read first and calls itself binding; `CLAUDE.md` calls its loop MANDATORY; `hard-rules.md` calls
   itself operational rules. No precedence sentence exists in any of them.
