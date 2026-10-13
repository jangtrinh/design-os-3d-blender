---
name: native-render-delivery
domain: pipeline
blender_target: "5.2 LTS"
audience: ai-agent-bpy
description: Deliver actual saved Blender assets at requested pixel density with camera, surface, decoded-video, reference and revision evidence.
loads_with: [native-agent-iteration, native-api-contracts]
tags: [render, full-hd, camera, normals, export, provenance, review, delivery]
id: native-render-delivery
title: "Native render and revision-bound delivery"
when: [render-current-model, share-quality-output, aspect-resolution-change, glb-export-delivery, media-refresh-after-geometry-change]
trust_tier: community_reference
sources_checked: 2026-10-13
---

# Native render and revision-bound delivery

## Purpose
Deliver images, video and GLB that come from the actual saved Blender scene, at the requested pixel density, with camera, surface, decoded-media and revision evidence — never a concept image, an enlarged screenshot or a stale media set.

## When to Use / When NOT
- ALLOWED: rendering the saved model for share-quality stills, animation or GLB — frozen artifact, aspect preflight, density review (§1-§3).
- ALLOWED: validating exported GLB bytes, PNG headers and decoded video — §4-§5.
- ALLOWED: packaging and review lineage after geometry revisions — §6.
- NOT ALLOWED: designing the camera/lighting/turntable shot itself — use `product-viz-and-shots` instead.
- NOT ALLOWED: choosing export options or interchange formats — use `export-interchange` instead.
- NOT ALLOWED: geometry diagnosis behind a failed compare — use `geometry-diagnostic-workflow` instead.
- NOT ALLOWED: manufacture or print acceptance — use `manufacturing-evidence-workflow` or `3d-printing` instead; delivery media never imply manufacture status.

## Core Knowledge Content

Activate for a request to render the current model, improve share-quality output,
change aspect/resolution, deliver animation/GLB, or refresh media after geometry
changes. The CK-001 B/C03 sequence supplies the worked evidence, not universal
camera, sample-count, hardware or performance presets.

### 1. Freeze the artifact before the picture

Record the exact saved scene, scene/spec hashes and applicable form/final gate <!-- ease:source S1 anchor="Delivery: separate status rows; geometry changed -> old evidence void" --><!-- ease:source S4 anchor="Freeze the geometry source and pin its SHA into every media receipt" -->.
Separate product geometry, materials/normal flags, camera, compositor, frame range
and source dependencies. A material/normal-only edit can preserve vertex geometry
while still invalidating media and export shading evidence. Record which identity
was preserved; do not claim the old scene hash remains valid after resaving.

A request to render the model is satisfied by Blender rendering that model <!-- ease:source S2 anchor="A native-render request must use the saved Blender model, not a separately generated concept" -->.
Generated concept imagery, screenshot enlargement and a filename containing
"FullHD" are different artifacts. They cannot stand in for source-bound model
output. Preserve reference bytes at their original resolution; do not upscale a
reference to satisfy a requirement on newly rendered delivery images <!-- ease:source UNVERIFIED reason="original-resolution rule is this module's own; the rubric only requires hashing actual local bytes" -->.

When a geometry revision already has media, retain the old set and show its source
SHA and historical status. Honor an existing owner authorization that covers the
new render. Otherwise obtain one decision with an estimate per media set <!-- ease:source S1 anchor="Media evidence void: never re-render automatically; ask exactly one question with a GPU estimate per media set" -->. A
technical neutral-material capture is not a replacement marketing release.

### 2. Preflight the actual output aspect and apparent scale

Set width, height, resolution percentage, pixel aspect, camera and frame before
checking framing. A 4:3 proof does not establish a 16:9 macro crop. Check every
shot, including isolated receiver/underside views and animation endpoints.

Use evaluated geometry and the evaluated camera. `framing()['in_frame']` includes
XY, positive depth and near/far clipping; it excludes occlusion, render borders, children and instances <!-- ease:source S3 anchor="framing docstring and in_frame expression" --> (the repo docstring does not mention render flags; treat them as unscreened too <!-- ease:source UNVERIFIED reason="render-flag exclusion is inferred, not stated in the docstring" -->). Name which objects need full
containment for a macro view rather than demanding the whole assembly fit it.

CK-001's D-receiver closeup passed the previous composition but failed its 16:9
camera guard <!-- ease:source S5 anchor="Full-HD macro exposed smoothness and framing defects; a 4:3 thumbnail licenses a clipped 16:9 closeup" -->. The correction increased the fitted camera span after measuring
projected extents. It did not disable the guard or rerun a finished model build.
Study [`fullhd.py`](../../builds/reference-keyboard/scripts/fullhd.py) and
[`fullhd_framing_test.py`](../../builds/reference-keyboard/tests/fullhd_framing_test.py)
as build-specific examples; they require the pinned local product scene.

### 3. Review the surface at delivery density before batching

Render the highest-risk metal edge, legend and translucent interface first <!-- ease:source S2 anchor="Before a final batch, inspect the risky close-up at the final aspect and apparent scale" -->. Look
for cylindrical banding, polygonal silhouettes, broken slot exits, floating text,
black undersides, lost surface detail and clipping. A low-resolution thumbnail
cannot settle these defects. Use a measured renderer profile and small trial cap;
do not assume a particular GPU or sample count is fastest or sufficient <!-- ease:source S4 anchor="DC-01 Metal render 3.12x faster and visibly wrong; CK-001 toy probe extrapolated 9.8 h vs real 609 s" -->.

Distinguish surface-normal discontinuities from geometric faceting <!-- ease:source S2 anchor="Record normals-versus-silhouette defects separately" -->. For CK-001,
smooth-face and intentional sharp-edge treatment removed knob-side banding while
keeping the geometry. Sharp channel exits stayed visible by design. A smoothed
normal cannot fix a genuinely polygonal silhouette or manufacture a missing bevel.
The native [`control_finish_test.py`](../../builds/reference-keyboard/tests/control_finish_test.py)
measures source preservation and creates an inspectable proof; it does not judge
visual quality automatically.

Project legends onto the actual dished surface using a declared offset. Separate
printed legends from manufacturing solids. A real emitter geometry/light path and
a baked export texture can support presentation, but emission strength is not
measured electrical power or calibrated optical output.

### 4. Export only the intended product and test the actual bytes

Select the product and required hierarchy explicitly and use the active scene.
The initial CK-001 export exposed a foreign default Cube from another scene <!-- ease:source S5 anchor="An unrelated scene object leaked into GLB; explicit active-scene product selection" -->.
After export, inspect the actual GLB container, mesh names/count, animation and
embedded-image records, then import in a new Blender process.

Compare named world-space geometry and transforms at rest, a meaningful actuation
pose and an exploded/other critical pose. GLB may split vertices for normals/UVs <!-- ease:source UNVERIFIED reason="vertex-splitting rationale is common glTF practice; the fetched spec text was not searched for it" -->;
raw vertex counts alone are not a geometry-fidelity predicate. Use triangle counts,
bounds and a declared surface method with both directions when sampled. Report
quantized correspondence precision separately from measured distance. A sampled
maximum of zero is not proof of all-frame material, driver or physical equivalence.

Actual implementations:
[`pass-06-export.py`](../../builds/reference-keyboard/pass-06-export.py),
[`export_compare.py`](../../builds/reference-keyboard/scripts/export_compare.py),
and the [geometry diagnostic workflow](geometry-diagnostic-workflow.md).

### 5. Validate images, frames and encoded motion independently

For a requested 1920 × 1080 delivery, require that actual PNG headers and decoded
video metadata have those dimensions at 100% output scale <!-- ease:source S1 anchor="Check actual image headers and fully decode video" -->. Verify complete frame
indices, hashes, fps/duration and a full decode without errors. Inspect selected
decoded frames and watch the motion when claiming timing or temporal quality.

Useful tools on a host where FFmpeg is already available:

```bash
ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=width,height,r_frame_rate,nb_read_frames,duration \
  -of json output.mp4
ffmpeg -v error -i output.mp4 -f null -
```

`output.mp4` is a placeholder. Use the actual file and preserve the command/result.
Both commands were run unchanged on a synthetic 2 s, 1920×1080, 24 fps clip with ffprobe 8.1.2: the JSON reported width 1920, height 1080, `r_frame_rate` 24/1, duration 2.000000, `nb_read_frames` 48, and the null-decode exited 0 with no output <!-- ease:source S8 anchor="nb_read_frames 48; ffmpeg exit=0" -->; the options are documented <!-- ease:source S7 anchor="count_frames, select_streams" -->.
Decode success cannot prove a good story, absence of temporal shimmer, or continuous
collision freedom. Raw-frame reuse requires matching declared dependencies and
complete matching files <!-- ease:source S4 anchor="Media chain, frame identity, decode" -->. An existing range or a filename is insufficient. The
native pass runner supports attempt reuse, not generic partial-frame recovery.

### 6. Review, package and preserve scope

Lock reference, candidate, numeric receipts and actual proof images through
`native-review.py` <!-- ease:source S2 anchor="critic evaluates the locked criteria, retains residual deltas" -->. The separate critic must inspect every contracted view and
provide pass/fail/unknown findings. Do not widen a failed fidelity criterion after
seeing the candidate. Record residual legend, camera, RGB or underside differences
even when the narrower contracted feature is accepted. A new target starts a new
review lineage. Declared reviewer identity is not authentication <!-- ease:source UNVERIFIED reason="statement about the local review script's trust model; not re-verified against its source" -->.

Before copying a package, verify scene/spec/export/media/review bindings and
semantic results <!-- ease:source S6 anchor="media-manifest.json records every file with byte size and SHA-256" -->. Derive mesh and part-family counts from actual reports. Rehash
copies and validate archive member lists/CRC. Keep the status of a candidate distinct
from an approved media set, and both distinct from physical manufacture.

CK-001's [`package_delivery.py`](../../builds/reference-keyboard/scripts/package_delivery.py)
handles the B presentation package;
[`manufacturing/package_candidate.py`](../../builds/reference-keyboard/manufacturing/package_candidate.py)
handles the C03/E02 engineering package. They are different task-specific consumers,
not a single generic release validator. C03 did not inherit B's GLB/video acceptance.

### Falsifiers and boundaries

Reject a new aspect that crops its target <!-- ease:source S5 anchor="A 4:3 thumbnail licenses a clipped/faceted 16:9 closeup" -->; a full-HD label on a smaller PNG; an
unreadable hidden receiver; a foreign scene object in GLB; missing decoded frames;
or a package whose media SHA belongs to an older geometry revision. A stronger
global summary must never erase a fail/unknown in its applicable local contract.

The helper tests validate numeric behavior and evidence handling <!-- ease:source S1 anchor="Every intended check must be declared and run; pass-coverage" -->. Actual visual
inspection, material fidelity, animation meaning, factory compatibility and
physical acceptance remain separate work. This workflow installs no renderer,
external generation service, asset download or background render daemon.

## Failure Modes (Mandatory)
- **16:9 close-up crops its target although the 4:3 proof passed** — cause: framing checked at the wrong aspect — fix: re-run `framing()` at the delivered width/height and enlarge the fitted span <!-- ease:source S5 anchor="Full-HD macro exposed smoothness and framing defects" -->.
- **GLB contains a default Cube or helper from another scene** — cause: export used implicit selection or the wrong scene — fix: select the product explicitly in the active scene and compare imported names <!-- ease:source S5 anchor="An unrelated scene object leaked into GLB" -->.
- **Film passes numeric gates but the owner rejects it as stuttery** — cause: 120 poses at 5 fps encoded to 30 fps by repeating frames — fix: record pose rate and distinct-state count in the media receipt before rendering <!-- ease:source S4 anchor="DC-01 film rejected by the owner: 5 fps pose rate" -->.
- **Package ships media whose SHA belongs to an older geometry revision** — cause: media reused after a resave — fix: keep the old set labelled, obtain one owner decision, re-render from the new saved scene <!-- ease:source S1 anchor="Media evidence void" -->.
- **GPU preview looks fine but delivery shows banding** — cause: faster device produced visibly different output — fix: compare against a CPU reference at delivery density and record the profile <!-- ease:source S4 anchor="DC-01 Metal render rejected: bands around the visor" -->.

## Sources
- [S1] Repo AGENTS.md (verify ladder, Delivery, media rules) — AGENTS.md — captured 2026-10-13 — sha256 d994b27effa2f9ae859d2a4215fa53bfe3902c50396f0a019eb3cd2a0a63ecc7
- [S2] Repo blender-image-to-3d review-rubric.md — .agents/skills/blender-image-to-3d/references/review-rubric.md — captured 2026-10-13 — sha256 4a9c962fe81b716f4d28188e7f2a23c5a9e2d898e9329bedaef0b9ef1f17375b
- [S3] Repo scripts/agent_verify/inspect_scene.py (framing, frame_stats) — scripts/agent_verify/inspect_scene.py — captured 2026-10-13 — sha256 49a1534b4dfb97169c768ce3c320e1d5d46f516ea935475090f376b92d9284b5
- [S4] Repo docs/native-build-pipeline-lessons.md — docs/native-build-pipeline-lessons.md — captured 2026-10-13 — sha256 f3bce9c77b38489998cbf42f9ee068b382a8ad09f782182a5ad61f784c38accb
- [S5] Repo docs/ck-001-session-retrospective.md — docs/ck-001-session-retrospective.md — captured 2026-10-13 — sha256 9b3a2cfedbb2fe84af493543b55d03282513a870d36d9e74f37585d3e4950c4e
- [S6] Repo docs/delivery-review-publication.md — docs/delivery-review-publication.md — captured 2026-10-13 — sha256 2544a0be212b1a5e1e4e906b99342b85e3a710e8659e58b1e5e5f5262c36de55
- [S7] FFmpeg ffprobe documentation — https://ffmpeg.org/ffprobe.html → knowledge/_evidence/kb-261013/w5-ffprobe-doc.html — captured 2026-10-13 — sha256 75dd3d482461e4b453510ec9fc87076a95f2eb0698d211784e1eabaabc82eeb6
- [S8] ffprobe/ffmpeg command self-test on a synthetic 1920x1080 24 fps clip — local run ffprobe 8.1.2 → knowledge/_evidence/kb-261013/w5-ffprobe-ffmpeg-command-selftest.txt — captured 2026-10-13 — sha256 1304316da045f2d799986f725519d60667bfa86d75b002eaa38074be86de48c3
