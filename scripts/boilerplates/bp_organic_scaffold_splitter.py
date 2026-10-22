"""
bp_organic_scaffold_splitter.py — Organic Mesh Frozen Scaffold Repair, Retopology & Parametric Split.

Solves Truong's Case 2 Failure Mode:
When a user provides an organic mesh (jewelry, figurine, sculpture from Tripo/Meshy/Hy3D
or high-res 3D scan) stored locally as a frozen scaffold, the agent must NEVER attempt
to reconstruct the organic silhouette from 360-degree render images using procedural primitives
("primitive soup hallucination"). Instead, the agent:
  1. Locks the local geometry (zero-rebuild contract).
  2. Cleans and repairs the mesh into a watertight 2-manifold solid (V > 0, 0 non-manifold edges).
  3. Parametrically splits the solid across a cutting plane with CNC/3D-print clearance.
  4. Generates integral male dowel alignment pins with 45-degree lead-in chamfers and matching
     female relief sockets for zero-collision press-fit manufacturing.

Target: Blender 5.2 LTS (Headless-safe via Data API depsgraph, zero GUI context dependencies).
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import bmesh
import bpy
from mathutils import Matrix, Vector

# Ensure agent_runtime is importable from repo scripts
_HERE = Path(__file__).resolve().parent
_SCRIPTS_DIR = _HERE.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import agent_runtime as rt


def apply_modifiers_data_api(obj: bpy.types.Object) -> None:
    """
    Applies all modifiers on obj via the evaluated depsgraph data API.
    Completely avoids bpy.ops.modifier_apply (context-free, headless-safe).
    """
    if not obj.modifiers:
        return
    dg = bpy.context.evaluated_depsgraph_get()
    eval_me = bpy.data.meshes.new_from_object(
        obj.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg
    )
    obj.modifiers.clear()
    old_me = obj.data
    obj.data = eval_me
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)


def prepare_frozen_organic_scaffold(
    obj: bpy.types.Object,
    merge_dist: float = 1e-5
) -> Dict[str, Any]:
    """
    Strips external/vendor materials, removes duplicate vertices, dissolves degenerate
    edges/faces, recalculates outward face normals, and verifies positive signed volume
    (V > 0) and non_manifold_edges == 0.

    Parameters:
        obj: The Blender mesh object representing the organic scaffold.
        merge_dist: Distance threshold in meters for welding duplicate vertices and degenerates.

    Returns:
        Dict containing diagnostic statistics.
    """
    # 1. Strip external vendor materials (Tripo/Meshy placeholder shaders)
    obj.data.materials.clear()

    # 2. BMesh topological cleanup
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    initial_verts = len(bm.verts)
    initial_faces = len(bm.faces)

    # Weld duplicate vertices from triangulated scan boundaries
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=merge_dist)
    doubles_removed = initial_verts - len(bm.verts)

    # Dissolve zero-length edges and zero-area degenerate faces
    bmesh.ops.dissolve_degenerate(bm, dist=merge_dist, edges=list(bm.edges))

    # Detect and prune internal non-manifold faces (edges shared by >2 faces)
    bad_faces = [f for f in bm.faces if any(len(e.link_faces) > 2 for e in f.edges)]
    if bad_faces:
        bmesh.ops.delete(bm, geom=bad_faces, context="FACES")

    # Enforce outward consistent face normals
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))

    # Inverted surface check: if signed volume is negative, reverse winding
    vol = bm.calc_volume(signed=True)
    if vol < 0.0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        vol = bm.calc_volume(signed=True)

    non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
    non_manifold_verts = sum(1 for v in bm.verts if not v.is_manifold)

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()

    # Assert watertight 2-manifold contract
    assert non_manifold_edges == 0, (
        f"Organic scaffold repair failed: {non_manifold_edges} non-manifold edges remain"
    )
    assert non_manifold_verts == 0, (
        f"Organic scaffold repair failed: {non_manifold_verts} non-manifold vertices remain"
    )
    assert vol > 0.0, (
        f"Organic scaffold repair failed: signed volume must be positive, got {vol}"
    )
    assert len(obj.data.materials) == 0, "Vendor materials were not cleared"

    return {
        "doubles_removed": doubles_removed,
        "degenerate_faces_removed": initial_faces - len(obj.data.polygons),
        "non_manifold_edges": non_manifold_edges,
        "non_manifold_verts": non_manifold_verts,
        "signed_volume": vol,
        "vertex_count": len(obj.data.vertices),
        "polygon_count": len(obj.data.polygons),
    }


def create_cutter_box(
    name: str,
    plane_co: Vector,
    plane_no: Vector,
    offset: float,
    size: float,
    cut_upper: bool
) -> bpy.types.Object:
    """
    Creates a solid cutter cube for EXACT boolean DIFFERENCE.
    If cut_upper is True: covers the half-space where (x - plane_co) . plane_no >= offset.
    If cut_upper is False: covers the half-space where (x - plane_co) . plane_no <= offset.
    """
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector((size, size, size)), verts=bm.verts)

    # Shift so boundary face sits at Z=0
    shift_z = (size / 2.0) if cut_upper else (-size / 2.0)
    bmesh.ops.translate(bm, vec=Vector((0.0, 0.0, shift_z)), verts=bm.verts)

    # Rotate local +Z towards plane_no
    up = Vector((0.0, 0.0, 1.0))
    rot_q = up.rotation_difference(plane_no.normalized())
    rot_mat = rot_q.to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=rot_mat, verts=bm.verts)

    # Translate boundary face to interface plane: plane_co + plane_no * offset
    boundary_pt = plane_co + plane_no.normalized() * offset
    bmesh.ops.translate(bm, vec=boundary_pt, verts=bm.verts)

    me = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(me)
    bm.free()
    me.update()

    cutter = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(cutter)
    return cutter


def split_organic_mesh_with_clearance(
    obj: bpy.types.Object,
    plane_co: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    plane_no: Tuple[float, float, float] = (0.0, 0.0, 1.0),
    clearance_mm: float = 0.3,
    unit_scale: float = 1e-3
) -> Tuple[bpy.types.Object, bpy.types.Object]:
    """
    Duplicates the manifold organic solid into Upper and Lower half-parts and cuts them
    using EXACT boolean cutter boxes offset by +/- clearance_mm / 2 so both halves remain
    closed 2-manifold solids separated by exact machining/assembly clearance.

    Parameters:
        obj: The source repaired watertight mesh object.
        plane_co: A point on the splitting plane in world coordinates.
        plane_no: The normal vector of the splitting plane.
        clearance_mm: The total clearance gap between halves in millimeters.
        unit_scale: Scale factor to convert millimeters to Blender Units (default 1e-3: 1 BU = 1 m).

    Returns:
        (upper_obj, lower_obj): Two watertight, closed 2-manifold split solids.
    """
    p_co = Vector(plane_co)
    p_no = Vector(plane_no).normalized()
    half_gap = (clearance_mm * unit_scale) / 2.0

    # Ensure cutter box is 3x larger than the bounding diameter of the object
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    min_c = Vector((min(c[i] for c in corners) for i in range(3)))
    max_c = Vector((max(c[i] for c in corners) for i in range(3)))
    diag = (max_c - min_c).length
    box_size = max(diag * 3.0, 1.0)

    # 1. Prepare Upper Part
    upper_obj = obj
    upper_obj.name = "Part_Upper"

    # 2. Prepare Lower Part
    lower_mesh = obj.data.copy()
    lower_mesh.name = "Part_Lower_mesh"
    lower_obj = bpy.data.objects.new("Part_Lower", lower_mesh)
    lower_obj.matrix_world = obj.matrix_world.copy()
    bpy.context.scene.collection.objects.link(lower_obj)

    # Cut Upper Part: remove negative half-space below +half_gap
    cutter_for_upper = create_cutter_box(
        "Cutter_For_Upper", p_co, p_no, offset=+half_gap, size=box_size, cut_upper=False
    )
    mod_u = upper_obj.modifiers.new("Bool_Cut_LowerHalf", 'BOOLEAN')
    mod_u.operation = 'DIFFERENCE'
    mod_u.solver = 'EXACT'
    mod_u.object = cutter_for_upper
    apply_modifiers_data_api(upper_obj)
    bpy.data.objects.remove(cutter_for_upper, do_unlink=True)

    # Cut Lower Part: remove positive half-space above -half_gap
    cutter_for_lower = create_cutter_box(
        "Cutter_For_Lower", p_co, p_no, offset=-half_gap, size=box_size, cut_upper=True
    )
    mod_l = lower_obj.modifiers.new("Bool_Cut_UpperHalf", 'BOOLEAN')
    mod_l.operation = 'DIFFERENCE'
    mod_l.solver = 'EXACT'
    mod_l.object = cutter_for_lower
    apply_modifiers_data_api(lower_obj)
    bpy.data.objects.remove(cutter_for_lower, do_unlink=True)

    # Verify manifold integrity and positive volume on both resulting halves
    for part in (upper_obj, lower_obj):
        bm = bmesh.new()
        bm.from_mesh(part.data)
        bad_e = sum(1 for e in bm.edges if not e.is_manifold)
        vol = bm.calc_volume(signed=True)
        bm.free()
        assert bad_e == 0, (
            f"Split error: {part.name} has {bad_e} non-manifold edges after planar cut"
        )
        assert vol > 0.0, (
            f"Split error: {part.name} signed volume {vol} is non-positive after planar cut"
        )

    return upper_obj, lower_obj


def add_alignment_dowel_keys(
    upper_obj: bpy.types.Object,
    lower_obj: bpy.types.Object,
    pin_positions: List[Tuple[float, ...]],
    pin_diameter_mm: float = 4.0,
    pin_height_mm: float = 6.0,
    radial_clearance_mm: float = 0.20,
    segments: int = 32,
    unit_scale: float = 1e-3,
    plane_z: float = 0.0,
    clearance_mm: float = 0.3
) -> None:
    """
    Creates cylindrical alignment pins with 45-degree lead-in chamfer tips unioned
    (EXACT boolean UNION) to lower_obj and matching female relief sockets
    (diameter = pin_diameter + 2*radial_clearance, depth = pin_height + 0.5mm)
    subtracted (EXACT boolean DIFFERENCE) from upper_obj.

    Parameters:
        upper_obj: Mating half receiving female sockets.
        lower_obj: Mating half receiving male dowel pins.
        pin_positions: List of (x, y) or (x, y, z) coordinates for pin centers.
        pin_diameter_mm: Outer pin body diameter in mm.
        pin_height_mm: Total male pin height in mm above the lower mating surface.
        radial_clearance_mm: Radial expansion of female socket in mm (e.g. 0.20 mm).
        segments: Radial polygon resolution for dowel cylinders (minimum 32).
        unit_scale: Conversion factor to BU (default 1e-3).
        plane_z: Nominal Z coordinate of split plane.
        clearance_mm: Clearance gap between mating halves in mm.
    """
    pin_radius = (pin_diameter_mm * unit_scale) / 2.0
    pin_height = pin_height_mm * unit_scale
    radial_clearance = radial_clearance_mm * unit_scale
    socket_radius = pin_radius + radial_clearance
    # Female socket has 0.5 mm extra depth relief to prevent pin bottoming out
    socket_depth = pin_height + (0.5 * unit_scale)
    chamfer = min(0.5 * unit_scale, 0.25 * pin_radius)
    embed = 1.0 * unit_scale  # Embed 1.0mm into lower solid for robust manifold union
    overlap = 0.2 * unit_scale  # Overlap 0.2mm outside upper face for clean difference cut

    half_gap = (clearance_mm * unit_scale) / 2.0
    z_lower = plane_z - half_gap
    z_upper = plane_z + half_gap

    # 1. Build combined pins mesh in lower_obj space
    bm_pins = bmesh.new()
    for pos in pin_positions:
        px = pos[0]
        py = pos[1]
        pz = pos[2] if len(pos) > 2 else z_lower

        ring0, ring1, ring2 = [], [], []
        for i in range(segments):
            a = 2.0 * math.pi * i / segments
            ca = math.cos(a)
            sa = math.sin(a)
            v0 = bm_pins.verts.new(
                Vector((px + pin_radius * ca, py + pin_radius * sa, pz - embed))
            )
            v1 = bm_pins.verts.new(
                Vector((px + pin_radius * ca, py + pin_radius * sa, pz + pin_height - chamfer))
            )
            v2 = bm_pins.verts.new(
                Vector((px + (pin_radius - chamfer) * ca, py + (pin_radius - chamfer) * sa, pz + pin_height))
            )
            ring0.append(v0)
            ring1.append(v1)
            ring2.append(v2)

        for i in range(segments):
            nxt = (i + 1) % segments
            # Cylindrical body
            bm_pins.faces.new((ring0[i], ring0[nxt], ring1[nxt], ring1[i]))
            # 45-degree lead-in chamfer cone
            bm_pins.faces.new((ring1[i], ring1[nxt], ring2[nxt], ring2[i]))

        # Base and top planar caps
        bm_pins.faces.new(list(reversed(ring0)))
        bm_pins.faces.new(ring2)

    bmesh.ops.recalc_face_normals(bm_pins, faces=list(bm_pins.faces))
    pins_me = bpy.data.meshes.new("Dowel_Pins_Mesh")
    bm_pins.to_mesh(pins_me)
    bm_pins.free()
    pins_me.update()

    pins_obj = bpy.data.objects.new("Dowel_Pins_Union", pins_me)
    bpy.context.scene.collection.objects.link(pins_obj)

    # EXACT Boolean UNION into lower_obj
    mod_u = lower_obj.modifiers.new("Bool_Union_Pins", 'BOOLEAN')
    mod_u.operation = 'UNION'
    mod_u.solver = 'EXACT'
    mod_u.object = pins_obj
    apply_modifiers_data_api(lower_obj)
    bpy.data.objects.remove(pins_obj, do_unlink=True)

    # 2. Build combined female sockets cutter mesh in upper_obj space
    bm_sockets = bmesh.new()
    for pos in pin_positions:
        px = pos[0]
        py = pos[1]
        pz = pos[2] if len(pos) > 2 else z_upper
        bmesh.ops.create_cone(
            bm_sockets,
            cap_ends=True,
            cap_tris=False,
            segments=segments,
            radius1=socket_radius,
            radius2=socket_radius,
            depth=socket_depth + overlap,
            matrix=Matrix.Translation(
                Vector((px, py, pz + (socket_depth - overlap) / 2.0))
            )
        )

    bmesh.ops.recalc_face_normals(bm_sockets, faces=list(bm_sockets.faces))
    sockets_me = bpy.data.meshes.new("Dowel_Sockets_Mesh")
    bm_sockets.to_mesh(sockets_me)
    bm_sockets.free()
    sockets_me.update()

    sockets_obj = bpy.data.objects.new("Dowel_Sockets_Cutter", sockets_me)
    bpy.context.scene.collection.objects.link(sockets_obj)

    # EXACT Boolean DIFFERENCE from upper_obj
    mod_d = upper_obj.modifiers.new("Bool_Diff_Sockets", 'BOOLEAN')
    mod_d.operation = 'DIFFERENCE'
    mod_d.solver = 'EXACT'
    mod_d.object = sockets_obj
    apply_modifiers_data_api(upper_obj)
    bpy.data.objects.remove(sockets_obj, do_unlink=True)

    # 3. Verify manifoldness on both parts after dowel operations
    for part in (upper_obj, lower_obj):
        bm = bmesh.new()
        bm.from_mesh(part.data)
        bad_e = sum(1 for e in bm.edges if not e.is_manifold)
        vol = bm.calc_volume(signed=True)
        bm.free()
        assert bad_e == 0, (
            f"Dowel key error: {part.name} has {bad_e} non-manifold edges after dowel operations"
        )
        assert vol > 0.0, (
            f"Dowel key error: {part.name} signed volume {vol} is non-positive after dowel operations"
        )


def measure_intersection_volume(obj_a: bpy.types.Object, obj_b: bpy.types.Object) -> float:
    """
    Computes exact volumetric intersection between two meshes using EXACT boolean INTERSECT.
    Returns intersection volume in m^3 (BU^3).
    """
    temp_me = obj_a.data.copy()
    temp_obj = bpy.data.objects.new("Temp_Intersect", temp_me)
    temp_obj.matrix_world = obj_a.matrix_world.copy()
    bpy.context.scene.collection.objects.link(temp_obj)

    mod = temp_obj.modifiers.new("Bool_Intersect", 'BOOLEAN')
    mod.operation = 'INTERSECT'
    mod.solver = 'EXACT'
    mod.object = obj_b

    apply_modifiers_data_api(temp_obj)

    bm = bmesh.new()
    bm.from_mesh(temp_obj.data)
    vol = bm.calc_volume(signed=True)
    bm.free()

    mesh_to_free = temp_obj.data
    bpy.data.objects.remove(temp_obj, do_unlink=True)
    if mesh_to_free.users == 0:
        bpy.data.meshes.remove(mesh_to_free)

    return abs(vol)


def create_organic_test_mesh(name: str = "OrganicScaffold_Coupon", radius: float = 0.045) -> bpy.types.Object:
    """
    Creates a non-trivial organic-like closed test mesh (deformed UV sphere with harmonic
    surface ripples and subdivision) representing a local frozen scaffold.
    Span: ~90 mm diameter.
    """
    # Clean default scene objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=36, v_segments=24, radius=radius)

    for v in bm.verts:
        x, y, z = v.co
        disp = 1.0 + 0.18 * math.sin(4.0 * x / radius) * math.cos(3.0 * y / radius) + 0.12 * math.sin(5.0 * z / radius)
        v.co *= disp

    mesh = bpy.data.meshes.new(name + "_mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    # Subdivide smoothly to create continuous organic curvature
    sub = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    sub.levels = 1
    sub.render_levels = 1
    apply_modifiers_data_api(obj)

    # Assign a dummy vendor material to verify material stripping
    mat = bpy.data.materials.new("Vendor_Tripo_Material")
    obj.data.materials.append(mat)

    return obj


def main() -> None:
    print("Executing bp_organic_scaffold_splitter.py in Blender 5.2 LTS...")

    # 1. Create organic test scaffold with vendor material
    obj = create_organic_test_mesh("Organic_Figurine_Scaffold", radius=0.045)
    print(f"Created organic test scaffold: {obj.name} with {len(obj.data.vertices)} vertices.")

    # 2. Prepare frozen organic scaffold
    stats = prepare_frozen_organic_scaffold(obj)
    print(f"Scaffold preparation verified: {stats}")

    # 3. Split organic mesh with 0.3mm clearance at Z = 0.0
    upper_obj, lower_obj = split_organic_mesh_with_clearance(
        obj,
        plane_co=(0.0, 0.0, 0.0),
        plane_no=(0.0, 0.0, 1.0),
        clearance_mm=0.3
    )
    print(f"Split complete: {upper_obj.name} ({len(upper_obj.data.polygons)} faces), {lower_obj.name} ({len(lower_obj.data.polygons)} faces)")

    # 4. Add 2 alignment dowel keys with 45-deg lead-in chamfer tips and female sockets
    pin_positions = [(-0.015, 0.0), (0.015, 0.0)]
    add_alignment_dowel_keys(
        upper_obj,
        lower_obj,
        pin_positions=pin_positions,
        pin_diameter_mm=4.0,
        pin_height_mm=6.0,
        radial_clearance_mm=0.20,
        segments=32,
        plane_z=0.0,
        clearance_mm=0.3
    )
    print("Dowel keys added and verified.")

    # 5. Volumetric collision audit
    intersect_vol = measure_intersection_volume(upper_obj, lower_obj)
    print(f"Measured intersection volume between Upper and Lower: {intersect_vol:.12f} m^3")
    assert intersect_vol < 1e-10, (
        f"DFM Collision Failure: Intersection volume {intersect_vol} exceeds threshold 1e-10 m^3"
    )

    # 6. Authoritative runtime sentinel emit
    rt.emit_ok(
        "bp_organic_scaffold_splitter",
        parts_created=2,
        upper_manifold=True,
        lower_manifold=True,
        clearance_mm=0.3,
        dowel_keys=len(pin_positions),
        intersection_volume_m3=intersect_vol
    )
    print("bp_organic_scaffold_splitter completed successfully.")


if __name__ == "__main__":
    main()
