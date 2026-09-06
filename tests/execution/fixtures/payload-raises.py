"""Payload that mutates the scene and then raises: must yield AGENT_FAIL + exit 3."""
import os
import sys

import bpy

SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def main():
    # Partial mutation before the failure, as in the audit's E1 probe.
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    print("MUTATION_DONE")
    raise RuntimeError("intentional failure from payload-raises")


if __name__ == "__main__":
    if "agent_runtime" in sys.modules:
        main()
    else:
        import agent_runtime as rt
        rt.run_file(__file__)
