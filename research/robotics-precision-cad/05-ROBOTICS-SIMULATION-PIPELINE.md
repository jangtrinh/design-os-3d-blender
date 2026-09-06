# Robotics Simulation Pipeline: URDF, Kinematics & Mesh Physics

**Date:** 2026-09-05  
**Scope:** ROS REP 103/120 coordinate frame conventions, URDF/SDF/MJCF specifications, visual vs. collision geometry decomposition, and analytical inertia tensor calculation via the Mirtich-Eberly algorithm.

---

## 1. Coordinate Frame Standards & Conventions (ROS REP 103 / REP 120)

Coordinate discrepancies between CAD packages, Blender, and physics engines are the leading cause of inverted joint motions, upside-down sensors, and unstable simulation controllers.

### 1.1 ROS REP 103 Standard Conventions
*   **Chirality:** Right-Handed Cartesian System.
*   **Units:** International System of Units (SI):
    *   Linear Distance: **Meters ($m$)**
    *   Mass: **Kilograms ($kg$)**
    *   Angles: **Radians ($rad$)**
    *   Force: **Newtons ($N$)**
    *   Torque: **Newton-meters ($N\cdot m$)**
*   **Body-Fixed Axis Orientation:**
    *   **+X:** Forward (direction of travel / front)
    *   **+Y:** Left
    *   **+Z:** Up (against gravity)

```
              +Z (Up)
                 ▲
                 │
                 │   +X (Forward)
                 │  /
                 │ /
                 └──────────► +Y (Left)
```

### 1.2 Coordinate System Alignment: Blender vs. ROS
*   **Blender Viewport:** +X Right, +Y Forward/Depth, +Z Up.
*   **ROS Robot Frame:** +X Forward, +Y Left, +Z Up.
*   *Transformation Matrix ($R_{Blender \to ROS}$):*
    To export from Blender to ROS without altering link geometry:
    $$\begin{bmatrix} X_{ROS} \\ Y_{ROS} \\ Z_{ROS} \end{bmatrix} = \begin{bmatrix} 0 & 1 & 0 \\ -1 & 0 & 0 \\ 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} X_{Blender} \\ Y_{Blender} \\ Z_{Blender} \end{bmatrix}$$
    *(A $+90^\circ$ rotation around Z-axis).*

### 1.3 Humanoid Kinematic Frame Hierarchy (ROS REP 120)
*   `base_footprint`: 2D planar projection of the robot center on the floor between the feet ($Z = 0$).
*   `base_link`: Root body of the robot, rigidly attached to the pelvis / waist.
*   `torso_link`: Upper torso above waist yaw/pitch joints.
*   `head_link` / `gaze`: Center of optical vision sensors.
*   `left_sole_link` / `right_sole_link`: Flat ground contact surface of foot.

---

## 2. Robot Description Formats: URDF, SDF & MJCF

### 2.1 Format Comparison Matrix

| Feature | URDF (ROS / ROS 2) | SDF (Gazebo / Ignition) | MJCF (MuJoCo) |
| :--- | :--- | :--- | :--- |
| **Data Schema** | XML (strict tree graph). | XML (general graph). | XML (compact tree with equality constraints). |
| **Closed Kinematic Loops** | Unsupported natively (requires dummy links or extensions). | Full native support. | Full native support via `<equality><connect>`. |
| **Collision Primitives** | Box, Cylinder, Sphere, Mesh. | Box, Cylinder, Sphere, Capsule, Mesh, Heightmap. | Capsule, Box, Cylinder, Sphere, Ellipsoid, Mesh. |
| **Contact Friction Models** | Basic Coulomb ($\mu_1, \mu_2$). | ODE / Bullet advanced multi-axis friction. | Pyramidal / Elliptic cone with rotational and torsional slip. |
| **Target Engines** | RViz, MoveIt, PyBullet, Isaac Sim (via URDF importer). | Gazebo Sim, Ignition Physics. | MuJoCo (Reinforcement Learning & System ID). |

### 2.2 URDF Link & Joint XML Architecture
```xml
<robot name="precision_joint_module">
  <!-- LINK DEFINITION -->
  <link name="link_arm">
    <inertial>
      <!-- Center of Mass relative to link frame origin -->
      <origin xyz="0.052 0.001 -0.012" rpy="0 0 0"/>
      <mass value="1.450"/>
      <!-- 3x3 Symmetric Inertia Tensor computed at CoM -->
      <inertia ixx="0.00345" ixy="-0.00002" ixz="0.00012"
               iyy="0.00892" iyz="0.00004"
               izz="0.00678"/>
    </inertial>
    
    <!-- HIGH-DETAIL VISUAL MESH -->
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <mesh filename="package://robot_description/meshes/visual/link_arm.dae"/>
      </geometry>
      <material name="anodized_black"/>
    </visual>
    
    <!-- SIMPLIFIED CONVEX COLLISION HULL -->
    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <mesh filename="package://robot_description/meshes/collision/link_arm_hull.stl"/>
      </geometry>
    </collision>
  </link>

  <!-- JOINT DEFINITION -->
  <joint name="joint_1_revolute" type="revolute">
    <parent link="base_link"/>
    <child link="link_arm"/>
    <!-- Position of joint pivot in parent link frame -->
    <origin xyz="0.0 0.0 0.125" rpy="0 0 0"/>
    <!-- Rotation axis unit vector in joint frame -->
    <axis xyz="0 0 1"/>
    <limit lower="-3.14159" upper="3.14159" effort="50.0" velocity="4.2"/>
    <dynamics damping="0.1" friction="0.05"/>
  </joint>
</robot>
```

---

## 3. Visual vs. Collision Geometry Decomposition

The most common mistake in robotics simulation is using the visual CAD mesh as the collision geometry.

```
      High-Poly Visual Mesh               V-HACD Convex Hull Collision
    (50,000 tris, chamfers, fillets)        (320 tris, watertight convex envelope)
         ┌───────────────┐                       ┌───────────────┐
        /                 \                     /                 \
       │  Visual Beauty    │                   │  Fast O(1) GJK    │
       │  PBR Textures     │                   │  Physics Query    │
        \                 /                     \                 /
         └───────────────┘                       └───────────────┘
```

### 3.1 Why Raw CAD Meshes Crash Simulators
1.  **Computational Complexity:** Collision detection between arbitrary non-convex meshes scales as $O(N_1 \cdot N_2)$. A pair of $50\text{k}$-face links requires up to $2.5 \times 10^9$ triangle intersection checks per physics tick ($1000\text{ Hz}$).
2.  **Concavity Snagging:** Non-convex meshes trap interpenetrating vertices during contact solver iterations, resulting in explosive numerical impulses ("mesh explosion").
3.  **Capsules and Primitive Superiority:**
    *   Spheres, Cylinders, Boxes, and **Capsules** evaluate analytical distance queries in $O(1)$ time with exact surface normals.
    *   Where possible, approximate robotic links (especially limbs and shafts) with **swept-sphere capsules**.

### 3.2 V-HACD (Volumetric Hierarchical Approximate Convex Decomposition)
When organic or complex mechanical shapes cannot be represented by simple primitives:
*   Pass the watertight manifold mesh through **V-HACD**.
*   V-HACD divides the complex concave volume into a minimal collection of non-overlapping **convex hulls** ($K = 4\text{–}16$ hulls).
*   Each convex hull is evaluated using the ultra-fast **Gilbert-Johnson-Keerthi (GJK)** and **Expanding Polytope Algorithm (EPA)** distance algorithms.

---

## 4. Analytical Mass Properties & The Mirtich-Eberly Algorithm

Accurate dynamic simulation requires three physical quantities for every rigid link:
1.  **Total Mass ($M$):** $M = \rho \cdot V$ (given uniform density $\rho$).
2.  **Center of Mass ($\vec{r}_{CoM}$):**
    $$\vec{r}_{CoM} = \frac{1}{V} \iiint_V \begin{bmatrix} x \\ y \\ z \end{bmatrix} dV$$
3.  **$3 \times 3$ Inertia Tensor ($I$):**
    $$I = \begin{bmatrix} I_{xx} & I_{xy} & I_{xz} \\ I_{yx} & I_{yy} & I_{yz} \\ I_{zx} & I_{zy} & I_{zz} \end{bmatrix}$$
    Where diagonal moments of inertia are:
    $$I_{xx} = \rho \iiint_V (y^2 + z^2) dV, \quad I_{yy} = \rho \iiint_V (x^2 + z^2) dV, \quad I_{zz} = \rho \iiint_V (x^2 + y^2) dV$$
    And off-diagonal products of inertia are:
    $$I_{xy} = -\rho \iiint_V xy \, dV, \quad I_{xz} = -\rho \iiint_V xz \, dV, \quad I_{yz} = -\rho \iiint_V yz \, dV$$

### 4.1 Reduction via Gauss's Divergence Theorem
Brian Mirtich (1996) and David Eberly established that for any closed, orientable triangle mesh, volume integrals can be reduced to boundary surface integrals over individual planar triangles:
$$\iiint_V (\nabla \cdot \mathbf{F}) \, dV = \iint_{\partial V} (\mathbf{F} \cdot \mathbf{n}) \, dA$$
By choosing vector fields $\mathbf{F}$ whose divergences equal $1, x, y, z, x^2, y^2, z^2, xy, yz, xz$, all 10 canonical volume integrals are computed in a **single $O(N)$ traversal** of the mesh's triangular facets.

### 4.2 Parallel Axis Theorem (Steiner's Theorem)
If the inertia tensor is initially computed around an arbitrary coordinate origin $O$, it must be shifted to the link's Center of Mass $\vec{r}_{CoM} = [x_c, y_c, z_c]^T$ for URDF specification:
$$I_{xx}^{CoM} = I_{xx}^{O} - M (y_c^2 + z_c^2)$$
$$I_{yy}^{CoM} = I_{yy}^{O} - M (x_c^2 + z_c^2)$$
$$I_{zz}^{CoM} = I_{zz}^{O} - M (x_c^2 + y_c^2)$$
$$I_{xy}^{CoM} = I_{xy}^{O} + M (x_c y_c)$$
$$I_{xz}^{CoM} = I_{xz}^{O} + M (x_c z_c)$$
$$I_{yz}^{CoM} = I_{yz}^{O} + M (y_c z_c)$$

*(Note on sign conventions: ROS URDF defines products of inertia without the leading minus sign, so $ixy = -\int xy dm$; verify simulation engine conventions before export).*

---

## 5. References & Standards

1.  **Mirtich, B. (1996).** *Fast and Accurate Computation of Polyhedral Mass Properties.* Journal of Graphics Tools, 1(2), 31–50. [DOI: 10.1080/10867651.1996.10487458] (Seminal paper reducing 3D volume integrals of mass, centroid, and inertia tensor to boundary face integrals via divergence theorem).
2.  **Eberly, D. (2004).** *Polyhedral Mass Properties.* Geometric Tools LLC, technical report. (Explicit closed-form algorithms for triangle mesh mass property calculation).
3.  **ROS REPs (Robot Operating System Enhancement Proposals):**
    *   *REP 103:* Standard Units of Measure and Coordinate System Conventions (Right-hand rule, SI units, X-forward, Y-left, Z-up).
    *   *REP 120:* Coordinate Frames for Humanoid Robots (`base_link`, `torso_link`, `pelvis`).
4.  **Mamou, K., & Ghorbel, F. (2009).** *A simple and efficient approach for 3D mesh approximate convex decomposition.* IEEE International Conference on Image Processing (ICIP), 3501–3504. (Mathematical basis for V-HACD algorithm).
5.  **Gilbert, E. G., Johnson, D. W., & Keerthi, S. S. (1988).** *A fast procedure for computing the distance between complex objects in three-dimensional space.* IEEE Journal on Robotics and Automation, 4(2), 193–203. (The GJK algorithm for convex distance queries).
6.  **Open Robotics / ROS.org. (2024).** *URDF (Unified Robot Description Format) XML Specification.* https://wiki.ros.org/urdf/XML

