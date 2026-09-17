# CK-001 revision B

> **Public checkout.** `runs/`, `delivery/`, the ZIP archives and manufacturer PDFs are not in this
> repository (size and redistribution). The r02 package — scene, GLB, Full HD media and the gate, fit,
> export and review reports cited below — is published under
> [`docs/reviews/ck-001/r02/`](../../docs/reviews/ck-001/r02/README.md) and on the
> [project site](https://jangtrinh.github.io/design-os-3d-blender/reviews/ck-001/r02/). Paths below
> are relative to the original build directory; `plans/` links and DESK NODE 120 are not published.

The current package is **`delivery/r02/`**. Open `delivery/r02/review.html` for eleven
native Full HD images and the four-second Full HD animation. The editable scene is
`delivery/r02/CK-001.blend`; the verified exchange file is `delivery/r02/CK-001.glb`.
Archive: `CK-001-revision-B-FullHD.zip`.

This is the refined digital prototype of the owner's compact keyboard reference:
284 x 92 x 32 mm, 58 keys, five slotted knobs and four feet. The new geometry resolves
previously omitted receiver and shaft interfaces; physical fabrication/electronics
qualification remains separate. The lower switch profile and supporting hardware
include explicitly declared design adaptations.

## What changed

- Keycaps now have integral bosses and actual cross receivers. Their visible skirt
  is 5 mm, with the overall keycap envelope preserved at 9.5 mm. The actual stem
  inserts 3.0 mm with 0.2 mm ceiling reserve.
- The wide spacebar has two integral guide pins and mounted sleeves. Rest engagement
  is 3.65 mm; the declared 3 mm travel was sampled at seven positions.
- All five knobs have stepped D receivers and matching D shafts. Encoder bodies,
  carrier plates, washers/nuts and prototype supports are modeled. Nominal D
  engagement is 5 mm; mismatched rotation and offset controls detect interference.
- PCB and USB daughterboard supports, encoder keepouts and non-overlapping screw
  insertion zones replace earlier unsupported or ambiguous arrangements.
- Transmissive acrylic receives light from actual scene emitter geometry. Curved
  control shading was corrected without changing vertex coordinates or face loops.
- Available local reference copies are now hash-bound to an actual independent
  visual review. They remain design references, not certified manufacturer drawings.

## Current evidence

| Area | Result | Source |
|---|---|---|
| Form gate | Eight representative families pass | `runs/geometry-B03/steps/gate/attempt-0001/gate-report.json` |
| Actual interfaces | 58 keys x seven samples over 0..3 mm; two guides and five D couplings pass the declared predicates | `runs/verification-B03/steps/inspect/attempt-0001/fit-report.json` |
| Final gate / STL re-import | Eight families pass with no failed/missing required checks | `runs/verification-B03/steps/final-gate/attempt-0001/` |
| Layout | 29 checks pass on the saved scene | `runs/verification-B03/steps/inspect/attempt-0001/layout-checks.json` |
| GLB re-import | Exact 781 names at frames 1, 7 and 60; triangle counts match, measured correspondence error 0.0 mm | `runs/verification-B03/steps/reopen/attempt-0001/glb-roundtrip.json` |
| Native media | Eleven PNGs and 96 video source frames all verified 1920 x 1080; MP4 fully decoded at 24 fps / four seconds | `runs/fullhd-B02/steps/media/attempt-0001/media-manifest.json` |
| Visual reference review | Seven declared feature groups accepted, residual visual differences recorded | `runs/reference-review-B01/assessment.json` |
| Decoded media review | Critical MP4 frames 1, 7, 60 and 96 inspected | `runs/reference-review-B01/final-media-review.json` |
| Package | 62 copied/generated files plus manifest; hashes and ZIP members/CRC checked | `delivery/r02/manifest.json` |
| Manufacture | BLOCKED pending physical process, hardware and electrical qualification | `delivery/r02/status.json` |

The 781 mesh count describes the assembly/export, including printed lettering and
illustrative electronic details. The production geometry gate covers eight stated
part families, not every visualization mesh. The STL set is an unreleased digital
specimen set, not a certified functional keyboard kit.

Scene SHA-256:
`de2251261c7d1c17c4150dd3cccc6e42f5a146036916d223801882c4f61c8e16`

GLB SHA-256:
`bc8c3c2f868b1052c7baa88f55d7533e2fa810dece21a0af8f39023a3633eb82`

Archive SHA-256:
`ac8c4c8596e44723244c4e5143cc4677cdddc14a17faee81200a625fe5bfb2e4`

## Remaining work before physical release

Modeled receivers and D shafts are no longer omitted. What remains is their
physical retention/fit across real hardware and process tolerances, guide friction
and wear, carrier adhesive/thread/preload strength, exact PCB/USB/LED circuitry and
firmware, material/process trials and assembly/load/thermal testing.

Visual review is feature-based. Camera/framing differs from the source; legends and
secondary markings are simplified; RGB is more restrained; the derived underside
label is omitted. No exact-likeness score or compliance-logo claim is made.

The four source reference copies retain their original resolutions under
`delivery/r02/reference/`. The Full HD requirement applies to the new rendered
media, not upscaling input evidence. The small packed RGB texture is an internal
material resource, not a delivered social image.

## Reproduction and history

Use the existing native pipeline manifests with new run directories. The accepted
sequence is geometry-B03, presentation-B03, verification-B03 and fullhd-B02.
Source, camera, spec or settings changes require a new hash-bound verification.
The failed FullHD-B01 attempt is retained; its D-receiver crop led to an actual-scene
camera regression and a measured framing correction. No failed journal was rewritten.

`README-r01-history.md`, `delivery/r01/`, earlier runs and
`source-snapshots/r01-before-refinement/` retain the previous handoff. The superseded
DESK NODE 120 example remains in its own build. Full completion details are in
`../../plans/260917-keyboard-refinement/reports/completion.md`.
