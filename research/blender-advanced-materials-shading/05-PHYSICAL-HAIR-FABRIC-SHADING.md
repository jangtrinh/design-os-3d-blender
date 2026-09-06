# Physical Hair & Fabric Shading: The Chiang-Marschner Model & Microfiber Sheen

Cylindrical fibers (human hair, animal fur, synthetic carbon strands) and woven textiles (velvet, denim, silk, satin) violate standard microfacet planar BRDFs. Light interacts through internal cylindrical reflections, cuticle scales, and microscopic perpendicular fuzz.

---

## 1. The Chiang-Marschner Hair Scattering Model

In 2003, Marschner et al. proved that hair fibers scatter light primarily through three distinct optical paths:

```
                          Cross-Section of a Hair Fiber
                          
                        Incident Light (ω_i)
                                │
                 R-Lobe (Primary Specular)
                 (Reflected off outer cuticle scales)
                 ▲
                 │     ╭─────────────────╮
                 └─────┤  Outer Cuticle  ├─────► TRT-Lobe (Colored Secondary Glint)
                       │  Cortex Melanin │       (Two internal bounces before exit)
                       │   Absorption    │
                       ╰────────┬────────╯
                                │
                                ▼
                       TT-Lobe (Transmitted Forward Light)
                       (Bright rim back-lighting through hair)
```

### 1.1 The Three Classical Hair Lobes ($R, TT, TRT$)
1.  **$R$ (Direct Reflection):** Bounces directly off the outer keratin cuticle scales without entering the fiber. It is **uncolored (pure white specular highlight)**, shifted slightly toward the hair root by the cuticle tilt angle $\alpha \approx 2^\circ\text{–}3^\circ$.
2.  **$TT$ (Transmission-Transmission):** Light refracts into the fiber, passes straight through the melanin-pigmented cortex, and refracts out the back. Creates brilliant, warm **sun-soaked backlighting**.
3.  **$TRT$ (Transmission-Reflection-Transmission):** Enters the fiber, reflects off the internal back wall, and exits toward the viewer. Because it travels through the pigmented cortex twice, it is **deeply colored and produces secondary specular caustic glints**.

---

## 2. Biological Hair Color: Eumelanin vs. Pheomelanin

Instead of picking an arbitrary RGB color, realistic mammalian hair is governed by two biological melanin pigments:

```
        Log Pigment Concentration
                 ▲
        Black    ┼────────── 100% Eumelanin
                 │
        Brown    ┼────────── 50% Eumelanin
                 │
        Blonde   ┼────────── 5% Eumelanin
                 │
        Red      ┼────────── 20% Eumelanin + 80% Pheomelanin
                 │
        Grey/Alb ┼────────── 0% Melanin (Pure white keratin scattering)
                 └──────────────────────────►
```

*   **Eumelanin:** Broad spectrum absorption; produces black, dark brown, and ash shades.
*   **Pheomelanin:** Transmits warm red/yellow wavelengths; produces ginger, strawberry blonde, and auburn tones.
*   *Blender 5.2 Principled Hair BSDF:* Exposes direct physical sliders: `Melanin` ($0.0 = \text{white/grey}, 1.0 = \text{jet black}$) and `Melanin Redness` ($0.0 = \text{cool ash}, 1.0 = \text{vibrant red}$).

---

## 3. Microfiber Velvet & Fabric Sheen Shading

Woven fabrics (especially velvet, fleece, and peach-skin microfiber) exhibit a characteristic **intense grazing-angle backscatter sheen**:

```
         Standard Diffuse (Lambertian)                   Velvet Microfiber Sheen
                 ▲                                                 ▲
               /   \                                            /     \
             /       \                                        /         \  Intense Sheen
       ─────•─────────•─────                            ─────•───────────•───── on grazing edges!
```

### 3.1 The Charlie Microfiber Sheen Model (Estevez & Kulla, 2017)
Standard GGX microfacets model pits and valleys on a flat plane. Velvet consists of cylindrical fiber pile standing **perpendicular to the surface**.
*   **The Inverted V-Cavity Distribution:** Grazing view rays intersect millions of microscopic fiber tips, scattering light backward toward the camera.
*   *Blender 5.2 OpenPBR Sheen Layer:*
    *   `Sheen Weight`: Controls the visibility of the grazing fuzz layer.
    *   `Sheen Roughness`: Controls the softness of the edge halo ($0.3\text{–}0.6$).
    *   `Sheen Tint`: Colors the grazing edge (crucial for iridescent fabrics, e.g. blue velvet with purple sheen).

---

## 4. Anisotropic Weaving: Silk & Satin Tangents

Woven fabrics consist of orthogonal warp and weft threads:
*   **Anisotropic Tangent Vector Field:** The specular highlight stretches along the thread direction.
*   *Implementation:* Drive the Principled BSDF `Anisotropic` input ($0.7\text{–}0.9$) using an `Anisotropic Tangent` node aligned with the UV coordinate grid ($U$ along warp, $V$ along weft).

---

## 5. Production Hair & Velvet Setup in Blender 5.2

```python
import bpy

def build_physical_hair_material(name="Brunette_Hair"):
    """Builds a physically accurate Principled Hair BSDF material in Blender 5.2."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    
    out_node = tree.nodes.new(type='ShaderNodeOutputMaterial')
    hair_node = tree.nodes.new(type='ShaderNodeBsdfHairPrincipled')
    
    # 1. Melanin-based biological coloring
    hair_node.parametrization = 'MELANIN'
    hair_node.inputs['Melanin'].default_value = 0.65       # Medium dark brown
    hair_node.inputs['Melanin Redness'].default_value = 0.25 # Warm chestnut undertone
    hair_node.inputs['Random Melanin'].default_value = 0.15 # Natural hair-to-hair variation
    
    # 2. Roughness parameters (Longitudinal & Azimuthal)
    hair_node.inputs['Roughness'].default_value = 0.35
    hair_node.inputs['Radial Roughness'].default_value = 0.45
    
    # 3. Cuticle tilt angle (2.5 degrees toward root)
    hair_node.inputs['Coat'].default_value = 0.05
    hair_node.inputs['Offset'].default_value = 0.0436 # ~2.5 deg in radians
    
    tree.links.new(hair_node.outputs['BSDF'], out_node.inputs['Surface'])
    return mat
```

---

## 6. References & Standards

1.  **Marschner, S. R., Jensen, H. W., Cammarano, M., Worley, S., & Hanrahan, P. (2003).** *Light scattering from human hair fibers.* ACM Transactions on Graphics (SIGGRAPH '03), 22(3), 780–791. [DOI: 10.1145/882262.882345] (The seminal paper establishing the R, TT, and TRT hair scattering lobes).
2.  **Chiang, M. J., et al. (2016).** *A practical and controllable hair scattering model for production path tracing.* ACM Transactions on Graphics (SIGGRAPH 2016), 35(4), Article 87. (The Disney Chiang-Marschner model implemented in Blender's Principled Hair).
3.  **Estevez, A. C., & Kulla, C. (2017).** *Production Friendly Microfacet Sheen BRDF.* Sony Pictures Imageworks Technical Report. (The Charlie sheen model used in OpenPBR and Blender 5.2).
4.  **d'Eon, E., Francois, G., Hill, M., Letteri, J., & Saint Girons, J. M. (2011).** *An energy-conserving hair reflectance model.* Computer Graphics Forum, 30(4), 1181–1187.
