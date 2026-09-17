---
name: manufacturing-evidence-workflow
domain: pipeline
blender_target: "5.2 LTS"
audience: ai-agent-bpy
description: Move a native digital prototype through an engineering candidate to traceable pilot evidence while preserving source, process, measurement and acceptance boundaries.
loads_with: [native-agent-iteration, 3d-printing]
tags: [manufacturing, workflow, qualification, provenance, metrology, electrical, retention]
---

# Manufacturing evidence: prototype, candidate and pilot

Use for a print/both assembly moving from digital geometry to measured pilot evidence.
Core owns scene execution; this workflow defines the evidence needed for each claim.
Render-only manufacture is `NOT_REQUESTED`. Print/both manufacture stays `BLOCKED`
while required evidence is missing. Pilot evidence does not establish yield, lifetime or certification.

The [CK-001 record][handoff] is a worked case, not reusable dimensions: 58 keys at eight
sampled travels through 3.2 mm and twelve representative geometry families pass digitally.
Physical observations remain zero against sixteen pilot metrics; manufacture does not become PASS.

## 1. Stage contract

| Stage | Inputs | Actions | Required postcondition | Stop condition |
|---|---|---|---|---|
| Contract | Purpose, references, dimensional sources, duty and interfaces | Assign source roles; resolve conflicting constraints; define independent targets and falsifiers | Versioned dimensions, tolerances, load/process intent, required evidence and unknowns | Missing constraint prevents the affected detailed construction |
| Digital prototype | Contract, native sources, declared scene inputs | Build, inspect actual saved geometry, sample motion, gate representative parts and reopen exports | Reports bind the scene/spec and state the exact measured scope | Failed, stale, missing or unexamined numerical/visual evidence |
| Engineering candidate | Prototype receipts, exact proposed hardware, retention and circuit design | Close design omissions; check nominal/tolerance envelopes, connectivity and source assumptions | Reviewable mechanical/electrical candidate with explicit open items | Unknown factory interface, unsupported force/headroom claim, missing required toolchain result |
| Process specimens | Candidate interfaces, proposed material/process and mating hardware | Identify a dimensional ladder; fabricate and measure representative specimens | Traceable specimen configurations and a measured selection rationale | Unrecorded processing, damage, unsafe interference or unmatched material/hardware |
| Physical pilot | Frozen design/configurations, approved criteria, actual instruments/specimens | Collect observations, conditions, raw records and paired service histories | Complete records for the declared cohorts and conditions | Missing samples, changed identity, invalid calibration, damage or uncertainty crossing limits |
| Assessment and handoff | Pinned prerequisites and physical records | Assess, replay before reuse, review raw evidence and publish scoped status | Evidence complete for the declared pilot scope, with an attributed engineering decision | Any unresolved prerequisite, stale binding or unsupported release claim |

Keep execution, visual, motion, export, fit and manufacture separate; `executed` has only its [declared scope][lifecycle].

## 2. Resolve sources and constraints before detail

| Source role | Valid use | Required boundary |
|---|---|---|
| Primary photo and close-ups | Visible count, placement, silhouette and construction clues | Hidden interfaces remain unknown or explicitly inferred |
| Authored blueprint or parts sheet | Owner-provided design dimensions | A derived drawing is not an authenticated manufacturer drawing |
| Exact manufacturer part/revision | Stated dimensions, polarity, ratings and test conditions | Family grammar or an evaluation-board BOM does not establish exact SKU availability |
| Engineering assumption/calculation | Proposed packaging, efficiency, load allocation or tolerance screen | Keep assumptions separate from guaranteed limits and measured behavior |
| Saved scene and export measurements | Evaluated geometry under the named checker/predicate | Bounds and collision samples do not establish strength or physical fit |
| Physical specimen record | Observed behavior of the identified hardware/material/process | Transfer requires a justified equivalence review; a hash cannot authenticate the laboratory |

Record source URL, revision, page/figure, selected MPN, units, orientation and supported claim.
Pin accessible source bytes when permitted; otherwise state the access limitation.
A mutable URL is not immutable provenance.
The case's [mechanical requirements][mechanical] retain drawing limits and unresolved
factory dust-wall geometry. [LED source evidence][led-source] records inspected pages;
its conversation capture IDs are historical references, not portable image assets.

Before detail, declare envelope/stack/datums, mating parts, tolerance extremes,
stroke/stop, material/process, minimum walls, screw seats/engagement/tip reserve,
retention load path, electrical keepouts, service-tool access and assembly sequence.
Define constraints before measuring the model; test them instead of rewriting targets to match.
Preserve conflicts and their resolution. Label source dimensions and display adaptations separately.
The reference image cannot supply an unseen thread or footprint.

## 3. Mechanical candidate: geometry, retention and force

Test the saved assembly and named mating objects at maximum and nominal/intermediate stroke,
plus excessive-travel negative controls. [Maximum-travel code][travel] checks selected
cap/stem/guide pairs; it excludes continuous-motion and full-assembly collision proof.
The case's modeled cover is a custom prototype. Its clearance does not qualify
the selected factory switch's surrounding housing, dust structure or real hard stop.
Check an actuator at its own measured stop; use an unloaded fixture for the maximum
design envelope. Do not force hardware to follow a CAD travel limit.

Replacing adhesive with screws, clamps or collars creates a retention scheme;
it does not measure pull-off force, thread strength, preload or wear.
Specify head type, seat geometry, tool access, thread engagement, opposing tip
reserve, local wall/edge ligaments and the actual mating material. A modeled pilot
hole is machining intent, not a manufactured female thread. A supplier's maximum
screw torque is a screw limit, not the assembly torque or the joint's strip torque.

Destructive specimens identify the first limiting failure: thread strip, screw fracture,
floor pull-through or post fracture. Legacy `post_strip_margin` means joint-failure torque
divided by proposed assembly torque; an earlier screw fracture is not thread-strip strength.
Retain both torques, their uncertainties and the selected screw limit.

C03 collars contact surviving shoulder sectors. Nominal checks do not establish uniform
bearing, preload, shims, creep or thermal allowance; physical assembly/process qualification remains.
Use [bench procedure][bench] for the case methods and [mechanical requirements][mechanical]
for the design rationale. Revalidate affected interfaces after a geometry change.

## 4. Electrical candidate: exact topology and bounded calculations

Bind the selected MPN, package orientation, polarity drawing and pins to netlist, BOM,
firmware mapping and power budget. Inspect the exact manufacturer source and driver topology.
A Blender board or pin proxy is not an ECAD footprint. Unwired visual indicators remain unwired.

E02 selects `19-237A/BHR6GHC-A01/2T`: common anode pin 3 belongs to the driver's
SW source; cathodes belong to CS sinks. The [authority][electrical-authority] and
[verifier][electrical-check] record that interpretation. Historical E01 selected
a common-cathode part and omitted this predicate; preserve its failure and source
snapshot. [Negative controls][electrical-negative] now reject the old polarity and
a fabricated guaranteed-headroom flag, alongside connectivity/power/GPIO faults.

Read Vf with its characterization current, temperature and tolerance; distinguish limits from assumptions.
The [power budget][power] gives a +0.69391 V low-current estimate and a -0.47523 V
screen using full-rated drops directly. Linear scaling of published VHR test points
is an assumption, not a guaranteed bound at the operating currents. Neither screen
is measured hardware behavior; guaranteed headroom remains `NOT_ESTABLISHED`.
Measure LED Vf, driver drops, rail regulation/ripple and temperature on the routed board.

Logical checks, schematic ERC, PCB DRC, linked target firmware and powered-board tests
are separate prerequisites. A host C test or ARM relocatable object proves neither
a bootable USB image nor timing on the device. The recorded
[electrical status][electrical-status] leaves KiCad/ERC, routing/DRC and QMK target
build work open; tool absence was observed on the checked host paths, not all hosts.

## 5. Select a process with specimens

The [specimen contract][specimens] contains nine cross receivers, three open D gauges,
three guide sleeves and one pin. The ladder includes deliberate interference candidates;
these are not proven fits or production defaults. Keep a prior receiver as an identified baseline.
Open D gauges do not prove axial retention; a printed pair does not qualify a machined pair.

Record material grade/lot, machine, orientation, settings, tooling/offsets, supports,
washing/curing/conditioning and finishing. Bag or label specimens before separating
the batch. Record sanding or rework as a process change. Use the intended mating
hardware, first inspect dimensions, and start with a safe clearance candidate.
Stop on damage or premature contact. Select from measured installation/removal
forces, retention, friction and wear; choosing the largest opening proves little.

PA12 results do not transfer automatically to POM-C, PBT or another resin/process.
A selected receiver/process starts a new revision with affected geometry/fit gates.
Force windows, cycles, temperatures and counts in [pilot requirements][requirements]
need a new engineering rationale elsewhere.

## 6. Freeze and collect a replayable evidence set

Freeze before release measurements; preserve earlier revisions and raw failures.
Pin requirements and `design_inputs` with unique roles: scene/spec, interface contract,
electrical authority/netlist, power budget, firmware and required reports. Record verifier
source/version alongside assessment; the assessor does not discover missing dependencies or pin all code.

Use a timezone-aware, non-future `frozen_at`. Each `test_configuration` names supported
metrics, exact MPN, pinned process record and manufacturer screw limit. An unspecified
global process string cannot represent several materials. The [freeze helper][freeze]
leaves configurations empty until selection; command success yields incomplete evidence.

Observations identify metric, configuration, serial, MPN, lot, operator, time, unit, value,
uncertainty, instrument, damage and raw-record path/SHA256. Measurements cannot predate the freeze.
Keep repeated curves in raw records, not duplicate specimen rows for one metric.
Service comparisons use the same cohort in order: installation, initial removal, post-service removal.
Preserve MPN, lot and configuration in paired knob/guide tests; a replacement starts a new history.

Instrument records carry unit, calibrated range, validity dates and a pinned certificate.
Required load, torque, time, ambient, soak and count conditions each have measured value,
uncertainty, instrument and raw-record pin; "loaded for ten seconds" alone is insufficient.
Preserve full traces and damage observations, including unexpected failures.

Keep uncertainty intervals within the metric and calibrated-instrument limits.
Continuous readings require positive uncertainty; logged counts are nonnegative integers
with zero counting uncertainty under this checker.
A zero nonnegative slip/current reading may pass an upper limit; a negative
magnitude may not. Derived joint margins must include propagated torque uncertainty
and keep assembly torque plus uncertainty within the frozen screw limit.

## 7. What is enforced, and what requires review

| Implementation | Enforced on the declared route | Remaining human responsibility |
|---|---|---|
| [Evidence I/O][evidence-io] | Root-contained file hashes, unique JSON keys, finite numbers and valid timestamps | Source authenticity and a complete dependency inventory |
| [Record checks][record-checks] | Units, calibrated ranges/dates, hardware/configuration match, uncertainty, damage flags, measured conditions and cohort order | Actual setup, calibration credibility, raw trace interpretation and honest observations |
| [Assessment][assessment-code] | Required prerequisite names, passing report bindings/assertions, specimen counts and all declared evidence pins | Adequacy of requirements, source roles, report fields and acceptance predicates |
| [Replay][assessment-code] | `validate_assessment()` re-hashes inputs and recomputes the saved result | Calling replay before reuse; reviewing changed scope and signing the engineering decision |
| [Electrical checks][electrical-check] | Case-specific topology, declared source metadata, arithmetic and retained release blockers | Primary-source inspection, ECAD, target build, powered-board behavior |

Empty records fail even if labelled physical; declared synthetic/simulation origin also fails.
The [unit tests][qualification-tests] use isolated synthetic fixtures, never bench data.
A dishonest physical-origin label can still pass structural checks with fabricated fields.
Hashes protect byte identity, not truth, reviewer independence or laboratory identity.
The schema also cannot prove that a selected assertion is a meaningful design proof.
Review raw evidence and the completeness of the criteria independently.

## 8. Existing entry points

Run from the repo root when changed dependencies or assessment needs warrant it.
These are examples, not retrospective test results. Use new outputs; preserve old reports/journals.

```bash
mfg_dir=builds/reference-keyboard/manufacturing
python3 scripts/native-pipeline.py status --run-dir "$mfg_dir/runs/gate-C03-final"
python3 scripts/native-pipeline.py check "$mfg_dir/mechanical/gate-C03-final.json"
python3 "$mfg_dir/electrical/verify.py"
python3 "$mfg_dir/electrical/negative_controls.py"
python3 "$mfg_dir/qualification/freeze_candidate.py" \
  --run "$mfg_dir/runs/gate-C03-final" \
  --scene "$mfg_dir/runs/mechanics-C03/steps/build/attempt-0001/model.blend" \
  --travel-run "$mfg_dir/runs/travel-C03" \
  --destination "$mfg_dir/qualification/NEW-CANDIDATE"
python3 "$mfg_dir/qualification/evidence_gate.py" \
  --snapshot "$mfg_dir/qualification/C03/design-snapshot.json" \
  --records "$mfg_dir/qualification/C03/bench-records.json" \
  --out "$mfg_dir/qualification/C03/assessment-NEW.json"
```

The freeze helper is hardcoded to the original host and C03/E02 inputs; inspect/adapt
it before another project. It is not a release-record editor. The shown C03 assessment
returns exit 1 and `INCOMPLETE_MANUFACTURING_EVIDENCE`; exit 0 of the assessor means
`COMPLETE_FOR_DECLARED_PILOT_SCOPE` only. Malformed input is an error, not an incomplete pass.
Replay uses the Python `validate_assessment(root, report)` function, not a separate CLI.
Electrical `--report` is optional and creates a new file inside its electrical directory.
Electrical checks also require the pinned local `mesh_inventory` from `authority.json`.

For changed qualification code, propose the existing suite:
```bash
python3 -m unittest discover -s builds/reference-keyboard/manufacturing/qualification -p 'test_*.py' -v
```
Use electrical verification plus its negative controls for changed electrical logic;
use `python3 -m unittest discover -s tests/production-gate` only for affected gate code.
Prime owns knowledge publication/route checks. Do not rebuild products or firmware
to recover a lost terminal or obtain a newer timestamp.

## 9. Blank closure table and revision handoff

Copy into a new candidate record. Empty cells mean no evidence; fill only from real records.
Keep requirement values in the approved contract.

| Claim / prerequisite | Source revision + SHA | Specimen / configuration / lot | Raw evidence + conditions | Reviewer / date / result |
|---|---|---|---|---|
| Factory mating interface and full stroke | | | | |
| Cap installation, retention and service wear | | | | |
| Knob axial/torsional retention | | | | |
| Joint strength and assembly torque | | | | |
| Guides, supports and acrylic assembly/process | | | | |
| Schematic ERC and routed-PCB DRC | | | | |
| Linked target firmware and control events | | | | |
| USB power, RGB headroom and thermal behavior | | | | |
| Pilot assessment, replay and engineering decision | | | | |

A receiver, screw, process, PCB or firmware change invalidates affected evidence.
Reuse other evidence only with explicit dependency equivalence. Bind media to its rendered
scene: Revision-B media remains historical after C03 geometry.
C03 engineering captures do not establish a new animation, GLB or marketing approval.
The [public note][public-build] identifies omitted runs, archives and manufacturer PDFs.
Commands needing local inputs cannot run from a fresh public checkout; never fabricate substitutes.

[handoff]: ../../builds/reference-keyboard/manufacturing/README.md
[lifecycle]: native-agent-iteration.md
[mechanical]: ../../builds/reference-keyboard/manufacturing/mechanical-requirements.json
[led-source]: ../../builds/reference-keyboard/manufacturing/electrical/E02-led-source-evidence.json
[travel]: ../../builds/reference-keyboard/manufacturing/qualification/travel_maximum.py
[bench]: ../../builds/reference-keyboard/manufacturing/qualification/BENCH-PROCEDURE.md
[electrical-authority]: ../../builds/reference-keyboard/manufacturing/electrical/authority.json
[electrical-check]: ../../builds/reference-keyboard/manufacturing/electrical/verify.py
[electrical-negative]: ../../builds/reference-keyboard/manufacturing/electrical/negative_controls.py
[power]: ../../builds/reference-keyboard/manufacturing/electrical/power-budget.json
[electrical-status]: ../../builds/reference-keyboard/manufacturing/electrical/status.json
[specimens]: ../../builds/reference-keyboard/manufacturing/coupons/contract.json
[requirements]: ../../builds/reference-keyboard/manufacturing/qualification/requirements.json
[freeze]: ../../builds/reference-keyboard/manufacturing/qualification/freeze_candidate.py
[evidence-io]: ../../builds/reference-keyboard/manufacturing/qualification/evidence_io.py
[record-checks]: ../../builds/reference-keyboard/manufacturing/qualification/record_checks.py
[assessment-code]: ../../builds/reference-keyboard/manufacturing/qualification/evidence_gate.py
[qualification-tests]: ../../builds/reference-keyboard/manufacturing/qualification/test_evidence_gate.py
[public-build]: ../../builds/reference-keyboard/README.md
