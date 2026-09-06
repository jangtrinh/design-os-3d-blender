# Hyper3D Rodin — Research Dossier

**Compiled:** 2026-07-28. All prices/version numbers carry the date of the source they came from.
**Context:** evaluating Rodin as the generative-3D backend for a Claude + `ahujasid/blender-mcp` Blender pipeline.

Legend: **[V]** = verified with a source link below. **[UNVERIFIED]** = could not confirm from a primary/independent source.

---

## 1. What it is now (2026)

- **Company:** Deemos Technology / "Deemos Corporation" (footer on hyper3d.ai reads `© 2026 Deemos Corporation`). Founded 2020, roots in ShanghaiTech University (Jingyi Yu / Lan Xu labs). Product lineage: WAND (2020, sketch→image) → Light Stage capture rig (2021–23, ~2,000 actors scanned) → ChatAvatar (SIGGRAPH 2023) → CLAY / Rodin (2024–). **[V]** (befores & afters interview with CTO QX Zhang, 2026-01-27)
- **Products under hyper3d.ai:** `Rodin` (general 3D gen), `ChatAvatar` (avatars/heads), `OmniCraft` (texture gen, HDRI gen, image enhance/remix, mesh editor, 3D model search, SVG→3D, format converter). **[V]** (hyper3d.ai nav, fetched 2026-07-28)
- **Current model version: Rodin Gen-2.5**, launched **2026-05-26**. Marketing headline on hyper3d.ai today: *"Geometry in ~4s, full model in ~5s, 10M+ polygons, clean structure, production-ready outputs."* **[V]** (press release 2026-05-26; hyper3d.ai homepage fetched 2026-07-28)
- **Version timeline [V]:**
  - Gen-1 / 1.5 — tiers `Sketch`, `Regular`, `Detail`, `Smooth`. Still documented and callable.
  - **Gen-2** — announced 2025-10-01. 10B-parameter model, "BANG architecture", recursive part-based generation, baked normals, HD textures.
  - **Gen-2 Edit / "3D Nano Banana"** — launched 2026-03-31. Box-select a region + natural-language edit; Smart Low-poly; BANG-to-parts; normal baking.
  - **Gen-2.5** — launched 2026-05-26. Five tiers, 3D-native texturing, up to 2M faces via API (10M+ claimed in the web app).
- **Actively developed: yes, strongly.** Evidence: Gen-2.5 launch May 2026; Gen-2 Edit March 2026; official Claude Code skill repo `DeemosTech/rodin3d-skills` last commit **2026-05-25 ("update Rodin Gen2.5 support")**; new funding round of "several hundred million RMB" announced **2026-07-03** to fund 3D foundation-model R&D and global commercialization of Hyper3D. **[V]**
- Deemos won a **SIGGRAPH 2025 Best Paper award** (the BANG paper, ACM TOG 44(4) Art. 62) — the second SIGGRAPH honour after CLAY's 2024 Best Paper Honorable Mention. **[V]**

---

## 2. Capability surface / "skill set"

### 2a. What the platform exposes

| Capability | Web app | REST API | In `ahujasid/blender-mcp`? |
|---|---|---|---|
| Text→3D | yes | yes (`prompt`, no images) | **yes** — `generate_hyper3d_model_via_text` |
| Image→3D (single) | yes | yes | **yes** — `generate_hyper3d_model_via_images` |
| Multi-image (≤5, multi-view) | yes | yes (`images` ×5, `image_label` F/FL/FR/L/R/B/BL/BR/U/D/?) | partially — you can pass a list, but no `image_label`, no `condition_mode` |
| Sketch→3D | not a distinct mode; "Sketch" is a *speed tier* name in Gen-1, not a sketch-input mode. A sketch is just an image input. **[V]** | same | n/a |
| Retexture existing mesh | yes (OmniCraft AI Texture Generator) | **yes** — `POST /api/v2/rodin_texture_only` (upload `model` ≤10MB + `image`, optional `prompt`, `reference_scale`, `resolution` Basic/High) | **no** |
| Remesh / poly-count control | yes ("Smart Low-Poly") | yes — `quality` + `quality_override` | **no** (hardcoded) |
| Part-level generation / split | yes ("Iterative Splitting", "BANG to Parts") | **yes** — `POST /api/v2/bang` (`asset_id` OR uploaded `model`, `strength` 2–12) | **no** |
| Localized edit / 3D inpainting | yes (Gen-2 Edit, Mar 2026) | **no public endpoint found** `[UNVERIFIED]` | **no** |
| PBR material output | yes | yes — `material` = `PBR` \| `Shaded` \| `All` \| `None`; PBR = basecolor + metallic + normal + roughness | implicit (GLB w/ built-in materials) |
| Texture resolution | 2K default, 4K via HighPack | `addons=["HighPack"]` → 4K; `hd_texture` bool; `texture_mode` legacy/extreme-low/low/medium/high; `texture_delight` | **no** — hardcodes `texture_mode=high` |
| Formats | GLB, GLTF, FBX, OBJ, STL, USDZ | `geometry_file_format` = `glb`\|`usdz`\|`fbx`\|`obj`\|`stl` | **GLB only** (hardcoded, and the importer only picks `*.glb`) |
| Quad vs tri | yes | `mesh_mode` = `Raw` (tris) \| `Quad`. **Gen-2.5 default is `Raw`**; Gen-1/Gen-2 default was `Quad` | **hardcoded `Raw`** → triangles |
| Bounding-box ControlNet | yes | `bbox_condition` = [Width(Y), Height(Z), Length(X)] | **yes** — `bbox_condition` param, normalized to 0–100 |
| Voxel / point-cloud ControlNet | yes (homepage claim) | **not in public API docs** `[UNVERIFIED]` | no |
| T/A-pose for humanoids | yes | `TAPose` bool | no |
| Seed control | yes | `seed` 0–65535 | no |
| Preview render | yes | `preview_render` bool | no |
| **Auto-rig / skeleton / skinning** | **no evidence found.** Not in the API docs index, not in the pricing feature matrix. An independent review states Rodin outputs "static meshes" with no rigging. Treat auto-rig as **absent**. **[V-negative]** | no | no |

### 2b. Gen-2.5 tier / poly-count matrix **[V]** (developer.hyper3d.ai, fetched 2026-07-28)

| Tier | Credits | Notes |
|---|---|---|
| `Gen-2.5-Extreme-Low` | 0.5 | fastest, simple assets |
| `Gen-2.5-Low` | 0.5 | clean assets, small hardsurface props |
| `Gen-2.5-Medium` | 0.5 | balanced; supports `geometry_instruct_mode=creative` |
| `Gen-2.5-High` | 0.5 | richer structure, smooth surfaces |
| `Gen-2.5-Extreme-High` | **1.0** | high-frequency detail; unlocks `is_micro` |

`quality` presets: `high` = 1M faces (Raw) / 50k (Quad) · `medium` = 500k / 18k · `low` = 60k / 8k · `extra-low` = 20k / 4k. `quality_override` ranges: Quad 1,000–200,000; Raw 500–1,000,000 (low tiers) or 20,000–2,000,000 (High / Extreme-High). **[V]**

`HighPack` addon: +1 credit → 4K textures instead of 2K, and in Quad mode ~16× the face count. **[V]**

### 2c. Exactly what `ahujasid/blender-mcp` ships (source read at commit `da4e16d`, 2026-07-21)

Four MCP tools in `src/blender_mcp/server.py`:

1. `get_hyper3d_status(user_prompt="")` → enabled/disabled + mode + key type (`private` / `free_trial`).
2. `generate_hyper3d_model_via_text(text_prompt, bbox_condition=None)`
3. `generate_hyper3d_model_via_images(input_image_paths=None, input_image_urls=None, bbox_condition=None)` — `input_image_paths` for MAIN_SITE mode (base64'd), `input_image_urls` for FAL_AI mode.
4. `poll_rodin_job_status(subscription_key=None, request_id=None)`
5. `import_generated_asset(name, task_uuid=None, request_id=None)`

The Blender-side addon (`addon.py`) does the HTTP. **Critical findings for your pipeline:**

- **It calls the legacy Gen-1 endpoint with `tier="Sketch"`, `mesh_mode="Raw"`, `texture_mode="high"` — hardcoded.** (`addon.py:1324-1326`). Sketch is the *lowest* Gen-1 tier: ~20s, 1K texture, low-poly, **triangles only**, `quality` locked to `medium`, `quality_override` ignored. You are getting the weakest thing Rodin sells.
- **Base URL is `https://hyperhuman.deemos.com/api/v2/rodin`** while current docs use `https://api.hyper3d.com/api/v2/rodin`. I probed both on 2026-07-28: **both return `401 {"error":"UNAUTHORIZED","message":"Active API key is required."}`**, so the legacy host is still live and aliased. **[V]**
- **Free trial key is literally the string `vibecoding`** (`addon.py:33`, `RODIN_FREE_TRIAL_KEY = "vibecoding"`). The *official* Deemos Claude skill documents the same key: *"Free Test Key: `vibecoding` (automatically used when no key is provided)"*. README: "free trial key allows you to generate a limited number of models per day." **[V]**
- **FAL_AI mode** posts to `https://queue.fal.run/fal-ai/hyper3d/rodin` with `Authorization: Key <k>` and `tier: "Sketch"` — also legacy.
- Import path only accepts `.glb` from the download list; the GLB is imported, joined, and renamed via `_clean_imported_glb`.
- No exposure of: tier, quality, mesh_mode, format, material, seed, TAPose, HighPack, texture options, BANG, retexture.

**Implication:** if quality matters, do not rely on blender-mcp's built-in Rodin path as-is. Either (a) fork `addon.py` and change three hardcoded form fields to `tier=Gen-2.5-High`, `mesh_mode=Quad`, `quality_override=...`, or (b) bypass it — call the REST API yourself, write the GLB/FBX to disk, and use blender-mcp's generic `execute_blender_code` to import. Option (b) also gets you BANG part-splitting and retexture, which blender-mcp has no wrapper for.

---

## 3. API

**[V] — all from developer.hyper3d.ai, fetched 2026-07-28**

- **Base:** `https://api.hyper3d.com/api/v2/` (legacy `https://hyperhuman.deemos.com/api/v2/` still answers).
- **Auth:** `Authorization: Bearer RODIN_API_KEY`. Keys from `https://hyper3d.ai/api-dashboard`. **A Business subscription is required** — errors `NO_ACTIVE_SUBSCRIPTION` / `SUBSCRIPTION_PLAN_TOO_LOW` ("Business subscription is required to use Rodin Gen-2.5 API").
- **Endpoints:**
  - `POST /api/v2/rodin` — generation (multipart/form-data). Free/Gen-1/Gen-2/Gen-2.5 all through this one endpoint, selected by `tier`.
  - `POST /api/v2/rodin_texture_only` — retexture an uploaded mesh. 0.5 credit.
  - `POST /api/v2/bang` — part decomposition. 0.5 credit.
  - `POST /api/v2/status` — poll. Free.
  - `POST /api/v2/download` — get signed URLs. Free.
  - `GET/POST /api/v2/...balance` — check remaining credits. Free.
- **Async job model:** submit → get `{uuid, jobs:{uuids[], subscription_key}}` → poll `/status` with `subscription_key` → statuses `Waiting` / `Generating` / `Done` / `Failed` → `POST /download` with `task_uuid` (note: `uuid`, **not** `jobs.uuids`) → list of `{url, name}` including a `preview.webp`.
- **Polling vs webhook:** the first-party API is **polling only** — docs recommend every 5s, and warn *"Please refrain from calling this API too frequently… We may throttle some requests that are sent too frequently."* No webhook in the first-party docs. **Webhooks exist only via fal.ai's queue wrapper** (`fal-ai/hyper3d/rodin/v2.5`), which supports webhook URLs. **[V]**
- **Rate limits:** stated on the pricing page as **120 RPM on the first three Gen-2.5 tiers, 240 RPM on higher tiers** for Business; Enterprise custom. No documented hard rate-limit table in the API docs beyond the throttling warning. **[V]**
- **Data retention:** "securely stored for **7 days**, will **not** be used for training, will **not** be shared without explicit consent", and API-generated models do not appear in any user's ASSETS tab. **[V]**
- **Official MCP server?** There is **no first-party MCP *server*** that I could confirm. What Deemos actually publishes is:
  - `DeemosTech/rodin3d-skills` — an **official Claude Code Skill/plugin** (`/plugin marketplace add DeemosTech/rodin3d-skills`), v2.0.0, Gen-2.5, last commit 2026-05-25. It's Python scripts + SKILL.md, not an MCP server. **[V]**
  - `DeemosTech/blender-mcp-rodin-integration` — Deemos' **fork of ahujasid/blender-mcp**, last commit 2026-01-23. Behind upstream. **[V]**
  - Third-party directories list a "Rodin MCP Server" under DeemosTech, but the repo `DeemosTech/rodin-mcp-server` was not clonable/public on 2026-07-28. **[UNVERIFIED]**

**Minimal working request [V]** (verbatim shape from the docs):

```bash
export RODIN_API_KEY="..."
curl https://api.hyper3d.com/api/v2/rodin \
  -H "Authorization: Bearer ${RODIN_API_KEY}" \
  -F "images=@/path/to/ref.jpg" \
  -F "tier=Gen-2.5-Medium" \
  -F "mesh_mode=Quad" \
  -F "quality_override=18000" \
  -F "geometry_file_format=fbx" \
  -F "material=PBR" \
  -F "texture_mode=high" \
  -F "geometry_instruct_mode=creative"
# -> {"uuid": "...", "jobs": {"uuids": [...], "subscription_key": "..."}}

curl -X POST https://api.hyper3d.com/api/v2/status \
  -H "Authorization: Bearer ${RODIN_API_KEY}" -H 'Content-Type: application/json' \
  -d '{"subscription_key":"..."}'          # poll every ~5s until all jobs "Done"

curl -X POST https://api.hyper3d.com/api/v2/download \
  -H "Authorization: Bearer ${RODIN_API_KEY}" -H 'Content-Type: application/json' \
  -d '{"task_uuid":"..."}'                  # -> {"list":[{"url":"...","name":"model.fbx"}, ...]}
```

Text-to-3D is the same call with **no** `images` field and a required `prompt`.

---

## 4. Pricing as of 2026

**[V] — hyper3d.ai/pricing, fetched 2026-07-28.**

| Plan | Monthly | Yearly | Included | Notes |
|---|---|---|---|---|
| **Free** | $0 | $0 | "Pay by result": generate free, pay on confirm/export. 10 private assets. Limited multi-image. **No API access.** | Top-up "direct credits" cost **$1.50 / credit** |
| **Creator** | **$30/mo** | **$288/yr** (= $24/mo) | "About 60 models". Multi-image→3D, Smart Low-Poly, HD/custom texture, baked normals, redos: geometry ×20 / material ×6. Unlimited export + private assets. | **No API access** |
| **Business** | **$120/mo** | **$1,152/yr** (= $96/mo) | "About 416 models". Everything in Creator **+ full API access**, 4K textures, high-poly quads, redos geometry ×50 / material ×15, **120 RPM (first three tiers) / 240 RPM (higher)**, ChatAvatar commercial licence | This is the minimum tier for the API |
| **Enterprise** | custom | custom | on-prem, custom LoRA fine-tuning, team controls, volume discount, "AI+Artist" production support | |
| **Education** | Creator benefits at education pricing, verification required | | | |

**What one generation actually costs [V]:**
- API credit cost: **0.5 credit** for every Gen-1/Gen-2/Gen-2.5 tier except `Gen-2.5-Extreme-High` = **1.0 credit**. `HighPack` addon = **+1 credit**. BANG split = 0.5 credit. Texture-only = 0.5 credit. Status/download = free.
- Pay-as-you-go direct credits: $1.50/credit → **~$0.75 per standard generation**, ~$1.50 for Extreme-High, ~$2.25 with HighPack.
- Via subscription the effective rate is much lower: Creator $30 ÷ ~60 models ≈ **$0.50/model**; Business $120 ÷ ~416 models ≈ **$0.29/model**. (Vendor's own "estimated output" numbers — treat as an upper bound on value.)
- Free tier: generation itself is free; you pay to *confirm/download*. This is the "totally free to generate, pay on download" model the CTO described in Jan 2026. Practical free throughput is unspecified.
- The `vibecoding` free-trial key used by blender-mcp is rate-limited "a limited number of models per day" — exact number undocumented. `[UNVERIFIED]`
- fal.ai hosts `fal-ai/hyper3d/rodin/v2.5` with its own metered pricing ("Extreme-High bills at double the base rate"); exact per-call USD not shown on the model page. `[UNVERIFIED]`

---

## 5. Output license

**[V] — Deemos Terms of Service, `https://hyperhuman.deemos.com/legal/terms` (= hyper3d.ai/legal/terms), fetched 2026-07-28.**

The ToS treats **Rodin and ChatAvatar completely differently**:

> **(b) Rodin** — "If you use **Rodin** to generate Output, **we will not limit your use of such Output**, subject to any restrictions set forth in these Agreements, the Applicable Laws and any third-party terms and conditions applicable to such Output or Services."

> **(a) ChatAvatar** — default output is a **Creative Commons non-commercial** licence ("Users shall not use the Content for commercial purpose"). Commercial use requires *purchasing* the "License" on that specific output, which then grants copy/modify/derivative/commercial rights on a non-exclusive, revocable, non-transferable, non-sublicensable basis.

Section 6.1 explicitly **carves Prompts and Output out** of Deemos' IP claim ("excluding any Prompts and Output, the arrangement of which shall be subject to Section 5").

Practical reading:
- **Rodin output: effectively unrestricted use, including commercial.** But note the wording is a *non-limitation*, **not an assignment of ownership**. Deemos does not warrant that the output is copyrightable or that any IP rights subsist in it: *"we make no representations, warranties or undertakings of any kind as to the copyrightability of any Output."* No indemnity — *"We take no responsibility for … any infringement of third party rights resulting from your use of such Output."*
- **You warrant your inputs.** You must hold all rights to any prompt/image you upload. Feeding in copyrighted reference art is on you.
- **Plan-gated in practice.** ToS §2 says you may export "for private or commercial use **depending on your subscription plan**", and the pricing matrix gives "Unlimited export and any use" only to Creator and above; Free is limited. Pricing FAQ: *"Paid plans include broader export and usage rights… Review the current terms before using assets in regulated or high-risk contexts."* So **do not assume the free tier is commercially clean.**
- ChatAvatar commercial licence is bundled into the Business plan.
- **Content moderation:** Deemos reserves the right to access, review, screen, edit, block, delete outputs and prompts at any time.

---

## 6. Quality, honestly assessed

**Big caveat up front:** the independent-evidence situation is poor. Search results for "Rodin review/comparison" in 2026 are dominated by (a) Deemos press releases syndicated across dozens of financial-news mirrors, (b) competitor-owned comparison pages (Meshy, Neural4D, 3DAIStudio, trellis2.app) that are marketing in review clothing, and (c) obviously AI-generated affiliate "review" sites. Reddit was unreachable from this environment (403 on the JSON API, proxy rejected domain-restricted search). **I could not find a rigorous, neutral, reproducible benchmark.** What follows is triangulated and flagged accordingly.

**Topology.** Marketing: "clean quad topology, no retopo needed." Reality is more conditional:
- Quad output is real and is a genuine differentiator — `mesh_mode=Quad` is a first-class documented parameter with a face-count budget you set (1k–200k). Gen-1/Gen-2 **defaulted** to Quad. **[V, docs]**
- But **Gen-2.5's documented default is `Raw` (triangles)**, and the highest-fidelity paths (Raw 20k–2M faces, `is_micro`, 10M-poly claims) are triangle soup by construction. High-poly Rodin output *is* dense triangles; the quad path is a separate, lower-poly product of their "Smart Low-Poly" autoregressive remesher. **[V, docs]**
- Independent-ish user reports say quad output is usable but not free: *"Complex topology still needs manual cleanup"*, and in a 5-take test *"cargo items merged into a single mesh in two of five takes"* for multi-object scenes (vuela.ai review). A competitor-authored but specific comparison notes Rodin's high poly counts "require post-processing for game assets" vs Tripo's leaner meshes.
- The company's own CTO said in Jan 2026 that the models are *"not that game-ready"* and are better for prototyping — that is the most credible negative signal available, because it's against interest. **[V]**
- **My read:** quad mode at 8k–50k faces is genuinely better than a marching-cubes triangle dump and is often good enough for props/set dressing; it is **not** artist-grade edge flow and will not survive close animation deformation. Character work still needs retopo.

**UVs.** Documented as automatic; Gen-1 Sketch is described as "simple UV mapping". No independent teardown of UV seam placement, island packing, or texel-density consistency exists that I could find. **[UNVERIFIED]** — assume auto-unwrap quality, i.e. fine for baked PBR, awkward if you plan to hand-paint or tile.

**PBR maps.** Real and multi-channel: basecolor + metallic + normal + roughness, 2K default / 4K with HighPack, plus an 8K standalone texture generator in OmniCraft. Gen-2.5's headline change is "3D-native texturing" with better 360° coverage (i.e. less of the classic back-side smearing you get from multi-view 2D projection). `texture_delight` removes baked lighting from input images — a genuinely useful pipeline feature. Reviewers consistently call the PBR maps the strongest part of the output. Weakest documented aspect: `hd_texture` "improves texture quality but **may reduce similarity to the original input**" — vendor's own admission of a fidelity/prettiness tradeoff. **[V, docs]**

**Watertightness / 3D printing.** Rodin is CLAY-lineage: a 3D-native latent diffusion model over a 3DShape2VecSet-style implicit representation, meshed out — which *structurally* tends to produce closed, manifold surfaces, unlike multi-view-reconstruction approaches. Hyper3D markets 3D printing as a first-class use case and ships direct **STL** export. But I found **no independent manifold/watertightness audit**, no reports on wall thickness, self-intersections, or floating shells. **[UNVERIFIED]** — plan to run a mesh-check (3D Print Toolbox / netfabb) before slicing.

**Rig quality.** N/A — **there is no auto-rig.** Output is static meshes. `TAPose` only biases generation toward T/A pose so *you* can rig it downstream (Mixamo, Blender Rigify, AccuRig). If auto-rigging is a requirement, Tripo is the one that advertises it. **[V-negative]**

**Speed.** Vendor: 4s geometry / 5s full model / ~9–80s depending on tier for Gen-2.5; ~90s for Gen-2; ~20s for Gen-1 Sketch. One user review reports **5–10 minutes per generation** in practice. Queue depth almost certainly dominates. Treat sub-10s as a best case, not a planning number. **[V both sides]**

**Failure modes to expect [aggregated, medium confidence]:** merged/fused objects when the reference image contains several items; softened fine engravings and thin features; inconsistency between takes (redos are a paid, quota'd resource — geometry ×20/×50, material ×6/×15 — which itself tells you retries are expected); high-poly modes producing meshes too heavy to drop into a realtime engine without decimation.

---

## 7. Underlying technology

**Not related to Microsoft's RODIN — name collision only.** **[V]**
- Microsoft Research's *"RODIN: A Generative Model for Sculpting 3D Digital Avatars Using Diffusion"* (Tengfei Wang et al., arXiv 2212.06135, CVPR 2023) is a **roll-out diffusion network** that diffuses a tri-plane/roll-out 2D representation of neural-radiance-field avatars. Different institution (MSRA), different authors, different representation (NeRF tri-plane), different scope (heads/avatars only).
- Hyper3D's Rodin is Deemos/ShanghaiTech, a **3D-native latent set diffusion** model producing meshes. The shared name is a reference to Auguste Rodin the sculptor, not a lineage. No paper of Deemos' cites the MSRA work as a basis.

**What Hyper3D's Rodin actually is, publicly:**
- **CLAY** — *"CLAY: A Controllable Large-scale Generative Model for Creating High-quality 3D Assets"*, Longwen Zhang, Ziyu Wang, Qixuan Zhang, Qiwei Qiu, Anqi Pang, Haoran Jiang, Wei Yang, Lan Xu, Jingyi Yu (ShanghaiTech + Deemos). ACM TOG 43(4), SIGGRAPH 2024, **Best Paper Honorable Mention**. arXiv 2406.13897. This is the acknowledged foundation of Rodin: a **latent diffusion model over a neural-field 3D representation following 3DShape2VecSet**, trained natively on 3D data (~500k assets at the time) rather than distilled from 2D — which is why surfaces come out "smooth and clean" instead of needing retopo from a multi-view reconstruction. Multi-resolution VAE + minimalist latent DiT + a geometry/material ControlNet stack. **[V]**
- **BANG** — *"BANG: Generative Exploded Dynamics for 3D Assembly and Disassembly"* (working title on the project page: *Generative Exploded Dynamics for 3D Asset Decomposition*), Longwen Zhang, Qixuan Zhang, Haoran Jiang, Yinuo Bai, Wei Yang, Lan Xu, Jingyi Yu — ShanghaiTech + Deemos + HUST. **SIGGRAPH 2025, ACM TOG 44(4) Art. 62, arXiv 2507.21493, Best Paper.** Fine-tuned diffusion with spatial prompts + temporal attention that generates a smooth "exploded" trajectory decomposing an object into parts. This is the published basis for the `/api/v2/bang` endpoint and for Gen-2's "recursive part-based generation". **[V]**
- **Rodin Gen-2 architecture claims (vendor, unpublished):** "brand-new BANG architecture", **10 billion parameters**, 4× geometric mesh quality vs Gen-1, recursive part-based generation ("dividing and subdividing"), baked normals from high-poly onto low-poly, HD texture maps. **[V as a claim]**, no peer-reviewed Gen-2 paper found. `[UNVERIFIED as architecture fact]`
- **Rodin Gen-2.5 (vendor, unpublished):** five "thinking effort" modes, "3D-native" texture generation (texturing in 3D rather than projecting 2D views), Smart Low-Poly via **autoregressive mesh reconstruction** (i.e. a mesh-token transformer in the MeshGPT/QuadGPT family), 3D ControlNet (bbox / voxel / point cloud), part-level and localized editing. **No paper.** `[UNVERIFIED]`
- Deemos also has ChatAvatar (SIGGRAPH 2023) and a Light Stage capture pipeline (~2,000 actors, sub-micron geometry/material capture) — the proprietary scan data is plausibly a real moat for their material/texture quality, though the training-set composition is undisclosed.
- `CLAY-3D/OpenCLAY` exists on GitHub as the paper's public repo; **weights for the production Rodin models are not open.** **[V]**

---

## 8. Where it fits vs alternatives

Pick **Rodin** when you want the *most controllable* single-asset generator and you're willing to pay $120/mo for API access: it is the only one of this group that gives you, in one call, an explicit face-count budget (`quality_override`, 500–2,000,000), an explicit quad-vs-tri switch, five geometry fidelity tiers, a bbox ControlNet, direct FBX/OBJ/STL/USDZ export, *and* published-research-backed part decomposition (BANG) plus standalone retexturing of meshes you already own. That parameter surface is what makes it a good fit for an **agentic** pipeline — Claude can reason about "this is a background prop, use `Gen-2.5-Low` + `Quad` + 8k faces" vs "this is a hero object, `Gen-2.5-Extreme-High` + Raw + HighPack" — where competitors mostly give you a single opinionated path. Pick **Meshy** if you want cheap breadth and fast 4-up previews to art-direct by selection rather than by parameter, and you accept doing your own cleanup. Pick **Tripo** if you specifically need **auto-rigging** and stylized/game-ready low-poly out of the box, which Rodin simply does not do. Pick **Hunyuan3D** if you need to self-host, avoid per-generation costs at volume, keep assets entirely on-prem, or fine-tune — it's open-weights and reported to be the most *consistent* (fewest broken-geometry failures), at the cost of running your own GPUs. Pick **TRELLIS** if you're doing research or need its multi-representation (Gaussian splat / radiance field / mesh) flexibility — it's an open model, not a product, and its splat-first outputs are awkward to land in a Blender/DCC pipeline. For your specific stack — Claude + blender-mcp, single objects, needing GLB into Blender with materials — Rodin is a defensible default, but the winning configuration is **Rodin via direct REST calls with Gen-2.5 tiers**, not via blender-mcp's hardcoded `tier=Sketch` path; and it's worth wiring Hunyuan3D (already supported in blender-mcp) as a cost-free fallback for bulk background assets.

---

## Sources

**Vendor / primary**
- Hyper3D homepage — https://hyper3d.ai/ (fetched 2026-07-28)
- Hyper3D pricing — https://hyper3d.ai/pricing (fetched 2026-07-28)
- Deemos Terms of Service — https://hyperhuman.deemos.com/legal/terms (fetched 2026-07-28)
- API docs index (llms.txt) — https://developer.hyper3d.ai/llms.txt
- Get started — https://developer.hyper3d.ai/get-started/readme-1
- Minimal example — https://developer.hyper3d.ai/get-started/minimal-example
- API overview — https://developer.hyper3d.ai/api-specification/overview_reset_v
- Gen-2.5 spec — https://developer.hyper3d.ai/api-specification/rodin-gen2.5
- Gen-2 spec — https://developer.hyper3d.ai/api-specification/rodin-generation-gen2
- Gen-1 & 1.5 spec — https://developer.hyper3d.ai/api-specification/rodin-generation
- BANG endpoint — https://developer.hyper3d.ai/api-specification/bang_reset_v
- Generate Texture endpoint — https://developer.hyper3d.ai/api-specification/generate-texture_reset_v
- Check Status — https://developer.hyper3d.ai/api-specification/check-status_reset_v
- Download Results — https://developer.hyper3d.ai/api-specification/download-results_reset_v
- Data Retention Policy — https://developer.hyper3d.ai/legal/data-policy
- Rodin Gen-2 blog — https://hyper3d.ai/blog/rodin-gen-2

**Code**
- `ahujasid/blender-mcp` — https://github.com/ahujasid/blender-mcp (read at commit `da4e16d`, 2026-07-21; `src/blender_mcp/server.py` L611-1016, `addon.py` L33, L1300-1600, L2715-2745)
- `DeemosTech/rodin3d-skills` — https://github.com/DeemosTech/rodin3d-skills (official Claude Code skill, v2.0.0, last commit 2026-05-25)
- `DeemosTech/blender-mcp-rodin-integration` — https://github.com/DeemosTech/blender-mcp-rodin-integration (fork, last commit 2026-01-23)
- `CLAY-3D/OpenCLAY` — https://github.com/CLAY-3D/OpenCLAY

**Papers**
- CLAY (SIGGRAPH 2024, Best Paper Honorable Mention) — https://arxiv.org/abs/2406.13897 · https://dl.acm.org/doi/10.1145/3658146 · https://sites.google.com/view/clay-3dlm
- BANG (SIGGRAPH 2025, Best Paper) — https://arxiv.org/abs/2507.21493 · https://sites.google.com/view/bang7355608 · https://dl.acm.org/doi/10.1145/3730840
- Microsoft RODIN (unrelated, CVPR 2023) — https://arxiv.org/abs/2212.06135 · https://www.microsoft.com/en-us/research/project/rodin-diffusion/ · https://openaccess.thecvf.com/content/CVPR2023/html/Wang_RODIN_A_Generative_Model_for_Sculpting_3D_Digital_Avatars_Using_CVPR_2023_paper.html

**Press / coverage**
- befores & afters, "Everything you need to know about Hyper3d.ai and its Rodin 3D generative AI model", 2026-01-27 — https://beforesandafters.com/2026/01/27/everything-you-need-to-know-about-hyper3d-ai-and-its-rodin-3d-generative-ai-model/
- Gen-2.5 launch press release, 2026-05-26 — https://www.barchart.com/story/news/2134263/hyper3d-launches-rodin-gen-2-5-bringing-sculpt-level-detail-and-production-control-to-ai-3d-generation
- Gen-2 Edit / "3D Nano Banana" press release, 2026-03-31 — https://markets.financialcontent.com/observerreporter/article/pressadvantage-2026-3-31-hyper3d-launches-3d-nano-banana-for-ai-powered-3d-model-editing
- Gen-2 launch, 2025-10-01/02 — https://beforesandafters.com/2025/10/02/deemos-launches-rodin-gen-2-a-groundbreaking-generative-ai-for-intuitive-3d-creation/ · https://www.awn.com/news/deemos-launches-groundbreaking-rodin-gen-2-genai-intuitive-3d-creation
- Deemos SIGGRAPH 2025 Best Paper + Gen-2 debut, 2025-08-14 — https://markets.financialcontent.com/dowtheoryletters/article/pressadvantage-2025-8-14-deemos-wins-siggraph-2025-best-paper-award-debuts-rodin-gen-2-text-to-3d-foundation-model
- 80.lv sponsored interview with CTO QX Zhang, 2026-06-03 — https://80.lv/articles/how-hyper3d-rodin-gen-2-5-is-bringing-production-level-control-to-ai-3d-generation
- AWN interview, "Beyond Generation: Hyper3D.AI CTO Zhang Qixuan on Rodin Gen-2 Edit" — https://www.awn.com/animationworld/beyond-generation-hyper3dai-cto-zhang-qixuan-rodin-gen-2-edit-and-future-3d-ai
- Funding round, 2026-07-03 — https://www.shanghaitech.edu.cn/en/2026/0703/c1260a1125057/page.psp · https://www.yicaiglobal.com/news/chinese-ai-startup-deemos-raises-new-funds-for-hyper3d-rodins-global-rollout (502 at time of writing)

**Third-party / comparison (all with bias caveats)**
- fal.ai Rodin v2.5 API — https://fal.ai/models/fal-ai/hyper3d/rodin/v2.5/api
- Scenario KB, "Comparing Generative 3D Models" — https://help.scenario.com/articles/1263568892-comparing-generative-3d-models
- Scenario KB, "Rodin Hyper3D Models: The Essentials" — https://help.scenario.com/articles/6155258011-rodin-hyper3d-models-the-essentials
- 3DAIStudio, "Rodin 2.5 vs Tripo P1 vs Hunyuan 3D" (competitor-owned) — https://www.3daistudio.com/blog/rodin-2-5-vs-tripo-vs-hunyuan-3d-comparison
- vuela.ai Rodin review (hands-on claims, unverified authorship) — https://vuela.ai/models/rodin-ai/review
- Indie Hackers, "Best AI 3D Model Generator in 2026" (likely affiliate) — https://www.indiehackers.com/post/best-ai-3d-model-generator-in-2026-i-tested-9-of-the-best-and-here-is-what-i-found-70ecab1a0a
- Skywork "Hyper3D Review (2025)" (likely AI-generated) — https://skywork.ai/skypage/en/Hyper3D-Review-(2025)-My-Deep-Dive-into-AI-Image-to-3D-Model-Generation/1974392702218465280
