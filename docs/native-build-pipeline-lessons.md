# Two full product builds: the pipeline that ran, and what it cost

September 2026. CK-001 (reference keyboard, from one owner photo) and DC-01 (desktop companion,
from "build it until it is ready for 3D printing, including the board, wiring, display, charger
and battery") were built end to end in Blender 5.2 by an agent. This is the distillation of both
working records: `plans/260917-reference-keyboard`, `plans/260917-keyboard-refinement`,
`plans/260917-keyboard-manufacturing`, `plans/260917-desktop-companion`,
`plans/260918-production-coverage`, and the build directories they produced.

The incident-level table for CK-001 lives in [the CK-001 retrospective](ck-001-session-retrospective.md);
the publishing leg lives in [delivery review publication](delivery-review-publication.md). This
file is the cross-build view: the shape of the pipeline, the failures that cost the most, and
which lessons are now code rather than prose.

## The shape both builds converged on

```
purpose + contract → blockout (owner sheet) → interfaces → mechanical revisions → integration
→ harness / controls → print kit → renderer qualification → animatic → delivery package → review page
```

Every phase closed the same way, and the repetition is the point:

**build → numeric assert ending in the `AGENT_OK` sentinel → immutable run directory → an
independent re-open of the saved artifact → a named review report → freeze by SHA.**

Revision counts show what "one phase" really means. DC-01: blockout ×3, electronics ×2 plus four
native KiCad attempts, controls ×3, mechanical →M29, integration →I06, harness →H13, print kit
×3, animatic ×6, delivery ×3. CK-001: r01 → revision B with three geometry, three presentation,
three verification and two Full-HD cycles, then the C/E manufacturing series. A build is not a
pass; it is a numbered series of passes whose survivor is frozen by hash.

## What actually cost the most

| Incident | Root cause | Cost | Evidence |
|---|---|---|---|
| DC-01 film rejected by the owner | D05 was 120 poses at a **5 fps pose rate**, encoded to 30 fps by repeating frames. It passed every numeric and visual gate. | 2,125 s of GPU re-render (35 min) on top of D05's 1,164 s, plus new verification, preflight and final reviews, plus a new package | `builds/desktop-companion/state.md`, `presentation/D05/native-frames/receipt.json` |
| DC-01 harness H12 "PASS" was false | the curvature sampler skipped one side of a curve join; the true minimum was 2.996432 mm against a 3 mm requirement | the D04 media set was discarded and the whole demo source superseded by H13 | `plans/260917-desktop-companion/harness-integration.md` |
| CK-001 r01 superseded | stem receivers, D-flats, spacebar guides and the USB support were never modelled, so the first package could not be accepted | a second full revision: 3 geometry + 3 presentation + 3 verification + 2 Full-HD run cycles | `builds/reference-keyboard/README-r01-history.md` |
| CK-001 caps contacted covers | the sweep used the nominal 3.0 mm stroke; the switch is 3.0 ± 0.2 mm, and 3.2 mm touched 57 caps | the whole 1U cap family re-cut in C03 | `plans/260917-keyboard-manufacturing/reports/mechanical-plan.md` |
| DC-01 I05 form failure | an *optional* triangulation/collinear cleanup broke the charger mesh | recoverable only because a checkpoint existed; otherwise a rebuild | `plans/260917-desktop-companion/engineering-integration.md` |
| DC-01 Metal render rejected | the GPU was 3.12× faster and visibly wrong: bands around the visor, max channel difference 38 | six profile renders plus a follow-up before CPU/MetalRT-OFF was qualified | `presentation/performance/image-comparison.json` |
| CK-001 render budget | a toy-resolution probe extrapolated 9.8 h; the real full-size render took 609 s inside a 2,400 s budget | a timeout authored from a number that meant nothing | `plans/260917-keyboard-refinement/reports/render-preflight.md` |
| CK-001 `pass-B-rotation.py` | authored, reviewed into the plan, never run — no manifest step, no run directory | the only check designed to prove a rotated knob pose survives GLB export does not exist as evidence | verified by `scripts/check-pass-coverage.py` |

Three checker false positives (USB containment, a 0.0673 mm BVH distance, a B01 key/plate
clash) each pointed at valid geometry. None was "fixed" by relaxing a tolerance: each was
disproved with an exact boolean and the checker was repaired with a positive fixture plus a
negative control.

## The ten rules worth carrying to the next build

1. **Freeze the geometry source and pin its SHA into every media receipt before the first
   delivery frame renders.** H12 → H13 voided a finished media set.
2. **Motion belongs in the media contract**: frame rate, distinct rendered states and what
   "smooth" means, agreed with the owner next to resolution and length. A film can pass every
   gate and still be wrong at 5 poses per second.
3. **A sampled predicate is not a bound.** Re-check at the exact extremes and on both sides of
   every join: 3.198 mm sampled, 2.9964 mm true; 3.0 mm swept, 3.2 mm real.
4. **Model and gate the mating interface before any presentation, material or media work.**
   Missing receivers cost a whole revision of a finished-looking keyboard.
5. **Treat cleanup (triangulation, collinear dissolve, weld) as candidate-breaking**: checkpoint
   first, keep it optional, bound its tolerance.
6. **Qualify a renderer or device change by pixel identity against frozen frames, never by
   speed.** And measure one full-size frame before trusting a timeout.
7. **An authored pass is not an executed pass.** Every intended check needs a manifest entry and
   a run directory. Enforced now: `scripts/check-pass-coverage.py`.
8. **A constructor fixture must run the gate's own predicate**, not a weaker manifold/volume
   check, or it passes while the gate finds 88 self-intersections.
9. **A surprising measurement gets a disproving probe before any geometry changes.** Fix the
   checker with a positive fixture, a negative control and a re-run on the *unchanged* scene.
10. **Never assemble an acceptance from checks taken across different runs.** Re-open the final
    artifact and re-run every predicate on it.

## Enforced by code today

| Boundary | Mechanism |
|---|---|
| Execution truth | `scripts/agent_runtime.py` sentinel, `scripts/headless-run.sh` |
| Declared inputs, journals, hash-checked reuse | `scripts/native-pipeline.py` and the per-build `*-pipeline*.json` |
| Geometry, walls, features, bed fit, export round-trip | `scripts/production-gate.py` + `scripts/production_gate/` (checker 1.0.2) |
| Per-part coverage, no aggregate blind spot | `production-gate.py --audit-report` (`production_gate/coverage*.py`) |
| Every intended pass is declared | `scripts/check-pass-coverage.py` (+ `tests/pass-coverage/`) |
| Print package identity | `print-kit/check-packages.py`, `verify-print-source.py`, 3MF reopen with damaged-data controls |
| Harness curvature at extrema and joins | `integration/harness/verify_saved.py`, `verify_pair_curvature.py` |
| ECAD | native KiCad ERC/DRC plus `check_electronics.py`, `check_copper.py` with injected faults |
| Media chain, frame identity, decode | `presentation/smooth/{verify30,render30,compose30}.py`, `delivery/package.py` |
| Physical-record honesty | `manufacturing/qualification/evidence_gate.py` (fail-closed, `frozen_at`, snapshot sha, required configurations) |
| Published review pages | `scripts/check-html-tag-balance.py`, `scripts/page-checks/` |

## Still controller discipline, not code

- The purpose question and its mesh-strategy table (`AGENTS.md` step 0b).
- Form gate before delivery media, final gate at delivery: nothing blocks a render when a gate
  has not passed.
- Owner decision points: blockout sheet, animatic before a long render, sign-off.
- The motion/fps contract — now stated in `AGENTS.md` §Delivery, still asked by a human.
- Choosing the *right* tolerance extreme into the spec: the gate checks the spec, never the
  spec's ambition.
- Visual judgment and image-to-original fidelity: no gate exists at all.

`scripts/check-pass-coverage.py` reports two findings on the current tree, and both are real:
`builds/reference-keyboard/pass-B-rotation.py` was never run, and
`builds/desktop-companion/pass-05-integration.py` ran outside any manifest. Neither is silenced
by an allowlist entry, because neither has an owner's reason yet.
