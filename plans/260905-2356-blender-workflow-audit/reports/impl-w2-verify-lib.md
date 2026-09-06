# W2 — verify lib rewrite, KB dedupe, tests

Worker B. 2026-09-06. Blender 5.2.0 LTS (`fbe6228777e7`), macOS. Every run fresh
`--factory-startup -b`; GUI PID 14172 never contacted. Scratch:
`/private/tmp/claude-501/-Users-jang-Products-Blender/770d4c04-83d4-40e0-b3f9-1fe468bcd0b0/scratchpad/w2/`.

## Conclusion

E2 is closed. Every row of audit-03's before/after table now reads **Restored: yes**,
proven by 7 tests that pass in 5.3 s. `verify_export` can no longer touch the live
scene at all — the re-import happens in a separate headless process. `scaffold()` no
longer overwrites anybody's units, fps or engine. The KB no longer carries a second
copy of the code.

One deliberate structural change: the lib is now `scripts/agent-verify-lib.py`
(70-line exec-able facade) over `scripts/agent_verify/` (5 modules, 24–77 lines each).
A single file came to 285 lines, over the project cap.

## What changed

**`scripts/agent-verify-lib.py`** — facade. Locates `agent_verify/` (own dir →
`$AGENT_REPO_ROOT/scripts` → `sys.path` → walk-up from cwd / `__file__` / `sys.argv`
`.py` / the open `.blend`), drops any stale `agent_verify` from `sys.modules` so each
load is fresh, binds the 13 public names into the caller's namespace, prints
`AGENT_LIB_OK bpy=(5, 2, 0) lib_sha=<8 hex>` (sha over the package sources plus the
facade). Works under `exec(open(path).read())` and under an exec-into-module loader.

**`scripts/agent_verify/paths.py`** — `repo_root()` walks up from the package's real
`__file__` looking for `scripts/` + `knowledge/`, else `$AGENT_REPO_ROOT`, else cwd.
No `/Users/jang` anywhere in the tree any more.

**`inspect_scene.py`** — `assert_exists, tri_count, world_bbox, has_material, framing,
frame_stats` unchanged in name and behaviour. Read-only.

**`preview.py`** — `preview_render(path=None, res=256, samples=16, engine="EEVEE")`.
Captures 10 values before writing anything (`resolution_x/y`,
`resolution_percentage`, `filepath`, `engine`, `film_transparent`,
`image_settings.file_format`, `image_settings.color_mode`, `cycles.samples`,
`eevee.taa_render_samples`) and restores all of them in `finally`. Asserts the
operator returned `{'FINISHED'}` and that the file exists. Default path
`$AGENT_PREVIEW_DIR` else `<repo>/output/previews/agent-preview.png`; parent dirs
created. Engine aliases: `EEVEE`→`BLENDER_EEVEE`, `CYCLES`, `WORKBENCH`.

**`export_check.py`** — `verify_export(path, expect_objects, expect_min_tris,
timeout=300)` raises `AssertionError` **before** launching anything if the file does
not exist, then runs the re-import in
`<blender> --factory-startup -b --python-exit-code 3 --python <tmp checker> -- <path>
<op module> <op name>` and parses the checker's `EXPORT_CHECK <json>` line. The
checker is a module-level string written to a tempfile; the format→operator dispatch
lives once in `IMPORT_OPS` and is passed to the checker as argv, so `import_any` and
the isolated checker cannot drift. No `read_homefile` anywhere in the parent process.

**`session.py`** — `scaffold(force=False, unit_scale=1.0, engine="CYCLES", fps=24,
collections=...)` returns `{setting: {"before", "after", "changed"}}` for
`unit_system, scale_length, engine, fps, collections`. Writes a setting only when it
still equals the Blender 5.2 factory value (`METRIC`, `1.0`, `BLENDER_EEVEE`, `24`)
or when `force=True`. Collections are created/linked, never removed.
`checkpoint(tag, root=None)` root from `$AGENT_CHECKPOINT_DIR` else
`<repo>/output/checkpoints`.

Stale comment "local may be 4.x" removed; the `bpy.app.version < (5, 0)` FBX branch
kept (it is a real version branch, not a stale claim).

**`knowledge/00-foundations/agent-workflow-loop.md` §4** — all function bodies gone,
replaced by the load snippet plus an 11-row table (function → purpose → safety class:
read-only / restoring / isolated / mutating). Subsection numbers 4.3, 4.4, 4.6 kept
because §5 links to them; the framing teaching prose, the `stdev < 0.01` rule and the
"an export is not verified until re-imported" rule survive as prose. §7 checklist
preview bullet now names `preview_render(engine="EEVEE")` as the cheap gate. File
294 → 225 lines.

**`knowledge/60-pipeline/scene-organization.md` §4.1** — `scaffold` →
`scaffold_new_scene`, `reset` now defaults to **False**, docstring warns that
`reset=True` deletes the scene and points at the non-destructive `scaffold()` in the
lib. Heading no longer says "run this first, in every task".

## Test summary (verbatim)

```
$ python3 -m unittest discover -s tests/execution -p 'test_verify_lib*' -v
test_both_engines_render_a_preview_headless (test_verify_lib.VerifyLibTest.test_both_engines_render_a_preview_headless) ... ok
test_lib_loads_and_prints_sentinel (test_verify_lib.VerifyLibTest.test_lib_loads_and_prints_sentinel) ... ok
test_preview_render_failure_restores_everything (test_verify_lib.VerifyLibTest.test_preview_render_failure_restores_everything) ... ok
test_preview_render_success_restores_everything (test_verify_lib.VerifyLibTest.test_preview_render_success_restores_everything) ... ok
test_scaffold_keeps_non_factory_settings_unless_forced (test_verify_lib.VerifyLibTest.test_scaffold_keeps_non_factory_settings_unless_forced) ... ok
test_verify_export_missing_file_raises_and_scene_survives (test_verify_lib.VerifyLibTest.test_verify_export_missing_file_raises_and_scene_survives) ... ok
test_verify_export_real_glb_passes_and_scene_survives (test_verify_lib.VerifyLibTest.test_verify_export_real_glb_passes_and_scene_survives) ... ok

----------------------------------------------------------------------
Ran 7 tests in 5.348s

OK

128px/8-sample preview, in-process seconds: CYCLES=0.052, EEVEE=0.177
```

`python3 -m unittest discover -s tests/knowledge` still 28 tests OK (0.189 s) — the
KB edits broke no knowledge test.

Each test spawns its own headless Blender with `AGENT_REPO_ROOT`,
`AGENT_PREVIEW_DIR`, `AGENT_CHECKPOINT_DIR` pointed at a fresh tempdir, runs a fixture
from `tests/execution/fixtures/verify-lib/`, and asserts on the fixture's
`RESULT <json>` line. Fixtures snapshot all 10 touched settings plus units, fps and
the object list before and after each call.

## E2 table, after

| Call | Setting | Before | After | Restored? |
|---|---|---|---|---|
| `scaffold()` | `unit_settings.scale_length` | 0.5 | 0.5 | **yes** (`changed: false`) |
| `scaffold()` | `render.fps` | 30 | 30 | **yes** (`changed: false`) |
| `scaffold()` | collections | 1 | 5 | n/a — adds only, never removes; reported in `collections.changed` |
| `preview_render()` success | resolution / percentage / filepath | 960×720 / 50 / `/tmp/ORIGINAL_OUTPUT_` | identical | yes |
| `preview_render()` success | `cycles.samples` | 99 | 99 | **yes** |
| `preview_render()` success | `eevee.taa_render_samples` | 77 | 77 | **yes** |
| `preview_render()` success | engine / film_transparent / file_format / color_mode | CYCLES / True / JPEG / RGB | identical | **yes** |
| `preview_render()` failure (no camera) | all 10 settings | as set | identical, `RuntimeError` raised | **yes** |
| `verify_export(missing)` | objects | 4 (incl. `UNSAVED_WORK`) | 4 | **yes** — `AssertionError` before any subprocess |
| `verify_export(real glb)` | objects / engine / resolution / `cycles.samples` | 4 / EEVEE / 1920×1080 / 4096 | identical | **yes** — check ran in another process |

## Timing — EEVEE vs CYCLES preview, headless

Default cube scene, 3 cold processes each. `render_s` = in-process
`preview_render` wall time; `real` = whole Blender process including 0.5 s start.

| Engine | res / samples | render_s (3 runs) | real (3 runs) | frame stdev |
|---|---|---|---|---|
| EEVEE | 128 / 8 | 0.168 · 0.181 · 0.166 | 0.69 · 0.70 · 0.67 | 0.0824 |
| CYCLES | 128 / 8 | 0.098 · 0.100 · 0.096 | 0.60 · 0.60 · 0.60 | 0.0823 |
| EEVEE | 256 / 16 | 0.196 · 0.212 · 0.223 | 0.71 · 0.74 · 0.74 | 0.0827 |
| CYCLES | 256 / 16 | 0.157 · 0.158 · 0.156 | 0.69 · 0.68 · 0.67 | 0.0826 |

Both engines render headless. **EEVEE is not the faster one on this scene** — Cycles
beats it by 0.04–0.07 s at these sizes (adaptive sampling terminates almost
immediately on a default cube). EEVEE stays the default because it does not need a
sample budget chosen per scene and it is what the plan froze; the cost argument for it
does not survive measurement on a trivial scene, and nothing here measures a heavy one.

Falsification run before trusting these: with `samples` 8 → 512 → 4096 the Cycles time
rose 0.051 → 0.070 → 0.091 s and every image hash differed, so Cycles is really
rendering, not silently falling through to EEVEE. Reading `scene.render.engine` after
`preview_render` returns `BLENDER_EEVEE` — that is the `finally` restore, not the
render engine used.

## Files referencing the old `scaffold` name (not edited — outside ownership)

| File | What | Owner |
|---|---|---|
| `knowledge/catalog.json:7228` | heading `"4.1 Deterministic scaffold — run this first, in every task"` | stale after the rename |
| `knowledge/catalog.json` (agent-workflow-loop entry) | headings `4.1 The scaffold…`, `4.2 Assertion helpers…`, `4.5 Checkpointing` | stale after the §4 rewrite |
| `.agents/skills/blender-agent-core/SKILL.md:31` | "Scaffold không phá — `scaffold()` … chỉ ghi khi factory-default hoặc `force=True`" | already matches the new behaviour |
| `.claude/skills/blender-agent-core/SKILL.md:38` | older wording, and already out of sync with `.agents/` | W4 mirror sync |
| `plans/reports/orchestrate-260905-blender-knowledge/review-snapshot/**` | historical snapshot copies | leave |
| `plans/…/backup/**` | rollback snapshot | leave |

`python3 scripts/blender-knowledge.py check` currently returns
`{"status": "error", "message": "Owned mirror drift: .agents/skills/blender-agent-core/SKILL.md"}`
— that drift is pre-existing and W4's; it aborts before reaching catalog staleness. A
`blender-knowledge.py build` is required after W4 lands, to pick up the new §4 headings.
I did not run it (writes `knowledge/catalog.json`, outside ownership).

No file in `builds/`, `scripts/boilerplates/`, or `tests/blender/` calls `scaffold(`,
`preview_render(`, `verify_export(` or `checkpoint(` — grep across the repo found zero
call sites outside the new tests. The API change to `scaffold`'s return value
(collection dict → report dict) therefore breaks no existing caller.

## Attacks run

- `preview_render` twice in a row in one session — both restore, both write files.
- `preview_render` with a path in a directory that does not exist — directory created,
  image written.
- `preview_render` with no camera — `RuntimeError`, all 10 settings restored.
- `verify_export` on a missing path while the scene held an unsaved `UNSAVED_WORK`
  object — raised, object survived, settings identical.
- `verify_export` on a real exported `.glb` — passed (`{"objects": ["Cube"], "tris": 12}`),
  `UNSAVED_WORK` and all settings survived.
- Worker A's `agent_runtime.load_lib("<root>/scripts/agent-verify-lib.py")`, run
  after his file landed, with cwd `/` and no `AGENT_REPO_ROOT`: module carries all
  public names, `repo_root()` resolves, the sha cache returns the same module on a
  second call, and `preview_render()` writes an image. (`load_lib` sets
  `module.__file__` to the lib path, which is the facade's first and best clue.)
- Facade loaded 4 ways: relative path with cwd = repo; absolute path from a payload
  inside the repo with cwd `/tmp` and no env; MCP style
  (`sys.path.insert(0, "<root>/scripts")` then exec) with cwd `/`; payload outside the
  repo with `AGENT_REPO_ROOT` set. All four print `AGENT_LIB_OK` and resolve
  `repo_root()` correctly.
- Payload outside the repo, cwd outside the repo, `AGENT_REPO_ROOT` unset → loud
  `ImportError` naming the fix. This is the one load path the old single file survived
  and the split does not; see below.

## Not verified

- Live-GUI behaviour. Everything was headless (hard rule). The restore paths are the
  same code, so GUI correctness is INFERENCE, not FACT.
- Cost of either engine on a real build scene. All timings are the default cube.
- `import_any` on `.fbx` and `.obj`, and `verify_export` on anything but `.glb`. Only
  the glTF path was exercised end to end.
- `checkpoint()` — carried over unchanged apart from the root resolution; the new root
  logic is exercised only through `repo_root()` in other tests, not by a save.
- Whether `bpy.ops.render.render` can return `{'FINISHED'}` while writing a corrupt
  file. `os.path.exists` is checked; content is not.

## Unresolved questions

1. The facade cannot find its package when the payload, the cwd and the `.blend` are
   all outside the repo, `AGENT_REPO_ROOT` is unset, and the load is a bare
   `exec(open(abs_path).read())` (not `load_lib`, which supplies `__file__`). It fails
   loudly with the fix in the message, but the old single-file lib worked there. Should
   `headless-run.sh` export `AGENT_REPO_ROOT` (worker A's file), or should the docs just
   say to set it?
2. `scaffold()`'s "factory default means unset" rule cannot distinguish a scene that
   was never configured from one deliberately set to a factory value. Acceptable?
3. `scaffold()`'s return type changed from `{name: Collection}` to a report dict. No
   caller exists today, but is the collection handle wanted back as an extra key?
4. `verify_export` spawns a Blender per call (~0.5 s). Fine at current call volume; if
   a gate ever verifies many exports, it should batch them into one subprocess.
5. `knowledge/catalog.json` is now stale for two documents. Who runs
   `blender-knowledge.py build`, and after which workstream?
