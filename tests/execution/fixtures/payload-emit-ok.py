"""Clean payload: asserts a real scene postcondition and emits AGENT_OK.

The four-line tail is the standard idiom: run directly by Blender it re-enters
through agent_runtime (which owns the sentinel and the exit code); run by
run_file the runtime is already imported, so main() executes inline.
"""
import os
import sys

import bpy

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def main():
    import agent_runtime as rt
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0.0, 0.0, 0.0))
    cube = bpy.context.object
    assert cube is not None, "cube was not created"
    rt.emit_ok("fixture-clean", object=cube.name, dim_x=round(cube.dimensions.x, 6))


if __name__ == "__main__":
    if "agent_runtime" in sys.modules:
        main()
    else:
        import agent_runtime as rt
        rt.run_file(__file__)
