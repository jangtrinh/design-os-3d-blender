# Skeletal Kinematics, Biped Locomotion, Skinning & Physically-Based Shading

> **Document ID:** `RES-CHAR-ANAT-06`  
> **Status:** Production Character Architecture Specification  
> **Target Platform:** Blender 5.2.0 LTS (Data-API, Armatures, Headless-Safe)  
> **Primary Standards & Academic Citations:**
> - Parent, R. (2012). *Computer Animation: Algorithms and Techniques* (3rd ed.). Morgan Kaufmann.
> - Craig, J. J. (2005). *Introduction to Robotics: Mechanics and Control* (3rd ed.). Pearson Prentice Hall.
> - Winter, D. A. (2009). *Biomechanics and Motor Control of Human Movement* (4th ed.). John Wiley & Sons.
> - Hildebrand, M. (1976). "Analysis of tetrapod gaits: analysis of the symmetrical gaits of tetrapods." *Physiology*, 20(3), 255–269.
> - Kavan, L., Collins, S., Žára, J., & O'Sullivan, C. (2007). "Skinning with dual quaternions." *ACM Transactions on Graphics (TOG)*, 26(3), 39-es.
> - Lewis, J. P., Cordner, M., & Fong, N. (2000). "Pose space deformation: a unified approach to shape interpolation and skeleton-driven deformation." *SIGGRAPH '00*, 165–172.
> - Christensen, P. H., & Burley, B. (2015). "Approximate reflectance profiles for efficient subsurface scattering." *Pixar Technical Memo*, 15-04.
> - Jimenez, J., Scully, T., Barbosa, N., Donner, C., Alvarez, X., Vieira, T., ... & Gutierrez, D. (2010). "A separable subsurface scattering approach." *Computer Graphics Forum*, 29(6), 1887–1897.
> - Marschner, S. R., Jensen, H. W., Cammarano, M., Narasimhan, S. G., & Hanrahan, P. (2003). "Light scattering from human hair fibers." *ACM Transactions on Graphics (TOG)*, 22(3), 780–791.
> - Chiang, M. J. Y., Bitterli, B., Tappan, C., & Burley, B. (2016). "A practical and controllable hair and fur model for production path tracing." *Computer Graphics Forum*, 35(2), 275–283.
> - d'Eon, E., Francois, G., Hill, M., Letteri, J., & Aubry, J.-M. (2011). "An energy-conserving hair reflectance model." *EGSR 2011*.

> **Audit note (2026-09-06 onboarding audit):** every `bpy` name in this file was introspected in a `--factory-startup` Blender 5.2.0 LTS. Anatomical figures and bibliographic entries are not runtime-checkable; the ones the audit could not confirm carry an inline `UNVERIFIED (2026-09-06 audit)` marker.
>
> **Citation corrections (2026-09-06 audit):**
> - **Kavan et al. (2007)** is *"Skinning with dual quaternions"*. It diagnoses the LBS
>   candy-wrapper collapse and proposes **dual quaternion skinning**; it does **not** propose
>   twist bones. §1.2 below cites it correctly for the artifact — do not cite it as the source
>   of the twist-bone technique (that is production practice, not that paper).
> - **Christensen & Burley (2015)** is the normalized-diffusion / approximate-reflectance
>   profile that Cycles exposes as `subsurface_method = 'BURLEY'`. Blender's `RANDOM_WALK` and
>   `RANDOM_WALK_SKIN` are volumetric path-traced methods, not that profile. See §4.1.
> - **Hildebrand (1976)**, *Physiology* 20(3), 255–269: this journal/volume/page triple could
>   not be confirmed offline. UNVERIFIED (2026-09-06 audit).
> - **Jimenez et al. (2010)**, "A separable subsurface scattering approach", CGF 29(6): the
>   title/venue pairing could not be confirmed offline. UNVERIFIED (2026-09-06 audit).

---

## 1. Character Skeletal Kinematics & Armature Architecture

### 1.1 Hierarchical Forward & Inverse Kinematics
A humanoid character skeleton is mathematically modeled as an acyclic directed kinematic tree of $N$ rigid bones (Parent, 2012). The spatial configuration of bone $i$ relative to the world coordinate frame is given by the recursive forward kinematics transform product:

$$\mathbf{T}_i^{world} = \prod_{j \in \text{ancestors}(i)} \mathbf{T}_j^{local}$$

Where each $\mathbf{T} \in SE(3)$ represents a $4 \times 4$ homogeneous transformation matrix containing orientation $\mathbf{R} \in SO(3)$ and translation $\mathbf{p} \in \mathbb{R}^3$:

$$\mathbf{T} = \begin{bmatrix} \mathbf{R} & \mathbf{p} \\ \mathbf{0}^T & 1 \end{bmatrix}$$

For limb end-effectors (hands and feet), Inverse Kinematics (IK) solves for the joint rotation vector $\mathbf{\theta} = [\theta_1, \theta_2, \dots, \theta_m]^T$ such that:

$$\mathbf{f}(\mathbf{\theta}) = \mathbf{p}_{target}$$

In Blender 5.2, character rigs employ a 2-bone analytical IK solver (`IK` constraint with `chain_count=2`), which uses an explicit **Pole Target** vector $\mathbf{v}_{pole}$ to resolve the rotational redundancy of the elbow/knee hinge plane around the shoulder-wrist or hip-ankle axis.

### 1.2 Twist Bones & The "Candy-Wrapper" Artifact
Linear Blend Skinning (LBS) exhibits the classic "candy-wrapper" volume collapse artifact when an axial joint (such as the forearm pronation/supination or femur rotation) rotates around its longitudinal axis:

$$\mathbf{v}' = \sum_{k=1}^K w_k \mathbf{T}_k \mathbf{v}$$

When $\mathbf{T}_{wrist}$ rotates $180^\circ$ relative to $\mathbf{T}_{elbow}$, the linear interpolation of rotations collapses the cross-sectional area to zero: $\det\left(\frac{1}{2}\mathbf{I} + \frac{1}{2}\mathbf{R}_{180^\circ}\right) = 0$.

**Production Mitigation:**
1. **Twist Bone Splitting:** Divide the limb segment into two bones: a primary bending bone (`Forearm_Bend.L`) and an axial twist bone (`Forearm_Twist.L`).
2. **Damped Track / Copy Rotation Constraint:** Constrain `Forearm_Twist.L` to absorb $50\%$ of the local Y-axis rotation from the hand bone (`factor=0.5`), preserving cylindrical mesh volume during extreme wrist rolls.

---

## 2. Biomechanics of Biped Locomotion (Gait Cycle Dynamics)

### 2.1 The Four Key Poses of an Animated Walk
The **Contact / Down / Passing / Up** naming below is animation practice (Williams, *The
Animator's Survival Kit*), not Winter's clinical phase nomenclature (initial contact, loading
response, mid-stance, terminal stance, pre-swing, swing). The stride percentages come from
clinical gait analysis (Winter, 2009); the four-pose framing is the animator's overlay on it.
Attributing the pose names themselves to Winter is a misattribution — corrected 2026-09-06.

```
       0%                    12%                   50%                   62%                  100%
     Contact                Down                 Passing                  Up                 Contact
  (Heel Strike)       (Weight Loading)       (Mid-Stance / Push)     (Toe-Off / Float)     (Heel Strike)
        │                      │                      │                      │                   │
  Left Foot Fwd         Both Feet Ground       Right Passes Left      Right Push-Off       Left Foot Fwd
  Pelvis: High-Roll     Pelvis: Min Z Drop     Pelvis: Max Z Rise     Pelvis: Mid Z        Pelvis: High-Roll
  Arms: Max Anti-Phase  Arms: Decelerating     Arms: Zero Velocity    Arms: Max Accel      Arms: Max Anti-Phase
```

### 2.2 Mathematical Kinematic Formulations for Procedural F-Curves
For a parametric walk cycle of duration $T$ frames and step frequency $\omega = \frac{2\pi}{T}$:

1. **Center of Mass (Pelvis / Root) Vertical Oscillation ($Z_{root}$):**
   In real gait the pelvis reaches minimum height during the loading response
   ($t \approx 0.12T, 0.62T$) and maximum height near mid-stance ($t \approx 0.35T, 0.85T$).
   The single harmonic at twice the stride frequency used by the boilerplate,
   $$Z_{root}(t) = Z_0 - A_z \cos(2\omega t), \qquad \omega = 2\pi/T$$
   puts its minima at $t = 0, 0.5T$ and its maxima at $t = 0.25T, 0.75T$ — i.e. it reproduces
   the *frequency* (2 rises per stride) but not the measured *phase offset*. Treat it as a
   first-order approximation and do not quote the 12%/35% figures as properties of this curve.
   Amplitude $A_z \approx 0.02\text{–}0.04 \times H_{body}$ ($2\text{–}4\text{ cm}$).

2. **Pelvic List / Lateral Drop ($R_{x, pelvic}$):**
   During single-limb support, the pelvis tilts downward toward the unsupported swing leg (Trendelenburg mechanism, Winter 2009):
   $$\theta_{tilt}(t) = A_{tilt} \sin(\omega t)$$

3. **Pelvic Transverse Rotation ($R_{z, pelvic}$):**
   The pelvis rotates forward on the side of the advancing leg to maximize effective stride length:
   $$\theta_{yaw}(t) = A_{yaw} \sin(\omega t)$$

4. **Thoracic / Shoulder Counter-Rotation:**
   To conserve angular momentum around the vertical axis, the thoracic spine and shoulders rotate in exact anti-phase ($180^\circ$ phase shift) to the pelvis:
   $$\theta_{shoulder}(t) = -k_{counter} \theta_{yaw}(t), \quad k_{counter} \in [0.7, 0.9]$$

5. **Arm Swing Kinematics:**
   Contralateral forward swing of the upper arm opposes the forward swing of the ipsilateral leg:
   $$\theta_{arm, L}(t) = -\theta_{arm, R}(t) = A_{arm} \sin(\omega t)$$

---

## 3. Production Skinning & Deformation Mechanics

### 3.1 Bounded Biharmonic & Smooth Distance Weighting
In automated skinning pipelines, vertex weights $w_{i,j}$ for vertex $\mathbf{v}_i$ and bone $j$ are computed to satisfy:
1. **Partition of Unity:** $\sum_{j=1}^M w_{i,j} = 1 \quad \forall i$.
2. **Non-negativity:** $w_{i,j} \ge 0$.
3. **Smoothness:** Minimization of the Laplacian energy $\Delta w_j = 0$ subject to bone boundary conditions (Jacobson et al., 2011).

In Blender 5.2 data-API scripting, robust headless skinning projects vertex $\mathbf{v}_i$ onto the finite bone segment $[\mathbf{p}_{head,j}, \mathbf{p}_{tail,j}]$:

$$\hat{t}_j = \text{clamp}\left(\frac{(\mathbf{v}_i - \mathbf{p}_{head,j}) \cdot (\mathbf{p}_{tail,j} - \mathbf{p}_{head,j})}{\|\mathbf{p}_{tail,j} - \mathbf{p}_{head,j}\|^2}, 0, 1\right)$$

$$d_{ij} = \|\mathbf{v}_i - (\mathbf{p}_{head,j} + \hat{t}_j(\mathbf{p}_{tail,j} - \mathbf{p}_{head,j}))\|$$

$$w_{i,j} \propto \exp\left(-\frac{d_{ij}^2}{2\sigma_j^2}\right)$$

**Implementation gap (2026-09-06 audit):** `bp_humanoid_rig_ikfk.bind_mesh_to_armature` does
**not** implement this Gaussian falloff. It performs nearest-bone *hard* assignment: the
projection and distance $d_{ij}$ above are computed, then the single closest bone receives
weight $1.0$ and every other bone $0.0$. Measured on the module's own test mesh: one group per
vertex, weight sums exactly $1.0$, no NaN. Partition of unity and non-negativity hold
trivially; **smoothness does not**. Smooth the weights before claiming deformation quality.

---

## 4. Physically-Based Skin Subsurface Scattering (SSS)

### 4.1 Normalized Random Walk Diffusion
Human skin consists of multiple anisotropic layers: the stratum corneum, epidermis (containing melanin chromophores), and dermis (rich in hemoglobin and collagen fibers). 

**Correction (2026-09-06 audit).** Blender 5.2's Principled BSDF offers four distinct methods,
enumerated at runtime as `BURLEY`, `RANDOM_WALK`, `RANDOM_WALK_SKIN`, `RANDOM_WALK_LEGACY`.
"Random Walk (Burley)" is not one thing:
- `BURLEY` is the Christensen & Burley (2015) normalized-diffusion approximation, whose
  reflectance profile is the closed form below.
- `RANDOM_WALK` / `RANDOM_WALK_SKIN` are brute-force volumetric path tracing inside the medium.
  `RANDOM_WALK_SKIN` (used by `bp_skin_sss_shader.py`) is the skin-tuned variant and exposes the
  `Subsurface IOR` socket, which is disabled — and therefore not addressable by name — under the
  default `BURLEY` method.

The Christensen–Burley profile (i.e. the `BURLEY` method) is:

$$R(r) = \frac{\alpha'}{8\pi A r} \left(e^{-r/d} + e^{-r/(3d)}\right)$$

Where:
- $\alpha'$ is the reduced albedo.
- $d$ is the diffuse mean free path (mean free scattering distance).
- $r$ is the radial distance from the incident ray entry point.

### 4.2 Spectral Subsurface Radii (Hemoglobin Absorption Profile)
Because human hemoglobin absorption drops sharply in the red wavelength spectrum ($\lambda \approx 650\text{ nm}$), red light penetrates significantly deeper into the vascularized dermis before re-emerging:

| Spectral Channel | Wavelength ($\lambda$) | Subsurface Radius $r_\lambda$ | Physical Mechanism |
|---|---|---|---|
| **Red (R)** | $\approx 650\text{ nm}$ | $1.000$ (Normalized Base) | Minimum hemoglobin absorption; deep dermal transmission |
| **Green (G)** | $\approx 550\text{ nm}$ | $0.200\text{–}0.250$ | High oxyhemoglobin absorption; shallow scattering |
| **Blue (B)** | $\approx 450\text{ nm}$ | $0.080\text{–}0.100$ | Maximum melanin/protein Rayleigh scattering; surface absorption |

In Blender 5.2 Python API:
```python
bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.22, 0.08)
bsdf.inputs["Subsurface Scale"].default_value = 0.025  # 25 mm real-world scale
```

---

## 5. Melanin-Based Biochemical Hair & Fur Shading

### 5.1 The Marschner-Chiang Hair Scattering Model
Hair and fur strands do not behave as smooth Lambertian surfaces or simple microfacet lobes. The Marschner model (Marschner et al., 2003) decomposes light scattering through an elliptical keratin cylinder into three primary specular lobes:
1. **$R$ (Primary Reflection):** Direct bounce off the outer cuticular scales (white specular highlight shifted $2^\circ\text{–}3^\circ$ toward the hair root).
2. **$TT$ (Transmission-Transmission):** Light entering the fiber, passing through the cortex, and exiting the opposite side (colored forward-scattering backlight).
3. **$TRT$ (Internal Reflection):** Light entering the fiber, reflecting off the inner back wall of the cuticle, and exiting toward the viewer (colored secondary glint).

### 5.2 Biochemical Melanin Absorption
Blender 5.2's **Principled Hair BSDF** utilizes Chiang et al. (2016)'s formulation parameterized by biochemical melanin concentrations:
- **Eumelanin ($C_e$):** Dark brown/black pigment chromophore.
- **Pheomelanin ($C_p$):** Red/yellow pigment chromophore.

The spectral absorption coefficient $\sigma_a(\lambda)$ is computed as:

$$\sigma_a(\lambda) = C_e \left(\frac{\lambda}{500\text{ nm}}\right)^{-3.45} + C_p \left(\frac{\lambda}{500\text{ nm}}\right)^{-4.80}$$

Exponents originate in d'Eon et al. (2011) and are carried into the Chiang et al. (2016) model;
the exact numeric values are UNVERIFIED (2026-09-06 audit) against the papers.

Phenotype table below: artist-facing guidance, UNVERIFIED (2026-09-06 audit).

| Hair Phenotype | Melanin Concentration ($C_e + C_p$) | Melanin Redness ($C_p / (C_e + C_p)$) |
|---|---|---|
| **Jet Black** | $0.90\text{–}1.00$ | $0.00\text{–}0.10$ |
| **Dark Brown** | $0.60\text{–}0.75$ | $0.15\text{–}0.25$ |
| **Auburn / Red** | $0.40\text{–}0.60$ | $0.70\text{–}0.90$ |
| **Golden Blonde** | $0.10\text{–}0.25$ | $0.40\text{–}0.60$ |
| **Albino / White** | $0.00\text{–}0.02$ | $0.00$ |

---

## 6. Implementation Architecture Matrix

| Component | Target File | Core Algorithm / Standard | Headless Postcondition Assert |
|---|---|---|---|
| **Humanoid IK/FK Rig** | `bp_humanoid_rig_ikfk.py` | Craig (2005) 2-bone analytical IK + twist bone (production practice, not Kavan 2007) | measured 33 bones; IK constraints carry target + pole target + `chain_count=2`; weight sums $1.0$, no NaN |
| **Biped Locomotion** | `bp_biped_locomotion.py` | 5-key harmonic approximation of a walk with antiphase counter-swing | `Action.fcurves` was **removed** in 5.2 — read `action.layers[0].strips[0].channelbag(slot).fcurves`; measured 12 curves, loop closure at frame $T$ within $10^{-4}$, arms anti-phase to $<10^{-6}$ |
| **Skin SSS Shader** | `bp_skin_sss_shader.py` | `RANDOM_WALK_SKIN` volumetric SSS (NOT Christensen-Burley, see §4.1) with dermal spectral radii | `assert mat.node_tree.nodes['Principled BSDF'].inputs['Subsurface Weight'].default_value > 0` |
| **Melanin Hair Shader** | `bp_fur_hair_shader.py` | Chiang et al. (2016) — module sets `model='CHIANG'` explicitly (5.2 alternative: `HUANG`) — melanin absorption on `Curves` geometry | `assert mat.node_tree.nodes['Principled Hair BSDF'] is not None` |
