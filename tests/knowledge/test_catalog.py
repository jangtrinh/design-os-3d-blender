"""Behavior contracts for the local knowledge catalog; no Blender or network."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('catalog', SCRIPTS / 'blender-knowledge.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class CatalogContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = {'version': 1, 'examples': [], 'annotations': {},
                       'portable': [], 'foundations': ['knowledge/a.md'],
                       'workflows': {'sample': {'purpose': 'fixture',
                           'required': ['knowledge/b.md'], 'supplemental': [],
                           'concepts': [], 'adapters': [], 'steps': ['Read'],
                           'gates': ['Assert actual output'], 'limitations': ['Fixture']}}}
        self.write('knowledge/a.md', '---\nname: alpha\nloads_with: [beta]\n---\n# Foundation\n')
        self.write('knowledge/b.md', '---\nname: beta\nloads_with: [alpha]\n---\n# Robot joint\nkinematics\n')
        self.write('research/rodin.md', '# Rodin\nrobot joint kinematics\n')
        self.save_config()

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def save_config(self):
        self.write('knowledge/catalog-config.json', json.dumps(self.config))

    def test_build_is_deterministic_and_cycles_are_bounded(self):
        first = api.make_catalog(self.root)
        self.assertEqual(first, api.make_catalog(self.root))
        pack = api.route(first, 'sample')
        self.assertEqual([x['path'] for x in pack['required']], ['knowledge/a.md', 'knowledge/b.md'])
        self.assertEqual(pack['related'], [])
        self.assertEqual(first['dependency_edges'], 2)

    def test_missing_dependency_is_error(self):
        self.write('knowledge/b.md', '---\nname: beta\nloads_with: [absent]\n---\n')
        with self.assertRaisesRegex(ValueError, 'dependency'):
            api.make_catalog(self.root)

    def test_ambiguous_name_is_error(self):
        self.write('knowledge/c.md', '---\nname: beta\n---\n# Collision\n')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            api.make_catalog(self.root)

    def test_stale_added_modified_deleted_are_detected(self):
        api.build(self.root)
        for change in ('add', 'modify', 'delete'):
            if change == 'add': self.write('research/new.md', '# New\n')
            if change == 'modify': self.write('knowledge/b.md', '---\nname: beta\n---\n# Changed\n')
            if change == 'delete': (self.root / 'research/new.md').unlink()
            with self.assertRaisesRegex(ValueError, 'stale'):
                api.checked_catalog(self.root)
            api.build(self.root)

    def test_default_search_excludes_restricted_but_all_labels_it(self):
        catalog = api.make_catalog(self.root)
        active = api.search(self.root, catalog, 'robot joint', 'active', 10)
        self.assertNotIn('research/rodin.md', [x['path'] for x in active])
        archive = api.search(self.root, catalog, 'robot joint', 'all', 10)
        row = next(x for x in archive if x['path'] == 'research/rodin.md')
        self.assertEqual(row['use'], 'archive-only')

    def test_mixed_legacy_generation_guides_are_archive_only(self):
        for name in ('oss-tooling.md', 'how-image-to-3d-works.md'):
            self.write('research/' + name, '# Pipeline\nUse rented generation service\n')
        catalog = api.make_catalog(self.root)
        hits = api.search(self.root, catalog, 'rented generation', 'active', 10)
        self.assertEqual(hits, [])
        all_hits = api.search(self.root, catalog, 'rented generation', 'all', 10)
        self.assertEqual(len(all_hits), 2)
        self.assertTrue(all(r['use'] == 'archive-only' for r in all_hits))

    def test_skill_mirrors_deduplicated_and_owned_drift_fails(self):
        for prefix in ('.agents', '.claude'):
            self.write(prefix + '/skills/blender-agent-core/SKILL.md', '# Core\n')
        catalog = api.make_catalog(self.root)
        paths = [r['path'] for r in catalog['records']]
        self.assertIn('.agents/skills/blender-agent-core/SKILL.md', paths)
        self.assertFalse(any(p.startswith('.claude') for p in paths))
        self.write('.claude/skills/blender-agent-core/SKILL.md', '# drift\n')
        with self.assertRaisesRegex(ValueError, 'mirror'):
            api.make_catalog(self.root)

    def test_imported_mirror_drift_is_visible(self):
        self.write('.agents/skills/img2threejs/SKILL.md', '# Imported\n')
        self.write('.claude/skills/img2threejs/SKILL.md', '# Different\n')
        catalog = api.make_catalog(self.root)
        self.assertTrue(catalog['warnings'])

    def test_missing_profile_source_and_restricted_required_fail(self):
        self.config['workflows']['sample']['required'] = ['absent.md']
        self.save_config()
        with self.assertRaisesRegex(ValueError, 'workflow'):
            api.make_catalog(self.root)
        self.config['workflows']['sample']['required'] = ['research/rodin.md']
        self.save_config()
        with self.assertRaisesRegex(ValueError, 'restricted'):
            api.make_catalog(self.root)

    def test_escape_and_symlink_refused(self):
        self.config['examples'] = ['../outside.py']
        self.save_config()
        with self.assertRaises(ValueError): api.make_catalog(self.root)
        self.config['examples'] = []
        self.save_config()
        (self.root / 'knowledge/link.md').symlink_to(self.root / 'knowledge/a.md')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            api.make_catalog(self.root)

    def test_annotation_staleness_is_visible(self):
        self.config['annotations']['knowledge/b.md'] = {
            'reviewed_sha256': 'old', 'caution': 'Check joint axes'}
        self.save_config()
        row = next(r for r in api.make_catalog(self.root)['records'] if r['path'] == 'knowledge/b.md')
        self.assertEqual(row['annotation_revision'], 'changed-since-review')

    def test_owned_mirror_extra_file_is_drift(self):
        for prefix in ('.agents', '.claude'):
            self.write(prefix + '/skills/blender-agent-core/SKILL.md', '# Core\n')
        self.write('.claude/skills/blender-agent-core/obsolete.md', '# Old route\n')
        with self.assertRaisesRegex(ValueError, 'mirror'):
            api.make_catalog(self.root)

    def test_show_can_start_after_line_200(self):
        self.write('knowledge/long.md', '# Long\n' + 'body\n' * 450)
        api.build(self.root)
        import subprocess
        result = subprocess.run([sys.executable, str(SCRIPTS / 'blender-knowledge.py'),
            '--root', str(self.root), 'show', 'knowledge/long.md',
            '--start', '400', '--lines', '5'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['excerpt'][0]['line'], 400)

    def test_invalid_metadata_is_not_silently_dropped(self):
        self.write('knowledge/b.md', '---\nname: beta\nloads_with: [alpha\n---\n')
        with self.assertRaises(ValueError): api.make_catalog(self.root)


if __name__ == '__main__':
    unittest.main()
