"""Keep the accepted rear-controller wire routes in the original studio style."""
from pathlib import Path
import bpy, json
ROOT = Path(__file__).resolve().parents[1]
sc = bpy.context.scene
assert sc.name == 'A5-Original-refined'
motion = json.loads((ROOT.parent/'robot-arm-assembly-guide/reports/motion.json').read_text())
assert len(motion['wires']) == 7
material = bpy.data.materials.new('A5-wire-charcoal')
bs = next(n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
bs.inputs['Base Color'].default_value = (.025, .03, .035, 1)
bs.inputs['Roughness'].default_value = .65
wires = []
for w in motion['wires']:
    if 'power-in' in w['names'][0]:
        continue
    name = w['names'][0].replace('A4-', 'A5-')
    assert name not in sc.objects
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = .0024 if 'power' in name else .00115
    data.bevel_resolution = 3
    sp = data.splines.new('POLY')
    sp.points.add(len(w['points'])-1)
    for p, co in zip(sp.points, w['points']):
        p.co = (*co, 1)
    data.materials.append(material)
    ob = bpy.data.objects.new(name, data)
    sc.collection.objects.link(ob)
    ob['presentation_only'] = True
    wires.append({'object': name, 'points': w['points']})
(ROOT/'reports/native-wires.json').write_text(json.dumps(wires, indent=2))
print('NATIVE_WIRES_PASS', len(wires))
