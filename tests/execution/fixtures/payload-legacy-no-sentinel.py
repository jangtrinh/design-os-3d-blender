"""A pre-sentinel payload: succeeds but prints no verdict.

headless-run.sh must still run it and must warn that the exit code it fell back
to is Blender's, which is not trustworthy on its own.
"""
import bpy

print("LEGACY_PAYLOAD_RAN objects=%d" % len(bpy.data.objects))
