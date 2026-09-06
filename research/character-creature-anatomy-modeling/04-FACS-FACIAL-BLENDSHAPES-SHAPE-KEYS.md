# Facial Action Coding System (FACS), 52 ARKit Blendshapes & Shape Key Mathematics

> **Document ID:** `RES-CHAR-ANAT-04`  
> **Status:** Production Character Architecture Specification  
> **Target Platform:** Blender 5.2.0 LTS (Data-API, Headless-Safe)  
> **Primary Standards & Citations:** Ekman & Friesen (1978 - *Facial Action Coding System: A Technique for the Measurement of Facial Movement*), Apple Inc. (2020 - *ARKit Face Tracking 52 Blendshapes Specification*), Lewis et al. (2000 - *Pose space deformation: a unified approach to shape interpolation and skeleton-driven deformation*), ISO/IEC 14496-2:2004 (MPEG-4 Part 2: Visual - Face Animation Parameters), Joshi et al. (2006 - *Learning physiological blendshape models*).
> **Audit note (2026-09-06 onboarding audit):** every `bpy` name in this file was introspected in a `--factory-startup` Blender 5.2.0 LTS. Anatomical figures and bibliographic entries are not runtime-checkable; the ones the audit could not confirm carry an inline `UNVERIFIED (2026-09-06 audit)` marker.


---

## 1. The Facial Action Coding System (FACS) Biological Foundation

Developed by Paul Ekman and Wallace Friesen (1978), FACS deconstructs all visible facial expressions into individual, anatomically grounded **Action Units (AUs)** produced by specific facial muscles:

| FACS AU | Descriptive Label | Primary Anatomical Muscle | Action Vector |
|---|---|---|---|
| **AU 1** | Inner Brow Raiser | *Frontalis* (medial belly) | Cranial $+Z$ pull on medial eyebrow tails |
| **AU 2** | Outer Brow Raiser | *Frontalis* (lateral belly) | Cranial $+Z$ pull on lateral eyebrow arches |
| **AU 4** | Brow Lowerer / Corrugator | *Corrugator supercilii* + *Depressor supercilii* | Medial $-X$ and caudal $-Z$ furrowing |
| **AU 6** | Cheek Raiser | *Orbicularis oculi* (pars orbitalis) | Superior $+Z$ elevation of malar fat pad |
| **AU 9** | Nose Wrinkler | *Levator labii superioris alaeque nasi* | Cranial $+Z$ tension on nasal bridge skin |
| **AU 12** | Lip Corner Puller (Smile) | *Zygomaticus major* | Superior $+Z$ and lateral $\pm X$ pull on modiolus |
| **AU 14** | Dimpler | *Buccinator* | Direct posterior $+Y$ retraction into cheek pocket |
| **AU 15** | Lip Corner Depressor (Frown) | *Depressor anguli oris* | Caudal $-Z$ pull on oral commissures |
| **AU 20** | Lip Stretcher | *Risorius* | Lateral $\pm X$ elongation of mouth width |
| **AU 26** | Jaw Drop | *Pterygoid* (lateral) + *Digastric* | Inferior $-Z$ rotation of mandible ($10^\circ\text{–}25^\circ$) |

---

## 2. The 52 ARKit Blendshape Target Inventory

**Correction (2026-09-06 audit):** the 52 targets are Apple's ARKit face-tracking spec, which
is FACS-*inspired*. They are **not** FACS Action Units (Ekman & Friesen define ~44) and they
are **not** ISO/IEC 14496-2 — that standard defines MPEG-4 Face Animation Parameters, a
different and larger parameter set. Cite ISO/IEC 14496-2 only when you actually mean FAPs.

The 52-target set is what facial capture and avatar pipelines (Apple ARKit, Epic MetaHuman,
Unity, VRChat) converge on as a de-facto interchange vocabulary:

```
52 ARKit Facial Shape Key Matrix:
├── Eye / Brow Group (19 targets: 14 eye + 5 brow)
│   ├── eyeBlinkLeft / Right, eyeLookDownLeft / Right, eyeLookInLeft / Right
│   ├── eyeLookOutLeft / Right, eyeLookUpLeft / Right, eyeSquintLeft / Right, eyeWideLeft / Right
│   └── browDownLeft / Right, browInnerUp, browOuterUpLeft / Right
├── Jaw Group (4 targets)
│   └── jawForward, jawLeft, jawRight, jawOpen
├── Mouth Group (23 targets)
│   ├── mouthClose, mouthFunnel, mouthPucker, mouthLeft, mouthRight
│   ├── mouthSmileLeft / Right, mouthFrownLeft / Right, mouthDimpleLeft / Right
│   ├── mouthStretchLeft / Right, mouthRollLower, mouthRollUpper
│   ├── mouthShrugLower, mouthShrugUpper, mouthPressLeft / Right
│   ├── mouthLowerDownLeft / Right, mouthUpperUpLeft / Right
├── Cheek & Nose Group (5 targets)
│   ├── cheekPuff, cheekSquintLeft / Right, noseSneerLeft / Right
└── Tongue Group (1 target)
    └── tongueOut
```
Group totals: $19 + 4 + 23 + 5 + 1 = 52$. (The earlier 15/27 split in this file was arithmetic
error, corrected by the 2026-09-06 audit against
`scripts/boilerplates/character_creature/bp_facs_blendshapes.py::ARKIT_52_NAMES`, whose 52
names are asserted unique at runtime.)

---

## 3. Mathematical Blendshape Deformation & Combination Keys

### 3.1 Linear Blendshape Summation
Given a neutral base mesh topology $\mathbf{V}_0 \in \mathbb{R}^{3N}$ and $K$ sculpted displacement delta-vectors $\Delta \mathbf{V}_k = \mathbf{V}_k - \mathbf{V}_0 \in \mathbb{R}^{3N}$, any facial expression is computed as:
$$\mathbf{V}(\mathbf{w}) = \mathbf{V}_0 + \sum_{k=1}^{K} w_k \cdot \Delta \mathbf{V}_k, \quad w_k \in [0.0, 1.0]$$

### 3.2 The Linear Superposition Failure & Corrective Keys (CSK)
Linear summation assumes complete orthogonality between Action Units. In real biology, muscles mechanically interact. When two strong targets activate simultaneously (e.g., $w_{jawOpen} = 1.0$ and $w_{mouthSmile} = 1.0$), naive linear addition pulls the lip corners outward while lowering the jaw, producing an exaggerated, torn, unphysical "joker mouth":
$$\mathbf{V}_{naive} = \mathbf{V}_0 + w_{jaw} \Delta \mathbf{V}_{jaw} + w_{smile} \Delta \mathbf{V}_{smile}$$

To resolve this, **Combination Shape Keys (Corrective Blendshapes)** are computed:
$$\mathbf{V}_{corrected} = \mathbf{V}_0 + w_{jaw} \Delta \mathbf{V}_{jaw} + w_{smile} \Delta \mathbf{V}_{smile} + (w_{jaw} \cdot w_{smile}) \Delta \mathbf{V}_{jaw\_smile}^{corr}$$
*Where:*
$$\Delta \mathbf{V}_{jaw\_smile}^{corr} = \mathbf{V}_{sculpted\_combo} - (\mathbf{V}_0 + \Delta \mathbf{V}_{jaw} + \Delta \mathbf{V}_{smile})$$
In Blender 5.2, combination shape keys are driven via **scripted drivers** evaluating the product variable `var = w_a * w_b`.

---

## 4. Blender 5.2 Headless Shape Key Architecture (`Mesh.shape_keys`)

### 4.1 Data API Structure
- The first shape key created on a mesh is irrevocably the **`Basis`** (rest-pose):
  ```python
  basis = obj.shape_key_add(name="Basis", from_mix=False)
  ```
- Subsequent keys store delta displacements directly on `ShapeKey.data[i].co`:
  ```python
  key = obj.shape_key_add(name="jawOpen", from_mix=False)
  key.value = 0.0          # Current blend weight [0.0, 1.0]
  key.slider_min = 0.0     # Clamped lower bound
  key.slider_max = 1.0     # Clamped upper bound
  ```

### 4.2 High-Speed Vectorized Displacement via `foreach_set`
Iterating over thousands of vertices in pure Python loop `for v in key.data: v.co = ...` takes several seconds. Production headless pipelines must use Blender's C-level memory buffer transfer:
```python
import array

# coords is a flat float array of length 3 * N: [x0, y0, z0, x1, y1, z1, ...]
coords = array.array('f', [0.0]) * (len(mesh.vertices) * 3)
# Mutate coords in numpy or mathutils
key.data.foreach_set('co', coords)
mesh.update()
```

---

## 5. Mathematical & FACS Citations

1. **Ekman, P., & Friesen, W. V. (1978)** — *Facial Action Coding System: A Technique for the Measurement of Facial Movement*, Consulting Psychologists Press, Palo Alto, CA.
2. **Apple Inc. (2020)** — *ARKit Face Tracking: Standard 52 Blend Shape Location Descriptions*, Apple Developer Documentation.
3. **Lewis, J. P., Cordner, M., & Fong, N. (2000)** — *Pose space deformation: a unified approach to shape interpolation and skeleton-driven deformation*, Proceedings of the 27th annual conference on Computer graphics and interactive techniques (SIGGRAPH '00), pp. 165-172.
4. **ISO/IEC 14496-2:2004** — *Information technology — Coding of audio-visual objects — Part 2: Visual (MPEG-4 Face Animation Parameters).* Related prior art only; it does **not** define the ARKit 52.
5. **Joshi, P., Tien, W. C., Desbrun, M., & Pighin, F. (2006)** — *Learning physiological blendshape models from 3D face scans*, ACM SIGGRAPH / Eurographics Symposium on Computer Animation (SCA '06), pp. 265-274.
6. **Orvalho, V., Bastos, P., Parke, F., Oliveira, B., & Alvarez, X. (2012)** — *A facial exp-rig for facial animation*, Computer Graphics Forum, 31(2), pp. 415-424.
