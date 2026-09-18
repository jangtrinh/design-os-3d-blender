# DC-01 native engineering demo

Open `index.html` in a browser. The page and media work offline. The MP4 has no audio.

## Included deliverables

| File | Content |
|---|---|
| `dc01-native-animatic.mp4` | 1,170 evaluated Blender timeline frames at30fps; 589 distinct native FullHD renders and 581 exact-state stationary reuses, lasting39seconds |
| `native/dc01-demo.blend` | Editable saved animation with the assembly at frame1 |
| `native/dc01-assembly.blend` | Full H13 assembly with all26 routed base connections |
| `native/dc01-engineering.blend` | Frozen I06 mechanical/electronic/control assembly before harness |
| `DC01-P03-print-kit.zip`, `print/` |18 STL parts, two core3MF plates, native print bake and source-bound checks |
| `electronics/` | Editable KiCad schematic/PCB and local libraries, BOMs, pin/wire maps, actual Gerber/Excellon candidates and native ERC/DRC records |
| `reports/` | Original revision-bound reports for geometry, wiring, print, animation and video |

## What the demonstration establishes

I06 has18 passing printable-part forms and an explicit per-part coverage audit. The exported P03 parts preserve the native source geometry under declared axis rotations. Both core3MF files were independently reopened; all triangles match the gated STL files.17 PETG parts and one TPU diaphragm are separated by material.

H13 has26 complete base connections comprising27 wire legs because the positive pack lead is split at the fuse. Reopened native curves were checked against252 static obstacles and every other installed wire. Independent curvature extrema and both sides of curve joins retain the3mm minimum-radius requirement. These are static geometry results, not a material or service-flexing test.

The native animation preserves1461 original mesh/curve basis geometries and uses29 catalog groups. Many mesh objects are copper, pads or other subdivisions of one physical part. The retimed animation preserves the recorded source anchors, including the assembled and returned states. All1,170 timeline frames pass the recorded camera screen. Side screws withdraw before the upper assembly lifts. Wires are omitted during the disconnected service phase and displayed separately in the explanatory catalog.

## Fixed construction and authored behavior

Arms and ears are fixed retained cosmetic parts. The feet are integral in the lower shell. There is no powered arm/ear joint or walking mechanism. Display blinking/looking and button displacement are authored illustrations; no firmware binary, measured button force, spring return, fatigue or safe overtravel is demonstrated. Audio is unpopulated.

The exploded catalog is an explanation of the same source parts, not a qualified factory assembly path. A grouped hardware cluster and small edge-on parts are overview limitations. Dedicated detail views, when included under `stills/details/`, state their hidden and translated objects separately. Exact photographic fidelity is not accepted: exposed fasteners, the visor and sharper edge/seam transitions differ from the original concept.

## Print and electrical status

**Digital geometry/export checks: complete in the recorded scope. Physical manufacture and battery operation: BLOCKED. Physical sample count:0.**

P03 contains geometry-only3MF files, not printer profiles, supports or G-code. Follow `print/README.md`: keep scale100%, assign actual PETG/TPU profiles, inspect support/brim space and evaluate first-layer contact. The18 meshes in `print/print.blend` retain original datums; the3MF build-item translations produce the plate layouts. Do not print the source-only scene or rotate parts twice.

The custom board is a carrier for a purchased ESP32-S3 module, not custom silicon. Native KiCad A04 reports0 ERC violations and0 DRC violations, unconnected items or schematic-parity issues. Actual passive/connector selection, battery lot/polarity, charge-temperature limits, operating undervoltage behavior, lead-fuse coordination, rails/transients, closed-case temperature, firmware and RF trials remain open.13 harness endpoints remain placement/termination proposals. See `electronics/bench-validation.md` and `reports/harness/handoff.json`.

The installed raised charger screw cannot be reached by the modeled driver and must be tightened during preassembly. The source service sequence records tested sampled poses and a detected former collision. Continuous transit, physical tools, tightening torque and wiring service movement are not established.

## Source pins and reproducibility

Full assembly: `526b2ca2822be17287f49f6fd3682295e700f269b11ade47891f94b5bbe67ab9`

Native animation: `1eba240b5936eb8a9d2dde202790904a96457c3f980088417e30d9ce6e6be590`

MP4: `d1e2148f72af10047d992202f9feebf84bbc6da8a6b14e355b0753663dff003d`

`manifest.json` and `SHA256SUMS` identify the delivered bytes. From this directory, run `shasum -a256 -c SHA256SUMS`. Original reports retain their original Mac workspace paths and hashes; package copies are separately listed in the delivery manifest. Reproduction scripts remain in the project's `builds/desktop-companion` workspace; the editable Blender/CAD files are included here. The native30 frame sequence, its exact-state reuse manifest and captioned sequence are preserved in `presentation/D06/` in that workspace. They are not duplicated in this compact archive.
