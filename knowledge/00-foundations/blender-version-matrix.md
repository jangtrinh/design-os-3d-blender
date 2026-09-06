---
name: blender-version-matrix
domain: foundations
blender_target: "5.2 LTS"
compat: "4.2 LTS+"
audience: ai-agent-bpy
description: Version timeline and the exact API breakages between 4.2 and 5.2 that silently invalidate memorized bpy code. Read this before writing any script.
loads_with: [bpy-scripting-core, agent-workflow-loop]
tags: [versioning, breaking-changes, compatibility, api-history, migration]
---

# Blender Version Matrix & Breaking Changes

## 1. Mental model

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

## 2. Decision first

| Situation | What to do |
|---|---|
| Start of any session | `bpy.app.version` → store as `(major, minor, patch)`. Log it. |
| Target unknown, script must be portable | Write for 5.x, add explicit `if bpy.app.version >= (5, 0)` guards on every item in §4 |
| Target is 4.5 LTS (still very common in studios) | Use the 4.5 column below; do NOT use 5.x-only APIs |
| Target is 5.2 LTS | Use this KB as written |
| Any socket / enum / operator name you are about to hardcode | Introspect it instead (see `bpy-scripting-core` §Introspection) |
| Add-on-provided API (Rigify, 3MF, print toolbox) | Probe with `addon_utils` / `hasattr`; never assume registration |

## 3. Rules

R1. Read `bpy.app.version` before the first line of real work.
    Why: every rule below is version-conditional; there is no safe default.
    Violation: `AttributeError` / `KeyError` on a line that looks obviously correct.

R2. Treat `docs.blender.org/api/current/` as **5.2**, not as "whatever is newest".
    Why: `current` tracks the latest release; as of July 2026 that is 5.2 LTS.
    Violation: citing a signature that does not exist on the user's 4.5 install.

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

## 4. Release timeline and what broke

### 4.1 Timeline

| Version | Released | Status (July 2026) |
|---|---|---|
| 4.2 LTS | Jul 2024 | LTS, in support |
| 4.3 | Nov 2024 | superseded |
| 4.4 | Mar 2025 | superseded |
| **4.5 LTS** | Jul 2025 | LTS, in support — the common "previous stable" |
| 5.0 | Nov 2025 | superseded (largest API break in years) |
| 5.1 | Mar 2026 | superseded |
| **5.2 LTS** | Jul 2026 | **current, LTS, this KB's target** |

Blender ships 3 releases/year; the July release is the LTS.

### 4.2 Breaking changes by version — the ones that hit generated code

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

**4.0 — bone layers → bone collections.** `armature.layers` gone;
`armature.collections` is the replacement. See `rigging-armature.md`.

**4.0 — AgX** became the default view transform (replacing Filmic). Still the
default in 5.2. Affects every brightness judgement an agent makes from a render.

**4.0 — light linking** added (`light.<...>.receiver_collection`).

**4.1 — Musgrave texture removed**, folded into Noise Texture (with a documented
Dimension → Roughness conversion). Any `ShaderNodeTexMusgrave` reference fails.

**4.1 — Auto Smooth checkbox removed.** Shading sharpness now lives in mesh
attributes (`sharp_face`, `sharp_edge`, `custom_normal`) plus a "Smooth by Angle"
modifier/asset. `mesh.use_auto_smooth` no longer exists. See `modeling-topology.md`.

**4.2 — EEVEE Next** replaced legacy EEVEE (different properties entirely).

**4.2 — Extensions system** replaced the legacy add-on model. Marketplace
extensions get `bl_ext.<repo>.<id>` module ids. **Bundled** IO add-ons keep plain
names (`io_scene_gltf2`, `io_scene_fbx`) — do not "fix" those to `bl_ext.*`.

**4.4 — Slotted Actions.** An Action now holds slots → layers → strips →
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
| Nodes | shader socket `Fac` | `Factor` |
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

**5.2 — geometry node modifier inputs.** The `mod["Socket_2"]` custom-property
scheme is gone:

```python
# 4.5 – 5.1
mod["Socket_2"] = 3.0
# 5.2+
mod.properties.inputs.Socket_2.value = 3.0     # .type in {'VALUE','ATTRIBUTE','LAYER'}
```

See `geometry-nodes.md` for the version-gated helper.

**5.2 — `gpu.init()`** is the documented probe for whether a GPU backend is
available (relevant to EEVEE headless viability).

## 5. Failure modes

| Symptom (what the agent sees) | Root cause | Fix |
|---|---|---|
| `KeyError: 'Specular'` on a Principled node | pre-4.0 socket name | resolve via `find_socket()` (`materials-pbr.md`) |
| `AttributeError: 'Action' object has no attribute 'fcurves'` | 5.0 removed the legacy Action API | `action_get_channelbag_for_slot()` (`animation-fcurves.md`) |
| `AttributeError: 'Scene' object has no attribute 'node_tree'` | 5.0 compositor move | `scene.compositing_node_group` |
| `AttributeError: ... 'inputs'` on a node group | pre-4.0 interface API | `tree.interface.new_socket(...)` |
| Render engine assignment silently ignored / falls back | used `BLENDER_EEVEE_NEXT` on 5.x, or `BLENDER_EEVEE` on 4.2–4.5 | branch on `bpy.app.version` |
| Output file written in the wrong container | `file_format` set before `media_type` | set `media_type` first |
| `mod["Socket_2"] = x` raises or has no effect | 5.2 GN modifier property rewrite | `mod.properties.inputs.<id>.value` |
| Boolean modifier ignores `solver='FAST'` | renamed to `'FLOAT'` in 5.0 | use `'FLOAT'`, or read the enum at runtime |
| `bpy.ops.wm.collada_export` missing | removed in 5.0 | export USD or glTF instead |
| Add-on operator missing (`pose.rigify_generate`) | extension not enabled / id changed | probe with `addon_utils.modules()` + `hasattr(bpy.ops.pose, ...)` |

## 6. Parameter defaults by use case

| Parameter | Game/realtime | Character anim | Motion graphics | Product viz | 3D print |
|---|---|---|---|---|---|
| Recommended target | 4.5 LTS (engine toolchains lag) | 5.2 LTS | 5.2 LTS | 5.2 LTS | 4.5 or 5.2 LTS |
| Why | Unity/Unreal importers and studio pipelines pin older FBX/glTF behaviour | slotted Actions + 5.x rigging fixes are worth it | newest geo-nodes zones (For Each, bundles) only in 5.x | AgX + EEVEE Next + compositor rewrite | either; nothing print-critical changed |
| Must-guard APIs | IO operator names, FBX import op | Action/channelbag API | GN modifier input access, zone APIs | compositor tree, `media_type` | boolean solver enum |

## 7. Verification checklist

- [ ] `v = bpy.app.version; print(v)` — logged at session start, and every branch below keys off it
- [ ] `assert bpy.app.version >= (4, 5), "KB targets 4.5 LTS or newer"` — refuse to run on older
- [ ] `hasattr(bpy.types.Scene, "compositing_node_group")` — confirms 5.x compositor model before touching the compositor
- [ ] `hasattr(bpy.types.Action, "slots")` — confirms 4.4+ slotted Actions before touching animation
- [ ] `"FLOAT" in bpy.types.BooleanModifier.bl_rna.properties["solver"].enum_items.keys()` — confirms 5.x boolean enum
- [ ] Any script that will be re-run later records `bpy.app.version` in a scene custom property so a future run can detect drift

## 8. Sources

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
