---
name: native-agent-iteration
domain: pipeline
blender_target: "5.2 LTS"
audience: ai-agent-bpy
description: Local task lifecycle, target-bound independent criticism and source-parameter contracts adapted from three reviewed upstream agent repositories.
loads_with: [native-api-contracts, agent-workflow-loop]
tags: [orchestration, workflow, critique, provenance, parameters, recovery, native]
---

# Native agent iteration: source, execution, judgment and revision

This workflow combines three distinct mechanisms: Meshy's task lifecycle, Dream-loop's
independent visual feedback, and Text-to-CAD's source/parameter/artifact discipline.
The detailed source analyses are in `research/upstream-agent-patterns/`. Reuse the
three existing skills; do not install the upstream skills as competing policies.

## 1. Convert a request into a verifiable native contract

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

## 2. Run a declared pass pipeline with durable evidence

Use `scripts/native-pipeline.py` to check and execute a bounded dependency-ordered
manifest. Each step names its existing project Python payload, declared input files,
dependencies, output names, required numerical postcondition fields and timeout.
The runner delegates to `headless-run.sh`; it does not generate code itself.

Each attempt gets a distinct output directory and a record written before launch.
The payload receives `DESIGN_OS_OUTPUT_DIR` and `DESIGN_OS_INPUTS_JSON`. Its
`project` map contains declared project files; its `artifacts` map contains only
explicit `artifact_inputs` entries such as `build:model.blend`, each mapped to an
absolute path. The producing step must be listed in `depends_on`.
Read these instead of guessing another step's filenames. Write outputs only in the
assigned directory. Source/manifest/runtime/input/output hashes bind successful work.

`executed` is an execution-and-artifact state. A downstream pass may inspect it, but
it is not visual or manufacturing approval. A timeout, interrupted attempt or missing
authoritative result remains unresolved. Resume only skips unchanged executed work
and starts untouched pending work. Inspect and reconcile failed/unknown work before
creating an explicitly new run; never erase evidence to bypass retry protection.

## 3. Prepare the visual target and critic packet

Create a target JSON with `version: 1`, an explicit `target_revision`, `purpose`,
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

## 4. Give the critic an evidence-focused assignment

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

Exit 0 means the declared numeric and attributed visual findings passed for the
bound revision. Exit 1 records unresolved findings. Exit 2 means malformed/stale
inputs or an invalid command. The command verifies bindings and completeness, not
the truth of a critic's vision or identity. A distinct reviewer name is a declared
separation, not authentication. Preserve this limitation in the delivery record.

## 5. Correct the right cause and detect stalls

| Result | Next action |
|---|---|
| Numerical check fails | Correct the measured issue before claiming completion; visual praise cannot override it. |
| A visual feature fails with a clear contract | `refine-code`; change the named geometry, placement, material or capture behavior. |
| The contract is contradicted | `refine-spec`; create a reviewed new target revision and new evidence. |
| Required evidence is unknown | `request-input`; obtain a discriminating view or missing dimensional information. |
| The same feature fails twice | Change approach class before another attempt; do not repeat cosmetic parameter tweaks. |
| Budget exhausted with unresolved findings | `request-input`; keep the evidence and unresolved work visible. |
| All declared findings and numeric checks pass | `stop` for this bounded review; retain separate motion/export/manufacture gates. |

A later packet includes the preceding assessment and its exact target hash. It
cannot silently compare progress against a newly invented target. Optimization is
another revision: regenerate the relevant numerical and visual evidence after
changing mesh density, materials, camera or render settings. An uncalibrated
weighted image score is not the stopping predicate.

## 6. Delivery and ongoing research

Deliver native source, explicit parameters, target/candidate/proof bindings,
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
