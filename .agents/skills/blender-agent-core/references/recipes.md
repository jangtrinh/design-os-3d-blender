# Blender operational recipes

Load only the section triggered by the task. These recipes reuse existing scripts and KB; they are not a new execution framework. Source evidence and missing automation are in the [workflow](../../../../docs/blender-ai-workflow.md) and [backlog](../../../../docs/blender-workflow-improvement-backlog.md).

## Explicit execution context

Preflight thủ công trước khi build, ghi lại trong task record:

- Interpreter thực sự chạy payload: Blender version/build, `sys.executable`, Python version; host Python có package không chứng minh Blender Python có package đó.
- Dependencies đúng interpreter: kiểm tra import/`importlib.util.find_spec` của package được dùng; nếu thiếu, chọn code không phụ thuộc hoặc môi trường đã có. Không tự cài hàng loạt hoặc thử import mù lặp lại.
- Scene hiện tại: absolute input path, scene name, mode, units/scale, active camera và frame range; xác nhận thuộc scope đã giao.
- API cần dùng: introspect RNA enums/sockets/operator availability; compiler-check script trước execution và đặt imports/helpers/`__file__` trong namespace rõ ràng.
- Controller duy nhất, checkpoint/input identity, output root, checker và postcondition của pass; port-open chỉ là tín hiệu transport, không phải scene readiness.

Each reviewed disk payload executed through MCP runs through the runtime module, which owns the namespace, the traceback and the sentinel:

```python
import sys; sys.path.insert(0, '<ROOT>/scripts')
import agent_runtime as rt
rt.run_file('/absolute/path/to/reviewed-pass.py')   # last stdout line: AGENT_OK {...} | AGENT_FAIL {...}
```

Imports/helpers must be inside that payload or loaded into that namespace. This preserves traceback source lines and does not assume values from a previous tool call. It is unrestricted Python, not a sandbox. Reject a failed postcondition even when the transport says execution succeeded. See [hard rules](hard-rules.md) for unknown outcomes.

For isolated read/verification or fault probes use a fresh headless process with explicit Python failure exit:

```text
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup --disable-autoexec -b [trusted-input.blend] --python-exit-code 23 --python [checker.py]
```

Brackets are placeholders. Put options before the action they affect. Auto-execution policy must match the trusted asset's driver needs; do not silently disable required behavior or enable untrusted startup scripts. `scripts/headless-run.sh` now supplies `--factory-startup --disable-autoexec --python-exit-code 3` and derives its exit from the last-line sentinel `AGENT_OK`/`AGENT_FAIL`; still verify the sentinel JSON, report identity and assertions together — exit code alone is not a gate. Use an external bounded supervisor only for its own disposable process; no killing the live GUI because it seems slow.

## Production contract

Trigger: any part that will be printed, machined or assembled with real hardware. Load `60-pipeline/3d-printing.md`, `70-cad-precision-robotics/cad-precision-modeling.md`, `fasteners-seals-mechanics.md`, `polymer-3dprinting-cad.md`; read `specs/README.md`.

1. **Before detailing**, write `builds/<slug>/spec.json` per `specs/build-spec.schema.json`: units mm; every part with `target_dims_mm` ± `tol_mm`, `material`/`process`/`orientation_up`, `min_wall_mm`, `max_overhang_deg`, `expected_shells`; every hole/boss/slot with axis, center, diameter ± tol and the fastener standard it serves; declared `load_cases` and `physical_evidence` still required. Missing numbers → verdict `request-input`; do not model around a guess.
2. Model in metres (`scale_length == 1`), apply transforms, one object per printed part, name = spec `object`.
3. Run the gate in an isolated process before any delivery claim:
   `python3 scripts/production-gate.py --scene builds/<slug>/<file>.blend --spec builds/<slug>/spec.json --report builds/<slug>/reports/gate-report.json --export-dir builds/<slug>/parts`
   Exit `0` pass · `1` requirement failed · `2` spec/scene incomplete · `3` execution error. The report binds scene+spec sha256, checker version, per-part measured vs allowed, `failed[]`, `coverage`, `exclusions`.
4. Read `coverage.unchecked` and `exclusions`: a passing gate proves topology, dimensions, feature diameters, wall/overhang screens and STL round-trip. It does **not** prove load capacity, fit after shrinkage, thermal duty, retention or assembly access — those stay `physical_evidence` items and keep manufacture `BLOCKED` until supplied.
5. Any geometry change re-runs the gate; an older report cannot be inherited (hash mismatch is rejected by design).

## Articulated task

Trigger: linked joints, tool swaps, grasping or task demonstrations. Load `40-animation/animation-fcurves.md`, `70-cad-precision-robotics/robotics-urdf-mechanisms.md` and their declared dependencies.

1. Define joint frames/axes/limits and descendants; retain separate removable parts. Derive end-effector/grip datum from actual native transforms and compare analytic FK/IK against evaluated scene transforms.
2. Check one real hand interaction early: open approach, close, lift and release. Distinguish rigid jaw collisions, allowed pad contact, numerical residue and modeled gaps. Props may be designed for a declared task; do not imply the gripper handles arbitrary objects.
3. Map requested abilities to story events; produce a short animatic and representative event poses before expensive render. Rear placement through yaw is not the same as a backward shoulder bend; record coverage honestly.
4. Check path poses, camera envelope, attachment/release continuity and final supports. Record contact exceptions, sampling interval and predicate limits; use continuous/solid tests when the claim requires them.
5. Preserve separate performance/physics status. A keyed relative payload transform proves authored alignment, not friction, grip force, holding torque or real controller behavior.

Arm examples: [motion plan](../../../../builds/robot-arm-v2-engineered/task-motion-plan.py), [props/datum](../../../../builds/robot-arm-v2-engineered/task-props.py), [path check](../../../../builds/robot-arm-v2-engineered/check-task-path.py), [presentation check](../../../../builds/robot-arm-v2-engineered/verify-task-presentation.py). These are artifact-specific examples, not generic APIs. The path script currently writes failure status without a failing exit; inspect its JSON explicitly until E3 is implemented. Do not run these builders against a different/live file without reviewing their scene ownership and input assumptions.

## Assembly and exploded views

Use [assembly sequences](assembly-sequences.md) for removable-part films: dependency graph, separated waiting poses, swept insertion, phase-bound contact exceptions and short animatic before full render. Joint range demos and assembly paths are separate verification scopes.

## Mechanical evidence

Trigger: printable, functional, load-bearing, removable hardware or thermal duty. Load `60-pipeline/3d-printing.md` and relevant `70-cad-precision-robotics/` files.

- Start with payload excluding tool, reach, hold duration, motion rates, material/process and actuator dimensions/continuous ratings. Obtain exact source drawings and distinguish rated/continuous evidence from stall torque. Do not infer unseen mounting geometry from a product render.
- Keep a component register for printed/purchased/metal parts and a dependency map: geometry → mass/centre of mass → joint loads → actuator/thermal/retention evidence. Clearance edits can change structural sections even if topology remains closed.
- Check wall/fit/fastener engagement, real output adapters, access/assembly, range, anchoring and cabling with predicates appropriate to each. A surface intersection screen is neither a solid containment check nor a continuous sweep.
- Export separated fit prototypes with stated units and revision, then re-import/check actual files in a fresh process. Printing, fit trials and loaded thermal/strength tests remain independent release gates.
- Carry physical blockers explicitly through film/export delivery. No visual-only acceptance can downgrade a user-approved payload/duty requirement.

Arm reference: [independent final check](../../../../builds/robot-arm-v2-engineered/reports/independent-final-check.md) and [flexibility review](../../../../builds/robot-arm-v2-engineered/reports/independent-flexibility-review.md). This arm remains blocked for manufacture; baseline STL evidence does not certify revised clearance cuts.

## Render delivery

Trigger: animation, batch rendering or exported media. Load `30-lighting-render/render-engines.md`, `30-lighting-render/compositing-output.md` and the relevant export/product-shot KB.

Use the scene's established working profile first. If tuning is justified, declare one metric, same representative frames, quality guards, one variable and a trial cap before comparing. GPU warmup, cold-start time and concurrent processes must not be mixed into a claimed speedup.

Freeze input file, scene, renderer/device, samples/denoiser, resolution, camera, fps/frame range and script identity. Current arm scripts support manual ranges; automatic validated resume is still E4. Reuse frames only when this input identity matches and each image is complete. Changed geometry/camera/lighting starts a new frame directory. A delay alone is not proof a frame failed.

Render raw images, process optional overlays separately, then encode. Before using an encoder filter, inspect local availability. Verify frame count, dimensions, duration/fps, decode errors and representative decoded frames; watch motion for timing/flicker when making those quality claims. Delivery clean versus annotated follows this task's brief, not a global no-caption rule.

Arm examples: [renderer](../../../../builds/robot-arm-v2-engineered/render-task-demo.py), [video verifier](../../../../builds/robot-arm-v2-engineered/verify-task-video.py), [final check](../../../../builds/robot-arm-v2-engineered/reports/task-video-check.json). This 30-second case used 720 raw PNGs; subtitle removal needed encoding only. Its settings are an example, not a universal quality target.

## Revision-bound acceptance

A future generic report should carry `artifact identity`, `scene`, `checker/config identity`, `frame coverage`, `exclusions`, `observed result`, `review evidence`, and independent `media / motion / fit / manufacture` statuses. This is a proposed contract; no common schema validator is installed yet.

Negative review example: media PASS + sampled-surface PASS + changed geometry + unresolved torque must remain manufacture BLOCKED. Reject inherited geometry-dependent approvals from the earlier revision. For current reports without identity fields, compare saved source/timing and explicitly disclose the weaker provenance; never fabricate missing hashes.
