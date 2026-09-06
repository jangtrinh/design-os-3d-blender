# Human Anatomical Proportions, Craniometrics & Parametric Morphology

> **Document ID:** `RES-CHAR-ANAT-01`  
> **Status:** Production Character Architecture Specification  
> **Target Platform:** Blender 5.2.0 LTS (Data-API, Headless-Safe)  
> **Primary Standards & Citations:** Loomis (1943 - *Figure Drawing for All It's Worth*), Bridgman (1920 - *Constructive Anatomy*), Farkas (1994 - *Anthropometry of the Head and Face*), Pavlakos et al. (2019 - *SMPL-X: Expressive Body Capture*), Li et al. (2017 - *FLAME: Learning a Model of Facial Shape and Expression*), ISO 7250-1:2017 (Basic human body measurements for technological design).
> **Audit note (2026-09-06 onboarding audit):** every `bpy` name in this file was introspected in a `--factory-startup` Blender 5.2.0 LTS. Anatomical figures and bibliographic entries are not runtime-checkable; the ones the audit could not confirm carry an inline `UNVERIFIED (2026-09-06 audit)` marker.


---

## 1. Classical Proportional Canons & Head-Unit (HU) Metrics

### 1.1 The Head-Unit Metric Scale
In digital character modeling, all linear dimensions are normalized to the vertical cranial height $H_{head}$ (measured from the vertex of the cranium to the inferior border of the chin/gnathion):
$$\text{HU} = H_{head} \equiv 1.0$$
Total stature height $H_{total}$ varies deterministically across aesthetic style and physiological age:

| Demographic / Style Archetype | Stature ($H_{total}$ in HU) | Head ($H_{head}$) | Torso (Clavicle to Pubis) | Inseam (Pubis to Soles) | Shoulder Span (Biacromial) |
|---|---|---|---|---|---|
| **Classical / Realistic Adult** | $7.50\text{–}8.00\text{ HU}$ | $1.00\text{ HU}$ | $2.50\text{–}2.75\text{ HU}$ | $3.75\text{–}4.00\text{ HU}$ | $2.00\text{ HU}$ (M) / $1.65\text{ HU}$ (F) |
| **Heroic / Stylized Comic** | $8.50\text{–}9.00\text{ HU}$ | $1.00\text{ HU}$ | $3.00\text{ HU}$ | $4.50\text{–}5.00\text{ HU}$ | $2.30\text{–}2.50\text{ HU}$ |
| **Adolescent (12–14 yrs)** | $6.50\text{–}7.00\text{ HU}$ | $1.00\text{ HU}$ | $2.25\text{ HU}$ | $3.25\text{–}3.50\text{ HU}$ | $1.50\text{ HU}$ |
| **Child (5–7 yrs)** | $5.50\text{–}6.00\text{ HU}$ | $1.00\text{ HU}$ | $2.00\text{ HU}$ | $2.50\text{–}2.75\text{ HU}$ | $1.30\text{ HU}$ |
| **Toddler / Infant (1–2 yrs)** | $4.00\text{–}4.50\text{ HU}$ | $1.00\text{ HU}$ | $1.75\text{ HU}$ | $1.50\text{ HU}$ | $1.10\text{ HU}$ |
| **Stylized / Chibi Figurine** | $2.50\text{–}3.50\text{ HU}$ | $1.00\text{ HU}$ | $0.80\text{–}1.00\text{ HU}$ | $0.70\text{–}1.20\text{ HU}$ | $1.00\text{ HU}$ |

```
Human Stature Canon (8-Head Realistic Adult):
  0 HU ───► Vertex of Cranium
  1 HU ───► Menton / Chin (Submentale)
  2 HU ───► Nipple Line / 4th Intercostal Space
  3 HU ───► Umbilicus (Navel) / Iliac Crest
  4 HU ───► Pubic Symphysis / Greater Trochanter (Midpoint of Body: 50% Stature)
  5 HU ───► Mid-Thigh
  6 HU ───► Inferior Border of Patella (Knee Joint Axis)
  7 HU ───► Lower Gastrocnemius Bellies (Mid-Calf)
  8 HU ───► Plantar Surface of Foot (Sole)
```

---

## 2. Craniometrics & Facial Landmark Morphology (Farkas 1994)

### 2.1 The Frankfort Horizontal Plane
Craniofacial orientation is canonically defined by the Frankfort Plane passing through:
1. The **Porion** (superior margin of the external acoustic meatus).
2. The **Orbitale** (inferior margin of the bony orbit).
In Blender CAD space, this plane is leveled parallel to the global $XY$ plane ($Z = \text{const}$).

### 2.2 The Rule of Facial Thirds (Vertical Division)
Vertical facial height is divided into three equal anthropometric thirds:
1. **Upper Third (Trichion to Glabella):** $h_{upper} \approx 0.33 \times H_{face}$. Forehead region.
2. **Middle Third (Glabella to Subnasale):** $h_{mid} \approx 0.33 \times H_{face}$. Orbit, nasal bridge, and nose tip.
3. **Lower Third (Subnasale to Gnathion/Menton):** $h_{lower} \approx 0.33 \times H_{face}$. Oral fissure, philtrum, and mandible.
   - The lower third subdivides further: Subnasale to Stomion (upper lip) = $1/3$; Stomion to Gnathion (lower lip + chin) = $2/3$.

### 2.3 The Rule of Facial Fifths (Transverse Division)
The transverse width of the face at the level of the palpebral fissures equals five ocular widths ($D_{eye} \approx 30\text{–}32\text{ mm}$ in adults):
$$W_{face} = 5 \times D_{eye}$$
- **1st Fifth:** Lateral temporal border to Exocanthion (lateral eye corner).
- **2nd Fifth:** Palpebral fissure width (Exocanthion to Endocanthion).
- **3rd Fifth:** Intercanthal distance (Endocanthion to Endocanthion), which equals the width of the nasal alar base ($W_{alare} = D_{eye}$).
- **4th Fifth:** Contralateral eye width.
- **5th Fifth:** Exocanthion to contralateral temporal border.
- **Oral Fissure Width ($W_{mouth}$):** Subtends precisely between the medial limbus margins of the irises in direct forward gaze ($\approx 1.5 \times D_{eye}$).

```
Facial Fifths Transverse Grid:
┌───────┬───────┬───────┬───────┬───────┐
│ Temp- │ Eye L │ Inter-│ Eye R │ Temp- │
│ oral  │ (D)   │ canth │ (D)   │ oral  │
│ (D)   │       │ (D)   │       │ (D)   │
└───────┴───────┴───────┴───────┴───────┘
        ◄────── Alar Base ──────►
            (W_alar = D)
```

---

## 3. Sexual Dimorphism & Biomechanical Skeletal Angles

### 3.1 Biacromial vs Bi-iliac Index
The skeletal envelope difference between male and female morphology is governed by the ratio of Biacromial breadth (shoulder width $W_{shoulder}$) to Bi-iliac breadth (pelvic width $W_{pelvis}$):
$$\mathcal{I}_{dimorph} = \frac{W_{shoulder}}{W_{pelvis}}$$
- **Adult Male:** $W_{shoulder} \approx 390\text{–}410\text{ mm}$, $W_{pelvis} \approx 270\text{–}290\text{ mm} \implies \mathcal{I}_{male} \approx 1.40\text{–}1.45$ (Inverted trapezoid / "V-taper").
- **Adult Female:** $W_{shoulder} \approx 350\text{–}365\text{ mm}$, $W_{pelvis} \approx 290\text{–}310\text{ mm} \implies \mathcal{I}_{female} \approx 1.15\text{–}1.20$ (Hourglass / pelvic dominance).

### 3.2 Pelvic Tilt and the Quadriceps Angle ($Q$-Angle)
1. **Pelvic Anteversion (Anterior Pelvic Tilt):**
   - Male: $4^\circ\text{–}8^\circ$ inclination.
   - Female: $10^\circ\text{–}15^\circ$ inclination, causing greater lumbar lordosis and prominent sacral shelf.
2. **Quadriceps Angle ($Q$-Angle):**
   Angle formed between the vector connecting the Anterior Superior Iliac Spine (ASIS) to the patellar midpoint and the vector from patella to tibial tuberosity:
   - **Male $Q$-Angle:** $10^\circ\text{–}14^\circ$ ($12^\circ$ nominal).
   - **Female $Q$-Angle:** $15^\circ\text{–}19^\circ$ ($17^\circ$ nominal), necessitated by wider acetabular distance.
3. **Elbow Carrying Angle (Cubitus Valgus):**
   - Full extension valgus angle between humerus longitudinal axis and ulna: Male $\approx 5^\circ\text{–}10^\circ$; Female $\approx 10^\circ\text{–}15^\circ$ (clears wider pelvic crests during swing phase of gait).

---

## 4. Mathematical Parametric Morphology: SMPL-X & FLAME

> **Native Asset Policy:** SMPL-X and FLAME are cited here as published *shape-space
> mathematics*. Their model files are separately licensed third-party assets — this project
> builds meshes natively and must not download or vendor them.

### 4.1 Statistical Shape Space ($\mathbf{\beta}$) Representation
Per **SMPL-X** (Pavlakos et al. 2019) and **FLAME** (Li et al. 2017), the rest-pose mesh vertex positions $\mathbf{T}(\mathbf{\beta}) \in \mathbb{R}^{3N}$ are modeled via Principal Component Analysis (PCA) over scanned population databases:
$$\mathbf{T}(\mathbf{\beta}) = \bar{\mathbf{T}} + \sum_{k=1}^{|\mathbf{\beta}|} \beta_k \mathbf{S}_k$$
*Where:*
- $\bar{\mathbf{T}}$ = Mean humanoid template mesh ($N = 10,475$ vertices in SMPL-X; the FLAME
  count given here as $3{,}857$ is UNVERIFIED (2026-09-06 audit) — check it against Li et al.
  (2017) before quoting it).
- $\mathbf{\beta} = [\beta_1, \beta_2, \dots, \beta_{|\mathbf{\beta}|}]^T \in \mathbb{R}^{|\mathbf{\beta}|}$ = Linear shape coefficient vector (typically $|\mathbf{\beta}| = 10\text{–}300$).
- $\mathbf{S}_k \in \mathbb{R}^{3N}$ = Orthonormal principal shape displacement eigenvectors.

### 4.2 Joint Location Prediction from Shape
In skeletal rigging, joint center coordinates $\mathbf{J}(\mathbf{\beta}) \in \mathbb{R}^{3 \times K}$ cannot be fixed; they are linearly regressed from the shaped mesh vertices using a learned sparse matrix $\mathcal{W} \in \mathbb{R}^{K \times N}$:
$$\mathbf{J}_j(\mathbf{\beta}) = \sum_{i=1}^{N} \mathcal{W}_{j, i} \mathbf{T}_i(\mathbf{\beta})$$
This guarantees that as a character's height, muscularity, or limb length changes via $\mathbf{\beta}$, the underlying armature bone joints automatically translate to the exact rotational centers of the corresponding skeletal joints.

---

## 5. Mathematical & Anthropometric Citations

1. **Loomis, A. (1943)** — *Figure Drawing for All It's Worth*, The Viking Press, New York.
2. **Bridgman, G. B. (1920)** — *Constructive Anatomy*, Bridgman Publishers, Pelham, NY.
3. **Farkas, L. G. (1994)** — *Anthropometry of the Head and Face*, 2nd Edition, Raven Press, New York, ISBN 978-0-7817-0159-4.
4. **Pavlakos, G., Choutas, V., Ghorbani, N., Bolkart, T., Osman, A. A., Tzionas, D., & Black, M. J. (2019)** — *Expressive Body Capture: 3D Hands, Face, and Body from a Single Image*, IEEE Conference on Computer Vision and Pattern Recognition (CVPR 2019), pp. 10975-10985.
5. **Li, T., Bolkart, T., Black, M. J., Li, H., & Romero, J. (2017)** — *Learning a model of facial shape and expression from 4D scans*, ACM Transactions on Graphics (SIGGRAPH Asia 2017), 36(6), Article 194.
6. **ISO 7250-1:2017** — *Basic human body measurements for technological design — Part 1: Body measurement definitions and landmarks.*
7. **Tilley, A. R., & Henry Dreyfuss Associates (2001)** — *The Measure of Man and Woman: Human Factors in Design*, John Wiley & Sons, ISBN 978-0-471-08180-7.
