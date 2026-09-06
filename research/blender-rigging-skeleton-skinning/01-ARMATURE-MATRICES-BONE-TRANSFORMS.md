# Armature Coordinate Spaces, Bone Matrices & Roll Mathematics

Armatures in Blender are the most mathematically complex subsystem in `bpy`. An agent cannot successfully script rigging without understanding the four disjoint coordinate spaces and the exact matrix pipeline connecting **EditBones** to **PoseBones**.

---

## 1. The Four Distinct Armature Coordinate Spaces

```
   [ World Space (4x4) ]
             │
             ▼  (Armature Object World Matrix: obj.matrix_world)
   [ Armature Object Local Space ]
             │
             ▼  (EditBone Rest Matrix: edit_bone.matrix)
   [ Bone Rest Space (Head at Origin, Tail along +Y) ]
             │
             ▼  (PoseBone Animated Delta: pose_bone.matrix_basis)
   [ Final Posed Bone Space (pose_bone.matrix) ]
```

### 1.1 EditBone vs. PoseBone: Strict Separation of Modes
*   `EditBone` (`armature.edit_bones`): **Only accessible in EDIT mode (`bpy.ops.object.mode_set(mode='EDIT')`)**. Defines the immutable rest anatomy: joint pivot location (`head`), limb direction (`tail`), and twist angle (`roll`).
*   `PoseBone` (`object.pose.bones`): **Accessible in OBJECT and POSE modes**. Owns animation channels, constraints (IK, Damped Track), and runtime transformation matrices.
*   *Fatal Bug Pattern:* Modifying `edit_bone.head` while in Pose Mode, or querying `pose_bone.location` without updating the dependency graph, yields stale coordinates or raises runtime exceptions.

---

## 2. Bone Anatomy & The Bone Local Coordinate System

In Blender, every bone has a standardized, strict local coordinate orientation:

```
                              Tail (End Pivot)
                                     ▲
                                     │  +Y Axis (Collinear with Head-to-Tail Vector)
                                     │
                                     │
                     -X Axis ◄───────┼───────► +X Axis (Primary Bending Axis)
                                    /
                                   /  +Z Axis (Perpendicular Roll Axis)
                                  ▼
                               Head (Root Joint Pivot)
```

*   **Local +Y Axis:** Aligned strictly from `head` to `tail`:
    $$\mathbf{y}_{bone} = \frac{\mathbf{tail} - \mathbf{head}}{\|\mathbf{tail} - \mathbf{head}\|}$$
*   **Local +X and +Z Axes:** Orthogonal to $\mathbf{y}_{bone}$, rotated around $\mathbf{y}_{bone}$ by the scalar **`bone.roll`**.

---

## 3. Bone Roll Mathematics & The Z-Axis Singularity

Bone roll is defined in radians. It dictates which direction the local $+Z$ axis points when the bone is at rest.

### 3.1 The Vertical Singularity Trap
When computing orthogonal $+X$ and $+Z$ vectors from direction $\mathbf{y}$, standard algorithms cross $\mathbf{y}$ with world $+Z$ ($[0, 0, 1]^T$).
*   *The Catastrophe:* If a bone points straight up ($\mathbf{y} = [0, 0, 1]^T$, e.g. a robot vertical spine or human neck), the cross product vanishes:
    $$\mathbf{y} \times [0, 0, 1]^T = \mathbf{0}$$
*   The bone experiences a sudden, violent **$90^\circ\text{ or }180^\circ$ gimbal flip**, ruining IK bending planes and twisting mesh vertices.

### 3.2 Robust Bone Roll Calculation in Blender Python
To deterministically orient a bone's local Z-axis toward a target direction vector $\mathbf{v}_{target}$ without gimbal singularities:

```python
import bpy
import math
from mathutils import Vector, Matrix

def align_bone_roll_to_vector(edit_bone, target_z_dir=Vector((0, 0, 1))):
    """
    Sets bone.roll so that the bone's local +Z axis aligns as closely as possible
    to target_z_dir, completely avoiding vertical alignment singularities.
    """
    y_axis = (edit_bone.tail - edit_bone.head).normalized()
    
    # If bone is nearly vertical, use world -Y as the stable reference
    if abs(y_axis.z) > 0.999:
        ref_vector = Vector((0, -1, 0))
    else:
        ref_vector = Vector((0, 0, 1))
        
    # Construct orthogonal frame
    x_axis = ref_vector.cross(y_axis).normalized()
    z_axis = y_axis.cross(x_axis).normalized()
    
    # Construct base orientation matrix (without roll)
    base_matrix = Matrix((x_axis, y_axis, z_axis)).transposed()
    
    # Compute roll angle required to align local Z to target_z_dir
    projected_target = (target_z_dir - y_axis * target_z_dir.dot(y_axis)).normalized()
    cos_angle = max(-1.0, min(1.0, z_axis.dot(projected_target)))
    cross_prod = z_axis.cross(projected_target)
    
    roll = math.acos(cos_angle)
    if y_axis.dot(cross_prod) < 0:
        roll = -roll
        
    edit_bone.roll = roll
    return roll
```

---

## 4. The Transformation Matrix Pipeline

For any pose bone, its final $4 \times 4$ transformation matrix in Armature Object space is computed hierarchically:

$$\mathbf{M}_{pose} = \mathbf{M}_{parent, pose} \cdot \mathbf{M}_{rest, local} \cdot \mathbf{M}_{basis}$$

Where:
*   $\mathbf{M}_{rest, local}$: The relative rest transformation between the parent's rest frame and this bone's rest frame.
*   $\mathbf{M}_{basis}$: The local animation offset (`pose_bone.location`, `pose_bone.rotation_quaternion`, `pose_bone.scale`).
*   $\mathbf{M}_{pose}$: The evaluated matrix in object space (`pose_bone.matrix`).

To convert a point $\mathbf{p}$ from Bone Local Space into Global World Space:
$$\mathbf{p}_{world} = \mathbf{M}_{obj, world} \cdot \mathbf{M}_{pose} \cdot \mathbf{p}_{local}$$

---

## 5. Blender 4.x/5.x Bone Collections (Replacing Legacy 32 Layers)

Blender 4.0 completely removed the legacy 32-bit integer bone layer system (`bone.layers[0] = True`), replacing it with dynamic, named **Bone Collections**:

```python
def assign_bone_to_collection(armature_data, bone_name, collection_name="Deform_Bones"):
    """Assigns a bone to a named Bone Collection in Blender 5.2."""
    # Ensure collection exists
    bcoll = armature_data.collections.get(collection_name)
    if not bcoll:
        bcoll = armature_data.collections.new(name=collection_name)
        
    bone = armature_data.bones.get(bone_name)
    if bone:
        bcoll.assign(bone)
```

---

## 6. References & Standards

1.  **Shoemake, K. (1985).** *Animating rotation with quaternion curves.* ACM SIGGRAPH Computer Graphics, 19(3), 245–254. [DOI: 10.1145/325334.325242] (Foundational mathematics of spherical linear interpolation SLERP and gimbal lock avoidance).
2.  **Parent, R. (2012).** *Computer Animation: Algorithms and Techniques* (3rd ed.). Morgan Kaufmann. (Hierarchical kinematic trees, coordinate frame transformations, and forward/inverse kinematics).
3.  **Blender Foundation. (2024).** *Blender Python API: Bone and Armature Data Structures.* https://docs.blender.org/api/current/bpy.types.EditBone.html
4.  **van Gumster, J. (2020).** *Blender For Dummies* (4th ed.). John Wiley & Sons. (Practical standards for bone roll conventions, pole target alignments, and deform hierarchies).
