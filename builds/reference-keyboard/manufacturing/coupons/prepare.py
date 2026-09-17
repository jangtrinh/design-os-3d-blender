"""Freeze the specimen specification before running any native construction."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BUILD = HERE.parents[1]
ROOT = BUILD.parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(BUILD / 'scripts')]
from production_gate.spec import validate


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2, allow_nan=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', default='pipeline.json')
    args = parser.parse_args()
    cfg = json.loads((HERE / 'contract.json').read_text())
    specimens = []
    for span in cfg['keycap_spans_mm']:
        for delta in cfg['keycap_arm_offsets_mm']:
            specimens.append({'id': f'K{len(specimens)+1:02}', 'kind': 'keycap',
                              'span_mm': span, 'horizontal_arm_mm': round(1.10 + delta, 4),
                              'vertical_arm_mm': round(1.28 + delta, 4),
                              'dims_mm': cfg['keycap_envelope_mm'], 'wall_mm': 1.0})
    for gauge in cfg['d_gauges']:
        specimens.append(dict(gauge, kind='D-gauge', dims_mm=[14, 14, 8], wall_mm=2.0))
    for i, diameter in enumerate(cfg['guide_ids_mm'], 1):
        specimens.append({'id': f'G{i:02}', 'kind': 'guide', 'diameter_mm': diameter,
                          'dims_mm': [6, 6, 7.9], 'wall_mm': .95})
    specimens.append({'id': 'P01', 'kind': 'pin', 'dims_mm': [8, 8, 12], 'wall_mm': .95})
    parts = [{'id': s['id'], 'object': s['id'], 'target_dims_mm': s['dims_mm'],
              'tol_mm': .03, 'min_wall_mm': s['wall_mm'], 'expected_shells': 1,
              'orientation_up': '+z', 'material': cfg['process'],
              'process': 'Dimensional characterization; not released production settings'} for s in specimens]
    spec = {'schema_version': 1, 'units': 'mm', 'project': cfg['revision'],
            'print_volume_mm': [150, 150, 50], 'brim_margin_mm': 3, 'parts': parts,
            'required_checks': ['non_manifold_edges', 'non_contiguous_edges', 'zero_area_faces',
                                'bbox_dims_mm', 'signed_volume_positive', 'scale_applied', 'wall_thickness_screen'],
            'physical_evidence': cfg['preconditions'],
            'load_cases': [{'description': 'Unloaded dimensional and subsequent controlled retention/slide specimens; no demonstrated load capacity'}]}
    validate(spec)
    write(HERE / 'specimens.json', specimens)
    write(HERE / 'spec.json', spec)
    sources = [HERE / 'contract.json', HERE / 'specimens.json', HERE / 'spec.json', HERE / 'shapes.py']
    sources += [BUILD / 'scripts' / name for name in ('controls.py', 'project.py', 'meshkit.py', 'studio.py', 'fullhd.py')]
    sources += list((ROOT / 'scripts' / 'production_gate').glob('*.py'))
    sources += list((ROOT / 'scripts' / 'agent_verify').glob('*.py'))
    sources += [ROOT / 'scripts/boilerplates/bp_core.py']
    inputs = sorted(path.relative_to(ROOT).as_posix() for path in sources)
    prefix = HERE.relative_to(ROOT).as_posix()
    steps = [
        {'id': 'build', 'script': f'{prefix}/build.py', 'inputs': inputs, 'depends_on': [],
         'artifact_inputs': [], 'outputs': ['specimens.blend', 'measurements.json'],
         'required_postconditions': ['specimens', 'measured_interfaces'], 'timeout_seconds': 120},
        {'id': 'gate', 'script': f'{prefix}/gate.py', 'inputs': inputs, 'depends_on': ['build'],
         'artifact_inputs': ['build:specimens.blend'],
         'outputs': ['gate-report.json', 'stl/manifest.json'] + [f'stl/{s["id"]}.stl' for s in specimens],
         'required_postconditions': ['families', 'failures', 'reimported_stl'], 'timeout_seconds': 240},
        {'id': 'view', 'script': f'{prefix}/view.py', 'inputs': inputs, 'depends_on': ['build', 'gate'],
         'artifact_inputs': ['build:specimens.blend', 'gate:gate-report.json'],
         'outputs': ['specimen-set-FullHD.png', 'view.json'],
         'required_postconditions': ['specimens', 'width', 'height'], 'timeout_seconds': 180}]
    write(HERE / args.manifest, {'version': 1, 'pipeline_id': cfg['revision'], 'steps': steps})
    print(json.dumps({'specimens': len(specimens), 'manifest': str(HERE / args.manifest)}))


if __name__ == '__main__':
    main()
