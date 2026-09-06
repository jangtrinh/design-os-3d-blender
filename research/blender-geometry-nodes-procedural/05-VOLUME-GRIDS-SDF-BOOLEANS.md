# Volume Grids, Signed Distance Fields (SDF) & Manifold Remeshing

Traditional polygonal mesh booleans (intersecting coplanar faces, zero-thickness walls) frequently fail or produce non-manifold topological defects. **Volume Grids & Signed Distance Fields (SDF)** in Blender 4.3+ and 5.2 convert polygonal surfaces into volumetric distance fields, perform smooth boolean unions, and re-mesh into guaranteed watertight manifold solids.

---

## 1. Signed Distance Fields (SDF) vs. Fog Volumes

A 3D spatial field $\Phi(\mathbf{x})$ represents geometry as an implicit function:

$$\Phi(\mathbf{x}) = \begin{cases} -d(\mathbf{x}, \partial \Omega) & \text{inside the solid body } \Omega \\ 0 & \text{on the boundary surface } \partial \Omega \\ +d(\mathbf{x}, \partial \Omega) & \text{outside in empty space} \end{cases}$$

```
                Signed Distance Field (SDF) Level Set
                
        Outside Space: Φ(x) > 0 (+3.0, +2.0, +1.0)
        ───────────────────────────────────────────────── ◄── Surface Boundary: Φ(x) = 0
        Inside Material: Φ(x) < 0 (-1.0, -2.0, -3.0)
```

### 1.1 Fog Volume vs. SDF Grid

| Property | Fog Density Volume (`density` grid) | Signed Distance Field (`distance` SDF grid) |
| :--- | :--- | :--- |
| **Voxel Stored Value** | Scalar particle density $[0.0, 1.0]$. | Euclidean distance to nearest surface $[-D_{max}, +D_{max}]$. |
| **Boundary Definition** | Fuzzy, semi-transparent cloud interface. | Razor-sharp zero-isosurface level set ($\Phi(\mathbf{x}) = 0$). |
| **Primary Use Cases** | Smoke, fire, clouds, atmospheric haze. | **Boolean modeling, organic remeshing, 3D printing.** |
| **Underlying Data Structure** | OpenVDB B+Tree sparse volumetric octree. | OpenVDB Narrow-Band Level Set ($3\text{–}5\text{ voxels}$ bandwidth). |

---

## 2. Inigo Quilez Smooth SDF Booleans

Standard polygon booleans create razor-sharp, unfilleted intersection corners ($90^\circ$ sharp edges). In nature and structural engineering, joints are smoothly radiused to distribute stress.

```
       Standard Sharp Boolean Union                      Smooth SDF Blended Union (Fillet Radius k)
       ┌───────────┐                                     ┌───────────┐
       │           │                                     │     ╭─────╯
       │     ┌─────┴─────┐                               │    (  Smooth Fillet!
       │     │           │                               │     ╰─────┐
       └─────┴───────────┘                               └───────────┘
```

### 2.1 Smooth Minimum Formulation
To merge two distance fields $\Phi_1(\mathbf{x})$ and $\Phi_2(\mathbf{x})$ with fillet blending radius $k$:
*   **Quadratic Smooth Minimum ($smin$):**
    $$h = \max\left( k - |\Phi_1 - \Phi_2|, \ 0.0 \right) / k$$
    $$\Phi_{union}(\mathbf{x}) = \min(\Phi_1, \Phi_2) - h^2 \cdot k \cdot \frac{1}{4}$$
*   **Smooth Subtraction:**
    $$\Phi_{diff}(\mathbf{x}) = \max(\Phi_1, -\Phi_2)$$
*   *Application in Robotics:* Merging intersecting tubular limbs into organic, hollow, fillet-reinforced joint sockets without manual beveling.

---

## 3. The Remeshing Pipeline: `Mesh to SDF` $\to$ `Volume to Mesh`

Geometry Nodes executes a 100% fail-safe solid modeling pipeline:

```
   [ Non-Manifold CAD / Photogrammetry Mesh ]
                      │
                      ▼
   [ Mesh to SDF Volume ]   ◄── Converts triangles into an OpenVDB narrow-band SDF;
                      │         Fills interior holes and welds self-intersections!
                      ▼
   [ Volume to Mesh ]       ◄── Marching Cubes extracts clean, watertight boundary;
                      │         Guaranteed zero non-manifold edges, zero internal faces!
                      ▼
   [ Production 3D Print / Physics Collision Mesh ]
```

### 3.1 Marching Cubes Isosurface Extraction (Lorensen & Cline)
*   The `Volume to Mesh` node iterates across active OpenVDB voxel cubes intersecting the $\Phi = 0$ zero-plane.
*   Based on an 8-bit index ($2^8 = 256$ topological cases), triangles are inserted across voxel edges via linear interpolation:
    $$\mathbf{p}_{vert} = \mathbf{x}_1 + \frac{-\Phi_1}{\Phi_2 - \Phi_1} (\mathbf{x}_2 - \mathbf{x}_1)$$
*   *Grid Resolution Setting:* Set voxel size ($V_{size}$) to half the minimum wall thickness of the part ($V_{size} \le 0.5 \cdot t_{min}$) to prevent thin walls from dissolving.

---

## 4. References & Standards

1.  **Museth, K. (2013).** *VDB: High-Resolution Sparse Volumes with Dynamic Topology.* ACM Transactions on Graphics (SIGGRAPH 2013), 32(3), Article 27. [DOI: 10.1145/2487228.2487235] (The OpenVDB data structure used natively in Blender).
2.  **Lorensen, W. E., & Cline, H. E. (1987).** *Marching Cubes: A High Resolution 3D Surface Construction Algorithm.* ACM SIGGRAPH Computer Graphics, 21(4), 163–169. [DOI: 10.1145/37402.37422] (The fundamental algorithm behind Volume to Mesh).
3.  **Quilez, I. (2013).** *Smooth Minimum and Distance Functions.* Articles on Computer Graphics (iquilezles.org). (The standard polynomial and exponential formulations of smooth SDF booleans).
4.  **Blender Foundation. (2024).** *Blender Documentation: Volume Nodes in Geometry Nodes.* https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/volume/
