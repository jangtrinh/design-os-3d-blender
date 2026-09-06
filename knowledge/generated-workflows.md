# Generated Blender workflow playbook

Generated from catalog-config.json. Edit the config, then prepare/publish again.
Routing reviews are static source assessments, not API, physics or hardware certification.
Read only the workflow and conditional topic relevant to the task. Core owns execution.

## native-hard-surface

Build from reference images, silhouette, topology, and softly filleted bodies using Blender-native tools.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/10-modeling/modeling-topology.md` — read-verify; SHA256 `1b24a3089c56d919a90b1717ce805592229479c03a3db9bc73697e3d4ddc3608`
- `knowledge/10-modeling/modifiers.md` — read-verify; SHA256 `88f4e06ffc4d5b9f74db1d00f2c0a95cee35cbe28a8248ab12b19dbf8f6a1ff1`

### Steps

- Establish the fidelity contract and scene graph from reference images/measurements.
- Blockout to proportion and camera before filleting edges.
- Build continuous surfaces, separate the real parts, and only then add detail.
- Compare against reference and occluded angles after each pass; return the verdict to core.

### Gates

- Landmarks and dimensions carry declared error margins.
- No critical part exists only as a description.
- Topology/transforms satisfy the object's predicate.
- Review the sheet at the same camera plus the 3/4 image; do not use a self-scored number to promise 100% accuracy.

### Limitations

- Images do not determine occluded faces precisely.
- ww_mesh.py returns raw vertex/face data in metres; the caller owns winding, unit conversion and scene ownership.

### Topic: python-adapter-review

When: When reusing a bpy boilerplate library instead of writing a new helper.

- `knowledge/00-foundations/python-agent-boilerplates.md` — read-verify; SHA256 `17ab56b12a636bbddab1c0bb4c0f954db77ef04e0f856b1b3449a91be4a17685`
  Caution: Registry claims verified, operator-free and standards-compliant behavior not established by actual modules. Static audits found missing bearing bores, sag, gear root/helical features, X-joint limits and physical thin-film optics; examples often test counts only. Bibliography is not certification; read module-specific cautions.
- `scripts/boilerplates/bp_core.py` — inspect-adapt; SHA256 `24716d4a714d7dceb25b7e039a51a3ab3ff69b5328ac21118f07ffb8390ca9fd`
  Caution: clean_scene deletes global objects; mode errors swallowed; named data removal can affect other users. Evaluated mesh cleanup handle is lost; substring socket resolution is ambiguous.
- `scripts/boilerplates/run_all_boilerplate_tests.py` — inspect-adapt; SHA256 `bce4755c515b1b9028e8a52c7c8d84eb86e6155e1a578e58db6424dee30e3f9f`
  Caution: PASS = last-line AGENT_OK from the sentinel shim, not a magic string. --list prints the generated registry. A module PASS proves it runs and asserts its own postconditions, not standards-correct constants.

**Steps**

- Pick the right module and read the actual source; distinguish documentation snippets from the implementation.
- Declare input/scene ownership, units, effects, and output; create a separate candidate.

**Gates**

- Check the API/runtime and assertions against task behavior, not against a verified header.
- Measure actual geometry/state and view the output; keep the original source for rollback.

**Limitations**

- clean_scene and node group/mesh replacement can destroy another scene; do not run them just because they are indexed.
- Knowledge routing does not certify mass/inertia, bone roll, or physics.

## native-product-visualization

Matte plastic materials, studio setup, camera, and polished product imagery.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/20-shading/materials-pbr.md` — read-verify; SHA256 `e455cc41465700c56266f5d9652adae920972e941644b27085b2982ab3fa8705`
- `knowledge/30-lighting-render/lighting.md` — read-verify; SHA256 `f2b8db7610f1793524b248c9442b0f1a6951dfe5015faa35d35168eadedd894f`
- `knowledge/60-pipeline/product-viz-and-shots.md` — read-verify; SHA256 `0ae55d706fd7496ee8bf802784938a97cbb5e4383939b27c09d47e1f48a85f35`

### Steps

- Lock the shot goal, background, texture scale, and roughness against reference.
- Check normals and bevels before editing the shader.
- Introspect node sockets; use neutral/grazing light to separate geometry defects from material defects.
- Render diagnostics at the same aspect ratio, then finish the shot.

### Gates

- Framing covers the whole moving part or object inside the camera.
- Grazing light exposes no shading defect or detached surface.
- Review the material in both neutral and hero views.

### Limitations

- A good-looking shader does not prove the real printed surface.
- Turntable/preview helpers modify the scene; use a separate candidate copy/process.

### Topic: opaque-micro-surfaces

When: When plastic/metal reflects incorrectly, or grain/imperfection at real-world size is required.

- `research/blender-advanced-materials-shading/01-OPENPBR-PRINCIPLED-BSDF-SURFACE.md` — read-verify; SHA256 `7d05fab6bb6ed95d4201618835091fbbc0522dab79320c7ae0b0d78e4332fc46`
  Caution: Fac/Factor migration conflicts with sibling snippets; Principled/OpenPBR equivalence is unverified. Introspect sockets; avoid deprecated use_nodes.
- `research/blender-advanced-materials-shading/04-PROCEDURAL-MICRO-SURFACE-IMPERFECTIONS.md` — read-verify; SHA256 `e41d624f3506ba398bab369df5770050e4e52f0d708e860966a08a685b27fc2a`
  Caution: Snippet uses 3D Object Noise rather than the described triplanar blending. Bump unit/presets are not calibrated physical thickness.
- `scripts/boilerplates/bp_materials_pbr.py` — inspect-adapt; SHA256 `8b143fdc2ad121976ad8f5e555f648b4e49b6a3d9265ea5fdf9d25da2846e2cd`
  Caution: Named material deletion affects global data; missing sockets silently ignored; data.materials assignment can affect shared mesh users. No actual rendered self-test.
- `scripts/boilerplates/materials_shading/bp_mat_metals.py` — inspect-adapt; SHA256 `c8ec6e3e66989bac62cc2a22c02c902666a8368ed77145c938aaac04de6775e9`
  Caution: Missing sockets silently skipped; unknown preset becomes aluminum. Deletes same-name material. Two-node test does not verify values, links, tangent orientation or physical reflectance; Optional annotation unresolved.

**Steps**

- Separate metallic/IOR/roughness; lock units and texture scale.
- Choose roughness, bump, or geometry according to the visible detail.

**Gates**

- Introspect sockets, material output, and finite values.
- Compare neutral/grazing crops: no seams, oversized grain, or broken normals.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: subsurface-optics

When: When thin/thick materials need transmissive scattering, such as silicone, wax, or skin.

- `research/blender-advanced-materials-shading/02-SUBSURFACE-SCATTERING-RANDOM-WALK.md` — read-verify; SHA256 `5c5a282cf39829e75795c0cea0b1e82b090dd87539b5e2d6e02b0aabc74d269f`
  Caution: Absolute fidelity, dual-layer model and hardcoded Random Walk enum are unverified; radius ratios and dimensional scale need distinction.

**Steps**

- Lock mesh dimensions, thickness, and relative scale/radius.
- Check the algorithm enum on the runtime before building the material.

**Gates**

- Bounds are in the correct units; scale/radius is declared and finite.
- Compare backlit thin/thick views against reference; do not take a preset as the pass threshold.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: thin-film-optics

When: When the brief calls for interference color that shifts with viewing angle, or a thin coating.

- `research/blender-advanced-materials-shading/03-THIN-FILM-INTERFERENCE-IRIDESCENCE.md` — read-verify; SHA256 `c3d776a5e078722e4ffabe65a173f91fe0378e633becd5f2129a64f77814b07f`
  Caution: Example connects Generated gradient to Coat Tint; it has no thickness/view-angle interference model. Spatial tint is not thin-film evidence.
- `scripts/boilerplates/materials_shading/bp_mat_thinfilm.py` — inspect-adapt; SHA256 `8d1870e3b0e47a3a09d7b26b8559f3764d63aee199b6ee29b8106d88cfb62e67`
  Caution: Facing-to-Base-Color ramp produces stylized angle coloration, not claimed Airy/thickness optics. Four stops despite five-stop comment; deletes material. Node count is not optical verification.

**Steps**

- Distinguish position-based tint from angle-based interference.
- Confirm the thickness/IOR sockets or the model actually in use.

**Gates**

- Record the thickness unit and the IOR parameters.
- Compare at least two camera/light angles; a fixed gradient does not prove thin film.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: fiber-fabric-surfaces

When: Only when hair/fur, velvet, satin, or weave direction is clearly visible in the shot.

- `research/blender-advanced-materials-shading/05-PHYSICAL-HAIR-FABRIC-SHADING.md` — read-verify; SHA256 `83846c13bd7c1938d3616f0eb7c4a27bd86e7da6808402b8f589f5a9a31f9c7a`
  Caution: TRT bounce descriptions conflict; anisotropy/tangent node and shader enum claims need runtime inspection.

**Steps**

- Choose between a strand shader and surface sheen/anisotropy.
- Lock tangent/UV and fiber size before adjusting color.

**Gates**

- Shader/enum/output/tangent are valid.
- Review highlight direction, silhouette, and consecutive frames to detect crawling.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

## native-animation-rigging

Joints, hand, natural pick/place, range of motion, and explode/reassemble.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/40-animation/rigging-armature.md` — read-verify; SHA256 `dd5b6f0feebbfb0d58ae1aed6963261ed8e5f09e96f16ece6e031b8b88671889`
- `knowledge/40-animation/animation-fcurves.md` — read-verify; SHA256 `1d0bc0a7456fb7dc092737f0d8f92b4aecc6d954061ace4fc6e07b9feaa9df81`
- `knowledge/70-cad-precision-robotics/robotics-urdf-mechanisms.md` — read-verify; SHA256 `dbd386d203b4e9f109a874f873fada6fd12aaab46016e04ed948d8e25f95174e`
  Caution: Static audit: named hull block decimates only; inertia block formats values; diagonal positivity is incomplete. Verify frame conventions independently.
- `knowledge/60-pipeline/scene-organization.md` — read-verify; SHA256 `7ca6183bbf3160eb85aae0c7d2843c3fe8ca4c0ad5eccf80f56a3890aa8ca10a`

### Steps

- Lock joint frames, limits, TCP, hand interface, and the parent-child diagram.
- Define the task as approach → grasp → lift → transfer → release; decompose explode into an assembly sequence.
- Blockout the motion and the extreme poses; a hand transfer must preserve continuity at the attach/release frames.
- Screen contact within the declared range and review the animatic before polish/render.

### Gates

- Joint axes/limits and hierarchy are correct in local/world space.
- No transform jump at grasp/release.
- Range of motion, standing upright, rear-side manipulation, and axis rotation have frame evidence when required.
- Correct order of fastener removal → part extraction; reassembly restores the transforms.
- Review the clip over time; a pose still does not replace motion review.

### Limitations

- The overlap diagnosis samples evaluated surfaces at chosen frames; it does not prove continuous collision or force.
- A scripted attachment animation does not prove the servo carries the load.
- The assembly builder copies objects with shared mesh data; copy the mesh before editing geometry.

### Topic: rig-spaces-ik-mechanisms

When: When armature scripting, IK/pole, piston, gear, or cable is required.

- `research/blender-rigging-skeleton-skinning/01-ARMATURE-MATRICES-BONE-TRANSFORMS.md` — read-verify; SHA256 `2ac1d81d4f2ed9f922406bd4baa6f63975a3f7e413b1ddf56b3801c1c43e93a0`
  Caution: Roll helper lacks zero-length/parallel guards; simplified hierarchy product is not a general evaluated constraint/inheritance transform.
- `research/blender-rigging-skeleton-skinning/02-INVERSE-KINEMATICS-SOLVERS-MATHEMATICS.md` — read-verify; SHA256 `ac3e18104c8ded749a2c9da37fd01194f743fc716edf449360ad016e7368fe29`
  Caution: Claimed exact pole calibration does not read rest-axis/roll and lacks straight/coincident guards; example uses a fixed pole angle.
- `research/blender-rigging-skeleton-skinning/04-PROCEDURAL-MECHANICAL-CHARACTER-RIGGING.md` — read-verify; SHA256 `3abab897422d4863c1459564e05c7045e58bd4465609e13c4be8ac51da6e8dad`
  Caution: Mutually constrained piston targets risk a dependency cycle; driver expression is not contact/load proof and spaces/axes need explicit validation.
- `scripts/generate-procedural-rig.py` — inspect-adapt; SHA256 `2f77cb8f2da4017204e0b6b107248b579e9ac8a51a4f5f11991228cf27e7ab32`
  Caution: Callable builder deletes all bpy.data objects. Fixed pole angle; no claimed exact calibration, pose sweep, mesh/limits/load/visual validation.
- `scripts/boilerplates/bp_rigging.py` — inspect-adapt; SHA256 `6978e0ef90b15f73881915785706c2e9f2a7fcd07c4c5974037a8f25efc46090`
  Caution: calculate_deterministic_roll always returns 0.0. Operator context is not restored, missing parents ignored, control bones remain deforming. No IK calibration.

**Steps**

- Lock world/rest/pose spaces, axes, hierarchy, and the motion envelope.
- Guard against zero-length/parallel bone references; calibrate the pole against the evaluated pose.
- Separate anchors from constrained parts; record stroke/ratio/space.

**Gates**

- Measure pivot and IK endpoint errors against the task tolerance.
- Check alignment/stroke/ratio at the extreme poses and at attachment events.
- Review the sweep through straight/upright/folded configurations; motion does not prove servo load.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.
- The adapter deletes every object when its build function is called; only inspect/adapt it in a separate candidate.

### Topic: skinning-modular-rigs

When: When meshes deform, limbs twist, or an installed and selected Rigify is used.

- `research/blender-rigging-skeleton-skinning/03-DUAL-QUATERNION-SKINNING-LBS.md` — read-verify; SHA256 `fb2d01f4293bbf3c383009522ac757fee1fb43a50e3a3d6105ba93a6a58b381c`
  Caution: Unconditional volume-preservation claims conflict with bulging discussion. DQ property and weight normalization behavior need runtime/group-role checks.
- `research/blender-rigging-skeleton-skinning/05-RIGIFY-MODULAR-RIGGING-PIPELINE.md` — read-verify; SHA256 `41d49fef80d6ca98fd3dabc48e3b3b373edc4190be16d1815c98c36b271ac796`
  Caution: WGT taxonomy and ORG-hand matrix_world statement are unverified/inconsistent with pose-space guidance; preexisting rig name can be mistaken for output.

**Steps**

- Compare LBS/preserve-volume/helper bones at identical poses.
- Distinguish deform groups from masks; keep the metarig and identify the new rig by provenance.

**Gates**

- Weights are finite and nonnegative; missing weights and wrong sums are detected.
- Measure displacement across the IK/FK switch; review bulging, cross-sections, and penetration.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.
- Do not install extensions on your own; an object named rig and operator success are not enough.

### Topic: animation-curves-drivers

When: When keyframes, a driver, or a turntable must be created from a Python helper.

- `scripts/boilerplates/bp_animation.py` — inspect-adapt; SHA256 `55df506beb0fa0584968ce053e0a1f8c2915c14d19236b6c369aae5c4c1915cd`
  Caution: Indexed assignment is not general RNA array/path handling. Matching curves across all action slots/preexisting keys may be edited. Turntable has no Cycles loop; driver setup clears state.

**Steps**

- Identify the object/action/slot and the RNA paths you may edit; leave pre-existing animation outside the scope untouched.
- Adapt the helper to the actual path/index; create drivers only on the selected property.

**Gates**

- Measure values at keyframes and between keyframes, verify the correct action slot, and confirm no curve outside the scope changed.
- Check the loop endpoint/seam and review playback; a single midpoint pass does not prove the whole cycle.

**Limitations**

- The current helper can alter multiple action slots and wipe driver state; do not run it directly on animation in use.
- The existing self-test checks only one midpoint; it does not certify the loop or natural motion.

### Topic: robot-joint-frame-adapter

When: When reusing the six-joint robot armature helper.

- `scripts/boilerplates/rigging_kinematics/bp_rig_robot_arm.py` — inspect-adapt; SHA256 `2ab750a637d9b7668cf0f6dcde63785b8f4cb109ecb820ec876cbe14f9a07651`
  Caution: X-axis joint limits unconfigured; local frames not aligned/verified against mechanical axes. Deletes named rig and mutates active mode/context. Six bones do not prove 6-DOF kinematics or limit behavior.

**Steps**

- Declare joint frames, hierarchy, rotation axes, and limits from the real mechanism.
- Align bone frames, lock the correct axes, and configure all of X/Y/Z in the candidate.

**Gates**

- Check allowed/locked axes on every joint; cross-check the FK endpoint at poses with known expected results.
- Sweep the limits, measure attachment/clearance, and review the motion; a bone count does not replace kinematics.

**Limitations**

- The helper omits X-axis limits and does not map bone frames onto mechanical axes.
- A demo motion does not prove load, torque, thermal behavior, or manufacturability.

### Topic: assembly-collision-staging

When: When filming assembly/explode, or detecting parts waiting to be installed and flight paths that overlap.

- `research/robotics-precision-cad/13-ROBOT-ARM-PIPELINE-LESSONS-LEARNED.md` — read-verify; SHA256 `22e2d4f0635550f1cedf9017c707e0bc116723cdac98b4c9ff7b08ebb29efb76`
  Caution: Lines39/46 unmeasured<1ms and universal0.20mm3 are not acceptance evidence; source-level units/evaluated geometry matter. Lines57-71 fixed120mm and perfectly jerk-free are overclaims: quintic third derivative endpoints=60. Lines82-94 collapsing unused cable points does not preserve length. Lines100-113 weights/packing are historical candidates, not general calibrated optimum; pair exclusions need named phase-bound justification. Actual Arm uses frame-sampled LINEAR F-curves: smooth quintic sample values do not establish a continuous C2 Blender trajectory.
- `scripts/boilerplates/cad_mechanics/bp_assembly_collision_audit.py` — inspect-adapt; SHA256 `e7af4179f5ff43404dbbbc791c688f01a93040e6c8d00b0ee8cd76a88aa433ad`
  Caution: Lines76-99 boolean copies raw mesh, ignores evaluated modifiers and scene scale_length; runtime reproduced false zero versus5999.95mm3 modifier clash and1e9 unit error. BVH cannot detect contained solids (0pairs with1000mm3). Lines147-149 total_steps=2 divides by zero; lines207-222 accepts oversize parts. No obstacle input or collision-free proof;0.20mm3 and zero-jerk claims are not universal.
- `.agents/skills/blender-agent-core/references/assembly-sequences.md` — read; SHA256 `9488f39087d6e1f3d5827ec03cc571b95979247ccac162a212df0b367c97aef7`

**Steps**

- Create a unit manifest and dependency graph ordered by receiver, internal parts, retention, wires, then covers.
- Compute staging separately and check world/projected gaps; do not check the final pose only.
- Check both arrival and seating over time; pick waypoints/axes from geometry and exempt named mates only in the correct phase.
- Review a short animatic at the failing segment, at similar mechanisms, and at the endpoint camera before a full render.

**Gates**

- Negative controls must detect waiting clash, clear-wait/blocked-transit, wrong phase exemption, and solid containment.
- Check evaluated modifiers and scene units; report surface flags, the solid predicate, and the sample range separately.
- The camera holds the intended framing; quintic samples/LINEAR F-curves must not be described as zero jerk or controller dynamics.

**Limitations**

- 120mm lift,0.20mm³ and the speed claim are case-specific/unverified values, not a general standard.
- The audit adapter ignores modifiers/scale inside the Boolean; same-future-link blanket exclusions can hide defects.
- Mating against an actuator-visual plus a media PASS does not settle mechanics, hardware/tool access, or load.

## polymer-functional-print

FDM plastic printing, fit, inserts, assembly/disassembly, durability, and materials.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/60-pipeline/3d-printing.md` — read-verify; SHA256 `4bce69b0a198c8406475bf230fe66a35cbad19752bba22aa8ce24ad66e6d0eda`
- `knowledge/70-cad-precision-robotics/polymer-3dprinting-cad.md` — read-verify; SHA256 `eab55760bfe566860b330463a65a8802b1dd569354d05e85ce96e5af3febd69d`
  Caution: Static audit: bottom semicircle spans90deg; chamfer example creates cylinder; wall test is bbox. Verify actual geometry before reuse.
- `knowledge/70-cad-precision-robotics/fasteners-seals-mechanics.md` — read-verify; SHA256 `870ac87843291f7991ff38c0d804fff817d743fac5e123b2c4ad667da68dfaa0`

### Steps

- Lock printer/nozzle/material/orientation, dimensions, and interfaces.
- Split parts along assembly lines and tool access; choose screws/inserts from real drawings.
- Design fit coupons and load-bearing parts using material data for the print orientation.
- Export the candidate in the correct units and inspect the exported file itself before a physical trial.

### Gates

- Manifoldness, scale, and local wall thickness are actually measured.
- Recessed screws have verified depth, thread engagement length, and tool access.
- Clearance/fit confirmed by coupon, not by bounding box alone.
- Load/thermal/creep and print deviation have evidence before release.

### Limitations

- A mesh pass or a good-looking image is not enough to call something load-bearing print-ready.
- The tolerance helper currently covers overhang/bbox only; there is no local-wall or clearance test.
- The research is uncertified synthesis; check the current datasheet/standard whenever a number is used.

### Topic: advanced-deposition-process

When: When high-flow, nonplanar, or LSAM is required; pick the correct branch.

- `research/polymer-additive-manufacturing-advanced/01-POLYMER-EXTRUSION-RHEOLOGY-HOTENDS.md` — read-verify; SHA256 `1be0673cd2e35dae58d243c1c2ef0a5ae84cebcd2367ed1d2d3896cb3a4ab13e`
  Caution: Pressure-advance example mixes displacement with seconds*acceleration; resolve quantity/units before control or firmware use.
- `research/polymer-additive-manufacturing-advanced/03-NON-PLANAR-SLICING-STRESS-ALIGNMENT.md` — read-verify; SHA256 `ad6b19112a6f25f67bd8c129a58cbf5571f1dfdaa42c5435dac64aa8e5aadeb7`
  Caution: Streamline loop never advances current_vert, repeatedly appending the same next point; no field read, reprojection or collision solver.
- `research/polymer-additive-manufacturing-advanced/05-LARGE-FORMAT-LSAM-PELLET-PRINTING.md` — read-verify; SHA256 `8458936f98c3796d58ae45cf9eab428952c532a197d069b085f9f7a0d059d0b5`
  Caution: No usable tmax calibration; total strain energy compared to fracture toughness without crack geometry/area; stock allowances unqualified.

**Steps**

- Lock the hardware envelope/flow/thermal or the toolpath/finishing constraints.

**Gates**

- Check that the path progresses and that the toolhead envelope holds; use real calibration/coupons.
- Do not emit G-code or drive a machine from research alone.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: polymer-selection

When: When the material is not locked yet, or isotropy/temperature limits need assessment.

- `research/3d-printing-polymer-engineering/01-POLYMER-MATERIALS-TAXONOMY.md` — read-verify; SHA256 `593b87a33135aa9734fb6e80857794eee902a539cc3a16a2c487fbd43483de57`
  Caution: Source has conflicting PETG crystallinity labels and absolute carbon-fiber warping claim; bibliography is not verification.

**Steps**

- Use the taxonomy to frame the questions; choose grade/process from datasheets and coupons.

**Gates**

- Do not treat PETG/carbon-fiber conclusions as absolute; the data must come from the same process/orientation.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: print-boss-cutouts

When: When building heat-set insert bosses or self-supporting holes for FDM.

- `scripts/boilerplates/dfam_3dprint/bp_insert_boss.py` — inspect-adapt; SHA256 `0bb053452708229c3a3a7f85e53a20eb32b28b3865d30f9d7b33ee045e87992b`
  Caution: 8-degree taper/minimum-wall claims not implemented; separate pillar/cutter are not assembled; unknown size falls back to M3.
- `scripts/boilerplates/dfam_3dprint/bp_teardrop_holes.py` — inspect-adapt; SHA256 `9e2919971fb179490cae5b3b8344b5a28b01c3abc97e30a65907e4c81691c219`
  Caution: Parameterized cutter lacks input guards and print validation; face count cannot establish self-support or retained bore dimensions.

**Steps**

- Choose the insert drawing, material/process/build orientation, and the fit coupon.
- Build the boss with a real cutter; check taper along depth and the hole axis before export.

**Gates**

- Measure hole/taper/minimum local wall after subtraction; do not take a parameter name as evidence.
- Print coupons to test fit/insertion/pull-out, or support/bore retention according to function.

**Limitations**

- The helper does not yet combine pillar and cutter; taper and wall claims are not enforced.
- Self-support depends on process/orientation; a face count is not enough.

### Topic: plate-nesting-screen

When: When using heuristic orientation and guillotine packing to lay parts out on the plate.

- `research/robotics-precision-cad/13-ROBOT-ARM-PIPELINE-LESSONS-LEARNED.md` — read-verify; SHA256 `22e2d4f0635550f1cedf9017c707e0bc116723cdac98b4c9ff7b08ebb29efb76`
  Caution: Lines39/46 unmeasured<1ms and universal0.20mm3 are not acceptance evidence; source-level units/evaluated geometry matter. Lines57-71 fixed120mm and perfectly jerk-free are overclaims: quintic third derivative endpoints=60. Lines82-94 collapsing unused cable points does not preserve length. Lines100-113 weights/packing are historical candidates, not general calibrated optimum; pair exclusions need named phase-bound justification. Actual Arm uses frame-sampled LINEAR F-curves: smooth quintic sample values do not establish a continuous C2 Blender trajectory.
- `scripts/boilerplates/cad_mechanics/bp_assembly_collision_audit.py` — inspect-adapt; SHA256 `e7af4179f5ff43404dbbbc791c688f01a93040e6c8d00b0ee8cd76a88aa433ad`
  Caution: Lines76-99 boolean copies raw mesh, ignores evaluated modifiers and scene scale_length; runtime reproduced false zero versus5999.95mm3 modifier clash and1e9 unit error. BVH cannot detect contained solids (0pairs with1000mm3). Lines147-149 total_steps=2 divides by zero; lines207-222 accepts oversize parts. No obstacle input or collision-free proof;0.20mm3 and zero-jerk claims are not universal.

**Steps**

- Choose material/process, units, bed usable area, margin, and spacing.
- Try orientations against support, bed contact, load axis/anisotropy, and support removability.
- Check every part after packing using real transforms; reject parts that do not fit before adding a plate.

**Gates**

- Oversize fixtures must be rejected; do not accept negative rectangles, parts outside the boundary, or duplicated/missing inventory.
- Re-import the STL/slicer file at the correct scale; a heuristic score does not replace real support and fit assessment.

**Limitations**

- The packer currently accepts an oversize part when it opens a new plate; do not treat an unverified result as print-ready.
- The weights/margins in the source are historical examples with no evidence of being generally optimal/calibrated.

## precision-assembly-metrology

Precision CAD, datums, tolerance stacks, and assembly/disassembly.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/70-cad-precision-robotics/cad-precision-modeling.md` — read-verify; SHA256 `bc171eb925df0f536a5745c294496268eb8a31464c2044439d2a688051fc51f6`
- `knowledge/70-cad-precision-robotics/fasteners-seals-mechanics.md` — read-verify; SHA256 `870ac87843291f7991ff38c0d804fff817d743fac5e123b2c4ad667da68dfaa0`

### Steps

- Lock datums/units and the interface list.
- Use real hardware drawings to build the nominal geometry.
- Compute the tolerance stack with the distribution/assumptions written out.
- Design the assembly path, tool access, and the measurement method.

### Gates

- Drawing and mesh share the same units/datum/revision.
- Fit zones do not rely on overall bounding-box dimensions.
- Critical dimensions have a measurement or a coupon.

### Limitations

- A Blender mesh does not by itself provide B-rep/GD&T or a tolerance solver.
- The inertia helper does not apply object scale/scene scale; do not use its numbers directly when the transform is not identity.

### Topic: compliant-tendon-motion

When: When a flexure, a cable-driven hand, or remote actuation is required.

- `research/robotics-precision-cad/07-COMPLIANT-MECHANISMS-FLEXURES.md` — read-verify; SHA256 `6bb4eb0ab90270fc7a5d4b2c47691bd6d2e0a1abad02ad7890e2d9b3f90c2f27`
  Caution: Stiffness expression has suspect units; zero/infinite-life claims need material/duty evidence, not animation.
- `research/robotics-precision-cad/09-CABLE-TENDON-TRANSMISSIONS.md` — read-verify; SHA256 `3ce580cbbf877b2e96963a83e8d63cbb30cfe11eada9050d8f8d9b63ccdba0ec`
  Caution: Zero backlash/creep and universal pulley ratios unverified; actual cable, pretension, bend life and termination matter.
- `scripts/boilerplates/cad_mechanics/bp_flexures.py` — inspect-adapt; SHA256 `362939358115d1d70e38c2e452f5cdc4d4453947c21cb3344d5be5187a398f4e`
  Caution: BMesh flexure function returns uncut cube; object variant bakes booleans with implicit operation; compliance validity and web geometry ungated.
- `scripts/boilerplates/cad_mechanics/bp_springs.py` — inspect-adapt; SHA256 `2773e4640a6919adfaec02d0d272095c0baac78df59d4cc6a120e55d7386ea0b`
  Caution: Helix lacks ground ends; single washer only; axial versus normal thickness differs; no self-contact, load or fatigue gate.
- `scripts/boilerplates/dfam_3dprint/bp_snap_fits.py` — inspect-adapt; SHA256 `1af01f09b98946ed9da8068e55e75383caa62d0a36dfecaa2780998c3e7bc488`
  Caution: Taper formula differs from implementation; strain table is unverified; no mating/root-fillet/engagement check; polygon count only.

**Steps**

- Lock travel/stiffness/parasitic motion and routing/pretension/tension-only constraints.

**Gates**

- Measure neck/strain, clearance across the envelope, and bend/tension limits.
- Check fatigue/creep/hysteresis against the real material/duty.
- Measure neck/root/thickness, snap engagement, and coil clearance; test physically under the matching process/duty.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.
- Demo geometry may lack notches, mating parts, or ground ends; a face count does not certify compliant performance.

### Topic: precision-material-tessellation

When: When bore/tolerance/finish/heat-treatment need a quantified budget.

- `research/robotics-precision-cad/04-CAD-VS-POLY-BLENDER-BRIDGE.md` — read-verify; SHA256 `c2aec3777fa475e9d3e285c4b18bcc86ca918f3bf78dcc03f1ea19fa8860fe49`
  Caution: Radial sagitta is not directly a diameter/H7 budget; STEP does not by itself supply GD&T. No CAD addon activation follows.
- `research/mechanical-engineering-foundations/03-MATERIALS-METALLURGY-HEAT-TREATMENT.md` — read-verify; SHA256 `73724dbe3b68749c29462f8093f84a183dc5fc8df897ecdbff16cc2a8a648f13`
  Caution: Grade/process dependence incomplete; zero-distortion/uniform-thickness/zero-dimension-change statements are not unconditional process guarantees.
- `scripts/boilerplates/bp_cad_robotics.py` — inspect-adapt; SHA256 `f4cefba47a6540da6fd19de46eb9cee9998c3065d9f974a2dcde69498435b566`
  Caution: Advertised inertia tensor is not computed/returned. Mass uses local evaluated coordinates without object/scene scale or validity guards. Counterbore concatenates capped cylinders, not a boolean union. Hull ignores modifiers.

**Steps**

- Separate nominal dimensions, tessellation error, process allowance, and material grade.

**Gates**

- Distinguish radial from diametral error, the units, and the exported mesh.
- Cross-check grade/temper/finish against sourced drawings/data.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.
- Do not infer GD&T from a STEP export, and do not install a CAD add-on on your own.

### Topic: hardware-interface-geometry

When: When using bearing, nut/washer, keyway, or gland helpers as mechanical interfaces.

- `scripts/boilerplates/cad_mechanics/bp_ball_bearing.py` — inspect-adapt; SHA256 `8383db28f846246672060a6ea553a3314bc9525d7115b2cdabb08cb203b99b4d`
  Caution: Inner/outer rings are overlapping solid cylinders; bores/raceways absent; demo checks ball face count only.
- `scripts/boilerplates/cad_mechanics/bp_fasteners_iso.py` — inspect-adapt; SHA256 `ad3513d1e7e4d031db513de349827e8e4a78bc8233b4ec3d7f59ec851adb6613`
  Caution: Only nut/washer exist; nut bore is hexagonal and unthreaded; unknown size silently becomes M6; face-count checks only.
- `scripts/boilerplates/cad_mechanics/bp_oring_glands.py` — inspect-adapt; SHA256 `75bd44c7c57fd6757e4227f669abb368f3a877fd44607fe29c1efbf5f22e9dbf`
  Caution: Static face gland only; claimed squeeze/fill limits not enforced; no seal-performance or geometry checks.
- `scripts/boilerplates/cad_mechanics/bp_shaft_couplings.py` — inspect-adapt; SHA256 `ffb7d0044c8413a575b80e09470b2e8a9a4adfd2261d516179dc42de93853fe6`
  Caution: Box/cylinder composites are not unioned; range fallback can silently choose wrong key; no spline/coupling or fit verification.

**Steps**

- Choose a specific hardware drawing, units, and tolerances; reject silent dimension fallbacks.
- Build/cut every hole, groove, and contact face in the candidate; check the evaluated mesh after the union.

**Gates**

- Measure bore/raceway/keyway and fit in cross-section; do not accept a solid cylinder in place of a ring.
- Verify local dimensions, squeeze/fill, and topology; verify force/wear/sealing separately with data or a physical test.

**Limitations**

- A standard's name in the header and a face count do not prove hardware compatibility.
- Some helpers currently lack bores/raceways/threads or the boolean union; do not use them directly as production parts.

### Topic: industrial-connector-panel-packaging

When: When building connectors, panel cutouts, terminals, and service clearance in a control enclosure.

- `knowledge/70-cad-precision-robotics/industrial-connectors-wire-harness.md` — read-verify; SHA256 `8835efc6e74d6ba2c45d0a0f0b2fc9b75e3b10d39a2af967511598b6a74fae1c`
  Caution: Lines36-49/154-158 present universal flats, bend and EMC spacing; treat as unverified task-specific inputs. Lines109-130 accept min_bend_radius but never use it; no curvature/strain-relief enforcement. Dimensions and connector coding require selected part drawings.
- `research/industrial-wiring-harness-packaging/01-INDUSTRIAL-BUS-PHYSICAL-LAYERS-PINOUTS.md` — read-verify; SHA256 `0de4f110d19f68c8b2fa83b1942970b058878e86f220e6aea2874fb11028d593`
  Caution: Lines51-60 collapse protocols/speeds/pinouts; A/B labels and terminal numbering require selected endpoint pin-view verification. Line73 says A>B while schematic pulls B high. HART loop resistance shares a table column with cable characteristic impedance. Lines153-159 mating/standoff envelopes are not universal dimensions.
- `research/industrial-wiring-harness-packaging/02-CONNECTOR-DIMENSIONAL-STANDARDS-PANEL-CUTOUTS.md` — read-verify; SHA256 `9bfd07b3b14ff26bc4ce263638dd428616117fb211398719b2c844e9284140b7`
  Caution: Lines80-82 RJ45 bayonet dimensions conflict with robotics source12; line131 DT04-4P dimensions conflict with extended boilerplate. Lines139-146 pitch alone does not establish terminal ratings, cutout or access. Choose actual housing/contact/terminal revision and drawings before machining.
- `scripts/boilerplates/cad_mechanics/bp_connectors_wiring.py` — inspect-adapt; SHA256 `c562ffea81232edf20bb2236280cc06dc96f955f8796e2ac5be368e527850ce2`
  Caution: Lines132-157 saddle is a solid8vertex cube: slot_width/slot_height unused. Lines160-186 AUTO Bezier does not enforce curvature, arc length or strain relief and leaves end caps disabled; runtime accepted0.370mm bend radius for7mm cable. D-cut default dimensions/manifold smoke passed; standard/fit claim still unverified.
- `scripts/boilerplates/cad_mechanics/bp_connectors_extended.py` — inspect-adapt; SHA256 `e6799635a8f6275cb8ecd5aeea4c3192ca99720f3e315bcf801f134f79650a8e`
  Caution: Lines142-189 thread_size changes name only; panel_thickness ignored, no real thread/membrane/vent. Runtime3disconnected solids. DT04 cutter shape differs from source02 and own documented tab size. EMC/IP compliance claims are unverified; cutter defaults require selected supplier drawing plus boolean/section checks.

**Steps**

- Lock connector/contact part numbers, pin view, protocol, cable, and the specific drawing; record where the sources conflict.
- Inspect/adapt the cutter in a separate scene; measure the cross-section, panel thickness, mounting face, and tool approach.
- Declare the pin-to-pin wire list, terminals/crimps, and the install/removal clearance.

**Gates**

- Changing a parameter must change the geometry accordingly; check dimensions, topology, and the actual Boolean after the cut.
- A D-cut smoke test does not replace a fit coupon; pin orientation and drawing revision must match the selected hardware.

**Limitations**

- The pinout/dimension tables are unvalidated synthesis; do not treat a pitch or an ISO name as a compatibility guarantee.
- The saddle is currently a cube with no slot; the vent lacks thread/membrane and ignores its parameters; the adapter must be fixed before production.

### Topic: enclosure-sealing-emc-harness

When: When control-enclosure packaging needs sealing, thermal management, shielding, or harness documentation.

- `research/industrial-wiring-harness-packaging/04-INGRESS-PROTECTION-SEALING-THERMAL-RELIEF.md` — read-verify; SHA256 `64e62ff9b34de40a3bee4a3f1adfaa5664b2ea58e673147af981762135390d44`
  Caution: Lines63-64 bolt pitch heuristic is not seal qualification. Lines87-89 use cold-temperature denominator while naming cooling vacuum, without matching initial-pressure reference. Lines96/117 universal membrane mandate and WEP values are unverified. IP rating requires assembled-product test, not CAD vent geometry.
- `research/industrial-wiring-harness-packaging/05-EMC-GROUNDING-SHIELDING-HARNESS-MANUFACTURING.md` — read-verify; SHA256 `0187d9f805ba6d158e2e475df576dfa7c692abe33d7088e1d4e85e537b9c7124`
  Caution: Production Architecture Specification label is not certification. Shield transfer impedance, universal segregation/crimp/pull-force and heat-shrink IP claims are unverified. Separation categories conflict with KB/source12. Pin-to-pin wire list must identify actual contact, wire, terminal/crimp tool and drawing revisions; formboard arc length does not prove strain relief.
- `scripts/boilerplates/cad_mechanics/bp_connectors_extended.py` — inspect-adapt; SHA256 `e6799635a8f6275cb8ecd5aeea4c3192ca99720f3e315bcf801f134f79650a8e`
  Caution: Lines142-189 thread_size changes name only; panel_thickness ignored, no real thread/membrane/vent. Runtime3disconnected solids. DT04 cutter shape differs from source02 and own documented tab size. EMC/IP compliance claims are unverified; cutter defaults require selected supplier drawing plus boolean/section checks.

**Steps**

- Separate the real environmental requirements from the industrial examples; choose seal/vent from the actual hardware.
- Declare the reference pressure/temperature and the model; check unit consistency and the assumptions.
- Draw up the wire list, routing, shield termination, crimp/tooling, and the assembly checks.

**Gates**

- Check cross-section/gland/mating and the real heat escape path; the vent model must carry the required characteristics.
- Do not claim IP/EMC from a mesh: an appropriate test method and data for the assembled unit are required.

**Limitations**

- The bolt spacing, membrane, EMC spacing, and pull force thresholds in the sources are not confirmed for this target.
- The boilerplate vent ignores thread/panel dimensions; looking sealed or compact does not confirm function.

## mechanisms-transmissions

Gears, reducers, shafts/bearings, sustained holding loads, and transmissions.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/70-cad-precision-robotics/gears-transmission-modeling.md` — read-verify; SHA256 `1975a92284d94b2b84cf09707c7594935f3bde34bf448b6624efb37a415dbe86`
  Caution: Static audit: root radius and tolerance arguments unused; root fillets not constructed.
- `knowledge/70-cad-precision-robotics/fasteners-seals-mechanics.md` — read-verify; SHA256 `870ac87843291f7991ff38c0d804fff817d743fac5e123b2c4ad667da68dfaa0`
- `knowledge/70-cad-precision-robotics/cad-precision-modeling.md` — read-verify; SHA256 `bc171eb925df0f536a5745c294496268eb8a31464c2044439d2a688051fc51f6`

### Steps

- Lock load, reach, duty, speed, efficiency, and the actuator envelope.
- Compute the worst-case moment including link, hand, and payload; distinguish continuous from stall torque.
- Build the reduction, bearings, fasteners, and cable space from real interfaces.
- Check backlash/collision/strength/thermal, then confirm with a bench test.

### Gates

- Mass/CoM/inertia are tagged with units and the geometry revision.
- Continuous torque has the required margin; do not take a stall rating as sustained holding.
- Gear profile/root/contact and bearing load are checked against the drawing/calculation.
- Stay BLOCKED while actuator specifications or a physical test are still missing.

### Limitations

- The gear KB snippet lacks the root fillet it describes; the tolerance parameter is not implemented.
- Holding a 250 g arm load for several minutes is BLOCKED; do not flip it to PASS from an animation.
- No shipped example screens sustained holding torque; compute and declare a gravity/torque bound for the actual load case instead of borrowing one.

### Topic: contact-wear-sealing

When: When wear/leakage/bearing/bushing/seal duty is required.

- `research/advanced-tribology-contact-mechanics/01-HERTZIAN-CONTACT-STRESS.md` — read-verify; SHA256 `345be386539b7a407d38d5759f2cf363530b59ac69f86d5f69b837baebafc0c2`
  Caution: Source mixes subsurface depth values across line/point contact; resolve regime and equations before calculation.
- `research/advanced-tribology-contact-mechanics/02-TRIBOLOGY-LUBRICATION-STRIBECK.md` — read-verify; SHA256 `38b7690b920d9c43be0c88082e2b77fcd8a515424044318a14f7e4c59a460496`
  Caution: Quantity called dimensionless reduces to length with declared units; zero-wear and360deg purge prescriptions are not general rules.
- `research/polymer-additive-manufacturing-advanced/04-POLYMER-TRIBOLOGY-GEARS-BUSHINGS.md` — read-verify; SHA256 `e39d9245c95345dc96524d23523f7df90f4ea7b4e14852bb4030f5191a7589ca`
  Caution: PV/process tables and resistance units require source data; flash-temperature expression contains undefined Wbt.
- `research/mechanical-engineering-foundations/04-FLUID-POWER-SEALS-O-RINGS.md` — read-verify; SHA256 `34d279fbc34d937346a4ed6f509aba7e267c80e69094eba6dfa42a26a058f175`
  Caution: Fraction/percent notation changes; verify selected gland, seal, fluid, temperature and tolerance against actual drawing.

**Steps**

- Ghi material pair, contact regime, load/speed/finish/lubrication/seal duty.

**Gates**

- Check that the units/equations match the contact regime and the hardware data.
- Measure local fit; test wear/temperature/leakage physically before any performance claim.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: cycloid-profile-kinematics

When: Only when a cycloidal reduction has already been chosen.

- `research/advanced-tribology-contact-mechanics/03-CYCLOIDAL-SPEED-REDUCERS-MATHEMATICS.md` — read-verify; SHA256 `ccbc9d27cd6404d81249e90b47d522b9180bc8f57c79642b814d4a94b19e481d`
  Caution: Cusping/undercut criterion and universal coefficient range lack derivation; K1<1 alone is not manufacturability proof.
- `scripts/generate-cycloid-drive.py` — inspect-adapt; SHA256 `1364eb417d11e4a4a189864b1a0bc126ed5cf56dc7ded9e8484bf828edd018e8`
  Caution: main deletes all objects; fixed profile sampling, incomplete drive/housing and no ratio/contact/manifold checks. Raw count/success text is not acceptance.

**Steps**

- Lock pins/lobes/eccentricity/phase/output holes/bearings.
- Build a separate candidate; the adapter is a reference source only.

**Gates**

- Check profile convergence, self-intersection, and bores/walls on the evaluated mesh.
- Sweep a full input revolution per the contract; check clearance and the output ratio.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.
- The generator wipes the scene, does not build the complete drive, and does not prove ratio/manufacturability by itself.

### Topic: actuator-duty-thermal

When: When payload, sustained holding, or repeated cycling drives the actuator choice.

- `research/advanced-tribology-contact-mechanics/04-ACTUATOR-INERTIA-MATCHING-THERMAL.md` — read-verify; SHA256 `8cfcba1b7133177b918f05c264e91ba79aeef71b7a43c32919b384d96a76b5da`
  Caution: Optimal ratio equation needs dimensional review; stated Cth*Rth gives25–300seconds, not5–15minutes. Pulse/peak-current envelope unvalidated.

**Steps**

- Build the torque/speed trajectory, the mass/inertia revision, and the electrical/thermal model.

**Gates**

- Check units, the motor/driver source, and continuous versus peak limits separately.
- Check the thermal response with a real duty test before any loaded-hold claim.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: parametric-gear-profile

When: When building a spur gear from an involute profile with BMesh.

- `scripts/boilerplates/cad_mechanics/bp_involute_gear.py` — inspect-adapt; SHA256 `5af44abbd8678d9e1a5e1eea10153a1fa06c5029c4a1637bdb9753104ae2ade4`
  Caution: Deletes same-name object/shared mesh; no helical/root-fillet implementation; flank phase/root geometry need validation; face count is not gear correctness.

**Steps**

- Lock module, tooth count, pressure angle, backlash, and face width against load/drawing.
- Verify the flank/pitch/root formulas; create the candidate mesh before mounting it into the transmission.

**Gates**

- Measure pitch tooth thickness and profile error at several sample counts; check root, bore, and manifoldness/self-intersection.
- Sweep the gear pair; measure ratio/interference/clearance; check load and material separately.

**Limitations**

- There is no helical/root fillet as the header claims; a geometry sample does not prove the gear is correct.

## robotics-links-simulation

Robot links, URDF, coordinate frames, collision, and inertia.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/70-cad-precision-robotics/robotics-urdf-mechanisms.md` — read-verify; SHA256 `dbd386d203b4e9f109a874f873fada6fd12aaab46016e04ed948d8e25f95174e`
  Caution: Static audit: named hull block decimates only; inertia block formats values; diagonal positivity is incomplete. Verify frame conventions independently.
- `knowledge/40-animation/rigging-armature.md` — read-verify; SHA256 `dd5b6f0feebbfb0d58ae1aed6963261ed8e5f09e96f16ece6e031b8b88671889`
- `knowledge/60-pipeline/export-interchange.md` — read-verify; SHA256 `54a6aba3dcdb747009017f27b30d874ac5453f4d137d4ec6186b036c37d23c0c`

### Steps

- Lock the coordinate system of each link/joint and SI units at the export boundary.
- Separate visual, collision, and physical properties; check mass/CoM/inertia with a validated method.
- Export the articulation and import it into the target simulator.
- Compare pose/pivot/limit, collision shape, and physical response against expectations.

### Gates

- Do not apply a fixed rotation from a software name alone; verify the basis vectors and the forward axis.
- Collision shapes are actually checked for convexity/simplicity; decimation does not prove convexity.
- The inertia tensor is symmetric and positive definite, shown by eigenvalues or principal minors.
- The round trip preserves link hierarchy, scale, and limits; the simulator test is saved.

### Limitations

- The URDF snippet currently formats the inertia passed into it; it does not compute inertia.
- The collision and tensor snippets in the KB do not carry the required predicates.
- Do not run or install a simulator merely because research was read.

### Topic: dynamic-harness-routing

When: When routing wiring from the controller across moving joints, or designing a carrier/drag chain.

- `knowledge/70-cad-precision-robotics/industrial-connectors-wire-harness.md` — read-verify; SHA256 `8835efc6e74d6ba2c45d0a0f0b2fc9b75e3b10d39a2af967511598b6a74fae1c`
  Caution: Lines36-49/154-158 present universal flats, bend and EMC spacing; treat as unverified task-specific inputs. Lines109-130 accept min_bend_radius but never use it; no curvature/strain-relief enforcement. Dimensions and connector coding require selected part drawings.
- `research/industrial-wiring-harness-packaging/03-CABLE-MECHANICS-FLEX-LIFE-DRAG-CHAINS.md` — read-verify; SHA256 `9505da833fe0db557b3385b4c94251829a5e5926ce37c86ed8987d98049256c6`
  Caution: Lines23-26 conductor class is not cycle-life qualification; generic radius, torsion/free-length and20-50N retraction values are unverified for target hardware. Chain neutral-axis layout, cable length/bend/torsion and endpoint strain relief require per-pose checks; no physical life proof.
- `research/robotics-precision-cad/12-INDUSTRIAL-WIRING-CONNECTORS-HARNESS-ROUTING.md` — read-verify; SHA256 `6ac53feff1fdfe7a1f10cb7e12875c130f24ecfb966357f6c80a6ca74754ed04`
  Caution: Generic cutout offsets, connector dimensions, EMC categories and breather mandate are unverified; source02 differs for RJ45 bayonet dimensions and source01 differs for PROFIBUS termination. Do not infer suitable terminal/contact selection from protocol or pitch; verify selected part and cable specification.
- `scripts/boilerplates/cad_mechanics/bp_cable_dragchain.py` — inspect-adapt; SHA256 `d1a95bc9acd1f7473c037a5716cb53dd9214ea38c865cb25c4489e972c79d978`
  Caution: Lines34-35 silently cap bend radius below own required minimum; negative dimensions yield negative link count. Lines71-76 production socket/stop claims exceed construction: runtime9disconnected primitive solids, no sockets/stops/union. Assembly poses are visual candidates; rated cable radius/torsion, link interference, fastening and endpoint strain relief unverified.

**Steps**

- Lock the endpoints, the real cable, connectors, bend/torsion limits, and the free length.
- Build the route for each joint pose; compute length, curvature, and clearance from the mechanism.
- Design retention/strain relief; check link sockets, stops, and fastening before calling the chain functional.

**Gates**

- Reject negative inputs and silent radius caps; measure minimum radius/length/torsion at the extreme poses with explicit units.
- Check chain interference and the connectivity of each link; test physically with the selected cable/link before claiming cycle life.

**Limitations**

- A curve reveal does not preserve length or prove real routing.
- The boilerplate currently creates detached primitives and lacks sockets/stops; a conductor type does not certify flex life.

## render-export-delivery

Caption-free video, batch rendering, encoding, and export/re-import.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/30-lighting-render/render-engines.md` — read-verify; SHA256 `a241aa51cbfffb4bd67aca186e5605e158049a88e2fac1d569de308fa44d8dfb`
- `knowledge/30-lighting-render/compositing-output.md` — read-verify; SHA256 `ce19c33464e1ea8ef58cc5c686406eb3d227272c4cc1feb98a4c361e1c42f2ab`
- `knowledge/60-pipeline/export-interchange.md` — read-verify; SHA256 `54a6aba3dcdb747009017f27b30d874ac5453f4d137d4ec6186b036c37d23c0c`

### Steps

- Lock the source hash, camera, frame range, fps, aspect ratio, and overlay/audio requirements.
- Measure the render profile on a representative frame in a separate process.
- Render raw frames with a dedicated output/range and verify the frame count is complete.
- Encode/decode or export/re-import the correct artifact; review the motion timing as well.

### Gates

- Python errors must return nonzero and carry a postcondition; a shell exit 0 is not enough.
- Missing/corrupt/mixed-revision frames are rejected before encoding.
- Duration/fps/resolution/range match the brief; the video carries no text when the user asked for none.
- Review the exact hashed file; record the technical results and the visual quality separately.

### Limitations

- The headless wrapper does not yet exit explicitly on a Python error; use the explicit CLI form from the core recipe.
- The video example hardcodes this build ffmpeg paths, 24 fps and frame identity, and leaves visual review PENDING; adapt the contract to the task.
- Do not resume on the basis that a file exists; stale-evidence enforcement E1–E5 is still backlog.

### Topic: renderer-diagnostics

When: When CPU/Metal measurement, sampling, or a renderer-limit comparison is needed.

- `research/blender-rendering-deep-dive/01-PATH-TRACING-CYCLES-ARCHITECTURE.md` — read-verify; SHA256 `1ca697b7e8199900a9c8b6d070d63efa52b249878bfdc8f240038ddceb03c4de`
  Caution: GPU-only preset is not measured device selection; backend is not enabled by device assignment alone. Bounce/clamping no-bias and95% claims unverified.
- `research/blender-rendering-deep-dive/02-EEVEE-NEXT-REALTIME-RENDER-PIPELINE.md` — read-verify; SHA256 `44c0b09d2b7ecb81e4f72f83e9409234007ef6e884d504a444b7285ee1f2896b`
  Caution: Legacy engine identifier and universal Metal mandate conflict with current project runtime-introspection and measured CPU/Metal policy.
- `scripts/boilerplates/bp_render_camera.py` — inspect-adapt; SHA256 `a0462c9844057b058c04e855b47d26c21be2513adb242a74288e9b9ae20e90e2`
  Caution: GPU backend chosen by enumerating get_devices_for_type per backend (returns METAL on this Mac); never gates on the empty compute_device_type enum. Changes backend preferences and deletes named camera/lights in its self-test.

**Steps**

- Benchmark a representative frame at the same resolution/source; choose the device from the measurement.
- Keep batch rendering on Cycles per policy; use EEVEE only when its capability is confirmed.

**Gates**

- The engine/device is actually enabled, and timing and settings are recorded.
- Compare noise/detail and reflection artifacts; speed does not replace quality.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.
- Do not inherit a GPU/Metal-only or bounce preset from research.

### Topic: participating-media

When: Only when the scene has haze/cloud/volume that must be controlled.

- `research/blender-rendering-deep-dive/03-VOLUMETRIC-SCATTERING-ATMOSPHERICS.md` — read-verify; SHA256 `3398c162a9916827d9f8cecf08f61be50dde18b4079a93242e14a05684d008ca`
  Caution: Universal zero-banding/integrator claim is not proven by stepping snippet; fixed100-unit cube/density is not scene-scale calibration.

**Steps**

- Lock volume bounds, density, and path-length assumptions.
- Compare against a baseline with the atmosphere off to isolate exposure/material defects.

**Gates**

- Bounds/density are finite and consistent with the scale.
- Review banding, light shafts, transmission, and product readability.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: color-denoise-delivery

When: When highlight/output colors or temporal noise need diagnosis.

- `research/blender-rendering-deep-dive/04-COLOR-MANAGEMENT-AGX-ACES.md` — read-verify; SHA256 `92ad6a1fe1eb4909477b6b9a90821f2aaba9f29b4718a0b40c453b846ea0a7b0`
  Caution: Hardcoded color/look/sequencer values omit an actual EXR output-space contract; sRGB and Rec709 transfer assumptions need qualification.
- `research/blender-rendering-deep-dive/05-DENOISING-OIDN-OPTIX-TEMPORAL.md` — read-verify; SHA256 `bfbe6228752fb87ad29ed1e75868cf2d3d5e63ceee83b1287b64703bc7a51da3`
  Caution: Snippet clears legacy scene compositor, assumes ViewLayer and pass sockets; conflicts with current KB. No real EXR setup or disocclusion rejection in shown blend.

**Steps**

- Lock display/view/look/exposure and the output encoding separately.
- Keep the raw noisy evidence; check the guide passes before wiring up the denoiser.

**Gates**

- Introspect compositor/pass sockets; the EXR contract has a real configuration.
- Compare raw/denoised crops and consecutive clips: no detail loss, ghosting, or boiling.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.
- Do not delete an existing compositor or treat a minimum sample count as a guarantee.

### Topic: framing-export-contract

When: When auto-framing the camera or exporting GLB/STL through an adapter.

- `scripts/boilerplates/pipeline_render/bp_export_pipeline.py` — inspect-adapt; SHA256 `f2499c0298d379263e2e8f2078d06ddbbfa6ca326a19e756c4b97290c0ce2ae1`
  Caution: Export operator FINISHED and file existence do not prove watertightness, units, contents or round-trip fidelity. Uses current selection/context and unvalidated output paths; self-test writes/deletes fixed /tmp filenames. Source citations are not export validation.
- `scripts/boilerplates/pipeline_render/bp_cam_autoframing.py` — inspect-adapt; SHA256 `78234a210fb236dcd25a08b9cd2faddca9c1976fd9f6cdb4deb200f13d2ce780`
  Caution: Only horizontal FOV/sensor_width considered; ignores render aspect, sensor fit, shift, clipping and orthographic cameras. Original bound_box may omit evaluated deformation. Reuses TRACK_TO and named target, assumes world values equal local location. Distance >2 test does not prove framing.

**Steps**

- Lock the object selection, evaluated bounds, camera type/aspect, and the candidate's output path.
- Adapt framing for both FOV axes; export with the units and properties the contract requires.

**Gates**

- Project the evaluated bounds through the camera, check both X/Y and near/far clipping at every required pose; review the rendered image.
- Read the artifact back independently and check object/count/bounds/units/materials per format; STL needs its own topology and tolerance checks.

**Limitations**

- FINISHED, an existing file, or a camera distance does not prove the output is correct.
- The helper can change an existing target/constraint and write to a hardcoded path; do not run its self-test on a production scene.

## native-procedural-simulation

Geometry Nodes, patterns, instances, and simulation/caches using Blender-native tools.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/50-procedural/geometry-nodes.md` — read-verify; SHA256 `4e4dc95e1d559e39c4446d62b3a2b9ea6abbd85e35e461b25b15a2abf6c981a6`
  Caution: Vertex-count growth does not verify pure instancing, and fixed-topology simulation need not change vertex count. Check instance counts/transforms or expected simulation state; require topology growth only if the task specifies it.
- `knowledge/50-procedural/simulation-physics.md` — read-verify; SHA256 `eeb6afd6ebdb67b9743da7945d30891d46756145c4cfb4d99d780d33fe0abc00`
- `knowledge/10-modeling/modifiers.md` — read-verify; SHA256 `88f4e06ffc4d5b9f74db1d00f2c0a95cee35cbe28a8248ab12b19dbf8f6a1ff1`

### Steps

- Lock procedural inputs, units, seed, instance domain, and the output contract.
- Introspect nodes/sockets/zones at runtime; blockout a small graph first.
- Check evaluated geometry/instance transforms and the cache on a representative frame.
- Bake/render a separate candidate and review the result across multiple frames.

### Gates

- Counts/attributes/instances match the input; changing an input changes the output as specified.
- The evaluated result and the export are not missing instances/modifiers.
- The cache is tagged with a revision and a frame range; replaying the candidate gives the correct result.
- Review visuals and timing after the numeric checks.

### Limitations

- A simulation mesh does not by itself prove real material or real hardware.
- The physics cache and the node API depend on the runtime; do not recall the version from memory.

### Topic: fields-parametric-solids

When: When field domains, attributes, or parametric mechanical shapes are the goal.

- `research/blender-geometry-nodes-procedural/01-FIELDS-ARCHITECTURE-EVALUATION-MODEL.md` — read-verify; SHA256 `e067dbda62c98c67b8de34cb27377d9106a61e166d5c788fbd29f8566ce2dc99`
  Caution: Snippet clears node interface. Universal zero-memory/interpolation/persistence claims exceed evidence; test consumer domain and data type.
- `research/blender-geometry-nodes-procedural/02-PROCEDURAL-HARD-SURFACE-CAD-MODELING.md` — read-verify; SHA256 `1fa9d830e42ba72055c9affa9ff59b3acf2537d9d1721681d7e6e61af9d552f3`
  Caution: Pipe snippet lacks interior bore; Boolean index-remap/solver and unconditional robustness claims need runtime inspection.
- `scripts/generate-procedural-geonodes.py` — inspect-adapt; SHA256 `294e8ea053d503b169b622bd9bbc804b830f4ecb6161fa1efca9e5baec07e76d`
  Caution: main deletes all objects. Graph omits advertised four mounting holes/stress_zone; fixed cutter/boss do not cover input range. Attribute existence alone is not validation.
- `scripts/boilerplates/bp_geonodes.py` — inspect-adapt; SHA256 `769758b062e335afca97b87d871a6c4e5f78f8b67f2647669e28327eb8bf1021`
  Caution: Named node group deletion is global. Missing node group returns silently; input fallback unverified. Self-test checks nonempty geometry, not parameter behavior.
- `scripts/boilerplates/bp_bmesh_cad.py` — inspect-adapt; SHA256 `c68939cd8ecf5e31c0b0b577e14f7c742af3ace3debd6bd8f0e940161d327086`
  Caution: Named global data deletion and modifier baking replace mesh/clear stack. Manifold flags do not prove winding, self-intersection, dimensions or clearance.

**Steps**

- Lock input ranges/units/schema/consumer domains.
- Introspect the sockets, then check a parameter matrix that includes the boundary values.

**Gates**

- Measure evaluated dimensions, hole/component counts, and topology.
- Check the actual attribute name/domain/type/distribution; review cross-sections and shading.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.
- The adapter lacks the four mounting holes its header claims; its main routine deletes every object.

### Topic: simulation-repeat-budgets

When: When state across frames, substeps, branching, or an iterative solver is required.

- `research/blender-geometry-nodes-procedural/03-SIMULATION-ZONES-PHYSICS-SOLVERS.md` — read-verify; SHA256 `8959b378ecad521c39fe3fd915c6b65a655d04c84830314a61adad76136a07c0`
  Caution: Indefinite stability/fixed substep/cache guarantees unproven; boids formulas lack empty-neighborhood/coincident guards.
- `research/blender-geometry-nodes-procedural/04-REPEAT-ZONES-FRACTALS-RECURSION.md` — read-verify; SHA256 `ac7657d383102eec3294e8bc24af5d101ffdd7bf867e18c08c38c073e2a7adf1`
  Caution: 0.707 is mislabeled golden-ratio decay; fixed iteration/resource claims unverified. Position smoothing does not guarantee equilateral quads.
- `scripts/boilerplates/bp_physics.py` — inspect-adapt; SHA256 `310830e00597192f942742ea24a580ba26f1a04e65bf75c8a632fc523201ccea`
  Caution: World setup uses operators; linking a collection is assumed to create rigid_body immediately. Cache frame stepping lacks clear/bake/context restoration; isolate and verify actual world membership.

**Steps**

- Separate inter-frame simulation from the intra-frame loop.
- Lock timestep/state/seed/cache revision; handle empty/coincident neighborhoods.
- Compare two timestep/substep candidates and estimate the growth before running.

**Gates**

- No NaN/Inf; count/time/memory stay within the task budget.
- Measure convergence/state residual and replay; do not require vertex growth with fixed topology.
- Review tunneling/stability/feature loss over time.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: sdf-feature-preservation

When: When choosing SDF boolean or volume remesh for a native candidate.

- `research/blender-geometry-nodes-procedural/05-VOLUME-GRIDS-SDF-BOOLEANS.md` — read-verify; SHA256 `420beb9331f727a560f9e3fcab806dfc7d08e47c37405017e37db4879dd4d233`
  Caution: Named smooth subtraction has no smoothing parameter; guaranteed manifold/print-ready/half-wall preservation is not established.

**Steps**

- Distinguish fog grid, distance grid, and isovalue.
- Choose voxel size against feature size and memory; keep the original.

**Gates**

- Compare topology, openings, local walls/clearance, and deviation at two resolutions.
- Review cross-sections and the camera-matched sheet: no filled-in holes or removed walls.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.
- SDF does not by itself guarantee manifoldness/print-readiness, nor preserve a wall through a half-wall rule.

### Topic: graded-lattice-reinforcement

When: When a lattice or reinforcement targets a specific mass/stiffness goal.

- `research/advanced-tribology-contact-mechanics/05-TOPOLOGY-OPTIMIZATION-LATTICES.md` — read-verify; SHA256 `e83faf7df5baa6639cdefeeb8484d463241f31e9bd2355f3134eb2a199a6f930`
  Caution: generate_gyroid_mesh only builds arrays/prints density; creates no Blender geometry or SIMP optimization. Field threshold is not physical wall thickness.
- `research/polymer-additive-manufacturing-advanced/02-CONTINUOUS-FIBER-COMPOSITES-CFRTP.md` — read-verify; SHA256 `6e4260f9be456a71959911ba1af3882f1c6b5868dca4edcb819050fd71ed2667`
  Caution: Quasi-isotropic in-plane layup does not justify zero directional weakness/warping claims for arbitrary through-thickness print behavior.

**Steps**

- Lock cell size/local wall/boundary/load paths and fiber directions.

**Gates**

- A real mesh, density/wall figures, and resolution convergence are required; a field preview is not a mesh.
- Check orientation/boundary condition and physical stiffness separately.

**Limitations**

- Research sources do not certify APIs or figures; verify against the runtime and the origin per the task's requirements.

### Topic: procedural-component-adapters

When: When adapting a parametric cable/tube or flange graph.

- `scripts/boilerplates/geometry_nodes/bp_gn_cables.py` — inspect-adapt; SHA256 `5212fe937edc66bab7b449d0232199ae768b21cc4bd98325e447c433df97eee0`
  Caution: Sag input unused; graph generates a straight tube despite catenary header. Replaces named group and leaves test object. Nonempty mesh does not verify sag, dimensions, caps or clearance.
- `scripts/boilerplates/geometry_nodes/bp_gn_pipe_flange.py` — inspect-adapt; SHA256 `7e7ea9168e56dc6d4c677a548e3815d46786ca9845c479f3402b4fc3685991e1`
  Caution: Disc-minus-bore only; promised Hub Length, bolt pattern and ASME dimensional/class contract absent. Positional Boolean sockets need runtime inspection; replaces group; nonempty-mesh test only.

**Steps**

- Lock the component shape, input ranges, and output measurements; do not take a header as a contract already met.
- Inspect the actual nodes/sockets/interface; add the missing features in a separate candidate.

**Gates**

- Measure endpoint/midpoint when changing Sag, diameter, OD/bore/thickness, and hole count per component.
- Check valid/invalid boundaries, caps/components/manifoldness, and cross-section/render; only a real drawing determines what the flange needs.

**Limitations**

- The cable currently ignores Sag; the flange is only a disc minus a bore, with no hub/bolt pattern.
- A nonempty mesh is not enough to prove the graph acted on the input.

## native-character-creature

Build a humanoid or creature that must deform: proportions, animation topology, facial blendshapes, hair/skin shading, IK rig and walk cycle.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/15-character-creature/character-creature-modeling.md` — read-verify; SHA256 `a185251e5024b5d00ec85118711558515687cde1d7f8ab8b8042c52c90f9678d`
  Caution: Anatomy/proportion tables and the SSS radius and scale values are artistic or literature figures, not standards - the ones the audit could not confirm are marked UNVERIFIED inline. The 52 ARKit targets are Apple's spec, not FACS AUs and not ISO/IEC 14496-2.
- `knowledge/10-modeling/modeling-topology.md` — read-verify; SHA256 `1b24a3089c56d919a90b1717ce805592229479c03a3db9bc73697e3d4ddc3608`
- `knowledge/40-animation/rigging-armature.md` — read-verify; SHA256 `dd5b6f0feebbfb0d58ae1aed6963261ed8e5f09e96f16ece6e031b8b88671889`
- `knowledge/40-animation/animation-fcurves.md` — read-verify; SHA256 `1d0bc0a7456fb7dc092737f0d8f92b4aecc6d954061ace4fc6e07b9feaa9df81`
- `knowledge/20-shading/materials-pbr.md` — read-verify; SHA256 `e455cc41465700c56266f5d9652adae920972e941644b27085b2982ab3fa8705`

### Steps

- Contract first: humanoid or creature, locomotor posture, stature canon, delivery target (render / game / print) and whether the face must be capture-driven.
- Blockout to the proportion canon and get the silhouette signed off before any detailing; measure stature and landmarks, do not eyeball them.
- Retopologise to animation topology: closed facial loops, three-loop hinges, poles pushed onto bony planes.
- Rig (IK + pole targets + twist bones), skin, and only then add blendshapes, hair curves and skin/hair shading.
- Verify numerically at every step; review a short animatic before any long render. Endpoint poses do not prove motion.

### Gates

- Stature within the declared canon's +/-2%; landmark elevations measured against the head unit.
- Deforming zones are all-quad with no extraordinary pole on a crease or hinge line; eyelids close without inversion.
- Weights are finite, non-negative, sum to 1.0 per vertex, and no control bone owns a vertex group.
- Walk cycle F-curves close the loop at frame T and the anti-phase / bounce-frequency relations hold numerically.
- Shader node trees have no dangling outputs; hair data-blocks contain actual curves (len(curves) > 0).

### Limitations

- Every mesh generator in this pack is a PROXY (primitive union, quad-dominant, non-manifold, unweighted). None is animation-ready; retopologise before rigging and never claim all-quad topology from them.
- Anatomy, proportion and biomechanics numbers come from cited literature and were NOT verified by the onboarding audit; only the bpy API names and the modules' own postconditions were.
- Facial capture readiness is not demonstrated: 46 of the 52 ARKit targets are named identity keys with no sculpted delta.
- Nothing here covers cloth, muscle simulation, or physical printability of a character; a character intended for print still needs specs/build-spec.schema.json and production-gate.py.
- There is no worked character build in builds/ yet, so the workflow has no adapter examples - only boilerplates.

### Topic: character-proportion-anatomy

When: When humanoid or creature proportions, stature canons, or limb posture must be fixed before any detailing.

- `research/character-creature-anatomy-modeling/01-HUMAN-ANATOMICAL-PROPORTIONS-CRANIOFACIAL.md` — read-verify; SHA256 `0926c81b148993aa204b3938748607becfd5f0964e4e6b2eab00bf6af312415b`
  Caution: The FLAME vertex count is flagged UNVERIFIED. SMPL-X/FLAME are cited as shape-space mathematics only - their model files are separately licensed third-party assets and must not be downloaded or vendored.
- `research/character-creature-anatomy-modeling/02-CREATURE-COMPARATIVE-ANATOMY-LOCOMOTION.md` — read-verify; SHA256 `8b4677f1408272d8840d45d2947668f8f5db7846485f61f351d1e0862af2dae8`
  Caution: Limb-length and elastic-recoil ratios are literature summaries flagged UNVERIFIED; the chimeric/monster sections are design reasoning, not biomechanics results.
- `scripts/boilerplates/character_creature/bp_humanoid_basemesh.py` — inspect-adapt; SHA256 `48f5bcc2ae2460dae78e17d64e3e925ca2d2dc4435c1e6cc998458b4e1d9b09f`
  Caution: PROXY only: primitive union, quad-dominant not all-quad, non-manifold, hinge 'loops' are separate disc primitives, vertex groups carry no weights. Retopologise before rigging.
- `scripts/boilerplates/character_creature/bp_creature_digitigrade.py` — inspect-adapt; SHA256 `2c6d7ba67b19d8ad18568d2bc282d5ce3623db034722a3a3fa2f67111d30c379`
  Caution: Skeletal LAYOUT proxy: the reusable content is the segment angles (femur +35, tibia -40, metatarsus +25 deg), not the surface. Cone caps are n-gons; groups are unweighted.

**Steps**

- Declare stature, head-unit canon and sex/species archetype BEFORE geometry; peg every landmark elevation to the head unit.
- For a creature, pick plantigrade / digitigrade / unguligrade first: it changes the whole hindlimb chain, not just the foot.
- Blockout with the proxy generators, measure the stature and landmark elevations, then retopologise before rigging.

**Gates**

- Measured stature within the declared canon's +/-2%; soles on the floor plane; knee and chin bands at their head-unit elevations.
- For a digitigrade limb, the hock measures clearly above ground and knee > hock > paw descends monotonically.
- Quad fraction and non-manifold edge count are reported as numbers, not asserted as 'clean'.

**Limitations**

- Both generators emit a PRIMITIVE UNION, not a basemesh: ~86% / ~73% quads, 16 non-manifold edges on the humanoid, n-gon cone caps, and the 'three-loop hinges' are separate disc primitives rather than edge loops.
- All landmark vertex groups are created EMPTY; nothing is weighted until a separate skinning pass runs.
- Proportion tables, sexual-dimorphism angles and locomotion scaling ratios are cited from the literature but were not verified by this audit.

### Topic: animation-topology-facial-loops

When: When deciding edge flow, pole placement, facial loop layout, or a polygon budget for a deforming character.

- `research/character-creature-anatomy-modeling/03-ANIMATION-TOPOLOGY-EDGE-FLOWS-FACIAL-LOOPS.md` — read-verify; SHA256 `917013bfac2105dc2d582f6821e52c0deb3d8c7f6888839c748d2e54b283d7a4`
  Caution: Hippolyte (2007) and Zander et al. (2004) could not be confirmed and are marked UNVERIFIED in the file; polygon budgets are rules of thumb, not standards.

**Steps**

- Route the four closed facial loops (orbicularis oculi, orbicularis oris, nasolabial, mandibular collar) before adding density anywhere else.
- Push every unavoidable valence-3/5 pole onto a rigid bony plane and keep poles at least three loops away from any crease or hinge line.
- Fix the polygon budget against the actual delivery target, then measure the mesh against it.

**Gates**

- Zero non-quad faces in deforming zones; zero extraordinary poles on eyelid rims, lip borders or hinge lines.
- Eyelids close to a 0 mm gap without triangle inversion; the mouth pucker and stretch shapes do not tear.
- Face and body quad counts are measured, not estimated.

**Limitations**

- The polygon budget table is industry rule-of-thumb, explicitly marked UNVERIFIED by the 2026-09-06 audit.
- Two of its six citations (Hippolyte 2007, Zander et al. 2004) could not be confirmed offline and are flagged in the file; the Catmull-Clark continuity claims stand on citations 1-2.
- This document is topology theory only: no runnable code and no mesh is produced or checked by it.

### Topic: facs-blendshape-targets

When: When building facial shape keys, ARKit-compatible capture targets, or combination corrective drivers.

- `research/character-creature-anatomy-modeling/04-FACS-FACIAL-BLENDSHAPES-SHAPE-KEYS.md` — read-verify; SHA256 `47e1438fa1d1a316adb57d25015628019234628d3769e37ef8f91e9e1c6975ca`
  Caution: The 52 ARKit targets are NOT FACS Action Units and NOT ISO/IEC 14496-2 (MPEG-4 FAPs); cite Apple's spec. Blendshape orthogonality is a modelling convention, which is why correctives exist.
- `scripts/boilerplates/character_creature/bp_facs_blendshapes.py` — inspect-adapt; SHA256 `8e611f7688efd291b95f52ebf779b4ac7d69e5cfd4a39919bcb8427948acb903`
  Caution: Only 6 of 52 targets carry sculpted deltas; the rest are identity keys. The head is a scaled UV sphere with no facial features. ARKit spec, not FACS AUs, not ISO/IEC 14496-2.

**Steps**

- Create the full 52-target ARKit inventory with clamped [0, 1] sliders, then record separately how many targets actually carry sculpted deltas.
- Author combination correctives as scripted drivers on the product of the two contributing weights and evaluate the depsgraph to prove the product.
- Use foreach_set for bulk vertex displacement; per-vertex Python loops do not scale to a real head.

**Gates**

- 52 unique target names present, Basis first, all sliders clamped to [0, 1].
- The corrective key's driven value equals w_a * w_b after a view-layer update (measured, not assumed).
- Count of targets with non-zero displacement is stated explicitly in the delivery note.

**Limitations**

- The boilerplate sculpts only 6 of the 52 targets (jawOpen, mouthSmile L/R, eyeBlink L/R, browInnerUp); the other 46 are correctly-named IDENTITY keys, not expressions.
- Its head is a scaled UV sphere: no eye sockets, lips or nostrils, and triangle fans at both poles. It exercises the plumbing, it is not a face.
- The ARKit 52 are Apple's product spec, FACS-inspired; they are NOT Ekman Action Units and NOT ISO/IEC 14496-2 (that standard defines MPEG-4 FAPs). The research file's original heading claimed otherwise and was corrected by the audit.

### Topic: hair-curves-grooming-shading

When: When grooming hair or fur on Blender 5.2 Curves, or shading skin and hair with the Principled BSDF / Principled Hair BSDF.

- `research/character-creature-anatomy-modeling/05-BLENDER-HAIR-CURVES-SKIN-TISSUE-PHYSICS.md` — read-verify; SHA256 `459b49ef08da6612390a492e22efdc2524183221fa72edf2d4a45449b0eae590`
  Caution: The original snippet (bpy.data.curves.new(..., 'CURVES') and Object.surface) does not run in 5.2 and was replaced. Legacy particle hair is NOT removed in 5.2. Spitieris & Bergou (2012) is flagged UNVERIFIED; prefer Bergou et al. 2008/2010.
- `scripts/boilerplates/character_creature/bp_hair_curves_gen.py` — inspect-adapt; SHA256 `b5ae56714c849d3830cb652a27622faecfed64d9979769b9969e47c73314fd89`
  Caution: The node tree only re-tapers radius: no interpolation, clumping, frizz or curl. surface_uv_coordinate values are a deterministic placeholder, not baked from the scalp UV map.
- `scripts/boilerplates/character_creature/bp_fur_hair_shader.py` — inspect-adapt; SHA256 `a9904d4ae5c086900ba4973d7e9ad1d59fd06d95cb4f575a4ca529ece6228df2`
  Caution: Melanin/redness phenotype values are artist guidance, not measured pigment concentrations. 5.2 names the strand-info node 'Curves Info' even though it is created as ShaderNodeHairInfo.
- `scripts/boilerplates/character_creature/bp_skin_sss_shader.py` — inspect-adapt; SHA256 `2fa9c2a68e5ccf3022bb62eaf0e66ef46db1f5506b5e0d93380243555dd891bc`
  Caution: subsurface_method must be set BEFORE Subsurface IOR (that socket is disabled and unreachable by name under the default BURLEY). Radius (1.0, 0.22, 0.08) and scale 0.025 m are look choices; Blender's defaults are (1.0, 0.2, 0.1) and 0.005 m.

**Steps**

- Create the data-block with bpy.data.hair_curves.new(name), set surface + surface_uv_map on the DATA, then call add_curves() and write points[i].position/.radius.
- For skin, set subsurface_method = 'RANDOM_WALK_SKIN' BEFORE reading or writing Subsurface IOR; a disabled socket is not reachable by name.
- Drive root-to-tip hair variation from the strand-info 'Intercept' output into 'Tint'; verify no node output is left dangling.

**Gates**

- len(curves_data.curves) > 0 and per-strand arc length within the declared strand_length band; radius tapers root to tip.
- Principled Hair BSDF reports parametrization 'MELANIN' and model 'CHIANG'; Principled BSDF reports 'RANDOM_WALK_SKIN' and the intended radius triple.
- Every non-output shader node has at least one linked output (a dangling colour ramp renders nothing and passes naive checks).

**Limitations**

- The Geometry Nodes tree only re-tapers radius: there is no guide interpolation, clumping, frizz or curl node despite the pipeline diagram in the research file.
- surface_uv_coordinate values are written as a deterministic placeholder, not baked from the scalp UV map, so strands are not truly surface-bound yet.
- Subsurface radius (1.0, 0.22, 0.08) and scale 0.025 m are artistic values, not standards; Blender's own defaults are (1.0, 0.2, 0.1) and 0.005 m. Christensen-Burley (2015) describes the BURLEY method, not the random walk.

### Topic: character-rig-locomotion

When: When building a humanoid IK/FK armature, twist bones, automatic weights, or a procedural walk cycle.

- `research/character-creature-anatomy-modeling/06-SKELETAL-KINEMATICS-LOCOMOTION-SKIN-SHADING.md` — read-verify; SHA256 `eedfaf1542ece694fd65120771fa3bdeb0320d9211083b07f1eff4042be6451d`
  Caution: Christensen-Burley 2015 is the BURLEY method, not the random walk; Kavan 2007 is dual quaternion skinning, not twist bones. The Gaussian weight formula is NOT what the boilerplate implements. Hildebrand 1976 and Jimenez 2010 citation details are flagged UNVERIFIED.
- `scripts/boilerplates/character_creature/bp_humanoid_rig_ikfk.py` — inspect-adapt; SHA256 `079383f9db4a556a9e848af089205c28e8594993fc8b5b9da9c212d84f62d7a3`
  Caution: Binding is NEAREST-BONE hard assignment (one group per vertex at weight 1.0), not smooth skinning - smooth the weights before any deformation-quality claim. Dual quaternion skinning stays off unless use_deform_preserve_volume is set.
- `scripts/boilerplates/character_creature/bp_biped_locomotion.py` — inspect-adapt; SHA256 `220d14ce2637618e974f0f7dd9b35f797197caa2902793e51387c7a3832cdb43`
  Caution: A 5-key harmonic approximation, not a gait solve: no stance plateau so expect foot slide, and pelvis Z extrema fall at 0/T/2 rather than Winter's 12%/62%. Review an animatic before calling it a walk.

**Steps**

- Build edit_bones inside mode_set('EDIT') (the sanctioned operator exception), then wire IK with target + pole target + pole angle + chain_count = 2 through the data API.
- Exclude control bones from the deform set by scanning the WHOLE name for _IK / _Pole: side-suffixed controls like Hand_IK.L do not end with _IK.
- Key the walk on the slotted action, then measure loop closure, arm anti-phase, bounce frequency and chest counter-rotation numerically before rendering anything.

**Gates**

- Bone count and IK wiring measured; twist constraint copies only local Y at the declared influence.
- Weights: one entry per vertex summing to 1.0, no NaN, and zero control-bone vertex groups.
- F-curve values at frame 0 and frame T agree within 1e-4; left/right arm curves sum to ~0 at every frame; pelvis Z shows two extrema per stride.

**Limitations**

- The binder is NEAREST-BONE HARD assignment (one group per vertex at weight 1.0), not the Gaussian falloff the research file's formula describes: partition of unity and non-negativity hold, smoothness does not.
- The walk is a 5-key harmonic approximation, not a gait solve: no stance plateau (expect foot slide), and pelvis Z extrema land at 0/T-4/T-2/3T-4 rather than Winter's 12%/35%/62%/85%.
- Kavan et al. 2007 is the dual-quaternion-skinning paper cited for the candy-wrapper artifact; it does not propose twist bones. Dual quaternion skinning stays off unless use_deform_preserve_volume is set.

