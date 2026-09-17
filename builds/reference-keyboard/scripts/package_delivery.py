"""Build a revision-B CK-001 review package from already verified native artifacts.

The packager is intentionally evidence-driven. It refuses mixed revisions, stale
review pins, incomplete Full HD media, or an existing destination/archive before
copying any bytes. Use --preflight-only while upstream evidence is still settling.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil
import struct
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project import BUILD, ROOT, write


class PackageError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise PackageError(message)


def bounded(value, *, must_exist=True, directory=None):
    raw = Path(value)
    path = (raw if raw.is_absolute() else ROOT / raw).resolve()
    root = ROOT.resolve()
    need(path.is_relative_to(root), f'path outside project root: {value}')
    if must_exist:
        need(path.exists(), f'missing path: {path}')
    if directory is True:
        need(path.is_dir(), f'expected directory: {path}')
    elif directory is False:
        need(path.is_file(), f'expected file: {path}')
    return path


def file_sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def value_sha(value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def load_json(path):
    def reject(value):
        raise PackageError(f'non-finite JSON value {value!r} in {path}')
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject)


def latest_attempt(steps, name):
    step = bounded(Path(steps) / name, directory=True)
    attempts = sorted(p for p in step.iterdir() if p.is_dir() and p.name.startswith('attempt-'))
    need(attempts, f'no attempt directory under {step}')
    return attempts[-1]


def png_size(path):
    with Path(path).open('rb') as handle:
        header = handle.read(24)
    need(header[:8] == b'\x89PNG\r\n\x1a\n', f'not a PNG: {path}')
    return list(struct.unpack('>II', header[16:24]))


def close(actual, expected, label, tolerance=1e-6):
    need(abs(float(actual) - float(expected)) <= tolerance,
         f'{label}: {actual!r} != {expected!r}')


def pin_path(pin, label):
    need(isinstance(pin, dict) and pin.get('path') and pin.get('sha256'), f'invalid {label} pin')
    path = bounded(pin['path'], directory=False)
    need(file_sha(path) == pin['sha256'], f'stale {label} pin: {pin["path"]}')
    return path


def key_count(layout):
    return (sum(len(row) for row in layout['main_rows']) + len(layout['bottom_row'])
            + int(layout['rear_macros']['count']) + len(layout['left_macros_mm']))


def contract_metrics(layout, interfaces, contract, fit, layout_checks):
    params = {name: row['value'] for name, row in contract['parameters'].items()}
    need(layout['revision'].startswith('B-') and interfaces['revision'] == 'B', 'revision-B design files required')
    for name, actual in {
        'width_mm': layout['width_mm'], 'depth_mm': layout['depth_mm'],
        'height_mm': layout['height_mm'], 'key_top_mm': layout['key_top_mm'],
        'key_height_mm': layout['key_height_mm'], 'switch_width_mm': layout['switch_width_mm'],
        'switch_height_mm': layout['switch_height_mm'], 'knob_diameter_mm': layout['knob_diameter_mm'],
        'knob_height_mm': layout['knob_height_mm'],
    }.items():
        close(actual, params[name], f'layout/contract {name}')

    keys, knobs = key_count(layout), len(layout['knobs_mm'])
    stem_length = interfaces['keycap']['stem_top_z'] - interfaces['keycap']['stem_bottom_z']
    reserve = interfaces['keycap']['receiver_depth'] - stem_length
    guides = len(interfaces['spacebar']['guide_offsets_x'])
    d_engagement = interfaces['encoder']['nominal_D_engagement']
    travel = layout['key_travel_mm']
    close(interfaces['keycap']['travel'], travel, 'key travel interface/layout')
    close(interfaces['spacebar']['travel'], travel, 'spacebar travel interface/layout')

    checks = {row['name']: row for row in layout_checks['checks']}
    need(layout_checks['status'] == 'pass' and not layout_checks['failed'], 'layout checks must pass')
    need(not [row for row in layout_checks['checks'] if row['status'] == 'fail'], 'layout check failure present')
    need(checks['key_count']['actual'] == keys == checks['key_count']['expected'], 'key count mismatch')
    need(checks['knob_count']['actual'] == knobs == checks['knob_count']['expected'], 'knob count mismatch')
    close(checks['overall_height']['actual']['height_mm'], layout['height_mm'], 'overall height')

    stem = fit['interfaces']['key_stem']
    wide = fit['interfaces']['wide_guides']
    encoder = fit['interfaces']['encoder_dshaft']
    overlap = fit['switch_keycap_overlap']
    need(stem['cells_checked'] == keys and stem['dimensions_within_0_05_mm'], 'stem evidence incomplete')
    need(stem['key_material_stem_collision_indices'] == [] and stem['stem_static_collision_indices'] == [],
         'stem collision evidence failed')
    need(overlap['pairs_checked'] == keys and overlap['collision_pairs'] == 0, 'key travel collision evidence failed')
    need(overlap['travel_samples_mm'][0] == 0.0, 'key travel must include rest position')
    close(overlap['travel_samples_mm'][-1], travel, 'sampled key travel')
    for value in stem['insertion_range_mm']:
        close(value, stem_length, 'stem insertion')
    for value in stem['ceiling_reserve_range_mm']:
        close(value, reserve, 'receiver ceiling reserve')
    need(wide['guides_checked'] == guides and wide['collision_free'], 'spacebar guide evidence failed')
    close(wide['travel_samples_mm'][-1], travel, 'spacebar sampled travel')
    need(encoder['pairs_checked'] == knobs and encoder['matching_rotations_collision_free'],
         'encoder D-shaft evidence failed')
    need(encoder['negative_controls_detect_collision'], 'encoder D-shaft negative control failed')
    for value in encoder['engagement_range_mm']:
        close(value, d_engagement, 'D-shaft engagement')

    return {
        'envelope_mm': [layout['width_mm'], layout['depth_mm'], layout['height_mm']],
        'keys': keys, 'knobs': knobs, 'key_travel_mm': travel,
        'stem_insertion_mm': round(stem_length, 4), 'receiver_ceiling_reserve_mm': round(reserve, 4),
        'spacebar_guides': guides, 'spacebar_rest_engagement_mm': wide['rest_engagement_range_mm'][0],
        'D_engagement_mm': d_engagement,
    }


def validate_gate(gate, spec, scene_sha, spec_sha, stl_manifest, stl_dir):
    need(gate['inputs']['scene_sha256'] == scene_sha, 'final gate bound to another scene')
    need(gate['inputs']['spec_sha256'] == spec_sha, 'final gate bound to another spec')
    need(not gate['failed'] and not gate['required_checks_missing'], 'final gate is not clean')
    spec_parts = {row['id']: row for row in spec['parts']}
    gate_parts = {row['id']: row for row in gate['parts']}
    need(spec_parts.keys() == gate_parts.keys(), 'gate families do not match spec parts')
    for ident, row in gate_parts.items():
        declared = spec_parts[ident]
        need(row['status'] == 'pass', f'gate family failed: {ident}')
        need(row['allowed']['target_dims_mm'] == declared['target_dims_mm'], f'{ident} target dimensions drifted')
        close(row['allowed']['tol_mm'], declared['tol_mm'], f'{ident} tolerance')
        close(row['allowed']['min_wall_mm'], declared['min_wall_mm'], f'{ident} minimum wall')
        need(row['allowed']['expected_shells'] == declared['expected_shells'], f'{ident} shell count drifted')
        for actual, expected in zip(row['measured']['bbox_dims_mm'], declared['target_dims_mm']):
            need(abs(actual - expected) <= declared['tol_mm'], f'{ident} bbox outside declared tolerance')

    need(stl_manifest['status'] == 'NOT_MANUFACTURING_APPROVED', 'STL manifest lost release boundary')
    stl_rows = {row['id']: row for row in stl_manifest['parts']}
    need(stl_rows.keys() == gate_parts.keys(), 'STL families do not match gated families')
    paths = []
    for ident, row in stl_rows.items():
        path = bounded(Path(stl_dir) / Path(row['file']).name, directory=False)
        need(file_sha(path) == row['sha256'], f'STL hash mismatch: {ident}')
        need(row['status'] == 'UNRELEASED_DIGITAL_CHECK_ONLY', f'STL release status invalid: {ident}')
        declared = spec_parts[ident]
        for actual, expected in zip(row['dims_mm'], declared['target_dims_mm']):
            need(abs(actual - expected) <= declared['tol_mm'], f'STL dimensions drifted: {ident}')
        paths.append(path)
    return paths, list(gate_parts)


def validate_roundtrip(roundtrip, glb_sha, export_settings, inventory):
    need(roundtrip['pass'] and roundtrip['mesh_names_match'], 'GLB reopen did not pass')
    need(roundtrip['glb_sha256'] == glb_sha == export_settings['glb_sha256'], 'GLB hash binding mismatch')
    expected = roundtrip['expected_mesh_names']
    need(expected and len(expected) == len(set(expected)), 'invalid expected GLB mesh names')
    need(roundtrip['imported_mesh_names'] == expected, 'imported mesh names differ from export names')
    need(export_settings['meshes'] == len(expected), 'export mesh count disagrees with actual roundtrip names')
    inventory_names = [row['name'] for row in inventory['objects']]
    need(len(inventory_names) == len(expected) and set(inventory_names) == set(expected),
         'scene inventory mesh set differs from roundtrip names')
    need(set(roundtrip['frames']) == {'1', '7', '60'}, 'roundtrip must contain exactly frames 1, 7 and 60')
    bbox_tol = float(roundtrip['tolerances_mm']['bbox'])
    surface_tol = float(roundtrip['tolerances_mm']['surface'])
    maximum = 0.0
    for frame in ('1', '7', '60'):
        rows = roundtrip['frames'][frame]['objects']
        need(len(rows) == len(expected), f'frame {frame} object count mismatch')
        need([row['name'] for row in rows] == expected, f'frame {frame} mesh names mismatch')
        for row in rows:
            need(row['pass'] and row['triangle_count_match'], f'frame {frame} failed: {row["name"]}')
            need(row['bbox_max_abs_error_mm'] <= bbox_tol, f'frame {frame} bbox tolerance failed: {row["name"]}')
            need(row['surface_max_error_mm'] <= surface_tol, f'frame {frame} surface tolerance failed: {row["name"]}')
            maximum = max(maximum, row['surface_max_error_mm'])
    return expected, maximum


def validate_media(media_dir, media_manifest, stills, scene_sha, gate_sha):
    need(media_manifest['scene_sha256'] == stills['scene_sha256'] == scene_sha, 'Full HD media scene binding mismatch')
    need(media_manifest['gate_sha256'] == gate_sha, 'Full HD media gate binding mismatch')
    need(media_manifest['settings'] == stills['settings'], 'Full HD still settings mismatch')
    need(media_manifest['views'] == stills['views'], 'Full HD view manifests disagree')
    settings = media_manifest['settings']
    need(settings.get('resolution') == [1920, 1080] and settings.get('native_render') is True,
         'Full HD media was not declared as native 1920x1080 rendering')
    views = media_manifest['views']
    need(isinstance(views, dict) and len(views) == 11, 'delivery requires exactly 11 Full HD still views')
    images = {}
    for name, row in views.items():
        need(name and '/' not in name and '\\' not in name, f'invalid media view id: {name!r}')
        path = bounded(Path(media_dir) / f'CK-001-{name}.png', directory=False)
        need(png_size(path) == [1920, 1080], f'view is not actual 1920x1080 PNG: {name}')
        need(row.get('verified_pixel_size') == [1920, 1080], f'view manifest size not verified: {name}')
        need(row.get('sha256') == file_sha(path), f'view hash mismatch: {name}')
        images[name] = path

    video = media_manifest['video']
    movie = bounded(Path(media_dir) / video['file'], directory=False)
    need(video['sha256'] == file_sha(movie), 'Full HD movie hash mismatch')
    probe = video['probe']
    need([probe['width'], probe['height']] == [1920, 1080], 'Full HD movie dimensions mismatch')
    need(int(probe['nb_read_frames']) == 96 and probe['r_frame_rate'] == '24/1', 'Full HD movie must be 96 frames at 24 fps')
    need(video['full_decode'] == 'pass', 'Full HD movie full decode did not pass')
    frames = video['frames']
    need(len(frames) == 96 and [row['frame'] for row in frames] == list(range(1, 97)), 'movie frame manifest is incomplete')
    frame_dir = bounded(Path(media_dir) / 'frames', directory=True)
    for row in frames:
        frame = bounded(frame_dir / row['file'], directory=False)
        need(row['sha256'] == file_sha(frame), f'movie source-frame hash mismatch: {row["frame"]}')
        need(png_size(frame) == [1920, 1080], f'movie source frame is not 1920x1080: {row["frame"]}')
    return views, images, movie


def validate_review(review_dir, media_views, images, expected_sources):
    names = ('target', 'packet', 'critique', 'assessment', 'references', 'numeric')
    paths = {name: bounded(Path(review_dir) / f'{name}.json', directory=False) for name in names}
    docs = {name: load_json(path) for name, path in paths.items()}
    packet, critique, assessment = docs['packet'], docs['critique'], docs['assessment']
    need(pin_path(packet['target'], 'review target') == paths['target'], 'review packet target path mismatch')
    need(pin_path(packet['numeric'], 'review numeric') == paths['numeric'], 'review packet numeric path mismatch')
    need(critique['packet_sha256'] == file_sha(paths['packet']), 'critique is not bound to packet')
    need(assessment['target_sha256'] == file_sha(paths['target']), 'assessment is not bound to target')
    need(assessment['candidate_sha256'] == packet['candidate_sha256'], 'assessment candidate binding mismatch')
    need(assessment['packet']['sha256'] == file_sha(paths['packet']), 'assessment packet hash mismatch')
    need(assessment['critique']['sha256'] == file_sha(paths['critique']), 'assessment critique hash mismatch')
    need(docs['numeric']['candidate_sha256'] == packet['candidate_sha256'], 'numeric candidate binding mismatch')
    need(docs['numeric']['status'] == 'pass', 'numeric review evidence must pass before packaging')

    for role, pin in packet['candidates'].items():
        pin_path(pin, f'review candidate {role}')
    for role, expected_path in expected_sources.items():
        need(role in packet['candidates'], f'review packet missing candidate role: {role}')
        pin = packet['candidates'][role]
        need(pin['sha256'] == file_sha(expected_path), f'review candidate hash mismatch: {role}')

    need(set(packet['proofs']) == set(media_views), 'review proofs do not cover the 11 delivery views')
    target_views = {row['id']: row for row in docs['target']['views']}
    need(set(target_views) == set(media_views), 'review target does not cover the 11 delivery views')
    references = {}
    for name in media_views:
        proof = packet['proofs'][name]
        need(pin_path(proof, f'review proof {name}') == images[name], f'review proof path mismatch: {name}')
        need(proof['sha256'] == file_sha(images[name]), f'review proof hash mismatch: {name}')
        view = target_views[name]
        need(view['proof_size'] == [1920, 1080], f'review proof size mismatch: {name}')
        ref = view['target']
        ref_path = pin_path(ref, f'reference for {name}')
        references[ref_path.name] = ref_path
    for key, pin in docs['references']['references'].items():
        pin_path(pin, f'references.json {key}')
    return paths, docs, references


def human_label(name):
    known = {
        'hero': 'Hero view', 'top': 'Top view', 'knob-detail': 'Knob detail',
        'key-detail': 'Key detail', 'exploded': 'Exploded assembly', 'bottom': 'Bottom view',
        'receiver': 'Cross receiver', 'spacebar-guides': 'Spacebar guides',
        'D-receiver': 'D-shaft receiver', 'encoder-mount': 'Encoder mount', 'usb-mount': 'USB mount',
    }
    return known.get(name, name.replace('-', ' ').strip().title())


def add_source(sources, relative, source):
    source = bounded(source, directory=False)
    need(relative not in sources, f'duplicate package path: {relative}')
    sources[relative] = {'path': source, 'sha256': file_sha(source), 'bytes': source.stat().st_size}


def preflight(args):
    presentation = bounded(args.presentation, directory=True)
    verification = bounded(args.verification, directory=True)
    if (verification / 'steps').is_dir():
        verification = bounded(verification / 'steps', directory=True)
    media = bounded(args.media, directory=True)
    review = bounded(args.review, directory=True)
    destination = bounded(args.destination, must_exist=False)
    archive = bounded(args.archive, must_exist=False)
    need(not destination.exists(), f'destination already exists: {destination}')
    need(not archive.exists(), f'archive already exists: {archive}')
    need(destination != archive and archive.suffix.lower() == '.zip', 'archive must be a new .zip file')

    inspect = latest_attempt(verification, 'inspect')
    gate_dir = latest_attempt(verification, 'final-gate')
    export = latest_attempt(verification, 'export')
    reopen = latest_attempt(verification, 'reopen')
    paths = {
        'scene': bounded(presentation / 'keyboard.blend', directory=False),
        'motion_contract': bounded(presentation / 'motion-contract.json', directory=False),
        'motion_report': bounded(presentation / 'motion-report.json', directory=False),
        'provenance': bounded(presentation / 'provenance.json', directory=False),
        'views': bounded(presentation / 'views.json', directory=False),
        'fit': bounded(inspect / 'fit-report.json', directory=False),
        'layout_checks': bounded(inspect / 'layout-checks.json', directory=False),
        'inventory': bounded(inspect / 'mesh-inventory.json', directory=False),
        'gate': bounded(gate_dir / 'final-gate.json', directory=False),
        'stl_manifest': bounded(gate_dir / 'stl/manifest.json', directory=False),
        'glb': bounded(export / 'keyboard.glb', directory=False),
        'export_settings': bounded(export / 'export-settings.json', directory=False),
        'export_evidence': bounded(export / 'export-evidence.json', directory=False),
        'source_surfaces': bounded(export / 'source-surfaces.json', directory=False),
        'roundtrip': bounded(reopen / 'glb-roundtrip.json', directory=False),
        'media_manifest': bounded(media / 'media-manifest.json', directory=False),
        'stills': bounded(media / 'stills.json', directory=False),
        'layout': bounded(BUILD / 'layout.json', directory=False),
        'interfaces': bounded(BUILD / 'interfaces.json', directory=False),
        'spec': bounded(BUILD / 'spec-B.json', directory=False),
        'contract': bounded(BUILD / 'dimensions-contract-B.json', directory=False),
        'design_notes': bounded(ROOT / 'plans/260917-keyboard-refinement/reports/final-engineering-review.md', directory=False),
        'visual_review': bounded(ROOT / 'plans/260917-keyboard-refinement/reports/final-visual-review.md', directory=False),
        'package_review': bounded(ROOT / 'plans/260917-keyboard-refinement/reports/package-review.md', directory=False),
    }
    data = {name: load_json(path) for name, path in paths.items() if path.suffix == '.json' and name != 'source_surfaces'}
    scene_sha, spec_sha = file_sha(paths['scene']), file_sha(paths['spec'])
    need(data['layout_checks']['scene_sha256'] == data['fit']['scene_sha256'] == data['inventory']['scene_sha256'] == scene_sha,
         'inspect reports are bound to another scene')
    need(data['fit']['interfaces']['source_binding']['caller_scene_sha256'] == scene_sha, 'fit source binding mismatch')
    need(data['export_settings']['blend_sha256'] == scene_sha, 'export settings bound to another scene')
    need(data['export_evidence']['scene_sha256'] == scene_sha, 'export evidence bound to another scene')
    need(data['export_evidence']['spec_sha256'] == spec_sha, 'export evidence bound to another spec')
    need(data['export_evidence']['contract_sha256'] == value_sha(data['contract']),
         'export evidence bound to another dimensional contract')
    glb_sha = file_sha(paths['glb'])
    need(data['export_settings']['glb_sha256'] == glb_sha, 'export settings GLB hash mismatch')
    need(any(row['sha256'] == glb_sha for row in data['export_evidence']['files']), 'export evidence does not pin actual GLB')
    source_surfaces_sha = file_sha(paths['source_surfaces'])
    need(data['roundtrip']['source_sha256'] == source_surfaces_sha, 'roundtrip source-surface hash mismatch')

    metrics = contract_metrics(data['layout'], data['interfaces'], data['contract'], data['fit'], data['layout_checks'])
    stl_paths, gate_ids = validate_gate(data['gate'], data['spec'], scene_sha, spec_sha,
                                        data['stl_manifest'], gate_dir / 'stl')
    expected_names, max_surface = validate_roundtrip(data['roundtrip'], glb_sha,
                                                     data['export_settings'], data['inventory'])
    need(data['inventory']['scene_sha256'] == scene_sha, 'mesh inventory scene binding mismatch')
    views, images, movie = validate_media(media, data['media_manifest'], data['stills'], scene_sha, file_sha(paths['gate']))

    review_expected = {
        'scene': paths['scene'], 'layout': paths['layout'], 'interfaces': paths['interfaces'],
        'spec': paths['spec'], 'gate': paths['gate'], 'fit': paths['fit'],
        'roundtrip': paths['roundtrip'], 'stills': paths['stills'],
    }
    review_paths, review_docs, references = validate_review(review, views, images, review_expected)

    media_review_path = None
    media_review = None
    if args.media_review:
        media_review_path = bounded(args.media_review, directory=False)
        media_review = load_json(media_review_path)
        need(media_review['scene_sha256'] == scene_sha, 'final media review scene mismatch')
        need(media_review['media_manifest_sha256'] == file_sha(paths['media_manifest']), 'final media review manifest mismatch')
        need(media_review['video_sha256'] == file_sha(movie), 'final media review movie mismatch')
        need(media_review['status'] == 'pass' and media_review['reviewer'], 'final media review must be attributed and pass')
        need(set(media_review['viewed_decoded_frames']) >= {1, 7, 60, 96}, 'final media review needs the four critical decoded frames')
        pin_path(media_review['pixel_audit'], 'final media pixel audit')

    need(data['motion_report']['status'] == 'pass', 'presentation motion report is not pass')
    need(data['provenance']['source_sha256'], 'presentation provenance has no source geometry SHA')
    need(metrics['keys'] == sum(name.startswith('RK_KEY_') for name in expected_names), 'GLB key mesh count mismatch')
    need(metrics['knobs'] == sum(name.startswith('RK_KNOB_') for name in expected_names), 'GLB knob mesh count mismatch')
    need(metrics['spacebar_guides'] == sum(name.startswith('RK_GUIDE_SLEEVE_') for name in expected_names),
         'GLB guide sleeve count mismatch')

    sources = {}
    for relative, source in {
        'CK-001.blend': paths['scene'], 'CK-001.glb': paths['glb'],
        movie.name: movie,
        'reports/fit-report.json': paths['fit'], 'reports/layout-checks.json': paths['layout_checks'],
        'reports/mesh-inventory.json': paths['inventory'], 'reports/final-gate.json': paths['gate'],
        'reports/export-settings.json': paths['export_settings'], 'reports/export-evidence.json': paths['export_evidence'],
        'reports/source-surfaces.json': paths['source_surfaces'], 'reports/glb-roundtrip.json': paths['roundtrip'],
        'reports/motion-contract.json': paths['motion_contract'], 'reports/motion-report.json': paths['motion_report'],
        'reports/presentation-provenance.json': paths['provenance'], 'reports/presentation-views.json': paths['views'],
        'reports/stills.json': paths['stills'], 'reports/fullhd-manifest.json': paths['media_manifest'],
        'reports/final-engineering-review.md': paths['design_notes'], 'reports/final-visual-review.md': paths['visual_review'],
        'reports/package-review.md': paths['package_review'],
        'design/layout.json': paths['layout'], 'design/interfaces.json': paths['interfaces'],
        'design/spec-B.json': paths['spec'], 'design/dimensions-contract-B.json': paths['contract'],
        'design/design-notes.md': paths['design_notes'], 'stl/manifest.json': paths['stl_manifest'],
    }.items():
        add_source(sources, relative, source)
    for name, image in images.items():
        add_source(sources, f'CK-001-{name}.png', image)
    for path in stl_paths:
        add_source(sources, f'stl/{path.name}', path)
    for name, path in review_paths.items():
        add_source(sources, f'reports/native-review/{name}.json', path)
    for name, path in references.items():
        add_source(sources, f'reference/{name}', path)
    if media_review_path:
        add_source(sources, 'reports/final-media-review.json', media_review_path)
        add_source(sources, 'reports/pixel-audit.json', pin_path(media_review['pixel_audit'], 'pixel audit'))

    review_assessment = review_docs['assessment']
    status = {
        'revision': 'B',
        'package_status': 'REVIEW_CANDIDATE',
        'share_quality_review': 'PRIME_FINAL_REVIEW_REQUIRED',
        'review': {'accepted': bool(review_assessment['accepted']), 'verdict': review_assessment['verdict'],
                   'reviewer': review_assessment['reviewer']},
        'scene_sha256': scene_sha, 'glb_sha256': glb_sha,
        'native_meshes': len(expected_names), 'gated_part_families': len(gate_ids), 'gated_part_ids': gate_ids,
        'roundtrip_frames': [1, 7, 60], 'roundtrip_surface_tolerance_mm': data['roundtrip']['tolerances_mm']['surface'],
        'max_roundtrip_surface_error_mm': max_surface,
        'native_render_pixels': [1920, 1080], 'stills': len(views), 'video_frames': 96, 'fps': 24,
        'media': 'PASS_NATIVE_FULLHD', 'motion': 'PASS_DECLARED_DIGITAL_SCOPE',
        'fit': 'PASS_DECLARED_DIGITAL_SCOPE', 'manufacture': 'BLOCKED',
        'contract': metrics,
        'physical_blockers': [
            'Keycap/switch insertion, retention force, tolerance stack, wear and process shrinkage need physical coupons.',
            'Knob D-flat fit and axial retention need physical shaft/knob testing.',
            'Encoder carrier threads, tightening torque and bonded-riser adhesive shear/peel/creep need physical qualification.',
            'PCB, encoder and USB footprints/netlist/ESD/power/firmware are not electrically qualified.',
            'Spacebar guide friction/rattle/wear and assembly bench testing remain open.',
            'Material/process, slicer/support, dimensional post-process and load/thermal evidence remain open.',
        ],
    }
    if media_review and review_assessment['accepted']:
        status['package_status'] = 'REVIEWED_DIGITAL_PROTOTYPE'
        status['share_quality_review'] = 'PASS_DECLARED_MEDIA_SCOPE'
        status['media_review_sha256'] = file_sha(media_review_path)
    return {
        'presentation': presentation, 'verification': verification, 'media': media, 'review': review,
        'destination': destination, 'archive': archive, 'paths': paths, 'sources': sources,
        'status': status, 'views': views, 'movie_name': movie.name, 'review_docs': review_docs,
        'reference_count': len(references),
    }


def bom(status, names):
    count = lambda prefix: sum(name.startswith(prefix) for name in names)
    c = status['contract']
    return {
        'revision': 'B', 'scene_sha256': status['scene_sha256'],
        'installed': [
            {'family': 'Keycaps with integral cross receivers', 'quantity': c['keys'],
             'evidence': f'{c["stem_insertion_mm"]:.1f} mm insertion; {c["receiver_ceiling_reserve_mm"]:.1f} mm ceiling reserve; physical retention unqualified'},
            {'family': 'Switch stem assemblies', 'quantity': count('RK_SWITCH_STEM_'),
             'evidence': f'virtual travel sampled through {c["key_travel_mm"]:.1f} mm; electrical/socket compatibility unqualified'},
            {'family': 'Spacebar guide sleeves', 'quantity': c['spacebar_guides'],
             'evidence': f'collision-free sampled travel; {c["spacebar_rest_engagement_mm"]:.2f} mm rest engagement; friction/rattle untested'},
            {'family': 'Slotted D-receiver knobs', 'quantity': c['knobs'],
             'evidence': f'{c["D_engagement_mm"]:.1f} mm nominal D engagement; physical retention unqualified'},
            {'family': 'PEC11R reference-envelope encoder bodies', 'quantity': count('RK_ENCODER_BODY_'),
             'evidence': 'mechanical envelope only; exact electrical suffix and fabricated circuit remain open'},
            {'family': 'Encoder carriers', 'quantity': count('RK_ENCODER_CARRIER_') - count('RK_ENCODER_CARRIER_SCREW_'),
             'evidence': 'modeled fastening path; thread strip, torque and bonded support strength unqualified'},
            {'family': 'USB daughterboard assembly', 'quantity': 1,
             'evidence': 'mechanically supported prototype envelope; exact connector footprint and electrical qualification open'},
            {'family': 'Main plate / diffuser / lower case', 'quantity': 3,
             'evidence': 'representative dimensional families pass the production geometry screen'},
            {'family': 'Feet', 'quantity': count('RK_FOOT_'), 'evidence': '14 x 5 x 2 mm digital envelopes'},
        ],
        'representative_gated_part_ids': status['gated_part_ids'],
        'boundary': 'The native mesh count is an assembly/export count. Only the declared representative families are production-gated; manufacture remains BLOCKED.',
    }


def render_readme(status, movie_name):
    c = status['contract']
    review = status['review']
    review_line = (f'Native eleven-still reference review is accepted with verdict `{review["verdict"]}`. '
                   'Package status remains **REVIEW_CANDIDATE** until prime completes the final share-quality review of the full media set.'
                   if review['accepted'] else
                   f'Native reference review is **not accepted**; current verdict is `{review["verdict"]}`. This package is a REVIEW_CANDIDATE.')
    if status['share_quality_review'] == 'PASS_DECLARED_MEDIA_SCOPE':
        review_line = ('The native eleven-still reference review and final decoded-media review have passed their '
                       'declared criteria. This is a **REVIEWED_DIGITAL_PROTOTYPE**, not a manufacturing release. '
                       'Camera framing, simplified markings and restrained RGB remain documented visual differences.')
    blockers = '\n'.join(f'- {item}' for item in status['physical_blockers'])
    return f'''# CK-001 revision B | native Blender delivery

Open `review.html` for the eleven native Full HD views and `{movie_name}`. The editable
scene is `CK-001.blend`; `CK-001.glb` is the verified exchange export. Both are bound to
scene SHA-256 `{status['scene_sha256']}` through the gate, inspection, export, Full HD
manifest and native review evidence.

## Declared digital result

The validated design envelope is {c['envelope_mm'][0]} × {c['envelope_mm'][1]} × {c['envelope_mm'][2]} mm with
{c['keys']} keys and {c['knobs']} knobs. Key travel is {c['key_travel_mm']:.1f} mm; actual fit evidence reports
{c['stem_insertion_mm']:.1f} mm stem insertion, {c['receiver_ceiling_reserve_mm']:.1f} mm receiver ceiling reserve,
{c['spacebar_guides']} parallel spacebar guides and {c['D_engagement_mm']:.1f} mm D-shaft engagement.

The GLB contains {status['native_meshes']} exported product meshes. All names, triangle counts,
bounds and sampled surfaces pass after reopening at frames 1, 7 and 60. This mesh count is
an exchange/assembly count, not a claim that every mesh is an independently printable part.
The production gate covers {status['gated_part_families']} declared representative families, listed in
`status.json` and `BOM.json`.

All eleven new delivery PNGs have actual 1920×1080 PNG headers and hashes matching the
Full HD manifest. The MP4 is recorded as 1920×1080, 96 fully decoded frames at 24 fps;
its 96 source frames were hash-checked during package preflight but are intentionally
excluded from this archive. The four files in `reference/` are byte-for-byte source
reference inputs used by the locked review. Their original lower resolutions are preserved;
the Full HD requirement applies only to newly rendered delivery media.

{review_line}

## Manufacture status: BLOCKED

{blockers}

The {status['gated_part_families']}-family representative STL set remains marked `UNRELEASED_DIGITAL_CHECK_ONLY` /
`NOT_MANUFACTURING_APPROVED` by its source manifest. No review result upgrades physical,
electrical, material or manufacturing evidence.

## Evidence layout

`reports/` contains the final gate, full-layout fit/layout inventory, export settings and
evidence, the complete source-surface proof used for GLB reopening, frames 1/7/60 reopen
comparison, presentation motion/provenance, Full HD manifests and the locked native-review
target/packet/critique/assessment. Those JSON files intentionally retain their historical
project source paths and hashes. `manifest.json` hashes every copied/generated package file
except itself, and the ZIP is fully CRC-read after creation.
'''


def render_html(status, views, movie_name):
    labels = [(name, human_label(name)) for name in views]
    figures = ''.join(
        f'<figure><img loading="lazy" src="CK-001-{html.escape(name)}.png" alt="{html.escape(label)}">'
        f'<figcaption>{html.escape(label)}</figcaption></figure>' for name, label in labels)
    poster = 'CK-001-exploded.png' if 'exploded' in views else f'CK-001-{labels[0][0]}.png'
    c = status['contract']
    review = status['review']
    review_text = (f'11-still review accepted · package candidate' if review['accepted']
                   else f'Review candidate · {review["verdict"]}')
    if status['share_quality_review'] == 'PASS_DECLARED_MEDIA_SCOPE':
        review_text = 'Native Full HD media reviewed · digital prototype'
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CK-001 Revision B</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0f1115;color:#f2f4f7;font:16px/1.55 system-ui,-apple-system,sans-serif}}main{{max-width:1440px;margin:auto;padding:48px 28px}}header{{display:flex;justify-content:space-between;gap:28px;align-items:end;flex-wrap:wrap}}small{{letter-spacing:.15em;color:#94a3b8}}h1{{font-size:46px;margin:8px 0}}p{{color:#b8c1cc}}a{{color:inherit;text-decoration:none;border:1px solid #424a56;border-radius:8px;padding:9px 13px;display:inline-block;margin:3px}}.meta{{display:flex;gap:34px;flex-wrap:wrap;margin:28px 0}}.meta b{{display:block;font-size:24px}}.meta span,figcaption{{color:#9eabb9;font-size:13px}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}}figure{{margin:0}}img,video{{width:100%;display:block;border-radius:12px;background:#d7d9dd}}figcaption{{padding:8px 2px 18px}}video{{margin-top:16px}}aside{{margin-top:30px;border:1px solid #5a5240;background:#242119;padding:22px;border-radius:12px;color:#e2d3ae}}code{{color:#d4d9df}}footer{{margin-top:28px;color:#8b98a7;font-size:13px}}@media(max-width:760px){{main{{padding:28px 16px}}h1{{font-size:34px}}.grid{{grid-template-columns:1fr}}}}
</style><main><header><div><small>DESIGN OS / BLENDER NATIVE</small><h1>CK-001 · Revision B</h1><p>{html.escape(review_text)}</p></div><div><a href="CK-001.blend">Blender scene</a><a href="CK-001.glb">GLB 3D file</a><a href="README.md">Evidence notes</a><a href="BOM.json">BOM</a></div></header>
<div class="meta"><div><b>{c['envelope_mm'][0]} × {c['envelope_mm'][1]} × {c['envelope_mm'][2]} mm</b><span>validated envelope</span></div><div><b>{c['keys']} keys / {c['knobs']} knobs</b><span>installed layout</span></div><div><b>1920 × 1080</b><span>11 native Blender stills + Full HD video</span></div><div><b>{status['gated_part_families']} families</b><span>representative geometry gate</span></div></div>
<h2>Native Full HD gallery</h2><div class="grid">{figures}</div><h2>Animation</h2><video controls loop preload="metadata" poster="{html.escape(poster)}"><source src="{html.escape(movie_name)}" type="video/mp4"></video>
<aside><strong>Manufacture remains blocked.</strong><br>Digital geometry, sampled interfaces, export/reopen fidelity and native media have evidence. Physical retention, adhesive/thread strength, electrical design, material/process behavior and bench testing remain open. The review assessment is shown exactly as recorded; a candidate verdict is not presented as acceptance.</aside>
<footer>Source reference files are preserved byte-for-byte under <code>reference/</code>. Full evidence, historical source paths and hashes are under <code>reports/</code>.</footer></main></html>'''


def copy_package(bundle):
    destination, archive = bundle['destination'], bundle['archive']
    destination.parent.mkdir(parents=True, exist_ok=True)
    archive.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(exist_ok=False)
    records = []
    for relative, source in sorted(bundle['sources'].items()):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        need(not target.exists(), f'refusing overwrite inside package: {target}')
        shutil.copy2(source['path'], target)
        need(file_sha(target) == source['sha256'], f'copied byte hash mismatch: {relative}')
        records.append({'file': relative, 'sha256': source['sha256'], 'bytes': source['bytes'],
                        'source': source['path'].relative_to(ROOT.resolve()).as_posix()})

    status = bundle['status']
    names = load_json(bundle['paths']['roundtrip'])['expected_mesh_names']
    generated = {
        'BOM.json': bom(status, names), 'status.json': status,
    }
    for relative, value in generated.items():
        write(destination / relative, value)
    text_files = {
        'README.md': render_readme(status, bundle['movie_name']),
        'review.html': render_html(status, bundle['views'], bundle['movie_name']),
        'reference/ORIGINAL-INPUTS.md': (
            '# Original reference inputs\n\n'
            'Files in this directory are byte-for-byte copies of the source-reference files pinned by the locked native review. '
            'They are preserved at their original local resolution and are excluded from the 1920×1080 requirement for newly rendered delivery media.\n'),
    }
    for relative, text in text_files.items():
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as handle:
            handle.write(text)
    for relative in (*generated, *text_files):
        path = destination / relative
        records.append({'file': relative, 'sha256': file_sha(path), 'bytes': path.stat().st_size,
                        'source': 'generated from preflight-validated revision-B evidence'})

    manifest = {
        'schema_version': 2, 'product': 'CK-001', 'revision': 'B',
        'scene_sha256': status['scene_sha256'], 'glb_sha256': status['glb_sha256'],
        'source_paths_are_historical': True, 'files': sorted(records, key=lambda row: row['file']),
        'status': status,
    }
    write(destination / 'manifest.json', manifest)
    for row in manifest['files']:
        path = destination / row['file']
        need(path.stat().st_size == row['bytes'] and file_sha(path) == row['sha256'],
             f'manifest verification failed after copy: {row["file"]}')

    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as handle:
        for path in sorted(p for p in destination.rglob('*') if p.is_file()):
            handle.write(path, 'CK-001/' + path.relative_to(destination).as_posix())
    expected_members = {'CK-001/' + path.relative_to(destination).as_posix()
                        for path in destination.rglob('*') if path.is_file()}
    with zipfile.ZipFile(archive) as handle:
        need(set(handle.namelist()) == expected_members, 'ZIP member set does not match package files')
        need(handle.testzip() is None, 'ZIP CRC verification failed')
    return manifest


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--presentation', required=True, help='presentation attempt directory containing keyboard.blend')
    parser.add_argument('--verification', required=True, help='verification steps directory (or run directory containing steps/)')
    parser.add_argument('--media', required=True, help='Full HD media attempt directory')
    parser.add_argument('--review', required=True, help='locked native review directory with assessment.json')
    parser.add_argument('--destination', required=True, help='new delivery directory, project-root bounded')
    parser.add_argument('--archive', required=True, help='new .zip archive, project-root bounded')
    parser.add_argument('--media-review', help='attributed final media review bound to this scene, manifest and decoded video')
    parser.add_argument('--preflight-only', action='store_true', help='validate all inputs/hashes without writing package files')
    return parser.parse_args()


def main():
    args = parse_args()
    bundle = preflight(args)
    if args.preflight_only:
        print(json.dumps({'status': 'PREFLIGHT_PASS', 'scene_sha256': bundle['status']['scene_sha256'],
                          'native_meshes': bundle['status']['native_meshes'],
                          'gated_part_families': bundle['status']['gated_part_families'],
                          'review': bundle['status']['review'], 'files_to_copy': len(bundle['sources'])}))
        return 0
    manifest = copy_package(bundle)
    print(json.dumps({'status': 'PACKAGE_COMPLETE', 'destination': str(bundle['destination']),
                      'archive': str(bundle['archive']), 'archive_sha256': file_sha(bundle['archive']),
                      'manifest_files': len(manifest['files']), 'package_status': bundle['status']['package_status']}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (PackageError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({'status': 'ERROR', 'message': str(exc)}), file=sys.stderr)
        sys.exit(2)
