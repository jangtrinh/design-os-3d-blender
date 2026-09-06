# Arm — print plates and step-by-step assembly

![38 fit-prototype parts on five print plates](../../docs/media/robot-arm-print-plates.png)

**38 separate fit-prototype parts on 5 plates: 32 PETG + 6 TPU.** Geometry comes from the latest live Arm task revision, not the older baseline STL package. Three optional tool-library pieces are included.

**Not released for a 250 g loaded run or manufacture.** These files support slicing and fit trials. Current wrist torque margin, thin/trimmed sections, actuator adapters, retentions and physical assembly/tool access remain unresolved. Closed meshes and the assembly movie do not establish those properties.

## Open

- `arm-print-plates.blend` → scene `A3-Print-plates`: all five arranged plates, object IDs and materials.
- `plates/plate-01-PETG.3mf` through `plate-04-PETG.3mf`; `plate-05-TPU.3mf`: one geometry package per plate, with separate named objects in millimetres. STL plate alternatives are alongside them.
- `parts/`: 38 individual binary STLs, identified P01–P38. Their orientation is the chosen printing candidate; the plate may add a 90-degree in-plane turn. `parts-list.csv` maps ID → object → plate → material → dimensions.
- `arm-step-assembly.blend` → scene `A3-Step-assembly`: editable 67-step assembly, frames 25–1429 at 24 fps. `video/arm-step-by-step.mp4` is the clean movie, without subtitles. `assembly-steps.csv` maps film times to source components and print IDs.
- `arm-fit-print-kit.zip`: plate packages, individual pieces and setup/reference information. No machine-specific G-code.

## Plate setup

| Plate | Material | Part instances |
|---|---|---:|
| 01 | PETG | 3 |
| 02 | PETG | 5 |
| 03 | PETG | 10 |
| 04 | PETG | 14 |
| 05 | TPU | 6 |

Assumed usable bed: **220 × 220 mm**, 7 mm edge margin, at least 8 mm rectangular part clearance. PETG and TPU are separated. Check the actual printer exclusion zones and any brim/support footprints before slicing; the geometric packing does not reserve a validated brim or printhead-clearance envelope. Print all objects by layer, not sequential by-object mode.

Starting fit-study assumptions retained from the Arm project: 0.4 mm nozzle, 0.2 mm layers, six perimeters for PETG structural parts. Use the actual filament/printer profile for temperatures, cooling and extrusion. Material label describes the intended polymer, not a machine preset. Matte appearance depends on the chosen filament and surface process.

Forks lie with the broad bridge against the bed. Plates, cheeks and jaws use broad-face candidates; cavities and print support access must be inspected. Wrist cassette, gripper cradle, split collet and thin cosmetic features need close slicing review. `reports/plates-manifest.json` records the selected local-up axis, estimated bed contact and downward-facing area for each piece. Those are orientation screens, not generated supports. Do not assume a part marked support-review=false is universally support-free.

Use fit coupons and inspect tool/fastener holes before printing a full functional set. No shrinkage/clearance compensation has been invented or silently applied to the source dimensions.

## What the movie assembles

Base → shoulder/lower-fork subassembly → elbow/upper-fork subassembly → wrist/roll/dock → gripper → service/cosmetic parts. Large-joint modules are presented off-arm before placement; nuts precede their clamping screws. Each modeled screw head and shaft remains one visual fastener operation. Servo cases and their assigned preassembled output/adaptor meshes travel rigidly together during installation; their operational rotation is not an assembly separation. Bearings, servos and metal carriers retain their source geometry.

The film accounts for all **402 Arm component meshes**, including 35 installed prints. The three alternate-tool prints are on the plates and in the parts list; they are not additional parts of the installed gripper. Servo visual shells and screw head/shaft meshes are representation pieces, not separate purchase items.

Actual nonprinted content: six actuator cases, four large-servo output visual meshes, eight small output/idler adapter envelopes, five bearings, fourteen machined metal components, two electronics envelopes and 328 hardware meshes. See `reports/source-freeze.json` and `reports/live-inventory.json`; these counts are a component census, not a procurement BOM. **Do not print metal carriers, journals or servo internals in polymer as substitutes.**

The sequence shows proposed order and placement, not validated insertion/tool trajectories. Missing retention remains missing: yaw-servo case retention, electronics shell/lid, skirt, fascia, wrist cross-bridge, roll cradle and vent cover need engineering work. Electronics objects reserve space rather than identify an actual controller. No invented screws are added to disguise these gaps.

## Evidence

`reports/source-freeze.json` binds a preserved dirty-session checkpoint and frozen geometry. Original Arm files were not overwritten. `reports/mesh-audit.json` records single connected shells, edge closure, winding and positive volume, plus a limited local-wall ray screen. Very short ray distances at holes/fillets or clearance cuts need local investigation; the screen is not an exhaustive minimum-wall or strength test.

`reports/export-check.json` reads actual STL bytes, validates edge incidence/volume and checks plate placement/material segregation. It also records each 3MF hash. Core 3MF structure follows the [3MF Consortium specification](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md); these packages contain geometry/units, without slicer-specific profiles/supports.

`reports/assembly-timeline.json` stores per-object source/final transforms and assembly intervals; `reports/camera-check.json` records endpoint framing. Transfer-camera refinement includes both separated and seated positions. Final saved-file and independent findings are recorded in `reports/`.

Open physical gates: exact spline/idler hardware, screw engagement and tool access, bearing seats, cable loops, printed section strength/creep, final base anchoring and instrumented multi-minute load/thermal trials. User requirement remains 250 g; it has not been reduced.

The ZIP includes the two editable Blender files, the movie, plate/part exports, CSV lists and compact check reports. Full dirty-session/frozen checkpoints and raw render frames are retained in the project build folder rather than duplicated into the ZIP.
