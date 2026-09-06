# Inverse Kinematics Solvers: CCD, FABRIK & Pole Angle Mathematics

Forward Kinematics (FK) calculates end-effector position from given joint angles ($\mathbf{x} = f(\boldsymbol{\theta})$). **Inverse Kinematics (IK)** solves the non-linear reverse problem: finding the vector of joint angles $\boldsymbol{\theta}$ that positions an end-effector at a desired 3D spatial target $\mathbf{x}_{target}$.

---

## 1. The Standard Solvers: CCD vs. FABRIK vs. Jacobian DLS

```
   [ Standard Blender IK (CCD) ]               [ FABRIK Solver ]
   Iterates through bone angles from           Iterates forward & backward through joint
   effector to root; fast, heuristic.          positions using pure line-segment geometry.
```

### 1.1 Cyclic Coordinate Descent (CCD)
Wang & Chen (1991):
1.  Start at the last bone before the end-effector ($i = N$).
2.  Compute vector from joint $i$ to current end-effector: $\mathbf{r}_c = \mathbf{p}_e - \mathbf{p}_i$.
3.  Compute vector from joint $i$ to target: $\mathbf{r}_t = \mathbf{p}_t - \mathbf{p}_i$.
4.  Compute rotation angle $\alpha$ and unit rotation axis $\mathbf{n}$:
    $$\cos\alpha = \frac{\mathbf{r}_c \cdot \mathbf{r}_t}{\|\mathbf{r}_c\| \|\mathbf{r}_t\|}, \quad \mathbf{n} = \frac{\mathbf{r}_c \times \mathbf{r}_t}{\|\mathbf{r}_c \times \mathbf{r}_t\|}$$
5.  Apply rotation to joint $i$, clamp to joint angle limits, and step backward to parent joint $i - 1$.
6.  Repeat entire chain iteration until error $\|\mathbf{p}_e - \mathbf{p}_t\| < \epsilon_{tol}$ (typically $20\text{–}50\text{ iterations}$).

### 1.2 Jacobian Damped Least Squares (DLS)
For continuous kinematic velocity mapping $\mathbf{\dot{x}} = \mathbf{J}(\boldsymbol{\theta}) \boldsymbol{\dot{\theta}}$:
Near kinematic singularities (fully outstretched arm where $\det(\mathbf{J}\mathbf{J}^T) \to 0$), the standard pseudo-inverse $\mathbf{J}^\dagger = \mathbf{J}^T(\mathbf{J}\mathbf{J}^T)^{-1}$ blows up to infinity, causing joints to whip violently.
*   **Damped Least Squares (Levenberg-Marquardt):**
    $$\mathbf{J}^* = \mathbf{J}^T (\mathbf{J} \mathbf{J}^T + \lambda^2 \mathbf{I})^{-1}$$
    Where damping factor $\lambda$ bounds maximum angular velocity, providing silky-smooth motion through full arm extension. (Blender's `iTaSC` solver uses DLS).

---

## 2. The Pole Target Vector & The Knee/Elbow Bending Plane

An IK chain with 2 bones (e.g. Upper Arm + Forearm) has **1 redundant degree of freedom**: the elbow can swivel in a continuous circle around the shoulder-to-wrist axis while keeping the hand pinned to the target.

```
                         Elbow Joint (Pole Plane)
                                  ╭─► •
                                 /     \
                                /       \
                               /         \
                              ▼           ▼
                      Shoulder (Root)    Wrist (IK Target)
```

To resolve this ambiguity, animators place a **Pole Target bone** (e.g., in front of the knee or behind the elbow).

---

## 3. The Pole Angle Twitching Problem & Exact Formula

The most notorious bug in Blender rigging: **assigning a Pole Target immediately rotates the knee or elbow $90^\circ$ or $180^\circ$ out of plane!**

### 3.1 Root Cause
*   Blender constructs a mathematical reference plane from the IK chain's root bone rest orientation.
*   If the rest bone roll does not align with the world vector connecting the root bone to the pole target, an offset phase angle exists between the solver's internal coordinate frame and the visual pole target.

### 3.2 Exact Mathematical Pole Angle Calculation
To calculate the exact `pole_angle` (in radians) so that the arm does not move a single millimeter when the constraint is activated:

```python
import bpy
import math
from mathutils import Vector

def calculate_exact_pole_angle(armature_obj, root_bone_name, mid_bone_name, pole_pos_world):
    """
    Calculates the exact pole_angle required for an IK constraint to eliminate
    all knee/elbow twitching.
    """
    pose = armature_obj.pose
    root = pose.bones[root_bone_name]
    mid = pose.bones[mid_bone_name]
    
    # World positions of joints
    p_root = armature_obj.matrix_world @ root.head
    p_mid = armature_obj.matrix_world @ mid.head
    p_tail = armature_obj.matrix_world @ mid.tail
    
    # 1. Normal of current limb bending plane
    v_chain_root = (p_mid - p_root).normalized()
    v_chain_tail = (p_tail - p_mid).normalized()
    plane_normal_current = v_chain_root.cross(v_chain_tail).normalized()
    
    # 2. Desired bending plane toward the pole target
    v_axis = (p_tail - p_root).normalized()
    v_to_pole = (pole_pos_world - p_root).normalized()
    plane_normal_pole = v_axis.cross(v_to_pole).normalized()
    
    # 3. Compute signed angle between current plane and pole plane
    cos_angle = max(-1.0, min(1.0, plane_normal_current.dot(plane_normal_pole)))
    cross_vec = plane_normal_current.cross(plane_normal_pole)
    
    angle = math.acos(cos_angle)
    if v_axis.dot(cross_vec) < 0.0:
        angle = -angle
        
    return angle
```

---

## 4. Setting up a 2-Bone IK Leg in Blender 5.2 via Python

```python
def setup_leg_ik(armature_obj, shin_name="Shin.L", target_name="Foot_IK.L", pole_name="Knee_Pole.L"):
    """Configures a rock-solid 2-bone IK constraint on the shin bone."""
    pose_bones = armature_obj.pose.bones
    shin_pbone = pose_bones[shin_name]
    
    # Add IK constraint
    ik_con = shin_pbone.constraints.new(type='IK')
    ik_con.target = armature_obj
    ik_con.subtarget = target_name
    ik_con.chain_count = 2 # Upper leg + Lower leg only (does not affect hips)
    ik_con.iterations = 50 # High convergence accuracy
    
    # Pole Target configuration
    ik_con.pole_target = armature_obj
    ik_con.pole_subtarget = pole_name
    # Standard human leg oriented with local Z forward requires pole_angle = -90° (-1.5708 rad)
    ik_con.pole_angle = -math.pi / 2.0
```

---

## 5. References & Standards

1.  **Aristidou, A., & Lasenby, J. (2011).** *FABRIK: A fast, iterative solver for the Inverse Kinematics problem.* Graphical Models, 73(5), 243–260. [DOI: 10.1016/j.gmod.2011.05.003] (The foundational geometric forward-and-backward solver).
2.  **Buss, S. R. (2004).** *Introduction to Inverse Kinematics with Jacobian Transpose, Pseudoinverse and Damped Least Squares methods.* IEEE Journal of Robotics and Automation, 17, 1–19. (Theoretical formulation of singularity damping in inverse kinematics).
3.  **Wang, L. C. T., & Chen, C. C. (1991).** *A combined optimization method for solving the inverse kinematics problems of mechanical manipulators.* IEEE Transactions on Robotics and Automation, 7(4), 489–499. (The original formulation of Cyclic Coordinate Descent CCD).
4.  **Blender Foundation. (2024).** *Blender Documentation: Inverse Kinematics & iTaSC Solver Guide.* https://docs.blender.org/manual/en/latest/animation/armatures/posing/bone_constraints/inverse_kinematics/
