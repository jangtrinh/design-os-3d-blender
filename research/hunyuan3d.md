# Tencent Hunyuan3D — Research Dossier

**Compiled:** 2026-07-28
**Purpose:** engineering-decision input for an AI-driven Blender pipeline (Claude + `ahujasid/blender-mcp`, which ships a Hunyuan3D integration).
**Confidence convention:** claims below are sourced. Anything I could not confirm from a primary source is marked `[UNVERIFIED]`.

---

## 0. TL;DR for the pipeline decision

- **Open-source ceiling is Hunyuan3D 2.1** (June 2025). Everything newer — 2.5, PolyGen, 3.0, 3.1 — is **API/platform only**. Do not plan a local pipeline around 3.x.
- **2.1 is the first open version with true PBR** (albedo + metallic + roughness). 2.0 and earlier bake a single RGB albedo-ish texture.
- **The license is not OSI-open.** Tencent Hunyuan Community License: **excludes EU, UK and South Korea from the licensed Territory**, and use of the *Outputs* outside the Territory is also unlicensed. This is the single most decision-critical fact in this document.
- **macOS/Apple Silicon is not a viable local target.** Shape generation limps along on MPS via a community fork; the texture stage depends on a CUDA custom rasterizer. Plan on cloud.
- **blender-mcp exposes exactly 4 Hunyuan tools**, and its "official API" path is the Tencent Cloud `SubmitHunyuanTo3DJob` action — geometry+texture, **no PBR flag**, OBJ-in-a-ZIP. Its "local API" path targets the `api_server.py` shipped in the Hunyuan3D repos.

---

## 1. Version history and current state (2026)

| Version | Date | Status | What changed |
|---|---|---|---|
| **Hunyuan3D 1.0** | 2024-11-05 (arXiv 2411.02293) | Open weights | Two-stage but *different* architecture from 2.x: multi-view diffusion (~4 s) → feed-forward sparse-view **reconstruction** model (~7 s). Two sizes: `lite` and `std` ("3x more parameters than our lite"). Text-conditioned via Hunyuan-DiT. |
| **Hunyuan3D 2.0** | 2025-01-21 (arXiv 2501.12202) | Open weights | Architecture reset to **latent-set diffusion**: Hunyuan3D-ShapeVAE + Hunyuan3D-DiT (flow matching) + Hunyuan3D-Paint (multi-view RGB). 1.1B DiT. |
| 2.0 Fast | 2025-02-03 | Open | Guidance-distilled, ~2x faster. |
| Texture enhancement module | 2025-02-14 | Open | — |
| 2mini / 2mv | 2025-03-18 | Open | 0.6B mini shape model; 1.1B multiview-conditioned shape model. |
| **FlashVDM / Turbo** | 2025-03-19 (arXiv 2503.16302) | Open | Step distillation + Lightning Vecset Decoder. >45x reconstruction, 32x generation speedup; **~1 s shape on a 4090**. |
| Paint Turbo + MV texture pipeline | 2025-04-01 | Open | Distilled texture model. |
| **Hunyuan3D 2.1** | **2025-06-13** (arXiv 2506.15442) | **Open weights — current OSS ceiling** | **First open PBR**: albedo/metallic/roughness. 3.3B shape DiT, 2B paint. Training code + VAE encoder released. |
| **Hunyuan3D 2.5** | 2025-06-23 (arXiv 2506.16504) | **Closed** — API/platform only | New shape foundation model **LATTICE**, up to **10B params**. PBR paint extended from 2.0 Paint. |
| **Hunyuan3D-PolyGen** (1.0) | ~2025-07-08 | **Closed** | "Art-grade" **autoregressive mesh generation / intelligent retopology** producing quad-dominant topology. This is where quads come from — *not* from open 2.1. |
| HunyuanWorld-1.0 | 2025-07-26 | Open weights | Scene/world generation, not object generation. Separate track. |
| **Hunyuan3D Studio** | 2025-09-16 (arXiv 2509.12815) | Platform | End-to-end pipeline: Part-level 3D Generation + Polygon Generation + Semantic UV + PBR texturing. |
| **Hunyuan3D-Part** (P3-SAM + X-Part) | 2025-09-23 | **Open weights** (light version) | Native 3D part segmentation (P3-SAM) + structure-coherent part decomposition (X-Part). Full X-Part is Studio-only. |
| **Hunyuan3D-Omni** | 2025-09-25 | **Open weights** | "ControlNet of 3D" built on 2.1: adds bbox / skeletal pose / point-cloud / voxel control. 3.3B, 10 GB VRAM. |
| **Hunyuan3D 3.0** | 2025-09-16 announced | **Closed** | Hierarchical 3D-DiT, **1536³ geometry resolution**, "3.6B voxel" modelling units, claimed 3x accuracy vs prior. 4K PBR. |
| Hunyuan 3D Engine global launch | 2025-11-26 | Platform | `3d.hunyuanglobal.com`. 20 free generations/day for individuals; 200 free credits for Tencent Cloud API users. |
| **Hunyuan 3D 3.1** | ~Feb 2026 `[UNVERIFIED exact date]` | **Closed** | Live on Replicate (`tencent/hunyuan-3d-3.1`, created "5 months ago" as of Jul 2026 → ~Feb 2026) and resellers. Reported: faster inference, improved geometric precision, adds `top`/`bottom`/`left_front`/`right_front` multi-view input types. Sketch mode remains 3.0-only. |
| **HY3D-Bench** | **2026-02-04** | **Open data** | 252K+ watertight meshes (~11 TB), 240K+ part-decomposed objects (~5.0 TB), 125K+ synthetic objects across 1,252 categories (~6.5 TB). Baseline: `Hunyuan3D-Shape-v2-1 Small`, 0.8B DiT. |

**Current state as of July 2026:** the newest *open* artefact in the Hunyuan3D object-generation line is **HY3D-Bench (Feb 2026)** — a dataset, not a model. The newest *open model* remains **Hunyuan3D-Omni (Sept 2025)**, itself built on 2.1. The newest *product* is **Hunyuan 3D 3.1**. There is no `Tencent-Hunyuan/Hunyuan3D-3.0` repo. `[UNVERIFIED]`: whether a 3.x technical report exists on arXiv — I found none; 3.0's specs come from Tencent's own X/press posts and secondary coverage.

An issue on the 2.1 repo (#111, "Inquiry: Open-Source Plans for Hunyuan3D-2.5 and Hunyuan3D-PolyGen") documents the community asking for these; no release followed.

---

## 2. Architecture (the important part)

### 2.1 Overall shape of the system

Two independent stages, joined only by a mesh:

```
image (or text→image)
   │
   ├─ [pre] background removal, recenter, resize, white fill
   │
   ▼
STAGE 1 — SHAPE
   Hunyuan3D-ShapeVAE      (latent vector-set autoencoder, SDF decoder)
   Hunyuan3D-DiT           (flow-matching diffusion transformer in VAE latent space)
   → marching cubes → triangle mesh (untextured, watertight)
   │
   ▼
STAGE 2 — TEXTURE
   [pre] image delighting  (Hunyuan3D-Delight, i2i, removes baked lighting)
   Hunyuan3D-Paint         (geometry-conditioned multi-view diffusion, SD2.1 backbone)
   → dense-view inference → super-resolution → UV unwrap/bake → inpaint
   → texture set (2.0: RGB;  2.1: albedo + metallic + roughness)
```

The two stages are genuinely decoupled: **Hunyuan3D-Paint can texture any mesh**, including hand-authored ones, driven by an arbitrary image or text prompt (the paper calls the swap-image case "re-skinning"). For a Blender pipeline this is the more interesting half — you can bring your own topology.

### 2.2 The 3D representation: latent *vector sets*, decoded to SDF

This is the design choice that most affects output quality, so it's worth being precise.

From the 2.0 paper: *"Hunyuan3D-ShapeVAE employs vector sets as the compact neural representations of 3D shapes."* The lineage is 3DShape2VecSet → Michelangelo → Dora → CLAY.

A vector set (a.k.a. "vecset" or "latent set") is an **unordered 1-D sequence of latent tokens** — *not* a triplane, *not* a voxel grid, *not* a sparse volume. The paper is explicit about the consequence:

> "we omit the positional embedding of the latent sequence as the specific latent token of our ShapeVAE in the sequence does not correspond to a fixed location in the 3D grid. Instead, the content of our 3D latent tokens themselves is responsible for figuring out the position/occupancy of the generated shape"

**Why this matters for engineering decisions:**

- **Resolution is decoupled from latent size.** The decoder is a *point perceiver*: you hand it an arbitrary query grid `Q_g ∈ R^(H×W×D)×3` and it returns SDF values. So `octree_resolution` at inference is a pure quality/time/VRAM knob — you can raise it without retraining, unlike a voxel/triplane model. This is exactly the knob blender-mcp exposes.
- **No spatial prior = better global coherence, weaker local locality.** The 2.0 related-work section concedes structured representations (triplane, sparse volume) "better preserve spatial priors" — the trade Tencent made is efficiency and detail-per-token.
- **Output is an SDF → watertight, holeless meshes.** Good for booleans, 3D printing, physics. Bad if you wanted open surfaces (cloth, foliage planes, single-sided geometry) — you will get a shelled solid.
- **Contrast with TRELLIS**, which uses structured latents over a sparse voxel grid and can emit Gaussian splats / radiance fields; Hunyuan3D is mesh-only by construction.
- Note that 3.0's marketing language ("1536³ geometric resolution", "3.6B voxel") suggests the closed 3.x line may have moved to a **sparse-voxel / hierarchical** representation. `[UNVERIFIED]` — no paper.

### 2.3 Hunyuan3D-ShapeVAE

**What it encodes.** Not the mesh. It encodes a **point cloud sampled from the mesh surface, with per-point normals** — 3D coordinates + normal vectors as encoder input. The decoder is trained to predict the **Signed Distance Function** of the shape.

**Importance sampling** — the paper's headline VAE contribution:

> "in addition to uniformly sampled point clouds, we designed an importance sampling method that samples more points on the edges and corners of the mesh, which provides more complete information for describing complex regions."

Mechanically:
1. Sample uniform surface points `P_u ∈ R^(M×3)` **and** importance points `P_i ∈ R^(N×3)` (edge/corner-biased).
2. Run **Farthest Point Sampling separately** on each to get point queries `Q_u`, `Q_i`. (Separately is load-bearing — joint FPS would let the dense edge samples starve the uniform ones.)
3. Concatenate → `P`, `Q`. Fourier positional encoding + linear projection.
4. One **cross-attention** layer compresses `P` into the `Q` queries, then a stack of self-attention layers.
5. Linear heads produce mean and variance of the latent `Z_s` (it is a proper VAE, KL-regularised).

The paper notes concurrent work (Dora) arrived at the same idea independently.

**Decoder.** projection `d_0 → d` → self-attention stack → point perceiver against a 3D query grid → linear head → SDF → marching cubes.

**Losses.** `L_r = E_x[ MSE(D_s(x|Z_s), SDF(x)) ] + γ·L_KL`, with reconstruction MSE estimated on randomly sampled space + surface points (full dense SDF is too expensive).

**Latent size.** Multi-resolution training: token-sequence length sampled from a predefined set. **Maximum sequence length = 3072** in both the 2.0 and 2.1 released versions. Shorter = cheaper, longer = sharper. Note the comparison table in 2.0 evaluates competitors at 1024 tokens because Direct3D's triplane "requires a 3072 token length (suffering significant performance degeneration when reducing token length)" — i.e. the vecset representation is more token-efficient.

**Reconstruction quality (2.0 paper, Table 1):**

| | V-IoU ↑ | S-IoU ↑ |
|---|---|---|
| 3DShape2VecSet | 87.88% | 80.66% |
| Michelangelo | 84.93% | 76.27% |
| Direct3D | 88.43% | 81.55% |
| **Hunyuan3D-ShapeVAE** | **93.6%** | **89.16%** |

### 2.4 Hunyuan3D-DiT

**Objective: flow matching, not DDPM.** Explicitly:

> "We utilize flow matching objective for training our model... we adopt the affine path with the conditional optimal transport schedule... `x_t = (1-t)x_0 + t·x_1`, `u_t = x_1 - x_0`"

Loss: `L = E[ ‖u_θ(x_t, c, t) − u_t‖² ]`. Inference: sample `x_0 ~ N(0,1)`, integrate with a **first-order Euler ODE solver**. Practical consequences: few-step sampling works well (hence Turbo at ~5 steps), and `num_inference_steps` behaves like an ODE step count, not a noise schedule — 20–50 for quality, 5 for turbo.

**Conditioning encoder: DINOv2, not CLIP.** Both papers:

> "we utilize a large image encoder – **DINOv2 Giant** and large input image size – **518×518**"

DINOv2-G is a self-supervised *spatial* feature extractor; CLIP is semantic/global. For geometry following you want dense patch features — the paper takes "the patch sequence including the head token at the last layer". This is why Hunyuan3D reproduces fine surface bumps (piano keys, calculator buttons, logo text) better than CLIP-conditioned models. Preprocessing (background removal, centering, unified size, white fill) is described as materially improving effective resolution.

**Block structure — and it changed between versions:**

- **2.0:** FLUX-inspired **dual-stream + single-stream** transformer. Dual-stream blocks give latent and condition tokens separate QKV/MLP but a shared attention; single-stream blocks concatenate them. Modulation from timestep embedding only. No positional embedding on the latent sequence.
- **2.1:** restructured, citing Hunyuan-DiT and TripoSG — **21 transformer layers**, **dimension-concatenation skip connections** on the latent code, **cross-attention** for image conditioning, plus an **MoE layer**. 3.3B params (vs 1.1B in 2.0).

**Guidance.** Classifier-free guidance, exposed as `guidance_scale`. The 2.0 "Fast" variants are **guidance-distilled** (fold CFG into one forward pass, ~2x); the "Turbo" variants add **step distillation** (FlashVDM's Progressive Flow Distillation, down to 5 steps). Note that distilled models largely ignore `guidance_scale` — a common source of confusion when wiring these knobs into an agent.

### 2.5 Hunyuan3D-Paint — and the PBR question

**This differs by version. Be precise:**

| Version | Output maps | Notes |
|---|---|---|
| 1.0 | RGB texture | via multi-view recon |
| **2.0** | **RGB / albedo-like only** | Delighting makes it "lighting-invariant", but there is **no metallic and no roughness map**. |
| **2.1** | **albedo + metallic + roughness** | Disney Principled BRDF. |
| 2.5 / 3.x (closed) | 4K PBR | plus normal `[UNVERIFIED]` |

Note carefully: **none of the open versions generate a normal/bump map.** 2.1's paper says "we adhere to the BRDF model and simultaneously output **albedo, roughness, and metallic** maps." Surface detail lives in the geometry, not in a normal map. If your Blender shader graph expects a 4-map PBR set, you will be synthesising or baking the normal map yourself.

**2.0 Paint pipeline (the base everything builds on):**

1. **Image delighting.** A dedicated i2i model (`Hunyuan3D-Delight-v2-0`, 1.3B) trained on pairs rendered under random HDRI vs even white light. Removes baked shadows so the multi-view model — trained entirely on white-light renders — produces illumination-invariant textures.
2. **View selection.** Geometry-aware greedy search. 4 fixed orthogonal views as basis, then iteratively add the view maximising *new* UV-texel coverage, up to `N_max = 12`. So **8–12 viewpoints** for inference.
3. **Double-stream image-conditioning ReferenceNet.** The raw (noiseless) VAE feature of the reference image is fed into a reference branch with **timestep pinned to 0**, and the branch uses **frozen original SD2.1 weights**. The freeze is deliberate: it "serves as a soft regularization that anchors the generated image distribution, preventing it from drifting away towards the rendered image distribution" — i.e. it stops the model from making everything look like an Objaverse render.
4. **Multi-task attention (view consistency).** Three attention paths in **parallel** (not serial, to avoid interference):
   `Z_MVA = Z_SA + λ_ref · Attn_ref + λ_mv · Attn_mv`
   where `Z_SA` is the frozen self-attention, `Attn_ref` injects the reference image, `Attn_mv` enforces cross-view consistency.
5. **Geometry conditioning.** Multi-view **canonical normal maps** and **canonical coordinate maps (CCM)** are VAE-encoded and **channel-concatenated with the latent noise** into a widened input conv. Plus a **learnable camera/view embedding** (integer per predefined viewpoint → embedding vector). The paper reports geometry conditioning + learnable camera embedding together give the best result.
6. **Dense-view inference.** Trained with **view dropout**: 6 views randomly drawn from **44 preset viewpoints** per batch. At inference the model can emit any requested viewpoint — dense coverage reduces self-occlusion holes so the inpainting stage has less to do.
7. **Super-resolution** per view (single-image SR; the paper claims it doesn't break cross-view consistency because it introduces little variation).
8. **Baking + inpainting.** Views are unwrapped into the UV map. Remaining uncovered texels are filled by projecting UV texture → vertex colours, then querying each texel as an **inverse-geometric-distance weighted sum** of connected textured vertices. Cheap, and it shows: this is a diffusion-free hole fill, so occluded cavities come out soft.
9. Training: from the **ZSNR checkpoint of Stable Diffusion 2 (v-model)**, at **512×512**, 80k steps, batch 48, lr 5e-5.

**2.1 Paint additions (the PBR upgrade):**

- **Disney Principled BRDF** target; albedo + metallic + roughness generated *simultaneously* across views.
- **Spatial-Aligned Multi-Attention.** A **parallel dual-branch UNet** — one branch for albedo, one for the packed metallic-roughness (MR) map — each with self / multi-view / reference attention. Crucially, the **output of the albedo reference-attention is propagated directly into the MR branch**, which is what keeps MR spatially registered to albedo (misregistration between albedo and roughness is the classic failure mode of naive multi-map generation).
- **3D-Aware RoPE** injects spatial information into attention, "significantly improving cross-view consistency and enabling seamless texturing." This replaces/augments the learnable camera embedding of 2.0.
- **Illumination-invariant training.** Two sets of training samples of the same object rendered under *different* lighting; a **consistency loss** forces identical intrinsic material output. This is stronger than 2.0's delight-then-generate approach.
- Training data: **70k+ human-annotated** assets filtered from Objaverse / Objaverse-XL; 4 elevations (−20°, 0°, 20°, random) × 24 azimuths, rendering albedo/metallic/roughness + HDR and point-light images at 512×512.

### 2.6 Mesh extraction, and the topology reality

**Extraction: isosurfacing from the decoded SDF field.** Two extractors ship in 2.1 (`hy3dshape/models/autoencoders/surface_extractors.py`):

- `MCSurfaceExtractor` — `skimage.measure.marching_cubes`. Default (`mc_algo='mc'`).
- `DMCSurfaceExtractor` — **differentiable dual marching cubes** via `diso.DiffDMC`, optional (`pip install diso`), selected with `mc_algo='dmc'`. Generally cleaner surfaces.

**No quads.** The DMC call is `self.dmc(sdf, deform=None, return_quads=False, normalize=True)` — quads are explicitly disabled. **There is no remeshing, no retopology, and no quad output anywhere in the open-source Hunyuan3D 2.x pipeline.** You get dense, isotropic, marching-cubes triangle soup with a UV atlas from `xatlas`.

That is precisely the gap **Hunyuan3D-PolyGen** fills — a self-developed **autoregressive mesh generation** model that emits artist-style, quad-dominant topology, marketed as "intelligent retopology". **PolyGen is closed.** It is available only through Hunyuan 3D Studio / the cloud API / resellers (Scenario lists "Hunyuan PolyGen 1.5", input high-poly GLB/OBJ, output quad-dominant with multiple reduction levels).

**Practical implication for a Blender pipeline:** if you use open-source 2.1 locally, budget a retopology step of your own — Blender's Quadriflow/Voxel remesh, Instant Meshes, or a decimate+shrinkwrap pass. Do not expect game-ready topology out of the box.

### 2.7 2.1+ additions summary

- PBR material synthesis (§2.5) — **2.1**, open.
- Part-level generation — **Hunyuan3D-Part** (P3-SAM segmentation + X-Part decomposition), Sept 2025, open but "a light version of X-Part"; full version Studio-only. Useful if you want per-part materials or separable objects in Blender.
- Multi-condition control — **Hunyuan3D-Omni**, Sept 2025, open. Bounding box, skeletal pose, point cloud, voxel. Built on 2.1's 3.3B backbone, 10 GB VRAM. This is the most directly useful open addition for a *directed* pipeline (e.g. "generate a character matching this rig pose").
- Higher resolution — 2.5 (LATTICE, 10B) and 3.0 (1536³ hierarchical 3D-DiT). Both closed.
- Retopology — PolyGen. Closed.
- Semantic UV — Studio. Closed.

---

## 3. Open source status and license

### 3.1 What weights are actually released

| Repo / HF | Weights | License file |
|---|---|---|
| `Tencent-Hunyuan/Hunyuan3D-1` | lite + std, multiview + recon | Tencent Hunyuan Community |
| `tencent/Hunyuan3D-2` | dit-v2-0 (1.1B), -fast, -turbo, paint-v2-0 (1.3B), paint-v2-0-turbo, delight-v2-0 (1.3B) | Tencent Hunyuan 3D 2.0 Community |
| `tencent/Hunyuan3D-2mini` | dit-v2-mini / -fast / -turbo (0.6B) | same |
| `tencent/Hunyuan3D-2mv` | dit-v2-mv / -fast / -turbo (1.1B) | same |
| `tencent/Hunyuan3D-2.1` | **Hunyuan3D-Shape-v2-1 (3.3B)**, **Hunyuan3D-Paint-v2-1 (2B)**, + VAE encoder + **training code** | **Tencent Hunyuan 3D 2.1 Community** |
| `tencent/Hunyuan3D-Omni` | 3.3B controllable | Tencent Hunyuan Community `[UNVERIFIED — no LICENSE at repo root main branch; 404]` |
| `tencent/Hunyuan3D-Part` | P3-SAM + X-Part (light) | **Tencent Hunyuan 3D-Part Community**, release date 2025-09-23 |
| `Tencent-Hunyuan/HY3D-Bench` | datasets (~22.5 TB) + 0.8B baseline | reuses **Tencent Hunyuan 3D 2.1 Community** license text |
| **Not released** | 2.5 / LATTICE, PolyGen, Semantic UV, 3.0, 3.1, full X-Part | — |

Note the README size table and the model-zoo table disagree slightly for 2.1 (README lists Shape 3.3B / Paint 2B; the 2.0 repo's zoo table lists `Hunyuan3D-DiT-v2-1` as 3.0B and `Hunyuan3D-Paint-v2-1` as 1.3B). Treat ~3B / ~2B as the working figures.

**The papers themselves are CC-BY-4.0 on arXiv. The weights are not.**

### 3.2 The Tencent Hunyuan 3D 2.1 Community License — actual terms

Read from `https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE`. Direct quotes:

**Header (all caps in the original):**
> "TENCENT HUNYUAN 3D 2.1 COMMUNITY LICENSE AGREEMENT
> Tencent Hunyuan 3D 2.1 Release Date: June 13, 2025
> **THIS LICENSE AGREEMENT DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND SOUTH KOREA AND IS EXPRESSLY LIMITED TO THE TERRITORY, AS DEFINED BELOW.**"

**Territory (§1.l):**
> "'Territory' shall mean the worldwide territory, **excluding the territory of the European Union, United Kingdom and South Korea**."

**Grant (§2):**
> "We grant You, **for the Territory only**, a non-exclusive, non-transferable and royalty-free limited license... to use, reproduce, distribute, create derivative works of (including Model Derivatives), and make modifications to the Materials"

**§5.c — this is the one people miss:**
> "You must not use, reproduce, modify, distribute, or display the Tencent Hunyuan 3D 2.1 Works, **Output or results** of the Tencent Hunyuan 3D 2.1 Works **outside the Territory**. Any such use outside the Territory is unlicensed and unauthorized under this Agreement."

So it is not merely that an EU/UK/KR entity may not run the model — **the generated 3D assets themselves may not be used or displayed in the EU, UK or South Korea**. For a Blender asset pipeline whose output might ship in a game or product sold in Europe, this is a hard blocker on the open weights. (Whether such a term is enforceable against downstream Outputs is a legal question, not a technical one — take advice. Note §6.d says "Tencent claims no rights in Outputs You generate", which sits in tension with §5.c; I am not qualified to reconcile them.)

**§4 — commercial MAU trigger:**
> "If, **on the Tencent Hunyuan 3D 2.1 version release date**, the monthly active users of all products or services made available by or for Licensee is greater than **1 million monthly active users** in the preceding calendar month, You must request a license from Tencent, which Tencent may grant to You **in its sole discretion**"

Note the timing quirk: the test is applied **as of the release date (13 June 2025)**, not continuously. If you were under 1M MAU in May 2025, growing past it later does not by its literal terms trigger §4. Licence requests go to `hunyuan3d@tencent.com` with company name/sector, intended use case, and modification plans.

**Below 1M MAU, commercial use is permitted and royalty-free**, subject to everything else.

**Distribution conditions (§3):** pass the Agreement to recipients; mark modified files; ship a NOTICE file reading *"Tencent Hunyuan 3D 2.1 is licensed under the Tencent Hunyuan 3D 2.1 Community License Agreement, Copyright © 2025 Tencent. All Rights Reserved."*; **encouraged (not required)** to publish a blog post and mark products "Powered by Tencent Hunyuan". §3.e requires you to prominently disclose your own legal identity as the provider and state that Tencent is not affiliated/endorsing.

**§5.b — no model-improvement clause:**
> "You must not use the Tencent Hunyuan 3D 2.1 Works or any Output or results... **to improve any other AI model** (other than Tencent Hunyuan 3D 2.1 or Model Derivatives thereof)."

Broad: it covers Outputs, so you cannot train a competing 3D generator on Hunyuan-generated meshes.

**Other:** §6.c patent-retaliation termination + indemnity; §7 as-is, no support obligation; §9 **governed by Hong Kong SAR law, exclusive Hong Kong jurisdiction**.

**Acceptable Use Policy (Exhibit A, last modified 2024-11-05)** — 20+ prohibitions. Item 1 is literally "Outside the Territory". Notable ones for a production pipeline: no undisclosed machine-generated content in public contexts (item 12); no high-stakes automated decisions (item 14); "In a manner that violates or disrespects the social ethics and moral standards of other countries or regions" (item 15) — vague and unilaterally updatable ("Tencent reserves the right to update this Acceptable Use Policy from time to time").

**Note on entity:** the licence records that "THL A29 Limited" (the old licensor) "has now been de-registered" and instructs treating all prior copies as licensed by "the applicable entity or entities in the Tencent corporate family."

**Summary judgement:** this is a source-available, geographically-restricted, use-restricted licence. Calling it "open source" is inaccurate. It fails the OSD on fields-of-use and geography. For a US/UK-ambiguous or EU-facing project, **use the cloud API instead** (whose terms are separate) or pick TRELLIS (MIT) / another permissively-licensed model.

---

## 4. Local deployment reality

### 4.1 VRAM

From the official READMEs:

| Version | Shape | Texture | Total |
|---|---|---|---|
| **Hunyuan3D 2.0** | **6 GB** | — | **16 GB** (shape + texture) |
| **Hunyuan3D 2.1** | **10 GB** | **21 GB** | **29 GB** |
| Hunyuan3D-Omni | **10 GB** | (uses 2.1 paint) | — |

2.1's PBR dual-branch UNet roughly doubled the texture-stage footprint. **29 GB means a single 24 GB card (4090/3090) cannot run 2.1 end-to-end without offloading.** Community work exists — `deepbeepmeep/Hunyuan3D-2GP` ("GPU Poor Version") targets low-VRAM configs `[UNVERIFIED specific VRAM floor]`.

### 4.2 Inference time

| Config | Time | Source |
|---|---|---|
| 2.0 shape, 4090 Mobile | ~35 s | community (MrForExample) |
| 2.0 shape+texture, 4090 Mobile | ~1 min total (35 s shape + 30 s MV+projection) | same |
| **2.0-Turbo shape, 4090** | **~1 s** | FlashVDM / Tencent |
| FlashVDM speedups | >45x reconstruction, 32x generation; ≥5-step sampling | arXiv 2503.16302 |
| **2.1 full (shape+PBR texture), RTX 4090** | **median 139.2 s** (~2.3 min) over 900+ generations | **SaladCloud, independent** |
| 3.0 Pro (cloud) | ~90 s | Scenario |

The Salad number is the most trustworthy figure here — large N, independent, on the actual 2.1 ComfyUI node.

### 4.3 Apple Silicon / macOS — the honest answer

The 2.1 README claims "Hunyuan3D 2.1 supports Macos, Windows, Linux", but the install instructions immediately require `torch==2.5.1+cu124` and then build two native extensions:

```
cd hy3dpaint/custom_rasterizer && pip install -e .
cd hy3dpaint/DifferentiableRenderer && bash compile_mesh_painter.sh
```

Both are CUDA-oriented. In practice:

The community macOS port (`Brainkeys/Hunyuan3D-2.1-mac`) documents the real situation:
- **Shape generation works on MPS** — "~5-10x slower than CUDA", **2–5 minutes** per shape.
- **Texture generation is "Limited"** — requires xatlas and has reduced functionality; the **custom rasterizer "uses CPU fallback", bypassing GPU acceleration entirely**.
- Overall "5–15x slower" than CUDA.
- **8–16 GB RAM minimum, 16 GB+ recommended**; ~4 GB during shape, ~8 GB during texture; 10 GB+ disk.
- Python 3.11–3.12 (3.13 incompatible).

**Verdict for a MacBook Pro:** a shape-only local workflow is technically possible (minutes per mesh, unified memory permitting), but the PBR texture stage — the thing that makes 2.1 worth using over 2.0 — is effectively crippled. **Do not architect the Blender pipeline around local Mac inference.** Use the cloud API (blender-mcp's `OFFICIAL_API` mode) or a remote GPU box exposing `api_server.py` (blender-mcp's `LOCAL_API` mode pointed at a LAN/tunnelled host).

### 4.4 ComfyUI

- **Native (core ComfyUI), since 2025-03-22:** Hunyuan3D 2.0, 2.0-MV, and 2mv-turbo. Geometry + texture; output to `ComfyUI/output/mesh`, previewable with the `Load 3D` node. Three shipped workflows (multiview, multiview-turbo, single-image).
- **2.1 (PBR) is community-only:** `visualbruno/ComfyUI-Hunyuan3d-2-1` — this is the node Tencent itself lists first on its "Community Contribution Leaderboard", and it's what SaladCloud benchmarked.
- Other wrappers: `ComfyUI-3D-Pack`, `ComfyUI-Hunyuan3DWrapper`, and `PozzettiAndrea/ComfyUI-HunyuanX` for Hunyuan3D-Omni.

### 4.5 Quantized / turbo / mini variants and their tradeoffs

| Variant | Params | Technique | Trade |
|---|---|---|---|
| `dit-v2-0` | 1.1B | baseline, ~50 steps | quality reference for 2.x |
| `dit-v2-0-fast` | 1.1B | **guidance distillation** | ~2x faster; CFG folded in, so `guidance_scale` becomes inert |
| `dit-v2-0-turbo` | 1.1B | **step distillation** (FlashVDM) | ~1 s on a 4090; some loss of fine detail and prompt adherence at extremes |
| `dit-v2-mini` / `-fast` / `-turbo` | **0.6B** | smaller backbone | lowest VRAM; noticeably weaker on complex/thin structures |
| `dit-v2-mv` / `-fast` / `-turbo` | 1.1B | **multi-view conditioned** | best geometry when you have 4 consistent views; useless from one image |
| `paint-v2-0-turbo` | 1.3B | distilled texture | faster texturing, RGB only |
| `Shape-v2-1` | 3.3B | 2.1 backbone | best open geometry; 10 GB |
| `Paint-v2-1` | 2B | PBR | 21 GB; the expensive one |
| `Shape-v2-1 Small` | **0.8B** | HY3D-Bench baseline (Feb 2026) | research baseline, not a product |

`[UNVERIFIED]`: I found no official INT8/FP8/GGUF quantisations from Tencent. Community quantisation exists in the ComfyUI ecosystem but I could not confirm specific quality-vs-VRAM numbers.

---

## 5. Cloud API

### 5.1 Official — Tencent Cloud

**Yes, and it is available internationally.** Two front doors:

1. **Consumer/creator:** `3d.hunyuanglobal.com` — global engine launched **2025-11-26**. "20 free generations daily" for individuals. Text-to-3D, image-to-3D (up to four multi-view images), sketch-to-3D, smart topology optimisation. Exports **OBJ and GLB**; Unity / Unreal / Blender compatible.
2. **Developer:** Tencent Cloud API. Actions include **`SubmitHunyuanTo3DJob`** / **`QueryHunyuanTo3DJob`** (service `hunyuan`, version `2023-09-01`, region `ap-guangzhou`) and a **`SubmitHunyuanTo3DProJob`** on the international docs site (`tencentcloud.com/document/product/1284/`). Enterprise API users get **200 free credits**.

**Pricing (Tencent Hunyuan 3D Global Purchase Guide, official PDF):**

Prepaid credit packs, 1-year validity:

| Credits | Price |
|---|---|
| 1,000 | **$15** |
| 10,000 | **$145** |
| 50,000 | **$700** |
| 100,000 | **$1,350** |

Postpaid (daily settlement): **$0.02 per credit** for the Professional API.

Credit cost per generation (Professional API):

| Feature | Credits |
|---|---|
| Normal (textured model) | 25 |
| Geometry only (untextured) | 15 |
| LowPoly | 30 |
| + PBR | +10 |
| + multi-view images | +10 |
| **Express API** | **15 per call** |

So a textured+PBR Pro generation ≈ 35 credits ≈ **$0.70** postpaid, or ~$0.53 at the 10k-pack rate, or ~$0.47 at the 100k rate. Free tier: **200 credits/user**, valid one year. Failed calls are not charged. 7-day unconditional refund on unused packs. **Concurrency is the sting: default 3 concurrent tasks (Professional) / 1 (Express), and additional concurrency is $5,000/month per slot.**

**Usable from outside China:** yes — the international console (`tencentcloud.com`) sells this in USD and the global engine is explicitly a worldwide launch. `[UNVERIFIED]`: whether the API terms of service impose the same EU/UK/KR territory exclusion as the open-weight licence. The API is a separate contract; **verify before relying on it from Europe.** Note also that blender-mcp hardcodes `region = "ap-guangzhou"` — a mainland-China region — which will add latency from Europe/US and may matter for data-residency policies.

### 5.2 Third-party hosts

| Host | Model | Price | Notes |
|---|---|---|---|
| **fal.ai** | `fal-ai/hunyuan3d-v3/text-to-3d` | **$0.375** Normal / **$0.45** LowPoly / **$0.225** Geometry; **+$0.15** PBR; **+$0.15** multi-view; **+$0.15** custom face count | GLB + OBJ + thumbnail. Most expensive per unit but simplest API. |
| fal.ai | `fal-ai/hunyuan3d/v2`, `/v2/turbo`, `/v2/mini` | `[UNVERIFIED per-call price]` | Older 2.x endpoints still live |
| **Replicate** | `tencent/hunyuan-3d-3.1` | `[UNVERIFIED — page did not expose per-run price]` | 74k+ runs; text-to-3D and image-to-3D |
| **Atlas Cloud** | Hunyuan 3D Rapid / Pro, image + text | **"from $0.02"** per generation; Rapid 2–3 min latency, Pro 3–6 min, 40K–1.5M faces, 4K PBR | Cheapest listed |
| **3D AI Studio** | Hunyuan 3D 3.0 + 3.1 | Pro 60 credits base, +20 PBR, +20 multi-view (max 100); Rapid 35 base, +20 PBR (max 55); credits expire 365 days | Exposes 3.1's extra view types |
| **SaladCloud** | self-hosted 2.1 on their fleet | **$0.0148** high-priority / **$0.009** batch per generation | Independent; claims ">90% less than FAL's Hunyuan 3D 2.0 endpoint" |
| **Scenario** | Hunyuan 3D 3.0/3.1 Pro, PolyGen 1.5, Part | `[UNVERIFIED pricing]` | One of the few places PolyGen retopology is reachable |
| WaveSpeedAI, Segmind, Pixio | 2.x variants incl. Mini | `[UNVERIFIED]` | — |

**Cost sanity check:** self-hosting 2.1 on rented GPUs lands around **$0.01–0.015/generation**; managed APIs run **$0.02–0.70**. If your Blender pipeline is doing tens of assets a day, the API is unambiguously cheaper than the engineering time. At thousands/day, self-host.

---

## 6. Quality vs competitors

### 6.1 Self-reported (weight these low — Tencent picked the baselines and the metrics)

**Shape generation, 2.1 paper Table 1** (ULIP/Uni3D similarity between generated mesh point cloud and image/VLM-caption):

| Model | ULIP-T ↑ | ULIP-I ↑ | Uni3D-T ↑ | Uni3D-I ↑ |
|---|---|---|---|---|
| Michelangelo | 0.0752 | 0.1152 | 0.2133 | 0.2611 |
| Craftsman 1.5 | 0.0745 | 0.1296 | 0.2375 | 0.2987 |
| TripoSG | 0.0767 | 0.1225 | 0.2506 | 0.3129 |
| Step1X-3D | 0.0735 | 0.1183 | 0.2554 | 0.3195 |
| **TRELLIS** | 0.0769 | 0.1267 | 0.2496 | 0.3116 |
| Direct3D-S2 | 0.0706 | 0.1134 | 0.2346 | 0.2930 |
| **Hunyuan3D-DiT (2.1)** | **0.0774** | **0.1395** | **0.2556** | **0.3213** |

**Texture synthesis, 2.1 paper Table 2** (image-to-texture):

| Method | CLIP-FID ↓ | CMMD ↓ | CLIP-I ↑ | LPIPS ↓ |
|---|---|---|---|---|
| SyncMVD-IPA | 28.39 | 2.397 | 0.8823 | 0.1423 |
| TexGen | 28.24 | 2.448 | 0.8818 | 0.1331 |
| Hunyuan3D-2.0 | 26.44 | 2.318 | 0.8893 | 0.1261 |
| **Hunyuan3D-Paint (2.1)** | **24.78** | **2.191** | **0.9207** | **0.1211** |

**End-to-end textured assets, 2.0 paper Table 4** (competitors anonymised as "Model 1/2/3" — read that as commercial systems, likely Tripo/Meshy/Rodin-class, but Tencent does not say):

| | CMMD ↓ | FID_CLIP ↓ | FID_Incept ↓ | CLIP-score ↑ |
|---|---|---|---|---|
| TRELLIS | 3.591 | 54.639 | 289.287 | 0.787 |
| Model 1 | 3.600 | 55.866 | 305.922 | 0.779 |
| Model 2 | 3.368 | 49.744 | 294.628 | 0.806 |
| Model 3 | 3.218 | 51.574 | 295.691 | 0.799 |
| **Hunyuan3D 2.0** | **3.193** | **49.165** | **282.429** | **0.809** |

Margins here are thin — 2.0 beats "Model 3" by 0.025 CMMD and 0.010 CLIP-score. The 2.1 shape table's ULIP-I gap (0.1395 vs 0.1267 for TRELLIS) is the largest single margin claimed, and ULIP-I is a point-cloud/image embedding similarity — a proxy for *image following*, not for mesh usability.

**User study (2.0 paper):** 50 volunteers, 300 unselected results, three criteria (visual quality, image-condition adherence, overall satisfaction). Reported as favouring Hunyuan3D 2.0, "particularly in its ability to adhere to image conditions." No numbers in the extracted table; figure-only.

### 6.2 Independent — 3D Arena (arXiv 2506.18787)

This is the best independent evidence available: an open crowdsourced pairwise-comparison arena, ELO-ranked, 123k+ votes, snapshot 30 May 2025. Anonymous side-by-side, so no brand bias.

| Rank | Model | ELO | Votes | Win rate | Format |
|---|---|---|---|---|---|
| 1 | CSM/Cube | 1405 | 3,027 | 83.3% | Splat |
| 2 | TRELLIS-3DGS | 1384 | 3,648 | 80.1% | Splat |
| 3 | Strawberrry (anon) | 1382 | 4,892 | 80.9% | Mesh |
| 4 | Strawb3rry (anon) | 1370 | 5,121 | 79.4% | Mesh |
| 5 | **TRELLIS** | **1306** | 4,877 | 67.0% | Mesh |
| 6 | Zaohaowu3D | 1302 | 582 | 64.8% | Mesh |
| **7** | **Hunyuan3D-2** | **1298** | **4,195** | **65.5%** | **Mesh** |
| 8 | InstantMesh | 1278 | 10,575 | 63.8% | Mesh |
| 9 | **Meshy** | 1243 | 7,023 | 58.1% | Mesh |
| 10 | Unique3D | 1230 | 8,959 | 55.1% | Mesh |
| 11 | Hi3DGen | 1207 | 1,565 | 47.7% | Mesh |
| 12 | MeshFormer | 1192 | 5,394 | 48.6% | Mesh |
| 13 | SF3D | 1190 | 6,267 | 48.4% | Mesh |
| 14 | Real3D | 1158 | 8,541 | — | Mesh |

**Reading this honestly:**
- Hunyuan3D-2 sits at **1298, essentially tied with TRELLIS-mesh (1306)** — 8 ELO apart is noise at these vote counts. It is **not** the clear winner the papers imply, but it is comfortably ahead of Meshy (1243).
- The arena tested **Hunyuan3D-2.0**, not 2.1, and not 2.5/3.x. The gap has almost certainly moved since May 2025.
- **Tripo and Rodin are absent** from this leaderboard. I could not find an independent, quantitative head-to-head of Hunyuan3D vs Tripo or Rodin. `[UNVERIFIED]`
- The paper's own caveat is important and cuts against naive reading: **Gaussian splats enjoy a +16.6 ELO presentation advantage over meshes**, and textured models a **+144.1 ELO** advantage over untextured — a controlled TRELLIS splat-vs-mesh comparison showed **+78 ELO for the same underlying model** purely from format. The authors conclude "voting patterns systematically favor visual impact through vibrant rendering and aesthetic appeal over downstream utility... despite widespread industry recognition that clean mesh topology is essential for professional workflows." **Arena ELO is a poor proxy for the thing a Blender pipeline actually needs.**

### 6.3 Independent — qualitative (Scenario's model guide, a vendor-neutral host offering all of them)

- **Hunyuan 3D 3.0 Pro** — "ultra-HD fidelity and production-ready assets", 1024 geometry resolution, 4K PBR, clean topology, ~90 s. Positioned as the **fidelity leader**.
- **Rodin Gen-2** — "scan-quality realism", **10B params, quad-based meshes**, ~60 s. Rodin's quad output is a real differentiator Hunyuan only matches via closed PolyGen.
- **Tripo 2.5** — photorealistic single-object, high-res textures, clean meshes, very fast. The balanced choice.
- **TRELLIS 2** — 4B diffusion, best on "complex topologies and stylized characters", supports transparency.
- **Meshy** — speed and a modular generate→refine→retexture→**rig** workflow. Meshy's rigging is something Hunyuan's open stack has no answer for.

Scenario explicitly declines to name an overall winner: "choose Hunyuan for maximum fidelity, Tripo for balanced speed-quality, Rodin for multi-view precision, or Meshy for rapid iteration."

### 6.4 Bottom line

- **Geometry fidelity / image adherence:** Hunyuan3D 2.1 is at or near the open-source state of the art; 3.x extends that lead but is closed.
- **Topology:** a clear weakness of open Hunyuan3D. Rodin (quads native) and Meshy (rigging) beat it on downstream usability.
- **Openness:** TRELLIS (MIT) is the meaningfully-open competitor. If licence risk matters more than a marginal quality edge, TRELLIS is the safer default.
- **PBR:** Hunyuan3D 2.1 is genuinely first-of-kind as a *fully open* PBR-generating pipeline, and this is its strongest differentiator for a Blender workflow.

---

## 7. What `ahujasid/blender-mcp` actually exposes

Two files matter: `src/blender_mcp/server.py` (the MCP server, 1,252 lines) and `addon.py` (the Blender-side socket addon, 2,883 lines).

### 7.1 The four MCP tools

**1. `get_hunyuan3d_status(ctx, user_prompt: str = "")`**
Returns a human-readable message. Reports whether the integration is enabled, which mode (`LOCAL_API` / `OFFICIAL_API`), and whether the needed credentials (SecretId/SecretKey for official, API URL for local) are present. Handler in addon: `get_hunyuan3d_status`.

**2. `generate_hunyuan3d_model(ctx, text_prompt: str = None, input_image_url: str = None, user_prompt: str = "")`**
Docstring: *"Generate 3D asset using Hunyuan3D by providing either text description, image reference, or both... The 3D asset has built-in materials."*
- `text_prompt` — "A short description of the desired model in English/Chinese."
- `input_image_url` — local path **or** remote URL. Local files are read and base64-encoded.
- Dispatches to `create_hunyuan_job` on the addon, which branches on mode.
- Returns `{"job_id": "job_<JobId>"}` on the official path.

**Important behavioural difference between modes, visible only in `addon.py`:**

| | `OFFICIAL_API` | `LOCAL_API` |
|---|---|---|
| Endpoint | Tencent Cloud, `service=hunyuan`, `action=SubmitHunyuanTo3DJob`, `version=2023-09-01`, **`region=ap-guangzhou`**, TC3 request signing | `POST {api_url}/generate` |
| Text + image together | **Rejected**: "Prompt and Image cannot be provided simultaneously" (contradicts the MCP docstring's "or both") | Allowed |
| Prompt limit | **200 characters**, enforced client-side | none |
| Batch | `Num: 1` — *"The current API limit is only 1"* | n/a |
| Extra params | **none exposed** — no octree/steps/guidance/PBR flag | `octree_resolution`, `num_inference_steps`, `guidance_scale`, `texture` |
| Return | async job → poll → ZIP of **OBJ** | synchronous; **GLB** bytes, written to a temp file and imported via `bpy.ops.import_scene.gltf` on a `bpy.app.timers` callback |
| Image field | `ImageUrl` or `ImageBase64` | `image` (always base64; remote URLs are downloaded first) |

**3. `poll_hunyuan_job_status(ctx, job_id: str = None)`**
Official path only (`QueryHunyuanTo3DJob`). Status `"RUN"` → in progress, `"DONE"` → complete. On `DONE` returns `ResultFile3Ds` containing the ZIP path of the OBJ model. The docstring warns it is a polling API — only proceed on a terminal state.

**4. `import_generated_asset_hunyuan(ctx, name: str, zip_file_url: str)`**
Downloads and imports the ZIP into the scene under `name`. Official path only.

### 7.2 Configuration surface (Blender UI / env vars)

Scene properties, registered in `addon.py`:

| Property | Type | Default | Range |
|---|---|---|---|
| `blendermcp_use_hunyuan3d` | bool | off | — |
| `blendermcp_hunyuan3d_mode` | enum | **`LOCAL_API`** | `LOCAL_API` \| `OFFICIAL_API` |
| `blendermcp_hunyuan3d_secret_id` / `_secret_key` | str | — | Tencent Cloud creds |
| `blendermcp_hunyuan3d_api_url` | str | — | local server base URL |
| `blendermcp_hunyuan3d_octree_resolution` | int | **256** | 128–512 |
| `blendermcp_hunyuan3d_num_inference_steps` | int | **20** | 20–50 |
| `blendermcp_hunyuan3d_guidance_scale` | float | **5.5** | 1.0–10.0 |
| `blendermcp_hunyuan3d_texture` | bool | **False** | — |

Env vars for headless/CI: `BLENDERMCP_HUNYUAN3D_SECRET_ID`, `BLENDERMCP_HUNYUAN3D_SECRET_KEY`, `BLENDERMCP_HUNYUAN3D_API_URL`.

**Critical gotcha:** these four generation parameters are **UI-only globals**. They are read from `bpy.context.scene` inside `create_hunyuan_job_local_site` — the LLM **cannot set them per-call** through the MCP tool signature. If you want Claude to vary resolution or step count per asset, you must either patch the addon to accept them as arguments, or drive the local `api_server.py` directly.

**Second gotcha:** `blendermcp_hunyuan3d_texture` defaults to **`False`**, so out-of-the-box local generation produces an **untextured mesh** — despite the MCP tool docstring promising "built-in materials". Turn it on in the panel.

**Third gotcha:** the official-API path exposes **no PBR flag at all**, while Tencent's own API charges +10 credits for PBR as an opt-in. So the blender-mcp official path almost certainly returns non-PBR textured OBJ. `[UNVERIFIED]` — I did not confirm whether `SubmitHunyuanTo3DJob` defaults `EnablePBR` on.

### 7.3 What the local server expects

`LOCAL_API` targets the `api_server.py` that ships in the Hunyuan3D repos — parameter names match exactly.

- **Hunyuan3D-2** `api_server.py`: `POST /generate`, defaults `octree_resolution=128`, `num_inference_steps=5`, `guidance_scale=5.0`, `texture=False`, `mc_algo='mc'`, `enable_flashvdm(mc_algo='mc')`. Also has `POST /send` + `GET /status/{uid}` for async.
- **Hunyuan3D-2.1** `api_server.py`: `POST /generate`, defaults `--port 8081`, `--model_path tencent/Hunyuan3D-2.1`, `--subfolder hunyuan3d-dit-v2-1`, `--device cuda`, `--mc_algo mc`, `--limit-model-concurrency 5`. Writes `{uid}_textured.glb` when texturing succeeds and returns it base64-encoded.

Note **`--device cuda`** is the default and the 2.1 texture path needs the compiled `custom_rasterizer` — reinforcing §4.3: run this on a Linux/NVIDIA box and point `BLENDERMCP_HUNYUAN3D_API_URL` at it over the network.

### 7.4 The prompt blender-mcp injects

The `asset_creation_strategy()` MCP prompt tells the model:
- *"Hunyuan3D is good at generating 3D models for single item."*
- Check `get_hunyuan3d_status()` first, then branch on mode: `OFFICIAL_API` → generate → poll → import; `LOCAL_API` → generate (which imports directly).
- *"For custom or unique items not available in libraries: Use Hyper3D Rodin or Hunyuan3D"* — i.e. Hunyuan3D is the fallback after PolyHaven and Sketchfab asset search, not the first choice.

### 7.5 Recommended wiring for this pipeline

1. **Use `LOCAL_API` mode pointed at a remote Linux/NVIDIA host** running `Hunyuan3D-2.1/api_server.py`. This is the only path that gets you 2.1 PBR *and* per-scene control of resolution/steps.
2. **Turn on `blendermcp_hunyuan3d_texture`** — it is off by default.
3. **Patch `create_hunyuan_job_local_site` to accept the four params as arguments** and widen the MCP tool signature, so Claude can trade speed for quality per asset (e.g. `octree_resolution=128, steps=5` for blockouts; `512, 50` for heroes).
4. **Add a retopology step in Blender** after import — nothing upstream produces quads.
5. **If you are EU/UK/KR-exposed, do not use the open weights.** Use the Tencent Cloud `OFFICIAL_API` path (separate terms — check them) or swap to TRELLIS.
6. Consider bypassing blender-mcp's Hunyuan tools entirely for the texture-only case: `Hunyuan3D-Paint` will texture *your* mesh, which is far more valuable in a Blender pipeline than generating shapes from scratch, and blender-mcp does not expose it.

---

## 8. Open questions / risks

- The `region=ap-guangzhou` hardcode in blender-mcp routes official-API traffic through mainland China. Latency and data-residency implications for a European/US user.
- 2.1's 29 GB total VRAM makes single-24GB-card end-to-end local inference impractical without offloading.
- No normal map from any open version; surface detail must come from geometry.
- The licence's Output-territory restriction (§5.c) is unusual and, as far as I can tell, untested. Treat as a genuine commercial risk, not boilerplate.
- Open-source cadence for the object-generation line appears to have stalled after Sept 2025 (Omni); Feb 2026's HY3D-Bench is data, not a model. Tencent's incentive has shifted to the paid Studio/Engine platform.

---

## Sources

**Papers**
- [Hunyuan3D 1.0: A Unified Framework for Text-to-3D and Image-to-3D Generation (arXiv 2411.02293)](https://arxiv.org/abs/2411.02293)
- [Hunyuan3D 2.0: Scaling Diffusion Models for High Resolution Textured 3D Assets Generation (arXiv 2501.12202)](https://arxiv.org/abs/2501.12202) — [full HTML method sections](https://arxiv.org/html/2501.12202v1)
- [Hunyuan3D 2.1: From Images to High-Fidelity 3D Assets with Production-Ready PBR Material (arXiv 2506.15442)](https://arxiv.org/abs/2506.15442) — [full HTML](https://arxiv.org/html/2506.15442v1)
- [Hunyuan3D 2.5: Towards High-Fidelity 3D Assets Generation with Ultimate Details (arXiv 2506.16504)](https://arxiv.org/abs/2506.16504)
- [Unleashing Vecset Diffusion Model for Fast Shape Generation — FlashVDM (arXiv 2503.16302)](https://arxiv.org/abs/2503.16302)
- [Hunyuan3D Studio: End-to-End AI Pipeline for Game-Ready 3D Asset Generation (arXiv 2509.12815)](https://arxiv.org/abs/2509.12815)
- [3D Arena: An Open Platform for Generative 3D Evaluation (arXiv 2506.18787)](https://arxiv.org/html/2506.18787v1)

**Repositories and weights**
- [Tencent-Hunyuan/Hunyuan3D-2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) — [README](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/README.md), [LICENSE](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE), [api_server.py](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/api_server.py), [surface_extractors.py](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/hy3dshape/hy3dshape/models/autoencoders/surface_extractors.py)
- [Tencent-Hunyuan/Hunyuan3D-2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2) — model zoo, changelog, [api_server.py](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/api_server.py)
- [Tencent-Hunyuan/Hunyuan3D-1](https://github.com/Tencent-Hunyuan/Hunyuan3D-1)
- [Tencent-Hunyuan/Hunyuan3D-Omni](https://github.com/Tencent-Hunyuan/Hunyuan3D-Omni)
- [Tencent-Hunyuan/Hunyuan3D-Part](https://github.com/Tencent-Hunyuan/Hunyuan3D-Part) — [LICENSE](https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-Part/main/LICENSE)
- [Tencent-Hunyuan/HY3D-Bench](https://github.com/Tencent-Hunyuan/HY3D-Bench)
- [Tencent-Hunyuan/FlashVDM](https://github.com/Tencent-Hunyuan/FlashVDM)
- [tencent/Hunyuan3D-2.1 on HuggingFace](https://huggingface.co/tencent/Hunyuan3D-2.1)
- [Open-source plans for 2.5 / PolyGen — issue #111](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/issues/111)

**blender-mcp**
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — [server.py](https://raw.githubusercontent.com/ahujasid/blender-mcp/main/src/blender_mcp/server.py), [addon.py](https://raw.githubusercontent.com/ahujasid/blender-mcp/main/addon.py), [README](https://raw.githubusercontent.com/ahujasid/blender-mcp/main/README.md)

**Cloud / API / pricing**
- [Tencent Hunyuan 3D Global Purchase Guide (official PDF)](https://staticintl.cloudcachetci.com/doc/pdf/product/pdf/1281_74120_en.pdf)
- [Tencent Cloud — Hunyuan 3D APIs](https://www.tencentcloud.com/document/product/1284/75539) · [SubmitHunyuanTo3DProJob](https://www.tencentcloud.com/document/product/1284/75540)
- [Tencent — Global Launch of Hunyuan 3D Engine (2025-11-26)](https://www.tencent.com/en-us/articles/2202235.html)
- [fal.ai — Hunyuan3D V3 text-to-3D](https://fal.ai/models/fal-ai/hunyuan3d-v3/text-to-3d) · [v2 turbo](https://fal.ai/models/fal-ai/hunyuan3d/v2/turbo) · [v2 mini](https://fal.ai/models/fal-ai/hunyuan3d/v2/mini)
- [Replicate — tencent/hunyuan-3d-3.1](https://replicate.com/tencent/hunyuan-3d-3.1)
- [Atlas Cloud — Hunyuan 3D model collection](https://www.atlascloud.ai/models/hunyuan-3d)
- [3D AI Studio — Hunyuan3D API (3.0 / 3.1 credit pricing)](https://www.3daistudio.com/Platform/API/Hunyuan3D)

**Deployment / benchmarks / integration**
- [SaladCloud — Hunyuan3D 2.1 image-to-3D benchmark, RTX 4090](https://blog.salad.com/hunyuan3d-2-1/)
- [Brainkeys/Hunyuan3D-2.1-mac — macOS/MPS port README](https://github.com/Brainkeys/Hunyuan3D-2.1-mac/blob/main/README_macOS.md)
- [ComfyUI blog — Hunyuan3D 2.0 & Multiview native support (2025-03-22)](https://blog.comfy.org/p/hunyuan3d-20-and-muitiview-native)
- [visualbruno/ComfyUI-Hunyuan3d-2-1](https://github.com/visualbruno/ComfyUI-Hunyuan3d-2-1)
- [PozzettiAndrea/ComfyUI-HunyuanX (Omni wrapper)](https://github.com/PozzettiAndrea/ComfyUI-HunyuanX)
- [deepbeepmeep/Hunyuan3D-2GP (GPU Poor)](https://github.com/deepbeepmeep/Hunyuan3D-2GP)
- [Hacker News — Hunyuan3D-2-Turbo ~1s on a 4090](https://news.ycombinator.com/item?id=43419237)

**Comparisons / coverage**
- [Scenario — Hunyuan 3D Models: The Essentials](https://help.scenario.com/articles/5886286147-hunyuan-3d-models-the-essentials)
- [Scenario — Comparing Generative 3D Models](https://help.scenario.com/articles/1263568892-comparing-generative-3d-models)
- [Scenario — Hunyuan PolyGen 1.5](https://www.scenario.com/models/hunyuan-polygen-15)
- [howaiworks.ai — Tencent Hunyuan 3D 3.0 announcement](https://howaiworks.ai/blog/tencent-hunyuan-3d-3-0-announcement)
- [Tencent Hunyuan on X — Hunyuan3D 3.0 launch (1536³, 3.6B voxel)](https://x.com/TencentHunyuan/status/1967873084960260470)
- [Tencent Hunyuan on X — Hunyuan3D-Omni](https://x.com/TencentHunyuan/status/1971495031040283125)
- [Tencent Hunyuan on X — Hunyuan3D-PolyGen](https://x.com/TencentHunyuan/status/1942174221976981881)
- [AI News — Tencent Hunyuan3D-PolyGen: a model for 'art-grade' 3D assets](https://www.artificialintelligence-news.com/news/tencent-hunyuan3d-polygen-a-model-for-art-grade-3d-assets/)
- [VoxelMatters — Tencent launches updated Hunyuan 3D 3.0 platform](https://www.voxelmatters.com/tencent-launches-updated-hunyuan-3d-3-0-platform-for-3d-model-generation/)
