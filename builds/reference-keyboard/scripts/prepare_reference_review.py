"""Bind available owner-reference copies to native Full-HD proofs and actual checks.

The renderer provides camera/frame context. A separate reviewer must author the
findings; this program never decides image likeness or supplies a positive verdict.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project import BUILD, ROOT, write, sha, spec_path
from native_review.evidence import file_pin, value_hash, png_pin
from native_review.packets import prepare, critique_template


def main():
    presentation, verification, media = [Path(p).resolve() for p in sys.argv[1:4]]
    destination = BUILD / 'runs' / sys.argv[4]
    for path in (presentation, verification, media, destination):
        assert path.is_relative_to(BUILD), path
    assert not destination.exists(), destination
    scene = presentation / 'keyboard.blend'
    gate_path = verification / 'final-gate/attempt-0001/final-gate.json'
    fit_path = verification / 'inspect/attempt-0001/fit-report.json'
    roundtrip_path = verification / 'reopen/attempt-0001/glb-roundtrip.json'
    gate, fit, exported = [json.loads(p.read_text()) for p in (gate_path, fit_path, roundtrip_path)]
    stills = json.loads((media / 'stills.json').read_text())
    assert gate['inputs']['scene_sha256'] == stills['scene_sha256'] == fit['scene_sha256'] == sha(scene)
    assert not gate['failed'] and not gate['required_checks_missing']
    assert exported['pass'] and exported['mesh_names_match']
    refdir = BUILD / 'delivery/r01/reference'
    refs = {key: file_pin(ROOT, refdir / name) for key, name in {
        'photo': 'original-work-louder.png', 'blueprint': 'blueprint-rev01.png',
        'catalog': 'parts-catalog-rev01.png', 'turnaround': '360-product-view.png',
    }.items()}
    reference_for = {'hero': 'photo', 'top': 'blueprint', 'exploded': 'catalog',
                     'knob-detail': 'turnaround', 'key-detail': 'turnaround', 'bottom': 'turnaround',
                     'receiver': 'catalog', 'spacebar-guides': 'catalog', 'D-receiver': 'catalog',
                     'encoder-mount': 'catalog', 'usb-mount': 'catalog'}
    views, proofs = [], {}
    for name, ref in reference_for.items():
        image = media / ('CK-001-' + name + '.png')
        pin = png_pin(ROOT, image, [1920, 1080])
        assert pin['sha256'] == stills['views'][name]['sha256']
        views.append({'id': name, 'target': refs[ref], 'proof_size': [1920, 1080],
                      'capture': stills['views'][name]['capture']})
        proofs[name] = image
    features = [
        ('control-layout', ['hero', 'top'], 'Five knobs in left/rear-trio/right arrangement, compact key grid, rear macro strip and wide spacebar remain readable.', 'Missing/extra knob, lost macro strip or wide spacebar, or gross layout divergence.'),
        ('key-form-and-legends', ['hero', 'key-detail'], 'Rounded charcoal key faces carry readable white legends; revision-B visible skirt is shorter than the old full-height wall.', 'Illegible/floating letters, lost rounded form, visibly inconsistent key families.'),
        ('slotted-knobs', ['hero', 'knob-detail'], 'Silver cylindrical controls retain actual recessed indicator channels, visible in the close-up.', 'A flat painted line replaces the channel, slots disappear in the close-up, or geometry breaks.'),
        ('layered-body-and-rgb', ['hero', 'exploded'], 'Dark mounting plate, separate PCB, translucent acrylic RGB perimeter and silver lower body remain distinct.', 'A layer is absent or fused visually; RGB is absent; gross intersections or cropped assembly.'),
        ('underside', ['bottom'], 'Silver underside and four separate dark feet are visible, without added certification claims.', 'Missing feet, hidden underside, gross crop or unreadable lighting.'),
        ('modeled-interfaces', ['receiver', 'spacebar-guides', 'D-receiver'], 'Revision-B declared design additions are visible: real cross receiver, two integral guide pins, stepped D receiver.', 'A promised opening or guide is missing, hidden or substituted by a flat surface. This is design inspection, not proof of source-photo hidden geometry.'),
        ('supported-hardware', ['encoder-mount', 'usb-mount'], 'Encoder carrier/shaft/hardware and mounted USB assembly are inspectable as the declared prototype design.', 'Required support geometry is absent, occluded beyond useful inspection or visibly disconnected. No electrical or load qualification is inferred.'),
    ]
    target = {'version': 1, 'purpose': 'both', 'target_revision': 'B-local-reference-feature-review-1',
              'max_rounds': 3, 'views': views,
              'features': [{'id': i, 'views': v, 'expectation': e, 'falsifier': f} for i, v, e, f in features],
              'scope': 'Owner-requested reconstruction and declared revision-B mechanical adaptations. Camera poses differ from source sheets; record visible deviations, not a similarity score.'}
    candidates = {'scene': scene, 'layout': BUILD / 'layout.json', 'interfaces': BUILD / 'interfaces.json',
                  'spec': spec_path(), 'gate': gate_path, 'fit': fit_path, 'roundtrip': roundtrip_path,
                  'renderer': BUILD / 'scripts/fullhd.py', 'stills': media / 'stills.json'}
    pins = {k: file_pin(ROOT, p) for k, p in candidates.items()}
    checks = [
        {'id': 'gated-part-failures', 'value': len(gate['failed']), 'status': 'pass'},
        {'id': 'full-key-travel-collisions', 'value': fit['switch_keycap_overlap']['collision_pairs'], 'status': 'pass' if fit['switch_keycap_overlap']['collision_pairs'] == 0 else 'fail'},
        {'id': 'D-pair-negative-controls', 'value': int(fit['interfaces']['encoder_dshaft']['negative_controls_detect_collision']), 'status': 'pass' if fit['interfaces']['encoder_dshaft']['negative_controls_detect_collision'] else 'fail'},
        {'id': 'reimported-meshes', 'value': len(exported['expected_mesh_names']), 'status': 'pass'},
        {'id': 'native-fullhd-stills', 'value': len(views), 'status': 'pass'},
    ]
    destination.mkdir()
    write(destination / 'references.json', {'references': refs, 'provenance': 'Local copies visually cross-checked against the owner images in this conversation; hash identifies these local bytes, not original upload transport or vendor certification.'})
    write(destination / 'target.json', target)
    write(destination / 'numeric.json', {'candidate_sha256': value_hash(pins), 'checks': checks,
          'status': 'pass' if all(c['status'] == 'pass' for c in checks) else 'fail'})
    packet = prepare(ROOT, destination / 'target.json', candidates, proofs, destination / 'numeric.json', 'prime-native-builder')
    write(destination / 'packet.json', packet)
    write(destination / 'critique.json', critique_template(ROOT, destination / 'packet.json'))
    print(json.dumps({'packet': str(destination / 'packet.json'), 'status': 'awaiting_actual_independent_review', 'views': len(views)}))


if __name__ == '__main__':
    main()
