# Audit 02 — Knowledge Base API Verification (falsification pass)

Read-only audit. Target: `knowledge/` vs the real local install
**Blender 5.2.0 LTS (hash fbe6228777e7, built 2026-07-14)**, Apple M4 Pro / macOS.
All probes: fresh `Blender --factory-startup -b --python-exit-code 23 --python <script>`.
GUI PID 14172 never contacted. Nothing under `builds/` opened. Scratch:
`/private/tmp/claude-501/.../scratchpad/kb-verify/` (probe1–5.py, v9.glb, cube_*.glb).

## Verdict

**The KB's "verified against 5.2" claim survives on facts and fails on executable helpers.**

- FACT — 62 of 67 machine-checkable *factual* claims PASS, including the hardest ones:
  the Principled BSDF 32-socket index→name table is byte-exact, every one of the 110
  glTF export kwargs exists (and the KB list has zero runtime extras), the FBX/USD/STL
  signature lists are complete, the slotted-Action API, bone collections, `media_type`
  ordering, boolean `'FLOAT'`, and the removed-operator claims are all correct.
  This is a genuinely well-verified reference layer — better than any Blender KB I would
  expect an LLM to produce from memory.
- FACT — but **4 of 11 copy-paste blocks executed verbatim fail or silently degrade**, and
  two of them are in the hot path of exactly this project's stated mission (headless Cycles
  render on Metal, headless rig build). An agent that trusts §4 code blocks the way the KB
  tells it to will ship a CPU render and a crashed rig script.
- INFERENCE — the failure signature is consistent: the *tables* were verified against source
  and docs; the *helper functions* were not executed on this machine. Three of the four
  failures come from one root cause — `bl_rna.properties[x].enum_items` returns `[]` or a
  static-only stub for **dynamic** enums (`engine`, `compute_device_type`, `denoiser`,
  `export_format`), yet three KB helpers gate behaviour on that list.

Blocking (fix before this KB is used for headless render/rig work):

1. `render-engines.md:149` `set_engine()` — raises `RuntimeError: CYCLES not available` on a
   working 5.2 Cycles install.
2. `render-engines.md:168` `enable_cycles_gpu()` — returns `'CPU'` on this Metal Mac; sets
   `compute_device_type='NONE'`. Silent 10–30× slowdown, no traceback.
3. `rigging-armature.md:135` `edit_armature()` — raises `RuntimeError` when the caller
   already linked the armature, which the KB's own §4.2 example does two lines earlier.
4. `export-interchange.md:280` `assert getsize > 2048` — a correct single-cube GLB is
   936 B (Draco) / 1400 B (plain). The KB's own success gate reports a good export as failure.

Non-blocking but wrong: 6 of the 24 "verified base socket idnames" in `geometry-nodes.md:185`
are rejected by `new_socket`.

## Claims table

`file:line` = where the claim is stated. All rows below were **executed** on 5.2.0.

| # | Claim | file:line | Runtime result | |
|---|---|---|---|---|
| F1 | Target is Blender 5.2 LTS | INDEX.md:156 | `bpy.app.version == (5,2,0)` | PASS |
| F2 | 4.4+ slotted Actions: `Action.slots` | version-matrix:202 | instance `.slots` present, in `bl_rna` | PASS |
| F3 | 5.0 removed `Action.fcurves` | version-matrix:150 | absent | PASS |
| F4 | 5.0 removed `Action.groups` / `.id_root` | version-matrix:150 | both absent | PASS |
| F5 | `Scene.compositing_node_group` (5.0) | version-matrix:144 | present in `bl_rna` | PASS |
| F6 | `Scene.node_tree` removed | version-matrix:144 | absent | PASS |
| F7 | `CompositorNodeComposite` removed | version-matrix:145 | absent from `bpy.types` | PASS |
| F8 | Boolean solver `FLOAT/EXACT/MANIFOLD` | modifiers:169 | `['FLOAT','EXACT','MANIFOLD']` | PASS |
| F9 | `--background` has a real `VIEW_3D` area | bpy-scripting-core:31 | areas = PROPERTIES, OUTLINER, DOPESHEET_EDITOR, **VIEW_3D** | PASS |
| F10 | …"and `IMAGE_EDITOR` areas" | bpy-scripting-core:31 | **no IMAGE_EDITOR area exists** in the default background window | FAIL |
| F11 | `Object.property_unset` replaces `del obj['cycles']` | version-matrix:157 | present | PASS |
| F12 | ID name limit raised (63→255 B) | version-matrix:161 | 200-char name kept in full | PASS |
| F13 | `gpu.init()` is the 5.2 GPU probe | version-matrix:186 | `gpu.init` exists | PASS |
| M1 | `materials.new()` builds the node tree itself | materials-pbr:19 | `mat.node_tree` non-None with no `use_nodes` | PASS |
| M2 | `use_nodes` is a deprecated no-op returning True | materials-pbr:57 | set False → reads True, tree intact, DeprecationWarning "removed in Blender 6.0" | PASS |
| M3 | **Principled BSDF 32-row index→name table** | materials-pbr:170-203 | 32/32 exact match, zero mismatches | PASS |
| M4 | `distribution` = GGX/MULTI_GGX, default MULTI_GGX | materials-pbr:206 | exact | PASS |
| M5 | `subsurface_method` 4 values, default RANDOM_WALK | materials-pbr:207 | exact incl. `RANDOM_WALK_LEGACY` | PASS |
| M6 | 13 Principled float defaults (Roughness .5, IOR 1.5, Coat Rough .03, SSS Scale .005, Thin Film IOR 1.33, …) | materials-pbr:172-203 | all match | PASS |
| M7 | idx 7 `Weight` is internal, `is_unavailable==True` | materials-pbr:179 | true — **but `bsdf.inputs["Weight"]` raises KeyError** (unavailable sockets are not key-addressable) | PASS* |
| M8 | 5.0 renamed shader `Fac`→`Factor` | materials-pbr:218 | Noise outputs `['Factor','Color']` | PASS |
| M9 | `surface_render_method` = DITHERED/BLENDED | materials-pbr:299 | exact | PASS |
| M10 | `blend_method` kept as deprecated alias | materials-pbr:301 | present | PASS |
| M11 | `thickness_mode`/`displacement_method`/`use_transparent_shadow` | materials-pbr:303-305 | all present | PASS |
| G1 | `NodeTree.inputs` removed in 4.0 | geometry-nodes:R2 | absent | PASS |
| G2 | `tree.is_modifier` | geometry-nodes:152 | present | PASS |
| G3 | `interface.new_socket(name, in_out=, socket_type=)` | geometry-nodes:157 | works | PASS |
| G4 | **24 "verified" base socket idnames** | geometry-nodes:185-190 | 18/24 accepted; **rejected: `NodeSocketTexture`, `NodeSocketScene`, `NodeSocketVector2D`, `NodeSocketVector4D`, `NodeSocketIntVector2D`, `NodeSocketIntVector3D`** (TypeError) | FAIL |
| G5 | subtypes rejected by `new_socket` (R3) | geometry-nodes:R3 | `NodeSocketFloatFactor` rejected | PASS |
| G6 | `structure_type` = AUTO/DYNAMIC/FIELD/GRID/LIST/SINGLE | geometry-nodes:205 | exact | PASS |
| G7 | `default_input` 11 values | geometry-nodes:214-216 | all 11 present | PASS |
| G8 | `interface.new_panel` + `move_to_parent` | geometry-nodes:227 | both present | PASS |
| G9 | DistributePointsOnFaces input is `Mesh` not `Geometry` | geometry-nodes:R7 | `['Mesh','Selection','Distance Min','Density Max','Density','Density Factor','Seed']` | PASS |
| G10 | SetPosition = Geometry/Selection/Position/Offset | geometry-nodes:~340 | exact order | PASS |
| G11 | CurveToMesh = Curve/Profile Curve/Scale/Fill Caps → Mesh | geometry-nodes:~322 | exact | PASS |
| G12 | `capture_items.new('VECTOR', name)` data-type enum | geometry-nodes:R9 | works, socket appears | PASS |
| G13 | StoreNamedAttribute = Geometry/Selection/Name/Value | geometry-nodes:~352 | exact | PASS |
| G14 | 5.2 `mod.properties.inputs.<id>.value` | geometry-nodes:268 | identifier `Socket_2`, set/read 7.5 OK | PASS |
| G15 | 5.2 killed `mod["Socket_2"]` | geometry-nodes:R6 | subscript raises | PASS |
| G16 | `mod.properties.inputs["id"]` marked **[UNVERIFIED]** | geometry-nodes:292 | subscript **does** work — the UNVERIFIED marker is now resolvable | PASS* |
| G17 | `mod.is_input_visible` / `is_input_used` | geometry-nodes:291 | both present | PASS |
| G18 | entry `.type` = VALUE / ATTRIBUTE / **LAYER** | geometry-nodes:270 | float socket enum is `['VALUE','ATTRIBUTE']` — no LAYER | FAIL* |
| A1 | `anim_utils.action_{get,ensure}_channelbag_for_slot` | animation-fcurves:R1 | both exist | PASS |
| A2 | `animdata_get_channelbag_for_assigned_slot` | animation-fcurves:~46 | exists | PASS |
| A3 | `keyframe_insert` auto-creates action + slot | animation-fcurves:R3 | slot `OBKBO` auto-assigned | PASS |
| A4 | `ad.action_suitable_slots` | animation-fcurves:~185 | present | PASS |
| A5 | `act.slots.new(id_type=, name=)` | animation-fcurves:~187 | works with `obj.id_type == 'OBJECT'` | PASS |
| A6 | `channelbag.fcurves.ensure(path, index=, group_name=)` | animation-fcurves:~205 | works; `evaluate(24)==3.0` | PASS |
| A7 | 5.0 renamed `action_group=` → `group_name=` | animation-fcurves:~203 | `action_group` rejected: "expected (data_path, index, group_name)" | PASS |
| A8 | 5.2 flips `use_keyframe_insert_available` to True | animation-fcurves:91 | `True` on factory startup | PASS |
| A9 | 13 interpolation enum values | animation-fcurves:~228 | exact list | PASS |
| A10 | 5 handle types | animation-fcurves:~232 | exact | PASS |
| A11 | 5.0: `driver_add` inserts 2 keyframes, not a Generator (R9) | animation-fcurves:R9 | `modifiers=[]`, `keyframe_points=2` | PASS |
| R1 | `armature.layers` removed (4.0) | rigging:463 | absent | PASS |
| R2 | `collections.new(name, parent=)` hierarchical | rigging:225 | works, parent set | PASS |
| R3 | headless Edit Mode + `edit_bones` works | rigging:126 | `is_editmode=True`, bones created | PASS |
| R4 | `assign()` takes Bone / PoseBone / EditBone | rigging:227 | Bone and PoseBone both accepted | PASS |
| R5 | `Bone.select` removed in 5.0, moved to PoseBone | rigging:461 | `Bone` has no `select`; `PoseBone` and `EditBone` do | PASS |
| R6 | `collections.active_name` / `is_solo_active` | rigging:233 | both present | PASS |
| N1 | engine ids = BLENDER_EEVEE / BLENDER_WORKBENCH / CYCLES | render-engines:17 | assignment of all three works — but `enum_items` reports only `['BLENDER_EEVEE']` (dynamic enum) | PASS* |
| N2 | `compute_device_type` = NONE/CUDA/OPTIX/HIP/METAL/ONEAPI | render-engines:206 | assignment works; **`enum_items` returns `[]`** | PASS* |
| N3 | `get_devices_for_type('METAL')` must be called to populate | render-engines:188 | populates `[('Apple M4 Pro','CPU'), ('Apple M4 Pro (GPU - 16 cores)','METAL')]` | PASS |
| N4 | `cycles.device` = CPU/GPU | render-engines:207 | exact | PASS |
| N5 | `media_type` = IMAGE / MULTI_LAYER_IMAGE / VIDEO | render-engines:402 | exact | PASS |
| N6 | `media_type` must be set **before** `file_format` (R7) | render-engines:100 | `OPEN_EXR_MULTILAYER` rejected under `IMAGE`, accepted after switch | PASS |
| N7 | Cycles adaptive defaults True / 0.01 | render-engines:225 | `True` / `0.00999999` | PASS |
| X1 | 13 KB operator-map names all exist | export-interchange:~62 | all 13 present (`wm.stl_export`, `wm.fbx_import`, …) | PASS |
| X2 | `export_scene.obj`, `export_mesh.stl`, `wm.collada_*` removed | export-interchange:20,29 | genuinely absent (`dir()` empty, `poll()` AttributeError); `import_scene.fbx` still present as KB says | PASS |
| X3 | **All 110 glTF export kwargs listed in §4.3** | export-interchange:~236-268 | 110 listed, 110 in runtime, **0 missing, 0 extras** | PASS |
| X4 | 7 glTF enum lists (image_format, materials, vertex_color, animation_mode, merge_animation, meshopt_extension, lighting_mode) | export-interchange:~272-286 | all 7 exact | PASS |
| X5 | `export_format` is a dynamic enum, prints `''`, pass explicitly | export-interchange:272 | `enum_items` is `[]` — KB's own caveat is correct | PASS |
| X6 | 43 FBX export kwargs | export-interchange:~330 | all present | PASS |
| X7 | `apply_scale_options` 4 values | export-interchange:~360 | exact | PASS |
| X8 | `mesh_smooth_type` OFF/FACE/EDGE/SMOOTH_GROUP | export-interchange:~395 | exact | PASS |
| X9 | USD: `export_textures_mode` present, `export_textures` gone (R1) | export-interchange:R1 | confirmed | PASS |
| X10 | 21 USD export kwargs | export-interchange:~404 | all present | PASS |
| X11 | 15 `wm.fbx_import` kwargs | export-interchange:~400 | all present | PASS |
| X12 | STL has both `global_scale` and `use_scene_unit` (R7) | export-interchange:R7 | both present | PASS |
| X13 | PLY `export_colors` includes SRGB | export-interchange:~50 | `['NONE','SRGB','LINEAR']` | PASS |
| X14 | bundled IO add-ons keep flat module names | export-interchange:~300 | `io_scene_gltf2`, `io_scene_fbx` enabled under flat keys | PASS |
| X15 | OBJ defaults VIEWPORT eval, USD defaults RENDER (R8) | export-interchange:R8 | obj=`DAG_EVAL_VIEWPORT`, usd=`RENDER`; **STL has `evaluation_mode`, not `export_eval_mode`** | PASS |
| P1 | `wm.stl_export` 11-arg signature | 3d-printing:389 | all 11 present | PASS |
| P2 | no native 3MF export in 5.2 | 3d-printing:395 | zero 3MF ops | PASS |
| P3 | 4.1 removed `mesh.use_auto_smooth` | version-matrix:~118 | absent | PASS |
| P4 | sharpness lives in `sharp_face`/`sharp_edge` attributes | version-matrix:~119 | both creatable; `object.shade_smooth_by_angle` exists | PASS |
| P5 | 4.1 removed `ShaderNodeTexMusgrave` | version-matrix:~115 | absent | PASS |
| P6 | 4.0 light linking `receiver_collection` | version-matrix:~113 | `Object.light_linking` → `receiver_collection`, `blocker_collection` | PASS |
| P7 | rigid-body world data API | boilerplates:223 | `Scene.rigidbody_world`, `Object.rigid_body` present | PASS |
| P8 | subsurf viewport uses `levels`, not `render_levels` | modifiers:357 | levels=1 → 26 verts; levels=2 → **98** verts (KB says 386, which is level 3) | FAIL* |

`PASS*` = claim holds but with a caveat the KB does not state. `FAIL*` = narrow/partial failure.

## Verbatim block execution

11 blocks lifted character-for-character out of `## 4. bpy patterns` and run in one headless session.

| Block | Source | Result |
|---|---|---|
| `set_engine(scene,'CYCLES')` | render-engines.md:149 | **RAISES** `RuntimeError: CYCLES not available; engines = ['BLENDER_EEVEE']`. Cause: gates on `bl_rna.properties['engine'].enum_items`, which for this dynamic enum lists only the static entry. Direct `scene.render.engine='CYCLES'` works fine. |
| `enable_cycles_gpu()` | render-engines.md:168 | **SILENTLY WRONG** — returns `'CPU'` and sets `compute_device_type='NONE'` on a machine where `get_devices_for_type('METAL')` finds `Apple M4 Pro (GPU - 16 cores)`. Same root cause: `available = ...enum_items.keys()` is `[]`, so every backend is skipped. No exception, no warning. |
| `find_socket` / `set_input` / `new_pbr_material` | materials-pbr.md:126-244 | Clean. All 6 legacy-name fallbacks (`Specular`, `Subsurface`, `Transmission`, `Clearcoat`, `Sheen`, `Emission`) resolve correctly on 5.2. |
| Reusable shader node group (§4.5) | materials-pbr.md:256-268 | Clean, including `find_socket(noise,"Factor","Fac",inputs=False)`. |
| GN scatter recipe (§4.2+4.3+4.5) | geometry-nodes.md:152-320 | Clean — 7 nodes, 8 links, all socket names resolve. |
| GN Set Position displacement (§4.7) | geometry-nodes.md:~338 | Clean — **by luck**. It links from `noi,"Fac"`, and the Noise node's socket *name* is now `Factor`; it only works because the KB's `sock()` also matches `s.identifier`, which is still `"Fac"`. Any reader who copies the string into `node.outputs["Fac"]` gets a KeyError. |
| `get_channelbag` + Route B + bulk `foreach_set` | animation-fcurves.md:~165-260 | Clean. 480 keys, `evaluate(100) == -0.5440`. Best-executing block in the KB. |
| `edit_armature` + skeleton + bone collections | rigging-armature.md:135-233 | **RAISES** `RuntimeError: Error: Object 'Rig' already in collection 'Scene Collection'`. Root cause: the guard `if arm_obj.name not in view_layer.objects` is evaluated before the view layer refreshes — measured directly: immediately after `scene.collection.objects.link(o)`, `o.name in view_layer.objects` is `False`; after `view_layer.update()` it is `True`. The KB's own §4.2 example links the object and then calls `edit_armature`, so following the file top-to-bottom crashes. |
| `export_glb()` | export-interchange.md:246-281 | **Exports correctly, then fails its own assertion.** glTF log shows 2 primitives Draco-encoded; `assert os.path.getsize > 2048` fires on a 1996-byte file. Measured single-cube GLB: **936 B** with Draco, **1400 B** without. The threshold is set above the size of a legitimate small asset. |
| `apply_all_modifiers()` | modifiers.md:~195 | Clean. 6 → 24 polys, stack cleared, no orphan mesh. |
| `temp_override` + `shade_smooth` (§4.5) | bpy-scripting-core.md:~230 | Clean. `VIEW_3D` area found headless, operator returns `{'FINISHED'}` — confirms the KB's headless-operators claim. |

Score: **7 clean / 1 clean-by-accident / 3 broken.**

## Retrieval-shape findings (ranked)

Measured over all 28 domain files (645 KB total). §2 = "Decision first", §5 = "Failure modes".

| Rank | Finding | Evidence |
|---|---|---|
| 1 | **The failure→fix table is buried at 79–88 % file depth.** For a debugging agent this is the single highest-value surface in the file and it is last. `geometry-nodes` §5 starts at line 532/605 (88 %); `export-interchange` 545/617; `product-viz-and-shots` 576/654. An agent that reads a file "until it has enough" never reaches it. | column `%to§5` in probe output |
| 2 | **One hop of `loads_with` costs 39k–51k tokens.** INDEX:58 says "Follow it rather than guessing"; INDEX:16 warns the links cycle. Mandatory 4 files = 51 KB (~12.8k tok). +1 hop: `modifiers` → 202 KB (~50.5k tok), `geometry-nodes` → 201 KB, `export-interchange` → 173 KB. There is no size hint anywhere in the frontmatter. | computed byte sums |
| 3 | **`loads_with` is 24 mutual 2-cycles, i.e. a near-complete graph per cluster.** Every 10-modeling file loads every other; `materials-pbr ↔ texturing-baking ↔ render-engines ↔ lighting` is a full mesh. As a routing signal it carries almost no information — it says "load the whole cluster". | cycle detection |
| 4 | **`§2 Decision first` placement is excellent and consistent** — line 21–41 in all 28 files, i.e. the first thing after the mental model. This is the one retrieval property the KB gets right, and it is why 200-line 70-cad files are usable. | column `§2@` |
| 5 | **Section-5 heading text is not uniform**, so a grep-based agent misses 6 files. INDEX:141-146 promises "Failure modes" for every file; the six `70-cad-precision-robotics/*` files title it "Anti-patterns & Traps" and §4 "Recipe: Copy-paste patterns". Same 8-slot structure, different strings. | `grep '^## ' 70-cad/*` |
| 6 | **`[UNVERIFIED]` markers are sparse and concentrated in the wrong place.** 39 markers across 645 KB; zero in all four mandatory 00-foundations files, zero in the six 70-cad files. INDEX:161-165 says they mark industry-practice numbers rather than API facts — that is true, but it means the API-fact surface carries no uncertainty signalling at all, and the three broken helper functions above are unmarked. | `[UNVERIFIED` counts |
| 7 | **`python-agent-boilerplates.md` is structurally an index, not a domain file** (88 lines, no §2, no §5) yet INDEX:20-27 lists it in the "always load first, non-negotiable" set — 9.2 KB of citation matrix that no task needs at load time. | file metrics |

## Boilerplate count check

INDEX.md:215 claims **"30 modules passing 100% headless"**.
`python-agent-boilerplates.md` frontmatter and §1 claim **"26 modular Python boilerplates"**.

Actual on disk: `find scripts/boilerplates -name 'bp_*.py'` → **30** (plus `run_all_boilerplate_tests.py` = 31 `.py` files).

- FACT — the **30** in INDEX matches the file count. The **26** in `python-agent-boilerplates.md` is stale by 4.
- FACT — the §1 registry in `python-agent-boilerplates.md` enumerates exactly those 26 and omits
  `cad_mechanics/bp_assembly_collision_audit.py`, `bp_cable_dragchain.py`,
  `bp_connectors_extended.py`, `bp_connectors_wiring.py`.
- FACT — INDEX's own bullet list (INDEX:216-232) names only **17** modules and omits a *different*
  subset (`bp_ball_bearing`, `bp_springs`, `bp_flexures`, `bp_shaft_couplings`, all three
  `dfam_3dprint/*`, `bp_gn_pipe_flange`, both `materials_shading/*`, `bp_rig_robot_arm`, both
  `pipeline_render/*`). So neither list is a complete registry, and the two lists disagree with
  each other.
- NOT CHECKED — whether the 30 actually pass headless (another auditor owns execution).
  The "passing 100% headless" half of the claim is unverified here.

## Not verified

1. Whether the 30 boilerplate modules execute — out of scope by instruction.
2. All `[UNVERIFIED]`-marked numbers (poly budgets, wall thicknesses, texel density, Cycles cost
   multipliers, metal base-color reflectances) — not machine-checkable against Blender.
3. Semantic correctness of anything that needs a rendered image: AgX exposure guidance, lighting
   wattage tables, `product-viz-and-shots` framing math, denoiser quality claims.
4. FBX/USD/Alembic *round-trip* fidelity (what Unity/Unreal actually see) — only kwarg existence
   and enum identity were checked, never an import into a target engine.
5. The 4.5 LTS half of every version-gated claim — only 5.2.0 is installed here.
6. `mocap-retargeting`, `uv-unwrapping`, `texturing-baking`, `compositing-output`, `lighting`,
   `simulation-physics`, `scene-organization`, `optimization-realtime`, `modeling-topology` —
   read only for retrieval-shape metrics, no API claims extracted or executed.
7. Whether the four broken helpers were ever green on some other machine/build (e.g. a Linux box
   where `enum_items` may populate differently) — I only proved they are broken *here*, on the
   install this repo targets.

## Unresolved questions

1. `enum_items` returning `[]` for `compute_device_type`/`denoiser` and static-only for `engine`:
   is this macOS/Metal-specific, `--factory-startup`-specific, or universal 5.2 behaviour? It
   decides whether the fix is "drop the enum gate" or "gate differently per platform".
2. INDEX:161 says names were checked "against live 5.2.0 / 4.5.9 installs running
   `--background --factory-startup`" — but three §4 helpers fail immediately under exactly that
   command. Were the *tables* verified live and the *functions* only written, or was a different
   5.2 build used?
3. `modifiers.md:357` cites 26 / 386 verts for the subsurf viewport-vs-render trap; measured
   26 (level 1) and 98 (level 2). 386 is level 3. Was the source example `render_levels=3`, or is
   the number wrong?
4. Should the six rejected `NodeSocket*` types be removed from `geometry-nodes.md:185`, or is
   there a different creation path (e.g. `NodeSocketVector` + `subtype`/dimension) that the KB
   meant and did not spell out?
5. Who owns the INDEX-vs-boilerplates count drift (30 vs 26 vs 17 listed)? Any fix needs a single
   generated registry, not three hand-maintained lists.

Status: DONE_WITH_CONCERNS
Summary: KB factual claims are strong — 62/67 executed claims PASS including the exact 32-socket Principled table and all 110 glTF kwargs — but 3 of 11 verbatim copy-paste blocks fail on the real 5.2.0 install (set_engine raises, enable_cycles_gpu silently falls back to CPU on Metal, edit_armature raises on the KB's own example sequence) and a 4th (export_glb) fails its own success assertion on a valid export.
Concerns: the two render-engines helpers are on the critical path for this project's headless Cycles/Metal mission and fail silently, not loudly; retrieval shape puts every failure→fix table at 79–88% file depth and `loads_with` one hop costs 39–51k tokens.
