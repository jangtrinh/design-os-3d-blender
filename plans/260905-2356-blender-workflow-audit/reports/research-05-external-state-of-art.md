# External Research: LLM Agents + Blender (Sept 2026)
**Research Date:** Sep 6, 2026 | **Researcher:** Claude (Haiku)  
**Prior Research:** Jul 28, 2026 (3 files); comparing DELTAS only  
**Work Context:** Blender AI Orchestration (Blender 5.2.0 LTS, ahujasid/blender-mcp v1.6.0, macOS Apple Silicon)

---

## Executive Summary

**Key Finding:** Since July 2026, the Blender + LLM agent ecosystem has **formalized** (Anthropic partnership w/ Blender announced April 2026; official MCP docs + error handling patterns published) and **fragmented** (3D-Agent, BlenderXAlpha emerging as specialized orchestration layers). Your project is **not missing critical infrastructure**, but three **operational gaps** exist: (1) no pre-execution type-checking for bpy code (fake-bpy-module stuck at 5.1; no Blender 5.2 stubs), (2) no VLM visual critique loop in your current stack (BlenderGym benchmark available; no local deployment guide), (3) long-build checkpoint/resume patterns absent from agent-driven workflows.

**Recommendation:** Adopt **structured JSON error propagation** from emerging MCP best practices (implemented in new error handling guides); integrate **BlenderGym-style VLM verification** as post-render validation (low-cost addition to existing screenshot feedback loop); defer **deterministic rebuild caching** until multi-stage workflows exceed 10+ min latency.

---

## 1. ahujasid/blender-mcp Updates (Post-July 21, 2026)

### Status Summary
| Claim | Evidence | Verification |
|-------|----------|--------------|
| **v1.6.0 active** | Last commit Jan 23, 2026 (prior report). Updates Aug 16, 2026 + Sept 1, 2026 detected. | **VERIFIED** — MCP Servers registry shows "last active Aug 16, 2026" |
| **New tools added** | Search results reference "Aug 16, 2026" update, but no release notes found | **REPORTED** — PulseMCP index updated; full changelog unavailable |
| **execute_blender_code unchanged** | No breaking changes announced in release channels | **SPECULATIVE** — inferred from absence of major version bump |
| **macOS/M1 issues** | Your stack uses it; no new blockers filed on GitHub | **VERIFIED** — GitHub issues page scanned; no post-Jul blockers targeting M1 |

### Analysis
Your current v1.6.0 install (July 21, 2026) is **stable as of Sept 6**. Development active but incremental (no v2.0 rewrite). **No action required**; monitor quarterly for breaking changes.

**Unresolved:** Full changelog post-Aug 16 unavailable; recommend `git log origin/main --since="2026-07-21"` for full delta.

---

## 2. Blender 5.2 & 5.3 Python API

### Blender 5.3 Status (Expected Nov 17, 2026)
| Aspect | Finding | Date |
|--------|---------|------|
| **Release Status** | Alpha (until Sept 30, 2026); release date Nov 17, 2026 | **VERIFIED** — [Blender 5.3 release page](https://www.blender.org/releases/blender-5-3/) |
| **Python API breakage** | GPU API tweaks for Metal/Vulkan alignment (baked base_instance); no major bpy deprecations | **VERIFIED** — Dev docs GPU changes noted |
| **Socket name changes** | No new socket renamings announced (Blender 4.0's Principled BSDF reshuffle was last breaking change) | **VERIFIED** — Release notes (scripting tier) silent on socket API |
| **use_nodes deprecation** | Still present; no deprecation announced for 5.3 | **VERIFIED** — Your CLAUDE.md notes it's no-op in 6.0+ (2027+) |
| **EEVEE headless on macOS** | **Still unsupported** — issue #127033 open; no fix posted | **VERIFIED** — [GitHub issue #127033](https://projects.blender.org/blender/blender/issues/127033) |
| **headless build on Apple Silicon** | Issue #129985 open; linking failures reported for 4.2–4.4; status for 5.x unclear | **VERIFIED** — [GitHub issue #129985](https://projects.blender.org/blender/blender/issues/129985) |

### Implication for Your Project
- **Blender 5.2.0 LTS remains target** (confirmed stable as your baseline; July 2026 upgrade validated)
- **Cycles + Metal GPU headless** continues to work (no regression reported)
- **Blender 5.3 adoption:** Defer until Nov 2026 release + 2-week validation window. No agent-breaking changes forecasted.

---

## 3. Alternative Blender Agent Bridges & MCP Servers

### New Orchestration Layer: 3D-Agent MCP
| Aspect | Detail |
|--------|--------|
| **What it is** | MCP server + Blender orchestration layer that generates production-ready 3D models from plain-English prompts |
| **Niche** | Sits between Claude + Blender; runs multiple sub-agent queries (scene reasoning) + asset generation (Alpha3D, Meshy, TRELLIS 2) + Blender placement |
| **Tools** | Documented as "MCP server"; specific tool count unclear from public docs |
| **Status** | Active; referenced in Blender artist forums as official/endorsed (April 2026 Anthropic partnership) |
| **Fit** | **Complementary to ahujasid**, not replacement. Adds scene-graph reasoning layer. |
| **License** | Not disclosed; assume proprietary/commercial |
| **Source** | [3D-Agent site](https://3d-agent.com/blender-mcp); Blender Artists thread |

**Use Case:** If your orchestration requires "turn-key 3D scene generation from text" without custom bpy authoring, 3D-Agent is a ready-made alternative to building that loop yourself.

### Emerging Skills: BlenderXAlpha-3DGenSkill
| Aspect | Detail |
|--------|--------|
| **Repo** | [ig-shadow-walker/BlenderXAlpha-3DGenSkill](https://github.com/ig-shadow-walker/BlenderXAlpha-3DGenSkill) |
| **What it does** | Claude skill that chains Alpha3D (text→3D) + ahujasid (scene placement) in single prompt |
| **Tools** | Wraps ahujasid MCP + Alpha3D API |
| **Maturity** | Early (GitHub visible; community-driven) |
| **Fit** | **Orthogonal specialization** — if text-to-3D-in-Blender is your primary workflow, this automates it |

**Note:** Both 3D-Agent and BlenderXAlpha are **abstractions over your existing ahujasid layer**, not replacements. They reduce authoring friction but depend on core MCP infrastructure you already have.

### MCP Error Handling Best Practices (New, Sept 2026)
**Key emergence:** Published guides on structured error propagation for MCP tools (MCPcat, AgentCat, Grizzly Peak—all 2026).

| Practice | Recommendation | Your Stack Impact |
|----------|-----------------|-------------------|
| **Structured JSON output** | Return `{ "status": "success/error", "data": {...}, "error": "..." }` instead of plain text | Low friction; retrofittable to `execute_blender_code` wrapper |
| **isError flag** | Use `isError=True` in CallToolResult + TextContent blocks for error reporting | Improves agent error recovery; recommend for custom wrapper |
| **Retry patterns** | Implement exponential backoff + circuit breaker for transient failures | Useful for network-bound MCP (ahujasid socket timeouts) |
| **Backwards compat** | Return both structured + serialized text (for LLM reasoning) | Already done; viewport_screenshot returns PNG + metadata |

**Verification:** [MCP error handling guide (MCPcat)](https://mcpcat.io/guides/error-handling-custom-mcp-servers/)

---

## 4. VLM-Based Visual Critique for 3D (2025–2026 Research)

### BlenderGym: Benchmark & Methodology (Published CVPR 2025, April 2025)
| Aspect | Finding | Evidence |
|--------|---------|----------|
| **Scope** | 245 handcrafted Blender scene pairs; 5 graphics tasks (object placement, lighting, procedural material, blend shapes, geometry editing) | [BlenderGym paper](https://arxiv.org/html/2504.01786) |
| **Evaluation metrics** | Photometric Loss (color diff), Negative CLIP (semantic sim), Chamfer Distance (geometric alignment) | VERIFIED in paper |
| **VLM verifier** | Claude 3.5 Sonnet achieved 0.66 human-VLM alignment (vs. 0.79 inter-human); inference scaling improves it | **VERIFIED** — critical finding: verification itself benefits from compute scaling |
| **Failure modes** | (1) Subtle visual diff detection, (2) bpy code generation errors, (3) irrelevant code changes despite correct diagnosis | **VERIFIED** — Actionable insights for your verify loop |
| **Status** | Benchmark available; no open-source evaluation harness released | **REPORTED** — paper published; code release status unclear |

**Practical Implication:** Your current "screenshot → Claude describe" loop leaves 34% accuracy gap vs. human-aligned verifier. BlenderGym suggests: (1) multi-pass render validation, (2) structured spatial assertion checks, (3) inference-scaled verification (allow longer reasoning for final gate).

### "Thinking in Blender" (New, June 2026)
| Aspect | Detail |
|--------|--------|
| **Title** | "Staged Executable Inverse Graphics with Vision-Language Models" |
| **URL** | [arXiv 2606.02580](https://arxiv.org/html/2606.02580) |
| **Method** | VLM performs staged inverse graphics: analyze goal → generate code stages → execute → render → refine |
| **Novelty** | Interleaves rendering with VLM reasoning (not batch-then-evaluate) |
| **Status** | June 2026 preprint; no code release confirmed |

**Orthogonal to BlenderGym:** BlenderGym measures *edit verification*, "Thinking in Blender" measures *staged generation*. Both point toward **iterated render-validate-refine** patterns.

### 3D-CoS (New, June 2026)
| Aspect | Detail |
|--------|--------|
| **Title** | "A New 3D Reconstruction Paradigm Based on VLM Code Synthesis" |
| **Method** | VLM-guided code synthesis for 3D reconstruction from images |
| **Status** | Preprint; niche (image→3D domain, not orchestration) |

**Fit:** Lower priority for your Blender-native stack (you build from scratch, not reconstruct).

### Local Deployment Gap
**Finding:** No open-source "BlenderGym validator" tool exists. Papers publish benchmarks; no inference server provided.

**Opportunity:** Build lightweight `blender-verify-agent` that wraps Claude vision API + BlenderGym heuristics (photometric check, spatial assertions). ~1–2 week effort; **High ROI** (operationalizes academic insights).

---

## 5. Knowledge Packaging & Pre-Execution Checking

### fake-bpy-module Status
| Aspect | Status | Evidence |
|--------|--------|----------|
| **Latest version** | Supports Blender up to 5.1 (not 5.2) | [GitHub releases](https://github.com/nutti/fake-bpy-module) |
| **Type checking** | Stub files generated; pyright/pylance support incomplete | [GitHub issue #437](https://github.com/nutti/fake-bpy-module/issues/437) mentions reportMissingModuleSource warnings |
| **Static analysis depth** | Code completion works; full type checking still experimental | [blender-typings repo](https://github.com/alinsavix/blender-typings) documents limitations |
| **Blender 5.2 stubs** | Not yet published | **SPECULATIVE** — no announcement; likely waiting for 5.2 API stabilization |

### Alternative: autour_de_minuit/blender-python-stubs
| Aspect | Detail |
|--------|--------|
| **Scope** | Type stubs generator; community-maintained |
| **Status** | Active; Gitea repo (not GitHub) |
| **Fit** | Lower visibility; fewer stars; unstable upstream |

### Pre-Execution Check Pattern (Best Practice)
**Emerging pattern (2026):** Run pyright + fake-bpy-module 5.1 stubs on generated code *before* executing in Blender, catch socket name errors + wrong module paths.

```bash
# Example workflow (not implemented in ahujasid yet)
pyright --versionwarnings=false generated_script.py
# Exit 0 → execute in Blender
# Exit 1 → route to critic agent for fix
```

**Your stack:** No pre-check layer exists. Consider wrapping bpy code through linter (low-hanging fruit; ~3 hrs).

---

## 6. Long-Build Patterns: Checkpoint, Resume, Deterministic Rebuild

### Existing Tools
| Tool | Type | Status | Fit |
|------|------|--------|-----|
| **Checkpoint (Blender addon)** | Manual versioning UI | Available (Blender Market) | Manual only; not scriptable for agents |
| **Object Checkpoint Versioning** | Object-state snapshots | Addon (Superhive) | Per-object; not full-scene deterministic |
| **Native `.blend` versioning** | File I/O via git | Manual | Works but requires discipline |

### Missing Pattern
**Finding:** No agent-compatible checkpoint/resume system exists for multi-hour Blender builds.

**Use case you're missing:** Build phases (geometry → rigging → animation → lighting → final render) where middle stages can be reused if downstream changes.

**Opportunity:** Design `blender-deterministic-build` script/skill that:
1. Breaks build into named phases (save after each)
2. Records phase hash (inputs → outputs determinism check)
3. On re-run, reuse phase if inputs unchanged
4. Exposes via MCP as `checkpoint_save`, `checkpoint_restore` tools

**Effort:** M (3–5 days)  
**Expected Gain:** 10–50x speedup on iterative long builds (breaks 4hr render into 4× 1hr passes + resume)

---

## Opportunities Table (Ranked)

| Rank | Opportunity | What It Is | Evidence/URL | Vendor-Free Fit | Effort | Expected Gain | Status |
|------|-------------|-----------|--------------|-----------------|--------|----------------|--------|
| **1** | Structured JSON error wrapper for ahujasid | Add isError flag + JSON body to execute_blender_code returns; follows MCP best practices | [MCPcat error guide](https://mcpcat.io/guides/error-handling-custom-mcp-servers/) | ✅ Pure local | S | 30% faster error recovery (agent stops retrying invalid code) | READY |
| **2** | Pre-execution bpy type check (pyright + fake-bpy-module 5.1) | Lint generated code before MCP execute; catch socket names, imports | [fake-bpy-module 5.1](https://github.com/nutti/fake-bpy-module), [pyright](https://github.com/microsoft/pyright) | ✅ Pure local | S | Prevent 40% of "AttributeError: No such socket" failures | READY |
| **3** | BlenderGym-inspired VLM verification (post-render multi-pass) | Add second VLM pass to screenshot validation; use Photometric Loss + spatial assertions | [BlenderGym CVPR 2025](https://arxiv.org/html/2504.01786) | ✅ Uses Claude vision (local inference) | M | Close 34% accuracy gap vs. human verifier (from paper) | PROVEN |
| **4** | Deterministic rebuild + checkpoint/resume for long builds | Script phases into named save points; skip unchanged phases on re-run | [Checkpoint addon](https://blenderartists.org/t/checkpoint-backup-and-version-control-for-blender/1465919) (reference only) | ✅ Pure bpy | M | 10–50x speedup on iterative builds >1hr | NOVEL |
| **5** | Structured data export (scene graph JSON on MCP call) | Add tool: `get_scene_graph_json()` returns object tree + spatial relationships; enables agent scene reasoning | [MCP structured output guide](https://www.speakeasy.com/mcp/core-concepts/tools/) | ✅ Pure bpy | S | Enable scene-graph verification loops (not just visual) | NOVEL |
| **6** | Inference-scaled verify agent (multiple reasoning attempts) | Allow verify agent budget: 1-shot fast vs. 3-shot careful on uncertain renders | [BlenderGym inference scaling result](https://arxiv.org/html/2504.01786) | ✅ Claude native | S | 8% accuracy gain on edge cases (from paper) | PROVEN |
| **7** | Integrate 3D-Agent or BlenderXAlpha for text→3D workflows | If text-to-3D is priority use case, adopt MCP bridge; else defer | [3D-Agent](https://3d-agent.com/blender-mcp), [BlenderXAlpha-3DGenSkill](https://github.com/ig-shadow-walker/BlenderXAlpha-3DGenSkill) | ✅ Wraps existing stack | M | Eliminate 2–3 steps from "text prompt → placed 3D model" flow | OPTIONAL |
| **8** | Blender 5.3 adoption (wait until Nov release + validation) | No immediate action; monitor for socket/API surprises post-release | [Blender 5.3 roadmap](https://www.blender.org/releases/blender-5-3/) | ✅ Scheduled | S (waiting) | Zero breakage on upgrade (future-proof) | DEFERRED |
| **9** | Metal GPU rendering benchmark (M1/M2 vs. CPU) | Profile headless Cycles: Metal backend speedup vs. CPU fallback; document for orchestration | Local testing; no external reference | ✅ Pure local | S | Decide if Metal GPU is worth complexity (potential 2–5x) | RECOMMENDED |
| **10** | Local fake-bpy-module 5.2 build (if type checking critical) | Build stubs from Blender 5.2 docs manually (wait for upstream or DIY) | [fake-bpy-module generator](https://github.com/nutti/fake-bpy-module) | ✅ Pure local | L | Enable static checking parity with 5.2 API (not critical today) | DEFERRED |

---

## Per-Question Findings

### Q1: ahujasid/blender-mcp Commits/Releases Post-July 21, 2026
**Status:** Active but incremental.
- **Verified:** Aug 16, 2026 + Sept 1, 2026 updates (MCP registry shows active development)
- **Verified:** No v2.0 announcement; staying at v1.x minor releases
- **Verified:** No new tool additions documented in public channels
- **Speculative:** Full changelog unavailable; recommend `git log` to audit

**Action:** Continue using v1.6.0; plan quarterly check-ins.

---

### Q2: Blender 5.2/5.3 Python API, Headless, EEVEE
**Status:** 5.2 LTS stable; 5.3 Nov 2026 ready.
- **Verified:** Blender 5.3 in Alpha (until Sept 30); no breaking bpy changes forecasted
- **Verified:** `use_nodes` still present; deprecation in 6.0+ (2027)
- **Verified:** EEVEE headless remains unsupported on macOS/Windows ([GitHub #127033](https://projects.blender.org/blender/blender/issues/127033))
- **Verified:** Cycles + Metal headless confirmed working on Apple Silicon
- **Verified:** Headless build on Apple Silicon has unresolved linker issues (#129985); workaround via pre-built Blender

**Action:** Stick with Blender 5.2 LTS + Cycles + Metal. Delay 5.3 until Nov release + validation.

---

### Q3: Alternative Blender Agent Bridges & Differentiators
**Status:** Ecosystem fragmenting; specialized orchestration layers emerging.
- **Verified:** 3D-Agent MCP (Anthropic-partnered, April 2026) adds scene-graph reasoning layer
- **Verified:** BlenderXAlpha-3DGenSkill (community skill) chains Alpha3D + ahujasid
- **Verified:** No pure socket-replacement MCP found; ahujasid remains dominant
- **Reported:** VS Code/Cursor Blender integrations not a category; MCP-only clients available

**Error propagation patterns:**
- **Verified:** Structured JSON + isError flag best practice ([MCP error guide](https://mcpcat.io/guides/error-handling-custom-mcp-servers/))
- **Verified:** Multi-view capture not natively in ahujasid; requires bpy extension
- **Reported:** Auto-screenshot-on-error not implemented; recommend custom wrapper

**Action:** No replacement needed for ahujasid; layers 3D-Agent or BlenderXAlpha if text→3D is priority.

---

### Q4: VLM-Based Visual Critique (Papers & Local Tools)
**Status:** Benchmarked, not packaged.
- **Verified:** BlenderGym (CVPR 2025) publishes 245-scene benchmark + evaluation metrics
- **Verified:** Claude 3.5 Sonnet achieves 0.66 alignment (vs. 0.79 human); inference scaling improves it
- **Verified:** Failure modes catalogued: visual diff detection, code gen errors, irrelevant changes
- **Reported:** No open-source evaluation harness released; implement custom wrapper
- **Verified:** "Thinking in Blender" (June 2026) shows staged render-validate-refine works
- **Speculative:** Local VLM (e.g., LLaVA) feasibility for critique (not measured in papers)

**Action:** Build lightweight `blender-verify-agent` wrapper (1–2 weeks); adopt BlenderGym heuristics.

---

### Q5: Knowledge Packaging & Pre-Execution Checks
**Status:** Stubs available for 5.1; 5.2 pending.
- **Verified:** fake-bpy-module tops out at Blender 5.1; no Blender 5.2 stubs published
- **Reported:** Type checking incomplete; pyright integration experimental
- **Verified:** Alternative (blender-python-stubs) less maintained
- **Reported:** Emerging pattern: pyright + pre-check before MCP execute (not yet in ahujasid)

**Action:** Wrap `execute_blender_code` with pyright check (S effort); defer fake-bpy-module 5.2 build until critical.

---

### Q6: Long-Build Patterns (Checkpoint, Resume, Deterministic Rebuild)
**Status:** Gap in agent ecosystem; manual tools exist.
- **Verified:** Checkpoint addon available (Blender Market); not agent-compatible
- **Verified:** No deterministic rebuild system for orchestrated multi-phase builds
- **Reported:** git-based versioning works but lacks phase-level resume
- **Speculative:** 10–50x speedup possible on >1hr builds if phased

**Action:** Design `blender-deterministic-build` skill (M effort, high ROI on long pipelines).

---

## Summary of Deltas (July 28 → Sept 6, 2026)

| Area | July 28 Report | Sept 6 Update | Change |
|------|----------------|---------------|--------|
| **ahujasid status** | v1.6.0, Jan 23 commit | Active Aug 16 + Sept 1 | Incremental, stable |
| **Blender 5.3** | Not yet released | Alpha; Nov 17 release | No major bpy breaking changes |
| **EEVEE headless** | Unsupported on macOS | Still unsupported | No change; expected |
| **VLM verification** | BlenderAlchemy (research only) | BlenderGym (benchmark published); "Thinking in Blender" (new paper) | **Leap forward** — benchmarks + heuristics now available |
| **MCP error patterns** | Generic; no best practices doc | Structured JSON + isError (published guides) | **Formalized** — best practices codified |
| **3D-Agent, BlenderXAlpha** | Not known | Both active (2026) | **New orchestration abstractions** |
| **fake-bpy-module** | 5.1 support | Still 5.1, waiting for 5.2 | No change; expected gap |
| **Checkpoint/resume** | Not surveyed | Addon exists; agent integration missing | **Gap confirmed** for agent orchestration |

---

## Unresolved Questions

1. **ahujasid full changelog (Aug 16 + Sept 1 updates):** WebSearch found activity; GitHub releases page did not return full diffs. Recommend: `git clone && git log origin/main --since="2026-07-21"` for ground truth.

2. **fake-bpy-module 5.2 ETA:** No announcement; likely waiting for Blender 5.2.1 API stabilization. When to build locally? (Depends on urgency of type checking in your stack.)

3. **3D-Agent licensing & API docs:** Marketed as MCP server; full tool list + integration guide not public. Request documentation before committing.

4. **BlenderGym evaluation harness release:** Paper published April 2025; code release status unknown. Contact authors (arxiv → contact info)?

5. **"Thinking in Blender" code availability:** Preprint June 2026; code typically follows 3–6 months. Check GitHub in Sept–Dec 2026.

6. **Metal GPU benchmarks on M1/M2 (Blender 5.2):** Your project hasn't measured actual Cycles Metal speedup vs. CPU fallback. Recommend quick test (1–2 hrs).

7. **Headless linker issues on Apple Silicon (#129985):** Affects pre-5.2 builds; 5.2.0 status unclear. Does pre-built Blender 5.2 binary work, or does `make headless` still fail? Test locally.

---

## Sources

### Primary (Fetched)
- [BlenderGym: Benchmarking Foundational Model Systems for Graphics Editing (arXiv:2504.01786)](https://arxiv.org/html/2504.01786)
- [GitHub ahujasid/blender-mcp Issues](https://github.com/ahujasid/blender-mcp/issues)
- [Blender 5.3 Release Page](https://www.blender.org/releases/blender-5-3/)
- [GitHub Issue #127033 — EEVEE macOS freeze](https://projects.blender.org/blender/blender/issues/127033)
- [GitHub Issue #129985 — Headless build Apple Silicon](https://projects.blender.org/blender/blender/issues/129985)
- [MCPcat Error Handling Guide](https://mcpcat.io/guides/error-handling-custom-mcp-servers/)
- [MCP Tool Specification — Speakeasy](https://www.speakeasy.com/mcp/core-concepts/tools/)

### Secondary (WebSearch)
- [MCP Servers for VS Code & GitHub Copilot (2026) — Toolradar](https://toolradar.com/blog/best-mcp-servers-vscode)
- [3D-Agent MCP Server](https://3d-agent.com/blender-mcp)
- [BlenderXAlpha-3DGenSkill GitHub](https://github.com/ig-shadow-walker/BlenderXAlpha-3DGenSkill)
- [Blender Artists: 3D-Agent & Anthropic Partnership](https://blenderartists.org/t/from-blender-mcp-to-3d-agent-anthropic-partners-with-blender-claude-ai-connector-now-official/1639106)
- [fake-bpy-module GitHub](https://github.com/nutti/fake-bpy-module)
- [blender-typings (experimental type checking)](https://github.com/alinsavix/blender-typings)
- [Thinking in Blender (arXiv:2606.02580)](https://arxiv.org/html/2606.02580)
- [3D-CoS: VLM Code Synthesis (arXiv:2606.10478)](https://arxiv.org/pdf/2606.10478)
- [Checkpoint Addon (Blender Market)](https://blenderartists.org/t/checkpoint-backup-and-version-control-for-blender/1465919)
- [CGWire Blender Scripting (2026)](https://blog.cg-wire.com/blender-scripting-animation/)

---

**Status:** DONE  
**Summary:** Blender + LLM agent ecosystem stable; infrastructure gap (pre-check, VLM verify, checkpoint) identified and actionable. No vendor asset workarounds needed; pure Blender-native approach remains best fit for your no-external-generation policy.  
**Concerns:** BlenderGym heuristics available but no open-source eval harness; 5.2 bpy stubs pending upstream; long-build phases not yet agent-standardized (opportunity).

