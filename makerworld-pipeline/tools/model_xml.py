"""3MF `.model` XML emitters (string-templated, not ElementTree).

String templating is used instead of ElementTree because the exact
attribute names/prefixes (`p:path`, `p:uuid`) must match Bambu Studio's
observed output verbatim; ElementTree's default-namespace prefix mangling
would fight that. All interpolated values are generator-controlled
(filenames from repo STLs, floats, fixed strings) -- never user text -- so
no HTML/XML injection risk exists here.

Layout mirrors the real Bambu 3MF (see plan phase-03 "Key insights"):
  <object id="wrapper"><components><component p:path=".../Objects/X.model"
    objectid="mesh" transform="identity"/></components></object>
  <build><item objectid="wrapper" transform="world placement" printable="1"/></build>
"""
from __future__ import annotations

from xml.sax.saxutils import escape

CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
SLIC3RPE_NS = "http://schemas.slic3r.org/3mf/2017/06"
PROD_NS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
IDENTITY_TRANSFORM = "1 0 0 0 1 0 0 0 1 0 0 0"


def format_floats(values: list[float]) -> str:
    return " ".join(_format_float(v) for v in values)


def _format_float(v: float) -> str:
    # Trim trailing zeros but keep integers readable (matches typical
    # slicer float formatting closely enough for structural fidelity;
    # exact formatting is never asserted by the structural diff test).
    text = f"{v:.9g}"
    return text


def build_object_model_xml(mesh_id: int, vertices: list[tuple[float, float, float]], triangles: list[tuple[int, int, int]]) -> str:
    """Render one `/3D/Objects/<name>_<mesh_id>.model` mesh-only file."""
    vertex_lines = "\n     ".join(
        f'<vertex x="{_format_float(x)}" y="{_format_float(y)}" z="{_format_float(z)}"/>'
        for x, y, z in vertices
    )
    triangle_lines = "\n     ".join(
        f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<model unit="millimeter" xml:lang="en-US" xmlns="{CORE_NS}" '
        f'xmlns:slic3rpe="{SLIC3RPE_NS}" xmlns:p="{PROD_NS}" requiredextensions="p">\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        " <resources>\n"
        f'  <object id="{mesh_id}" type="model">\n'
        "   <mesh>\n"
        "    <vertices>\n"
        f"     {vertex_lines}\n"
        "    </vertices>\n"
        "    <triangles>\n"
        f"     {triangle_lines}\n"
        "    </triangles>\n"
        "   </mesh>\n"
        "  </object>\n"
        " </resources>\n"
        "</model>"
    )


def build_root_model_xml(
    root_metadata: dict[str, str],
    objects: list[dict],
    build_uuid: str,
) -> str:
    """Render the root `/3D/3dmodel.model`.

    Each entry in `objects` is:
      {wrapper_id, wrapper_uuid, mesh_id, object_path,
       item_uuid, item_transform: [12 floats]}
    """
    metadata_lines = "\n ".join(
        f'<metadata name="{escape(key)}">{escape(value)}</metadata>'
        for key, value in root_metadata.items()
    )

    object_blocks = []
    for obj in objects:
        object_blocks.append(
            f'  <object id="{obj["wrapper_id"]}" p:uuid="{obj["wrapper_uuid"]}" type="model">\n'
            "   <components>\n"
            f'    <component p:path="{obj["object_path"]}" objectid="{obj["mesh_id"]}" '
            f'transform="{IDENTITY_TRANSFORM}"/>\n'
            "   </components>\n"
            "  </object>"
        )
    resources_xml = "\n".join(object_blocks)

    item_blocks = []
    for obj in objects:
        transform = format_floats(obj["item_transform"])
        item_blocks.append(
            f'  <item objectid="{obj["wrapper_id"]}" p:uuid="{obj["item_uuid"]}" '
            f'transform="{transform}" printable="1"/>'
        )
    build_xml = "\n".join(item_blocks)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<model unit="millimeter" xml:lang="en-US" xmlns="{CORE_NS}" '
        f'xmlns:slic3rpe="{SLIC3RPE_NS}" xmlns:p="{PROD_NS}" requiredextensions="p">\n'
        f" {metadata_lines}\n"
        " <resources>\n"
        f"{resources_xml}\n"
        " </resources>\n"
        f' <build p:uuid="{build_uuid}">\n'
        f"{build_xml}\n"
        " </build>\n"
        "</model>"
    )


def build_model_rels_xml(object_paths: list[str]) -> str:
    """Render `/3D/_rels/3dmodel.model.rels` -- one relationship per object model."""
    rel_type = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
    lines = "\n ".join(
        f'<Relationship Target="{path}" Id="rel-{i + 1}" Type="{rel_type}"/>'
        for i, path in enumerate(object_paths)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        f" {lines}\n"
        "</Relationships>"
    )
