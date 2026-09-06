# Blender workflow implementation backlog

2026-09-05 (status lines added 2026-09-06). Findings come from the [retro](../plans/reports/retro-260905-1946-blender-workflow.md), independent debate and fresh-process probes. **These fixes are not implemented by the retrospective.** Shared code and delivered robot artifacts were preserved. Project has no Git repository/remote available for issue filing; these local executor-ready items are the current record.

## E1 — Propagate execution failure and preserve evidence

**Status 2026-09-06: IMPLEMENTED** — sentinel contract (`AGENT_OK`/`AGENT_FAIL` last line, exit 0/1/2/3) in `scripts/agent_runtime.py`; `scripts/headless-run.sh` runs payloads through `scripts/agent-run-headless.py` with `--factory-startup --disable-autoexec --python-exit-code 3`, exit 2 on missing script, refuses success when sentinel and Blender exit disagree; `scripts/blender-socket-client.py` fixed (EOF, status, no truncation). Tests: `tests/execution/` (45 pass). Evidence: `plans/260905-2356-blender-workflow-audit/reports/impl-w1-execution-truth.md`.

Priority (historical): first. Owner: next execution-helper implementation task. Scope: `scripts/headless-run.sh`, `scripts/blender-socket-client.py`, new isolated transport/CLI tests. No addon changes initially.

Evidence: [runtime probes](../plans/blender-workflow-retro/reports/runtime-contract-probes.json) reproduce an unhandled Python exception returning 0 without `--python-exit-code`, and 23 with it. Socket client statically has undefined response on early EOF, no failure-status check and 4000-character JSON truncation. Local addon execution can partially mutate before raising.

Acceptance: intentional failure returns nonzero; complete structured response is saved; malformed/empty/error/partial UTF-8 fixtures fail clearly; timeout after send becomes unknown outcome with zero automatic mutation retries. Success requires declared postconditions. Bound resource use without pretending unrestricted Python is a sandbox. Keep existing command-line compatibility or document any intentional change.

Reproduce current CLI finding: `python3 plans/blender-workflow-retro/probe-runtime-contracts.py`. This audit script currently expects the known defect; create separate desired-behavior regression tests before fixing helpers, preserve this historical report.

## E2 — Make preview/check helpers preserve state

**Status 2026-09-06: IMPLEMENTED** — `scripts/agent-verify-lib.py` is a facade over `scripts/agent_verify/`; `preview_render` restores all 10 touched settings in `finally` (success and injected failure), `verify_export` re-imports in a separate `--factory-startup -b` process, `scaffold` is report-first/non-destructive; regression tests `tests/execution/test_verify_lib.py` (7 pass). Evidence: `plans/260905-2356-blender-workflow-audit/reports/impl-w2-verify-lib.md`.

Priority (historical): second. Owner: next verification-helper task. Scope: `scripts/agent-verify-lib.py` and its duplicated KB example plus focused Blender tests.

Evidence: preview error leaves samples 99→7, resolution 960×720→64×64, and output path changed in [probe result](../plans/blender-workflow-retro/reports/runtime-contract-probes.json). Success path also lacks samples restoration by source inspection. `verify_export` resets the scene.

Acceptance: success and injected failure both restore all touched settings using `finally`; composition previews preserve intended aspect or explicitly state their changed purpose; export round-trip runs in isolated state. Relevant existing assertions remain, with negative controls. Verify one real caller after change; do not migrate valid task-specific gates solely to raise import counts.

## E3 — Bind gate results to their inputs

**Status 2026-09-06: PARTIAL** — for printed parts, `scripts/production-gate.py` writes reports bound to `scene_sha256`+`spec_sha256`, with `failed[]`, `coverage.unchecked`, `exclusions`, exit 1 on any failed requirement (`tests/production-gate/`, 20 pass). Task/flexibility checkers in `builds/` are unchanged. Evidence: `impl-w3-production-gate.md`.

Priority (historical): third. Owner: next evidence-contract task. Scope: task/flexibility checkers and a small common result validator; preserved build outputs must be copied to a candidate directory for tests.

Evidence: path checks print `AGENT_OK` even when report status is `REQUIRES_REFINEMENT`; video checker consumes boolean reports without checking their input identities. These are current static findings, not proof the delivered movie used stale reports.

Acceptance: collision/failure fixture returns failing status and nonzero exit while retaining its report; reports identify source/checker/config/frame range/exclusions; changing a source or config rejects stale acceptance. Decode/render/export evidence must refer to the artifact actually delivered. Preserve stronger task-local predicates and compare their prior cases before replacing them.

## E4 — Resume validated frame ranges

Priority: after E1/E3, when interrupted batch work recurs. Owner: render helper task. Scope: small manifest/resume utility around existing renderer; no daemon or automatic GPU tuning.

Evidence: three disjoint task logs covered frames 1–720 without overlap; raw frames permitted caption removal without rerender. Existing scripts take ranges but do not implement identity-bound resume.

Acceptance: complete matching PNGs are reused; truncated/missing images rerender; scene/settings mismatch requires a new output set; two explicitly assigned ranges cannot overwrite each other. Log process start/end and cold/steady frame timing. A presentation-only edit must not trigger source rendering. Stop conditions and process ownership are explicit.

Optional experiment: compare one known profile with one candidate on the same three frames, twice, changing one variable. Choose caps and a minimum practical gain before running; keep baseline if motion quality or reproducibility regresses. Thresholds in [Performance report](../plans/blender-workflow-retro/reports/performance.md) are proposed defaults, not universal rules or measured gains.

## E5 — Preserve engineering blockers at delivery

Priority: before any manufacturing claim. Owner: evidence/release task; physical tests require hardware owner or qualified mechanical reviewer. Scope: report aggregation and domain acceptance; actual wrist redesign is a separate arm workstream.

Evidence: the [print-assembly README](../builds/robot-arm-print-assembly/README.md) retains wrist torque margin, thin/trimmed sections, adapters, retention and tool access as unresolved. Later clearance work changed section volume; media success does not close those conditions.

Acceptance: negative case with media PASS, sampled-screen PASS, changed geometry and unresolved torque remains manufacture BLOCKED; baseline STL/load approval cannot attach to revised geometry. No statements of continuous collision freedom from sampled surfaces. No 250 g multi-minute claim until relevant load, thermal, retention, adapter and anchoring evidence exists.

## E6 — Validate assembly states before full render

Priority: before another multi-part assembly film. Owner: next assembly-validator implementation task. Scope: reusable manifest/state graph and read-only Blender checks; no automatic mechanical redesign.

Evidence: A5 waiting fork intersected the receiver at source588 although final transforms and framing passed. Remote staging fixed waiting overlap but direct transfer crossed actual servo cases. Lift/traverse/lower removed those case/body contacts in frame samples; simplified output mating stayed unresolved. See [assembly recipe](../.agents/skills/blender-agent-core/references/assembly-sequences.md) and [specific acceptance](../builds/robot-arm-original-refined/reports/clearance-acceptance.json).

Acceptance: failed waiting fixture, clear waiting/failed transit fixture, same-future-link exclusion fixture, full containment case, named terminal mate window and incorrect window must be distinguishable. Preserve evaluated world transforms/scene units, installed-state coverage and fail exit. Record omitted hardware and subframe/physical limits. Include endpoint camera envelope and a short reviewed temporal preview; full render is not the first visual test. Existing Arm tests are stronger evidence than a blanket adapter PASS but are not a common installed gate.

E4 update: A5 now has artifact-specific exact-state frame caching and a2931-frame prefix reuse proof for a camera-only ending edit. This does not close generalized resume: its state key does not hash every geometry/material/render dependency across arbitrary scenes. Require unchanged static-domain evidence as well as matching sampled state before adapting it.

## E7 — Qualify the new collision, connector and harness adapters

Priority: before their production reuse; not a blocker for annotated catalog publication. Owner: next adapter implementation task, one writer per module. Preserve original sources until that task explicitly owns a candidate/fix.

Evidence: [four smoke runs and twelve diagnostics](../plans/260905-2337-arm-session-retro/reports/new-knowledge-review/report.md); controller rerun [log](../plans/260905-2337-arm-session-retro/reports/controller-negative-checks.log). Ten cases expose limitations/defects; two are positive controls. Exit0 here means the diagnostic reproduced expectations, not the code was repaired.

| Scope | Required correction and acceptance |
|---|---|
| Collision/packing adapter | Honor evaluated geometry and scene scale; separate surface/solid predicates; reject invalid path step counts and oversize parts. Preserve rotated-cube positive control and add desired-behavior tests that fail on current source. |
| Connector/vent/saddle adapters | Parameters must alter intended dimensions/features; construct actual slots, bores/threads/vent interfaces or remove unsupported function claims. Use selected supplier drawing and section/fit checks. |
| Cable/chain adapter | Reject negative input or radius below selected cable requirement; implement actual mating joints/stops and per-pose curvature/length/strain checks. Disconnected closed primitives cannot pass as a working link. |

Rerun: `/Applications/Blender.app/Contents/MacOS/Blender --factory-startup --disable-autoexec -b --python-exit-code 23 -P plans/260905-2337-arm-session-retro/reports/new-knowledge-review/disposable/negative-checks.py`. This preserves current-defect evidence; do not merely flip its expectations and call the adapter fixed. Desired-behavior tests and an actual candidate visual check must accompany implementation; fit/IP/EMC/load/life require their own evidence.

## Deferred or rejected

No new Blender daemon, many-domain-skill split, forced generic-helper migration, universal CPU/Metal/sample preset, or global no-subtitle preference. Reconsider a new router only after a recorded retrieval-caused missed gate. Consider a cooperative lock only if multiple writers are actually required; manual single-writer ownership is not enforcement. No managed `es-*` skill was changed and no kit gap was established by this project-only evidence.
