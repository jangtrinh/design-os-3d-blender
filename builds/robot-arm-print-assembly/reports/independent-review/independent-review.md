# Independent print-package and assembly review

## Reviewed snapshots

- Corrected assembly candidate: `arm-step-assembly-corrected.blend`, SHA-256 `20e27bc6022251d1a07ff6cad86098f11aade295178e9e2af2adfc83b69495ba`.
- Plate scene: `arm-print-plates.blend`, SHA-256 `4370c7122160247c3a35f4e16ab27a2649282f93daf2c59c17bf19f6d1947675`.
- Frozen source: `frozen-source.blend`, SHA-256 `75b716e552eb1905d725d80c2d36c46fd7916f64d81ce1b78e57bd68f2b9f9bc`.
- Independent outputs: `package-check.json`, `stl-self-overlap-check.json`, and `assembly-check.json` in this folder. Checkers read reviewed assets without saving them.

## Printable-package result

The binary package passes the requested inventory and geometry checks:

- Exactly 38 individual binary STLs are present and match the manifest filenames and SHA-256 values: 32 PETG and 6 TPU. Their total is 183,678 triangles.
- Every part STL has a valid binary byte count, finite nondegenerate triangles, positive signed volume, and exactly two incident faces per undirected edge. The five combined plate STLs pass the same checks.
- A Blender BVH screen on the actual STL triangles found zero overlapping nonadjacent triangle pairs across all 38 parts. Pairs sharing a mesh vertex were classified as adjacent and excluded. This screen does not test slicer repair, minimum feature size, support strategy, tolerance or strength.
- Five 3MF archives declare `unit="millimeter"`. Their build lists cover all 38 unique part IDs exactly once; each resource triangle count matches its individual STL. Plates 1–4 contain only PETG and plate 5 contains only the six TPU pads.
- All 3MF vertices remain within X/Y 7–213 mm and Z >= -0.0011 mm. Plate membership is 3, 5, 10, 14 and 6 objects, totaling 38. The placement therefore preserves the stated 7 mm bed-edge margin on a 220 mm square bed.

The frozen census is also consistent: 38 printable meshes were selected while 14 machined-metal meshes, 6 actuator bodies, 4 actuator visuals, 8 purchased adapters, 5 bearings, 2 electronics envelopes and 328 hardware meshes were excluded from print exports.

## Assembly result

The corrected candidate passes the independent saved-file checker:

- 402 source assembly objects appear exactly once across 67 events and are all hidden at frame 1, visible at frame 1429, and returned to their recorded final transforms.
- Final matrices match the directly opened frozen source exactly. The maximum saved-scene versus timeline matrix-element residue is `1.1920928955078125e-7`. All 402 mesh digests match their frozen counterparts.
- All 146 screw head/thread-envelope pairs share group, step and interval and have zero relative displacement error at every integer frame of their arrival.
- Thirty-four explicit receiver-order checks pass: large-servo mount-foot nuts, lower/upper cassette nuts, wrist cage nuts, tool-lock nuts, hand-adapter nuts, hand-case nuts and fixed-jaw nuts all arrive before their corresponding fasteners.
- Yaw, shoulder, elbow, roll and gripper servo/output preparation groups preserve rigid relative motion at every arrival frame in the corrected candidate. `servo-motion-repair.json` binds the correction to the old and candidate hashes and limits visible changes to 37 arrival frames.
- The refined camera code checks all 67 seated endpoints and every visible object during chapter-transfer frames `transfer_start + 8` through `transfer_end`; the preview endpoints are legible and the final frame is complete.

## Concrete remaining issues

1. The named `arm-step-assembly.blend` reviewed during discovery still has SHA-256 `c3861ff2a9768b22b43c2fccdfeb5716c0aeff1d316ca0f586bf0c9574c25071` and fails rigid shoulder/elbow output arrival by as much as 110 mm relative displacement. The passing artifact is the separately named corrected candidate. Delivery must promote or explicitly select the candidate and ensure rendered replacement frames come from its hash.
2. The source models no retention for the wrist cross-bridge, roll cradle or vent cover. Event wrist/7 groups the cross-bridge with pivot screws, but those screw axes attach the cheeks/hubs; they do not establish bridge retention. The yaw skirt, shoulder fascia, electronics shell/lid and yaw-servo body likewise arrive without modeled retention. The animation is an authored placement overview for these pieces.
3. The three alternate-tool prints are present in the package: P20 pen adapter, P21 split collet and P29 universal blank. They carry `tool_library=true` and are intentionally excluded from the 402-object/67-event arm assembly, so the movie does not demonstrate alternate-head assembly or interchange.
4. The animation verifies endpoint identity and component ordering, not collision-free insertion or tool access. This is particularly relevant to the dual-bearing carrier sequence and captive receivers after neighboring parts obscure them; the timeline itself discloses this limit.
5. Final Metal-frame rendering and encoded no-subtitle video were still in progress. Static CPU endpoints were inspected; final replacement-frame provenance, encode completeness and playback were not available in this review.

Status: DONE_WITH_CONCERNS

Summary: The corrected candidate has 38 valid print exports on five millimetre-scale, material-separated 3MF plates and a 67-event assembly that returns all 402 components to frozen-source geometry and transforms. Raw STL closure and a nonadjacent self-overlap screen pass.

Concerns/Blockers: The corrected candidate has not yet replaced the failing named assembly blend, several placed components have no modeled retention, alternate tools are exported but omitted from the assembly movie, and final encoded media remains unreviewed. The package remains a fit prototype and does not resolve the established 250 g multi-minute release blockers.
