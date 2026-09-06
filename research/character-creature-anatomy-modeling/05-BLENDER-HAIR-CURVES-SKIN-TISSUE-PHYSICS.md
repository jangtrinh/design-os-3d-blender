# Modern Hair Curves Architecture, Cosserat Rod Dynamics & Soft-Tissue Biomechanics

> **Document ID:** `RES-CHAR-ANAT-05`  
> **Status:** Production Character Architecture Specification  
> **Target Platform:** Blender 5.2.0 LTS (Data-API, Curves, Headless-Safe)  
> **Primary Standards & Citations:** Spitieris & Bergou (2012 - *Discrete Cosserat Rods for Hair and Strand Mechanics*), Selle et al. (2008 - *Mass-Spring Hair Simulation with Realistic Clumping*), Lewis et al. (2000 - *Pose Space Deformation*), Terzopoulos et al. (1987 - *Elastically Deformable Models*), Blender Foundation (2024 - *Blender Curves Data-Block & Procedural Hair Grooming System*).
> **Audit note (2026-09-06 onboarding audit):** every `bpy` name in this file was introspected in a `--factory-startup` Blender 5.2.0 LTS. Anatomical figures and bibliographic entries are not runtime-checkable; the ones the audit could not confirm carry an inline `UNVERIFIED (2026-09-06 audit)` marker.


---

## 1. Modern Blender 5.2 Hair Curves Architecture (`CURVES` Data-Block)

### 1.1 Legacy Particle Hair vs Modern Hair Curves
In Blender 4.x/5.x, modern character grooming uses the pure geometry **`Curves`** data-block,
created with **`bpy.data.hair_curves.new(name)`**.

*Correction (2026-09-06 audit, Blender 5.2.0 LTS):* the constructor is `bpy.data.hair_curves.new`
— there is no `bpy.data.curves_new()`. And the legacy particle path is **not removed** in 5.2:
`bpy.ops.particle.new` exists, a `PARTICLE_SYSTEM` modifier is creatable, and
`ParticleSettings.type` still offers `HAIR`. Blender's own docs call particle hair legacy;
whether it is *formally deprecated* is UNVERIFIED (2026-09-06 audit). The reason to prefer
Curves for this project is concrete and checkable: Curves is data-API-authorable headless,
particle hair is operator- and mode-gated.

| Architectural Property | Legacy Particle Hair (`PARTICLE`) | Modern Hair Curves (`CURVES`) |
|---|---|---|
| **Data Representation** | Hidden internal particle cache | Native first-class geometry data-block |
| **Surface Attachment** | Random barycentric triangle scatter | Deterministic `surface_uv_coordinate` attribute |
| **Modifier Pipeline** | Limited fixed particle edit mode | Full Geometry Nodes stack evaluation |
| **Memory & Performance** | Heavy CPU overhead per strand | GPU-accelerated Metal/OptiX BVH curve primitives |
| **Headless Python API** | Fragile operator dependency (`bpy.ops.particle`) | Pure data-API creation and attribute setting |

Rows other than the Headless Python API row are architectural descriptions, not measured
benchmarks — UNVERIFIED (2026-09-06 audit).

### 1.2 Programmatic Hair Curves Generation in Python
```python
import bpy

# 1. Create the hair-curves data-block and its object.
#    bpy.data.curves.new(name, 'CURVES') raises TypeError: that enum is CURVE/SURFACE/FONT.
curves_data = bpy.data.hair_curves.new("Character_Hair")
hair_obj = bpy.data.objects.new("Character_Hair", curves_data)
bpy.context.scene.collection.objects.link(hair_obj)

# 2. Attach to the emitter scalp mesh. `surface` is on the DATA-block;
#    bpy.types.Object has no `surface` attribute.
scalp_mesh = bpy.data.objects["Head_Mesh"]
hair_obj.parent = scalp_mesh
curves_data.surface = scalp_mesh
curves_data.surface_uv_map = scalp_mesh.data.uv_layers.active.name

# 3. Allocate real strands, then write point positions and radii.
#    Without add_curves() the data-block is empty and renders nothing.
curves_data.add_curves([8] * 40)                    # 40 strands x 8 points
for c in curves_data.curves:
    for i in range(c.points_length):
        pt = curves_data.points[c.first_point_index + i]
        pt.position = pt.position                   # replace with groom math
        pt.radius = 4e-5 * (1.0 - i / 7.0) + 5e-6

# 4. Per-strand surface binding attribute (FLOAT2 on the CURVE domain).
curves_data.attributes.new("surface_uv_coordinate", 'FLOAT2', 'CURVE')
```
All names above were exercised at runtime on 2026-09-06 (Blender 5.2.0 LTS); the working
module is `scripts/boilerplates/character_creature/bp_hair_curves_gen.py`.

---

## 2. Procedural Hair Styling Pipeline in Geometry Nodes

Production hair styling operates through a non-destructive Geometry Nodes modifier stack:

```
Scalp Emitter Mesh
       │
       ▼
 [1. Generate Guide Curves] ──► Low-density artist-placed or sparse guide curves
       │
       ▼
 [2. Interpolate Hair Curves] ──► Density multiplier (e.g. 50,000 dense child curves)
       │
       ▼
 [3. Clump Hair Curves] ──► Attracts child strands to guide centroid via power curve y = x^p
       │
       ▼
 [4. Frizz / Curl Modifiers] ──► 3D Perlin noise helical perturbation
       │
       ▼
 [5. Set Curve Radius] ──► Root-to-tip taper (e.g. r_root = 40 µm, r_tip = 5 µm)
```

### 2.1 Clumping Mathematical Formulation
A hair clump attracts child strands towards a central guide curve based on normalized distance along the curve $t \in [0, 1]$ (where $t=0$ is root, $t=1$ is tip):
$$\mathbf{P}_{clumped}(t) = (1 - \alpha(t)) \cdot \mathbf{P}_{child}(t) + \alpha(t) \cdot \mathbf{P}_{guide}(t)$$
$$\alpha(t) = \text{clamp}\left(t^p \cdot C_{intensity}, 0.0, 1.0\right)$$
- When exponent $p > 1.0$, strands remain separated at the root and tightly coalesce at the tip.
- When $p < 1.0$, strands bunch together immediately near the scalp.

---

## 3. Hair Strand Physical Mechanics: The Discrete Cosserat Rod

Real hair strands possess non-negligible bending stiffness and torsional resistance. They are modeled as one-dimensional elastic **Cosserat rods** (Spitieris & Bergou 2012):

### 3.1 Kinematic Centerline & Orthonormal Material Frame
A hair strand of length $L$ is parameterized by arc-length $s \in [0, L]$:
- Centerline trajectory: $\mathbf{r}(s) \in \mathbb{R}^3$.
- Orthonormal material frame: $\{\mathbf{d}_1(s), \mathbf{d}_2(s), \mathbf{d}_3(s)\}$, where $\mathbf{d}_3 = \frac{\partial \mathbf{r}}{\partial s}$ is the unit tangent vector.

### 3.2 Elastic Energy & Equations of Motion
The total strain energy $\mathcal{E}$ integrates stretch, shear, bending, and torsion:
$$\mathcal{E} = \frac{1}{2} \int_0^L \left( \alpha \left\|\frac{\partial \mathbf{r}}{\partial s}\right\|^2 + E I (\kappa_1^2 + \kappa_2^2) + G J \tau^2 \right) ds$$
*Physical Parameters for Human Hair* (textbook ranges, UNVERIFIED (2026-09-06 audit))*:*
- Young's Modulus: $E \approx 3.0\text{–}4.5\text{ GPa}$.
- Shear Modulus: $G \approx 1.2\text{ GPa}$.
- Radius: $R \approx 25\text{–}40\,\mu\text{m}$.
- Area Moment of Inertia: $I = \frac{\pi R^4}{4}$.
- Polar Moment of Inertia: $J = \frac{\pi R^4}{2} = 2 I$.

---

## 4. Soft-Tissue Biomechanics & Secondary Muscle Bulging

### 4.1 Pose Space Deformation (PSD / Lewis et al. 2000)
Standard Linear Blend Skinning (LBS) assumes rigid bone transformation, causing muscles to collapse during joint flexion:
$$\mathbf{v}_{LBS} = \sum_{j} w_j \mathbf{M}_j \mathbf{v}_0$$

Under PSD, an anatomical muscle bulge displacement $\Delta \mathbf{v}(\mathbf{\theta})$ is added as a function of the joint angle vector $\mathbf{\theta}$:
$$\mathbf{v}_{PSD}(\mathbf{\theta}) = \sum_{j} w_j \mathbf{M}_j \left( \mathbf{v}_0 + \Delta \mathbf{v}(\mathbf{\theta}) \right)$$
$$\Delta \mathbf{v}(\mathbf{\theta}) = \sum_{k=1}^{M} \phi\left(\|\mathbf{\theta} - \mathbf{\theta}_k\|\right) \mathbf{c}_k$$
Where $\phi(r)$ is a Radial Basis Function (RBF, e.g., Gaussian $\phi(r) = e^{-\epsilon r^2}$) and $\mathbf{c}_k$ are weights determined from scanned or sculpted muscular flexion poses.

### 4.2 Secondary Flesh Jiggle (Damped Harmonic Oscillator)
Soft adipose and muscular tissue (breasts, gluteal mass, abdominal belly, creature jowls) exhibit secondary dynamic recoil governed by the damped mass-spring equation:
$$m \ddot{\mathbf{x}} + c \dot{\mathbf{x}} + k (\mathbf{x} - \mathbf{x}_{anchor}) = -m \mathbf{a}_{chassis}$$
- **Natural Frequency:** $\omega_n = \sqrt{k/m} \approx 4\text{–}8\text{ Hz}$ for biological adipose tissue.
- **Damping Ratio:** $\zeta = \frac{c}{2\sqrt{km}} \approx 0.3\text{–}0.5$ (underdamped, creating visible elastic settling oscillations).

---

## 5. Mathematical & Physical Citations

1. **Spitieris, M., & Bergou, M. (2012)** — *Discrete Cosserat Rods for Hair and Strand Mechanics*, Computer Graphics Forum (Eurographics 2012), 31(2), pp. 437-446. UNVERIFIED (2026-09-06 audit): this author/title/venue triple could not be confirmed offline. The established discrete-rod references for hair are Bergou et al., *Discrete Elastic Rods* (SIGGRAPH 2008) and *Discrete Viscous Threads* (SIGGRAPH 2010) — prefer those until this entry is checked.
2. **Selle, A., Lentine, M., & Fedkiw, R. (2008)** — *A mass spring model for hair simulation*, ACM Transactions on Graphics (SIGGRAPH 2008), 27(3), Article 64. (The header line's "with Realistic Clumping" subtitle is descriptive, not part of the published title.)
3. **Lewis, J. P., Cordner, M., & Fong, N. (2000)** — *Pose space deformation: a unified approach to shape interpolation and skeleton-driven deformation*, Proceedings of SIGGRAPH 2000, pp. 165-172.
4. **Terzopoulos, D., Platt, J., Barr, A., & Fleischer, K. (1987)** — *Elastically deformable models*, Proceedings of SIGGRAPH '87, pp. 205-214.
5. **Bertails, F., Audoly, B., Cani, M. P., Querleux, B., Leroy, F., & Leveque, J. L. (2006)** — *Super-Helices for Predicting the Dynamics of Natural Hairs*, ACM Transactions on Graphics (SIGGRAPH 2006), 25(3), pp. 1180-1187.
6. **Blender Foundation** — *Curves* / *Hair Curves*, Blender Manual (5.x). Exact manual title and year UNVERIFIED (2026-09-06 audit); the API behaviour cited in §1 was verified directly against the 5.2.0 LTS runtime instead.
