---
name: robotics-urdf-mechanisms
domain: cad-precision-robotics
blender_target: "5.2 LTS"
compat: "4.5 LTS+"
audience: ai-agent-bpy
description: Robotics kinematic hierarchies, joint coordinate frame orientation, visual vs collision mesh decimation, and URDF generation in Blender.
loads_with: [cad-precision-modeling, rigging-armature, export-interchange]
tags: [robotics, urdf, kinematics, joints, collision, inertia, physics-simulation, ros]
id: robotics-urdf-mechanisms
title: "Robotics Kinematic Mechanisms & URDF Integration"
when: [urdf-link-joint-frames, collision-vs-visual-mesh, inertia-tensor-from-mesh, rep-103-frames, closed-kinematic-chains]
trust_tier: draft
sources_checked: 2026-10-13
---

# Robotics Kinematic Mechanisms & URDF Integration

## Purpose
Shows how to prepare a Blender model as a kinematic tree for URDF: joint-pivot origins, ROS frame conventions, separate visual and collision geometry, and mass properties from a closed mesh. Design-reference note, not certification: verify frame conventions and inertia on the real exporter output before simulation or control use.

## When to Use / When NOT
- ALLOWED: turning a mechanism model into links, joints, collision proxies and inertial blocks for ROS 2 or a simulator
- ALLOWED: checking that a mesh is valid for polyhedral mass-property integration
- NOT ALLOWED: sensing, encoders and filtering — use `sensor-fusion-state-estimation` instead
- NOT ALLOWED: identifying real arm kinematic errors — use `kinematic-calibration-dh-metrology` instead
- NOT ALLOWED: ros2_control hardware interfaces and drive state machines — use `ros2-realtime-control-architecture` instead
- NOT ALLOWED: rigging for animation — use `rigging-armature` instead

## Core Knowledge Content

### 1. Mental model

In robotics, a 3D model is not just a visual skin—it is a **kinematic tree of rigid bodies (links)** coupled by **constrained degrees of freedom (joints)**, each possessing accurate mass, Center of Mass (CoM), and an inertia tensor.
1. **Coordinate Frame Alignment:** Physics simulators (ROS 2, Gazebo, MuJoCo, Isaac Sim) follow **ROS REP 103** (Right-Handed, +X Forward, +Y Left, +Z Up). Blender's native viewport (+X Right, +Y Depth/Back, +Z Up) needs an explicit rotational transform to match the robot forward axis. (Flagged 2026-10-13: the former "$+90^\circ$ around Z" is not stated in REP 103, which fixes the ROS body frame only; the exact angle depends on the exporter and the model's front. Verify on the exported URDF.) <!-- ease:source S1 anchor="Axis Orientation: x forward, y left, z up; all systems right handed" -->
2. **Dual-Geometry Principle:** Every link requires two distinct geometric representations: <!-- ease:source UNVERIFIED reason="300-triangle budget and 1000 Hz physics rate are unsourced heuristics" -->
   * **Visual Mesh:** Full aesthetic fidelity (PBR textures, chamfers, logos, high polygon count).
   * **Collision Geometry:** Convex envelopes or basic analytical primitives (capsules, cylinders, boxes) with minimal face counts ($\le 300$ triangles) for $1000\text{ Hz}$ physics stability.
3. **Inertia Tensor Invariance:** Moments of inertia must be computed from the exact closed manifold boundary using the Divergence Theorem, and expressed relative to the link's Center of Mass, not the Blender world origin. <!-- ease:source S3 anchor="surface integrals with outward-pointing unit normals; moments about the centre of mass are derived from the volume integrals" -->

### 2. Decision first

| Component | Visual Representation | Collision Representation | Inertia Method | Joint Axis Alignment |
| :--- | :--- | :--- | :--- | :--- |
| **Robot Base (Chassis)** | High-poly shell + hardware | Bounding box / 4–8 convex hulls | Polyhedral mesh integral | Ground frame / base_link |
| **Actuator Joint (Arm)** | Detailed housing + cables | Cylinders or capsules along axis | Analytical cylinder + rotor | Local +Z axis (standard) |
| **Link Arm (Beam)** | Ribbed hollow beam | Swept-sphere capsule or convex box | Polyhedral mesh integral | Along link length |
| **Gripper / End-Effector** | Fingers + rubber pads | Multiple oriented bounding boxes (OBB) | Component mass summation | Tool Center Point (TCP) |

Decision tree for joint & link preparation:
1. Does the link rotate or slide? → Place object origin **exactly at the physical joint axis of rotation/translation**.
2. Is the mesh concave? → Decompose into convex hulls or primitives for collision; never pass raw concave meshes to `<collision>`.
3. Does the link have moving parts inside? → Separate into parent and child links; define joint limits (`effort`, `velocity`, `lower`, `upper`). <!-- ease:source S2 anchor="JointLimits fields lower, upper, effort, velocity" -->

### 3. Rules

R1. Object Origin must sit at the Joint Pivot Point.
    Why: In URDF, joint origins are defined relative to the child link's coordinate frame. If the origin is placed at the link centroid instead of the hinge axis, joint rotation will orbit rather than pivot.
    Violation: Dislocated swinging links and broken kinematic kinematics.

R2. Collision meshes must be strictly convex or primitives. <!-- ease:source UNVERIFIED reason="GJK/EPA and O(N^2) claims unsourced; many simulators convexify meshes themselves" -->
    Why: GJK and EPA distance solvers require convex geometry. Non-convex meshes cause contact instability, simulator lag ($O(N^2)$ checks), and physics explosions.
    Violation: Simulation runs at 0.05x realtime or explodes on floor contact.

R3. Mesh normals must be consistently outward-facing before computing inertia. <!-- ease:source S3 anchor="section 3: outward-pointing unit-length normals in the surface integrals" -->
    Why: The Mirtich-Eberly polyhedral mass algorithm evaluates surface integrals with outward normal dot products. Inverted or flipped normals result in negative volume and negative inertia moments ($I_{xx} < 0$), causing physics engines to crash with NaN errors.
    Violation: Simulation crashes with "Inertia tensor is not positive definite".

R4. Apply transforms (`rotation=True`, `scale=True`) to visual meshes, but keep joint relative origins intact. <!-- ease:source UNVERIFIED reason="L^5 scaling is dimensional analysis (I ~ m L^2, m ~ L^3), derived in-module" -->
    Why: Unapplied scales skew inertia tensor integration by $scale^5$ (since inertia scales as $mass \times length^2 \propto volume \times length^2 \propto L^5$).
    Violation: Wildly incorrect mass and inertia calculations.

R5. Link coordinate frames must align with REP 103 conventions (+X forward, +Y left, +Z up). <!-- ease:source S1 anchor="Axis Orientation: x forward, y left, z up" -->
    Why: Disregarding REP 103 causes joint angles to rotate opposite to standard MoveIt / ROS control commands.
    Violation: Robot drives backwards or joints invert in RViz.

### 4. Recipe: Copy-paste patterns

#### Recipe 1: Generate Convex Collision Hull for a Link in Python

```python
import bpy

def generate_collision_hull(link_obj):
    """Duplicates the visual link mesh and decimates it. This is NOT a convex hull; see Recipe 1b for a true hull."""
    hull_obj = link_obj.copy()
    hull_obj.data = link_obj.data.copy()
    hull_obj.name = f"{link_obj.name}_collision"
    bpy.context.collection.objects.link(hull_obj)
    
    # Apply Remesh / Decimate to keep face count under 300 tris
    mod_dec = hull_obj.modifiers.new(name="CollisionDecimate", type='DECIMATE')
    mod_dec.ratio = 0.1  # Aggressive reduction
    
    # Or use Remesh blocks / Convex Hull operator
    return hull_obj
```

#### Recipe 1b: True convex hull of a link mesh

Recipe 1 only decimates. This one builds a convex hull from the link's vertices in a fresh bmesh. Checked 2026-10-13 on Blender 5.2.0 LTS with a torus: 0 non-manifold edges, signed volume 2.83 (a bounding cylinder is 3.19). The hull has more faces than the 300-triangle budget, so decimate it afterwards and re-check.

```python
import bpy, bmesh

def convex_hull_copy(link_obj):
    """Returns a new object holding the convex hull of link_obj's vertices (fresh loose-vertex bmesh, interior removed)."""
    bm = bmesh.new()
    for v in link_obj.data.vertices:
        bm.verts.new(v.co)
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:], use_existing_faces=False)
    bmesh.ops.delete(bm, geom=list(set(res["geom_interior"]) | set(res["geom_unused"])), context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    hull_mesh = bpy.data.meshes.new(f"{link_obj.name}_collision_mesh")
    bm.to_mesh(hull_mesh)
    bm.free()
    hull_obj = bpy.data.objects.new(f"{link_obj.name}_collision", hull_mesh)
    hull_obj.matrix_world = link_obj.matrix_world.copy()
    bpy.context.collection.objects.link(hull_obj)
    return hull_obj
```

#### Recipe 2: Calculate Mirtich-Eberly Inertia Tensor & Format URDF XML

```python
import bpy
import mathutils

def get_link_urdf_snippet(link_obj, mass_kg, com_local, inertia_tensor_com):
    """
    com_local: mathutils.Vector (x, y, z)
    inertia_tensor_com: 3x3 matrix [[ixx, ixy, ixz], [ixy, iyy, iyz], [ixz, iyz, izz]]
    """
    ixx = inertia_tensor_com[0][0]
    ixy = inertia_tensor_com[0][1]
    ixz = inertia_tensor_com[0][2]
    iyy = inertia_tensor_com[1][1]
    iyz = inertia_tensor_com[1][2]
    izz = inertia_tensor_com[2][2]
    
    snippet = f"""
  <link name="{link_obj.name}">
    <inertial>
      <origin xyz="{com_local.x:.6f} {com_local.y:.6f} {com_local.z:.6f}" rpy="0 0 0"/>
      <mass value="{mass_kg:.4f}"/>
      <inertia ixx="{ixx:.8f}" ixy="{ixy:.8f}" ixz="{ixz:.8f}"
               iyy="{iyy:.8f}" iyz="{iyz:.8f}"
               izz="{izz:.8f}"/>
    </inertial>
    <visual>
      <geometry>
        <mesh filename="package://robot_description/meshes/visual/{link_obj.name}.dae"/>
      </geometry>
    </visual>
    <collision>
      <geometry>
        <mesh filename="package://robot_description/meshes/collision/{link_obj.name}_collision.stl"/>
      </geometry>
    </collision>
  </link>
"""
    return snippet
```

#### Recipe 3: Align Object Origin to Selected Joint Axis Pivot

```python
import bpy

def set_origin_to_joint_pivot(obj, pivot_world_coord):
    """Sets object origin to the exact physical hinge coordinate without moving geometry."""
    saved_cursor = bpy.context.scene.cursor.location.copy()
    bpy.context.scene.cursor.location = pivot_world_coord
    
    # Set active and apply origin to 3D cursor
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    
    bpy.context.scene.cursor.location = saved_cursor
```

### 5. Anti-patterns & Traps

1. **The Origin at Bounding Box Center Trap:**
   Leaving the object origin at the geometric center of a robot arm link. When exported to URDF, the joint hinge pivots around the center of the arm tube instead of the bearing axis.
   *Fix:* Use `set_origin_to_joint_pivot` to place the origin on the bearing centerline.

2. **Negative Diagonal Inertia ($I_{xx} \le 0$):**
   Occurs when mesh has flipped normals or self-intersections during Divergence Theorem integration. <!-- ease:source S3 anchor="outward normals required by the surface integrals" -->
   *Fix:* Run `mesh.validate()` and ensure normals are oriented outside before computing inertia.

3. **Collision Mesh Overlap at Joint Interfaces:**
   If collision hulls of parent link and child link overlap at the hinge boundary, physics engines register a continuous phantom collision, generating explosive repulsive forces.
   *Fix:* Cut clearance margins ($1\text{–}2\text{ mm}$) at joint mating boundaries on collision hulls, or add `<disable_collision link1="..." link2="..."/>` in SRDF. <!-- ease:source UNVERIFIED reason="SRDF/MoveIt syntax not captured" -->

### 6. Verification & diagnostics

```python
def verify_positive_definite_inertia(ixx, iyy, izz, ixy, ixz, iyz):
    """Necessary-condition screen only (positive diagonal + triangle inequality). It ignores the off-diagonal terms, so positive-definiteness is NOT proven; check that the eigenvalues of the full tensor are > 0."""
    assert ixx > 0 and iyy > 0 and izz > 0, "Principal diagonal moments must be strictly positive"
    # Triangle inequality for moments of inertia:
    assert (ixx + iyy >= izz) and (ixx + izz >= iyy) and (iyy + izz >= ixx), \
        "Moments of inertia violate triangle inequality (A + B >= C)"
```

### 7. Production edge cases

*   **Closed Kinematic Chains (e.g. 4-bar linkages / Parallel wrists):** <!-- ease:source UNVERIFIED reason="URDF tree-only and MuJoCo/Gazebo closure syntax not captured" -->
    Standard URDF format does not support closed kinematic loops (it is strictly a tree structure). When exporting closed loops:
    1. Break the loop at a passive joint in URDF.
    2. Add a virtual floating joint.
    3. In MuJoCo (`<equality><connect>`) or Gazebo (`<joint type="revolute"><parent>...<child>...`), add the closing kinematic constraint explicitly in the simulation description.

### 8. Sources & References

- [ROS REP 103: Standard Units of Measure and Coordinate Conventions](https://www.ros.org/reps/rep-0103.html) (Right-handed, SI units, X-forward, Y-left, Z-up).
- [ROS REP 120: Coordinate Frames for Humanoid Robots](https://www.ros.org/reps/rep-0120.html) (`base_link`, `base_footprint`, torso, gaze, feet contact frames).
- Mirtich, B. (1996). "Fast and Accurate Computation of Polyhedral Mass Properties". *Journal of Graphics Tools*, 1(2): 31–50. [DOI: 10.1080/10867651.1996.10487458](https://doi.org/10.1080/10867651.1996.10487458).
- Eberly, D. "Polyhedral Mass Properties (Revisited)". *Geometric Tools Technical Report* (created 2002-12-31, last modified 2009-11-03 per the PDF header; the former "2004" date was not confirmed). [geometrictools.com/Documentation/PolyhedralMassProperties.pdf](https://www.geometrictools.com/Documentation/PolyhedralMassProperties.pdf).
- Lynch, K. M., & Park, F. C. (2017). *Modern Robotics: Mechanics, Planning, and Control*. Cambridge University Press. ISBN: 978-1107156302. (Screw theory, Product of Exponentials, spatial inertia tensors).
- Craig, J. J. (2005). *Introduction to Robotics: Mechanics and Control* (3rd ed.). Pearson / Prentice Hall. ISBN: 978-0201543612.
- Mamou, K. (2016). *V-HACD: Volumetric-Hierarchical Approximate Convex Decomposition*. GitHub repository: `kmammou/v-hacd`.
- [Blender 5.2 Python API — `mathutils.Matrix`](https://docs.blender.org/api/current/mathutils.Matrix.html) & [`bpy.types.Object.evaluated_get`](https://docs.blender.org/api/current/bpy.types.Object.html)
- Empirically verified against `scripts/compute-mesh-inertia.py` on Blender 5.2.0 LTS: analytical cube inertia moment matches computed $I_{xx} = 5.333333\text{ kg}\cdot\text{m}^2$ within $1.59 \times 10^{-7}\text{ kg}\cdot\text{m}^2$ error. <!-- ease:source S4 anchor="cube Ixx 5.333333 computed 5.333333, err 1.59e-07, ALL TESTS PASSED (re-run 2026-10-13)" -->

## Failure Modes (Mandatory)
- **Joint swings around the link centre instead of the hinge** — cause: object origin left at the bounding-box centre — fix: set the origin to the joint axis (Recipe 3)
- **Physics engine reports non-positive-definite inertia or NaN** — cause: inside-out normals or self-intersections give negative volume (S3 uses outward normals) — fix: validate and recalculate normals before integration
- **`generate_collision_hull` output is not convex** — cause: Recipe 1 only decimates (annotation in catalog-config) — fix: use Recipe 1b (verified, S5)
- **Phantom collisions at a hinge** — cause: parent and child collision shapes overlap at the joint — fix: add clearance or disable the pair in the planning config
- **Robot drives backwards or joints invert in RViz** — cause: frames not following x forward, y left, z up (S1) — fix: apply the exporter axis conversion and re-check

## Sources
- [S1] REP 103: Standard Units of Measure and Coordinate Conventions (raw rst from ros-infrastructure/rep) — https://raw.githubusercontent.com/ros-infrastructure/rep/master/rep-0103.rst — knowledge/_evidence/kb-261013/w7-rep-0103.rst (www.ros.org/reps page is behind a bot check and was not fetched) — captured 2026-10-13 — sha256 bf397ddcab96cc1d10d8f5893960cb1d5e50154dd96462433a5ac342237a0c20
- [S2] urdfdom_headers joint.h (JointLimits: lower, upper, effort, velocity) — https://raw.githubusercontent.com/ros/urdfdom_headers/master/include/urdf_model/joint.h — knowledge/_evidence/kb-261013/w7-urdf-joint.md.txt — captured 2026-10-13 — sha256 57c69feb617b373416fcf674fd54dd93e1c17be79b0c1eec8097e93bb94004a5
- [S3] Eberly, D., "Polyhedral Mass Properties (Revisited)", Geometric Tools (created 2002-12-31, last modified 2009-11-03 per PDF header) — https://www.geometrictools.com/Documentation/PolyhedralMassProperties.pdf — knowledge/_evidence/kb-261013/w7-eberly-polyhedral.pdf — captured 2026-10-13 — sha256 70c001aa8f8dd8eba7c4331688f5be3cc37720d7998c64ffbd4830e332449193
- [S4] Repo: mesh inertia script and its Blender 5.2.0 LTS self-test output — scripts/compute-mesh-inertia.py — knowledge/_evidence/kb-261013/w7-compute-mesh-inertia-test-output.txt — captured 2026-10-13 — sha256 4a65191466674d6091bf2f51fcc55d8f14cc6e4c97c619d30543d64f2b0a93b0
- [S5] Blender 5.2.0 LTS convex-hull recipe check (script) — knowledge/_evidence/kb-261013/w7-convex-hull-recipe-check.py — captured 2026-10-13 — sha256 50744a24964b053fe26cebb26cc2d9b7523306862fbd56cd0f566d3c91f9da76
- [S6] Blender 5.2.0 LTS convex-hull recipe check (output) — knowledge/_evidence/kb-261013/w7-convex-hull-recipe-check-output.txt — captured 2026-10-13 — sha256 5465b0a93de3be5789bda75278061bbc7ccd9576fc270baf6786b63db621a3da
- [S7] Mirtich, B. (1996), "Fast and Accurate Computation of Polyhedral Mass Properties", Journal of Graphics Tools 1(2) — bibliographic entry (not re-read) — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)
- [S8] Lynch & Park (2017) Modern Robotics; Craig (2005) Introduction to Robotics — bibliographic entries (not re-read) — captured 2026-10-13 — sha256 NOT-CAPTURED (bibliographic entry only)
