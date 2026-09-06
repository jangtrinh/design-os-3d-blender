"""
bp_physics.py — Rigid Body Simulation & Point Cache Boilerplate.

Pure Data-API configuration of rigid body worlds, active/passive collisions,
and headless frame-by-frame simulation evaluation.
Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import bpy
from typing import Optional


def ensure_rigidbody_world(scene: Optional[bpy.types.Scene] = None) -> bpy.types.RigidBodyWorld:
    """
    Ensures a RigidBodyWorld exists on the scene and sets up its collections cleanly.
    """
    scene = scene or bpy.context.scene
    if scene.rigidbody_world is None:
        with bpy.context.temp_override(scene=scene):
            bpy.ops.rigidbody.world_add()

    rbw = scene.rigidbody_world
    if rbw.collection is None:
        col = bpy.data.collections.new("RigidBodyWorld")
        scene.collection.children.link(col)
        rbw.collection = col
    if rbw.constraints is None:
        con_col = bpy.data.collections.new("RigidBodyConstraints")
        scene.collection.children.link(con_col)
        rbw.constraints = con_col

    return rbw


def add_rigid_body(
    obj: bpy.types.Object,
    kind: str = 'ACTIVE',
    shape: str = 'CONVEX_HULL',
    mass: float = 1.0,
    scene: Optional[bpy.types.Scene] = None
) -> bpy.types.RigidBodyObject:
    """
    Pure Data API: linking a MESH object into rbw.collection auto-creates obj.rigid_body.
    Avoids context-sensitive bpy.ops.rigidbody.object_add.
    """
    rbw = ensure_rigidbody_world(scene)
    assert obj.type == 'MESH', "Rigid body requires a MESH object"
    if obj.name not in rbw.collection.objects:
        rbw.collection.objects.link(obj)

    rb = obj.rigid_body
    rb.type = kind
    rb.collision_shape = shape
    rb.mass = mass
    rb.friction = 0.5
    rb.restitution = 0.1
    return rb


def step_simulation_headless(scene: bpy.types.Scene, target_frame: int) -> bpy.types.Depsgraph:
    """
    Advances physics integrators step-by-step from frame_start to target_frame.
    Crucial for headless evaluation where no GUI timer runs.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    scene.frame_set(scene.frame_start)
    for f in range(scene.frame_start, target_frame + 1):
        scene.frame_set(f)
    bpy.context.view_layer.update()
    return dg


if __name__ == '__main__':
    print("Testing bp_physics.py headless...")
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 60

    # Floor plane
    mesh_floor = bpy.data.meshes.new("FloorMesh")
    floor = bpy.data.objects.new("Sim_Floor", mesh_floor)
    scene.collection.objects.link(floor)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=5.0)
    bm.to_mesh(mesh_floor)
    bm.free()
    floor.location = (0, 0, 0)
    add_rigid_body(floor, kind='PASSIVE', shape='MESH')

    # Falling cube
    mesh_cube = bpy.data.meshes.new("CubeMesh")
    cube = bpy.data.objects.new("Sim_Falling_Cube", mesh_cube)
    scene.collection.objects.link(cube)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh_cube)
    bm.free()
    cube.location = (0, 0, 5.0)
    add_rigid_body(cube, kind='ACTIVE', shape='BOX', mass=2.5)

    # Initial frame
    scene.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get()
    z_start = cube.evaluated_get(dg).matrix_world.translation.z

    # Step to frame 25
    dg = step_simulation_headless(scene, target_frame=25)
    z_mid = cube.evaluated_get(dg).matrix_world.translation.z

    print(f"Cube Evaluated Z at frame 1: {z_start:.3f} m, at frame 25: {z_mid:.3f} m")
    assert z_mid < z_start, "Rigid body did not fall under gravity!"
    print("bp_physics verified successfully.")
