"""Prepare a calibrated coupon's critic packet; never fabricate a visual verdict.

Run after native-iteration-pipeline.json. Round 1 reviews candidate, round 2 reviews
revision and requires a saved assessment-r01.json from actual critic findings.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from boilerplates.bp_parametric_contract import source_evidence_current
from native_review.evidence import file_pin, load, path_at, write_new
from native_review.packets import critique_template, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--round', type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    run = path_at(ROOT, args.run_dir)
    reference = run / 'steps/reference/attempt-0001'
    selected = 'candidate' if args.round == 1 else 'revision'
    candidate = run / 'steps' / selected / 'attempt-0001'
    original = load(ROOT, reference / 'summary.json')
    summary = load(ROOT, candidate / 'summary.json')
    normalized = load(ROOT, candidate / 'contract.json')
    if not source_evidence_current(summary['source_evidence'], ROOT, contract=normalized):
        raise ValueError('coupon source evidence changed; use a new run')
    if original['capture'] != summary['capture']:
        raise ValueError('reference and candidate capture context differ')
    reviews = run / 'reviews'
    target = reviews / 'target.json'
    expected = {
        'version': 1, 'purpose': 'render-only', 'target_revision': 'collar-coupon-v2',
        'max_rounds': 3,
        'views': [{'id': 'hero', 'target': file_pin(ROOT, reference / 'proof.png'),
                   'proof_size': [256, 256], 'capture': original['capture']}],
        'features': [
            {'id': 'two-collars', 'views': ['hero'],
             'expectation': 'Two separate gold collars surround the blue vertical body at the reference heights.',
             'falsifier': 'Either gold collar is absent, merged into the other, or displaced from its reference location.'},
            {'id': 'body-and-base', 'views': ['hero'],
             'expectation': 'A blue vertical cylindrical body stands centered on a wider round base matching the target.',
             'falsifier': 'The body is missing, visibly tilted or detached, or the broad round base is absent.'},
            {'id': 'framing', 'views': ['hero'],
             'expectation': 'The entire coupon is visible at the same orientation and apparent scale as the target.',
             'falsifier': 'Any outer part is cropped or the view angle/scale differs enough to hide a contracted feature.'}
        ]
    }
    if target.exists():
        if load(ROOT, target) != expected:
            raise ValueError('locked target differs; do not overwrite it')
    else:
        if args.round != 1:
            raise ValueError('round 2 requires the existing locked target')
        write_new(ROOT, target, expected)
    previous = reviews / 'assessment-r01.json' if args.round == 2 else None
    packet = prepare(ROOT, target, {k: p['path'] for k, p in summary['candidate_pins'].items()},
                     {'hero': str(candidate / 'proof.png')}, candidate / 'numeric.json',
                     'native-coupon-builder', args.round, previous)
    packet_path = reviews / f'packet-r{args.round:02}.json'
    write_new(ROOT, packet_path, packet)
    template = reviews / f'critique-r{args.round:02}.json'
    write_new(ROOT, template, critique_template(ROOT, packet_path))
    print(json.dumps({'packet': str(packet_path), 'critique_template': str(template),
                      'packet_sha256': file_pin(ROOT, packet_path)['sha256'],
                      'review_status': 'PENDING_ACTUAL_REVIEW'}))


if __name__ == '__main__':
    main()
