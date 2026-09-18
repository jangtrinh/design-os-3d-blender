# From API research to a tested product workflow

Session: 17 September 2026. This retrospective converts the recorded work into
reusable decisions, procedures and falsifiers. It does not reopen the manufacturing
verdict. C03/E02 remains an engineering candidate with no physical measurements.

## What is now reusable

| Intent | Procedure | Skill / CLI entry |
|---|---|---|
| Start a serious product project | [Contract and stage template](product-workflow-template.md) | Core skill; `native-hard-surface --topic session-retrospective` |
| Diagnose geometry versus checker failures | [Geometry diagnostic workflow](../knowledge/60-pipeline/geometry-diagnostic-workflow.md) | Core; `precision-assembly-metrology --topic geometry-diagnostics` |
| Produce source-bound render/export media | [Native render delivery](../knowledge/60-pipeline/native-render-delivery.md) | Core + image-to-3D; `render-export-delivery --topic native-render-delivery` |
| Advance toward physical pilot evidence | [Manufacturing evidence workflow](../knowledge/60-pipeline/manufacturing-evidence-workflow.md) | Core; `precision-assembly-metrology --topic manufacturing-evidence` |
| Promote new lessons without duplicating skills | [Knowledge promotion procedure](../.agents/skills/blender-knowledge-workbench/references/knowledge-to-workflow.md) | Knowledge workbench |

CLI fragments in the table follow `python3 scripts/blender-knowledge.py route`.
The three existing skills remain the entrypoints. Long-form diagnosis is loaded
only when relevant; no fourth skill or background research daemon was added.

## The progression and its boundaries

Initial research improved evaluated mesh ownership, camera checks, Action slots,
Geometry Nodes binding and helper-cache invalidation. See
[native API contracts](../knowledge/00-foundations/native-api-contracts.md).
Each reusable helper needed a native positive case and a control that would reject
the old wrong behavior. A self-test that merely creates objects is insufficient.

Three upstream repositories contributed mechanisms, not automatic capabilities:
[Meshy](../research/upstream-agent-patterns/meshy.md) informed task lifecycle;
[Dream-loop](../research/upstream-agent-patterns/dream-loop.md) informed distinct
builder/critic feedback; [Text-to-CAD](../research/upstream-agent-patterns/text-to-cad.md)
informed parameter/source/role separation. Commit-pinned dossiers distinguish what
was read from what was implemented locally. No hosted generation, B-rep kernel,
slicer or device stack was installed by that integration.

The first enclosure sample was superseded when the owner selected the keyboard.
Its failed STL report remained preserved; it was not repaired to pretend the
superseded project had finished. Requirements and authorization followed the
owner-selected project, while superseded evidence retained its own identity.

The controlled missing-detail coupon was useful for testing a critic packet. It
was not accepted as the requested production-grade demonstration. The keyboard
then exercised actual interfaces, geometry, source exchange, media and failure
recovery across multiple revisions with unplanned defects.

## Lessons mapped to action and disproof

| Incident or discovery | Reusable action | A result that must be rejected |
|---|---|---|
| A bare temporary mesh accessor lost its allocation owner | Borrow evaluated owner + mesh in a context manager; copy independent numbers out | Original object is cleared instead, or exceptions bypass cleanup |
| Modifier/constraint changes were absent from measurements | Read evaluated vertices and evaluated transforms under an explicit view-layer/frame scope | Array or constraint changes leave measurements unchanged |
| One Action can hold distinct object slots | Use the assigned channelbag; edit only requested channels/frames | A neighbor slot changes or a rerun duplicates keys |
| A stored GN property may be disconnected from its input | Resolve actual identifiers, reject ambiguous names/types, measure output change | Assignment succeeds while generated dimensions stay unchanged |
| Facade hashes miss imported implementation edits | Declare loader dependencies and index nested source modules | Same-size dependency edit silently reuses old helper code |
| User images and later generated sheets disagreed | Give every source an authority role; freeze actual bytes and preserve conflicts | A derivative image becomes proof of hidden hardware geometry |
| Target dimensions were at risk of being inferred from the output | Keep authored requirements separate from measurement records | Wrong output defines its own acceptance target |
| Source declares nominal stroke plus tolerance | Inspect rest, intermediate poses and tolerance extremes | 3.0 mm passes and is presented as covering 3.2 mm |
| Rounded-square profile points distorted a purported circular bore | Sample the circular interface independently; probe actual radii | Nominal radius passes while the true opening is smaller |
| Rays could not cross a 284 mm plate | Derive axial reach from the measured object's projected extents | An arbitrary fixed ray limit makes a real through-hole fail |
| Fine collar triangles all fell below the face-area threshold | Diagnose coverage; fallback only when the primary selection is empty | Thin, empty or degenerate control passes after the fix |
| Temporary BMesh owner was lost inside a generator expression | Hold and explicitly free the native allocation | The fixture crashes and is blamed on the product predicate |
| BVH distances and split export vertices were misleading | Check units/local coordinates and triangle correspondence; retain a sampled fallback with limits | Triangle count alone or reordered vertex count becomes fidelity proof |
| An unrelated scene object leaked into GLB | Explicit active-scene product selection and imported-name comparison | Default Cube or a helper is silently shipped |
| Full-HD macro exposed smoothness and framing defects | Test final aspect and highest-risk surface before the batch | A 4:3 thumbnail licenses a clipped/faceted 16:9 closeup |
| A render request initially received concept imagery | Render the actual saved Blender model with a manifest | A generated concept is labeled as evidence from the model |
| A successful build was rejected by numeric-postcondition metadata | Read saved bytes, retain the failed journal, verify the existing artifact | Rebuild solely to rewrite execution history as green |
| Keycaps contacted covers at the maximum tolerance stroke | Fix the cap within its contract; keep receiver and unrelated geometry stable | Widen the simulated factory housing or weaken the contact test |
| Adhesive joints were replaced with screws | Inspect seats, tip gaps, thread zones, access and material section | Screw presence is claimed to prove retention or strip strength |
| Acrylic had an axial gap despite a complete-looking stack | Add a defined load-path part; measure actual surviving support sectors | Nominal contact is reported as uniform bearing or qualified preload |
| E01 logic checks missed LED polarity | Read the exact part's circuit diagram and add the missing rejection case | Old common-cathode mapping passes a common-anode driver contract |
| A positive voltage estimate lacked a guaranteed bound | Label assumptions and conservative screens separately; require board evidence | A model estimate is promoted to guaranteed headroom |
| ARM compilation produced a relocatable object | Record the exact build artifact and missing link/startup/USB stages | `.o` is reported as target-bootable firmware |
| A physical-record checker could accept stale or mismatched data | Bind records, calibration, process, cohorts, dates, source predicates and uncertainty | Synthetic/empty/stale records produce pilot acceptance |
| Local ignored outputs and public source had different availability | Verify the staged tracked tree, not just the working machine | Published routes depend on unshipped local reports/models |

## Current worked evidence, not a blanket production claim

The [Revision-B public review](reviews/ck-001/r02/README.md) records 58 keys,
five knobs, 781 exported meshes, eight representative gated families, 11 native
1920 × 1080 stills and a decoded 96-frame video. Its GLB comparisons cover frames
1, 7 and 60. Mesh count is not manufactured-part count; sampled poses are not a
continuous collision proof. Residual camera, legend and RGB differences were kept
in the visual findings.

The [C03/E02 manufacturing source](../builds/reference-keyboard/manufacturing/README.md)
records the later mechanical/electrical candidate. C03 replaced 57 one-unit cap
meshes, added four acrylic collars and preserved 515 other mesh/transform
identities. Its local saved-scene check covered 58 keys at eight travel values
through 3.2 mm and retained a failing 6 mm overtravel control. The final 12-family
geometry/STL gate passed. Sixteen separate fit specimens characterized possible
interfaces; none is a measured material/process result.

E02's [final logical report](../builds/reference-keyboard/manufacturing/electrical/verification-E02-final.json)
contains 37 checks, with
[seven negative controls](../builds/reference-keyboard/manufacturing/electrical/negative-controls-E02-final.json).
Those verify pin/net/source/math consistency, not schematic ERC, routed-board DRC,
working firmware or powered hardware. Guaranteed RGB path headroom remains
`NOT_ESTABLISHED`; three status-indicator meshes remain unwired.

The [blank record form](../builds/reference-keyboard/manufacturing/qualification/bench-records.json)
contains zero measurements. The local C03 assessment had 0 of 16 pilot metrics and
five missing prerequisites: factory-switch interface, ERC, PCB DRC, target firmware
build and physical assembly/process. The physical checker validates declared
records and source identity; it cannot authenticate a laboratory or compensate for
an incomplete criterion. C03 does not inherit B's presentation or GLB acceptance.

## Enforcement inventory

| Mechanism | Implemented boundary | Still controller or engineering work |
|---|---|---|
| `native-pipeline.py` | Declared manifest/dependencies, journals, outputs, finite numerical postconditions, hash-checked attempt reuse | Correct pass assertions; reconciliation of partial output; arbitrary Python is not sandboxed |
| `native-review.py` | Target/candidate/proof/numeric pins, complete attributed findings, bounded rounds | Looking at images, correct target, true independence and final visual judgment |
| Parameter helper | Length units, local frames, datums/roles and source/export pins | World composition, true mating, B-rep and physical meaning |
| Production checker 1.0.2 | Declared geometry families and numerical screens, export/reimport | Exhaustive local thickness, process, loads, wear, thermal and factory fit |
| CK-001 package/qualification code | Task-specific source/result/media checks and record replay; `evidence_gate.py` now also binds `frozen_at`, `design_snapshot_sha256`, required `test_configurations`, prerequisite shas and `validate_assessment()` (Q1–Q4 implemented 2026-09-18) | General schema coverage across arbitrary products; evidence authenticity |
| Skills and playbook | Bounded source routing and hash-current publication | Execution and appropriate task-specific acceptance |

## Operating changes for the next project

Start from the [template](product-workflow-template.md), select an identity-risk
family and a real second consumer, and prove the physical interface before adding
expensive presentation detail. Freeze reference roles and authored targets early.
Review broad task assumptions and critical individual parts at their final apparent
scale. Use failed checks to distinguish product, checker and evidence defects.

After a requirement change, write a dependency-scoped invalidation record. A
geometry-preservation hash can justify a bounded reused check, but does not reuse
scene-wide media or electrical/physical acceptance. Keep manual gates labeled as
manual. Carry open work to the appropriate stage instead of repeatedly writing a
global blocked disclaimer without a next action.

## Publication and forward validation

Source, contracts, scripts, tests and these workflows are versioned. Large local
run directories, manufacturer PDF copies, delivery ZIPs, private session reports
and generated pilot snapshots stay local. Historical source paths and hashes in
receipts identify what was tested; they do not claim those files are shipped.
Build-specific scripts retain their input/host guards and need explicit adaptation
before running in another checkout. Never bypass a guard just to make a demo run.

The reusable regressions are in `tests/execution`, `tests/native-pipeline`,
`tests/native-review`, `tests/production-gate`, `tests/knowledge` and
`builds/reference-keyboard/manufacturing/qualification/test_evidence_gate.py`.
Use fresh reports for a current rerun; do not overwrite frozen historical proof.
Publication must pass real topic routing, mirror checks and a tracked-tree check.

No measured productivity, token-cost, autonomous-repair or all-platform benchmark
is inferred from this session. The durable gain is an executable, inspectable
procedure for making narrower claims that the next wrong result can disprove.
