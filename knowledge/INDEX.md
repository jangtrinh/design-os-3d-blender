# Blender Knowledge Foundation — INDEX

A knowledge base for an **AI agent that drives Blender through `bpy` Python**
(blender-mcp: `execute_blender_code` + `get_viewport_screenshot`), typically
headless. Written against **Blender 5.2 LTS** (July 2026), with divergences from
**4.5 LTS** called out inline.

This file is the **router**. Read it first, load only the domain files a task
actually needs. Every file is self-contained and follows the same 8-section
structure, so a file can be lifted into a Claude Skill with minimal editing.

---

## Cross-corpus task routing

This INDEX is an on-demand lookup, not a session-start read. Use [blender-knowledge-workbench](../.agents/skills/blender-knowledge-workbench/SKILL.md) for task packs spanning this KB, engineering research, portable imported concepts and inspected execution examples. Run `python3 scripts/blender-knowledge.py list` / `route <workflow-id>`. The [usage guide](../docs/blender-knowledge-workflows.md) explains provenance and limitations. `loads_with` links form cycles: keep them as optional related reads, never recursively load the whole graph. The domain table below remains a direct lookup.

## How to use this KB

### Always load first (3 files, non-negotiable)

`python-agent-boilerplates.md` is a registry, not a foundation — open it only when you need a module.

| File | Why it is mandatory |
|---|---|
| [`00-foundations/blender-version-matrix.md`](00-foundations/blender-version-matrix.md) | Your memory of `bpy` is a blend of every Blender version. This file says which strings changed and when. |
| [`00-foundations/bpy-scripting-core.md`](00-foundations/bpy-scripting-core.md) | Data API vs `bpy.ops`, context overrides, headless reality, introspection, error taxonomy. |
| [`00-foundations/agent-workflow-loop.md`](00-foundations/agent-workflow-loop.md) | How to prove a step worked before moving to the next one. |

### Then route by task

| If the task is… | Load |
|---|---|
| "make/model a shape", topology, normals, mesh repair | `10-modeling/modeling-topology.md` |
| non-destructive stack, subdiv/mirror/array/boolean | `10-modeling/modifiers.md` |
| UVs, seams, packing, texel density, lightmaps | `10-modeling/uv-unwrapping.md` |
| materials, shaders, Principled BSDF, node trees | `20-shading/materials-pbr.md` |
| textures, color space, normal maps, baking | `20-shading/texturing-baking.md` |
| lights, HDRI, exposure, studio setups | `30-lighting-render/lighting.md` |
| choosing/configuring Cycles vs EEVEE, GPU, output | `30-lighting-render/render-engines.md` |
| passes/AOVs, EXR, compositor, color management, VSE | `30-lighting-render/compositing-output.md` |
| keyframes, F-curves, easing, timing, drivers | `40-animation/animation-fcurves.md` |
| armatures, bones, IK, constraints, skinning | `40-animation/rigging-armature.md` |
| mocap import, retargeting, NLA, loops, shot staging | `40-animation/mocap-retargeting.md` |
| procedural geometry, scatter, instancing, zones | `50-procedural/geometry-nodes.md` |
| rigid body, cloth, fluid, particles, caches | `50-procedural/simulation-physics.md` |
| collections, naming, units, linking, scene scaffold | `60-pipeline/scene-organization.md` |
| export to glTF/FBX/USD/OBJ/STL/Alembic | `60-pipeline/export-interchange.md` |
| poly budgets, LODs, atlasing, render-time cost | `60-pipeline/optimization-realtime.md` |
| printable geometry, manifold checks, tolerances | `60-pipeline/3d-printing.md` |
| cameras, framing math, DOF, turntables, studio shots | `60-pipeline/product-viz-and-shots.md` |
| precision CAD, mechanical fits, tolerances, DFMA | `70-cad-precision-robotics/cad-precision-modeling.md` |
| robotics URDF, kinematics, joint frames, inertia | `70-cad-precision-robotics/robotics-urdf-mechanisms.md` |
| gears, involute teeth, planetary, cycloidal | `70-cad-precision-robotics/gears-transmission-modeling.md` |
| polymer 3D printing, DFAM, tear-drop holes, infill | `70-cad-precision-robotics/polymer-3dprinting-cad.md` |
| print plates, nesting/packing, part orientation, STL per plate | `70-cad-precision-robotics/print-plate-layout.md` |
| bolts, counterbores, O-ring glands, bearings | `70-cad-precision-robotics/fasteners-seals-mechanics.md` |
| wiring, industrial connectors (M12, RJ45, DB9), harness | `70-cad-precision-robotics/industrial-connectors-wire-harness.md` |

Each file's frontmatter carries a `loads_with:` list — the files usually needed
alongside it. Follow it rather than guessing.

---

## Full catalogue

### 00 — Foundations

| File | Description |
|---|---|
| `blender-version-matrix` | Version timeline and the exact API breakages between 4.2 and 5.2 that silently invalidate memorized bpy code. Read before writing any script. |
| `bpy-scripting-core` | How to write bpy that actually runs — data API over operators, context overrides, headless reality, introspection instead of recall, and the error taxonomy. |
| `python-agent-boilerplates` | Standard, copy-pasteable, headless-verified Python boilerplates for CAD, geometry nodes, PBR shaders, armatures, animation, physics, and rendering. |
| `agent-workflow-loop` | The execute-verify-refine loop over blender-mcp — how to plan, how to prove a step worked, and when to stop and hand off. |

### 10 — Modeling

| File | Description |
|---|---|
| `modeling-topology` | Quad-flow, poles, normals/sharpness attributes, transform application, and headless mesh construction/diagnostics via bmesh and `from_pydata`. |
| `modifiers` | The modifier stack as an ordered evaluation graph — order rules, data-API configuration, headless application via depsgraph, boolean solver selection. |
| `uv-unwrapping` | Seams, unwrap methods, packing margin math, texel density, UDIMs, multi-UV layouts, and the headless operator-context patterns UV work actually requires. |
| character/creature anatomy, facial loops, blendshapes, hair curves | `15-character-creature/character-creature-modeling.md` |

### 15 — Character & Creature

| File | Description |
|---|---|
| `character-creature-modeling` | Humanoid & creature proportion canons, animation edge flow, the 52 ARKit blendshape targets, Blender 5.2 Hair Curves (`bpy.data.hair_curves` + `add_curves`), 2-bone IK rigs with twist bones, harmonic walk cycles, `RANDOM_WALK_SKIN` skin SSS and melanin hair optics. bpy names runtime-verified 2026-09-06; anatomy figures are literature, not standards. |

### 20 — Shading

| File | Description |
|---|---|
| `materials-pbr` | Principled BSDF socket inventory for 5.x, physically plausible value ranges, and safe runtime socket resolution when building node trees. |
| `texturing-baking` | Image texture wiring, color space correctness (sRGB vs Non-Color), procedural textures in 5.x, and the headless Cycles bake pipeline. |

### 30 — Lighting & Render

| File | Description |
|---|---|
| `lighting` | Light data properties, physical wattage reasoning against AgX/Film Exposure, HDRI worlds, light linking, studio recipes. |
| `render-engines` | Choosing and configuring Cycles / EEVEE / Workbench, GPU device setup, denoising traps, and what actually works under `--background`. |
| `compositing-output` | Building the 5.x compositor node group in Python, passes/AOVs, File Output wiring, scene- vs display-referred color, VSE stitching. |

### 40 — Animation & Rigging

| File | Description |
|---|---|
| `animation-fcurves` | Slotted-Action data model, F-curve/keyframe creation, interpolation & Bezier easing math, F-modifiers, drivers, timing numbers. |
| `rigging-armature` | Armature data model (edit_bones vs bones vs pose_bones), headless edit-mode patterns, bone collections, constraints, IK/FK, skinning limits. |
| `mocap-retargeting` | Importing FBX/BVH/glTF animation, constraint-based retargeting, baking, NLA with slotted actions, root motion, loop cleanup, shot staging. |

### 50 — Procedural

| File | Description |
|---|---|
| `geometry-nodes` | Build, wire and drive Geometry Node trees entirely from bpy — 4.0+ interface API, fields vs values, zones, instancing, baking. |
| `simulation-physics` | Rigid body, cloth, soft body, particles, Mantaflow, dynamic paint, force fields — statefulness, caches, headless baking. |

### 60 — Pipeline

| File | Description |
|---|---|
| `scene-organization` | Collections, visibility flags, data-block users/orphans, linking vs appending, units, and a deterministic scene scaffold. |
| `export-interchange` | Verified 5.2 operator names and arguments for glTF, FBX, USD, OBJ, STL, PLY, Alembic, plus a target-to-settings decision table. |
| `optimization-realtime` | Poly/draw-call budgets, LODs, atlasing, high-to-low baking, instancing, simplify, and what actually costs time in Cycles. |
| `3d-printing` | Manifold/watertight requirements, wall thickness and clearance by process, bmesh-based failure detection, STL/3MF export. |
| `product-viz-and-shots` | Camera as a technical instrument — framing math, DOF, constraints, studio backdrops, turntables, shadow catchers, render-review loop. |

### 70 — Precision CAD & Robotics

| File | Description |
|---|---|
| `cad-precision-modeling` | Precision mechanical modeling, CAD standards, metric units, exact boolean workflows, chamfers, and GD&T clearance tolerances in Blender. |
| `robotics-urdf-mechanisms` | Robotics kinematic hierarchies, joint coordinate frame orientation, visual vs collision mesh decimation, and URDF generation in Blender. |
| `gears-transmission-modeling` | Parametric involute gear generation, tooth profiling, cycloidal pin-wheel drives, and planetary transmission modeling via bmesh. |
| `polymer-3dprinting-cad` | Engineering design for 3D printing in polymers (FDM/SLA/SLS), tear-drop holes, self-supporting chamfers, heat-set insert bosses, and hole shrinkage compensation. |
| `fasteners-seals-mechanics` | Standards and modeling patterns for ISO 4762 metric fastener counterbores, AS568/ISO 3601 O-ring glands, and bearing housing shoulders. |
| `industrial-connectors-wire-harness` | Standards and modeling patterns for industrial connectors (M12 D-cut, RJ45, DB9), cable glands, wire harness bend radius, and panel cutouts. |

---

## File anatomy

Every domain file has these eight sections, in this order:

1. **Mental model** — what the domain is and the single most common way agents get it wrong
2. **Decision first** — the table/tree consulted *before* writing code
3. **Rules** — numbered, each with `Why:` and `Violation:` (the observable symptom)
4. **bpy patterns** — copy-paste-ready, data-API-first, headless-safe, version-gated
5. **Failure modes** — symptom → root cause → fix
6. **Parameter defaults by use case** — Game/realtime · Character anim · Motion graphics · Product viz · 3D print
7. **Verification checklist** — assertions the agent can run itself
8. **Sources** — primary docs, with `[UNVERIFIED]` marking anything not confirmed

The `Violation:` lines and the §5 tables are deliberately written as **observable
symptoms** rather than explanations, because a traceback string or a visual artifact
is the only thing the agent will actually have when it needs this knowledge.

---

## Conventions and trust level

- **Target:** Blender 5.2 LTS. `docs.blender.org/api/current/` **is** 5.2 as of July 2026.
- **Verification:** API names, socket names, operator arguments and enum identifiers
  were checked against the official API reference, the 4.0/4.2/4.4/5.0/5.1/5.2
  release notes, and — where docs were ambiguous — against Blender source at tag
  `v5.2.0` and against live 5.2.0 / 4.5.9 installs running
  `--background --factory-startup`.
- **`[UNVERIFIED]` markers** appear on claims that could not be confirmed against a
  primary source. These are mostly *industry practice* numbers (poly budgets, wall
  thicknesses, texel density targets, Cycles cost multipliers) rather than API facts.
  Treat them as defensible defaults, not as ground truth.
- **Anti-hallucination stance:** where a name was uncertain, the file gives a
  **runtime introspection pattern** instead of a guessed string. If you find
  yourself typing a literal that Blender defined, print it first.

---

## KB → Skills

Installed routers: `blender-agent-core`, `blender-image-to-3d`, `blender-knowledge-workbench` (2026-09-05 decision). No per-domain skills exist; do not invoke names like `blender-modeling` or `blender-render`. Add a router only after a recorded retrieval-caused missed gate; see [current capability map](../docs/blender-ai-workflow.md).

## Deep Engineering Research Repositories

Engineering research synthesis with equations, diagrams and citations; claim-specific validation is required before use:
1. **[`research/robotics-precision-cad/`](../research/robotics-precision-cad)** (13 reports: kinematics, GD&T, DFMA, B-Rep bridge, URDF/simulation, gear math, flexures, stackup, tendon routing, humanoid actuators, industrial wiring & connectors, robot arm pipeline lessons learned).
2. **[`research/mechanical-engineering-foundations/`](../research/mechanical-engineering-foundations)** (5 reports: machine elements, strength of materials, metallurgy, fluid power & seals, springs & bolted joints).
3. **[`research/3d-printing-polymer-engineering/`](../research/3d-printing-polymer-engineering)** (5 reports: polymer taxonomy, anisotropy & reptation, DFAM rules, fasteners & snap-fits, thermal warping & annealing).
4. **[`research/polymer-additive-manufacturing-advanced/`](../research/polymer-additive-manufacturing-advanced)** (5 reports: melt rheology & Cross-WLF, continuous fiber CFRTP, non-planar stress-aligned slicing, polymer tribology, LSAM pellet extrusion).
5. **[`research/advanced-tribology-contact-mechanics/`](../research/advanced-tribology-contact-mechanics)** (5 reports: Hertzian contact & subsurface shear, Stribeck EHL lubrication, cycloid speed reducers, actuator inertia matching, SIMP topology & TPMS lattices).
6. **[`research/blender-rendering-deep-dive/`](../research/blender-rendering-deep-dive)** (5 reports: Cycles path tracing & MIS, EEVEE Next VSM & Hi-Z, Chandrasekhar volume scattering, AgX/ACES gamut science, OIDN/OptiX temporal denoising).
7. **[`research/blender-rigging-skeleton-skinning/`](../research/blender-rigging-skeleton-skinning)** (5 reports: Armature coordinate spaces & roll math, IK CCD/FABRIK/DLS solvers & pole angle calibration, LBS vs Dual Quaternion Skinning, procedural mechanical piston rigs, Rigify pipeline).
8. **[`research/blender-advanced-materials-shading/`](../research/blender-advanced-materials-shading)** (5 reports: OpenPBR Principled BSDF microfacets, Random Walk SSS physics, Airy thin-film wave interference, procedural fractal fBm imperfections, Chiang-Marschner hair & velvet sheen).
9. **[`research/blender-geometry-nodes-procedural/`](../research/blender-geometry-nodes-procedural)** (5 reports: Fields architecture & context evaluation, procedural hard-surface CAD & booleans, Simulation Zones & physics ODEs, Repeat Zones & recursion/Laplacian relaxation, OpenVDB Volume Grids & SDF smooth booleans).
10. **[`research/industrial-wiring-harness-packaging/`](../research/industrial-wiring-harness-packaging)** (5 reports: Industrial bus physical layers & pinouts, connector dimensional standards & panel cutouts, cable mechanics & drag chains, IP sealing & thermal breathing vents, EMC grounding & harness manufacturing).
11. **[`research/character-creature-anatomy-modeling/`](../research/character-creature-anatomy-modeling)** (6 reports: Human proportions & craniometrics, creature comparative anatomy & locomotion, animation topology & facial loops, FACS 52 ARKit blendshapes & CSK drivers, Blender 5.2 Hair Curves & soft-tissue physics, skeletal kinematics & biped locomotion & skin SSS & melanin optics).

---

## Python Agent Boilerplate Library (`scripts/boilerplates/`)

Registry is generated, not hand-maintained: `python3 scripts/boilerplates/run_all_boilerplate_tests.py --list` prints every module with its docstring line; `run_all_boilerplate_tests.py` runs them headless and decides PASS by the `AGENT_OK` sentinel. Catalogue and usage notes: [`00-foundations/python-agent-boilerplates.md`](00-foundations/python-agent-boilerplates.md). A module's self-test proves it runs and asserts what its docstring says — not that its engineering constants are standards-correct for your case.

## Maintain the knowledge pipeline

Run `python3 scripts/knowledge-pipeline.py scan` for additions, revisions and un-routed sources. Follow the [curation pipeline](../.agents/skills/blender-knowledge-workbench/references/knowledge-to-workflow.md); reviewed topics compile into the [generated playbook](generated-workflows.md). Source diagrams/snippets remain research until their task-specific checks are performed.
