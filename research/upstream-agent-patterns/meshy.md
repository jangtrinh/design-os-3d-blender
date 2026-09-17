# Meshy 3D Agent — pinned source audit for native Blender orchestration

Audit date: 2026-09-17
Upstream: `https://github.com/meshy-dev/meshy-3d-agent`
Pinned commit: `b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610`
Commit date: 2026-08-08T19:16:45+08:00
Commit subject: `[Fix] Correct API facts that make agents do the wrong thing (ENG-1576) (#7)`

This is a source-pattern audit, not permission to call Meshy or import generated/vendor assets. `design-os-3d-blender` keeps its Native Asset Policy: production geometry remains Blender-native and local. The useful upstream material is the orchestration discipline around asynchronous work, task lineage, bounded skill references, generated-copy drift checks, output organization, and print-boundary thinking.

The upstream was cloned with `--depth 1 --filter=blob:none --no-checkout` into `research/tools/upstream-260917/meshy-3d-agent`; all inspection used `git show <commit>:<path>`. No upstream script was executed, no checkout was created, and no API/service call was made.

## License and attribution

The repository root is MIT licensed: the license grants use/modification/distribution subject to preserving the copyright and permission notice ([LICENSE L1-L20](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/LICENSE#L1-L20)). Generation and printing skill frontmatter also says `MIT`; the OpenClaw skill says `MIT-0`, which conflicts with the root license declaration ([generation SKILL L1-L10](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/SKILL.md#L1-L10), [printing SKILL L1-L10](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-printing/SKILL.md#L1-L10), [OpenClaw SKILL L1-L21](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-openclaw/SKILL.md#L1-L21)). This audit adopts ideas and contracts rather than copying substantial upstream implementation. Any later code copy must retain the applicable upstream notice and resolve the MIT/MIT-0 ambiguity first.

## What the upstream actually implements

### 1. A thin task runner around an asynchronous service

The canonical runner is `scripts/src/meshy_task.py`. It exposes a small library/CLI surface for create, poll, download, project directory creation, recording and thumbnails ([meshy_task.py L1-L7](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L1-L7)). `create_task()` posts a payload and returns the service task ID; the CLI variant prints the raw ID as the final stdout line so shell composition can capture it ([L94-L116](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L94-L116), [L290-L319](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L290-L319)).

The reference explicitly models every remote job as asynchronous and lists the state progression `PENDING -> IN_PROGRESS -> SUCCEEDED | FAILED | CANCELED` ([reference/source.md L23-L25](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/reference/source.md#L23-L25), [L93-L99](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/reference/source.md#L93-L99)). The skill then composes endpoint-specific pipelines from the shared CLI rather than having every prompt reconstruct network logic ([generation SKILL L93-L95](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/SKILL.md#L93-L95)).

**Essence to adopt locally:** a stable runner should own execution truth; higher-level recipes should compose runner calls and never reimplement execution semantics inline.

### 2. Polling is resumable by task ID, but timeout is an unknown outcome

`poll_task()` uses 5-second initial polling with 1.5x backoff capped at 30 seconds, switching to a fixed 15 seconds at 95%+ progress. It returns only on `SUCCEEDED`; it exits on `FAILED`, `CANCELED`, or local timeout ([meshy_task.py L119-L153](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L119-L153)). The CLI duplicates that polling implementation rather than calling `poll_task()` ([L338-L382](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L338-L382)).

Crucially, the troubleshooting guide says a local poll timeout usually is **not** a remote task failure: invoke `poll` again with the same task ID and a larger timeout because the task continues server-side ([troubleshooting.md L22-L24](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/references/troubleshooting.md#L22-L24)). That is the right semantic insight even though the code represents it only as `sys.exit("TIMEOUT ...")`.

**Essence to adopt locally:** timeout/transport loss after execution starts is `unknown`, never `failed` and never an invitation to replay automatically. A durable journal must say an attempt started before execution and require reconciliation before any repeat.

### 3. Retry policy is documented but not enforced by the runner

The troubleshooting reference claims 429 should auto-retry after 5 seconds up to three times and 5xx should auto-retry once after 10 seconds ([troubleshooting.md L5-L13](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/references/troubleshooting.md#L5-L13)). The canonical implementation does something different: create paths immediately `sys.exit` on 429, while ordinary 5xx falls through `raise_for_status()` with no retry ([meshy_task.py L94-L116](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L94-L116), [L299-L318](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L299-L318)). Poll GET failures similarly call `raise_for_status()` directly ([L135-L153](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L135-L153)).

This is a **described-vs-enforced defect** at the pinned commit. There are no upstream unit/integration tests in the Git tree that would expose the mismatch.

**Essence to adopt locally:** retry must be part of the executable state machine, not prose. More importantly for Blender, retry classes must distinguish a pre-execution launch failure from an execution with unknown completion; only the former can be retried automatically.

### 4. Delete exists upstream, cancellation orchestration does not

The reference documents per-endpoint `DELETE .../:id` as permanent task/data deletion, for example Text-to-3D ([reference/source.md L304-L318](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/reference/source.md#L304-L318)). The task runner has no delete/cancel subcommand in its CLI dispatch ([meshy_task.py L460-L546](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L460-L546)); it only recognizes a service-returned `CANCELED` status while polling ([L143-L153](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L143-L153)). The reference calls DELETE “delete task,” not “cancel running task,” so it would be unsafe to infer cancellation semantics from that endpoint.

**Essence to adopt locally:** state machines need an explicit stop/reconcile contract. `design-os-3d-blender` should not invent a universal cancellation promise for Blender subprocesses; an interrupted process becomes `unknown` unless the launcher can prove termination before mutation.

## Task lineage, history and output handling

### Good pattern: project-scoped lineage

The generation skill requires every project to live under one structured output directory and asks chained tasks such as preview → refine → rig to reuse the same `project_dir`; tasks are accumulated into project `metadata.json` and global `history.json` ([generation SKILL L48-L66](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/SKILL.md#L48-L66)). The default Text-to-3D recipe captures a preview ID, creates a project directory, downloads/records the preview, then creates a refine task referencing `preview_task_id` and keeps the same project directory ([pipelines.md L15-L43](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/references/pipelines.md#L15-L43)).

This makes the lineage visible and supports follow-up edits without losing the root task identity. Retexture, remesh, resize, rigging and animation similarly consume earlier task IDs rather than pretending each stage is unrelated ([pipelines.md L145-L214](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/references/pipelines.md#L145-L214), [L218-L263](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/references/pipelines.md#L218-L263)).

**Adapt for design-os:** represent each Blender pipeline step with explicit `depends_on` and immutable source/input hashes. Revisions are new attempts or downstream steps; do not overwrite an earlier accepted attempt.

### Weak pattern: history is late, mutable and not crash-safe

`record_task()` creates or loads `metadata.json`, appends a task record, then rewrites the file; it separately loads/rewrites global `history.json` ([meshy_task.py L181-L229](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L181-L229)). Writes are plain `json.dump(open(..., "w"))`: there is no atomic replace, fsync, file locking, attempt sequence, source/input hash, output hash, or duplicate-task protection.

More seriously, recipes normally call `record` only **after** create → successful poll → download ([pipelines.md L20-L42](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/references/pipelines.md#L20-L42)). `poll --project-dir` writes the full task JSON only after it reaches success ([meshy_task.py L353-L389](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/src/meshy_task.py#L353-L389)). A process death after task creation, a `FAILED`/`CANCELED` response, or a local timeout therefore may leave no project-level durable record of what started.

Output filenames in recipes such as `preview.glb`, `refined.glb`, `model.glb`, or `remeshed.glb` are also mutable names inside the reused project directory ([pipelines.md L27-L42](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/references/pipelines.md#L27-L42), [L168-L182](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-generation/references/pipelines.md#L168-L182)).

**Adapt for design-os:** persist `running` before launch, append rather than rewrite attempt history, hash every declared input/output, and give each attempt an immutable output directory. The generic orchestration layer may prove only an `executed` receipt scoped to measured execution postconditions and declared artifact hashes; geometry, visual, fit and manufacture gates remain separate predicates.

## Skill packaging and drift control

### Strong idea: canonical sources plus generated copies

The README identifies canonical sources and generated destinations: `reference/source.md` fans out to each skill’s `reference.md`, `scripts/src/meshy_task.py` fans out to three skill copies, and printing helper sources fan out to OpenClaw copies ([README L227-L244](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/README.md#L227-L244)). `scripts/build.py` implements byte-for-byte freshness checks for generated reference/script copies and also checks linked references and a 300-line SKILL limit ([build.py L189-L271](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/build.py#L189-L271)).

The separate validator adds useful packaging gates: frontmatter semantics/version shape ([validate_skills.py L127-L166](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/validate_skills.py#L127-L166)), synchronized versions ([L169-L229](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/validate_skills.py#L169-L229)), reference reachability from `SKILL.md` ([L337-L377](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/validate_skills.py#L337-L377)), and prevention of references escaping an independently installable skill directory ([L380-L434](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/scripts/validate_skills.py#L380-L434)).

This closely matches the direction already present in design-os: bounded reading packs, canonical `.agents` skills, mirrored `.claude` skills, and hash-bound catalog review.

### Defect: README claims generated-copy CI enforcement that the workflow does not run

README says CI runs `python3 scripts/build.py --check` to reject stale generated outputs ([README L237-L244](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/README.md#L237-L244)). The actual workflow installs PyYAML and runs only `python scripts/validate_skills.py` ([validate-skills.yml L16-L30](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/.github/workflows/validate-skills.yml#L16-L30)). `validate_skills.py` contains no call to `build.py`, no generated-copy byte comparison and no 300-line check. At the pinned commit, those `build.py --check` gates exist but are **not CI-enforced**.

There is no `tests/` path in the pinned Git tree. The only automated upstream workflow found is this structural skill validator. Therefore runtime claims about retry, polling, history mutation, file download correctness and printing transforms are source-audited but not upstream test-certified.

**Essence to adopt locally:** keep source-of-truth and mirror/hash checks, but execute the freshness gate in the actual CI/publication path. A rule that exists only in a dormant script is still manual.

## Printing and coordinate boundaries

The printing skill makes a good architectural decision: print intent owns the pipeline from generation-time parameters onward rather than receiving a generic model at the end ([printing SKILL L15-L29](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-printing/SKILL.md#L15-L29)). It separates automated topology screening from manual print-quality checks. The printability recipe recognizes `healthy`, `warning`, `error`, and `unknown` results and explicitly routes `unknown` to manual inspection/retry ([printing.md L37-L85](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-printing/references/printing.md#L37-L85)).

However, its local OBJ fixer is unsuitable as a production contract for design-os. It unconditionally assumes glTF-style Y-up input, rotates `(x, y, z) -> (x, -z, y)`, scales to a default 75 mm height, centers XY, and places the bottom at Z=0 ([fix_obj.py L13-L20](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-printing/scripts/fix_obj.py#L13-L20), [L30-L68](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-printing/scripts/fix_obj.py#L30-L68)). The printing walkthrough then runs this in place by default ([printing.md L118-L130](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-printing/references/printing.md#L118-L130)).

For design-os production parts, 1 BU = 1 m and dimensions originate in a spec in millimetres. Arbitrary “fit to 75 mm” normalization would destroy dimensional correctness. Coordinate conversion must instead be an explicit frame/unit transform whose source axis, target axis, handedness, scale and origin are declared and numerically verified. The upstream Resize API itself illustrates the better contract shape: choose exactly one dimension mode and optionally choose `origin_at` ([reference/source.md L798-L820](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/reference/source.md#L798-L820)).

Similarly, upstream `print/analyze` is only a geometric printability screen. Its own printing guide leaves wall thickness, overhangs, minimum detail and base stability to a manual check ([printing.md L236-L248](https://github.com/meshy-dev/meshy-3d-agent/blob/b9db44b5663e6e92d89828bf2e4fe1dc1b3f6610/skills/meshy-3d-printing/references/printing.md#L236-L248)). It cannot replace design-os `spec.json`, form/final production gates, physical fit or load evidence.

## Described vs enforced vs tested

| Topic | Described upstream | Enforced in code | Tested at pinned commit | Audit verdict |
|---|---|---|---|---|
| Async lifecycle | Task ID + poll/stream; terminal success/fail/cancel | Yes, poll recognizes terminal states | No runtime tests found | **Adopt concept** |
| Poll backoff | 5s→30s; 15s at 95% | Yes | No | **Adapt** with durable unknown state |
| Timeout resume | Same task ID can be polled again; task keeps running | Only via operator manually re-running CLI | No | **Adopt semantic**, enforce journal reconciliation |
| 429 retry x3 | Troubleshooting says automatic | No; runner exits immediately | No | **Defect — exclude behavior claim** |
| 5xx retry once | Troubleshooting says automatic | No; `raise_for_status()` | No | **Defect — exclude behavior claim** |
| Cancel/delete | Reference documents DELETE; poll recognizes CANCELED | No CLI cancel/delete and delete is not documented as cancel | No | **Do not infer cancellation** |
| Task/project history | `metadata.json` + global `history.json` | Yes after explicit `record` | No | **Adapt** to append-only pre-launch journal |
| Immutable attempt outputs | Not described | No | No | **Add locally** |
| Task lineage | Follow-up endpoints consume task IDs | Yes through recipe payloads | No | **Adopt** as explicit DAG deps |
| Single source/generated copies | Canonical reference/script sources | `build.py --check` implements byte checks | Not run by current CI | **Adopt + actually enforce** |
| Reference reachability/path bounds | Bounded skill docs | `validate_skills.py` | CI runs validator | **Adopt** |
| Coordinate conversion | Y-up→Z-up + target 75 mm | Yes, hardcoded local transform | No | **Exclude for production; replace with explicit transform contract** |
| Printability analysis | Geometry screen + separate manual concerns | Remote service only; not used here | No local tests | **Concept only; existing design-os gates remain authoritative** |

## Adopt / adapt / exclude matrix for design-os-3d-blender

| Pattern | Decision | Local interpretation |
|---|---|---|
| One canonical execution helper, recipes compose it | **Adopt** | `native_pipeline.runner` owns execution semantics; skills/workflows only route it. |
| Task IDs and chained lineage | **Adopt** | Pipeline step IDs + `depends_on`; attempts get immutable IDs and hashes. |
| Project-scoped outputs/history | **Adapt** | One run root, append-only journal, immutable `attempt-N/` outputs instead of mutable filenames. |
| Poll timeout = remote work may still run | **Adopt semantic** | Blender timeout/interruption becomes `unknown`; inspect state before retry. |
| Explicit terminal status | **Adopt** | Separate `running`, `executed`, `failed`, `unknown`; `executed` means only required numeric execution postconditions plus declared artifact hashes were recorded. |
| Retry prose outside runner | **Exclude** | Retry classes live in executable state machine and tests. |
| Blind replay after timeout | **Exclude** | Unknown attempts never auto-retry. |
| Canonical sources + generated mirrors | **Adopt** | Continue hash-bound catalog and skill-mirror checks; publication must actually run them. |
| Bounded reference graph | **Adopt** | Skill router links only scoped references; stale/unreachable sources fail checks. |
| API/vendor model generation | **Exclude** | Violates Native Asset Policy for production. |
| Fixed Y-up→Z-up and 75 mm normalization | **Exclude** | Use explicit units/axes/origin contracts and preserve spec dimensions. |
| Remote printability/repair | **Exclude as dependency** | Keep native production gate and physical-evidence boundaries. |

## Candidate local APIs derived from the audit

These are candidates for the native pipeline layer, not claims that Meshy has these exact APIs.

```python
# manifest.py
manifest = load_manifest(path, repo_root)
# normalized step:
# {id, script, depends_on, inputs, artifact_inputs, outputs,
#  required_postconditions, timeout_seconds}
normalized = validate_manifest(data, repo_root, max_steps=32)

# journal.py
attempt = begin_attempt(
    journal_path,
    pipeline_id=...,
    step_id=...,
    manifest_sha256=...,
    script={"path": ..., "sha256": ...},
    runtime_identity={...},
    input_sha256={...},
    output_base="steps/<step-id>",
    declared_outputs=[...],
    required_postconditions=[...],
)
# durable state exists before subprocess launch
finish_attempt(
    journal_path,
    attempt["attempt_id"],
    state="executed",
    result={"outputs": {...}, "postconditions": {...}, "scope": ...},
)

# runner.py
check_pipeline(manifest_path, repo_root=repo_root)
run_pipeline(manifest_path, run_dir=run_dir, repo_root=repo_root, resume=False)
status_pipeline(run_dir)
```

Required semantics:

1. A step is runnable only after declared dependencies are `executed`.
2. `begin_attempt()` is durable before `headless-run.sh` starts.
3. Process timeout, interruption, missing/ambiguous sentinel, or lost result after launch is `unknown`.
4. `AGENT_OK` alone is insufficient: `executed` additionally requires every declared numeric postcondition and every declared output artifact, whose bytes are hashed. This is still not semantic geometry/visual/manufacture verification.
5. `--resume` may reuse only an `executed` attempt whose manifest/script/runtime/input/output hashes still match. Runtime identity includes `headless-run.sh`, `agent-run-headless.py`, `agent_runtime.py`, `native-pipeline.py`, the four `native_pipeline` implementation modules, and the exact Blender executable bytes.
6. An `unknown`, `running`, or `failed` attempt is never silently replayed. Recovery uses a deliberately new run directory after inspection.
7. Every new attempt writes to a new output directory; outputs are not overwritten in place.
8. No pipeline state implies print readiness, manufacturing readiness, fit, load, thermal behavior or visual fidelity unless a task-specific gate explicitly establishes that predicate.

The final v1 manifest also binds artifact consumption textually. A downstream step names `artifact_inputs` as `<producer-step>:<producer-output>`; the producer must be listed in `depends_on` and must have declared that output. Project `inputs` are also the caller's source/helper dependency manifest: the runner deliberately does not pretend it can infer every transitive Python import.

Per-attempt environment exposed to payloads:

```text
DESIGN_OS_OUTPUT_DIR=/abs/run/steps/<step>/attempt-0001
DESIGN_OS_INPUTS_JSON={"project":{"path":"/abs/path"},"artifacts":{"build:model.blend":"/abs/path"}}
DESIGN_OS_PIPELINE_ID=<pipeline-id>
DESIGN_OS_STEP_ID=<step-id>
DESIGN_OS_ATTEMPT_ID=<step-id>-attempt-0001
DESIGN_OS_RUN_DIR=/abs/run
```

The runner additionally forces `HEADLESS_RAW=0` and `HEADLESS_KEEP_ADDONS=0` for each child. This prevents ambient shell configuration from bypassing the runtime wrapper or factory-startup isolation that the execution receipt hashes. Root-level `stdout.log` and `stderr.log` are reserved by the runner and cannot be declared as outputs.

## Discriminating tests worth implementing

- Start record is present after a launcher crashes before producing any sentinel.
- Timeout after subprocess launch produces `unknown`, and a subsequent ordinary `run` refuses blind replay.
- `--resume` refuses when a script, manifest or declared input hash changed.
- A printed/forged `AGENT_OK` that was not the authoritative runner sentinel cannot verify a step.
- Genuine `AGENT_OK` missing one required postcondition becomes `failed`, not `executed`.
- Genuine `AGENT_OK` with all postconditions but a missing declared artifact becomes `failed`.
- Output bytes are hashed after execution; a changed output cannot reuse an older `executed` receipt.
- Two attempts for the same step never share output paths.
- Duplicate step IDs, dependency cycles/topological violations, duplicate/aliased output names within one step and path escapes fail manifest validation before Blender starts. The same basename is valid across different step-owned directories.
- A downstream step never starts while any dependency is failed/unknown/running/unexecuted.
- Repeated `--resume` on `running`/`unknown`/`failed` launches zero replacement processes.
- A manifest changed to entirely new step IDs cannot evade an unresolved earlier attempt because all existing journal entries must match the current pipeline ID and exact manifest hash before any resume launch.
- A step that changes its script or any caller-declared project/artifact input while its child is running becomes `unknown` rather than receiving an `executed` receipt.
- Freshness/publication test changes a canonical source and proves mirror/catalog status becomes stale; it must be wired into the actual check command, not merely exist as an unused helper.

## Source paths inspected

Pinned blobs inspected with `git show`:

- `README.md`, `LICENSE`, `CHANGELOG.md`
- `.github/workflows/validate-skills.yml`
- `scripts/src/meshy_task.py`
- `scripts/build.py`
- `scripts/validate_skills.py`
- `reference/source.md`
- `skills/meshy-3d-generation/SKILL.md`
- `skills/meshy-3d-generation/references/pipelines.md`
- `skills/meshy-3d-generation/references/troubleshooting.md`
- `skills/meshy-3d-printing/SKILL.md`
- `skills/meshy-3d-printing/references/printing.md`
- `skills/meshy-3d-printing/scripts/fix_obj.py`
- `skills/meshy-openclaw/SKILL.md`

The full pinned tree was listed first. It contains no `tests/` directory or test-named paths; the GitHub workflow runs the structural skill validator only. No upstream executable was run during this audit.
