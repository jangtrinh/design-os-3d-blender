---
name: native-agent-iteration
domain: pipeline
blender_target: "5.2 LTS"
audience: ai-agent-bpy
description: Local task lifecycle, target-bound independent criticism and source-parameter contracts adapted from three reviewed upstream agent repositories.
loads_with: [native-api-contracts, agent-workflow-loop]
tags: [orchestration, workflow, critique, provenance, parameters, recovery, native]
id: native-agent-iteration
title: "Native agent iteration: source, execution, judgment and revision"
when: [native-pass-pipeline, independent-visual-critic, bound-review-packet, parameter-contract, recovery-after-partial-success, stall-detection]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Native agent iteration: source, execution, judgment and revision

## Purpose

Define the local loop that turns a request into a verifiable native Blender build: a parameter contract, a declared dependency-ordered pass pipeline with durable execution records, and a revision-bound independent critic whose verdict drives refine-code / refine-spec / request-input / stop. Behaviour statements are tied to `scripts/native_pipeline/*` and `scripts/native_review/*`; upstream-agent comparisons are tied to the pinned research records.

## When to Use / When NOT

- ALLOWED: running `scripts/native-pipeline.py` for a bounded multi-step build, or preparing a `native-review.py` packet and assessment for a visual target.
- ALLOWED: recovering after a wrapper/postcondition failure when a valid saved model exists.
- NOT ALLOWED: surprising measurement or gate disagreement — use `geometry-diagnostic-workflow`; final media packaging — use `native-render-delivery`.
- NOT ALLOWED: physical or electrical closure — use `manufacturing-evidence-workflow`; an `executed` pipeline state or an accepted review is never manufacture or visual-fidelity approval (AGENTS.md).
- NOT ALLOWED: installing the upstream skills as competing policies; reuse the three existing skills (`blender-agent-core`, `blender-image-to-3d`, `blender-knowledge-workbench`).

## Core Knowledge Content

This workflow combines three distinct mechanisms: Meshy's task lifecycle, Dream-loop's <!-- ease:source S7 anchor="Meshy task lifecycle record; pinned commit b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610" --> <!-- ease:source S8 anchor="Dream-loop record" --> <!-- ease:source S9 anchor="Text-to-CAD record" -->
independent visual feedback, and Text-to-CAD's source/parameter/artifact discipline.
The detailed source analyses are in `research/upstream-agent-patterns/`. Reuse the
three existing skills; do not install the upstream skills as competing policies.

### 1. Convert a request into a verifiable native contract

Record purpose first. For print/both use the existing production spec before detail;
for a reference task, retain the image-to-3D fidelity contract. A parameter contract
adds explicit units, finite literals, allowed ranges, right-handed frames, datums,
semantic ports and separate visual/collision/physical role declarations. Those
declarations describe intent; they do not prove actual geometry or physics.

Keep dimensions and capture context outside hardcoded geometry. The constructor
reads the normalized parameter contract; records pin the actual Python source and
declared inputs. A source helper, parameter, reference or renderer-setting change
invalidates the corresponding evidence. There is no automatic discovery of arbitrary
Python imports, random state or external configuration; declare each dependency.

Do not translate a request for an editable mesh into a claim that the result is a
B-rep/STEP solid. Do not translate a URDF visual mesh into collision or inertial
qualification. Export, physical loads, slicing and printer operation have their own
contracts and authority. This integration adds no CAD kernel or hardware access.

### 2. Run a declared pass pipeline with durable evidence

Use `scripts/native-pipeline.py` to check and execute a bounded dependency-ordered <!-- ease:source S2 anchor="manifest fields: artifact_inputs, depends_on" -->
manifest. Each step names its existing project Python payload, declared input files,
dependencies, output names, required numerical postcondition fields and timeout.
The runner delegates to `headless-run.sh`; it does not generate code itself. <!-- ease:source S1 anchor="runner delegates execution to the headless runner" -->

Each attempt gets a distinct output directory and a record written before launch.
The payload receives `DESIGN_OS_OUTPUT_DIR` and `DESIGN_OS_INPUTS_JSON`. Its <!-- ease:source S1 anchor="env DESIGN_OS_OUTPUT_DIR and DESIGN_OS_INPUTS_JSON" -->
`project` map contains declared project files; its `artifacts` map contains only
explicit `artifact_inputs` entries such as `build:model.blend`, each mapped to an
absolute path. The producing step must be listed in `depends_on`.
Read these instead of guessing another step's filenames. Write outputs only in the
assigned directory. Source/manifest/runtime/input/output hashes bind successful work.

`executed` is an execution-and-artifact state. A downstream pass may inspect it, but <!-- ease:source S1 anchor="return "executed", common" -->
it is not visual or manufacturing approval. A timeout, interrupted attempt or missing
authoritative result remains unresolved. Resume only skips unchanged executed work <!-- ease:source S3 anchor="--resume: reuse matching executed attempts and run only never-attempted pending steps" -->
and starts untouched pending work. Inspect and reconcile failed/unknown work before
creating an explicitly new run; never erase evidence to bypass retry protection.

### 3. Prepare the visual target and critic packet

Create a target JSON with `version: 1`, an explicit `target_revision`, `purpose`, <!-- ease:source S4 anchor="version must be 1; purpose in render-only/print/both; max_rounds bounded to at most three" -->
`max_rounds` from 1 to 3, `views`, and `features`. Each view contains a pinned PNG
reference, expected proof dimensions and a capture-context object. Each feature
contains a stable ID, required view IDs, expected construction and a falsifier.
The actual renderer/controller must establish capture context; JSON cannot do that.

The numeric receipt names actual checks with pass/fail/unknown states and a finite
numeric `value` (an unknown check may instead provide an observation). It is bound
to the canonical hash of the candidate file-pin mapping. Do not manufacture a
passing receipt from target dimensions. The sample demonstrates constructing this
receipt from measured evaluated Blender geometry.

```bash
python3 scripts/native-review.py prepare \
  --target builds/example/target.json \
  --candidate scene=builds/example/candidate.blend \
  --proof hero=builds/example/proof.png \
  --numeric builds/example/numeric.json \
  --author builder --out builds/example/packet-r01.json
python3 scripts/native-review.py template \
  --packet builds/example/packet-r01.json \
  --out builds/example/critique-r01.json
```

These are example paths, not shipped artifacts. The template is deliberately
incomplete and cannot pass assessment until an actual reviewer supplies findings.
PNG completeness, dimensions and file hashes are checked; they do not prove likeness.

### 4. Give the critic an evidence-focused assignment

Provide the locked brief, feature expectations/falsifiers, target and candidate
images at the declared views, and optionally previous evidence. Ask for one result
per feature: pass, fail or unknown; concrete observation; the views examined; an
action for anything unresolved; and cause code/spec/missing-evidence. Prefer a fresh
independent reviewer. The builder must not write its own favorable critic verdict.

Avoid implementation explanations such as how hard a boolean was or how many
objects exist. Ask what is visible and what specific geometric, material, camera
or evidence change would fix the gap. Review all contracted views; a front image
cannot certify hidden rear construction. Keep uncertain details UNKNOWN.

```bash
python3 scripts/native-review.py assess \
  --packet builds/example/packet-r01.json \
  --critique builds/example/critique-r01.json \
  --out builds/example/assessment-r01.json
```

Exit 0 means the declared numeric and attributed visual findings passed for the <!-- ease:source S6 anchor="assess returns 1 when not accepted; main returns 2 on error" -->
bound revision. Exit 1 records unresolved findings. Exit 2 means malformed/stale
inputs or an invalid command. The command verifies bindings and completeness, not
the truth of a critic's vision or identity. A distinct reviewer name is a declared
separation, not authentication. Preserve this limitation in the delivery record.

### 5. Correct the right cause and detect stalls

| Result | Next action |
|---|---|
| Numerical check fails | Correct the measured issue before claiming completion; visual praise cannot override it. |
| A visual feature fails with a clear contract | `refine-code`; change the named geometry, placement, material or capture behavior. |
| The contract is contradicted | `refine-spec`; create a reviewed new target revision and new evidence. |
| Required evidence is unknown | `request-input`; obtain a discriminating view or missing dimensional information. |
| The same feature fails twice | Change approach class before another attempt; do not repeat cosmetic parameter tweaks. |
| Budget exhausted with unresolved findings | `request-input`; keep the evidence and unresolved work visible. |
| All declared findings and numeric checks pass | `stop` for this bounded review; retain separate motion/export/manufacture gates. |

<!-- ease:source S5 anchor="repeated failed features: Change the modeling or capture approach before another attempt" -->

<!-- ease:source S5 anchor="decision ladder: accepted -> stop; unknown -> request-input; budget exhausted -> request-input; cause spec -> refine-spec; else refine-code" -->

A later packet includes the preceding assessment and its exact target hash. It
cannot silently compare progress against a newly invented target. Optimization is
another revision: regenerate the relevant numerical and visual evidence after
changing mesh density, materials, camera or render settings. An uncalibrated
weighted image score is not the stopping predicate.

### 6. Delivery and ongoing research

Deliver native source, explicit parameters, target/candidate/proof bindings, <!-- ease:source S11 anchor="delivery: separate media/motion/fit/manufacture statuses; manufacture BLOCKED while evidence absent" -->
execution journal, numeric receipts, critic findings and separate outcome statuses.
For print/both, this review layer keeps manufacture BLOCKED; the existing production
gate and physical evidence remain required. For render-only verification fixtures,
manufacture is NOT_REQUESTED. Do not start a slicer, upload a part, or operate a
machine just because an upstream skill documents it.

New upstream knowledge follows scan → curate → prepare → review → publish. Keep
commit-pinned provenance and the distinction between upstream documentation,
source-level checks, upstream mocked tests, local native tests and physical evidence.
The durable lesson is to keep source identity, execution state and acceptance
evidence separate until the actual declared predicates join them.

### 7. Product-scale use and recovery after partial success

The [CK-001 retrospective](../../docs/ck-001-session-retrospective.md) and
[new-product template](../../docs/product-workflow-template.md) extend the coupon
into a real assembly without claiming a general autonomous-repair benchmark.
Required pipeline fields are finite numerical observations; keep SHA strings and <!-- ease:source S10 anchor="native-pipeline requires finite numerical postconditions; SHA strings in evidence metadata" -->
status labels in metadata. If the native process saved a valid model but a wrapper
or postcondition declaration failed, inspect the model/receipt identity and preserve
the failed attempt. Verify that existing artifact through a new explicit route
instead of reconstructing it merely to get a successful journal entry.

Route surprising measurements through `geometry-diagnostic-workflow`, final media <!-- ease:source S10 anchor="retrospective routes lessons to the three workflow modules" -->
through `native-render-delivery`, and physical/electrical closure through
`manufacturing-evidence-workflow`. These documents are conditional reading; they
do not make their case-specific specimen values, source roles or scripts universal.

## Failure Modes (Mandatory)

- **A downstream pass cannot find an upstream file** — cause: guessing another step's filename instead of reading `DESIGN_OS_INPUTS_JSON` (`project` and `artifacts` maps) — fix: declare `artifact_inputs` (e.g. `build:model.blend`), list the producing step in `depends_on`, read the map.
- **Retry is refused or work is repeated after a crash/timeout** — cause: attempt left unknown/interrupted and resume only skips unchanged executed work — fix: inspect and reconcile the failed attempt, then start an explicitly new run; never erase evidence to bypass retry protection.
- **Review assess exits 2** — cause: malformed or stale inputs (hashes, `max_rounds` above 3, missing `target_revision`) — fix: regenerate the packet against the exact revision hash; exit 1 means unresolved findings, not an error.
- **Same visual feature fails twice and parameter tweaks continue** — cause: cosmetic retries inside one approach class — fix: the decision code reports `Change the modeling or capture approach`; switch approach class before another attempt.
- **Valid saved model but the pipeline wrapper failed on a postcondition** — cause: a required field was a SHA string or status label instead of a finite number — fix: keep the failed attempt, verify the saved artifact through a new declared route; put SHA/status in metadata (S10).

## Sources

- [S1] Repo: scripts/native_pipeline/runner.py (runner env DESIGN_OS_OUTPUT_DIR / DESIGN_OS_INPUTS_JSON; executed state; delegates to headless-run.sh) — scripts/native_pipeline/runner.py — captured 2026-10-13 — sha256 fc89b0103e4a3954312497b10b1fff15af4e84552695729f49338157d450a694
- [S2] Repo: scripts/native_pipeline/manifest.py (manifest fields incl. artifact_inputs, depends_on) — scripts/native_pipeline/manifest.py — captured 2026-10-13 — sha256 182a206b3dc370f04b0d9707fc0fa25f8a6dc81aa22c11ffe9ffc93f6a2103df
- [S3] Repo: scripts/native-pipeline.py (CLI: run --resume, exit 0 ok / 1 not ok / 2 invalid) — scripts/native-pipeline.py — captured 2026-10-13 — sha256 ac067360dd934128cda76028acd16e52447579e62ef0e9636698e3f55f3030db
- [S4] Repo: scripts/native_review/evidence.py (review contract: version 1, target_revision, purpose, max_rounds <= 3) — scripts/native_review/evidence.py — captured 2026-10-13 — sha256 90fef1da272eb4adf7092f47b7085c03582f5b8495f27a84d74ee31243d31b12
- [S5] Repo: scripts/native_review/decision.py (verdict ladder: stop / request-input / refine-spec / refine-code; repeated failure message) — scripts/native_review/decision.py — captured 2026-10-13 — sha256 19ece8175b2d0fd33fac9511352ea594446bed0261ef4da81adb8242f892e9df
- [S6] Repo: scripts/native-review.py (CLI: prepare, template, assess; exit 1 when assess not accepted; exit 2 on error) — scripts/native-review.py — captured 2026-10-13 — sha256 45dce9a430642a6595da3075791afd99bbde644aed678cd5ac1ee52685b7b917
- [S7] Repo: research/upstream-agent-patterns/meshy.md (upstream Meshy pattern record (pinned commit)) — research/upstream-agent-patterns/meshy.md — captured 2026-10-13 — sha256 0fe883d2734647eb50dce07c655926df85765a8bade05d802430456c90a82c33
- [S8] Repo: research/upstream-agent-patterns/dream-loop.md (upstream Dream-loop pattern record) — research/upstream-agent-patterns/dream-loop.md — captured 2026-10-13 — sha256 55e02f0155ed1a3f441feb1c64a1b62d883c67b1276fb16ba55c8662aea1ab07
- [S9] Repo: research/upstream-agent-patterns/text-to-cad.md (upstream Text-to-CAD pattern record) — research/upstream-agent-patterns/text-to-cad.md — captured 2026-10-13 — sha256 77babb47e52062e987404c3c0416dbe01fdd2103fab555e11a9f496db0f349ec
- [S10] Repo: docs/ck-001-session-retrospective.md (CK-001 retrospective: partial-success recovery, finite postcondition fields) — docs/ck-001-session-retrospective.md — captured 2026-10-13 — sha256 9b3a2cfedbb2fe84af493543b55d03282513a870d36d9e74f37585d3e4950c4e
- [S11] Repo: AGENTS.md (binding rules: purpose, verify ladder, verdicts, manufacture BLOCKED) — AGENTS.md — captured 2026-10-13 — sha256 d994b27effa2f9ae859d2a4215fa53bfe3902c50396f0a019eb3cd2a0a63ecc7
