# Thin-Film Wave Interference & Iridescence: Optics & Shader Implementation

Standard computer graphics assumes geometric ray optics where light behaves as straight particles. **Iridescence** (soap bubbles, oil slicks, tempered heat-colored steel, titanium anodizing, peacock feathers) requires **Wave Optics**, where electromagnetic light waves interfere constructively and destructively based on nanometer-scale film thicknesses.

---

## 1. Wave Optics: The Airy Multi-Beam Interference Formula

When light strikes a thin transparent dielectric film of thickness $d$ and refractive index $n_2$ deposited on a substrate of index $n_3$:

```
                  Air (n1 = 1.0)
                         \               Ray 1 (Reflected from top surface)
                          \             /
                           \           /
        ════════════════════\═════════/════════════════════════ Top Boundary
                             \       /  Ray 2 (Reflected from bottom, delayed!)
           Thin Film (n2, d)  \     /
                               \   /    Optical Path Difference: Δ = 2·n2·d·cos(θ2)
        ════════════════════════\═/════════════════════════════ Bottom Boundary
                  Substrate (n3)
```

### 1.1 The Optical Path Difference (OPD - $\Delta$)
The geometrical path difference between Ray 1 and Ray 2 is:
$$\Delta = 2 \cdot n_2 \cdot d \cdot \cos\theta_2$$
Where $\theta_2$ is the refracted angle inside the film ($\sin\theta_2 = \frac{n_1}{n_2}\sin\theta_1$).

### 1.2 Phase Shifts & Interference Conditions
*   **Fresnel Reflection Phase Shift ($\phi$):** Light reflecting off an optically denser medium ($n_1 < n_2$) experiences a **$\pi$ phase inversion** ($180^\circ$ flip).
*   **Constructive Interference (Colors Reinforced):**
    $$2 n_2 d \cos\theta_2 = \left( m - \frac{1}{2} \right) \lambda \quad (m = 1, 2, 3, \dots)$$
*   **Destructive Interference (Colors Extinguished):**
    $$2 n_2 d \cos\theta_2 = m \cdot \lambda$$
*   *Why Colors Shift with View Angle:* As view angle $\theta_1$ tilts toward grazing, $\cos\theta_2$ decreases $\implies$ The reinforced wavelength $\lambda$ shifts toward shorter wavelengths (e.g. Red shifts to Green, Green shifts to Blue/Violet).

---

## 2. Nanometer Thickness Spectrum: The Newton Scale

The color of a thin film depends directly on its physical thickness $d$:

```
  Film Thickness d (nm)
         ▲
  800 nm ┼────────── Third-Order Green / Pink
         │
  550 nm ┼────────── Second-Order Vibrant Magenta / Purple (Oil Slick)
         │
  400 nm ┼────────── First-Order Straw Yellow (Tempered Exhaust Steel)
         │
  200 nm ┼────────── First-Order Deep Blue (Heat-treated Titanium)
         │
   50 nm ┼────────── Destructive extinction of all visible light (Black film)
         └──────────────────────────►
```

| Film Thickness ($d$) | Film Material / Context | Dominant Reinforced Color | Visual Physical Manifestation |
| :--- | :--- | :---: | :--- |
| **$200\text{ nm}$** | Titanium Oxide ($TiO_2$) on Titanium | Deep Electric Blue | Anodized custom fasteners, racing manifolds. |
| **$380\text{ nm}$** | Iron Oxide ($Fe_3O_4$) on Carbon Steel | Straw Yellow / Bronze | Steel heated to $230^\circ\text{C}$ (tempering colors). |
| **$520\text{ nm}$** | Organic hydrocarbon slick on water | Vibrant Violet / Magenta | Gasoline puddle on wet asphalt. |
| **$650\text{ nm}$** | Water/Soap film ($n = 1.33$) | Emerald Green / Cyan | Fresh blowing soap bubbles. |

---

## 3. Thin-Film Implementation in Blender 5.2

Blender's Principled BSDF or custom OSL node graphs simulate thin-film iridescence without complex spectral rendering engines by evaluating the Belcour-Barla polynomial model:

```python
import bpy

def setup_heat_tempered_exhaust_titanium(mat_name="Tempered_Titanium"):
    """
    Creates a heat-tempered iridescent titanium exhaust material.
    """
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    
    # 1. Output & Principled BSDF
    out_node = tree.nodes.new(type='ShaderNodeOutputMaterial')
    bsdf = tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    
    # Base metal: Titanium (Metallic = 1.0, Base Color = 0.54, 0.49, 0.44)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Base Color'].default_value = (0.54, 0.49, 0.44, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.25
    
    # In Blender 4.x/5.x, Coat layer can simulate the oxide film
    # Coat Roughness = 0.1, Coat IOR = 2.4 (Titanium dioxide rutile index)
    bsdf.inputs['Coat Weight'].default_value = 1.0
    bsdf.inputs['Coat Roughness'].default_value = 0.08
    bsdf.inputs['Coat IOR'].default_value = 2.40
    
    # 2. Procedural Color Ramp driving Coat Tint along exhaust temperature gradient
    coord = tree.nodes.new(type='ShaderNodeTexCoord')
    grad = tree.nodes.new(type='ShaderNodeTexGradient')
    ramp = tree.nodes.new(type='ShaderNodeValToRGB')
    
    # Gradient spectrum: Raw Titanium -> Straw Bronze -> Purple -> Electric Blue
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1.0, 1.0, 1.0, 1.0)
    
    el_bronze = ramp.color_ramp.elements.new(0.35)
    el_bronze.color = (0.85, 0.65, 0.25, 1.0) # Bronze straw
    
    el_purple = ramp.color_ramp.elements.new(0.60)
    el_purple.color = (0.65, 0.15, 0.75, 1.0) # Violet
    
    el_blue = ramp.color_ramp.elements[len(ramp.color_ramp.elements)-1]
    el_blue.position = 0.85
    el_blue.color = (0.10, 0.35, 0.95, 1.0) # Electric blue
    
    # Connect gradient to Coat Tint
    tree.links.new(coord.outputs['Generated'], grad.inputs['Vector'])
    tree.links.new(grad.outputs['Fac'], ramp.inputs['Fac'])
    tree.links.new(ramp.outputs['Color'], bsdf.inputs['Coat Tint'])
    tree.links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    
    return mat
```

---

## 4. References & Standards

1.  **Born, M., & Wolf, E. (1999).** *Principles of Optics: Electromagnetic Theory of Propagation, Interference and Diffraction of Light* (7th ed.). Cambridge University Press. (The seminal mathematical treatise on wave optics and thin film reflection).
2.  **Belcour, L., & Barla, P. (2017).** *A practical extension to microfacet theory for the modeling of varying iridescence.* ACM Transactions on Graphics (SIGGRAPH 2017), 36(4), Article 65. [DOI: 10.1145/3072959.3073620] (The standard GPU model for thin-film interference in modern PBR shaders).
3.  **Smits, B. (1999).** *An RGB-to-spectrum conversion for reflectances.* Journal of Graphics Tools, 4(4), 11–22. (Accurate mapping of thin-film phase shifts to linear RGB render spaces).
