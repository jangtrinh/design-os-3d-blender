# OpenPBR Surface & The Principled BSDF: Microfacet Physics & Layered Energy Conservation

Blender 4.0 through 5.2 overhauled the **Principled BSDF** (`ShaderNodeBsdfPrincipled`) to align with the industry-standard **OpenPBR Surface specification** (developed by the Academy Software Foundation - ASWF, Autodesk, and Adobe).

---

## 1. Microfacet Theory: The Cook-Torrance Specular Model

Physical surfaces are not mathematically flat; they consist of microscopic planar facets oriented with random micro-normals $\mathbf{m}$:

$$f_r(\mathbf{l}, \mathbf{v}) = \frac{D(\mathbf{m}) \cdot F(\mathbf{l}, \mathbf{m}) \cdot G(\mathbf{l}, \mathbf{v}, \mathbf{m})}{4 (\mathbf{n} \cdot \mathbf{l}) (\mathbf{n} \cdot \mathbf{v})}$$

```
                Incoming Light (l)           Outgoing Eye View (v)
                         \                     /
                          \        Half-Vector\
                           \           m       /
                            \          ▲      /
                             ▼         │     ▲
                          ────\────────|────/──── Microfacet
                       ~~~~~~~~~~~~~~~~~~~~~~~~~~~ Rough Surface Profile
```

### 1.1 Trowbridge-Reitz (GGX) Normal Distribution Function $D(\mathbf{m})$
Dictates the statistical concentration of microfacets aligned with the half-vector $\mathbf{m} = \frac{\mathbf{l} + \mathbf{v}}{\|\mathbf{l} + \mathbf{v}\|}$:
$$D_{GGX}(\mathbf{m}) = \frac{\alpha^2}{\pi \left( (\mathbf{n} \cdot \mathbf{m})^2 (\alpha^2 - 1) + 1 \right)^2}$$
Where $\alpha = \text{Roughness}^2$ (perceptually linear roughness mapping).
*   *Property of GGX:* Features a heavy power-law tail, reproducing the soft, realistic glare halos seen around real-world specular highlights (unlike Gaussian or Beckmann distributions which cut off sharply).

### 1.2 The Smith Masking-Shadowing Function $G_2(\mathbf{l}, \mathbf{v})$
Accounts for microfacets shadowing incoming light ($G_1(\mathbf{l})$) or occluding outgoing reflections from the camera ($G_1(\mathbf{v})$):
$$G_2(\mathbf{l}, \mathbf{v}) = G_1(\mathbf{l}) \cdot G_1(\mathbf{v}) = \frac{2 (\mathbf{n} \cdot \mathbf{l})}{(\mathbf{n} \cdot \mathbf{l}) + \sqrt{\alpha^2 + (1 - \alpha^2)(\mathbf{n} \cdot \mathbf{l})^2}} \cdot \frac{2 (\mathbf{n} \cdot \mathbf{v})}{(\mathbf{n} \cdot \mathbf{v}) + \sqrt{\alpha^2 + (1 - \alpha^2)(\mathbf{n} \cdot \mathbf{v})^2}}$$

---

## 2. Fresnel Reflection & The $F_0$ Physical Baseline

Light hitting a surface reflects more strongly at grazing angles ($\theta \to 90^\circ$) than at normal incidence ($\theta = 0^\circ$).

```
        Normal Incidence (θ = 0°)                     Grazing Angle (θ = 90°)
             F0 = 4% Reflectance                             F90 = 100% Reflectance
                  │                                            \
                  ▼                                             \ 
             ┌─────────┐                                         ▼─────────►
             │ Plastic │                                         │ Plastic │
             └─────────┘                                         └─────────┘
             96% enters material (Diffuse/SSS)                   Total Specular Reflection!
```

### 2.1 Schlick's Approximation
$$F(\theta) = F_0 + (1 - F_0)(1 - \cos\theta)^5$$
Where $F_0$ is reflectance at perpendicular normal incidence:
$$F_0 = \left( \frac{\eta - 1}{\eta + 1} \right)^2$$
Where $\eta$ is Index of Refraction (IOR):
*   **Water ($\eta = 1.33$):** $F_0 = \left(\frac{0.33}{2.33}\right)^2 \approx \mathbf{0.020\ (2.0\%)}$.
*   **Plastics / Acrylic / Glass ($\eta = 1.50$):** $F_0 = \left(\frac{0.50}{2.50}\right)^2 = \mathbf{0.040\ (4.0\%)}$.
*   **Diamond ($\eta = 2.42$):** $F_0 = \mathbf{0.172\ (17.2\%)}$.

### 2.2 Dielectrics vs. Metals (The Metallic Switch)
*   **Dielectrics (Insulators, `Metallic = 0.0`):**
    $F_0$ is achromatic (pure grey, $\sim 4\%$). Specular reflections have **zero tint** (a red plastic ball reflects white specular highlights). Unreflected light penetrates into the body to produce diffuse or subsurface scattering.
*   **Metals (Conductors, `Metallic = 1.0`):**
    Free conduction electrons extinguish internal transmission immediately (zero diffuse bounce). $F_0$ is colored and extremely high:
    *   **Gold:** $F_0 = (1.00, 0.78, 0.34)$ ($78\text{–}100\%$ colored reflectance).
    *   **Copper:** $F_0 = (0.95, 0.64, 0.54)$.
    *   **Silver:** $F_0 = (0.97, 0.96, 0.94)$.

---

## 3. Layered Energy Conservation Architecture

The OpenPBR model enforces strict thermodynamic energy conservation across stacked surface slabs:

```
    [ Clearcoat Layer ]       ◄── Adds secondary glossy sheen (IOR 1.5);
             │                    Reflects fraction R_coat; Transmits (1 - R_coat).
             ▼
    [ Specular Primary ]      ◄── Reflects fraction R_spec;
             │                    Transmits (1 - R_coat) · (1 - R_spec).
             ▼
    [ Base Substrate ]        ◄── Divides remaining energy between Diffuse, SSS,
                                  and Transmission (Refraction). Total Energy ≤ 1.0!
```

---

## 4. Programmatic Socket Resolution in Blender 5.2

> [!IMPORTANT]
> **Socket Rename Discipline:** Blender 4.0 renamed 8 Principled sockets (`Subsurface` $\to$ `Subsurface Weight`, `Transmission` $\to$ `Transmission Weight`), and Blender 5.0 renamed `Fac` $\to$ `Factor`. Never hardcode raw string keys; resolve via runtime inspection:

```python
import bpy

def get_principled_socket(node, *candidate_names):
    """Safely retrieves a shader socket across Blender 4.x/5.x naming migrations."""
    for name in candidate_names:
        if name in node.inputs:
            return node.inputs[name]
    raise KeyError(f"None of {candidate_names} found in node inputs: {[s.name for s in node.inputs]}")

def build_gold_pbr_material(name="Gold_PBR"):
    """Creates a physically accurate PBR Gold material in Blender 5.2."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    tree = mat.node_tree
    bsdf = tree.nodes.get("Principled BSDF")
    
    # 1. Base Color = Gold spectral reflectance (Linear RGB)
    base_color_sock = get_principled_socket(bsdf, "Base Color")
    base_color_sock.default_value = (1.0, 0.766, 0.336, 1.0)
    
    # 2. Metallic = 1.0 (Pure conductor)
    metallic_sock = get_principled_socket(bsdf, "Metallic")
    metallic_sock.default_value = 1.0
    
    # 3. Roughness = 0.15 (Polished jewelry gold)
    roughness_sock = get_principled_socket(bsdf, "Roughness")
    roughness_sock.default_value = 0.15
    
    return mat
```

---

## 5. References & Standards

1.  **Academy Software Foundation (ASWF). (2023).** *OpenPBR Surface Specification Version 1.0.* https://github.com/AcademySoftwareFoundation/OpenPBR (The unified industry standard for PBR surface shading).
2.  **Burley, B. (2012).** *Physically-Based Shading at Disney.* ACM SIGGRAPH 2012 Courses: Practical Physically Based Shading in Film and Game Production. (The original Disney Principled BRDF).
3.  **Walter, B., Marschner, S. R., Li, H., & Torrance, K. E. (2007).** *Microfacet models for refraction through rough surfaces.* Proceedings of the 18th Eurographics Conference on Rendering Techniques (EGSR '07), 195–206. (Derivation of the GGX microfacet distribution).
4.  **Cook, R. L., & Torrance, K. E. (1982).** *A Reflectance Model for Computer Graphics.* ACM Transactions on Graphics, 1(1), 7–24. [DOI: 10.1145/357290.357293]
