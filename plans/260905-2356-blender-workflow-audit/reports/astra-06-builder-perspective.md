# Astra (Codex gpt-6-astra) — builder perspective on the robot-arm session

Source: `codex exec resume 01a07092-608e-77b0-b32a-656a405c2bc0` (read-only sandbox), 2026-09-06 00:1x, asked by Claude controller at Jang's request. Verbatim reply below.

---

**Prioritize a checkable engineering contract and release gate before more rendering automation.** I built the Arm; I also let presentation progress outrun mechanical proof. This is a read-only assessment of the September 5 session.

## 1. Friction — ranked

Exact minutes per incident were not measured; counts below are documented rework, not estimates.

1. **No enforced engineering contract before detailing.** I detailed geometry before resolving payload and duty. The later requirement—250 g held for minutes—invalidated direct-drive assumptions and required larger joints/full rebuilding. Hand interfaces needed additional correction. I substituted bespoke load calculations and retained manufacturing blockers. This was my sequencing error as much as a tooling gap. [Journal](./plans/journals/260905-arm-session/02-reference-va-tai-thuc.md)

2. **No shared assembly-state/path validator.** Final transforms passed while waiting parts overlapped. Remote staging cleared waiting positions but diagonal arrival still crossed servo cases. Two insufficient repair approaches preceded lift/traverse/lower plus changed carrier order. I wrote phase-specific sweeps and acceptance checks. Final-position correctness was never enough.

3. **Preview/batch verification was incomplete.** Persistent-data behavior required **294 image rerenders**; rigid servo motion required **37 frames**. Final fingertip cropping required **89 replacement frames**, reusing 2,931. Separately, I chose an unwanted camera direction: numeric framing could not validate owner intent. I returned to the selected film and used decoded-frame review. [Retro evidence](./plans/reports/retro-260905-2337-arm-full-session.md)

4. **Execution success was unreliable.** The retrospective reproduced Python exceptions returning exit **0**, versus **23** with the explicit flag. Preview failure left samples/resolution/path altered. Initial MCP setup also had one documented connection failure. I used explicit CLI flags, saved reports and fresh-process checks; retry counts attributable to these defects are unknown. [Probes](./plans/blender-workflow-retro/reports/runtime-contract-probes.json)

5. **Knowledge retrieval was broad; authority was weak.** Recursive dependencies pulled **18–19 documents** for one topic. Four new boilerplate self-tests later passed despite ten reproduced limitations. I replaced recursive reading with bounded topics and source-specific cautions. Re-executing the helper library was irritating, but I have no evidence it dominated time.

## 2. What I hand-wrote that should be shared

| Promote after regression tests | Existing build examples |
|---|---|
| Evaluated-mesh audit, dimension checks, isolated STL round-trip/export manifest, plate inventory/bounds | `audit-meshes.py`, `check-stl-files.py`, `export-plate-packages.py` |
| Assembly dependency/state validation; waiting/transit/mating checks; containment-aware clearance screening | `assembly-order.py`, `check-clearance-acceptance.py`, independent overlap checker |
| Artifact identity, stale-report rejection, validated frame reuse | `exact-frame-state.py`, `check-render-prefix-state.py` |

Common interface:

```text
tool --scene candidate.blend --spec build.json --report result.json
```

JSON should include schema version, input/checker hashes, units, measured versus allowed values, failed part/interface IDs, exclusions and unchecked coverage. Exit **0=pass, 1=failed requirements, 2=invalid/incomplete input, 3=execution error**.

Keep Arm-specific poses, camera choreography and mating exceptions local. Extract coupon generators only after parameter/measurement tests; do not generalize an unverified coupon by renaming it.

## 3. Mandatory production gates

Code can enforce evidence requirements; mesh tests alone cannot guarantee a manufactured product.

1. **Contract completeness:** missing dimensions, tolerances, hardware evidence or load cases blocks release.
2. **Geometry/export:** evaluated geometry, expected connected bodies, manifoldness, self-intersection, positive volume, feature dimensions, wall screening, plate bounds and STL round-trip.
3. **Interfaces/DFAM:** datum-based fit stacks, head/recess clearance, engagement/bottoming, insertion/tool access, print orientation, support removal and process-specific coupons.
4. **Mechanics/electrics:** all declared load cases, actuator duty evidence, retention, anchoring, cable travel/bend constraints and pin-to-pin checks.
5. **Physical release:** measured fit, assembly, loaded thermal/drift and relevant durability results, bound to the exact revision. Missing evidence stays **BLOCKED**.

I want versioned JSON containing:

```text
units; part IDs/revisions; datums; feature measurements/tolerances;
material/printer/nozzle/process/orientation;
fastener standard+edition+size+length+grade+source;
interfaces/fit stacks; actuator drawings/duty ratings;
payload/tool mass/reach/speed/hold duration;
required checks and physical evidence references
```

Bounding-box agreement cannot prove a hole’s location, diameter or fit.

## 4. Knowledge: useful versus misleading

Most relevant: `polymer-3dprinting-cad.md`, `fasteners-seals-mechanics.md`, `cad-precision-modeling.md`, and robotics fundamentals/tolerance-stack research. Their value was structuring checks—not certifying dimensions.

Noise: vendor-generation material, duplicated startup rules and synthesis labeled “production” without tested implementation.

Missing: verified, revisioned hardware data—especially actual spline geometry, usable thread depth, continuous-duty behavior and printer/material coupon measurements. I cannot honestly claim an authoritative ISO table set was established during this session.

## 5. Candidate ratings

| Candidate | Verdict |
|---|---|
| **a. Execute wrapper/module cache** | **CHANGE:** keep structured failures/full persisted traceback; cache by helper hash/version, reset scene-bound references, treat timeout-after-send as unknown outcome. |
| **b. EEVEE previews** | **KEEP:** your measured 2-second result justifies a local preview profile; retire the categorical prohibition. I have not independently rerun it. |
| **c. Print-readiness script** | **CHANGE:** one orchestrator, modular predicates; wall rays and contiguous meshes are screening, not manufacturing certification. |
| **d. Build spec** | **KEEP:** highest priority; include datum/features, evidence provenance and physical release requirements. |
| **e. Headless exit handling** | **KEEP:** reproduced false-success defect; fix first. |
| **f. Restore state in finally** | **KEEP:** include samples, aspect, filepath and every touched setting; test success and injected failure. |
| **g. Consolidate instructions** | **KEEP:** bounded routing and one authority; verify the proposed token reduction rather than claiming it measured. |
| **h. Pyright/5.1 stubs** | **CHANGE:** advisory lint for obvious errors; 5.2 runtime introspection and isolated execution remain authoritative. |

## 6. What would actually unblock manufacture?

A stronger wrist solution, verified output/retention hardware and instrumented prototypes. The frozen engineering review reported wrist demand **1.006224 Nm versus 0.980665 Nm rated**, with only **2.9% shoulder headroom**. These historical results require recalculation against revised geometry. Better tooling cannot create missing torque or thermal evidence. [Engineering review](/Users/jang/Products/Blender/builds/robot-arm-v2-engineered/reports/independent-final-check.md)

**Status: DONE**  
**Summary:** Prioritize contract, failure propagation and revision-bound engineering gates.  
Manufacturing remains blocked until hardware interfaces, load margins and physical tests pass.
