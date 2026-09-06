# W5 — KB helper fixes + sentinel boilerplate runner

Worker D. 2026-09-06. Blender **5.2.0 LTS** (`fbe6228777e7`, built 2026-07-14), Apple M4 Pro / macOS.
Every run: fresh `--factory-startup -b --python-exit-code 3`. GUI PID 14172 never contacted; nothing
under `builds/` opened. Scratch: `/private/tmp/claude-501/-Users-jang-Products-Blender/770d4c04-83d4-40e0-b3f9-1fe468bcd0b0/scratchpad/w5/`.

## Conclusion

All 9 deliverables done and re-executed on the real install. **FACT** — the four audit-02 blockers
were first *reproduced verbatim* (they are real, not report artefacts), then fixed, and the fixed
code was re-run **by extracting the fenced python blocks out of the edited Markdown itself**
(`scratchpad/w5/extract_kb_blocks.py` → `kb_blocks_run.py`), so the evidence is about the KB text,
not about a private copy of it. **FACT** — the runner now fails the audit-03 liar module and passes
the handled-operator-error module, and 30/30 real modules pass under the new criterion.

Root cause of 3 of the 4 KB blockers, confirmed by measurement: **`enum_items` is empty or
static-only for Blender's *dynamic* enums.** Measured 5.2.0: `render.engine.enum_items` →
`['BLENDER_EEVEE']` (Cycles missing), `compute_device_type.enum_items` → `[]`,
`cycles.denoiser.enum_items` → `[]`. Assignment to all of them works. Rule now written into the KB:
**try-assign + read back; never gate on `enum_items` for a dynamic enum.**

## Defect → fix → rerun → result

| # | Defect (audit-02/03) | Fix | Rerun command | Result |
|---|---|---|---|---|
| 1a | `render-engines.md` `set_engine()` raises `RuntimeError: CYCLES not available` — gates on `enum_items` | try-assign in a `try/except TypeError` + read-back; restores previous engine before raising; documents the dynamic-enum rule | `Blender --factory-startup -b --python-exit-code 3 --python kb_blocks_run.py` | **PASS** — `{'CYCLES':'CYCLES','EEVEE':'BLENDER_EEVEE','WORKBENCH':'BLENDER_WORKBENCH'}` |
| 1b | `enable_cycles_gpu()` returns `'CPU'`, sets `compute_device_type='NONE'` on a Metal Mac (silent 10–30× slowdown) | enumerate `get_devices_for_type(b)` directly for OPTIX/CUDA/HIP/METAL/ONEAPI; **filter `d.type == backend`** (the METAL list also contains a CPU entry); assign `compute_device_type` in `try/except TypeError` + read back; return the real backend | same run | **PASS** — returns `METAL`, `compute_device_type='METAL'`, `scene.cycles.device='GPU'`, enabled device = `Apple M4 Pro (GPU - 16 cores)` |
| 1c | EEVEE-headless-on-macOS wording | added a **measured fact box** in §4.8 + a pointer in §1; R2 "do not assume" kept verbatim | `Blender … --python eevee_bench.py` (×2) | **PASS** — engine reads back `BLENDER_EEVEE`; 256 px / 8 samples renders in **0.18–0.20 s**, whole fresh process **0.67–0.81 s wall**, valid 39 KB PNG |
| 2 | `rigging-armature.md` `edit_armature()` raises `Object 'Rig' already in collection 'Scene Collection'` on the KB's own §4.2 sequence | measured the cause (`o.name in view_layer.objects` is **False** immediately after `link()`, **True** after `view_layer.update()`); fix = refresh first, link only if genuinely unlinked, refresh again | same run, §4.1 + §4.2 blocks extracted from the edited file | **PASS** — 5 bones `[spine, chest, upper_arm.L, forearm.L, hand.L]`, `is_editmode False`, mode restored to `OBJECT`. Also passes when the caller has **not** linked the object |
| 3 | `export-interchange.md` `assert getsize > 2048` fails a valid export | replaced with `assert_valid_glb()` — parses the GLB header (magic `glTF`, version 2, `length == filesize`), then the JSON chunk and asserts `meshes >= 1` | same run | **PASS** — Draco `(1120 B, 1 mesh)`, plain `(1732 B, 1 mesh)`; a file truncated to half length fails with `header length 1732 != file size 866` |
| 4 | `geometry-nodes.md` lists 6 socket idnames `new_socket` rejects | replaced the hand-written 24 with the **measured accepted set of 18**, named the 6 rejects explicitly, added the runtime introspection snippet | same run (snippet executed from the doc) | **PASS** — 18 accepted, identical to the doc's list |
| 5 | `bpy-scripting-core.md:31` claims a headless `IMAGE_EDITOR` area | corrected to `VIEW_3D` only + the measured 4-area list + "enumerate, never assume" one-liner | `probe1.py` | **PASS** — background areas = `PROPERTIES, OUTLINER, DOPESHEET_EDITOR, VIEW_3D`; no `IMAGE_EDITOR` |
| 6 | Runner PASS = magic substring; `rc==0` proves nothing; hardcoded "(100% HEADLESS SAFE)" | rewritten (183 lines): each module run through a generated **sentinel shim** (`runpy.run_path(..., run_name='__main__')`, catches `BaseException`, prints `AGENT_OK`/`AGENT_FAIL` JSON, `os._exit` with 0/1/3 so the sentinel is genuinely the last stdout line and the exit code matches the frozen contract). PASS iff last non-empty stdout line starts with `AGENT_OK `. `--factory-startup -b --python-exit-code 3`. Literal removed. | `python3 scripts/boilerplates/run_all_boilerplate_tests.py` | **30/30 PASS in 14.05 s**, exit 0, final `SUMMARY_JSON …` + `AGENT_OK {"total":30,"passed":30}` |
| 7 | 3 disagreeing hand-maintained module lists (30 / 26 / 17) | `--list` added (globs `bp_*.py`, reads each first docstring line via `ast`, no `bpy` import); `python-agent-boilerplates.md` §1 replaced with the generated table + generation command + date; frontmatter/intro no longer state a hand-written count | `python3 scripts/boilerplates/run_all_boilerplate_tests.py --list` | **PASS** — `count: 30`, 30 rows pasted into the doc |
| 8 | 4 boilerplates assert nothing (class C in audit-03) | real postconditions added to each, all within the +15-line budget | `… --only bp_core.py bp_materials_pbr.py bp_render_camera.py bp_rigging.py` | **4/4 PASS** |

### What the 4 new boilerplate asserts actually prove

| Module | lines | Postconditions asserted |
|---|---|---|
| `bp_core.py` | 154 → 169 | collection datablock exists **and** is linked to the scene collection; object linked to it; `obj.data is mesh`; depsgraph round-trip returns `0 == len(mesh.vertices)` verts; `safe_get_socket(Principled, "Base Color")` resolves |
| `bp_materials_pbr.py` | 111 → 126 | Principled BSDF present; `Metallic == 0.95`, `IOR == 1.5`, `Base Color == (0.15,0.16,0.18,1.0)` (values that were passed in are actually written); **exactly 4 links**; Roughness driven by a `MAP_RANGE` node |
| `bp_render_camera.py` | 157 → 172 | `render.engine == 'CYCLES'` read back; `cycles.samples == 16`; `view_transform == 'AgX'`; `cycles.device` self-consistent with the returned backend; camera aim error vs the target < 0.01 rad on the **evaluated** matrix (measured 0.0) |
| `bp_rigging.py` | 168 → 183 | exactly 5 bones; collections `{DEF, CTL}`; `Shin.L` parented to `Thigh.L`; `Foot.L.use_connect`; **measured lengths** `Thigh.L == 0.5 m`, `Foot.L == 0.180278 m`; zero roll (local Z carries no world-X component); IK constraint with `('IK_Target.L','IK_Pole.L',2)` |

## Runner attack results (audit-03 §"The PASS criterion is defeatable")

`scratchpad/w5/run_attack.py` loads the real runner and points `SCRIPT_DIR` at 4 scratch modules.

| Scratch module | Behaviour | Old runner | New runner | Correct? |
|---|---|---|---|---|
| `bp_liar.py` | prints `"… verified successfully."` then `raise RuntimeError` | **PASS** | **FAIL** (`rc=3`, `AGENT_FAIL`, `RuntimeError`) | yes |
| `bp_handled_op_error.py` | catches a real `bpy.ops.uv.smart_project()` error, asserts, completes | **FAIL** | **PASS** (`rc=0`, `AGENT_OK`) | yes |
| `bp_honest_fail.py` | `assert False` before any print | FAIL | **FAIL** (`rc=1`, `AssertionError`) | yes |
| `bp_silent_ok.py` | completes correctly, never prints the magic string | FAIL | **PASS** | yes |

Runner exit: `2/4 PASSED`, exit code **1**, final line `AGENT_FAIL {…"passed":2}`. Full-suite run exits **0**.
Exit codes now follow the frozen contract because the shim owns them: assert → 1, other exception → 3, ok → 0.

## Reproduction commands (all re-run after the last edit)

```bash
cd /Users/jang/Products/Blender
S=/private/tmp/claude-501/-Users-jang-Products-Blender/770d4c04-83d4-40e0-b3f9-1fe468bcd0b0/scratchpad/w5

# 1. the four blockers, code lifted out of the EDITED markdown
python3 $S/extract_kb_blocks.py $S/kb_blocks_run.py
W5_SCRATCH=$S /Applications/Blender.app/Contents/MacOS/Blender \
  --factory-startup -b --python-exit-code 3 --python $S/kb_blocks_run.py

# 2. headless areas / enum_items / device enumeration
/Applications/Blender.app/Contents/MacOS/Blender \
  --factory-startup -b --python-exit-code 3 --python $S/probe1.py

# 3. EEVEE headless on macOS
W5_SCRATCH=$S /usr/bin/time -p /Applications/Blender.app/Contents/MacOS/Blender \
  --factory-startup -b --python-exit-code 3 --python $S/eevee_bench.py

# 4. boilerplate suite + registry + attack
python3 scripts/boilerplates/run_all_boilerplate_tests.py            # 30/30, exit 0
python3 scripts/boilerplates/run_all_boilerplate_tests.py --list     # count: 30
python3 $S/run_attack.py                                             # 2/4, exit 1
```

## Files changed (ownership respected)

`knowledge/30-lighting-render/render-engines.md` (577→609) ·
`knowledge/40-animation/rigging-armature.md` (547→560) ·
`knowledge/60-pipeline/export-interchange.md` (617→650) ·
`knowledge/50-procedural/geometry-nodes.md` (605→633) ·
`knowledge/00-foundations/bpy-scripting-core.md` (373→377) ·
`knowledge/00-foundations/python-agent-boilerplates.md` (88→96) ·
`scripts/boilerplates/run_all_boilerplate_tests.py` (48→183) ·
`bp_core.py`, `bp_materials_pbr.py`, `bp_render_camera.py`, `bp_rigging.py` (asserts only).

**`knowledge/00-foundations/blender-version-matrix.md` NOT touched** — its only `enum_items` use
(line 203, `BooleanModifier.solver`) is a *static* enum and audit-02 F8 confirms it returns
`['FLOAT','EXACT','MANIFOLD']`. No 5.2 fact there needed correcting.

## Two measured gotchas worth carrying forward

1. **`is` is unsafe on bpy structs.** `link.to_socket is bsdf.inputs["Roughness"]` → **False**;
   `==` → **True** (RNA wrappers are recreated per access). Two of my first-draft asserts failed on
   this. Compare with `==` or by name.
2. **`Bone.roll` does not exist** outside Edit Mode (`AttributeError`) — `roll` is an `EditBone`
   property. In Object Mode use `bone.z_axis` / `bone.matrix_local`.

## NOT verified

1. Whether the `enum_items`-empty behaviour is macOS/Metal-specific or universal 5.2 — I only
   proved it on this install (audit-02 unresolved Q1 stays open). The fixes are platform-agnostic
   either way, since they no longer read `enum_items` at all.
2. Whether `enable_cycles_gpu()` actually *renders faster* on METAL — I verified device selection
   and state, not a timed GPU render.
3. `assert_valid_glb` against a real textured/animated multi-mesh GLB and against `.gltf` +
   separate `.bin` — tested on a single cube (Draco + plain) and one truncated file only.
4. `NodeSocketVector2D/4D` alternative path — the doc says "no `new_socket` path in 5.2" and marks
   the `socket.dimensions` suggestion `[UNVERIFIED]`; I did not test `dimensions` writability.
5. Whether the 26 previously-asserting boilerplates assert the *right* things — audit-03's class B
   ("polys > 100") critique is untouched; only the 4 class-C modules were given asserts.
6. Any 4.5 LTS behaviour — only 5.2.0 is installed here.

## Out-of-scope defects found (for the controller / other workers)

1. **`scripts/boilerplates/bp_render_camera.py:39` carries the exact same `enum_items` bug** as the
   KB helper I fixed: `configure_cycles_headless()` gates on
   `cprefs.bl_rna.properties['compute_device_type'].enum_items.keys()` and therefore returns
   `'CPU'` on this Metal Mac. My ownership permits asserts only, so I asserted *self-consistency*
   (`cycles.device` matches the returned backend) rather than `backend == 'METAL'` — which would
   have turned a real defect into a red suite. **This module still silently renders on CPU.**
   Recommend porting the fixed `enable_cycles_gpu()` body into it.
2. **`knowledge/10-modeling/uv-unwrapping.md:27` and `:216`** repeat the false headless
   `IMAGE_EDITOR` claim (`:222` then filters for an area that does not exist in background).
   Not in my ownership.
3. `knowledge/INDEX.md:215` ("30 modules passing 100% headless") and its 17-item bullet list are
   still hand-maintained; the generated `--list` output is now the single source of truth.

## Unresolved questions

1. Should `--list` output be committed as a generated artefact (e.g. `scripts/boilerplates/registry.json`)
   so `INDEX.md` and the KB doc can both be diffed against it in CI, rather than pasted by hand?
2. The sentinel shim uses `os._exit()` to keep `AGENT_OK` as the last stdout line (Blender prints
   "Blender quit" on normal teardown). Worker A's `agent_runtime.py` will face the same problem —
   does the frozen contract want `os._exit`, or "last line matching `AGENT_(OK|FAIL)`" instead of
   "last line is"? A looser matcher would remove the need for `os._exit` but weakens the contract.
3. Single-cube GLB sizes differ between runs: audit-02 measured 936 B / 1400 B, I measure
   1120 B / 1732 B with the KB's own kwargs on one default cube. Unimportant for the gate (both are
   far below the old 2048 threshold) but the doc now states my numbers — worth one line from
   audit-02's author on which scene it used.
4. `bp_render_camera.py`'s CPU fallback (above) — fix it in W5's follow-up or hand it to whoever
   owns `scripts/boilerplates/` content?

Status: DONE_WITH_CONCERNS
Summary: All 4 KB blockers + the GN socket list + the IMAGE_EDITOR claim fixed and re-executed clean by extracting the code straight out of the edited Markdown on the real 5.2.0 install; the runner now decides PASS by the `AGENT_OK` sentinel (liar module FAILs, handled-operator-error module PASSes), `--list` prints 30 modules and feeds the now-generated KB registry, and all 30 modules pass with real asserts added to the 4 that had none.
Concerns/Blockers: `scripts/boilerplates/bp_render_camera.py` still contains the same `enum_items` defect and silently selects CPU on this Metal Mac — my ownership allowed asserts only, so it is reported, not fixed; `knowledge/10-modeling/uv-unwrapping.md` repeats the false headless `IMAGE_EDITOR` claim and is outside my file list.
