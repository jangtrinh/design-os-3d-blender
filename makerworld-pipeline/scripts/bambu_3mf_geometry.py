"""Geometry resolution for Bambu-shaped .3mf files: component/inline mesh
resolution and the 3MF core-spec 12-float row-vector transform.

Math ported verbatim from the pinned reference implementation
(.../scratchpad/reference-per-plate-bbox.py, per phase-04 step 3) -- not
re-derived. Kept separate from bambu_3mf_reader.py to stay under the
project's 200-line-per-file guidance.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

NS = {
    "m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
    "p": "http://schemas.microsoft.com/3dmanufacturing/production/2015/06",
}
IDENT_12 = "1 0 0 0 1 0 0 0 1 0 0 0"
MODEL_PATH = "3D/3dmodel.model"


def apply_transform_12(vertex, matrix):
    """3MF core-spec row-vector transform: 12 floats, verbatim port of
    reference-per-plate-bbox.py::apply12."""
    x, y, z = vertex
    m = matrix
    return (
        m[0] * x + m[3] * y + m[6] * z + m[9],
        m[1] * x + m[4] * y + m[7] * z + m[10],
        m[2] * x + m[5] * y + m[8] * z + m[11],
    )


def parse_transform(attr_value):
    if attr_value is None:
        return None
    parts = attr_value.split()
    if len(parts) != 12:
        return None
    try:
        return [float(p) for p in parts]
    except ValueError:
        return None


def mesh_vertices(object_elem):
    return [
        (float(v.attrib["x"]), float(v.attrib["y"]), float(v.attrib["z"]))
        for v in object_elem.findall(".//m:vertex", NS)
    ]


def model_objects_by_id(root):
    return {obj.attrib.get("id"): obj for obj in root.findall(".//m:object", NS)}


def read_model_xml(zf, path=MODEL_PATH):
    """Parse a .model XML member. Raises ET.ParseError / KeyError to the
    caller (checks module decides how to report that)."""
    return ET.fromstring(zf.read(path))


def resolve_geometry(zf, root=None):
    """For every <object> in the root 3dmodel.model, resolve its local
    (unplaced) vertices either through a <components><component p:path>
    reference into 3D/Objects/*.model, or from an inline <mesh> on the
    object itself (the "AND inline meshes" half of check 3).

    Returns {object_id: {"kind": "component"|"inline"|"unresolved",
                          "vertices": [...], "external_path": str|None}}.
    """
    if root is None:
        root = read_model_xml(zf)
    names = set(zf.namelist())
    result = {}
    for obj in root.findall(".//m:object", NS):
        oid = obj.attrib.get("id")
        comp = obj.find("m:components/m:component", NS)
        if comp is not None:
            result[oid] = _resolve_component(zf, comp, names)
        else:
            verts = mesh_vertices(obj)
            if verts:
                result[oid] = {"kind": "inline", "vertices": verts, "external_path": None}
            else:
                result[oid] = {"kind": "unresolved", "vertices": [], "external_path": None}
    return result


def _resolve_component(zf, comp, names):
    path_attr = comp.attrib.get(f"{{{NS['p']}}}path")
    target_id = comp.attrib.get("objectid")
    ctrans = parse_transform(comp.attrib.get("transform", IDENT_12)) or [
        float(v) for v in IDENT_12.split()
    ]
    internal_path = (path_attr or "").lstrip("/")
    if not path_attr or internal_path not in names:
        return {"kind": "unresolved", "vertices": [], "external_path": path_attr}
    try:
        ext_obj = model_objects_by_id(read_model_xml(zf, internal_path)).get(target_id)
    except ET.ParseError:
        ext_obj = None
    if ext_obj is None:
        return {"kind": "unresolved", "vertices": [], "external_path": path_attr}
    local_verts = mesh_vertices(ext_obj)
    return {
        "kind": "component",
        "vertices": [apply_transform_12(v, ctrans) for v in local_verts],
        "external_path": path_attr,
    }


def read_build_items(root):
    """Returns an ORDERED LIST of build items (never a dict keyed by
    objectid -- Bambu Studio writes one <build><item> per placed instance,
    and N items with the same objectid is the common "duplicated part"
    plate edit, not a collision): [{"objectid": str, "instance_id": int,
    "transform": [12 floats]|None, "printable": bool}].

    instance_id is the 0-indexed occurrence count of this objectid among
    <build><item> elements in document order. This matches Bambu Studio's
    own convention for the <model_instance><metadata key="instance_id">
    values written to Metadata/model_settings.config: the Nth <item> for a
    given objectid is instance_id N-1 (verified against the real-file
    oracle, where every object has exactly one item and instance_id "0")."""
    items = []
    seen_counts = {}
    for item in root.findall(".//m:build/m:item", NS):
        oid = item.attrib.get("objectid")
        instance_id = seen_counts.get(oid, 0)
        seen_counts[oid] = instance_id + 1
        items.append({
            "objectid": oid,
            "instance_id": instance_id,
            "transform": parse_transform(item.attrib.get("transform")),
            "printable": item.attrib.get("printable", "1") != "0",
        })
    return items


def world_vertices_by_instance(local_geometry, build_items):
    """Apply each build item's OWN transform to its object's resolved
    local vertices. Returns {(objectid, instance_id): [world vertices]}.
    Keeping instances distinct (rather than collapsing all items of one
    objectid into a single dict entry) is what lets N duplicated build
    items of one object each contribute their own placement to a plate's
    bounding box. Items with no resolvable geometry or malformed
    transform are omitted."""
    world = {}
    for item in build_items:
        geom_entry = local_geometry.get(item["objectid"])
        if geom_entry is None or item["transform"] is None:
            continue
        world[(item["objectid"], item["instance_id"])] = [
            apply_transform_12(v, item["transform"]) for v in geom_entry["vertices"]
        ]
    return world
