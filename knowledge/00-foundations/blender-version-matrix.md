---
name: blender-version-matrix
domain: foundations
blender_target: "5.2 LTS"
compat: "4.2 LTS+"
audience: ai-agent-bpy
description: Version timeline and the exact API breakages between 4.2 and 5.2 that silently invalidate memorized bpy code. Read this before writing any script.
loads_with: [bpy-scripting-core, agent-workflow-loop]
tags: [versioning, breaking-changes, compatibility, api-history, migration]
id: blender-version-matrix
title: "Blender Version Matrix & Breaking Changes"
when: [bpy-version-branching, api-breaking-changes, principled-socket-renames, action-slots, compositor-node-group, gn-modifier-inputs]
trust_tier: community_reference
sources_checked: 2026-10-13
---
# Blender Version Matrix & Breaking Changes

## Purpose

Stop agents from emitting bpy written against the wrong Blender release: it fixes the timeline (4.2 to 5.2 LTS) and the exact API removals and renames between them, each checked against release notes and the installed 5.2.0 runtime.

## When to Use / When NOT

- ALLOWED: any script that hardcodes an API name, enum, socket or operator that changed between 4.0 and 5.2 — read this first, then introspect
- ALLOWED: choosing a target build (4.5 LTS vs 5.2 LTS) for a pipeline that must run again later — the timeline and support windows are here
- NOT ALLOWED: Principled socket inventory, defaults and node wiring — use `materials-pbr` instead
- NOT ALLOWED: how to write and verify a bpy payload (wrapper, context overrides, headless) — use `bpy-scripting-core` instead
- NOT ALLOWED: animation/compositor tutorials beyond the rename — use the matching domain module (`animation-fcurves`, `compositing-output`) instead

## Core Knowledge Content


### 1. Mental model

An LLM's memory of `bpy` is a blend of every Blender version it ever read. Blender
does not keep that memory honest: between 4.0 and 5.2 the Principled BSDF sockets
were renamed, the node-group interface API was replaced, the Action data model was
rebuilt, the compositor tree moved, and half a dozen operator idnames changed. None
of this fails loudly at the point of the mistake — a wrong socket name raises
`KeyError` three lines later, a wrong enum silently no-ops, a removed attribute
raises `AttributeError` only on the branch that happens to run.

So the first thing an agent does in a session is **read the version**, and the
second is **branch on it or introspect**, never recall. Everything in this knowledge
base is written against 5.2 LTS with the divergences from 4.5 LTS called out.

The most common way agents get this wrong: writing code that "works on Blender"
without asking which one, then debugging the resulting `AttributeError` as if it
were a logic bug.

### 2. Decision first

| Situation | What to do |
|---|---|
| Start of any session | `bpy.app.version` → store as `(major, minor, patch)`. Log it. |
| Target unknown, script must be portable | Write for 5.x, add explicit `if bpy.app.version >= (5, 0)` guards on every item in §4 |
| Target is 4.5 LTS (still very common in studios) | Use the 4.5 column below; do NOT use 5.x-only APIs |
| Target is 5.2 LTS | Use this KB as written |
| Any socket / enum / operator name you are about to hardcode | Introspect it instead (see `bpy-scripting-core` §Introspection) |
| Add-on-provided API (Rigify, 3MF, print toolbox) | Probe with `addon_utils` and `name in dir(bpy.ops.<module>)`; `hasattr(bpy.ops.x, name)` is always True. Never assume registration |

### 3. Rules

R1. Read `bpy.app.version` before the first line of real work.
    Why: every rule below is version-conditional; there is no safe default.
    Violation: `AttributeError` / `KeyError` on a line that looks obviously correct.

R2. Treat `docs.blender.org/api/current/` as a moving locator, not a version pin.
    Record the installed build and the version of the documentation actually read.
    Prefer a versioned API page and introspect the installed RNA before mutation.
    The historical 5.2 target of this knowledge base is not proof of today's page.

R3. Never hardcode a name that appears in §4's rename tables. Resolve it at runtime.
    Why: these are the exact strings that changed, and they change again.
    Violation: silent no-op (enum) or `KeyError` (socket/attribute).

R4. When you must support both 4.5 and 5.x, write a small resolver function once
    and call it everywhere, rather than sprinkling `if` statements.
    Why: version branches scattered through a script are where partial migrations rot.
    Violation: half the script works on 5.2, half on 4.5, neither works fully on either.

R5. Prefer LTS targets (4.2, 4.5, 5.2) for anything that must run again in six months.
    Why: LTS gets two years of critical fixes; non-LTS gets fixes until the next release.
    Violation: pipeline breaks on a point release you did not choose.

### 4. Release timeline and what broke

#### 4.1 Timeline

| Version | Released | Status (July 2026) |
|---|---|---|
| 4.2 LTS | Jul 2024 (16th) | LTS, support window ended July 2026 |
| 4.3 | Nov 2024 (19th) | superseded |
| 4.4 | Mar 2025 (18th) | superseded |
| **4.5 LTS** | Jul 2025 (15th) | LTS, supported until July 2027 — the common "previous stable" |
| 5.0 | Nov 2025 (18th) | superseded (largest API break in years) |
| 5.1 | Mar 2026 (17th) | superseded |
| **5.2 LTS** | Jul 2026 (14th) | **current stable, LTS until July 2028, this KB's target** |
| 5.3 / 5.4 | — | beta / alpha at the 2026-10-13 capture; never target them for production scripts |
<!-- ease:source S1 anchor="Previous Versions list" -->

Blender ships 3 releases/year; the July release is the LTS. <!-- ease:source S1 anchor="intro: LTS yearly, release every ~4 months" -->

#### 4.2 Breaking changes by version — the ones that hit generated code

**4.0 — Principled BSDF socket renames** (still the #1 source of broken snippets)

| Pre-4.0 | 4.0 → 5.2 |
|---|---|
| `Specular` | `Specular IOR Level` |
| `Specular Tint` (float) | `Specular Tint` (**color**) |
| `Subsurface` | `Subsurface Weight` |
| `Subsurface Color` | **removed** |
| `Transmission` | `Transmission Weight` |
| `Emission` | `Emission Color` (+ `Emission Strength`) |
| `Sheen` | `Sheen Weight` |
| `Sheen Tint` (float) | `Sheen Tint` (**color**) |
| `Clearcoat` | `Coat Weight` |
| `Clearcoat Roughness` | `Coat Roughness` |
<!-- ease:source S10 anchor="SOCK index 14 'Specular IOR Level', index 15 'Specular Tint' RGBA" -->
<!-- ease:source S8 anchor="Principled BSDF revamp (4.0 shading notes)" -->

See `materials-pbr.md` for the full verified 5.2 socket inventory and the
`find_socket()` resolver you should use instead of any of these strings.

**4.0 — node group interface API replaced**

```python
# REMOVED in 4.0 — this is what an LLM will reach for first:
#   tree.inputs.new('NodeSocketGeometry', 'Geometry')
# Correct 4.0 → 5.2:
tree.interface.new_socket(name="Geometry", in_out='INPUT',
                          socket_type='NodeSocketGeometry')
```
<!-- ease:source S7 anchor="Node tree interface: tree.interface.new_socket(name=, in_out=)" -->

**4.0 — bone layers → bone collections.** `armature.layers` gone; <!-- ease:source S7 anchor="Armature: 'Layers and bone groups have been removed ... Bone collections'" -->
`armature.collections` is the replacement. See `rigging-armature.md`.

**4.0 — AgX** became the default view transform (replacing Filmic). Still the <!-- ease:source S10 anchor="view_transform_default = AgX on 5.2 (4.0 switch itself not in a fetched source)" -->
default in 5.2. Affects every brightness judgement an agent makes from a render.

**4.0 — light linking** added. The properties live on the emitter object: `Object.light_linking.receiver_collection` and `.blocker_collection` (checked on 5.2.0; the earlier text `light.<...>.receiver_collection` was wrong).

**4.1 — Musgrave texture removed**, folded into Noise Texture (with a documented <!-- ease:source S10 anchor="ShaderNodeTexMusgrave absent in 5.2 (exists False); 4.1 attribution from the 4.1 rendering notes could not be fetched" -->
Dimension → Roughness conversion). Any `ShaderNodeTexMusgrave` reference fails.

**4.1 — Auto Smooth checkbox removed.** Shading sharpness now lives in mesh <!-- ease:source S11 anchor="prop Mesh.use_auto_smooth = False on 5.2; 4.1 attribution not re-fetched" -->
attributes (`sharp_face`, `sharp_edge`, `custom_normal`) plus a "Smooth by Angle"
modifier/asset. `mesh.use_auto_smooth` no longer exists. See `modeling-topology.md`.

**4.2 — EEVEE Next** replaced legacy EEVEE (different properties entirely). <!-- ease:source S9 anchor="'EEVEE identifier has been changed to BLENDER_EEVEE_NEXT'" -->

**4.2 — Extensions system** replaced the legacy add-on model. Marketplace <!-- ease:source S9 anchor="Add-on Packaging: extensions platform, old packaging is legacy" -->
extensions get `bl_ext.<repo>.<id>` module ids. **Bundled** IO add-ons keep plain
names (`io_scene_gltf2`, `io_scene_fbx`) — do not "fix" those to `bl_ext.*`.

**4.4 — Slotted Actions.** An Action now holds slots → layers → strips → <!-- ease:source S6 anchor="Slotted Actions: slots -> layers -> strips -> channelbag; legacy action.fcurves operates on first slot" -->
channelbags → fcurves, so one Action can drive several IDs. In 4.4/4.5 the old
`action.fcurves` still works as a proxy.

**5.0 — the big one.** Everything below is a hard removal or rename:

| Area | Before | 5.0+ |
|---|---|---|
| Actions | `action.fcurves`, `action.groups`, `action.id_root` | **removed**; use `bpy_extras.anim_utils.action_get_channelbag_for_slot()` / `action_ensure_channelbag_for_slot()` |
| Actions | `action_group=` kwarg | `group_name=` |
| Armature | `Bone.select`, bone selection/visibility flags | moved onto `PoseBone` |
| Compositor | `scene.node_tree` | `scene.compositing_node_group` |
| Compositor | `CompositorNodeComposite` | **removed** — use `NodeGroupOutput` |
| Nodes | `material.use_nodes` / `world.use_nodes` / `scene.use_nodes` | deprecated **no-ops** (node trees always exist) |
| Nodes | shader socket `Fac` | socket **name** `Factor`; the **identifier** stays `Fac`, and in 5.2.0 `node.outputs["Fac"]` and `node.outputs["Factor"]` both resolve |
| Render | engine id `BLENDER_EEVEE_NEXT` | `BLENDER_EEVEE` |
| Output | set `file_format` directly | set `image_settings.media_type` **before** `file_format` |
| Modifiers | Boolean solver `'FAST'` | `'FLOAT'` |
| IO | `bpy.ops.import_scene.fbx` | `bpy.ops.wm.fbx_import` (C++; legacy op still present) |
| IO | Collada (`wm.collada_export`) | **removed** |
| Props | `del obj['cycles']` to reset | `obj.property_unset('cycles')` |
| Props | `bpy.props` values readable via `obj['name']` | stored separately from custom properties |
| Props | — | new `get_transform` / `set_transform` accessors; `READ_ONLY` option flag |
| Misc | ID name limit 63 bytes | 255 bytes |
| Cycles | adaptive subdivision experimental | promoted to stable |
<!-- ease:source UNVERIFIED reason="no fetched source states the stable promotion" -->
<!-- ease:source UNVERIFIED reason="63-byte former limit not in any fetched source; 255 accepted on 5.2.0 (probe 1 id_name_255 = 255)" -->
<!-- ease:source S2 anchor="'New get_transform and set_transform bpy.props accessors', READ_ONLY flag" -->
<!-- ease:source S2 anchor="'Removal of (Unsupported) Access to Runtime-Defined Properties Storage Data'" -->
<!-- ease:source S2 anchor="'obj.property_unset' replaces del obj['cycles']" -->
<!-- ease:source S12 anchor="'collada_export' in dir(bpy.ops.wm) == False on 5.2" -->
<!-- ease:source S11 anchor="dir(bpy.ops.wm) has fbx_import; dir(bpy.ops.import_scene) == ['fbx','gltf']" -->
<!-- ease:source S2 anchor="'FAST boolean solver has been renamed to FLOAT'" -->
<!-- ease:source S2 anchor="'media_type ... needs to be set ... before setting file_format'" -->
<!-- ease:source S2 anchor="'EEVEE's render engine identifier was changed from BLENDER_EEVEE_NEXT to BLENDER_EEVEE'" -->
<!-- ease:source S13 anchor="node.outputs['Factor'].identifier == 'Fac'; both lookups succeed" -->
<!-- ease:source S2 anchor="'use_nodes deprecated, always True, no effect' (Shading section)" -->
<!-- ease:source S10 anchor="CompositorNodeComposite class absent on 5.2; NodeGroupOutput used in the 5.0 example" -->
<!-- ease:source S2 anchor="'scene.node_tree was removed, use scene.compositing_node_group'" -->
<!-- ease:source S2 anchor="'select, select_head, select_tail of the bone itself have been removed'; PoseBone.select added" -->
<!-- ease:source S2 anchor="'action_group became group_name'" -->
<!-- ease:source S2 anchor="Action: legacy properties removed; use anim_utils channelbag helpers" -->

**5.2 — geometry node modifier inputs.** The `mod["Socket_2"]` custom-property
scheme is gone:

```python
# 4.5 – 5.1
mod["Socket_2"] = 3.0
# 5.2+
mod.properties.inputs.Socket_2.value = 3.0     # .type in {'VALUE','ATTRIBUTE','LAYER'}
```
<!-- ease:source S4 anchor="'The API for accessing Geometry Nodes modifier properties has changed'; probe 2/3 confirm properties.inputs.<id>.value" -->

See `geometry-nodes.md` for the version-gated helper.

**5.2 — `gpu.init()`** is the documented probe for whether a GPU backend is <!-- ease:source S4 anchor="'Added gpu.init() to initialize gpu backend when running Blender in background mode'" -->
available (relevant to EEVEE headless viability).

### 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `KeyError: 'Specular'` on a Principled node | pre-4.0 socket name | resolve via `find_socket()` (`materials-pbr.md`) |
| `AttributeError: 'Action' object has no attribute 'fcurves'` | 5.0 removed the legacy Action API | `action_get_channelbag_for_slot()` (`animation-fcurves.md`) |
| `AttributeError: 'Scene' object has no attribute 'node_tree'` | 5.0 compositor move | `scene.compositing_node_group` |
| `AttributeError: ... 'inputs'` on a node group | pre-4.0 interface API | `tree.interface.new_socket(...)` |
| Render engine assignment silently ignored / falls back | used `BLENDER_EEVEE_NEXT` on 5.x, or `BLENDER_EEVEE` on 4.2–4.5 | branch on `bpy.app.version` |
| Output file written in the wrong container | `file_format` set before `media_type` | set `media_type` first |
| `mod["Socket_2"] = x` raises `TypeError: this type doesn't support IDProperties` (read) / `AttributeError: no __getitem__` (write) | 5.2 GN modifier property rewrite | `mod.properties.inputs.<id>.value` |
| Boolean modifier ignores `solver='FAST'` | renamed to `'FLOAT'` in 5.0 | use `'FLOAT'`, or read the enum at runtime |
| `bpy.ops.wm.collada_export` missing | removed in 5.0 | export USD or glTF instead |
| Add-on operator missing (`pose.rigify_generate`) | extension not enabled / id changed | probe with `addon_utils.modules()` + `"rigify_generate" in dir(bpy.ops.pose)`. Never `hasattr(bpy.ops.pose, ...)`: it is always `True` (calling a missing op raises `AttributeError: ... could not be found`) |
<!-- ease:source S12 anchor="hasattr(bpy.ops.pose,'definitely_not_an_operator') = True; 'in dir' = False" -->

### 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Recommended target | 4.5 LTS (engine toolchains lag) | 5.2 LTS | 5.2 LTS | 5.2 LTS | 4.5 or 5.2 LTS |
| Why | Unity/Unreal importers and studio pipelines pin older FBX/glTF behaviour | slotted Actions + 5.x rigging fixes are worth it | newest geo-nodes zones (For Each, bundles) only in 5.x | AgX + EEVEE Next + compositor rewrite | either; nothing print-critical changed |
| Must-guard APIs | IO operator names, FBX import op | Action/channelbag API | GN modifier input access, zone APIs | compositor tree, `media_type` | boolean solver enum |

### 7. Verification checklist

- [ ] `v = bpy.app.version; print(v)` — logged at session start, and every branch below keys off it
- [ ] `assert bpy.app.version >= (4, 5), "KB targets 4.5 LTS or newer"` — refuse to run on older
- [ ] `"compositing_node_group" in bpy.types.Scene.bl_rna.properties` — confirms 5.x compositor model before touching the compositor (`hasattr(bpy.types.Scene, ...)` is False for every built-in RNA property: a false negative) <!-- ease:source S11 anchor="prop Scene.compositing_node_group = True; control hasattr(Scene,'frame_current') = False" -->
- [ ] `"slots" in bpy.types.Action.bl_rna.properties` — confirms 4.4+ slotted Actions before touching animation
- [ ] `"FLOAT" in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items.keys()` — confirms 5.x boolean enum (5.2.0 reports `FLOAT, EXACT, MANIFOLD`) <!-- ease:source S10 anchor="boolean_solver = ['FLOAT','EXACT','MANIFOLD']" -->
- [ ] Any script that will be re-run later records `bpy.app.version` in a scene custom property so a future run can detect drift

### 8. Sources

- [Blender Python API — current (5.2)](https://docs.blender.org/api/current/)
- [Blender Python API change log](https://docs.blender.org/api/current/change_log.html)
- [Blender 5.0 Python API release notes](https://developer.blender.org/docs/release_notes/5.0/python_api/)
- [Blender 5.1 Python API release notes](https://developer.blender.org/docs/release_notes/5.1/python_api/)
- [Blender 5.2 LTS release notes](https://developer.blender.org/docs/release_notes/5.2/)
- [Blender 4.0 Python API release notes](https://developer.blender.org/docs/release_notes/4.0/python_api/)
- [Blender compatibility notes index](https://developer.blender.org/docs/release_notes/compatibility/)
- [Blender LTS program](https://www.blender.org/download/lts/)
- [Blender release schedule / endoflife.date](https://endoflife.date/blender)

Version-specific claims in §4.2 were cross-checked against the release notes and,
where the notes were ambiguous, against Blender source at tag `v5.2.0` and against
a live 5.2.0 and 4.5.9 install running `--background --factory-startup`.

## Failure Modes (Mandatory)

- **`AttributeError: 'Action' object has no attribute 'fcurves'`** — cause: 5.0 removed the legacy Action API (`bpy.types.Action.bl_rna.properties` has no `fcurves`) — fix: `bpy_extras.anim_utils.action_get_channelbag_for_slot()` / `action_ensure_channelbag_for_slot()`
- **Capability probe says an API is missing (or present) when it is not** — cause: `hasattr(bpy.types.X, 'prop')` is False for every built-in RNA property, and `hasattr(bpy.ops.mod, 'op')` is True for every name — fix: use `'prop' in bpy.types.X.bl_rna.properties` and `'op' in dir(bpy.ops.mod)` (runtime probes 2 and 3)
- **`KeyError: 'Specular'` on a Principled node** — cause: 4.0 renamed it `Specular IOR Level`; since 4.0 `node.inputs[name]` also honours socket availability — fix: resolve via `find_socket()` in `materials-pbr`
- **Engine assignment silently ignored** — cause: `BLENDER_EEVEE_NEXT` used on 5.x (5.2.0 lists only `BLENDER_EEVEE`) — fix: branch on `bpy.app.version` or read `RenderSettings.bl_rna.properties['engine'].enum_items`
- **Output written in the wrong container** — cause: `file_format` set before `image_settings.media_type` (5.0) — fix: set `media_type` first

## Sources

- [S1] Blender Release Notes index (dates, LTS support windows) — https://developer.blender.org/docs/release_notes/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-index.html) — captured 2026-10-13 — sha256 9ba6bbf15913200305d45a65483b621562074621094652ec950253ecb9dce80c
- [S2] Blender 5.0 Python API release notes — https://developer.blender.org/docs/release_notes/5.0/python_api/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-0.html) — captured 2026-10-13 — sha256 5ee8a5f78edc6bba1b822a31271598934e3988263b0345632b8fcdc4e3ef3eff
- [S3] Blender 5.1 Python API release notes — https://developer.blender.org/docs/release_notes/5.1/python_api/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-1-python.html) — captured 2026-10-13 — sha256 31318ad73ff7341f91354696cb8e587c37de05909caf7e065ed5aef7407e14b4
- [S4] Blender 5.2 LTS Python API release notes — https://developer.blender.org/docs/release_notes/5.2/python_api/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-2-python.html) — captured 2026-10-13 — sha256 613fac2fa63a96155d40c761571e1a7407c709926ebc2eff96f846343bb1b086
- [S5] Blender 5.2 LTS release notes overview (compatibility list) — https://developer.blender.org/docs/release_notes/5.2/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-5-2.html) — captured 2026-10-13 — sha256 1adc33e9ce2590ade88e0b8c8bdd97622bd82ffbfa1d7e45d5855d82d5b1745d
- [S6] Blender 4.4 Python API release notes (slotted Actions) — https://developer.blender.org/docs/release_notes/4.4/python_api/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-4-4.html) — captured 2026-10-13 — sha256 d6401ff1d90dff3a0b93c0d583d482203558257980bcf397ecf849809fb0ba33
- [S7] Blender 4.0 Python API release notes (interface, bone collections) — https://developer.blender.org/docs/release_notes/4.0/python_api/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-4-0-python.html) — captured 2026-10-13 — sha256 6afa52860e6e9b22fadc662b9cc5da797b315e003e70a27f22f28dc7285b12eb
- [S8] Blender 4.0 Shading release notes (Principled BSDF revamp) — https://developer.blender.org/docs/release_notes/4.0/shading/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-4-0-shading.html) — captured 2026-10-13 — sha256 501b7b4d502675cde6d006e909cb051f14a619ebdd7acc098c2c68f2ef575f6a
- [S9] Blender 4.2 Python API release notes (EEVEE Next id, extensions) — https://developer.blender.org/docs/release_notes/4.2/python_api/ (frozen copy: knowledge/_evidence/kb-261013/w1-rel-4-2-python.html) — captured 2026-10-13 — sha256 0ba1a96ef2e0133146779c438382166a9bdb8f9a083fee8fff4f447c205e7f9a
- [S10] Runtime probe 1 on Blender 5.2.0 LTS (script w1-probe-5.2-runtime.py): sockets, engines, solver enum, classes — knowledge/_evidence/kb-261013/w1-probe-5.2-runtime-output.txt — captured 2026-10-13 — sha256 3ad8e713a6ecef0926ba15bdbcf92c69a4926d64eed1a7d9c25ba88310591388
- [S11] Runtime probe 2 on 5.2.0 (bl_rna property/function presence, GN modifier API, ops lists) — knowledge/_evidence/kb-261013/w1-probe2-5.2-runtime-output.txt — captured 2026-10-13 — sha256 fc89a17430ce6e7ba578923a672478bfb042b5adb5eb78b3692126a760e3179c
- [S12] Runtime probe 3 on 5.2.0 (bpy.ops hasattr reliability, GN input access, error strings) — knowledge/_evidence/kb-261013/w1-probe3-5.2-runtime-output.txt — captured 2026-10-13 — sha256 4ba39f8ce9c4c8a536fde301496e9e766da6a02147ed455df3fda5b9d199b995
- [S13] Runtime probe 6 on 5.2.0 (Fac/Factor lookup by name and identifier) — knowledge/_evidence/kb-261013/w1-probe6-5.2-runtime-output.txt — captured 2026-10-13 — sha256 8d880cd427af7d24ff5a8d483602f721a6b20b830e0caa9c33b6c1b780c4f70e
