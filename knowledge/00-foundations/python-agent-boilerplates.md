---
name: python-agent-boilerplates
domain: foundations
blender_target: "5.2 LTS"
compat: "Per-module; contract results apply to the stated runtime"
audience: ai-agent-bpy
description: Inspectable Python boilerplate library for Blender AI agents; registry generated from disk, with per-module API contracts and explicit qualification limits.
loads_with: [bpy-scripting-core, blender-version-matrix, agent-workflow-loop]
tags: [python, bpy, boilerplate, bmesh, geometry-nodes, pbr-materials, rigging, animation, rendering, physics, cad, dfam, robotics]
id: python-agent-boilerplates
title: "Python Agent Boilerplates for Blender 5.2 LTS (Complete Catalogue)"
when: [boilerplate-registry, find-bp-module, standards-leads, headless-boilerplate]
trust_tier: draft
sources_checked: 2026-10-13
---
# Python Agent Boilerplates for Blender 5.2 LTS (Complete Catalogue)

## Purpose

Index the inspectable boilerplate library that agents copy from: a registry generated from disk (40 modules on 2026-10-13) plus the standards and literature leads behind each module, flagged as leads, not certifications.

## When to Use / When NOT

- ALLOWED: locating which `scripts/boilerplates/**/bp_*.py` module covers a task before writing bpy from scratch
- ALLOWED: regenerating or auditing the registry (`run_all_boilerplate_tests.py --list`)
- NOT ALLOWED: claiming a module is standards-compliant or print/manufacture-ready because it is listed here — use the module's contract test and the production gate instead
- NOT ALLOWED: evaluated-mesh, Action-slot, GN-binding and camera contracts — use `native-api-contracts` instead
- NOT ALLOWED: general bpy rules — use `bpy-scripting-core` instead

## Core Knowledge Content


A copy-pasteable library of modular Python boilerplates for autonomous AI agents executing `bpy` scripts headlessly (`--background`). **The module count and list are not written by hand here** — they are generated from disk (see §1), because three hand-maintained lists in this repo previously disagreed with each other (30 on disk vs 26 here vs 17 in `INDEX.md`).

The project targets Blender 5.2.0 LTS and prefers data APIs. A module's presence
in this registry does not certify its API compatibility, platform coverage or
engineering standards. Read its current catalog caution and run the relevant
contract on the intended interpreter. Operators and destructive helpers still
require caller-owned scope. Bibliographic entries below are provenance leads;
their editions and applicability require claim-specific verification.

For evaluated mesh lifetime, assigned Action slots, Geometry Nodes binding and
camera-depth screening, start with [native API contracts](native-api-contracts.md)
and the executed evidence in `plans/260917-blender-auto-research/reports/`.

---

### 1. Boilerplate Registry (generated — do not hand-edit)

**Single source of truth = the files on disk.** Regenerate this table with: <!-- ease:source S2 anchor="--list globs scripts/boilerplates/**/bp_*.py" -->

```bash
python3 scripts/boilerplates/run_all_boilerplate_tests.py --list
```

That prints JSON (`{root, count, modules:[{path, doc}]}`) built by globbing
`scripts/boilerplates/**/bp_*.py` and reading each module's first docstring line without
importing `bpy`. The same runner without `--list` executes every module in a fresh
headless Blender and passes it only if its last stdout line is `AGENT_OK ...`.

Regenerated 2026-10-13 from the command above — **40 modules** (the 2026-09-06 list had 30; ten were added since: `bp_mating_contract`, `bp_parametric_contract` and eight `character_creature/` modules). <!-- ease:source S1 anchor="count: 40 on 2026-10-13" -->
(`knowledge/INDEX.md` carries its own summary line and bullet list; keeping those in sync
with this generated table is the INDEX owner's job, not this file's.)

| Module (`scripts/boilerplates/`) | First docstring line |
|---|---|
| `bp_animation.py` | bp_animation.py — Animation & Driver Boilerplate for Blender 5.2+. |
| `bp_bmesh_cad.py` | bp_bmesh_cad.py — BMesh & Non-Destructive CAD Modeling Boilerplate. |
| `bp_cad_robotics.py` | bp_cad_robotics.py — Precision CAD & Robotics Tooling Boilerplate. |
| `bp_core.py` | bp_core.py — Core Foundation Boilerplate for Blender 5.2+ bpy Scripts. |
| `bp_geonodes.py` | bp_geonodes.py — Procedural Geometry Nodes Boilerplate for Blender 5.2+. |
| `bp_materials_pbr.py` | bp_materials_pbr.py — Physically Based Shading & Node Boilerplate. |
| `bp_physics.py` | bp_physics.py — Rigid Body Simulation & Point Cache Boilerplate. |
| `bp_render_camera.py` | bp_render_camera.py — Production Rendering, Camera & Lighting Boilerplate. |
| `bp_rigging.py` | bp_rigging.py — Armature & Mechanical/Character Rigging Boilerplate. |
| `cad_mechanics/bp_assembly_collision_audit.py` | bp_assembly_collision_audit.py — Assembly Collision Auditing & Kinematic Staging Boilerplate. |
| `cad_mechanics/bp_ball_bearing.py` | bp_ball_bearing.py — Deep Groove Ball Bearing Generator Boilerplate. |
| `cad_mechanics/bp_cable_dragchain.py` | bp_cable_dragchain.py — Parametric Energy Drag Chain & Articulated Cable Carrier Boilerplate. |
| `cad_mechanics/bp_connectors_extended.py` | bp_connectors_extended.py — Extended Industrial Connectors, Flanges & Breather Vents Boilerplate. |
| `cad_mechanics/bp_connectors_wiring.py` | bp_connectors_wiring.py — Industrial Connectors, Panel Cutouts & Wire Harness Boilerplate. |
| `cad_mechanics/bp_fasteners_iso.py` | bp_fasteners_iso.py — Standard Metric Fastener Generator Boilerplate. |
| `cad_mechanics/bp_flexures.py` | bp_flexures.py — Compliant Mechanism Notch Flexure Generator Boilerplate. |
| `cad_mechanics/bp_involute_gear.py` | bp_involute_gear.py — Parametric Involute Spur & Helical Gear Boilerplate. |
| `cad_mechanics/bp_oring_glands.py` | bp_oring_glands.py — AS568 & ISO 3601 O-Ring & Gland Generator Boilerplate. |
| `cad_mechanics/bp_shaft_couplings.py` | bp_shaft_couplings.py — Transmission Shaft Keyways & Couplings Boilerplate. |
| `cad_mechanics/bp_springs.py` | bp_springs.py — Helical Springs & Belleville Disc Washer Boilerplate. |
| `dfam_3dprint/bp_insert_boss.py` | bp_insert_boss.py — Heat-Set Threaded Insert Boss Generator Boilerplate. |
| `dfam_3dprint/bp_snap_fits.py` | bp_snap_fits.py — Cantilever Snap-Fit Joint Generator Boilerplate. |
| `dfam_3dprint/bp_teardrop_holes.py` | bp_teardrop_holes.py — Self-Supporting Teardrop Hole Cutter Boilerplate. |
| `geometry_nodes/bp_gn_cables.py` | bp_gn_cables.py — Procedural Catenary Hanging Cable Node Tree Boilerplate. |
| `geometry_nodes/bp_gn_pipe_flange.py` | bp_gn_pipe_flange.py — Parametric Pipe Flange Geometry Node Tree Boilerplate. |
| `materials_shading/bp_mat_metals.py` | bp_mat_metals.py — Physically Based Metals & Anisotropy Boilerplate. |
| `materials_shading/bp_mat_thinfilm.py` | bp_mat_thinfilm.py — Wave Interference & Thin-Film Iridescence Boilerplate. |
| `pipeline_render/bp_cam_autoframing.py` | bp_cam_autoframing.py — Camera Bounding-Box Frustum Auto-Framing Boilerplate. |
| `pipeline_render/bp_export_pipeline.py` | bp_export_pipeline.py — Headless Interchange & Export Pipeline Boilerplate. |
| `rigging_kinematics/bp_rig_robot_arm.py` | bp_rig_robot_arm.py — 6-DOF Industrial Robot Arm Kinematic Rig Boilerplate. |
| `bp_mating_contract.py` | Parametric mating contract boilerplate for Blender 5.2 LTS. |
| `bp_parametric_contract.py` | Small stdlib-only contract for Blender-native parametric model intent/… |
| `character_creature/bp_biped_locomotion.py` | bp_biped_locomotion.py — Procedural Biomechanical Walk Cycle Generator… |
| `character_creature/bp_creature_digitigrade.py` | bp_creature_digitigrade.py — Procedural Digitigrade Creature Hindlimb… |
| `character_creature/bp_facs_blendshapes.py` | bp_facs_blendshapes.py — FACS 52 ARKit Facial Blendshapes & Corrective… |
| `character_creature/bp_fur_hair_shader.py` | bp_fur_hair_shader.py — Melanin-Based Biochemical Hair & Fur Shader… |
| `character_creature/bp_hair_curves_gen.py` | bp_hair_curves_gen.py — Modern Blender 5.2 Hair Curves Generator & Geo… |
| `character_creature/bp_humanoid_basemesh.py` | bp_humanoid_basemesh.py — Procedural Humanoid PROPORTION PROXY Generat… |
| `character_creature/bp_humanoid_rig_ikfk.py` | bp_humanoid_rig_ikfk.py — Procedural Humanoid IK/FK Armature & Deforma… |
| `character_creature/bp_skin_sss_shader.py` | bp_skin_sss_shader.py — Production Physically-Based Human Skin Shader… |

---

### 2. Standards & Academic Citation Matrix

| Boilerplate Module | Primary Standards & Formal Literature Citations |
|---|---|
| `bp_involute_gear.py` | DIN 3960:1987; AGMA 2001-D04; ISO 1328-1:2013; Dudley's Gear Handbook (2012). |
| `bp_fasteners_iso.py` | ISO 4014:2011; ISO 4032:2012; ISO 7089:2000; ISO 4762:2004. |
| `bp_oring_glands.py` | SAE AS568D:2023; ISO 3601-2:2016; Parker O-Ring Handbook (ORD 5700). |
| `bp_ball_bearing.py` | DIN 625-1:2011; ISO 15:2017; ISO 281:2007 (Dynamic Load Ratings). |
| `bp_springs.py` | DIN 2093:2013; EN 13906-1:2013; Shigley's Mechanical Engineering Design (10th ed.). |
| `bp_flexures.py` | Paros & Weisbord (1965), *Machine Design*; Howell (2001), *Compliant Mechanisms*. |
| `bp_shaft_couplings.py`| DIN 6885-1:1993; DIN 5480-1:2006; ANSI B17.1. |
| `bp_insert_boss.py` | ISO 16903:2015 (**suspect: appears to be an LNG standard, not an insert standard**); SPI AN-110; ASTM D638-14. |
| `bp_teardrop_holes.py` | ISO/ASTM 52910:2018; ASTM F2792; Gibson, Rosen & Stucker (2015). |
| `bp_snap_fits.py` | Bayer MaterialScience (2004), *Snap-Fit Joints for Plastics*; ASTM D638. |
| `bp_gn_pipe_flange.py` | ASME B16.5-2020; Blender 5.2 LTS Python API Reference. |
| `bp_gn_cables.py` | Irvine (1981), *Cable Structures*; Meriam & Kraige (2012), *Engineering Mechanics: Statics*. |
| `bp_mat_metals.py` | OpenPBR Surface (Academy Software Foundation; spec page at capture reads v1.1.1, 2026-04-17); Walter et al. (2007); Burley (2012). |
| `bp_mat_thinfilm.py` | Born & Wolf (1999), *Principles of Optics*; Belcour & Barla (2017), *ACM TOG*. |
| `bp_rig_robot_arm.py` | Denavit & Hartenberg (1955), *ASME J. Appl. Mech.*; Craig (2005); ISO 9787:2013. |
| `bp_cam_autoframing.py`| Hartley & Zisserman (2004), *Multiple View Geometry in Computer Vision*. |
| `bp_export_pipeline.py`| ISO/IEC 12113:2022 (glTF 2.0); ISO/ASTM 52915:2020 (**AMF**, not 3MF/STL). |
| `bp_cad_robotics.py` | Eberly (2002), *Polyhedral Mass Properties*; ASME Y14.5-2018. |
<!-- ease:source S3 anchor="OpenPBR Surface spec page header: 'OpenPBR Surface specification v1.1.1, 2026-04-17'" -->
<!-- ease:source UNVERIFIED reason="ISO/ASTM 52915:2020 is the Additive Manufacturing File Format (AMF) v1.2 per publisher listings found by web search 2026-10-13 (not frozen); it is not the 3MF spec" -->
<!-- ease:source UNVERIFIED reason="ISO 16903:2015 appears to be the LNG standard 'Petroleum and natural gas industries - Characteristics of LNG, influencing the design, and material selection' (web search 2026-10-13, publisher listing not frozen); SPI AN-110 not located" -->
<!-- ease:source UNVERIFIED reason="standard numbers/editions and books listed in this matrix are provenance leads; publisher pages (iso.org, din.de, ansi) answered with a bot challenge or are paywalled, so none was frozen" -->

## Failure Modes (Mandatory)

- **Registry table disagrees with disk** — cause: hand-maintained module lists drift (30 on disk vs 26 here vs 17 in INDEX.md in 2026-09; 40 on disk by 2026-10-13) — fix: regenerate with `--list`, never hand-edit counts
- **Module treated as standards-certified** — cause: the citation matrix lists provenance leads, some wrong or unverifiable (ISO 16903:2015 appears to be an LNG standard; ISO/ASTM 52915:2020 is AMF) — fix: verify the edition and applicability per claim before relying on it
- **Boilerplate imports fail or silently misbehave on 5.2** — cause: module written for an older API name (see `blender-version-matrix`) — fix: run its contract test in a fresh headless Blender and require a final `AGENT_OK` line
- **Bare `hasattr(bpy.ops...)` capability check in copied code** — cause: always True on `bpy.ops` — fix: `name in dir(bpy.ops.mod)`

## Sources

- [S1] Output of `python3 scripts/boilerplates/run_all_boilerplate_tests.py --list` on 2026-10-13 (count 40) — knowledge/_evidence/kb-261013/w1-boilerplate-list.json — captured 2026-10-13 — sha256 a03981e84f9b7c8a77f8bcdd11c0e4b9464be4fb3fcf5cf45e7c81f0559586dd
- [S2] Repo: scripts/boilerplates/run_all_boilerplate_tests.py (--list generates the registry) — scripts/boilerplates/run_all_boilerplate_tests.py — captured 2026-10-13 — sha256 bce4755c515b1b9028e8a52c7c8d84eb86e6155e1a578e58db6424dee30e3f9f
- [S3] OpenPBR Surface specification (Academy Software Foundation) — https://academysoftwarefoundation.github.io/OpenPBR/ (frozen copy: knowledge/_evidence/kb-261013/w1-openpbr-spec.html) — captured 2026-10-13 — sha256 3bec2edd0abd1f6a626777783f945825d771caf680c2e1e19abe7c3329e1595a
- [S4] Repo module: native-api-contracts (contract-level evidence for the helpers) — knowledge/00-foundations/native-api-contracts.md — captured 2026-10-13 — sha256 0a6abb42733af1ec4309affe49cb79a9f0c93e1c5b0e0dc1412ebbd1d1aa24d9
