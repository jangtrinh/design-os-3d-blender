"""Native calibration coupon: missing detail can preserve global dimensions.

Only for disposable verification scenes. These are controlled positive/negative
variants, not a claim that a generative agent has learned to repair an asset.
"""
import json
import os
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

from agent_verify import world_bbox
from boilerplates.bp_parametric_contract import bind_source_evidence, normalize_contract
from native_review.evidence import file_pin, value_hash

CAPTURE = {'camera': 'CouponCamera', 'projection': 'ORTHO', 'frame': 1,
           'location': [0.20, -0.26, 0.16], 'target': [0, 0, 0.043],
           'ortho_scale': 0.15, 'clip_start': 0.001, 'clip_end': 10.0,
           'resolution': [256, 256]}


def material(name, color, metallic):
    mat = bpy.data.materials.new(name)
    shader = mat.node_tree.nodes.get('Principled BSDF')
    assert shader and {'Base Color', 'Metallic', 'Roughness'} <= set(shader.inputs.keys())
    shader.inputs['Base Color'].default_value = color
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = 0.32
    return mat


def cylinder(name, radius, depth, z, mat):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    try:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=64,
                             radius1=radius, radius2=radius, depth=depth)
        bm.to_mesh(mesh)
    finally:
        bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location.z = z
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new('EdgeHighlight', 'BEVEL')
    bevel.width, bevel.segments = 0.0006, 3
    return obj


def build(root, output, variant):
    assert bpy.app.background and not bpy.data.filepath, 'Disposable factory-startup scene required'
    assert variant in ('reference', 'candidate', 'revision')
    output = Path(output)
    names = ('model.blend', 'proof.png', 'numeric.json', 'contract.json', 'summary.json')
    if any((output / name).exists() for name in names):
        raise ValueError('Never overwrite any existing coupon output, including a partial attempt')
    output.mkdir(parents=True, exist_ok=True)
    param_path = 'specs/examples/native-iteration-parameters.json'
    normalized = normalize_contract(json.loads((root / param_path).read_text()))
    p = {name: item['values_si']['value'] for name, item in normalized['parameters'].items()}
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    blue = material('BodyBlue', (0.035, 0.15, 0.28, 1), 0.3)
    gold = material('CollarGold', (0.55, 0.28, 0.055, 1), 0.5)
    dark = material('BaseDark', (0.08, 0.09, 0.11, 1), 0.1)
    parts = [cylinder('base', p['base_radius'], 0.006, 0.003, dark),
             cylinder('body', p['radius'], p['height'], 0.006 + p['height'] / 2, blue),
             cylinder('lower_collar', p['collar_radius'], 0.010, 0.006 + p['height'] * 0.2, gold)]
    if variant != 'candidate':
        parts.append(cylinder('upper_collar', p['collar_radius'], 0.010, 0.006 + p['height'] * 0.775, gold))
    scene = bpy.context.scene
    scene.unit_settings.system, scene.unit_settings.scale_length = 'METRIC', 1.0
    scene.render.engine, scene.cycles.device, scene.cycles.samples = 'CYCLES', 'CPU', 8
    scene.render.resolution_x = scene.render.resolution_y = 256
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.world.color = (0.18, 0.18, 0.18)
    camera_data = bpy.data.cameras.new('CouponCamera')
    camera_data.type, camera_data.ortho_scale = 'ORTHO', CAPTURE['ortho_scale']
    camera_data.clip_start, camera_data.clip_end = 0.001, 10
    camera = bpy.data.objects.new('CouponCamera', camera_data)
    scene.collection.objects.link(camera)
    camera.location = CAPTURE['location']
    camera.rotation_euler = (Vector(CAPTURE['target']) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = camera
    for name, location, energy in [('Key', (0.12, -0.16, 0.22), 15), ('Fill', (-0.12, 0.1, 0.15), 8)]:
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.size = energy, 0.18
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = location
        light.rotation_euler = (Vector(CAPTURE['target']) - light.location).to_track_quat('-Z', 'Y').to_euler()
    bounds = [world_bbox(obj) for obj in parts]
    height = max(high.z for _, high in bounds) - min(low.z for low, _ in bounds)
    assert abs(height - (p['height'] + 0.006)) < 1e-6
    assert abs(height - normalized['datums']['top']['position_m'][2]) < 1e-6
    scene.render.filepath = str(output / 'proof.png')
    assert bpy.ops.wm.save_as_mainfile(filepath=str(output / 'model.blend')) == {'FINISHED'}
    assert bpy.ops.render.render(write_still=True) == {'FINISHED'}
    context = json.loads(os.environ['DESIGN_OS_INPUTS_JSON'])
    sources = sorted(set(context['project']) | {param_path, 'scripts/samples/native-iteration-build.py'})
    candidates = {'scene': file_pin(root, output / 'model.blend')}
    candidates.update({path: file_pin(root, path) for path in sources})
    numeric = {'status': 'pass', 'candidate_sha256': value_hash(candidates),
               'checks': [{'id': 'overall-height', 'status': 'pass', 'value': height, 'unit': 'm'},
                          {'id': 'scene-unit-scale', 'status': 'pass', 'value': scene.unit_settings.scale_length}],
               'limits': ['Overall height and units only; missing detail may still pass.']}
    summary = {'variant': variant, 'capture': CAPTURE, 'candidate_pins': candidates,
               'part_count': len(parts), 'height_m': height, 'manufacture': 'NOT_REQUESTED',
               'source_evidence': bind_source_evidence(normalized, sources, root)}
    for name, value in [('numeric.json', numeric), ('contract.json', normalized), ('summary.json', summary)]:
        with (output / name).open('x') as handle:
            json.dump(value, handle, indent=2, allow_nan=False)
    return summary
