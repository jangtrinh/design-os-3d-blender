#!/usr/bin/env python3
"""
design-os-3d-blender-mcp: Model Context Protocol Server
Evidence-first native Blender modeling and verification for Blender 5.2 LTS.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional

# Protocol SDK import with v1 / v2 resilience
try:
    from mcp.server.mcpserver import MCPServer
    ServerClass = MCPServer
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
        ServerClass = FastMCP
    except ImportError:
        class ServerClass:  # type: ignore
            """Fallback stub if mcp package is missing during offline lint."""
            def __init__(self, name: str, **kwargs: Any) -> None:
                self.name = name
            def tool(self) -> Any:
                return lambda fn: fn
            def prompt(self) -> Any:
                return lambda fn: fn
            def resource(self, uri: str) -> Any:
                return lambda fn: fn
            def run(self) -> None:
                sys.stderr.write("mcp package not installed. Install with `pip install 'mcp>=1.2.0'`\n")

mcp = ServerClass("design-os-3d-blender")

# Resolve repository root safely without cwd dependency
_CURRENT_DIR = Path(__file__).resolve().parent
_CANDIDATE_ROOTS = [
    _CURRENT_DIR.parent.parent,
    Path.cwd(),
]
REPO_ROOT = _CURRENT_DIR.parent.parent
for cand in _CANDIDATE_ROOTS:
    if (cand / "knowledge").is_dir() and (cand / "specs").is_dir():
        REPO_ROOT = cand
        break

KNOWLEDGE_DIR = REPO_ROOT / "knowledge"
SPECS_DIR = REPO_ROOT / "specs"


def find_blender_bin() -> Optional[str]:
    """Detect Blender executable across environment and common system paths."""
    env_bin = os.environ.get("BLENDER_BIN")
    if env_bin and os.path.isfile(env_bin) and os.access(env_bin, os.X_OK):
        return env_bin

    candidates = [
        "/Applications/Blender.app/Contents/MacOS/Blender",
        "/Applications/Blender 5.2.app/Contents/MacOS/Blender",
        "/usr/bin/blender",
        "/usr/local/bin/blender",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c

    which_bin = shutil.which("blender")
    if which_bin:
        return which_bin

    return None


# =====================================================================
# TOOLS (Exposed to MCP clients)
# =====================================================================

@mcp.tool()
def blender_runtime_status() -> str:
    """Inspect the host environment for Blender 5.2 availability, OS, and knowledge readiness.
    
    Returns:
        JSON string describing Blender binary availability, paths, and status.
    """
    blender_bin = find_blender_bin()
    blender_version = None
    if blender_bin:
        try:
            proc = subprocess.run(
                [blender_bin, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            first_line = proc.stdout.strip().split("\n")[0] if proc.stdout else ""
            blender_version = first_line
        except Exception as err:
            blender_version = f"Error querying version: {err}"

    catalog_path = KNOWLEDGE_DIR / "catalog.json"
    catalog_exists = catalog_path.is_file()

    payload = {
        "status": "ok",
        "blender_available": blender_bin is not None,
        "blender_bin": blender_bin,
        "blender_version": blender_version,
        "host_platform": sys.platform,
        "python_version": sys.version.split()[0],
        "repo_root": str(REPO_ROOT),
        "knowledge_ready": catalog_exists,
        "message": (
            "Blender detected and ready for headless passes."
            if blender_bin
            else "Blender binary not detected. Set BLENDER_BIN environment variable for execution passes."
        ),
    }
    return json.dumps(payload, indent=2)


@mcp.tool()
def query_blender_knowledge(query: str, topic: str = "") -> str:
    """Query the verified bpy 5.2 knowledge base for modeling, shading, modifiers, and gate rules.

    Args:
        query: Search keywords (e.g., 'bevel modifier', 'pbr shader', 'watertight mesh', 'cycloid drive').
        topic: Optional topic filter (e.g., '00-foundations', '10-modeling', '20-shading', '60-pipeline').

    Returns:
        JSON string containing matching knowledge entries, guidelines, and code snippets.
    """
    catalog_path = KNOWLEDGE_DIR / "catalog.json"
    results: List[Dict[str, Any]] = []

    # 1. Try reading precompiled catalog.json if available
    if catalog_path.is_file():
        try:
            data = json.loads(catalog_path.read_text(encoding="utf-8"))
            records = data.get("records", [])
            q_lower = query.lower()
            t_lower = topic.lower()
            for r in records:
                text_corpus = (
                    r.get("path", "") + " " +
                    r.get("title", "") + " " +
                    r.get("summary", "") + " " +
                    " ".join(r.get("tags", []))
                ).lower()
                if (not topic or t_lower in r.get("path", "").lower()) and (q_lower in text_corpus):
                    results.append({
                        "path": r.get("path"),
                        "title": r.get("title"),
                        "summary": r.get("summary"),
                        "tags": r.get("tags", []),
                    })
        except Exception:
            pass

    # 2. Fallback: Search markdown files directly
    if not results and KNOWLEDGE_DIR.is_dir():
        q_lower = query.lower()
        for md_file in KNOWLEDGE_DIR.glob("**/*.md"):
            if md_file.name == "INDEX.md":
                continue
            if topic and topic.lower() not in str(md_file).lower():
                continue
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                if q_lower in content.lower():
                    lines = [line.strip() for line in content.splitlines() if line.strip()]
                    title = lines[0].lstrip("# ") if lines else md_file.stem
                    rel_path = str(md_file.relative_to(KNOWLEDGE_DIR))
                    results.append({
                        "path": rel_path,
                        "title": title,
                        "match_preview": "\n".join(lines[:6]),
                    })
            except Exception:
                continue

    output = {
        "query": query,
        "topic": topic,
        "total_results": len(results),
        "results": results[:10],
    }
    return json.dumps(output, indent=2)


@mcp.tool()
def validate_part_spec(spec_path: str) -> str:
    """Validate a 3D part specification (spec.json) against design:os requirements.

    Args:
        spec_path: Path to the part specification JSON file.

    Returns:
        JSON string containing validation status, errors, and checked dimensions.
    """
    path = Path(spec_path)
    if not path.is_absolute():
        path = REPO_ROOT / path

    if not path.is_file():
        return json.dumps({
            "valid": False,
            "error": f"File not found: {spec_path}",
        }, indent=2)

    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except Exception as err:
        return json.dumps({
            "valid": False,
            "error": f"JSON parse error: {err}",
        }, indent=2)

    errors: List[str] = []
    if "schema_version" not in spec:
        errors.append("Missing required field: schema_version")
    if spec.get("units") != "mm":
        errors.append("Field 'units' must be explicitly 'mm'")

    parts = spec.get("parts", [])
    if not isinstance(parts, list) or len(parts) == 0:
        errors.append("Spec must contain a non-empty 'parts' list")
    else:
        for idx, part in enumerate(parts):
            p_id = part.get("id", f"part[{idx}]")
            for req in ("id", "object", "target_dims_mm", "tol_mm", "min_wall_mm"):
                if req not in part:
                    errors.append(f"Part '{p_id}' missing required field: '{req}'")

    return json.dumps({
        "valid": len(errors) == 0,
        "spec_file": str(path),
        "project": spec.get("project", ""),
        "parts_count": len(parts) if isinstance(parts, list) else 0,
        "errors": errors,
    }, indent=2)


@mcp.tool()
def execute_blender_pass(script_path: str, blend_path: str = "") -> str:
    """Execute a bpy Python script in headless Blender and verify the AGENT_OK sentinel contract.

    Args:
        script_path: Path to the Python script to execute inside Blender.
        blend_path: Optional path to an existing .blend file to open.

    Returns:
        JSON string containing execution returncode, stdout snippet, and AGENT_OK / AGENT_FAIL sentinel.
    """
    blender_bin = find_blender_bin()
    if not blender_bin:
        return json.dumps({
            "status": "error",
            "sentinel": "AGENT_FAIL",
            "message": "Blender binary not found on host. Set BLENDER_BIN=/path/to/blender.",
        }, indent=2)

    s_path = Path(script_path)
    if not s_path.is_absolute():
        s_path = REPO_ROOT / s_path
    if not s_path.is_file():
        return json.dumps({
            "status": "error",
            "sentinel": "AGENT_FAIL",
            "message": f"Script file not found: {script_path}",
        }, indent=2)

    cmd = [blender_bin, "-b"]
    if blend_path:
        b_path = Path(blend_path)
        if not b_path.is_absolute():
            b_path = REPO_ROOT / b_path
        if b_path.is_file():
            cmd.append(str(b_path))

    cmd.extend(["--python", str(s_path)])

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
        )
        output = proc.stdout or ""
        lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
        last_line = lines[-1] if lines else ""
        passed = "AGENT_OK" in last_line

        return json.dumps({
            "status": "ok" if (passed and proc.returncode == 0) else "fail",
            "sentinel": "AGENT_OK" if passed else "AGENT_FAIL",
            "returncode": proc.returncode,
            "last_line": last_line,
            "tail_output": "\n".join(lines[-15:]) if len(lines) > 15 else output,
        }, indent=2)
    except Exception as err:
        return json.dumps({
            "status": "error",
            "sentinel": "AGENT_FAIL",
            "message": str(err),
        }, indent=2)


# =====================================================================
# PROMPTS (Exposed to MCP clients)
# =====================================================================

@mcp.prompt()
def design_parametric_part(part_name: str, purpose: str = "both") -> str:
    """Prompt template for designing a parametric 3D mechanical part in Blender 5.2.

    Args:
        part_name: Name or slug of the part to design (e.g., 'bracket-m3').
        purpose: Deliverable purpose: 'render-only', 'print', or 'both'.
    """
    return f"""You are designing a mechanical 3D part named '{part_name}' for deliverable purpose '{purpose}' in Blender 5.2 LTS.

Follow the design:os binding rules:
1. Prefer data API and bmesh operations over `bpy.ops`.
2. All spatial coordinates and dimensions MUST be in millimeters (1 BU = 1 m; 1 mm = 0.001 BU).
3. Ensure the part has declared origin/datum, explicit wall thickness (min 2.0 mm for FDM), and watertight geometry.
4. Model mating interfaces, counterbores, and clearance tolerances before adding aesthetic fillets.
5. End your pass script with numerical assertions and print the sentinel:
   `print('AGENT_OK')` on success or `print('AGENT_FAIL: <reason>')` on error.
"""


@mcp.prompt()
def review_geometry_gate(part_slug: str) -> str:
    """Prompt template for reviewing a 3D print gate report.

    Args:
        part_slug: Slug of the part build (e.g., 'bracket-m3').
    """
    return f"""Audit the production gate results for part build '{part_slug}'.

Verify the following digital gate criteria:
1. Watertight geometry: Non-manifold edges == 0, non-manifold vertices == 0.
2. Minimum wall thickness satisfies the manufacturing limit (e.g. >= 2.0 mm).
3. Overhang angles do not exceed 45.0 degrees without support structure.
4. Bounding box matches target dimensions within the specified tolerance.
5. Verify STL/GLB export bytes and ensure an independent reopening check passes.
"""


# =====================================================================
# RESOURCES (Exposed to MCP clients)
# =====================================================================

@mcp.resource("blender://knowledge/index")
def get_knowledge_index() -> str:
    """Resource listing the verified bpy 5.2 knowledge base chapters and modules."""
    index_file = KNOWLEDGE_DIR / "INDEX.md"
    if index_file.is_file():
        return index_file.read_text(encoding="utf-8")
    return "# design-os-3d-blender Knowledge Base\nVerified bpy 5.2 LTS knowledge for AI agents."


@mcp.resource("blender://specs/bracket-example")
def get_bracket_example_spec() -> str:
    """Resource returning reference bracket-m3.spec.json specification."""
    spec_file = SPECS_DIR / "examples" / "bracket-m3.spec.json"
    if spec_file.is_file():
        return spec_file.read_text(encoding="utf-8")
    return json.dumps({"project": "bracket-m3", "units": "mm"}, indent=2)


# =====================================================================
# MAIN ENTRYPOINT
# =====================================================================

def main() -> None:
    """Console script entrypoint for design-os-3d-blender MCP server."""
    # Strict stdio purity: never print anything to stdout before or during mcp.run()
    mcp.run()


if __name__ == "__main__":
    main()
