# CK-001 reference keyboard: archived r01 handoff

Historical record only. The current revision-B handoff is described in README.md.

The current digital review package is `delivery/r01/`. Open `delivery/r01/review.html`
for the image gallery and four-second animatic, or open `delivery/r01/CK-001.blend`
in Blender 5.2. The checked archive is `CK-001-review-r01.zip`.

This is a Blender-native reconstruction and engineering adaptation from the owner's
photo, blueprint, 360-degree sheet and parts catalog. The modeled envelope is
284 x 92 x 32 mm, with 58 installed keycaps, 58 representative switch assemblies,
five slotted knobs, four feet and separately organized chassis/PCB/plate layers.
The latest catalog's 32 mm envelope is used; the earlier 41 mm side annotation is
retained as an inconsistent source dimension rather than silently equated to it.

## Current acceptance

| Area | Status | Actual evidence |
|---|---|---|
| Native geometry | PASS for declared digital criteria | `runs/geometry-r03/steps/gate/attempt-0001/gate-report.json` |
| Final geometry and STL | PASS for seven representative part families | `runs/verification-r02/steps/final-gate/attempt-0001/final-gate.json` and `stl/` |
| Layout and layer dimensions | PASS | `runs/verification-r02/steps/inspect/attempt-0001/layout-checks.json` |
| Switch geometry / key travel | 58 cells measured; zero detected contact at 0/0.5/1/1.5 mm sampled travel | `runs/verification-r02/steps/inspect/attempt-0001/fit-report.json` |
| Animation | 96 frames, 58 evaluated drivers, 11 sampled transform checks | `runs/presentation-r02/steps/presentation/attempt-0001/motion-report.json` |
| GLB geometry / sampled motion | PASS: exact 496 mesh names and triangle counts at frames 1, 7 and 60; triangle-coordinate correspondence at 0.00001 mm | `runs/reopen-r03/glb-roundtrip.json` |
| Media | Reviewed images and 96-frame / 24 fps / 4-second fully decoded video | `runs/media-r01/steps/media/attempt-0001/media-manifest.json` |
| Visual feature review | Independent reviewer inspected actual output views | `../../plans/260917-reference-keyboard/reports/final-visual-review.md` |
| Formal original-image hash review | BLOCKED | Original inline reference-image bytes were not available through the local tools |
| Physical manufacture / hardware compatibility | BLOCKED | Stem receiver, D-flat, selected hardware/electronics, process and physical trials remain unqualified |

The source scene contains 496 product meshes. The seven gate entries are representative
families, not a claim that all 496 meshes are manufacturing solids. Legends and
electronics details include visualization-only geometry. STL files are digital
specimens and are not a qualified functional keyboard printing kit.

## Delivered files

`delivery/r01/CK-001.blend` retains native Geometry Nodes, separate parts, materials,
packed RGB texture, key/knob animation and assembly groups. `CK-001.glb` has one merged
scene animation and an embedded image. The delivery includes 1024 x 768 hero and
exploded images, detail/underside views, an H.264 animatic, representative STLs,
BOM, explicit design choices, checked reports and a per-file SHA-256 manifest.

Scene SHA-256:
`1e132063327caf7e9853615b4e0385287a6e2a0cb234b96dc2e54b298d6a53a3`.

GLB SHA-256:
`09dc68a0a472a743c4a4c37c72bd48e37d00f8da91675833ddd89cfa462496c7`.

Review archive SHA-256:
`3d6e1a14d031563baa61b40969448852b6798d02431a1f3da88225db587dd62d`.

## Reproduction and evidence ownership

The project uses the repository's `native-pipeline.py`, `agent_runtime`, evaluated
mesh/GN/animation helpers, parametric contract and production gate. Run scripts from
the repository root. Preparation scripts use exclusive output creation; do not rerun
them over existing contracts. Pipeline resumes reuse only source/runtime/input/output
hash-matching executed attempts. Failed or uncertain attempts remain preserved.

The final GLB checker was corrected after `verification-r02` recorded a failure.
That pipeline journal still correctly records the failed reopen attempt. The subsequent
fresh Blender comparison of the unchanged export is retained separately in
`runs/reopen-r03/glb-roundtrip.json`; no prior journal was rewritten to show success.

The first sample, DESK NODE 120, was superseded by the owner's keyboard reference.
Its failed STL roundtrip remains in the separate build and is not a keyboard result.

## Boundaries

The keycap shell has no qualified stem receiver, and the knob's circular 6 mm bore
has no sourced D-flat or qualified retention. The knob neck, PCB seating rebate,
mounting grid, switch envelope, cable location and legend transcription include
explicit local design choices. PCB forms do not constitute a netlist or a working
electronic design. Neither geometric checks nor the film establish actual fit,
preload, electrical operation, optical diffusion, printability, strength or temperature
behavior. The original references require a further direct comparison once their
bytes are available locally; no 100% likeness claim is made.
