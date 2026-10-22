"""
bp_cad_step_roundtrip.py — CAD STEP Round-Trip, Parametric Batch Edit & DFM Zero-Collision Builder.

Features:
- ISO-10303-21 Fusion 360 Vietnamese Unicode string decoder (\\X2\\...\\X0\\ and \\X\\..).
- Non-destructive hierarchical assembly organizer (00_CAD_Reference, 01_Assembly_Main -> sub-collections).
- Parametric batch editing for named hardware components (e.g. Ốc_Lục_Giác* resizing).
- DFM zero-collision ($V_{intersect} == 0.0 mm^3$) and coplanar butt-weld ($delta <= 10^-4 m$) geometric auditor.
- Optional build123d / OpenCASCADE (OCP) XCAF & TopoDS_Compound helpers with pure-Python/bpy fallback.

Target: Blender 5.2 LTS.
"""

from __future__ import annotations
import os
import sys
import re
import fnmatch
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import bpy
import bmesh
from mathutils import Matrix, Vector

# Ensure scripts directory is available for agent_runtime import
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
import agent_runtime as rt


# --- OpenCASCADE / build123d Inspection & Optional Helpers ------------------

HAS_BUILD123D = importlib.util.find_spec("build123d") is not None

if HAS_BUILD123D:
    import build123d as bd
    from OCP.TopoDS import TopoDS_Compound
    from OCP.BRep import BRep_Builder
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.GProp import GProp_GProps
    from OCP.BRepGProp import BRepGProp
    from OCP.BRepMesh import BRepMesh_IncrementalMesh

    def make_multibody_compound(label: str, solids: list) -> bd.Part:
        """Pack multiple solids into a single TopoDS_Compound wrapped in a Part."""
        builder = BRep_Builder()
        comp = TopoDS_Compound()
        builder.MakeCompound(comp)
        for s in solids:
            builder.Add(comp, s.wrapped if hasattr(s, "wrapped") else s)
        p = bd.Part(comp)
        p.label = label
        return p

    def export_multibody_step(compound: Any, filepath: str) -> None:
        """Export multi-body compound directly to STEP format."""
        bd.export_step(compound, filepath)

    def check_cad_solid_intersection(solid_a: Any, solid_b: Any) -> float:
        """Return intersection volume in mm^3 using OpenCASCADE BRepAlgoAPI_Common."""
        common = BRepAlgoAPI_Common(solid_a.wrapped, solid_b.wrapped)
        common.Build()
        if common.IsDone():
            props = GProp_GProps()
            BRepGProp.VolumeProperties_s(common.Shape(), props)
            return float(props.Mass())
        return 0.0
else:
    def make_multibody_compound(label: str, solids: list) -> Any:
        """Fallback placeholder when build123d is not available in embedded Python."""
        return {"label": label, "solids": solids, "type": "compound_fallback"}

    def export_multibody_step(compound: Any, filepath: str) -> None:
        """Fallback placeholder when build123d is not available in embedded Python."""
        raise NotImplementedError("STEP export requires build123d/OCP installed in Python environment.")

    def check_cad_solid_intersection(solid_a: Any, solid_b: Any) -> float:
        """Fallback placeholder when build123d is not available in embedded Python."""
        return 0.0


# --- 1. ISO-10303-21 Vietnamese Unicode String Decoder -----------------------

def decode_step_string(s: str) -> str:
    """
    Decodes ISO-10303-21 Fusion 360 / SolidWorks hexadecimal Unicode strings.
    Handles \\X2\\<HEX4>...\\X0\\ sequences (UTF-16BE) and \\X\\<HEX2> (Latin-1).
    Example:
      '\\X2\\004D1EB70074\\X0\\_B\\X2\\00E0\\X0\\n_Plywood' -> 'Mặt_Bàn_Plywood'
      '\\X2\\1ED00063\\X0\\_L\\X2\\1EE5\\X0\\c_Gi\\X2\\00E1\\X0\\c_M8' -> 'Ốc_Lục_Giác_M8'
    """
    if not s:
        return ""

    def replace_x2(m: re.Match) -> str:
        hex_str = m.group(1)
        res = ""
        for i in range(0, len(hex_str), 4):
            chunk = hex_str[i:i+4]
            if len(chunk) == 4:
                res += chr(int(chunk, 16))
        return res

    def replace_x(m: re.Match) -> str:
        return chr(int(m.group(1), 16))

    # Match \X2\<hex>\X0\ where backslashes may be escaped in string representations
    decoded = re.sub(r'\\X2\\([0-9A-Fa-f]+)\\X0\\', replace_x2, s)
    decoded = re.sub(r'\\X\\([0-9A-Fa-f]{2})', replace_x, decoded)
    return decoded.strip()


# --- 2. Hierarchical CAD Assembly Builder ------------------------------------

def build_hierarchical_cad_assembly(
    manifest_items: List[Any],
    rules_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Builds structured Blender collections representing a professional CAD assembly tree:
      Scene Collection
      ├── 00_CAD_Reference (Locked reference models)
      └── 01_Assembly_Main
          ├── Comp_Primary_Structure (Heavy frames, structural columns)
          ├── Comp_Framing_Profiles (Extrusions, T-slot rails, stretchers)
          ├── Comp_Hardware_Fasteners (Bolts, screws, washers, nuts)
          └── Comp_Panels (Tabletop panels, sheet metal plates, CNC plywood)
    Organizes objects and maintains 1:1 rigid CAD geometry without re-extrusion.
    """
    scene = bpy.context.scene

    # Ensure root collections
    coll_ref = bpy.data.collections.get("00_CAD_Reference")
    if not coll_ref:
        coll_ref = bpy.data.collections.new("00_CAD_Reference")
        scene.collection.children.link(coll_ref)

    coll_main = bpy.data.collections.get("01_Assembly_Main")
    if not coll_main:
        coll_main = bpy.data.collections.new("01_Assembly_Main")
        scene.collection.children.link(coll_main)

    # Sub-collections
    sub_colls = {}
    sub_names = [
        "Comp_Primary_Structure",
        "Comp_Framing_Profiles",
        "Comp_Hardware_Fasteners",
        "Comp_Panels"
    ]
    for sn in sub_names:
        c = bpy.data.collections.get(sn)
        if not c:
            c = bpy.data.collections.new(sn)
            coll_main.children.link(c)
        sub_colls[sn] = c

    # Link/sort manifest items
    linked_objects = []
    for item in manifest_items:
        obj = None
        if isinstance(item, bpy.types.Object):
            obj = item
        elif isinstance(item, dict) and "object" in item:
            obj = item["object"]
        elif isinstance(item, str):
            obj = bpy.data.objects.get(item)

        if not obj or obj.type != 'MESH':
            continue

        clean_name = obj.name.lower()

        # Destination collection routing
        dest_coll_name = "Comp_Primary_Structure"
        if any(k in clean_name for k in ["mat_ban", "tabletop", "plywood", "panel", "plate"]):
            dest_coll_name = "Comp_Panels"
        elif any(k in clean_name for k in ["nhom", "profile", "rail", "t-slot", "3030", "leg", "tube", "stretcher"]):
            dest_coll_name = "Comp_Framing_Profiles"
        elif any(k in clean_name for k in ["oc", "luc_giac", "bolt", "screw", "fastener", "washer", "nut", "m8", "m10"]):
            dest_coll_name = "Comp_Hardware_Fasteners"

        dest_coll = sub_colls[dest_coll_name]

        # Link to target collection and unlink from root collection if present
        if dest_coll not in obj.users_collection:
            dest_coll.objects.link(obj)
        for cur_coll in list(obj.users_collection):
            if cur_coll != dest_coll:
                cur_coll.objects.unlink(obj)

        linked_objects.append(obj)

    return {
        "root_ref": coll_ref,
        "root_main": coll_main,
        "sub_collections": sub_colls,
        "objects": linked_objects
    }


# --- 3. Parametric Batch Edit By Pattern -------------------------------------

def batch_edit_parts_by_pattern(
    name_pattern: str,
    scale_xyz: Tuple[float, float, float] = (1.25, 1.25, 1.0),
    apply_scale: bool = True
) -> List[str]:
    """
    Finds all mesh objects matching `name_pattern` (e.g. 'Ốc_Lục_Giác*'),
    scales them parametrically in batch without disturbing locked structural parts,
    and applies scale to underlying mesh vertices when apply_scale=True.
    Returns the list of modified object names.
    """
    modified_names = []
    scale_mat = Matrix.Diagonal((scale_xyz[0], scale_xyz[1], scale_xyz[2], 1.0))

    for obj in bpy.data.objects:
        if obj.type == 'MESH' and fnmatch.fnmatch(obj.name, name_pattern):
            if apply_scale:
                if len(obj.data.vertices) > 0:
                    xs = [v.co.x for v in obj.data.vertices]
                    ys = [v.co.y for v in obj.data.vertices]
                    zs = [v.co.z for v in obj.data.vertices]
                    local_center = Vector((
                        0.5 * (min(xs) + max(xs)),
                        0.5 * (min(ys) + max(ys)),
                        0.5 * (min(zs) + max(zs))
                    ))
                    pivot_mat = Matrix.Translation(local_center) @ scale_mat @ Matrix.Translation(-local_center)
                    obj.data.transform(pivot_mat)
                else:
                    obj.data.transform(scale_mat)
                obj.data.update()
                obj.scale = Vector((1.0, 1.0, 1.0))
            else:
                obj.scale.x *= scale_xyz[0]
                obj.scale.y *= scale_xyz[1]
                obj.scale.z *= scale_xyz[2]
            modified_names.append(obj.name)

    return modified_names


# --- 4. DFM Zero-Collision & Butt-Weld Auditor -------------------------------

def get_world_aabb(obj: bpy.types.Object) -> Tuple[Vector, Vector]:
    """Calculate world-space axis-aligned bounding box for an object."""
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    min_v = Vector((min(c[i] for c in corners) for i in range(3)))
    max_v = Vector((max(c[i] for c in corners) for i in range(3)))
    return min_v, max_v


def audit_dfm_zero_collision_and_butt_weld(
    objects: List[bpy.types.Object],
    clearance_mm: float = 0.2
) -> Dict[str, Any]:
    """
    Checks pairwise BMesh & world-space geometry for:
    1. Zero-collision rule: intersection volume V_intersect == 0.000 mm^3.
    2. Coplanar butt-weld contacts: tangential plane contact delta <= 1e-4 m (0.1 mm).
    """
    coplanar_count = 0
    max_vol_mm3 = 0.0
    collision_pairs = []
    butt_weld_pairs = []
    checked_pairs = 0

    eps_tangential = 1e-4  # 0.1 mm tangential tolerance
    mesh_objects = [o for o in objects if o.type == 'MESH']

    for i in range(len(mesh_objects)):
        for j in range(i + 1, len(mesh_objects)):
            obj_a = mesh_objects[i]
            obj_b = mesh_objects[j]
            checked_pairs += 1

            a_min, a_max = get_world_aabb(obj_a)
            b_min, b_max = get_world_aabb(obj_b)

            dx = min(a_max.x, b_max.x) - max(a_min.x, b_min.x)
            dy = min(a_max.y, b_max.y) - max(a_min.y, b_min.y)
            dz = min(a_max.z, b_max.z) - max(a_min.z, b_min.z)

            # Check for coplanar butt-weld interface (tangential contact on one axis, overlap on orthogonal plane)
            is_butt_weld = False
            # Z-axis flush contact
            if dx > eps_tangential and dy > eps_tangential:
                if (abs(a_min.z - b_max.z) <= eps_tangential or abs(b_min.z - a_max.z) <= eps_tangential) and dz <= eps_tangential:
                    is_butt_weld = True
            # X-axis flush contact
            if dy > eps_tangential and dz > eps_tangential:
                if (abs(a_min.x - b_max.x) <= eps_tangential or abs(b_min.x - a_max.x) <= eps_tangential) and dx <= eps_tangential:
                    is_butt_weld = True
            # Y-axis flush contact
            if dx > eps_tangential and dz > eps_tangential:
                if (abs(a_min.y - b_max.y) <= eps_tangential or abs(b_min.y - a_max.y) <= eps_tangential) and dy <= eps_tangential:
                    is_butt_weld = True

            vol_mm3 = 0.0
            # If 3D bounding boxes overlap significantly, measure exact boolean volume
            if dx > eps_tangential and dy > eps_tangential and dz > eps_tangential:
                mod = obj_a.modifiers.new(name="DFM_Collision_Check", type='BOOLEAN')
                mod.object = obj_b
                mod.operation = 'INTERSECT'
                mod.solver = 'EXACT'

                dg = bpy.context.evaluated_depsgraph_get()
                eval_obj = obj_a.evaluated_get(dg)
                bm_eval = bmesh.new()
                bm_eval.from_mesh(eval_obj.data)
                vol_m3 = abs(bm_eval.calc_volume())
                vol_mm3 = vol_m3 * 1e9  # m^3 to mm^3
                bm_eval.free()
                obj_a.modifiers.remove(mod)

            if vol_mm3 > 1e-4:
                collision_pairs.append({
                    "pair": (obj_a.name, obj_b.name),
                    "intersection_vol_mm3": round(vol_mm3, 4)
                })
                if vol_mm3 > max_vol_mm3:
                    max_vol_mm3 = vol_mm3
            elif is_butt_weld:
                coplanar_count += 1
                butt_weld_pairs.append((obj_a.name, obj_b.name))

    return {
        "max_intersection_vol_mm3": round(max_vol_mm3, 6),
        "coplanar_contacts": coplanar_count,
        "checked_pairs": checked_pairs,
        "collision_pairs": collision_pairs,
        "butt_weld_pairs": butt_weld_pairs
    }


# --- Geometry Generation Helpers for Testing ---------------------------------

def create_tabletop_panel(
    name: str = "Mặt_Bàn_Plywood",
    length_m: float = 1.2,
    width_m: float = 0.8,
    thickness_m: float = 0.036,
    z_bottom_m: float = 0.720
) -> bpy.types.Object:
    """Create a tabletop panel mesh centered in X/Y with bottom face at z_bottom_m."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Diagonal((length_m, width_m, thickness_m, 1.0))
    )
    bmesh.ops.translate(
        bm,
        vec=Vector((0.0, 0.0, z_bottom_m + (thickness_m / 2.0))),
        verts=bm.verts[:]
    )
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return obj


def create_aluminum_3030_leg(
    name: str,
    x_pos_m: float,
    y_pos_m: float,
    profile_size_m: float = 0.030,
    height_m: float = 0.720
) -> bpy.types.Object:
    """Create a 3030 aluminum profile leg terminating flush at Z=height_m (butt-weld)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    bm = bmesh.new()
    bmesh.ops.create_cube(
        bm,
        size=1.0,
        matrix=Matrix.Diagonal((profile_size_m, profile_size_m, height_m, 1.0))
    )
    bmesh.ops.translate(
        bm,
        vec=Vector((x_pos_m, y_pos_m, height_m / 2.0)),
        verts=bm.verts[:]
    )
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return obj


def create_fastener_bolt(
    name: str,
    location: Vector,
    thread_dia_m: float = 0.008,
    shank_len_m: float = 0.025,
    head_dia_m: float = 0.013,
    head_len_m: float = 0.006
) -> bpy.types.Object:
    """Create an ISO metric socket head cap screw fastener (M8)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    bm = bmesh.new()
    # Hexagonal head (6 segments)
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=6,
        radius1=head_dia_m / 2.0,
        radius2=head_dia_m / 2.0,
        depth=head_len_m,
        matrix=Matrix.Translation(Vector((0.0, 0.0, head_len_m / 2.0)))
    )
    # Cylindrical shank (16 segments)
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        segments=16,
        radius1=thread_dia_m / 2.0,
        radius2=thread_dia_m / 2.0,
        depth=shank_len_m,
        matrix=Matrix.Translation(Vector((0.0, 0.0, -shank_len_m / 2.0)))
    )
    # Translate entire bolt to specified location
    bmesh.ops.translate(bm, vec=location, verts=bm.verts[:])
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return obj


# --- Execution Self-Test ----------------------------------------------------

def main() -> None:
    # 1. Reset scene to empty factory environment
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = 'MILLIMETERS'

    # 2. Test ISO-10303-21 Vietnamese Unicode String Decoder
    test_str_1 = "\\X2\\004D1EB70074\\X0\\_B\\X2\\00E0\\X0\\n_Plywood"
    test_str_2 = "\\X2\\1ED00063\\X0\\_L\\X2\\1EE5\\X0\\c_Gi\\X2\\00E1\\X0\\c_M8"

    decoded_tabletop = decode_step_string(test_str_1)
    decoded_fastener = decode_step_string(test_str_2)

    assert decoded_tabletop == "Mặt_Bàn_Plywood", f"Decoder mismatch: {decoded_tabletop} != 'Mặt_Bàn_Plywood'"
    assert decoded_fastener == "Ốc_Lục_Giác_M8", f"Decoder mismatch: {decoded_fastener} != 'Ốc_Lục_Giác_M8'"

    # 3. Create Sample Assembly:
    # - 1 Tabletop panel (Mặt_Bàn_Plywood, underside at Z=0.720m)
    # - 2 Aluminum 3030 legs butt-welded flush at underside of tabletop (Z=0.720m, 0 overlap volume)
    # - 4 Ốc_Lục_Giác_M8 bolts
    tabletop = create_tabletop_panel(
        name=decoded_tabletop,
        length_m=1.2,
        width_m=0.8,
        thickness_m=0.036,
        z_bottom_m=0.720
    )
    leg_01 = create_aluminum_3030_leg("Khung_Nhom_3030_Leg_01", x_pos_m=-0.4, y_pos_m=0.0, height_m=0.720)
    leg_02 = create_aluminum_3030_leg("Khung_Nhom_3030_Leg_02", x_pos_m=0.4, y_pos_m=0.0, height_m=0.720)

    bolt_positions = [
        Vector((-0.4, -0.015, 0.720)),
        Vector((-0.4, 0.015, 0.720)),
        Vector((0.4, -0.015, 0.720)),
        Vector((0.4, 0.015, 0.720)),
    ]
    fasteners = []
    for idx, pos in enumerate(bolt_positions):
        bolt_name = f"{decoded_fastener}_{idx+1:02d}"
        fasteners.append(create_fastener_bolt(bolt_name, location=pos))

    all_parts = [tabletop, leg_01, leg_02] + fasteners

    # 4. Build Hierarchical CAD Assembly
    assembly_meta = build_hierarchical_cad_assembly(all_parts)
    assert len(assembly_meta["sub_collections"]["Comp_Panels"].objects) == 1
    assert len(assembly_meta["sub_collections"]["Comp_Framing_Profiles"].objects) == 2
    assert len(assembly_meta["sub_collections"]["Comp_Hardware_Fasteners"].objects) == 4

    # 5. Batch Edit Named Hardware Fasteners (e.g. M8 -> M10 resize by 1.25x in XY)
    edited_parts = batch_edit_parts_by_pattern("Ốc_Lục_Giác*", scale_xyz=(1.25, 1.25, 1.0), apply_scale=True)
    assert len(edited_parts) == 4, f"Expected 4 edited fasteners, got {len(edited_parts)}"

    # 6. Run DFM Zero-Collision & Butt-Weld Audit on structural frame
    dfm_result = audit_dfm_zero_collision_and_butt_weld([tabletop, leg_01, leg_02])
    assert dfm_result["max_intersection_vol_mm3"] == 0.0, f"Collision detected: {dfm_result['max_intersection_vol_mm3']} mm^3"
    assert dfm_result["coplanar_contacts"] == 2, f"Expected 2 coplanar contacts, got {dfm_result['coplanar_contacts']}"

    # 7. Authoritative Sentinel Emission via agent_runtime
    rt.emit_ok(
        "bp_cad_step_roundtrip",
        decoded_name=decoded_tabletop,
        fastener_edited_count=len(edited_parts),
        max_intersection_vol_mm3=dfm_result["max_intersection_vol_mm3"],
        coplanar_contacts=dfm_result["coplanar_contacts"]
    )


if __name__ == "__main__":
    main()
