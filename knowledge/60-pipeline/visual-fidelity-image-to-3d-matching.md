---
name: visual-fidelity-image-to-3d-matching
category: 60-pipeline
domain: pipeline_automation
loads_with: [export-interchange, product-viz-and-shots, 3d-printing]
tags: [image-to-3d, visual-fidelity, nano-banana, blueprint-synthesis, exploded-view, parts-catalog, camera-matching, closed-loop-gate, production-grade]
id: visual-fidelity-image-to-3d-matching
title: "Visual Fidelity Image-to-3D Matching: Multi-Modal Blueprint Synthesis & Closed-Loop Verification"
description: Verify reference-image fidelity with per-feature review plus diagnostic silhouette IoU and MAE; hosted blueprint synthesis is not permitted in production under the Native Asset Policy.
when: [reference-image-reconstruction, silhouette-iou-check, orthographic-blueprint-setup, fidelity-review-gate]
trust_tier: draft
sources_checked: 2026-10-13
---

# Visual Fidelity Image-to-3D Matching: Multi-Modal Blueprint Synthesis & Closed-Loop Verification

## Purpose
Describe how to reconstruct an object from reference images with native Blender geometry and how to measure silhouette overlap and pixel error as diagnostics, while keeping the verdict a per-feature review rather than a single fidelity percentage.

## When to Use / When NOT
- ALLOWED: setting up orthographic reference views and image empties for a native reconstruction — §3.
- ALLOWED: computing silhouette IoU and mean absolute error between a reference image and a matched-camera render as a diagnostic — §4.
- NOT ALLOWED: calling Nano Banana or any hosted generative/mesh service for production assets — the Native Asset Policy forbids hosted-model calls; use the native route in skill `blender-image-to-3d` instead.
- NOT ALLOWED: declaring a numeric "99% fidelity" or passing a build on IoU/MAE alone — the review rubric requires per-feature PASS/FAIL/UNKNOWN verdicts; use `blender-image-to-3d` references/review-rubric.md.
- NOT ALLOWED: print tolerance, wall thickness or manufacturing acceptance — use `3d-printing` and `scripts/production-gate.py` instead.
- NOT ALLOWED: studio lighting and delivery renders — use `product-viz-and-shots` instead.

## Core Knowledge Content

> Production standard for achieving 99% visual and geometric fidelity from 2D image inputs: overcoming the ill-posed single-view limit through Nano Banana multi-modal synthesis (Orthographic Blueprints, Exploded Views, Parts Catalogs), Blender-native orthographic CAD reconstruction, and closed-loop optical verification.

---

> **Policy and evidence status (2026-10-13).** (1) The "Nano Banana" synthesis in §2 is a hosted generative-model call. `.project-agent.md` states that no generated/retrieved vendor mesh, paid credit, hosted-model call or external asset download may enter production <!-- ease:source S1 anchor="Tech Stack: No new generated/retrieved vendor mesh, hosted-model call" -->, and the native reconstruction skill builds "without ... hosted model calls" <!-- ease:source S2 anchor="Build from supplied references without new generated/retrieved vendor meshes, hosted model calls" -->. Treat §2 as historical description of the `builds/quadruped-02` dossier <!-- ease:source S4 anchor="Nano Banana 4-view blueprint, exploded view, parts catalog" -->; a generated sheet is secondary authority and "cannot authenticate unseen" geometry <!-- ease:source S2 anchor="generated blueprint/360 sheet ... later generated views cannot authenticate unseen switch, shaft or PCB geometry" -->. (2) The 99%/98% figures and the 0.05/51%/29%/20% statistics below have no primary source in the repo or literature (UNVERIFIED), and the rubric says not to "substitute a global score or invented decimal fidelity number" and that "pixel similarity is not a fidelity test" <!-- ease:source S3 anchor="Give every critical feature a named PASS, FAIL, or UNKNOWN verdict; Pixel similarity is not a fidelity test" -->. IoU/MAE here are diagnostics only.

### 1. Mathematical Foundations & The Single-View Blind Spot

#### A. The Ill-Posed Inverse Problem & Generative Prior Ceiling
A single 2D photograph $I(u, v)$ is a degenerate perspective projection of a 3D surface $\mathcal{S} \subset \mathbb{R}^3$ under unknown illumination $\mathcal{L}$ and camera intrinsics $\mathbf{K}$:

```math
% illustrative notation only
I(u, v) = \pi_{\mathbf{K}, \mathbf{R}, \mathbf{t}} \left( \int_{\Omega} f_r(\mathbf{x}, \omega_i, \omega_o) L_i(\mathbf{x}, \omega_i) (\mathbf{n} \cdot \omega_i) \, d\omega_i \right)
```
<!-- ease:source UNVERIFIED reason="schematic image-formation sketch, not a derived or cited formula" -->

1. **Information Destruction:** <!-- ease:source S5 anchor="Single-image 3D is ill-posed; occluded regions are hallucinated" -->
   - Projection collapses the depth coordinate $Z$, destroying metric scale.
   - Occluded surfaces (rear, interior, opposite flank) have strictly zero photographic evidence.
2. **Generative AI Ceiling (80%–88%):** <!-- ease:source UNVERIFIED reason="80-88% ceiling has no cited measurement" -->
   - Pure feed-forward 1-click generative models (TRELLIS.2, Hunyuan3D-2.1) sample a conditional prior $p(\mathcal{S} \mid I)$ <!-- ease:source S5 anchor="TRELLIS.2 arXiv:2512.14692; Hunyuan3D 2.0/2.1; occluded regions sampled from the prior" -->.
   - JEV System One verified that the probability of single-shot 1-click AI producing a $\ge 99\%$ exact engineering digital twin is **$0.05$ (5%)**. <!-- ease:source UNVERIFIED reason="no receipt for the 0.05 JEV figure found in the repo; the rubric forbids invented decimal fidelity numbers" -->
   - Primary failure modes: **Perspective Drift ($51\%$)**, **Baked Lighting contamination ($29\%$)**, and **Occluded Feature Hallucination ($20\%$)**. <!-- ease:source UNVERIFIED reason="the 51/29/20 split has no source" -->

---

### 2. The Multi-Modal Synthesis Architecture (Nano Banana)

To cross from the $85\%$ generative ceiling to **$99\%$ Master Artisan precision** <!-- ease:source UNVERIFIED reason="85% and 99% are unmeasured marketing-style figures" -->, the single 2D image must first be expanded into a complete **Four-Modal Technical Dossier** before opening Blender (hosted step; see the policy note above):

```
[ User Input Image (3/4 Perspective) ]
                  │
                  ▼
    [ Nano Banana Multi-Modal Synthesis ]
  ├── 1. Orthographic Blueprint (Front, Side, Top, Back + Dimensions)
  ├── 2. Mechanical Exploded View (Internal Skeleton + Assembly Hierarchy)
  ├── 3. Parts Catalog & CMF Matrix (Materials, Roughness, Finishes)
  └── 4. 360° Turnaround Views (Resolving 100% of Occluded Angles)
                  │
                  ▼
[ Blender Native Precision Orthographic CAD Reconstruction ]
                  │
                  ▼
   [ Closed-Loop Optical Verification Gate (IoU ≥ 99%, MAE < 2%) ]
```

#### A. 4-View Orthographic Blueprint
- Generates aligned **Front, Side, Top, and Back** views on a neutral background with explicit bounding-box dimensions ($L, W, H$ in millimeters).
- **Zero-Drift Alignment:** Loading orthographic views into Blender's orthographic viewports (`NUMPAD 1`, `NUMPAD 3`, `NUMPAD 7` = Front, Right, Top <!-- ease:source S6 anchor="Top Numpad7, Front Numpad1, Right Numpad3" -->) removes perspective distortion in the Blender view; it cannot remove distortion already present in a supplied sheet, so "$0.00^\circ$ perspective error" holds only if the source drawing is a true orthographic projection <!-- ease:source UNVERIFIED reason="true-orthographic status of generated sheets is not verifiable" -->.

#### B. Mechanical Exploded View
- Deconstructs the monolithic outer shape into discrete, manufactured components (list below is specific to the quadruped example; the components are generated inferences, not measured hidden geometry <!-- ease:source S2 anchor="Do not promise exact hidden geometry from insufficient evidence" -->):
  1. Outer aerodynamic polymer cowlings.
  2. Internal structural CNC chassis lattice.
  3. Modular quick-release battery pack.
  4. Cycloidal/harmonic drive actuators with planetary gearing.
  5. Structural carbon-fiber limbs, pin hinges, and elastomer feet.
- Enforces proper mechanical assembly hierarchy, making the model animation-ready, rig-ready, and 3D print-ready.

#### C. Parts Catalog & CMF Matrix
- Defines art-directed Principled BSDF input values for each component (starting points, not measured material constants; the earlier text called them "exact physical OpenPBR parameters", but Blender 5.2.0 has no OpenPBR node type and the Principled BSDF inputs are named `Base Color`, `Metallic`, `Roughness`, `Coat Weight` <!-- ease:source S11 anchor="Principled inputs list; OpenPBR node types []" --><!-- ease:source S10 anchor="Principled BSDF layers: coat, sheen, emission" -->):
  - **CNC Aluminum 6061:** `Metallic = 1.0`, `Roughness = 0.18–0.22`, `Base Color = #D0D4D9`. <!-- ease:source UNVERIFIED reason="material values are art-directed, no reflectance source" -->
  - **Molded ABS-PC:** `Metallic = 0.0`, `Roughness = 0.38–0.42`, `Base Color = #6E7882`. <!-- ease:source UNVERIFIED reason="art-directed value" -->
  - **High-Modulus Carbon Fiber:** `Metallic = 0.15`, `Roughness = 0.28`, `Coat Weight = 0.65` (renamed from "Clear Coat"; 5.2.0 input name is `Coat Weight`), $2\times 2$ Twill weave. <!-- ease:source UNVERIFIED reason="art-directed value" -->
  - **SBR Rubber (60 Shore A):** `Metallic = 0.0`, `Roughness = 0.62`, `Base Color = #0C0C0D`. <!-- ease:source UNVERIFIED reason="art-directed value; Shore A hardness has no visual-parameter mapping" -->

---

### 3. Blender Native CAD Precision Reconstruction

#### A. Viewport Background Plane Setup
Load the orthographic reference as image empties (the 5.2.0 way to place a reference image: an Empty with `empty_display_type='IMAGE'` and `.data = image`, verified <!-- ease:source S11 anchor="image empty EMPTY IMAGE True" -->) and create orthographic cameras that look along the three principal axes. The function below creates only the cameras (its `blueprint_path` argument is unused); it needs `import math`, which the previous version omitted:

```python
import bpy, math

def add_reference_image_empty(name: str, image_path: str):
    """Place a reference image as an Image empty (call once per view and rotate/offset it to its plane)."""
    img = bpy.data.images.load(image_path)
    ref = bpy.data.objects.new(name, None)
    ref.empty_display_type = 'IMAGE'
    ref.data = img
    bpy.context.scene.collection.objects.link(ref)
    return ref

def setup_ortho_blueprint(blueprint_path: str = ""):
    """Creates orthographic Front/Side/Top reference cameras (verified view directions: Front looks +Y from y=-5, Side looks -X from x=+5, Top looks -Z from z=+5)."""
    #  [ease:source S11 anchor="module cam Front looks (0,1,0); Side (-1,0,0); Top (0,0,-1)"]
    views = {
        "Front": (0, -5.0, 0, (math.radians(90), 0, 0)),
        "Side":  (5.0, 0, 0,  (math.radians(90), 0, math.radians(90))),
        "Top":   (0, 0, 5.0,  (0, 0, math.radians(-90)))
    }
    for name, (x, y, z, rot) in views.items():
        cam_data = bpy.data.cameras.new(f"Ref_Cam_{name}")
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = 1.2
        cam_obj = bpy.data.objects.new(f"Ref_Cam_{name}", cam_data)
        cam_obj.location = (x, y, z)
        cam_obj.rotation_euler = rot
        bpy.context.scene.collection.objects.link(cam_obj)
```

#### B. Hard Surface Modeling & Normal Preservation
1. **Weighted Normal Modifier:** Project rule for CAD-like planar surfaces to prevent shading pinching near chamfers; the manual says it "can be useful to make some faces appear very flat during shading" <!-- ease:source S8 anchor="Weighted Normal Modifier changes custom normals; flat shading" --> (calling it "mandatory" is a local convention <!-- ease:source UNVERIFIED reason="'mandatory' is a project convention, not a Blender requirement" -->).
2. **Bevel Modifier by Weight:** Keep mechanical edges crisp with calibrated edge bevel weights ($0.0\text{--}1.0$; weight 0.0 applies no bevel) rather than destructive mesh beveling <!-- ease:source S9 anchor="Limit Method Weight: use an attribute; weight 0.0 no bevel" --><!-- ease:source S11 anchor="BevelModifier limit_method NONE ANGLE WEIGHT VGROUP" -->.
3. **Bilateral Symmetry:** Use the Mirror Modifier with clipping across the $YZ$ plane (mirror along X, the modifier's default axis) so left and right are symmetric in the Front view used above. **Correction:** the previous text said "XZ plane", which would mirror front/back under this module's own camera convention <!-- ease:source S11 anchor="mirror defaults use_axis (True, False, False)" --><!-- ease:source S7 anchor="Mirror Modifier" -->.

---

### 4. Closed-Loop Optical Verification Gate

**Metric definitions.** Silhouette IoU is the Jaccard overlap of two foreground masks, area(A ∩ B) / area(A ∪ B), the same ratio the PASCAL VOC challenge uses for boxes with a 50% acceptance threshold <!-- ease:source S15 anchor="Eq. (3): area(Bp ∩ Bgt) / area(Bp ∪ Bgt); overlap threshold 50%" --><!-- ease:source S16 anchor="Jaccard index definition" -->. MAE is the mean absolute per-channel pixel difference (`ImageChops.difference` returns abs(image1 - image2); `ImageStat.Stat.mean` is the per-band average) <!-- ease:source S17 anchor="difference: out = abs(image1 - image2)" --><!-- ease:source S18 anchor="Stat.mean: average pixel level per band" -->. An optional structural metric is SSIM: Wang et al. use an 11×11 circular Gaussian window with sigma 1.5, K1 = 0.01, K2 = 0.03, L = 255 for 8-bit images and report the mean over local windows (MSSIM) <!-- ease:source S14 anchor="Section III: 11x11 Gaussian, std 1.5; Eq. (13), Eq. (17) MSSIM; Fig. 3 caption K1=0.01, K2=0.03" --> (formula glyphs of Eq. (13) are not text-extractable from the PDF layer used here; the constants and window were verified).

```python
"""
Illustrative gate (no such file exists under scripts/). Run with the HOST python3 + Pillow,
not Blender's bundled Python, which has no PIL (observed 5.2.0)  # ease:source S11 anchor="PIL in blender python NO".
Computes silhouette IoU and mean absolute error ONLY. It does not compute Canny edge overlap or a
heatmap (the previous docstring promised both). Diagnostic, not a fidelity verdict.
"""
from PIL import Image, ImageChops, ImageStat

def _flatten_on_white(im):
    return Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im.convert("RGBA")).convert("RGB")

def _mask(im, bg_threshold=245):
    """Foreground mask: alpha > 127 when the image has alpha, else luminance < bg_threshold (white background assumed)."""
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        return im.convert("RGBA").getchannel("A").point(lambda a: 255 if a > 127 else 0).convert("1")
    return im.convert("L").point(lambda p: 255 if p < bg_threshold else 0).convert("1")

def evaluate_visual_fidelity(ref_path: str, render_path: str, bg_threshold: int = 245) -> dict:
    with Image.open(ref_path) as ref_img, Image.open(render_path) as ren_img:
        ref, ren = ref_img.copy(), ren_img.copy()
    assert abs(ref.width / ref.height - ren.width / ren.height) < 1e-3, "aspect mismatch: resize would distort"
    ren = ren.resize(ref.size, Image.LANCZOS)
    mae = sum(ImageStat.Stat(ImageChops.difference(_flatten_on_white(ref), _flatten_on_white(ren))).mean) / 3.0
    a, b = _mask(ref, bg_threshold), _mask(ren, bg_threshold)
    inter = ImageChops.logical_and(a, b).histogram()[255]
    union = ImageChops.logical_or(a, b).histogram()[255]
    iou = inter / union if union else 1.0
    return {
        "silhouette_iou_percent": round(iou * 100.0, 2),
        "mean_absolute_error_8bit": round(mae, 2),
        "within_module_thresholds": bool(iou >= 0.98 and mae < 5.0),   # heuristic thresholds, see table
    }
```

**Why the shipped gate was replaced.** On synthetic discs (Pillow 12.3.0) the shipped function returned IoU 100.0% for two RGBA renders whose silhouettes were shifted by 25 px (true IoU 52.33%), because converting a transparent RGBA render to RGB turns the background black and the "foreground" mask covers the whole frame; it also gave IoU 20.01% and MAE 203.97 for an identical disc on white versus transparent <!-- ease:source S12 anchor="RGBA transparent: shifted 25px original=(100.0, 3.76) corrected=(52.33, 28.18)" -->. The corrected code returned 100.0/0.0 and 52.33/28.18 for those cases <!-- ease:source S13 anchor="corrected IoU/MAE on the same cases" -->. The key `passed_99_threshold` was also misnamed: its test used 0.98, not 0.99.

---

### 5. Industrial Quality & Fidelity Checklist

<!-- ease:source UNVERIFIED reason="all thresholds in this table (1.0 mm, 98%) are local heuristics without a primary source; Canny edge overlap has no implementation here" -->

| Verification Gate | Threshold Standard | Failure Impact | Mitigation |
|---|---|---|---|
| **Orthographic Blueprint Alignment** | Landmark error $<1.0\,\text{mm}$ | Asymmetric stance, bent chassis | Align viewport planes before any beveling |
| **Silhouette IoU (Visible View)** | $\ge 98.0\%$ | 3D mesh deviates from user photograph | Adjust camera focal length ($F$) and pitch angle |
| **Edge Alignment (Canny Gradient)** | $\ge 98.0\%$ overlap | Chamfers or fillets too thick/thin | Adjust Bevel modifier radius on outer cowlings |
| **PBR Albedo Integrity** | Delighted Albedo (No baked shadows) | Asset looks unnatural when relit | Calibrate materials via CMF lookup table |
| **Component Hierarchy** | 100% discrete subassemblies | Mesh is monolithic, cannot rig or print | Follow Exploded View component decomposition |

---

### See Also
- [export-interchange](export-interchange.md) — GLB, USD, and STEP interchange standards.
- [product-viz-and-shots](product-viz-and-shots.md) — Studio three-point lighting, turntable cameras, and Cycles delivery.
- [3d-printing](3d-printing.md) — Watertight 2-manifold tolerances for mechanical assembly.

## Failure Modes (Mandatory)
- **Gate reports 100% silhouette IoU for a visibly shifted render** — cause: RGBA transparent render converted to RGB, background black, mask covers the frame — fix: build masks from alpha (corrected `_mask`) <!-- ease:source S12 anchor="RGBA transparent shifted 25px: original IoU 100.0 vs corrected 52.33" -->.
- **MAE is huge (about 200 of 255) for a correct render** — cause: transparent background compared against a white-background reference without flattening — fix: composite on white before differencing <!-- ease:source S12 anchor="ref RGB vs candidate RGBA transparent: original MAE 203.97, corrected 0.0" -->.
- **`NameError: name 'math' is not defined` when running the blueprint camera setup** — cause: the previous snippet used `math.radians` without importing it — fix: `import bpy, math` (corrected).
- **Pipeline stops at the Nano Banana step in production** — cause: hosted generative-model calls are forbidden by the Native Asset Policy — fix: build from the owner-supplied references with the native route; record the generated sheet, if any, as secondary authority <!-- ease:source S1 anchor="No hosted-model call may enter production" -->.
- **A build is called "99% faithful" from IoU/MAE** — cause: pixel similarity treated as a fidelity verdict — fix: per-feature PASS/FAIL/UNKNOWN with proof view and falsifier <!-- ease:source S3 anchor="Pixel similarity is not a fidelity test" -->.

## Sources
- [S1] Repo .project-agent.md (Native Asset Policy, binding rules) — .project-agent.md — captured 2026-10-13 — sha256 8cde6609763c6f287717b23587c6f542f195e506e1c9fa283f40b3eaf65af82c
- [S2] Repo skill blender-image-to-3d SKILL.md — .agents/skills/blender-image-to-3d/SKILL.md — captured 2026-10-13 — sha256 297032c6f30c389ad135a4c71973357f290939ff45d1793d05c597e96a39b15b
- [S3] Repo blender-image-to-3d review-rubric.md — .agents/skills/blender-image-to-3d/references/review-rubric.md — captured 2026-10-13 — sha256 4a9c962fe81b716f4d28188e7f2a23c5a9e2d898e9329bedaef0b9ef1f17375b
- [S4] Repo builds/quadruped-02/README.md (build that used the Nano Banana dossier) — builds/quadruped-02/README.md — captured 2026-10-13 — sha256 dc6e3c6da526603cc5d99b3cfbc9e087867c046f51b48211740c10335f1ebc94
- [S5] Repo research/how-image-to-3d-works.md — research/how-image-to-3d-works.md — captured 2026-10-13 — sha256 896944614081676026bbb053714fd5de1e6abe99ab95d210cc0a7ac92c681264
- [S6] Blender 5.2 Manual: Viewpoint (numpad views) — https://docs.blender.org/manual/en/latest/editors/3dview/navigate/viewpoint.html → knowledge/_evidence/kb-261013/w5-man-navigate-viewpoint.html — captured 2026-10-13 — sha256 554ff160c2c1e6ffa96e242331125fd2f276ce48e14e75d233909f5a515eca34
- [S7] Blender 5.2 Manual: Mirror Modifier — https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/mirror.html → knowledge/_evidence/kb-261013/w5-man-mirror-modifier.html — captured 2026-10-13 — sha256 60a1a27ec1b7237f874647b7945efb8814bee839e0d89baac5bedc7b9caf119f
- [S8] Blender 5.2 Manual: Weighted Normal Modifier — https://docs.blender.org/manual/en/latest/modeling/modifiers/normals/weighted_normal.html → knowledge/_evidence/kb-261013/w5-man-weighted-normal.html — captured 2026-10-13 — sha256 1d741bc1cd64d91f47d269b413e0bd3bb29574a0b33b194ab538c278b13d7920
- [S9] Blender 5.2 Manual: Bevel Modifier — https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html → knowledge/_evidence/kb-261013/w5-man-bevel-modifier.html — captured 2026-10-13 — sha256 ef8e2b73ff7cbb65012f068c11533820e8b78ad7a299cc2d7739c9e49a092374
- [S10] Blender 5.2 Manual: Principled BSDF — https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html → knowledge/_evidence/kb-261013/w5-man-principled.html — captured 2026-10-13 — sha256 9cf2bfbbce180c70fd3a5ba4fd5f57ccc83e6d2a06e7145d91e7c4055dfa65cf
- [S11] Blender 5.2.0 LTS runtime probe 4 (RNA descriptions, Principled inputs, modifier defaults); script w5-probe4-blender-52-rna-descriptions.py — local run /Applications/Blender.app → knowledge/_evidence/kb-261013/w5-blender-52-runtime-probe4-output.txt — captured 2026-10-13 — sha256 bcefc0f57b0b5accab6fe6d589b642ca522734407791b0eb4b795b0280d7c54e
- [S12] Silhouette IoU/MAE gate self-test, shipped vs corrected; script w5-fidelity-gate-selftest.py (Pillow 12.3.0) — local run python3 → knowledge/_evidence/kb-261013/w5-fidelity-gate-selftest-output.txt — captured 2026-10-13 — sha256 ed6b8d4f39a6d4e1930dbdcf9cb0796c78954af1aa6cb2ae5589e5df80808c05
- [S13] Corrected gate code block executed from this module on synthetic images (host python3, Pillow 12.3.0); script w5-gate-final-codeblock-test.py — local run python3 → knowledge/_evidence/kb-261013/w5-gate-final-codeblock-test-output.txt — captured 2026-10-13 — sha256 edd68c14f88a72dea79f1d653237af79f6f893f48288c80e40524f6223c1bc1f
- [S14] Wang, Bovik, Sheikh, Simoncelli, Image Quality Assessment: From Error Visibility to Structural Similarity, IEEE TIP 13(4), 2004 (author reprint) — https://www.cns.nyu.edu/pub/eero/wang03-reprint.pdf → knowledge/_evidence/kb-261013/w5-ssim-wang2004.pdf — captured 2026-10-13 — sha256 d643c9f72b90627ed206df46be1e91827e1423281903bf4dc1378e27bc303e2d
- [S15] Everingham et al., The PASCAL Visual Object Classes (VOC) Challenge, IJCV 88, 2010 — http://host.robots.ox.ac.uk/pascal/VOC/pubs/everingham10.pdf → knowledge/_evidence/kb-261013/w5-voc-everingham2010.pdf — captured 2026-10-13 — sha256 2286ee0b336806b00e8f84499b2858d28a88e976c8b5000a628e003fe96c410b
- [S16] Wikipedia: Jaccard index (community reference) — https://en.wikipedia.org/wiki/Jaccard_index → knowledge/_evidence/kb-261013/w5-wiki-jaccard.html — captured 2026-10-13 — sha256 35aea239c3fa5b59e5cdf9d2ec628fae4223368b6ed0cce43d29205128596b12
- [S17] Pillow docs: ImageChops — https://pillow.readthedocs.io/en/stable/reference/ImageChops.html → knowledge/_evidence/kb-261013/w5-pillow-imagechops.html — captured 2026-10-13 — sha256 295ee91cb218f09252a2930eb32f80405d04cb9868e2a89a3bd6301565ac8cdb
- [S18] Pillow docs: ImageStat — https://pillow.readthedocs.io/en/stable/reference/ImageStat.html → knowledge/_evidence/kb-261013/w5-pillow-imagestat.html — captured 2026-10-13 — sha256 300dc371ade2ba30fed8db0e0ca7e3f16f0c4651dce038b2f0a9e7a7ea0bc136
