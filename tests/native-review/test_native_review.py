"""Contract fixtures for evidence binding, not a substitute for visual review."""
import binascii
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import subprocess
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from native_review.decision import assess
from native_review.evidence import file_pin, path_at, value_hash, write_new
from native_review.packets import critique_template, prepare


def png(value=128):
    def chunk(name, payload):
        return (struct.pack('>I', len(payload)) + name + payload
                + struct.pack('>I', binascii.crc32(name + payload) & 0xffffffff))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' + bytes([value] * 6)) * 2)) + chunk(b'IEND', b''))


class ReviewContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        for name in ('target.png', 'proof.png'):
            (self.root / name).write_bytes(png())
        (self.root / 'candidate.bin').write_bytes(b'fixture revision 1')
        self.target = {'version': 1, 'purpose': 'render-only', 'target_revision': 'r1',
                       'max_rounds': 3, 'views': [{'id': 'front', 'target': self.pin('target.png'),
                       'proof_size': [2, 2], 'capture': {'camera': 'front', 'frame': 1,
                       'projection': 'ORTHO', 'location': [0, 0, 10], 'target': [0, 0, 0],
                       'resolution': [2, 2], 'ortho_scale': 8.0, 'clip_start': 0.1, 'clip_end': 100}}],
                       'features': [{'id': 'outline', 'views': ['front'],
                                     'expectation': 'Two visible shoulders',
                                     'falsifier': 'A missing shoulder'}]}
        self.put('target.json', self.target)
        self.numeric = {'status': 'pass', 'candidate_sha256': value_hash({'scene': self.pin('candidate.bin')}),
                        'checks': [{'id': 'dimension', 'status': 'pass', 'value': 3.0}]}
        self.put('numeric.json', self.numeric)

    def pin(self, name):
        return file_pin(self.root, name)

    def put(self, name, data):
        (self.root / name).write_text(json.dumps(data))

    def packet(self, number=1, previous=None):
        body = prepare(self.root, 'target.json', {'scene': 'candidate.bin'}, {'front': 'proof.png'},
                       'numeric.json', 'builder', number, previous)
        name = f'packet-{number}.json'
        self.put(name, body)
        return name

    def critique(self, packet, status='pass', reviewer='independent-critic'):
        body = critique_template(self.root, packet)
        body['reviewer'] = reviewer
        body['findings'][0].update(status=status, observation='Observed the stated outline',
                                    action='Rebuild the absent shoulder', cause='code')
        name = packet.replace('packet', 'critique')
        self.put(name, body)
        return name

    def test_current_evidence_can_pass_but_does_not_certify_manufacture(self):
        packet = self.packet()
        result = assess(self.root, packet, self.critique(packet))
        self.assertTrue(result['accepted'])
        self.assertEqual(result['verdict'], 'stop')
        self.assertEqual(result['manufacture'], 'NOT_REQUESTED')

    def test_print_purpose_never_inherits_manufacturing_acceptance(self):
        self.target['purpose'] = 'both'
        self.put('target.json', self.target)
        packet = self.packet()
        self.assertEqual(assess(self.root, packet, self.critique(packet))['manufacture'], 'BLOCKED')

    def test_numeric_failure_blocks_visual_pass(self):
        self.numeric['status'] = 'fail'
        self.numeric['checks'][0]['status'] = 'fail'
        self.put('numeric.json', self.numeric)
        packet = self.packet()
        result = assess(self.root, packet, self.critique(packet))
        self.assertFalse(result['accepted'])
        self.assertEqual(result['numeric_failures'], ['dimension'])

    def test_unknown_is_never_accepted(self):
        packet = self.packet()
        result = assess(self.root, packet, self.critique(packet, 'unknown'))
        self.assertFalse(result['accepted'])
        self.assertEqual(result['verdict'], 'request-input')

    def test_same_builder_cannot_sign_as_independent_reviewer(self):
        packet = self.packet()
        with self.assertRaisesRegex(ValueError, 'independent'):
            assess(self.root, packet, self.critique(packet, reviewer='builder'))

    def test_empty_template_cannot_count_as_review(self):
        packet = self.packet()
        self.put('empty.json', critique_template(self.root, packet))
        with self.assertRaises(ValueError):
            assess(self.root, packet, 'empty.json')

    def test_changed_source_or_proof_invalidates_a_pass(self):
        for file, data in [('candidate.bin', b'changed geometry'), ('proof.png', png(64)),
                           ('target.png', png(32)), ('numeric.json', b'{}')]:
            with self.subTest(file=file):
                packet = self.packet()
                critique = self.critique(packet)
                original = (self.root / file).read_bytes()
                (self.root / file).write_bytes(data)
                with self.assertRaisesRegex(ValueError, 'stale'):
                    assess(self.root, packet, critique)
                (self.root / file).write_bytes(original)

    def test_incomplete_or_duplicate_findings_rejected(self):
        packet = self.packet()
        critique = self.critique(packet)
        original = json.loads((self.root / critique).read_text())
        for findings in ([], original['findings'] * 2):
            body = copy.deepcopy(original)
            body['findings'] = findings
            self.put(critique, body)
            with self.assertRaises(ValueError):
                assess(self.root, packet, critique)

    def test_critique_cannot_be_reused_for_different_packet(self):
        packet = self.packet()
        critique = self.critique(packet)
        body = json.loads((self.root / packet).read_text())
        body['author'] = 'another-builder'
        self.put(packet, body)
        with self.assertRaisesRegex(ValueError, 'bound'):
            assess(self.root, packet, critique)

    def test_repeated_gap_changes_approach_then_stops_at_budget(self):
        previous = None
        for number in (1, 2, 3):
            packet = self.packet(number, previous)
            result = assess(self.root, packet, self.critique(packet, 'fail'))
            self.assertFalse(result['accepted'])
            self.assertEqual(result['change_approach'], number > 1)
            if number == 3:
                self.assertEqual(result['verdict'], 'request-input')
            previous = f'assessment-{number}.json'
            self.put(previous, result)

    def test_new_target_cannot_reuse_prior_round(self):
        packet = self.packet()
        self.put('previous.json', assess(self.root, packet, self.critique(packet, 'fail')))
        self.target['target_revision'] = 'r2'
        self.put('target.json', self.target)
        with self.assertRaisesRegex(ValueError, 'different target'):
            self.packet(2, 'previous.json')

    def test_invalid_proof_and_target_alias_rejected(self):
        (self.root / 'proof.png').write_bytes(b'\x89PNG\r\n\x1a\n')
        with self.assertRaises(ValueError):
            self.packet()
        with self.assertRaisesRegex(ValueError, 'separate'):
            prepare(self.root, 'target.json', {'scene': 'candidate.bin'}, {'front': 'target.png'},
                    'numeric.json', 'builder')

    def test_wrong_numeric_binding_rejected(self):
        self.numeric['candidate_sha256'] = '0' * 64
        self.put('numeric.json', self.numeric)
        with self.assertRaisesRegex(ValueError, 'bound'):
            self.packet()

    def test_claimed_numeric_pass_needs_a_finite_measurement(self):
        for value in (None, True, 'measured'):
            self.numeric['checks'][0]['value'] = value
            self.put('numeric.json', self.numeric)
            with self.assertRaises(ValueError):
                self.packet()

    def test_escaped_paths_symlinks_and_existing_output_rejected(self):
        with self.assertRaises(ValueError):
            path_at(self.root, '../outside.json')
        (self.root / 'alias').symlink_to(self.root / 'candidate.bin')
        with self.assertRaises(ValueError):
            file_pin(self.root, 'alias')
        with self.assertRaises(FileExistsError):
            write_new(self.root, 'target.json', {})

    def test_missing_previous_round_and_extra_budget_rejected(self):
        for number in (2, 4):
            with self.assertRaises(ValueError):
                self.packet(number)

    def test_capture_requires_camera_frame_and_projection_context(self):
        original = copy.deepcopy(self.target['views'][0]['capture'])
        for bad in ({'foo': 1}, original | {'resolution': [4, 4]},
                    original | {'clip_end': 0.01}, original | {'frame': True}):
            self.target['views'][0]['capture'] = bad
            self.put('target.json', self.target)
            with self.assertRaises(ValueError):
                self.packet()

    @unittest.skipUnless(Path('/Applications/Blender.app/Contents/MacOS/Blender').is_file(), 'Blender missing')
    def test_native_partial_coupon_output_is_preserved_before_scene_mutation(self):
        repo = Path(__file__).resolve().parents[2]
        proc = subprocess.run(['bash', 'scripts/headless-run.sh',
                               'tests/native-review/fixtures/coupon_collision.py'],
                              cwd=repo, capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('"preserved": 1', proc.stdout)


if __name__ == '__main__':
    unittest.main()
