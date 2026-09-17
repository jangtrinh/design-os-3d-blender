"""Native parameter -> evaluated geometry -> animation -> camera numeric sample.

Run: bash scripts/headless-run.sh scripts/samples/native-api-contract.py
Purpose: render-only verification; manufacture NOT_REQUESTED. No files or media.
"""
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from agent_runtime import emit_ok
from agent_verify import framing, tri_count, world_bbox
from boilerplates.bp_animation import animate_property_keys
from boilerplates.bp_geonodes import assign_geonodes_modifier, set_modifier_input

assert bpy.app.background, 'Run in a disposable headless process'
assert 'ContractSample' not in bpy.data.objects, 'Sample already exists'
mesh = bpy.data.meshes.new('ContractSample')
obj = bpy.data.objects.new('ContractSample', mesh)
bpy.context.scene.collection.objects.link(obj)
tree = bpy.data.node_groups.new('ContractSample', 'GeometryNodeTree')
tree.is_modifier = True
tree.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
height = tree.interface.new_socket(name='Height', in_out='INPUT', socket_type='NodeSocketFloat')
height.default_value, height.min_value, height.max_value = 1.0, 0.1, 10.0
group_input = tree.nodes.new('NodeGroupInput')
group_output = tree.nodes.new('NodeGroupOutput')
cube = tree.nodes.new('GeometryNodeMeshCube')
size = tree.nodes.new('ShaderNodeCombineXYZ')
size.inputs['X'].default_value = size.inputs['Y'].default_value = 2.0
tree.links.new(group_input.outputs['Height'], size.inputs['Z'])
tree.links.new(size.outputs['Vector'], cube.inputs['Size'])
tree.links.new(cube.outputs['Mesh'], group_output.inputs['Geometry'])
modifier = assign_geonodes_modifier(obj, tree)

measured_heights = []
for requested in (1.0, 3.0):
    set_modifier_input(modifier, height.identifier, requested)
    low, high = world_bbox(obj)
    actual = high.z - low.z
    assert abs(actual - requested) < 1e-5, (requested, actual)
    measured_heights.append(actual)
assert len(mesh.vertices) == 0, 'Base mesh must remain unchanged'
assert tri_count(obj) == 12

animate_property_keys(obj, 'location', [(1, 0.0), (11, 2.0)], index=0, interpolation='LINEAR')
bpy.context.scene.frame_set(6)
graph = bpy.context.evaluated_depsgraph_get()
midpoint = obj.evaluated_get(graph).matrix_world.translation.x
assert abs(midpoint - 1.0) < 1e-5
camera_data = bpy.data.cameras.new('ContractSampleCamera')
camera_data.type, camera_data.ortho_scale = 'ORTHO', 8.0
camera_data.clip_start, camera_data.clip_end = 0.1, 100.0
camera = bpy.data.objects.new('ContractSampleCamera', camera_data)
bpy.context.scene.collection.objects.link(camera)
camera.location = (0, 0, 10)
screen = framing(obj, camera)
assert screen['in_frame'], screen
emit_ok('native-api-contract-sample', blender=bpy.app.version_string,
        build_hash=bpy.app.build_hash.decode(), heights=measured_heights,
        midpoint_x=midpoint, frame=6, triangles=tri_count(obj),
        camera_screen=screen, manufacture='NOT_REQUESTED')
