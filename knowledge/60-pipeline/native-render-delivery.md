---
name: native-render-delivery
domain: pipeline
blender_target: "5.2 LTS"
audience: ai-agent-bpy
description: Deliver actual saved Blender assets at requested pixel density with camera, surface, decoded-video, reference and revision evidence.
loads_with: [native-agent-iteration, native-api-contracts]
tags: [render, full-hd, camera, normals, export, provenance, review, delivery]
---

# Native render and revision-bound delivery

Activate for a request to render the current model, improve share-quality output,
change aspect/resolution, deliver animation/GLB, or refresh media after geometry
changes. The CK-001 B/C03 sequence supplies the worked evidence, not universal
camera, sample-count, hardware or performance presets.

## 1. Freeze the artifact before the picture

Record the exact saved scene, scene/spec hashes and applicable form/final gate.
Separate product geometry, materials/normal flags, camera, compositor, frame range
and source dependencies. A material/normal-only edit can preserve vertex geometry
while still invalidating media and export shading evidence. Record which identity
was preserved; do not claim the old scene hash remains valid after resaving.

A request to render the model is satisfied by Blender rendering that model.
Generated concept imagery, screenshot enlargement and a filename containing
"FullHD" are different artifacts. They cannot stand in for source-bound model
output. Preserve reference bytes at their original resolution; do not upscale a
reference to satisfy a requirement on newly rendered delivery images.

When a geometry revision already has media, retain the old set and show its source
SHA and historical status. Honor an existing owner authorization that covers the
new render. Otherwise obtain one decision with an estimate per media set. A
technical neutral-material capture is not a replacement marketing release.

## 2. Preflight the actual output aspect and apparent scale

Set width, height, resolution percentage, pixel aspect, camera and frame before
checking framing. A 4:3 proof does not establish a 16:9 macro crop. Check every
shot, including isolated receiver/underside views and animation endpoints.

Use evaluated geometry and the evaluated camera. `framing()['in_frame']` includes
XY, positive depth and near/far clipping; it excludes occlusion, render flags,
render borders, children and un-realized instances. Name which objects need full
containment for a macro view rather than demanding the whole assembly fit it.

CK-001's D-receiver closeup passed the previous composition but failed its 16:9
camera guard. The correction increased the fitted camera span after measuring
projected extents. It did not disable the guard or rerun a finished model build.
Study [`fullhd.py`](../../builds/reference-keyboard/scripts/fullhd.py) and
[`fullhd_framing_test.py`](../../builds/reference-keyboard/tests/fullhd_framing_test.py)
as build-specific examples; they require the pinned local product scene.

## 3. Review the surface at delivery density before batching

Render the highest-risk metal edge, legend and translucent interface first. Look
for cylindrical banding, polygonal silhouettes, broken slot exits, floating text,
black undersides, lost surface detail and clipping. A low-resolution thumbnail
cannot settle these defects. Use a measured renderer profile and small trial cap;
do not assume a particular GPU or sample count is fastest or sufficient.

Distinguish surface-normal discontinuities from geometric faceting. For CK-001,
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

## 4. Export only the intended product and test the actual bytes

Select the product and required hierarchy explicitly and use the active scene.
The initial CK-001 export exposed a foreign default Cube from another scene.
After export, inspect the actual GLB container, mesh names/count, animation and
embedded-image records, then import in a new Blender process.

Compare named world-space geometry and transforms at rest, a meaningful actuation
pose and an exploded/other critical pose. GLB may split vertices for normals/UVs;
raw vertex counts alone are not a geometry-fidelity predicate. Use triangle counts,
bounds and a declared surface method with both directions when sampled. Report
quantized correspondence precision separately from measured distance. A sampled
maximum of zero is not proof of all-frame material, driver or physical equivalence.

Actual implementations:
[`pass-06-export.py`](../../builds/reference-keyboard/pass-06-export.py),
[`export_compare.py`](../../builds/reference-keyboard/scripts/export_compare.py),
and the [geometry diagnostic workflow](geometry-diagnostic-workflow.md).

## 5. Validate images, frames and encoded motion independently

For a requested 1920 × 1080 delivery, require that actual PNG headers and decoded
video metadata have those dimensions at 100% output scale. Verify complete frame
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
Decode success cannot prove a good story, absence of temporal shimmer, or continuous
collision freedom. Raw-frame reuse requires matching declared dependencies and
complete matching files. An existing range or a filename is insufficient. The
native pass runner supports attempt reuse, not generic partial-frame recovery.

## 6. Review, package and preserve scope

Lock reference, candidate, numeric receipts and actual proof images through
`native-review.py`. The separate critic must inspect every contracted view and
provide pass/fail/unknown findings. Do not widen a failed fidelity criterion after
seeing the candidate. Record residual legend, camera, RGB or underside differences
even when the narrower contracted feature is accepted. A new target starts a new
review lineage. Declared reviewer identity is not authentication.

Before copying a package, verify scene/spec/export/media/review bindings and
semantic results. Derive mesh and part-family counts from actual reports. Rehash
copies and validate archive member lists/CRC. Keep the status of a candidate distinct
from an approved media set, and both distinct from physical manufacture.

CK-001's [`package_delivery.py`](../../builds/reference-keyboard/scripts/package_delivery.py)
handles the B presentation package;
[`manufacturing/package_candidate.py`](../../builds/reference-keyboard/manufacturing/package_candidate.py)
handles the C03/E02 engineering package. They are different task-specific consumers,
not a single generic release validator. C03 did not inherit B's GLB/video acceptance.

## Falsifiers and boundaries

Reject a new aspect that crops its target; a full-HD label on a smaller PNG; an
unreadable hidden receiver; a foreign scene object in GLB; missing decoded frames;
or a package whose media SHA belongs to an older geometry revision. A stronger
global summary must never erase a fail/unknown in its applicable local contract.

The helper tests validate numeric behavior and evidence handling. Actual visual
inspection, material fidelity, animation meaning, factory compatibility and
physical acceptance remain separate work. This workflow installs no renderer,
external generation service, asset download or background render daemon.
