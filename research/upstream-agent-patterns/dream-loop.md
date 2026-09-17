# Dream-loop: source analysis and native adaptation

Reviewed 2026-09-17 at commit `9bddb901f7d071cfefdd21e264267c757177a9df`.
Upstream: https://github.com/achimala/dream-loop
License observed in the pinned source: MIT, Copyright (c) 2026 Anshu Chimala.
This is an attributed analysis and independently written native implementation,
not a renamed installation of the upstream skill or its service integration.

## What the repository actually contains

The pinned tree contains one root skill, two alternative prose workflows, two
asset-sourcing guides, a Fal reference, a JavaScript queue helper with nine test
cases, and a Python preview server. There is no Blender model generator, machine
vision judge implementation or learned 3D model in this repository. The orchestration
depends on the calling agent following instructions and supplying vision/subagents.
The generation helper talks to a hosted service. Its tests use injected local HTTP
responses, not real service calls; reading them does not qualify any paid endpoint.

Source was read through a partial Git clone without checkout. All substantive
workflow, reference, helper and test text was inspected; the demo GIF was not
downloaded or used as evidence of production performance. Some web/raw-file fetches
failed, but the pinned Git blobs were available. Upstream code was not executed.

## Mechanisms and evidence

| Mechanism | Pinned source | What it provides |
|---|---|---|
| Lock a visual destination before building | [SKILL.md](https://github.com/achimala/dream-loop/blob/9bddb901f7d071cfefdd21e264267c757177a9df/SKILL.md) | Uses a supplied target or derives a target from the existing product screenshot so a redesign need not discard the original composition. This is controller guidance, not an implemented immutable target lock. |
| Independent comparison after implementation and testing | [Pro workflow](https://github.com/achimala/dream-loop/blob/9bddb901f7d071cfefdd21e264267c757177a9df/references/pro-mode/workflow.md) | Builder tests first; judge receives target, current capture, and prior capture/verdict. Concrete correction requests are preferred over general aesthetic impressions. |
| Detect repeated failure and change approach | Same Pro workflow | Two rounds without sufficient improvement or a repeated gap trigger a larger change; another stall asks the owner. It is not enforced by code. |
| Separate orchestration from worker implementation | [Plus workflow](https://github.com/achimala/dream-loop/blob/9bddb901f7d071cfefdd21e264267c757177a9df/references/plus-mode/workflow.md) | A controller validates workers' output and checks integration orientation after each pass. Worker/model policy and the three-round cap live in prose. |
| Preflight, submit, collect as separate operations | [Fal helper](https://github.com/achimala/dream-loop/blob/9bddb901f7d071cfefdd21e264267c757177a9df/scripts/fal-batch.mjs) and [reference](https://github.com/achimala/dream-loop/blob/9bddb901f7d071cfefdd21e264267c757177a9df/references/fal.md) | Offline input validation precedes submission. The queue record retains service-returned identifiers/URLs instead of reconstructing them. Collection is a single pass, not an unbounded blocking loop. |
| Persist before a side effect; preserve uncertain state | Same helper, `runBatch()` | Writes `submitting` before HTTP POST. Accepted IDs, partial responses and uncertain submissions prevent automatic replacement submission. Explicit preconnection failures can remain retryable. |
| Preserve complete artifact boundaries | Same helper | Checks GLB signature/version/declared byte length and writes through a `.part` file before rename. This does not inspect geometry, materials or likeness. |
| Test the unhappy paths | [Queue tests](https://github.com/achimala/dream-loop/blob/9bddb901f7d071cfefdd21e264267c757177a9df/scripts/fal-batch.test.mjs) | Nine tests cover local concurrency, retry suppression, input validation, incomplete acceptance, service/result failure and diagnostic redaction. They are not an empirical image-quality benchmark. |
| Capture an actual running application | [Preview server](https://github.com/achimala/dream-loop/blob/9bddb901f7d071cfefdd21e264267c757177a9df/scripts/preview-server.py) | A localhost POST endpoint saves timestamped captures and a latest alias. It checks the PNG header and byte count, not full PNG integrity or correspondence to a scene revision. |

## What changes when applied to design-os-3d-blender

**Preserve the stable destination.** The target is a versioned local contract with
source-image hashes, named views, capture context, expected feature construction
and falsifiers. A generated mood image could be a design proposal in a separately
authorized workflow; it cannot replace an owner's dimensional drawing or approved
reference. Redesigning the target requires a new explicit contract revision. Old
reviews cannot be inherited by a new target merely because the filename matches.

**Make criticism actionable and bounded.** Replace the weighted 0–10 score with one
PASS/FAIL/UNKNOWN result per contracted feature. Include observed evidence, required
views, a correction or discriminating check, and whether the root cause is code,
specification or missing evidence. The new local review command rejects incomplete
findings and unknown evidence cannot produce acceptance. On a repeated failed
feature, the next action changes approach; the contract caps the review sequence at
three rounds. The number is a controller budget, not a quality guarantee.

**Separate implementation evidence from visual judgment.** Numerical checks are
bound to the candidate's file hashes before a critic packet is assembled. A visual
pass cannot override a failed numerical receipt. Conversely a nonempty mesh, correct
height or valid PNG cannot establish likeness. The critic still needs actual vision.
The local code validates declared evidence and decides the next action; it does not
pretend to recognize images or authenticate reviewer identity.

**Use a restricted critic packet.** Give the critic the locked brief, named visual
features, target/current views and optionally the prior round. Builder explanations
and implementation claims are not part of the visual judgment prompt. Keep actual
source and candidate hashes in the packet for traceability without embedding source
code or encouraging the critic to accept a claimed implementation. A fresh worker
is preferred; when unavailable, label controller review honestly instead of inventing
an independent judge. A different reviewer string only checks declared separation.

**Adopt the lifecycle without the service.** The native pipeline records intent
before starting an existing headless Blender payload, retains immutable attempt
directories and does not silently repeat an unknown execution. `executed` means
declared postconditions and artifacts were observed. It never means visual quality,
physical fit, manufacturing readiness or a paid task's remote success.

**Reuse stronger existing infrastructure.** The existing `hq_coverage.png` checks
CRC, chunk completeness and decompressed payload dimensions, so the new review code
reuses it instead of copying the weaker header-only capture check. Headless execution
still uses `agent_runtime` and `headless-run.sh`. Production and HQ gates retain their
separate scopes. No new server or background watcher is required.

## Explicit exclusions

The asset guides rank hosted generation above Blender and one branch excludes
Blender entirely. They also claim a hosted image-to-3D call should not count as
downloading assets. Those instructions conflict with this project's native asset
policy and are not adopted. No credential search, Fal call, image-service call,
vendor mesh or texture retrieval is authorized by reading this repository.

Subscription-based model selection, named-model prescriptions, forced fresh worker
creation and a requirement to skip worker tests are not imported. Existing user
worker settings and project test discipline govern this integration. A requirement
to match every pixel and an 8/10 completion threshold are not reproducible fidelity
or manufacturing predicates. Target FPS only applies to a declared realtime artifact;
it is not a universal condition for a Blender still, animation or printed part.

## Static limitations discovered in the executable helpers

The queue manifest is atomically replaced under an exclusive file lock, but a crash
can leave the lock behind; recovery is not a proof that a remote request never ran.
Source-image content is not hashed into accepted request identity. A job already
marked downloaded skips collection without revalidating its on-disk file. GLB header
validation alone cannot detect all semantic corruption. The preview server can store
a header-shaped payload as a PNG and does not bind the capture to camera/frame/source.
These are source-level observations; no production failure or performance gain is
inferred from them.

## Native deliverables and falsifiers

`scripts/native-review.py` and `scripts/native_review/` implement prepare, an explicitly
incomplete critique template, and assess. `tests/native-review/` tests changed target,
candidate, proof and numerical inputs; missing/duplicate findings; same-author review;
numerical failure despite visual pass; repeated gaps and budget limits. The native
coupon supplies real Blender renders separately from the host-side contract fixtures.

The adaptation fails if a changed input can inherit a current review, if UNKNOWN or
an empty critique is accepted, if a valid screenshot can override a failed size check,
or if the pipeline silently starts the same unresolved mutation twice. Final executed
results and independent review are recorded under
`plans/260917-upstream-agent-integration/reports/`.
