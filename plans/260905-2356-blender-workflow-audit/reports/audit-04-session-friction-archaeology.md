---
title: Session friction archaeology — Blender AI orchestration
date: 2026-09-06
scope: read-only audit of plans/, builds/, .brv/ records for 260728 (drone/img2threejs) and 260905 (robot arm) sessions
method: journals + retros + evidence JSON + build READMEs/reports + render logs + on-disk frame counts
---

# Audit 04 — Session friction archaeology

## Verdict

The dominant cost in this project is **not** bpy syntax, MCP flakiness, or missing skills. It is a
**verification-shape problem**: gates were written for the artifact's *final state* (transforms, mesh
closure, endpoint framing, decode exit code) while the owner and physics judge the artifact's
*process* (staging paths, camera rhythm, proportions vs reference, held load). Every expensive event
in the record is one of two shapes:

1. **False green** — a numeric PASS whose predicate was narrower than acceptance (275/275 endpoints
   framed, then rejected; decode exit 0, then fingertip clipped; 4 boilerplate self-tests exit 0,
   then 10 defects reproduced).
2. **Commit-before-contract** — geometry detailed or thousands of frames rendered before the spec,
   payload, or staging that governs them was locked.

Measured consequence: **≈8,400 rendered/processed frames discarded or superseded** (≈6,700 if the 1,780 caption frames turn out to be post-processed rather than rendered — see Unresolved Q1) and one full video never
delivered, out of ~163 minutes of render process time across the arm builds. FACT (frame counts on
disk + render logs); the minutes are elapsed-to-last-save, not GPU time.

Second-order finding the retros do not state: **the first retro (19:46–20:59) already concluded
"animatic/preview before full render" — and within 90 minutes the session committed two more
render-then-reject incidents (A4 22:27, A5 23:00).** Journal 04 names the reason: *"Quy tắc viết
trong Markdown không tự enforce"* (L4649). Any redesign that outputs only Markdown rules repeats this.

---

## Failure patterns (ranked)

Recurrence = distinct occurrences with a citable artifact. "Sessions" = 260905-arm (S1),
260728-drone/img2threejs (S2), 260905-knowledge-orchestration (S3).

| # | Pattern | Occurrences | Sessions | Evidence (strongest) | Recorded cost |
|---|---|---:|---|---|---|
| 1 | **Authored motion/camera verified at endpoints only** → interpenetration or bad path found by owner or late sweep | 7 | S1 | overlap-diagnosis.md: shoulder f588 / elbow f1198 waiting fork through cassette; first repair `e9323` swept through **real servo case** f563–572 / f1211–1217 | 1,835 partial frames discarded; 1 rejected repair revision; owner had to spot 00:24 |
| 2 | **False green — PASS predicate narrower than acceptance** | 6 | S1,S3 | journal 05: "22:15 numeric/reviewer xác nhận 275/275 endpoints framed. Nhưng 22:27 owner yêu cầu dừng"; L417 `NameError: name 'framing' is not defined` **inside** "Code executed successfully"; retro2 §54: "4 exact-copy self-tests…exit 0; 12 diagnostics gồm 10 giới hạn/lỗi" | A4 video killed (~25.7 min render, 3,074 frames); hero re-render 89 frames |
| 3 | **Measurements/spec not locked before detailing → proportions wrong → rebuild** | 5 | S1,S2 | journal 01: "Ảnh kích thước lúc 15:51 thay giả định 90/90 bằng 119/111/137/166 mm"; 260728-1519: "dimensions were guessed in code and tests checked framing/presence rather than projected reference correspondence"; fable audit: hero IoU 0.246 after 3 manual passes | Full Arm rebuild (L2273); V2 built as a second model; drone native build retired entirely |
| 4 | **Long render started before story/staging gate** | 5 | S1 | A4 `video/frames`=1743 + drafts 780+551, never delivered; A5 `rejected-522afd-partial-frames`=1835; `empty-target-draft-animatic`=1128; flexibility 589 rendered / 240 encoded (performance.md:19) | ≈8,400 frames discarded/superseded; ~26 min on the killed A4 alone |
| 5 | **Geometry / export assertion failures during build** | 12 | S1 | session-evidence.json: L657/L980/L999 nonmanifold masters, L775/L783 degenerate faces **in the exported STL** (mesh looked fine in Blender), L2374/2599/2645/2917/3021 part assertions | 12 failure-bearing outputs pre-L4288; caught pre-delivery (see Wins) |
| 6 | **Runtime / dependency / environment errors** | 8 | S1 | `ModuleNotFoundError: scipy` (L1500), `fitz` (L2075), `name '__file__' is not defined` under MCP exec (L2365), `IndentationError` (L1081), ffmpeg `drawtext` filter missing (`video-encode.log:14-16`, L4249) | 8 outputs; no measured retry count |
| 7 | **Render/verify state leakage (settings clobbering)** | 3 | S1 | A4 checkpoint: "stale Cycles persistent-data black silhouettes; images now use persistent_data=False"; runtime-contract-probes.json preview failure leaves samples 99→7, res 960×720→64×64, path changed, `restored: false` | **294 images re-rendered** (598.7 s wasted); helper defect still unfixed (E2) |
| 8 | **Failure not propagated (exit 0 / OK on failure)** | 3 | S1 | runtime-contract-probes.json `default-python-exit` returncode **0** with `traceback_present: true`; backlog E3: "path checks print `AGENT_OK` even when report status is `REQUIRES_REFINEMENT`"; forward-verifier: "path checker can write failure status without a failing exit" | Unquantified; unfixed (E1/E3) |
| 9 | **Source churn invalidates review snapshot → subagent retries** | 4 | S1,S3 | `state.json`: arbiter `attempts: 3`, forward-verifier `attempts: 2`; arbiter history: "Live `check` and both searches returned `Catalog stale` after concurrent research additions"; journal 04: "Source vẫn đổi giữa lúc review khiến công sức snapshot nhanh cũ" | 3 extra subagent rounds |
| 10 | **Consumer written against assumed schema / wrong path → guard block** | 3 | S1 | retro plan.md §Verification correction: "assumed topic gates lived under the topics summary… KeyError then assertion failure"; retro2 §64: "prepare lần đầu đặt bundle ngoài `plans/knowledge-updates/` bị guard từ chối exit 2" | 2–3 rework rounds inside the retro itself |

Overflow (real but ≤2 occurrences, or cheap) in Appendix A — includes MCP connection, which the record
does **not** support as a recurring cost.

---

## Where time went

| Bucket | Measured value | Source / caveat |
|---|---:|---|
| Session wall clock (arm, S1) | 8 h 39 m 55.6 s | retro2:10 — span, **not** labor or waste |
| Top-level tool calls / outputs (S1) | 1,003 / 1,003 | chronology-evidence.json; `exec` may nest more |
| User messages / assistant messages (S1) | 40 / 217 | same |
| Render process elapsed-to-last-save, all arm builds | **≈163 min** (9,804 s) | my sum of 47 render logs' final `Saved:` timestamps; excludes concurrency and stalls |
| Frames rendered/processed then discarded/superseded | **≈8,460** (≈6,680 excluding caption frames) | 1835 (A5 rejected) + 1128 (A5 empty-target draft) + 1743+780+551 (A4 video, never delivered) + 349 (flexibility unencoded) + 294 (A4 black re-render) + ~1,780 caption frames |
| A4 video render burned then killed by owner | 2,671 saves / 1,539.8 s (~25.7 min) | receiver-video-final + final-video-main + receiver-video-opening + gap + render logs |
| A4 images rendered twice (persistent-data bug) | 294 → 294, 598.7 s + 700.4 s | `all-pages.log`, `all-pages-final.log` |
| Failure-bearing tool outputs (window ≤ L4288 only) | 25 = 8 runtime + 12 geometry/export + 5 framing/IK | session-evidence.json; **whole session N/A** |
| Owner steering messages / clarification asks | 13 selected steering; 4 ask calls / 6 question items | session-evidence.json, retro2:23 |
| Guard/gate blocks that stopped work | ≥4 (prepare exit 2; stale-source `show` exit 2; 2 stale-catalog review rejections) | retro2:64, forward-verifier history — **retro reports "0 hook denials"** |
| Reuse that avoided render | 720 frames (caption removal, encode 1.25 s); 2,931/3,020 prefix frames; 1,104 byte-identical hold frames | performance.md:24, hero-prefix-reuse.json, A4 checkpoint |

INFERENCE: discarded frames ≈ the same order of magnitude as delivered frames (A5 delivered 3,020).
Roughly half of all render work in S1 produced nothing shipped.

---

## Retro vs record

| # | Retro conclusion | What the record shows | Weight |
|---|---|---|---|
| 1 | Both retros: "Hook/gate blocks = 0 matching hook denials" | Scope-limited to a text pattern in one transcript window. Outside it, guards **did** block work ≥4× (prepare exit 2; stale-source refusal exit 2; two `Catalog stale` review rejections). The number reads as "guards never fired" | **Under-counted cost**; guards are a working control, and their friction is a design input |
| 2 | Retro1 §Debate C/D: animatic + raw-frame separation = "Do" | Both were concluded at 19:46–20:59, and the two most expensive render-then-reject incidents happened **after** (22:27 A4 kill, 23:00 A5 overlap). Journal 04 L4649 already flags "quy tắc viết trong Markdown không tự enforce" | **Strongest unflagged pattern**: a retro conclusion that did not bind within the same session |
| 3 | Retro2: "4 presentation incidents named" (A4 camera, empty receiver, 00:24 overlap, hero crop) | At least 3 more of the same class exist in the record: A3 servo flying off case → **37 frames re-rendered** (L6093), V1 tool-change keyframe full-vector overwrite (L1252), hand servo fouling wrist (L2478) | Class is ~2× more frequent than the retro's headline |
| 4 | `CLAUDE.md` Failure Protocol ranks `poll()`/context errors and 4.x socket-name AttributeErrors as the top failure modes | **Zero** `poll()` failures and **zero** socket-name AttributeErrors among the 25 categorized failures. Nearest is one `__file__ is not defined` under MCP exec | Operative doc points attention at a failure class the record does not exhibit |
| 5 | Retro1 Infra bucket: "1 initial connection error… không chứng minh lỗi kết nối lặp lại" | Correct and well-hedged. Adding S2: MCP tools "chưa nạp session" was routed around by the socket bridge, no cost recorded | **Retro conclusion supported**; MCP flakiness is not a real cost driver — do not redesign for it |
| 6 | Retro1/2 "F: more skills/daemons = Don't now" | Supported. But the *retrieval* cost the retros under-weight is real: `loads_with` cycles pulled 18–19 documents for one topic (L4838), and the catalog went 155 → 222 → 235 sources inside one day | Right verdict, wrong risk emphasised: reading cost, not skill count |
| 7 | Retro1 win: "Bỏ phụ đề tái dùng raw PNGs" | True and valuable. Not counted: ~1,780 captioned frames (384+589+720+87) were produced first and then thrown away by the owner's "Không cần phụ đề" | Reuse win partly offsets self-inflicted work |
| 8 | Skeptic report: "the risk is downstream summarization discarding qualifications" | Confirmed by the record's own shape: every build README carries correct BLOCKED language, and no instance was found of a summary dropping it | **Prediction held**; keep the per-artifact status fields |

---

## Wins (evidence that a practice prevented rework)

1. **Failing check with a nonzero exit, not a screenshot opinion.** The overlap repair was rejected
   *before* the long render: "Failing check exit 23 chứng minh lỗi, không chỉ nhận xét screenshot"
   (journal 07, L8502); `check-overlap-repair.py` re-run exits 0 and writes JSON. Saved a second
   3,020-frame render.
2. **Raw frame sequences kept separate from presentation.** Caption removal re-encoded from raw PNGs
   in **1.25 s** instead of re-rendering 720 frames (`task-video-encode.log`, performance.md:24).
3. **Per-frame evaluated-state hashing for reuse.** Hero framing fix reused **2,931** of 3,020 frames,
   re-rendered 89 — bound by old/new scene SHA-256, not filename (`hero-prefix-reuse.json`).
4. **Byte-identical hold-frame reuse.** A4 renderer rendered 5,411 unique states and copied **1,104**
   hash-bound identical frames (A4 checkpoint).
5. **Numeric geometry gates before delivery.** 12 geometry/export assertions fired pre-delivery,
   including degenerate faces detected only by **reading the exported STL back** — journal 01: "Kiểm
   tra file STL thật và sửa hình học/xuất file là cần thiết; mesh trong Blender đẹp không đủ."
6. **Independent review that reverses itself on measurement.** Reviewer withdrew the driver-obstruction
   finding after measuring screw-head direction (journal 07; overlap-diagnosis.md "Direct measurement
   corrects the earlier access inference").
7. **Originals preserved with hashes.** V1 `9ed05eb6…` and reference-V2 `7ec71fb5…` unchanged across
   five downstream builds; `frozen-source.blend` / `source-freeze.json`. No destructive-overwrite
   incident appears anywhere in the record.
8. **Two-fails → change approach class.** SYJ: procedural gradient failed twice → cropped + rectified
   the real wallpaper → passed immediately (`build-260728-0947`, "ĐỔI APPROACH").
9. **Coupon/fit-study before the full set.** 36×36×6 mm coupon exported and measured after STL import
   before any full print set (reference-v2 README).
10. **Preview did catch one staging error.** "Preview lộ camera đi tới vùng trống (L8195)" → receiver-first
    redesign. FACT that temporal preview works — it caught 1 of the 2 A5 defects; the 00:24 overlap
    escaped because the preview was not checked against a *path* predicate.

Counter-evidence to a common assumption: **blockout and animatic artifacts existed and still did not
prevent the A4 rejection.** `workshop-blockout.blend`, `original-style-blockout.blend`, A4
`video/animatic` = 267 frames, A5 `animatic` = 472. The gate existed as an artifact; it was not a
**decision point shown to the owner**. That distinction is the actionable one.

---

## Orchestration patterns

| Session | Pattern | Observed consequence |
|---|---|---|
| S1 arm (260905, Codex transcript `01a07092`) | Single main agent, live MCP socket (9876) for build, headless for renders; internal read-only reviewers spawned per delivery | 1,003 tool calls / 8h40m; 13 owner steering messages; every presentation defect was caught by owner or an *independent* reviewer, never by the builder's own gate |
| S1 knowledge orchestration (S3) | `jobs.yaml`: 5 internal subagents, concurrency 3, `effect: observe`, **R0 read/report only — main performs all writes** | Clean isolation, no write collisions. Cost: arbiter 3 attempts, forward-verifier 2 attempts, both from snapshot staleness under concurrent source additions |
| S1 retro | `ak:brainstorm` → `ak:autoresearch` → `ak:predict` (5 independent personas + 1 cross-debate) + controller fault probes | Produced the only falsifiable artifacts in the whole record (`runtime-contract-probes.json`); the "Don't now" verdicts resisted skill sprawl |
| S2 drone (260728) | Declared tiering: Codex 5.6 sol plans/reviews · Terra implements · Kongming/Fable audit | Direction produced, **execution paused**; no geometry built after the fidelity decision. Tiering was declared, not exercised |
| S2 img2threejs / avata | Fable architecture audit on a stuck build | Correctly killed a dead end: "Stop manually tuning circles and boxes" after 3 failed parameter passes at IoU 0.25–0.48 |

Notes: no instance of a **subagent going idle without delivering** appears in this project's record —
the known global trap did not fire here (all five orchestrated jobs wrote `result.md`). Live-MCP vs
headless was never a source of confusion in the record; the one connection error (L27) was a missing
addon, resolved in 6 minutes.

---

## Spec vs code drift

**Count:** `refine-code` events are more frequent (≈25 categorized failures + repair rounds).
**Cost:** `refine-spec` events dominate by an order of magnitude — every full rebuild traces to one.

| Event | Class | Trigger |
|---|---|---|
| V1 built on assumed 90/90 mm links; reference dimension photo arrives at 15:51 | refine-spec | Owner supplied "Tham khảo kích thước" (L1083) after detailing had begun |
| "Follow 100% shape/khớp reference… dựng 1 model thứ 2" (L1413) | refine-spec | Whole second model (V2) + later full Arm rebuild (L2273) |
| Payload 250 g / hold many minutes answered only at L1853–1855 | refine-spec | Invalidated V1 actuator sizing; forced SM105 class, larger shoulder/elbow |
| Demo: joint-range → natural task (L3663) | refine-spec | 589-frame flexibility render superseded, 240 encoded |
| A4 workshop camera → back to A3 language (L7850) | refine-spec | Entire A4 video abandoned (~3,074 frames) |
| Drone spec "explicitly permits stylized webs, smooth placeholder caps… pass gate 0.7" | refine-spec | review-260728-1112: "This is a `refine-spec` failure first, then a geometry failure" |
| 00:24 overlap, `e9323` diagonal sweep, black frames, keyframe overwrite, servo fly-off | refine-code | Correctly diagnosed and repaired at source |
| img2threejs review smoke rejected headset-omitting render but **misrouted root cause as `refine-code`** | misclassification | BRV: "image metrics must not decide spec-vs-code without structural evidence" |

INFERENCE: the verdict taxonomy exists (`continue/refine-spec/refine-code/request-input/stop`) and is
correct; what is missing is the **cheap discriminator** that decides which one applies. In every
expensive case the discriminator was an owner message, not a check.

---

## Owner corrections (verbatim, `public-message-timeline.json`)

Strongest signals of what "better" means to Jang. Line numbers are transcript lines.

| L | Verbatim | Reads as |
|---:|---|---|
| 44 | "I can't see the tab BlenderMCP, **you control blender and do it for me**." | Do not hand back manual GUI steps; install/configure yourself |
| 602 | "Toàn bộ body cũng cần **polish hơn ngoại hình**. Tương tự như cái hình được gửi từ ban đầu." | Appearance vs the reference is a first-class requirement, not cosmetics |
| 880 | "cái model đó nhìn **mềm mại và polish cực tốt**. Các ốc vít không quá dài và thô, tổng thể nhìn **như hàng của Apple** vậy." | Product-grade finish is the bar |
| 937 | "Ốc và vít thì phải **âm vừa vặn vào thân, không lồi ra ngoài**." | Concrete, checkable constraint given only after V1 |
| 1413 | "Các shape và các khớp của reference image. Chúng ta cần **follow 100%**." | Fidelity contract, arrived mid-build |
| 1815 | "đây là bản thiết kế chuẩn để có thể in 3D và **hoạt động chứ không phải làm demo cho vui**. Cần phải tính toán về mặt cơ khí chính xác, tải, vận hành" | Rejects "pretty demo" framing outright |
| 2263 | "**Rồi dựng lại toàn bộ Arm chưa?**" | Caught that only a joint study, not the arm, had been rebuilt |
| 2471 | "**Nhớ kiểm tra luôn cái module hand nữa nhé.**" | Owner supplying the missing coverage check |
| 3663 | "Nên demo **1 cách tự nhiên hơn**. Robot di chuyển và làm 1 số task" | Purposeful behavior > axis sweeps |
| 4210 | "**Không cần phụ đề đâu.** Video thôi." | Presentation minimalism |
| 5711 | "OK đã index và map vào workflow và skill hết chưa? **đã tự tin bắt đầu task chưa?**" | Demands a readiness assertion before work |
| 7001 | "Mấy cái slide photo step by step thì **chúng ta chưa cần làm annotation** và text vội." | Cut scope the agent had expanded |
| 7206 | "trong lúc lắp thì **camera phải focus vào object đang lắp**. Các element sẽ tự bay tới." | Explicit camera contract |
| 7815 | "**Dừng cái video đi, nó chưa đúng ý của tôi. Vì camera cứ lia loạn hết cả lên.**" | Hard stop on a passing-but-wrong render |
| 7850 | "cái video ban đầu **đã gần đúng ý** với tôi rồi. Chỉ cần phần transition mượt hơn và thứ tự lắp chuẩn hơn" | Owner names the baseline — do not redesign it |
| 7998 | "**Bỏ cục màu đen đi**, chỉ cần nối dây cho đẹp và có tổ chức" | Removes agent-invented element |
| 8439 | "Đoạn từ **0:24 các element bị đè lên nhau, lỗi**." | Owner is the last-resort defect detector |
| 9190 | "**Tốt lắm**, bây giờ retro…" | Only acceptance in the record — of the *repaired video*, nothing mechanical |

Pattern across these: the owner corrects **direction and scope 11 times** and **defects 2 times**.
The two defect catches (7815, 8439) both happened *after* internal gates reported PASS.

---

## Not read

- Raw transcript `~/.codex/sessions/2026/09/05/rollout-…01a07092….jsonl` (only the derived
  timeline/evidence JSONs).
- Most `builds/*/reports/*.json` (read: overlap, video-status, hero-prefix-reuse, acceptance, state,
  runtimes, session-evidence; skipped ~150 others).
- `knowledge/` (26 files), `research/` (20 dirs), `scripts/`, `tests/` sources.
- Persona reports `architect.md`, `security.md`, `ux.md`, `final-review.md`, `debate-response.md`
  (read `skeptic.md`, `performance.md`, `debate.md`, `research.md`).
- `plans/reports/knowledge-evolution/*` detail; `plans/robot-arm-modular/plan.md`,
  `robot-arm-reference-v2/*.md`; `plans/checkpoints/`; `plans/blender-knowledge-workflows/`.
- Three.js build sources (`syj-threejs`, `compact-mac-threejs`, `dji-avata-2-threejs` — READMEs only).
- `researcher-260728-0918-*` (3 × ~20k research reports) and `research-260728-1156-img2threejs-hands-on.md`
  (BRV summary only).
- No image, video, or `.blend` was opened; no Blender was run.

## Unresolved questions

1. Were the ~1,780 caption frames rendered separately, or produced by post-processing existing raw
   frames? `task-caption.log` has no timestamp; cost is UNKNOWN. If post-processing, pattern 4's cost
   drops by ~1,780 frames.
2. The ≈163 min render figure assumes runs were sequential. `parallel-probe-a/b/c.log` show a
   concurrency experiment; if renders overlapped, wall-clock render time is lower.
3. `animation-render.log` has a 1,062 s gap between saves 289/290 — sleep, contention, or a stalled
   frame? performance.md:16 leaves it UNKNOWN. If stalls recur, an unattended-render watchdog matters
   more than any workflow rule.
4. Are the July drone/avata failures the *same* class as the arm's, or a distinct
   "two-view reconstruction is underdetermined" class that no workflow can fix? Both records blame
   "no quantitative reference-to-geometry contract", but the avata audit concluded the *representation*
   was the limit — those imply different remedies.
5. What made retro1's conclusions non-binding 90 minutes later — no enforcement mechanism, or the
   conclusions were never re-read in-session? The record shows the outcome, not the cause.
6. No Git repository exists; all "no destructive overwrite" claims rest on hash records the same agent
   wrote. Unfalsifiable from inside the record.

---

## Appendix A — patterns with ≤2 occurrences (do not redesign around these)

| Pattern | Occurrences | Evidence | Note |
|---|---:|---|---|
| MCP/transport failure | 2 | L27 "Could not connect to Blender" (missing addon, fixed by 15:03); S2 "MCP tools chưa nạp session" → socket-bridge workaround | Retro's refusal to generalize is correct |
| `bpy.ops` context / `poll()` failure | **0** | absent from all 25 categorized failures | `CLAUDE.md` Failure Protocol over-weights this |
| Blender 4.x socket-name AttributeError | **0** | absent | ditto |
| Local dependency missing in Blender's Python | 2 | `scipy` L1500, `fitz` L2075 | Cheap; a preflight import check closes it |
| ffmpeg filter unavailable | 1 | `video-encode.log:14-16` `drawtext` not found | Preflight only the filters actually requested |
| Subagent idle without delivering | **0** | all 5 orchestrated jobs wrote `result.md` | Global known-trap did not fire here |
| Destructive overwrite of a delivered artifact | **0** | V1/V2 hashes preserved across 5 builds | Strongest standing discipline in the project |

## Appendix B — frame accounting (on-disk, 260906)

| Location | Frames | Fate |
|---|---:|---|
| `robot-arm-original-refined/video/frames` | 3,022 | **delivered** (3,020 in MP4) |
| `…/rejected-522afd-partial-frames` | 1,835 | discarded (owner found 00:24 overlap at ~60%) |
| `…/empty-target-draft-animatic` | 1,128 | superseded (camera into empty area) |
| `…/animatic` | 472 | preview — used |
| `robot-arm-assembly-guide/video/frames` | 1,743 | **never delivered** (video stopped) |
| `…/tray-camera-draft-frames` | 780 | superseded |
| `…/receiver-camera-anticipation-draft-frames` | 551 | superseded |
| `robot-arm-assembly-guide/images` | 294 | delivered (after a full 294-image re-render) |
| `robot-arm-v2-engineered/videos/flexibility-frames` | 589 | 240 encoded, 349 superseded |
| `…/task-frames` + `task-captioned` | 720 + 720 | 720 delivered; captioned set dropped |
| `…/frames` + `captioned-frames` | 384 + 384 | captioned set dropped |
