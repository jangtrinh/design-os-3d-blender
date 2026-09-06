# Geometry Nodes Fields Architecture, Evaluation Model & Attribute Domains

Blender's **Geometry Nodes** is a node-based procedural modeling and physics system based on an asynchronous **Lazy Functional Evaluation Model** known as **Fields**.

---

## 1. The Core Paradigm: Data Flow vs. Field Flow

```
   Circular Socket ───────► DATA FLOW (Eager, Single Concrete Value / Mesh Data)
                            Evaluated immediately; flows from left to right.
   
   Diamond Socket  - - - -► FIELD FLOW (Deferred Pure Function / Lambda)
                            Evaluates lazily PER ELEMENT inside a Geometry context.
```

### 1.1 The Field as a Deferred Lambda Function
A diamond socket does not contain a list of numbers; it outputs a **stateless lambda expression**:
$$\text{Field}: \quad \mathcal{F}(\text{ElementContext}) \longrightarrow \text{Value}$$
*   A `Position` or `Normal` node outputs a function, not coordinates.
*   **The Execution Context:** When a Field is wired into `Set Position`, the node executes a parallel SIMD loop over all $N$ vertices in the active mesh domain:
    $$\forall i \in [0, N-1]: \quad \mathbf{p}_i \leftarrow \mathbf{p}_i + \mathcal{F}(\text{context}_i)$$
*   If a field is not connected to a Geometry node, **it is never evaluated and consumes zero memory**.

---

## 2. The Six Fundamental Attribute Domains & Interpolation Math

Mesh and curve geometries are divided into six hierarchical topological domains:

```
                  Attribute Domain Hierarchy
                  
         ┌───────────────────┐        ┌───────────────────┐
         │     FACE DOMAIN   │ ◄────► │    EDGE DOMAIN    │
         └─────────┬─────────┘        └─────────┬─────────┘
                   │                            │
                   ▼                            ▼
         ┌───────────────────┐        ┌───────────────────┐
         │   CORNER DOMAIN   │ ──────►│    POINT DOMAIN   │
         │  (UVs, Col, Loop) │        │ (Vertices, Knots) │
         └───────────────────┘        └───────────────────┘
```

### 2.1 Domain Definitions

| Domain | Underlying C++ Data-Block | Primary Use Cases | Typical Element Count ($N$) |
| :--- | :--- | :--- | :---: |
| **Point** | `Mesh.verts` / `Curves.points` | 3D vertex positions, deform weights, point cloud radius. | $V$ ($10^4\text{–}10^6$) |
| **Edge** | `Mesh.edges` | Crease weights, seam flags, wireframe thickness. | $E \approx 2 \times V$ |
| **Face** | `Mesh.polys` | Material indices, face normal vectors, shading flags. | $F \approx V$ |
| **Corner** | `Mesh.corners` (`MLoop`) | UV coordinates, split custom normals, vertex colors. | $C \approx 4 \times F$ |
| **Spline** | `Curves.curves` | Curve resolution, cyclic flags, spline type. | $S \ll V$ |
| **Instance** | `GeometrySet.instances` | Transform matrices ($4 \times 4$), instance IDs for scattering. | $I$ ($10^2\text{–}10^5$) |

### 2.2 Mathematical Domain Interpolation
When a field defined on one domain is sampled by a node operating on another domain, Blender applies automatic linear interpolation:

1.  **Point $\longrightarrow$ Face:**
    The value on face $F_k$ is the arithmetic average of its $M$ boundary vertices:
    $$\mathbf{v}_{Face}(F_k) = \frac{1}{M} \sum_{j \in \text{verts}(F_k)} \mathbf{v}_{Point}(j)$$
2.  **Face $\longrightarrow$ Point (Area-Weighted Normalization):**
    The value on vertex $P_i$ is the weighted average of connected faces, scaled by face surface area $A_k$:
    $$\mathbf{v}_{Point}(P_i) = \frac{\sum_{k \in \text{faces}(P_i)} A_k \cdot \mathbf{v}_{Face}(k)}{\sum_{k \in \text{faces}(P_i)} A_k}$$
3.  **Corner $\longrightarrow$ Point:**
    Corners with identical positions but differing UV seams are averaged, eliminating sharp UV splits.

---

## 3. Attribute Management: Anonymous vs. Stored Named Attributes

```
       Anonymous Attribute (Capture Attribute)           Stored Named Attribute
    ┌──────────────────────────────────────────┐      ┌──────────────────────────────────────────┐
    │ Bound to a specific Geometry wire.       │      │ Stored directly on the C++ Mesh ID block.│
    │ Destroyed automatically when wire ends.  │      │ Persists to disk; accessible in Shaders! │
    │ ★ Prevents memory leaks & name clashes!  │      │ ★ Exposes attributes to Cycles/EEVEE!    │
    └──────────────────────────────────────────┘      └──────────────────────────────────────────┘
```

### 3.1 `Capture Attribute` Node (Anonymous Data Flow)
*   Samples a field on an initial geometry state, caches the resulting array internally, and binds an anonymous handle to the geometry output socket.
*   *Essential Use Case:* Capturing the surface normal of a face *before* it is extruded, so the newly extruded side walls can be transformed relative to the original face normal.

### 3.2 `Store Named Attribute` Node (Shader Pipeline Bridge)
*   Stores an attribute as a permanent named column (e.g. `"heat_stress"`, `"roughness_wear"`) in the mesh data table.
*   In the Shader Editor, an `Attribute` node reads this name directly to modulate procedural PBR shaders.

---

## 4. Blender 4.0–5.2 Node Interface Architecture

> [!IMPORTANT]
> **API Breaking Change:** In Blender 4.0+, the legacy `node_tree.inputs.new()` and `node_tree.outputs.new()` API was **completely removed**. Node trees now use a unified **`node_tree.interface`** manager:

```python
import bpy

def setup_geometry_node_interface(node_tree):
    """Safely creates input and output sockets using the Blender 4.0+ interface API."""
    tree_interface = node_tree.interface
    tree_interface.clear()
    
    # 1. Add Geometry Input & Output sockets
    tree_interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    tree_interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    # 2. Add Custom User Control Parameters
    sock_radius = tree_interface.new_socket(name="Bevel Radius", in_out='INPUT', socket_type='NodeSocketFloat')
    sock_radius.default_value = 0.005
    sock_radius.min_value = 0.0
    sock_radius.max_value = 1.0
    
    sock_count = tree_interface.new_socket(name="Lobe Count", in_out='INPUT', socket_type='NodeSocketInt')
    sock_count.default_value = 12
    sock_count.min_value = 3
    sock_count.max_value = 128
```

---

## 5. References & Standards

1.  **Lucke, J. (2021).** *Geometry Nodes: The Fields Architecture.* Blender Developers Blog. https://code.blender.org/2021/08/geometry-nodes-fields/ (The original design specification of deferred functional field evaluation).
2.  **Blender Foundation. (2024).** *Blender Python API: NodeTreeInterface and GeometryNodeTree.* https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html
3.  **Kensler, P. (2006).** *Correlated Multi-Jittered Sampling for Subdivision Surfaces and Attribute Interpolation.* Pixar Technical Memo.
4.  **Botsch, M., & Kobbelt, L. (2004).** *An intuitive framework for real-time freeform modeling.* ACM Transactions on Graphics (SIGGRAPH 2004), 23(3), 630–634. (Topological domain transfer and area-weighted laplacian averaging).
