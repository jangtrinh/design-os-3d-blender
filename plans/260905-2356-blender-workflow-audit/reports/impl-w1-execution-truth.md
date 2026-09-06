# W1 — execution truth: implementation report

Worker A. 2026-09-06. Blender 5.2.0 LTS (`fbe6228777e7`), host python 3.14.6, Blender python 3.13.
Live GUI (PID 14172, port 9876) never contacted — ownership re-checked after every risky probe, still 14172.

## Verdict

Sentinel contract implemented and enforced end-to-end. All four audited headless defects and all four
audited socket-client defects are fixed and covered by tests. **43 tests, OK, 11.6 s** (36 mine + 7 from
worker B's `test_verify_lib.py`, which discovers in the same dir).

Hand-run acceptance (plan.md §Acceptance 1), FACT, verbatim exit codes:

```
raising script       -> exit 3   (AGENT_FAIL, traceback names payload-raises.py:17)
clean emit_ok        -> exit 0   (AGENT_OK, postconditions dim_x=2.0)
handled op error     -> exit 0   (false-red case)
missing script       -> exit 2   (message on stderr, stdout empty)
forged-sentinel liar -> exit 3
failed requirement   -> exit 1   (AssertionError, not 3)
```

## What changed

**`scripts/agent_runtime.py` (new, 200 lines).** Frozen interface as specified: `run_file(path, argv=None)`,
`emit_ok(step, **post)`, `emit_fail(step, exc, **post)`, `load_lib(path)`, `is_background()`. Added
`exit_code_for(exc)` and `parse_sentinel(text)` so shell/socket/tests share one "last line wins" rule.

- Sentinel = one line, `sort_keys`, `ensure_ascii` → a multi-line traceback stays on one line (FACT, tested).
- Payload compiled with its real filename → traceback names payload file + line + source text (FACT, shown below).
- **Exit-code mechanism (measured, not recalled).** `sys.exit(N)` from a `--python` payload sets the process
  exit code to N *with or without* `--python-exit-code` (FACT: exit0→0, exit3→3, both flag states). And
  `--python-exit-code 3` does **not** clobber an explicit `sys.exit(0)` (FACT). So `run_file` owns the exit
  code by calling `sys.exit(code)` in background; the flag is only the backstop for an error that escapes
  the runtime itself (syntax error, import failure) — that path exits 3 instead of the old 0 (FACT).
- `is_background()` False under GUI ⇒ `run_file` returns a dict instead of killing Blender. Verified by
  simulating the addon's own call shape: `exec(code, {"bpy": bpy})` + `redirect_stdout`, `is_background`
  forced False → process survived, exactly 1 sentinel, traceback contained the payload filename (FACT).
- `load_lib` keys `sys.modules` by sha256 + abspath; same content → same module object, changed content →
  re-executed, stale attributes gone (FACT, tested both in host python and inside headless Blender).
  Handles hyphenated names (`agent-verify-lib.py`) that `import` cannot.

**`scripts/headless-run.sh` (rewritten, 104 lines).** `--factory-startup --disable-autoexec -b
--python-exit-code 3 --python <script>`; `--` args forwarded; `--blend <f>` plus the legacy trailing
`.blend` positional (both verified loading a scratch blend); `BLENDER_BIN`; `HEADLESS_KEEP_ADDONS=1`;
`--help`. Missing/unreadable script, missing blend, non-executable Blender → exit 2 on stderr.
Exit derived from the last sentinel; no sentinel → Blender's exit **plus a stderr warning** that it is
unreliable (legacy payloads still run). Hermeticity FACT: default run logs 0 "addon registered" lines;
`HEADLESS_KEEP_ADDONS=1` logs it and the addon self-refuses in background — port 9876 unchanged after.

**`scripts/blender-socket-client.py` (rewritten, 177 lines).** Wire contract read from the addon source
(`~/Library/.../addons/blender_mcp.py:195-240, 320-340, 525-545`), not assumed: one JSON object back, no
length prefix, no delimiter, connection stays open. So: loop until the buffer parses; EOF → clear message
exit 3 (no `UnboundLocalError`); timeout → exit 3 naming the byte count; `{"status":"error"}` → exit 1 with
the message; full JSON printed, no `[:4000]`; `--out <file>`; `--host/--port/--timeout` with the old
defaults. `--file` wraps the payload through `agent_runtime` (`sys.modules.pop('agent_runtime')` first, so
a stale runtime in the GUI process can't be reused), then decides by the sentinel in the captured stdout:
AGENT_FAIL AssertionError → 1, other → 3.

**Tests (`tests/execution/`, unittest, stdlib only).** `test_headless_run.py` (12), `test_agent_runtime.py`
(13), `test_socket_client.py` (13), `fixtures/` 9 payloads + `fake_addon_socket_server.py`.
Socket tests bind `127.0.0.1:0` and assert `port != 9876` before listening.

## Attacks run against my own work

| Attack | Result |
|---|---|
| audit-03's 3-line liar (print magic string, then raise) | **FAIL as required** — run_file emits the real AGENT_FAIL after; exit 3 |
| forged `AGENT_OK` printed mid-run, real failure after | **FAIL** — only the last sentinel counts |
| payload calls `emit_fail` then returns normally (no raise) | **found a hole in my first draft; fixed** — run_file now honours the payload's own FAIL verdict (exit 1/3) instead of overwriting it green |
| payload emits FAIL then prints a forged `AGENT_OK` as the literal last line | **found a second hole; fixed** — shell cross-checks: AGENT_OK + nonzero Blender exit ⇒ refuse success, exit nonzero |
| my own first draft emitted **two** sentinels on every failure | fixed — `_finish()` raises SystemExit, so it was being caught by the outer `except SystemExit` and re-reported as a `SystemExit("3")` failure. Restructured; asserted "exactly 1 sentinel" in tests |

Example traceback delivered through the sentinel (FACT, verbatim):

```
File ".../scripts/agent_runtime.py", line 146, in run_file
    exec(compile(source, abspath, "exec"), namespace)
File ".../tests/execution/fixtures/payload-raises.py", line 17, in main
    raise RuntimeError("intentional failure from payload-raises")
RuntimeError: intentional failure from payload-raises
```

## Rerun commands

```bash
cd /Users/jang/Products/Blender
python3 -m unittest discover -s tests/execution -v          # 43 tests, ~11.6 s
bash scripts/headless-run.sh tests/execution/fixtures/payload-raises.py                  ; echo $?  # 3
bash scripts/headless-run.sh tests/execution/fixtures/payload-emit-ok.py                 ; echo $?  # 0
bash scripts/headless-run.sh tests/execution/fixtures/payload-handled-operator-error.py  ; echo $?  # 0
bash scripts/headless-run.sh /tmp/nope.py                                                ; echo $?  # 2
```

Payload idiom used by every fixture (works under `--python` and under `run_file`, no recursion):

```python
if __name__ == "__main__":
    if "agent_runtime" in sys.modules:
        main()
    else:
        import agent_runtime as rt
        rt.run_file(__file__)          # add sys.argv[index("--")+1:] to forward args
```

## NOT verified

- **The socket client against the real addon.** Fake server only, per the hard rule. The addon's actual
  chunking/partial-write behaviour on a large reply is INFERENCE from its source (single `sendall`).
- **GUI (non-background) behaviour of `run_file`.** Proven by simulating the addon's namespace + stdout
  capture in a headless process with `is_background` forced False, not by a real MCP call.
- **The audit's false-red exit-1 case did not reproduce on 5.2.0.** I tried 7 operator failures
  (`open_mainfile`, `save_as_mainfile`, `mode_set`, `render`, `export_scene.gltf`, `wm.link`, `image.open`)
  under `--python` with and without `--python-exit-code`: all exit 0. The audit's exit-1 probably came from
  the old non-hermetic invocation (user add-ons loaded). Moot either way — `run_file` sets the exit code
  explicitly, which is proven to override; the "handled operator error → 0" test locks that in.
- **Windows/Linux paths** — macOS only; `mktemp -t` and the default Blender path are macOS-shaped
  (`BLENDER_BIN` covers the binary).
- MCP-path residual: a payload that emits FAIL and then prints a forged AGENT_OK **after** `run_file`
  returns would read green over MCP (no exit code to cross-check there, unlike the shell). Out of contract
  — nothing may print after `run_file` — but not blocked mechanically.
- I did not touch `agent-verify-lib.py`, knowledge/, skills, docs, or builds/. `tests/execution/test_verify_lib.py`
  and `fixtures/verify-lib/` are worker B's; I only observed them passing in the same discovery run.

## Unresolved questions

1. `parse_sentinel` and `exit_code_for` are public in `agent_runtime` but not in plan.md §Frozen interfaces.
   W3's `production-gate.py` and W5's boilerplate runner both need exactly this parsing — should the plan
   record them as part of the frozen surface so the three implementations do not drift?
2. Exit code 2 ("invalid/incomplete input") is reachable from a payload only via `sys.exit(2)` or an
   `OSError` subclass. W3's gate needs 2 for an incomplete spec. Should `agent_runtime` export a named
   `ContractError` for that, or does W3 own its own exit path?
3. Legacy payloads without a sentinel currently run and warn. Should `headless-run.sh` eventually hard-fail
   them (exit 2) once the boilerplates are migrated, and if so who migrates the 30 modules — W5?
4. `HEADLESS_KEEP_ADDONS=1` loads the MCP addon; today only the addon's own background guard prevents a
   port-9876 collision. Should the wrapper also refuse when the GUI holds 9876, or is add-on-owned safety
   acceptable for a rarely-used escape hatch?
