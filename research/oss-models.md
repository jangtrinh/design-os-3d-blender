# Open-Source / Open-Weight Generative 3D — Survey and Feasibility Report

**Date:** 28 July 2026
**Context:** AI-driven Blender pipeline (Claude + blender-mcp, Blender 5.2 LTS, MacBook Pro Apple Silicon).
**Goal:** reduce dependency on commercial platforms; identify what is genuinely open, genuinely maintained, and genuinely runnable.

---

## 0. Executive summary

1. **The licensing picture improved dramatically in 2025→2026.** TRELLIS.2 (Microsoft, MIT, 4B, native PBR) is the single most important development: it is a permissively licensed model that emits Base Color / Roughness / Metallic / Opacity, not just geometry. This removes the main reason people tolerated Hunyuan3D's territory-restricted community licence.
2. **The real licence traps are no longer the headline models — they are the dependencies.** TRELLIS.2 is MIT, but its default preprocessing stack pulls **RMBG-2.0 (CC BY-NC 4.0)** and **DINOv2 (Meta custom licence)**. A CC-BY-NC background remover in your pipeline contaminates commercial output just as effectively as a restrictive generator would. This is the trap, and almost nobody documents it.
3. **Apple Silicon is now partially viable but not for texturing.** `trellis-mac` runs TRELLIS.2 on MPS with no CUDA, ~18 GB peak unified memory, ~3 min shape generation. But **texture baking is bound to a CUDA-only rasterizer**; on M1 Max the baking path ran 66–224 minutes and produced garbage UVs. Practical macOS output = geometry + vertex colours only.
4. **Mesh-native / quad generation is still research-only, and honestly so.** MeshAnythingV2 is capped at 1600 faces *and* is non-commercial (S-Lab). BPT reaches ~8k faces. The genuinely good quad models — Hunyuan3D-PolyGen, QuadGPT, PolyFlow — have **no released weights**. Learned retopology is not yet a production option; keep using QuadRemesher/Blender's remesh.
5. **Rigging is the weakest link, but UniRig (MIT) is a real, usable, permissive tool** and exports FBX. Quality degrades sharply when skeleton prediction misses limbs/tails, so treat it as a first-pass rig requiring manual cleanup, not a finished rig.
6. **Part-level generation is the sleeper category.** PartCrafter (MIT, 8 GB VRAM) and Roblox's CubePart (May 2026, OpenRAIL) produce separately-editable, separately-riggable parts — which matters far more for a Blender pipeline than a marginally better single blob mesh.

---

## 1. Master comparison table

Legend — PBR: does it emit material channels, not just colour. Quad: artist-like quad topology. macOS: runs on Apple Silicon without CUDA.

| Project | Licence | Task | Representation | VRAM | Time | PBR? | Quad? | macOS? | Repo health | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **TRELLIS.2** (Microsoft) | **MIT** | image→3D | O-Voxel sparse (16× downsample VAE), 4B params | 24 GB min (A100/H100 tested) | 3 s @512³, 17 s @1024³, 60 s @1536³ (H100) | **Yes** — BaseColor/Rough/Metal/Opacity | No | via fork only | 8.5k stars; last commit [UNVERIFIED] | **Best-in-class. The anchor of any open stack.** |
| **trellis-mac** (shivampkumar) | MIT (port); deps not | image→3D on MPS | same as TRELLIS.2 | ~18 GB peak unified; 24 GB machine min | ~3.5 min @512 (M4 Pro); 201 s (M1 Max) | Attributes yes, **baking broken** | No | **Yes** | Small fork; [UNVERIFIED] stars/commits | Geometry+vertex colour on Mac. Texture path unusable. |
| **TRELLIS** (v1, Microsoft) | MIT | image→3D | SLAT structured latents | ~16 GB [UNVERIFIED] | seconds | No (vertex colour / GS) | No | via fork | Mature, superseded | Superseded by 2.x. |
| **TripoSG** (VAST) | **MIT** | image→3D | SDF, rectified-flow DiT, 1.5B, 2048 latent tokens | 8 GB | [UNVERIFIED] | **No** (geometry only) | No | [UNVERIFIED] | 1.7k stars; last major release Mar 2025 | Excellent low-VRAM geometry. Needs separate texturing. |
| **TripoSF / SparseFlex** (VAST) | **MIT** | shape **VAE**, not a generator | SparseFlex, arbitrary topology, up to 1024³ | 12 GB @1024³ | n/a | No | No | [UNVERIFIED] | 742 stars | **Not image→3D.** A representation/reconstruction component. |
| **Direct3D-S2** (DreamTech) | **MIT** | image→3D | sparse volumetric SDF, unified sparse VAE | 10 GB @512; ~24 GB @1024 | ~2× faster than v1 [UNVERIFIED absolute] | Not mentioned | No | [UNVERIFIED] | 1.3k stars; last commit **30 May 2025** | Strong 1024³ geometry, but repo quiet ~14 months. |
| **Step1X-3D** (StepFun) | **Apache-2.0** (code) | image→3D + texture | TSDF geometry 1.3B + texture 3.5B | **27–29 GB** | ~152 s (50 steps, geo+tex) | Texture maps yes; PBR channels [UNVERIFIED] | No | No | 877 stars | Supports 2D LoRA transfer — genuinely interesting for style control. VRAM heavy. |
| **Hunyuan3D 2.1** (Tencent) | **Community licence — excludes EU/UK/South Korea, extends to Outputs** | image→3D + PBR | DiT + Hunyuan3D-Paint | ~29 GB total; **21 GB paint stage** | minutes | **Yes** | No | No (CUDA rasterizer) | 3.6k stars | **Territory restriction taints output. Avoid for commercial work.** |
| **Hunyuan3D 2.5 / PolyGen** | **Closed** | image→3D / retopo | — | — | — | Yes | **Yes (PolyGen)** | No | Not released | Open-sourcing requested (issue #111), **no official commitment**. |
| **Hi3DGen** (Stable-X / ByteDance) | **MIT** (Copyright Bytedance Inc.) | image→3D geometry | normal-bridged, TRELLIS-lineage | [UNVERIFIED] | [UNVERIFIED] | No | No | [UNVERIFIED] | Active; Stable3DGen successor framework | Best-in-class *geometric precision*; geometry only. |
| **Sparc3D** | **Effectively closed** | image→3D | sparse repr. | — | — | — | — | — | Code without usable checkpoints; pivoted to paid Hitem3D | **Bait-and-switch. Do not plan around it.** |
| **CraftsMan3D** | [UNVERIFIED — not confirmed this pass] | image→3D | native 3D diffusion + normal refine | [UNVERIFIED] | [UNVERIFIED] | No | No | [UNVERIFIED] | [UNVERIFIED] | Largely superseded by TripoSG/Direct3D-S2. |
| **TripoSR** (Tripo+Stability) | **MIT** | image→3D fast draft | triplane NeRF→mesh | 6–8 GB | sub-second | No | No | Likely (small) | Mature | Fastest draft/blockout. Low fidelity. |
| **SF3D / Stable Fast 3D** (Stability) | **Stability Community Licence** [UNVERIFIED exact terms] | image→3D + **UV unwrap + delight** | triplane | low | ~1 s | Partial (delit albedo) | No | [UNVERIFIED] | Mature | Useful for UV-unwrap + delighting alone. **Licence is NOT MIT — verify before shipping.** |
| **Hunyuan3D-Paint** (in 2.1) | Tencent Community (territory-restricted) | **texture existing mesh** | multiview diffusion → UV | **21 GB** | minutes | Yes | n/a | No | Part of 2.1 | Technically the best open mesh-texturer; **licence-blocked**. |
| **Material Anything** (3DTopia) | **MIT** | **PBR for existing mesh** | diffusion, confidence-mask progressive | [UNVERIFIED] | [UNVERIFIED] | **Yes** — albedo/rough/metal/bump | n/a | [UNVERIFIED] | 347 stars; CVPR'25 Highlight | **The permissive answer to Hunyuan3D-Paint.** Needs Blender 3.2.2 for its render step. |
| **StableMaterials** (Vecchio) | [UNVERIFIED — check HF repo] | tileable PBR **materials** | SD-based, semi-supervised | low | seconds | **Yes** | n/a | Likely | CVPR 2026 paper | Material/substance generation, not mesh texturing. Complementary. |
| **StableGen** (sakalond) | **GPL-3.0** | **Blender addon**: texture existing meshes | SDXL/FLUX/Qwen via ComfyUI | 8 GB (SDXL), 16+ GB (FLUX) | minutes | Projection-based | n/a | **Yes (listed macOS Apple Silicon)** | 810 stars; **last commit 5 Mar 2026** | **Most directly useful for your pipeline.** Note Blender 4.2–4.5 / 5.1+; **5.0 unsupported** — check 5.2. GPL-3.0 = addon copyleft, output fine. |
| **MVPaint** | [UNVERIFIED] | texture existing mesh | synchronized multiview diffusion | [UNVERIFIED] | [UNVERIFIED] | [UNVERIFIED] | n/a | [UNVERIFIED] | [UNVERIFIED] | Paper-stage for our purposes. |
| **TEXGen** | [UNVERIFIED] | UV-space texture gen | UV-space diffusion | [UNVERIFIED] | [UNVERIFIED] | [UNVERIFIED] | n/a | [UNVERIFIED] | [UNVERIFIED] | Not verified this pass. |
| **UniRig** (VAST + Tsinghua) | **MIT** | **auto-rig: skeleton + skinning** | autoregressive skeleton + bone-point cross-attention | 8 GB | [UNVERIFIED] | n/a | n/a | CUDA required | 1.6k stars; active (36 commits main) | **Best open rigger. Handles humans/animals/objects. Exports FBX.** |
| **MagicArticulate** (Seed3D) | **Apache-2.0** | skeleton + skinning | autoregressive sequence model | [UNVERIFIED] | [UNVERIFIED] | n/a | n/a | [UNVERIFIED] | 402 stars; Articulation-XL2.0 (48k models) | Solid permissive alternative/second opinion to UniRig. |
| **Particulate** (Li et al., CVPR 2026) | [UNVERIFIED] | **part articulation + kinematics** | feed-forward | [UNVERIFIED] | **~10 s/object** | n/a | n/a | [UNVERIFIED] | 156 stars; weights auto-download from HF | Not character rigging — mechanical/kinematic articulation. Great for props. |
| **Anymate** | [UNVERIFIED] | rigging dataset + baselines | — | — | — | n/a | n/a | — | [UNVERIFIED] | Mainly a dataset/benchmark contribution. |
| **RigNet** | Non-commercial [UNVERIFIED exact] | auto-rig (2020) | graph NN | low | — | n/a | n/a | — | Effectively legacy | Superseded by UniRig. |
| **MoMask** | [UNVERIFIED] | text→motion | residual VQ + masked transformer | low | fast | n/a | n/a | Likely | Mature, widely forked | Best-known open text-to-motion; SMPL-space. |
| **MotionGPT / MotionGPT3** (OpenMotionLab) | [UNVERIFIED] | text→motion, motion understanding | LLM-style motion tokens; MoT framework | [UNVERIFIED] | [UNVERIFIED] | n/a | n/a | [UNVERIFIED] | MotionGPT3 is the active successor | Output is SMPL — **retargeting to your rig is the real work.** |
| **MeshAnything v1/v2** | **S-Lab 1.0 — NON-COMMERCIAL** | mesh-native retopo | autoregressive, adjacent mesh tokenization | ~8 GB | ~45 s (A6000) | No | Triangle, artist-like | [UNVERIFIED] | v2 ~1.0k stars | **Hard cap 1600 faces + non-commercial. Not shippable.** |
| **BPT** (Tencent) | [UNVERIFIED — LICENSE file 404] | mesh-native gen from point cloud | blocked+patchified tokenization, 75% compression | ~12 GB fp16 | ~2 min/mesh | No | Triangle, artist-like | No | 303 stars | **>8k faces** — best open face budget. Licence unverified; assume Tencent-restrictive until read. |
| **DeepMesh** (zhaorw02) | **Apache-2.0** | mesh-native gen from point cloud | autoregressive + RL, 0.5B | [UNVERIFIED] (A100/A800/A6000 tested) | −50% vs baseline [UNVERIFIED absolute] | No | Triangle, artist-like | No | 727 stars; weights on HF (`zzzrw/DeepMesh`) | **The permissive mesh-native option.** Requires point clouds *with normals*. |
| **QuadGPT** | **No release info** | **native quad** mesh gen | autoregressive, 1.1B, 24 layers | A100-class | ~230 tok/s → ~3072 faces/window | No | **Yes, native quad** | No | Paper only | Research-only. Pretrained on 64×A100 ×7 days. |
| **PolyFlow** (Tencent + ZJU, 2026) | **No release info** | artist-mesh gen | flow matching, continuous topology embedding | A100 | parallel (non-AR) | No | **Triangle only** (despite "polygonal") | No | Paper only | Promising (parallel, not autoregressive) but no weights. |
| **MeshRipple** (2512.07514) | [UNVERIFIED] | structured AR artist-mesh gen | structured autoregressive | [UNVERIFIED] | [UNVERIFIED] | No | [UNVERIFIED] | [UNVERIFIED] | Paper (Dec 2025) | Not evaluated in depth. |
| **PartCrafter** (NeurIPS 2025) | **MIT** | **part-level** image→3D | compositional latent diffusion on TripoSG | **8 GB** | [UNVERIFIED] | No | No | [UNVERIFIED] | **2.4k stars** | **Excellent. Separately editable parts. MIT. Low VRAM.** |
| **CubePart** (Roblox, May 2026) | **OpenRAIL** | open-vocab part-controllable gen | multi-part DiT + shape VAE | [UNVERIFIED] | [UNVERIFIED] | [UNVERIFIED] | No | [UNVERIFIED] | HF weights released | Newest entrant. **OpenRAIL has use-restrictions — read Attachment A.** |
| **OmniPart** (HKU, SIGGRAPH Asia 2025) | [UNVERIFIED] | part-aware gen | semantic decoupling + structural cohesion | [UNVERIFIED] | [UNVERIFIED] | No | No | [UNVERIFIED] | [UNVERIFIED] | Peer of PartCrafter; licence unverified. |
| **HoloPart** (VAST) | [UNVERIFIED — repo has NOTICE file] | **part amodal segmentation** | generative completion of occluded parts | [UNVERIFIED] | [UNVERIFIED] | n/a | n/a | [UNVERIFIED] | [UNVERIFIED] | Decomposes an *existing* mesh into complete parts. Very useful downstream. |
| **PartField** (NVIDIA) | [UNVERIFIED] | part feature field / segmentation | feed-forward field | [UNVERIFIED] | [UNVERIFIED] | n/a | n/a | [UNVERIFIED] | [UNVERIFIED] | NVIDIA licences are often research-only — verify. |

---

## 2. License traffic-light section

### 🟢 GREEN — MIT / Apache-2.0, ship anything, output unencumbered

| Project | Licence | Note |
|---|---|---|
| TRELLIS.2 / TRELLIS | MIT | Weights + code MIT. **But see dependency warning below.** |
| TripoSG | MIT | |
| TripoSF / SparseFlex | MIT | |
| Direct3D-S2 | MIT | |
| Hi3DGen | MIT (© Bytedance Inc.) | Verified in LICENSE file |
| TripoSR | MIT | |
| UniRig | MIT | Verified in LICENSE file — commercial use permitted |
| MagicArticulate | Apache-2.0 | |
| PartCrafter | MIT | |
| Material Anything | MIT | |
| DeepMesh | Apache-2.0 | |
| Step1X-3D | Apache-2.0 (**code**) | ⚠️ Weight licence not separately verified — see amber note |
| trellis-mac | MIT (port code) | ⚠️ Dependencies are not — see red |
| StableGen | GPL-3.0 | Copyleft binds *the addon code*, **not your textures/renders**. Safe to use commercially; only matters if you redistribute a modified addon. |

### 🟡 AMBER — usable with care: research-only, unverified, use-restricted, or dependency-tainted

| Project | Issue |
|---|---|
| **CubePart** (Roblox) | **OpenRAIL**. Commercial use generally permitted, but OpenRAIL carries **behavioural use-restrictions that propagate to downstream users and to derivatives**. Not OSI-open. Read Attachment A before shipping. |
| **SF3D / Stable Fast 3D** | **Stability AI Community Licence** — commonly free only below a revenue threshold, with paid tier above. Not MIT. [UNVERIFIED exact 2026 terms] — **verify before relying on it.** |
| **BPT** (Tencent) | LICENSE file returned 404 on fetch. Tencent's default for 3D repos is a restrictive community licence. **Assume restricted until read.** |
| **Step1X-3D weights** | Repo code is Apache-2.0; the *model weights* licence was not separately confirmed (HF LICENSE path 404'd). Chinese-lab models frequently split code/weight licensing. [UNVERIFIED] |
| **Sparc3D** | Nominally open, but ships **no usable checkpoints**; team pivoted to the paid Hitem3D platform and pulled the free HF demos. Treat as closed. |
| **PartField / OmniPart / HoloPart / MVPaint / TEXGen / MoMask / MotionGPT / Particulate / Anymate / MeshRipple / StableMaterials** | Licences not verified this pass. Do not assume permissive. |
| **RigNet** | Legacy academic licence, non-commercial [UNVERIFIED exact]. Superseded anyway. |

### 🔴 RED — avoid for commercial work

| Project | Why — **and note which ones restrict the OUTPUT** |
|---|---|
| **Hunyuan3D 2.x (all)** | Tencent Community Licence **excludes EU / UK / South Korea, and the exclusion extends to the generated Outputs.** ⚠️ **OUTPUT-RESTRICTING.** Even if you generate outside those territories, the assets themselves carry the restriction. This is disqualifying for anything sold into or through the EU/UK. |
| **Hunyuan3D-Paint** | Same licence as 2.1 — ⚠️ **OUTPUT-RESTRICTING.** The best open mesh-texturer is legally unusable for EU/UK commerce. |
| **MeshAnything v1 & v2** | **S-Lab License 1.0 — non-commercial only.** Verbatim: permits "redistribution and use for non-commercial purpose"; commercial use requires contacting the contributors. ⚠️ Because it *transforms your asset*, the non-commercial term realistically **attaches to the retopologised output**. |
| **RMBG-2.0 (briaai)** | **CC BY-NC 4.0.** ⚠️ **OUTPUT-RESTRICTING** — NC licences propagate to derived works. This is pulled in by default by TRELLIS/trellis-mac preprocessing as the background remover. **Replace it.** Commercial use requires a paid BRIA agreement. |
| **DINOv2 (Meta)** | Meta custom licence, not OSI. Used as an image encoder in the trellis-mac dependency chain. ⚠️ Restrictions can reach downstream use. Verify which DINOv2 release/licence version your checkpoint uses. |
| **Hunyuan3D 2.5 / PolyGen** | Closed source, no weights. Community request (issue #111) has **no official Tencent response**. Do not plan around a hypothetical release. |
| **Sparc3D / Hitem3D** | Effectively commercial. |

### ⚠️ The single most important finding in this section

**A permissive model does not give you a permissive pipeline.** TRELLIS.2 is MIT, but the stock inference path uses **RMBG-2.0 (CC BY-NC)** and **DINOv2 (Meta custom)**. If you run the default repo and sell the result, your output is arguably encumbered by a non-commercial licence *despite the model being MIT*.

**Mitigation:** replace RMBG-2.0 with an MIT/Apache background remover (BiRefNet and `rembg`'s permissive backbones are the usual candidates — [UNVERIFIED: confirm the specific BiRefNet checkpoint's licence, as some variants are non-commercial]), and audit which image encoder checkpoint is actually loaded. Do this **before** the first commercial asset, not after.

---

## 3. Category 1 — Image/text → shape (core generators)

**The 2026 state of play.** The field consolidated onto sparse-voxel / sparse-SDF latents with rectified-flow or DiT backbones. Resolution moved from 256³ → 1024³–1536³. The genuinely new thing in 2026 is **native PBR from a permissive model**.

**TRELLIS.2 is the headline.** 4B parameters, MIT, "O-Voxel" omni-voxel representation encoding geometry *and* appearance in one sparse structure, 16× spatial downsampling VAE. It emits Base Color, Roughness, Metallic **and Opacity** (translucency), exports GLB. Reported H100 times: 3 s @512³ (2 s shape + 1 s materials), 17 s @1024³, 60 s @1536³. Minimum 24 GB NVIDIA VRAM; the repo states testing on Linux only. 8.5k stars. This is the model to build on.

**TripoSG remains the low-VRAM geometry champion.** 1.5B, MIT, SDF via rectified-flow transformer with 2048 latent tokens, trained on 2M curated image–SDF pairs, hybrid SDF + surface-normal + eikonal supervision. **8 GB VRAM.** Geometry only — no PBR, no textures. A `TripoSG-scribble` variant runs at 512 tokens for sketch input. Note the last major release was **March 2025**: stable, not actively advancing.

**Direct3D-S2** is the resolution specialist — sparse volumetric SDF with a unified sparse VAE, 10 GB @512 and ~24 GB @1024, MIT. Its contribution is training efficiency (1024³ on 8 GPUs vs 32+). But **last commit 30 May 2025** — ~14 months quiet. Usable, not evolving.

**Step1X-3D** (Apache-2.0 code) is the most *controllable*: it uniquely supports **direct transfer of 2D LoRAs to 3D synthesis**, which is genuinely valuable for locking an art style across an asset library. Cost: 1.3B geometry + 3.5B texture, **27–29 GB VRAM**, ~152 s for 50 steps. Rented-GPU only.

**Hi3DGen** (MIT, © Bytedance) targets geometric precision via normal bridging — it goes image → high-quality normals → geometry, which preserves fine surface detail better than direct image→SDF. Geometry only. Now folded into the broader **Stable3DGen** framework.

**Sparc3D is a cautionary tale.** Announced May 2025 as open, free HF demos ran May–June 2025, then the demos were quietly removed and traffic redirected to the paid **Hitem3D** platform. The GitHub repo contains framework code **without pre-trained checkpoints** — "open-source in name only," per community issues (#22, #25). Budget zero planning time for it.

**Hunyuan3D 2.x** is technically strong (2.1 has real production PBR) but the Community Licence's EU/UK/South Korea exclusion **extends to Outputs**, and 2.5/PolyGen were never released. Given TRELLIS.2 exists under MIT with PBR, there is now **no reason to accept Hunyuan3D's licence.**

---

## 4. Category 2 — Texture / PBR as a separate stage

This is the highest-value category for your situation, because the valuable case is **texturing a mesh you already have** — from a marketplace, from your own modelling, or from a geometry-only generator like TripoSG.

**Material Anything (MIT, 3DTopia, CVPR 2025 Highlight) is the recommendation.** It generates PBR materials for *any* 3D object: texture-less meshes, albedo-only objects, generated models, and scanned objects. Outputs **albedo, roughness, metallic, bump/normal**, in UV space. It works via progressive material generation guided by confidence masks, with two checkpoints (Material Estimator + Material Refiner) on HuggingFace. It requires **Blender 3.2.2** for its rendering step — an annoying pin given you are on 5.2, so expect to run that step in a separate Blender install or container. 347 stars — small, but MIT and it does the exact job.

**StableGen (GPL-3.0, 810 stars, last commit 5 March 2026) is the most immediately practical.** It is a **Blender addon** that textures existing meshes using SDXL / FLUX.1-dev / Qwen Image Edit through a ComfyUI backend, and it supports **scene-wide multi-mesh texturing** (texturing an entire environment consistently, not one object at a time). It can also drive TRELLIS.2 to generate a mesh and then refine it. It explicitly lists **macOS (Apple Silicon)** support. 8 GB VRAM for SDXL, 16+ GB for FLUX. Caveats: it supports Blender 4.2–4.5 and 5.1+ but **explicitly not 5.0** — verify 5.2 compatibility before committing. GPL-3.0 binds the addon code only; your generated textures are yours.

**Hunyuan3D-Paint** is technically the strongest open mesh-texturer — it accepts a mesh path directly (`paint_pipeline(mesh_path, image_path=...)`), so it genuinely does the "texture my existing mesh" job, at 21 GB VRAM. It is **blocked by the territory-restricted licence that extends to outputs**, and it requires compiling custom CUDA rasterizers and a differentiable renderer. Excluded on both licence and platform grounds.

**Step1X-3D's texture stage** (3.5B, SD-XL-based, conditioned on geometry, multi-view) is Apache-2.0 at the code level and is the licence-safe heavyweight alternative — but 27–29 GB.

**StableMaterials** (CVPR 2026) generates **tileable PBR materials** via knowledge distillation + semi-supervised learning. This is substance/material generation, not mesh texturing — complementary, good for filling a material library. Licence [UNVERIFIED].

**SF3D** is worth noting specifically for two side-capabilities that are hard to get elsewhere: **automatic UV unwrapping** and **illumination disentanglement (delighting)**. Delighting matters a lot — generated textures usually have baked-in lighting that fights your Blender lighting. But its licence is the Stability Community Licence, not MIT. [UNVERIFIED 2026 terms.]

**MVPaint** (synchronized multi-view diffusion) and **TEXGen** (UV-space diffusion) were not verified in this pass — treat as paper-stage.

---

## 5. Category 3 — Auto-rigging and animation

**Be honest: this is the weakest area, and open models are noticeably behind.** But it is not empty, and the licences here are unusually good.

**UniRig (MIT, VAST + Tsinghua, SIGGRAPH 2025, 1.6k stars) is the clear pick.** Two stages: skeleton prediction via an autoregressive transformer, then skinning weight prediction via bone-point cross-attention. **8 GB VRAM.** Accepts `.obj`, `.fbx`, `.glb`, `.vrm`; **exports FBX** — which matters, because FBX is what actually round-trips into Blender with a rig intact. It handles humans, animals, and inanimate objects, including anime characters and organic/inorganic structures.

The honest caveats, from the maintainers' own README:
- Skinning quality **degrades sharply if the skeleton is wrong** — missing tail or wing bones wreck the result. Skeleton refinement before skinning is advised.
- The maintainers say "the code may be a bit messed up."
- The checkpoint currently shipped is trained on **Articulation-XL2.0**, not the Rig-XL/VRoid data used for the paper's headline results. **The published results are not what you get from the released weights.**

Treat UniRig as a **first-pass rig requiring manual cleanup in Blender**, not a finished rig. For humanoids specifically, a hand-built or Rigify rig will still beat it.

**MagicArticulate (Apache-2.0, Seed3D, CVPR 2025, 402 stars)** frames skeleton generation as sequence modelling with an autoregressive transformer handling variable bone counts, and does produce **skinning weights** as well as skeletons. Trained on **Articulation-XL2.0** (48k+ annotated models filtered from Objaverse-XL). Permissive, and a useful second opinion when UniRig misses a limb.

**Particulate (CVPR 2026, 156 stars)** is different and worth knowing: it infers **parts, kinematic structure, and motion constraints** from a single static mesh in **~10 seconds**, with weights auto-downloading from HuggingFace. This is *not* character rigging — it is mechanical articulation (what hinges, what slides, what rotates). For props, machinery, doors, and tools it is exactly right, and it pairs naturally with part-level generation.

**Text-to-motion.** **MoMask** (residual VQ + masked transformer) remains the reference open model; **MotionGPT3** (OpenMotionLab) is the active successor, framing motion as a second modality in a Mixture-of-Transformers setup. Licences [UNVERIFIED].

The blunt reality: **the models output SMPL-space human motion, and the real work is retargeting** that onto your character's rig. Open retargeting is not a solved, packaged problem — expect to use Blender's Rokoko addon, Auto-Rig Pro (commercial), or hand-rolled constraint mapping. Do not budget "text → animated character" as a one-click open path in 2026.

---

## 6. Category 4 — Mesh-native / quad generation and learned retopology

**You flagged this as the highest-leverage category. The honest answer: it is still research-only for anything you could ship, and the best models have no weights.**

The face-count ceiling is the whole story. Autoregressive mesh generation costs tokens per face, so context length caps geometry complexity:

| Model | Face budget | Licence | Weights |
|---|---|---|---|
| MeshAnything v1/v2 | **1600 faces (hard)** | S-Lab 1.0 — **non-commercial** | Yes |
| BPT | **>8k faces** (75% compression) | [UNVERIFIED, 404] | Yes |
| DeepMesh (0.5B) | [UNVERIFIED] | **Apache-2.0** | Yes (`zzzrw/DeepMesh`) |
| QuadGPT (1.1B) | ~3072 faces / 36,864-token window | none stated | **No** |
| PolyFlow | 250–4000 vertices | none stated | **No** |
| Hunyuan3D-PolyGen | production-grade | **closed** | **No** |

**MeshAnythingV2** does produce genuinely artist-like topology with Adjacent Mesh Tokenization, ~8 GB and ~45 s on an A6000. But it is capped at 1600 faces — the README states plainly that it "cannot generate meshes with more than 1600 faces" — and it is **S-Lab 1.0, non-commercial.** Both problems are disqualifying, and the licence issue is worse than it looks because the model *transforms your asset*, so the non-commercial term realistically attaches to the retopologised output.

**BPT (Tencent, CVPR 2025)** is the face-count leader among released weights: blocked + patchified tokenization achieving ~75% compression, enabling **>8k faces**, ~12 GB fp16, ~2 min per mesh, point-cloud input. 303 stars. **Its LICENSE file 404'd on fetch** — given Tencent's pattern with Hunyuan3D, assume restrictive until you read it.

**DeepMesh (Apache-2.0, 727 stars) is therefore the only permissively-licensed mesh-native model with released weights.** 0.5B, autoregressive transformer with reinforcement learning, ~50% generation-time reduction after the April optimisation pass. Input is **point clouds with normals included** — so you need a normal-bearing point cloud, not just a mesh. Tested on A100/A800/A6000. This is your only real option in this category, and it is small.

**The quad models are all locked.** **QuadGPT** is the first autoregressive framework designed for **native quad-dominant** generation rather than tri→quad conversion — 1.1B, 24 layers, three-stage hourglass, 36,864-token window (~3072 faces at 12 tokens/face), ~230 tok/s on an A100, pretrained on **64× A100 for 7 days**. No code or licence information. **PolyFlow** (Tencent + Zhejiang, 2026) is architecturally exciting — flow matching with continuous topology embeddings enabling **parallel** denoising instead of the autoregressive bottleneck, user-controlled vertex count 250–4000 — but despite the name it outputs **triangle meshes**, and there is no release. **Hunyuan3D-PolyGen** is the actual production-grade quad retopology model and it is closed, with Tencent giving no commitment to release.

**Verdict: do not plan a learned-retopology stage in 2026.** Keep using QuadRemesher, Instant Meshes (open, MIT-ish), or Blender's built-in remesh + manual cleanup. Revisit if PolyGen or QuadGPT ever ships weights.

---

## 7. Category 5 — Part-level / compositional generation

**This is the most underrated category and it matters more than a marginally better single mesh** — because parts are separately editable, separately texturable, and separately riggable. A monolithic isosurface blob is nearly useless in a Blender pipeline; a chair that arrives as seat + back + four legs is immediately workable.

**PartCrafter (MIT, NeurIPS 2025, 2.4k stars) is the pick.** Compositional latent diffusion transformers producing structured multi-part meshes from a single image. It is built on **TripoSG** — only the DiT is finetuned, the VAE is kept fixed — and the authors note the approach is compatible with **all vector-set-based 3D generative models**, explicitly including Hunyuan3D-2.1. Training configs go to 16 parts; scene examples use 6. **8 GB VRAM** — it runs on modest hardware. Output is GLB. It has more stars than most of the single-shape generators, which tells you the community found it useful.

**CubePart (Roblox, May 2026, OpenRAIL)** is the newest entrant and the only major 2026 release in this category: **open-vocabulary, part-controllable** mesh generation, two checkpoints (multi-part DiT + shape VAE) on HuggingFace, with a demo Space. Open-vocabulary part control means you can ask for parts by name rather than accepting an unlabelled decomposition — genuinely useful for an agentic pipeline where Claude is issuing the instructions. **OpenRAIL is not OSI-open**: it permits commercial use but carries behavioural use-restrictions that propagate to derivatives and downstream users. Read Attachment A before shipping. VRAM and parameter count [UNVERIFIED].

**OmniPart (HKU, SIGGRAPH Asia 2025)** takes a different route — semantic decoupling plus structural cohesion — and is a direct peer of PartCrafter. Licence [UNVERIFIED].

**HoloPart (VAST)** solves the complementary problem: **generative 3D part amodal segmentation**, i.e. decomposing an *existing* mesh into complete parts, hallucinating the occluded geometry where parts interpenetrate. This is the tool for "I bought a mesh and need it in pieces." The repo carries a NOTICE file; licence [UNVERIFIED].

**PartField (NVIDIA)** provides feed-forward part feature fields for segmentation. NVIDIA research licences are frequently non-commercial — **verify before use.**

**Pipeline implication:** PartCrafter → HoloPart → per-part Material Anything → UniRig or Particulate is a coherent, mostly-MIT chain that produces genuinely editable assets. That is a better target than chasing single-mesh fidelity.

---

## 8. Category 6 — Datasets you could actually use

**Objaverse / Objaverse-XL — understand the licence reality.** The *collection* is **ODC-BY v1.0** (attribution required). But the AllenAI docs state explicitly that **"individual objects in Objaverse-XL are licensed under different licenses."** The 10M+ objects carry heterogeneous per-object terms, including CC-BY-NC and All-Rights-Reserved material. **The dataset licence does not launder the object licences.**

Practical consequence: you **cannot** bulk fine-tune on Objaverse-XL and safely sell the outputs. You must filter to commercially-permissive per-object licences first. Note also the ongoing artist-consent controversy — a large volume of Sketchfab content was ingested, and creators have objected to its use in training. For a business that wants to be defensible, this is reputational as well as legal exposure.

**TexVerse (2025) is the better fine-tuning corpus for your use case.** 858,669 unique high-resolution 3D models (1.6M instances with resolution variants), textures at **minimum 1024px**, and crucially **158,518 models with real PBR materials** (metalness and specular workflows). It also contains **69,138 rigged models and 54,430 animated models with skeleton and animation data preserved** — which is directly relevant to the rigging gap, since rigging models are data-starved. Plus 856,312 GPT-5-generated annotations describing overall characteristics, structure, and fine features. Sourced from Sketchfab, standardised to `.glb`. **Over 80% of models are CC-BY or CC0**, which the authors state enables commercial use. This is the most commercially-tractable large 3D corpus currently available.

**Articulation-XL2.0** — 48k+ models with high-quality articulation annotations (46.7k train / 2k test), filtered from Objaverse-XL. It is what both UniRig's shipped checkpoint and MagicArticulate were trained on. Inherits Objaverse-XL's per-object licence heterogeneity.

**ABO (Amazon Berkeley Objects)** — ~8k artist-created products with real PBR materials and catalogue metadata. Small but very clean; the licence is an Amazon research/CC-style term [UNVERIFIED exact]. Good for PBR material work, useless for scale.

**Toys4K** — ~4k toy-category objects, clean and category-balanced. Research licence [UNVERIFIED]. Good for evaluation and few-shot work, not pretraining.

**OmniObject3D** — large-vocabulary real-scanned objects; good for realism/robustness evaluation, licence [UNVERIFIED].

**What to use them for:**
- **Retrieval, not generation, is the underrated move.** With ~860k TexVerse assets under CC-BY/CC0, semantic retrieval into Blender is often faster, cleaner-topology, and more legally defensible than generating. Build an embedding index and let Claude query it before it reaches for a generator.
- **Fine-tuning:** TexVerse (licence-filtered) for texture/PBR; Articulation-XL2.0 for rigging; avoid unfiltered Objaverse-XL.
- **Evaluation:** ABO and Toys4K.

---

## 9. Realistic Apple Silicon section

### What actually runs locally on an M-series MacBook

**TRELLIS.2 via `trellis-mac` (shivampkumar) — verified working, with real limits.** A CUDA-free MPS port. Concrete measured numbers:

| Metric | M4 Pro | M1 Max 64GB |
|---|---|---|
| Shape generation | ~3.5 min | 201 s (shoe), 152 s (anime), 166 s (pixel-chibi) |
| Peak memory | ~18 GB | 17.5–18.5 GB across all runs |
| Total w/o texture | — | ~5 min |
| **Texture baking** | — | **3,954 s / 5,024 s / 13,429 s** (66 / 84 / 224 min) |

**Requires a 24 GB machine minimum. 16 GB Macs cannot run this practically.**

Known limitations vs CUDA:
- **No usable texture output.** The model computes PBR attributes, but **texture baking is tightly coupled to the CUDA-only rasterizer**. On M1 Max, baking not only took hours but produced unusable results — "the red accents from the input are picked up but scattered randomly across the UV sheet instead of landing on meaningful surface regions." **Vertex-colour output was the best result of the whole experiment.**
- **The 1024 high-resolution pipeline crashed** during mesh decoding with a sparse-convolution bounds error. Only the 512 pipeline is functional.
- No mesh hole filling.
- Sparse convolution is **~10× slower** than the CUDA kernel — this is the core bottleneck.

**Licence warning specific to this port:** the port code is MIT, but it pulls **DINOv2 (Meta custom licence)** and **RMBG-2.0 (CC BY-NC 4.0)**. Swap RMBG-2.0 out before commercial use.

**Also plausible locally:** StableGen lists macOS Apple Silicon support (SDXL at 8 GB is well within a 24–36 GB Mac); TripoSR is small enough to be comfortable; TripoSG at 8 GB is a candidate but CUDA-dependence is [UNVERIFIED].

### Honest local verdict

On a MacBook Pro you get: **image → geometry + vertex colours, ~3–4 minutes, at 512³.** That is genuinely useful for blockouts, proxies, silhouette iteration, and previz inside Blender. You do **not** get production PBR textures, 1024³+ detail, mesh-native retopology, or rigging locally.

### What needs a rented GPU

- Any PBR texture baking (TRELLIS.2 CUDA path, Material Anything, Step1X-3D)
- 1024³ / 1536³ generation
- Step1X-3D at all (27–29 GB)
- UniRig (CUDA required)
- DeepMesh / BPT mesh-native generation
- Any fine-tuning

### Sane cheap remote-GPU option

The pattern that fits your workflow: **keep iteration local on the Mac (fast, free, geometry-only), then batch the finals to a rented GPU.** Generate 20 blockouts locally, pick 3, send those 3 for high-res + PBR.

Ballpark 2026 pricing (verified figures marked; others [UNVERIFIED]):

| Provider / GPU | ~$/hr | Note |
|---|---|---|
| RunPod H100 (Community) | **$1.99** | verified |
| RunPod H100 (Secure) | **$3.19** | verified |
| RunPod, cheapest listed GPU | **$0.12** | verified, Community Cloud |
| RunPod (generic blended) | ~$1.49 | verified, July 2026 |
| Lambda A100 | ~$1.99 | verified, July 2026 |
| Modal A100 | ~$2.50 | verified, July 2026 |
| CoreWeave A100 | ~$2.70 | verified, July 2026 |
| RTX 4090 / L40S / A100-80GB specific rates | — | **[UNVERIFIED]** — not listed in sources checked |
| Vast.ai | — | **[UNVERIFIED]** — typically undercuts RunPod, verify directly |

**Cost per generation, derived from verified rates and verified inference times:**

- TRELLIS.2 @1024³ on H100: 17 s inference. Even assuming **2 minutes** of wall-clock including model load and I/O, at $1.99/hr Community that is **≈ $0.066 per asset** — about 7 cents.
- TRELLIS.2 @1536³: 60 s inference; assume 3 min wall-clock → **≈ $0.10**.
- Step1X-3D: ~152 s inference; assume 5 min wall-clock → **≈ $0.17**.
- A 50-asset batch at 1024³ with PBR: **under $5**, plus the annoyance of spinning up the pod.

**This is the decisive economic argument.** Hyper3D Rodin's $120/month Business tier buys roughly **1,800 H100-hours-equivalent** of generation at RunPod Community rates — orders of magnitude more assets than a subscription tier grants. The break-even against any commercial platform is reached almost immediately. **Serverless (RunPod Serverless / Modal) is the right shape** for spiky, per-asset workloads — you pay per second and avoid idle cost. Container cold-start on a 4B model is the practical tax; keep a warm worker if you are doing a session, kill it otherwise.

---

## 10. Recommended open stack

### Primary stack (maximally permissive, PBR-capable)

| Stage | Tool | Licence | Where it runs |
|---|---|---|---|
| **0. Retrieval first** | TexVerse index (CC-BY/CC0 filtered) | CC-BY / CC0 | local |
| **1. Local iteration** | TRELLIS.2 via `trellis-mac` @512 | MIT (**swap RMBG-2.0**) | **Mac, ~3.5 min, vertex colours** |
| **2. Final geometry + PBR** | TRELLIS.2 @1024³/1536³ | MIT | RunPod H100, ~$0.07–0.10/asset |
| **3. Part decomposition** | PartCrafter (gen) / HoloPart (existing mesh) | MIT / [UNVERIFIED] | 8 GB — rented or high-RAM Mac |
| **4. Texture existing meshes** | **StableGen** in Blender (SDXL/FLUX via ComfyUI) | GPL-3.0 (addon only) | **Mac-capable** |
| **5. PBR for untextured/marketplace meshes** | **Material Anything** | **MIT** | rented; needs Blender 3.2.2 side-install |
| **6. Retopology** | **QuadRemesher / Instant Meshes / Blender remesh** — *not* a learned model | — | local |
| **7. Rigging** | **UniRig** → FBX → manual cleanup in Blender | **MIT** | rented (CUDA), 8 GB |
| **8. Prop articulation** | Particulate (~10 s/object) | [UNVERIFIED] | rented |
| **9. Motion** | MoMask / MotionGPT3 → manual retarget | [UNVERIFIED] | rented |
| **Orchestration** | Claude + blender-mcp, Blender 5.2 LTS | — | local |

**One-sentence version:** TRELLIS.2 (MIT) for shape and PBR — run locally on the Mac via `trellis-mac` for geometry iteration and burst to a ~$2/hr RunPod H100 for final textured output — with PartCrafter for editable parts, Material Anything or StableGen for texturing existing meshes, UniRig for a first-pass rig, conventional QuadRemesher for retopology, and RMBG-2.0 swapped out of every preprocessing path.

### Second-choice fallback (if TRELLIS.2 proves unworkable)

**TripoSG (MIT, 8 GB) for geometry → Material Anything (MIT) for PBR → UniRig (MIT) for rigging.**

Rationale: it is fully MIT end-to-end, the VRAM floor is 8 GB throughout (so a 24 GB Mac or the cheapest rented GPU suffices), and it decouples geometry from texture so you can swap either stage independently. You lose TRELLIS.2's single-pass PBR quality and its 1536³ ceiling, and TripoSG has been static since March 2025. For style-locked asset libraries, substitute **Step1X-3D** (Apache-2.0, 2D-LoRA transfer) at the cost of a 27–29 GB rented GPU.

### Explicitly rejected

- **Hunyuan3D 2.x / -Paint** — output-restricting territory licence, no longer necessary now that TRELLIS.2 exists under MIT with PBR.
- **MeshAnything v1/v2** — non-commercial S-Lab licence *and* a 1600-face ceiling.
- **Sparc3D** — no usable checkpoints; pivoted commercial.
- **Any learned quad retopology** — QuadGPT / PolyFlow / PolyGen have no weights.
- **Unfiltered Objaverse-XL fine-tuning** — per-object licence heterogeneity plus consent controversy.

---

## 11. What could not be verified

- **Last commit dates for most repos.** The GitHub API was gated in this session and `github.com/*/commits/main` is robots-disallowed. Star counts came from rendered README pages and are approximate/point-in-time. Confirmed dates: Direct3D-S2 (30 May 2025), StableGen (5 Mar 2026).
- **BPT's licence** — LICENSE file returned 404. Assume Tencent-restrictive until read.
- **Step1X-3D weight licence** (distinct from the Apache-2.0 code licence) — HF LICENSE path 404'd.
- **SF3D / Stable Fast 3D exact 2026 Stability Community Licence terms**, including the revenue threshold.
- **CubePart** VRAM, parameter count, inference time; and the exact OpenRAIL variant / Attachment A restrictions.
- **Licences for:** OmniPart, HoloPart, PartField, MVPaint, TEXGen, StableMaterials, MoMask, MotionGPT/MotionGPT3, Particulate, Anymate, MeshRipple, RigNet, ABO, Toys4K, OmniObject3D.
- **CraftsMan3D** — not confirmed in this pass at all (licence, health, specs).
- **Whether TripoSG / Hi3DGen / PartCrafter / Material Anything have working MPS paths** — none advertise Apple Silicon support.
- **DeepMesh max face count and VRAM**; absolute (not relative) inference times for DeepMesh and Direct3D-S2.
- **RTX 4090 / L40S / A100-80GB specific hourly rates**, and Vast.ai pricing generally.
- **BiRefNet checkpoint licences** — proposed as the RMBG-2.0 replacement, but some variants are non-commercial; verify the specific checkpoint.
- **Which exact DINOv2 release/licence version** the TRELLIS.2 and trellis-mac checkpoints load.
- **StableGen compatibility with Blender 5.2** — it documents 4.2–4.5 and 5.1+, excludes 5.0; 5.2 untested in sources.
- **Whether TRELLIS.2's stated 24 GB minimum** holds at 512³ or only at higher resolutions.
- All benchmark/quality rankings are as claimed by authors; **no independent benchmarks were run.**

---

## Sources

**Core generators**
- TRELLIS.2 GitHub — https://github.com/microsoft/TRELLIS.2
- TRELLIS.2-4B on HuggingFace — https://huggingface.co/microsoft/TRELLIS.2-4B
- TRELLIS.2 project page — https://microsoft.github.io/TRELLIS.2/
- TripoSG — https://github.com/VAST-AI-Research/TripoSG
- TripoSF / SparseFlex — https://github.com/VAST-AI-Research/TripoSF
- Direct3D-S2 — https://github.com/DreamTechAI/Direct3D-S2
- Step1X-3D — https://github.com/stepfun-ai/Step1X-3D
- Hi3DGen LICENSE — https://github.com/Stable-X/Hi3DGen/blob/main/LICENSE
- Hi3DGen project page — https://stable-x.github.io/Hi3DGen/
- Stable3DGen — https://github.com/Stable-X/Stable3DGen
- Hunyuan3D-2.1 — https://github.com/tencent-hunyuan/hunyuan3d-2.1
- Hunyuan3D-2 LICENSE — https://github.com/Tencent-Hunyuan/Hunyuan3D-2/blob/main/LICENSE
- Open-source plans for 2.5 / PolyGen (issue #111) — https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/issues/111
- Sparc3D repo — https://github.com/lizhihao6/Sparc3D
- Sparc3D controversy — https://www.vset3d.com/the-sparc3d-controversy-from-open-source-promise-to-paid-hitem3d-platform/
- Sparc3D issue #25 — https://github.com/lizhihao6/Sparc3D/issues/25
- State of AI 3D Generation 2026 — https://www.3daistudio.com/state-of-ai-3d-generation-2026
- SF3D paper — https://arxiv.org/html/2408.00653v1

**Texture / PBR**
- Material Anything — https://github.com/3DTopia/MaterialAnything
- StableGen (Blender addon) — https://github.com/sakalond/StableGen
- StableMaterials (CVPR 2026) — https://openaccess.thecvf.com/content/CVPR2026/html/Vecchio_StableMaterials_Enhancing_Diversity_in_Material_Generation_via_Semi-Supervised_Learning_CVPR_2026_paper.html
- StableMaterials arXiv — https://arxiv.org/abs/2406.09293
- Hunyuan3D-Paint README — https://huggingface.co/spaces/tencent/Hunyuan3D-2.1/blob/main/hy3dpaint/README.md
- RMBG-2.0 licence — https://huggingface.co/briaai/RMBG-2.0

**Rigging / animation**
- UniRig — https://github.com/VAST-AI-Research/UniRig
- UniRig LICENSE — https://github.com/VAST-AI-Research/UniRig/blob/main/LICENSE
- UniRig paper — https://arxiv.org/html/2504.12451v1
- MagicArticulate — https://github.com/Seed3D/MagicArticulate
- Particulate (CVPR 2026) — https://github.com/ruiningli/particulate
- Instruct-Particulate — https://arxiv.org/html/2606.14699v1
- Anymate — https://anymate3d.github.io/
- MoMask — https://github.com/EricGuo5513/momask-codes
- MotionGPT — https://github.com/OpenMotionLab/MotionGPT
- MotionGPT3 — https://github.com/OpenMotionLab/MotionGPT3
- awesome-text-to-motion — https://github.com/Zilize/awesome-text-to-motion

**Mesh-native / quad**
- MeshAnythingV2 — https://github.com/buaacyw/MeshAnythingV2
- MeshAnythingV2 LICENSE (S-Lab 1.0) — https://github.com/buaacyw/MeshAnythingV2/blob/main/LICENSE.txt
- MeshAnything V2 paper — https://arxiv.org/html/2408.02555v1
- BPT — https://github.com/Tencent-Hunyuan/bpt
- BPT paper — https://arxiv.org/abs/2411.07025
- DeepMesh — https://github.com/zhaorw02/DeepMesh
- DeepMesh paper — https://arxiv.org/abs/2503.15265
- QuadGPT — https://arxiv.org/html/2509.21420v1
- PolyFlow — https://arxiv.org/html/2606.30673v1
- MeshRipple — https://arxiv.org/abs/2512.07514
- Hunyuan3D-PolyGen coverage — https://www.artificialintelligence-news.com/news/tencent-hunyuan3d-polygen-a-model-for-art-grade-3d-assets/

**Part-level**
- PartCrafter — https://github.com/wgsxm/PartCrafter
- PartCrafter project page — https://wgsxm.github.io/projects/partcrafter/
- OmniPart — https://github.com/HKU-MMLab/OmniPart
- OmniPart paper — https://arxiv.org/html/2507.06165v1
- HoloPart — https://github.com/VAST-AI-Research/HoloPart
- CubePart (Roblox) — https://huggingface.co/Roblox/cubepart
- CubePart paper — https://arxiv.org/abs/2605.28763
- CubePart project page — https://cubepart.github.io/
- Roblox newsroom — https://about.roblox.com/newsroom/2026/05/cubepart-roblox-open-vocabulary-part-controllable-3d-generator

**Datasets**
- Objaverse-XL — https://github.com/allenai/objaverse-xl
- Objaverse-XL paper — https://arxiv.org/html/2307.05663v1
- Objaverse home — https://objaverse.allenai.org/
- Objaverse artist-consent coverage — https://3dvf.com/en/ai-this-massive-dataset-of-3d-objects-is-a-game-change-heres-why-it-may-include-some-of-your-3d-assets/
- TexVerse — https://arxiv.org/html/2508.10868v1
- OmniObject3D — https://omniobject3d.github.io/

**Apple Silicon / infrastructure**
- trellis-mac repo — https://github.com/shivampkumar/trellis-mac
- TRELLIS.2 on Apple Silicon MPS (CUDA-free port) — https://lilting.ch/en/articles/trellis2-apple-silicon-mps-cuda-free
- trellis-mac on M1 Max 64GB, hands-on — https://lilting.ch/en/articles/trellis2-m1-max-hands-on
- RunPod GPU pricing — https://computeprices.com/providers/runpod
- GPU cloud pricing comparison (June/July 2026) — https://www.buildmvpfast.com/api-costs/gpu
- Vast.ai vs RunPod pricing 2026 — https://medium.com/@velinxs/vast-ai-vs-runpod-pricing-in-2026-which-gpu-cloud-is-cheaper-bd4104aa591b
