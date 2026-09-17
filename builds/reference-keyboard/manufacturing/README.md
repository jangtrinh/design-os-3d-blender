# CK-001 manufacturing development: C03 mechanics / E02 electrical

Current state: **engineering candidate, not released for manufacture**.

Repository scope: source, contracts and small logical reports are versioned.
Paths under `runs/`, `delivery/` and `qualification/C03/` below identify local
historical artifacts; those models, captured measurements and images are not part
of the public source checkout. Build-specific scripts keep the original host and
input guards and must be reviewed/adapted for a new environment. For reusable
practice use `knowledge/60-pipeline/manufacturing-evidence-workflow.md` from the
repository root.
The physical record set contains **zero observations against 16 required pilot
metrics**. The independent digital prerequisites still missing are the factory
switch interface, schematic ERC, routed-PCB DRC, target firmware build and the
physical assembly/process qualification.

## Current corrections and evidence

| Area | Current result | Evidence |
|---|---|---|
| Structural attachment | Thirty structural adhesive joints replaced by lower fasteners and daughterboard clamps; five knobs have set screws | C02 mechanical inspection: 46 checks; `runs/mechanics-C02/attempt-0001/inspect.json` |
| Lower screw seats | Thirty cylindrical extra-low-head L4 screws; D2.5 x 0.5 seats, 2.5 mm nominal post engagement, 0.5 mm pilot reserve | C02 inspection and manufacturer-source report |
| Full-stroke key clearance | 57 one-unit caps changed from 4.5 to 5.0 mm skirt-start datum; existing guided wide key retained. All 58 caps clear at eight sampled travels through 3.2 mm | `runs/travel-C03/steps/travel/attempt-0001/maximum-travel.json` |
| Acrylic retention | Four OD8.8 / ID5.8 / H1.6 collars occupy the former vertical gap and contact surviving shoulder sectors | `runs/mechanics-C03/steps/build/attempt-0001/changes.json` |
| Current representative geometry | All 12 families pass the gate and STL roundtrip on the same C03 scene | `runs/gate-C03-final/steps/gate/attempt-0001/gate-report.json` |
| Electrical polarity | Exact common-anode A01 LED selected; SW/common and CS/cathode mapping corrected | `electrical/verification-E02-final.json`: 37 logical checks; `negative-controls-E02-final.json`: 7 fault controls |
| Process characterization tooling | 16 native fit specimens with separate STL files and digital gate evidence | `runs/coupons-C02/steps/gate/attempt-0001/` |
| Physical evidence handling | Snapshot, calibrated conditions, sample chronology, raw-record hashes and uncertainty checks | `qualification/C03/assessment.json`; 11 checker unit tests passed |

Current saved assembly:

`runs/mechanics-C03/steps/build/attempt-0001/model.blend`

Scene SHA-256:
`2961a5afbc13dc04bb8841949f69db9e0c319cabf64bedb640cf9d8d5985ca3d`

The C03 integration preserves 515 existing non-1U mesh geometries and transforms.
Its new collars have 0.199999 mm minimum spacer clearance and 0.406245 mm minimum
knob clearance in the nominal mesh. Their support is partial shoulder contact,
not a uniform annular bearing. Thickness/shims, bearing stress, acrylic creep and
thermal expansion still require first-article engineering.

## Electrical limitation that must not be hidden

The E01 common-cathode choice was incompatible with the selected driver topology.
The historical E01 host checks did not test that predicate; they are superseded,
not retrospectively marked correct. E01 files remain in the electrical history.

E02 fixes polarity and verifies source/math consistency. It does **not** establish
guaranteed RGB voltage headroom: the low-current engineering estimate is +0.69391 V,
while directly applying the published full-rated voltage drops gives -0.47523 V.
Those are two different screening assumptions, not measured circuit performance.
Actual LED voltage, driver drop, supply regulation/ripple and temperature remain
board-test items. Three modeled status indicators are still electrically unwired.

The portable C core was host-tested and compiled into an ARMv6-M relocatable object.
It is not linked/bootable USB firmware. E02 did not repeat the unchanged core build.
The logical schematic is explicitly non-ERC; no routed PCB or fabrication Gerbers
are represented as complete.

## Visual and exchange scope

`runs/C03-engineering-views/` contains three actual native 1920 x 1080 engineering
captures: assembly, cap receiver and collar/spacer. Temporary neutral materials
make the geometry inspectable; these views omit the finished legends and RGB
presentation. They are not a new marketing-fidelity approval.

Revision-B Full HD media, animation and GLB in `../delivery/r02/` remain historical
Revision-B outputs. They do not depict or qualify C03. The current C03 handoff is
the native engineering scene, representative STL files, electrical sources,
process specimens and evidence; no new C03 animation/GLB roundtrip is claimed.

## Remaining work to obtain manufacturing evidence

Measure the selected factory switch's full housing/dust structure before trying
the custom boss. Check the real actuator only at its own measured stop; never
force a shorter-stroke part to 3.2 mm. Select the receiver/material/process from
the fit ladder using measured installation, retention and wear results.

Complete schematic/footprint integration, routing/DRC and target firmware. Then
perform actual assembly, joint-strength, knob/guide retention, USB/current and
thermal tests using `qualification/BENCH-PROCEDURE.md`. Choose and freeze each
specimen's hardware/process configuration before recording data. A passing file
checker cannot substitute for these operations or authenticate a laboratory.

## Preserved failures and checker improvement

The C01 maximum-travel report correctly retains 57 cap/cover contacts at 3.2 mm.
C03 repairs those contacts without widening the mating cover or changing the
receiver. A 6.0 mm overtravel control still detects collision.

The first C03 build completed and saved its source-bound model, but its pipeline
declaration incorrectly required a SHA string as a numeric postcondition. That
failed journal is preserved. Subsequent verification consumed the existing model;
the geometry build was not repeated to erase the failure.

The first C03 gate could not sample the finely faceted collar because every
triangle was below its 0.3 mm² area filter. Checker 1.0.2 retains the original
filter whenever eligible faces exist and otherwise samples all positive-area
faces with the same opposing-normal predicate. The thick collar passes; thin,
empty and degenerate controls fail. All 29 production-gate regression tests pass.
The final C03 gate uses that checker on the unchanged saved scene.
