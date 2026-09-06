"""Knowledge changes require explicit compilation and stale-input checks."""
import json
from pathlib import Path
import runpy
import unittest
import test_catalog as fixtures
api, SCRIPTS = fixtures.api, fixtures.SCRIPTS

pipe = runpy.run_path(str(SCRIPTS / 'knowledge-pipeline.py'))


class EvolutionContract(unittest.TestCase):
    setUp = fixtures.CatalogContract.setUp
    tearDown = fixtures.CatalogContract.tearDown
    write = fixtures.CatalogContract.write
    save_config = fixtures.CatalogContract.save_config
    def add_topic(self):
        self.write('research/domain/detail.md', '# Detail\nUseful topic\n')
        h = api.digest((self.root / 'research/domain/detail.md').read_bytes())
        self.config['workflows']['sample']['topics'] = {'detail': {
            'when': 'A task needs detail', 'sources': ['research/domain/detail.md'],
            'steps': ['Measure input'], 'gates': ['Assert task result'],
            'limitations': ['Not certified'], 'review': {
                'kind': 'static-routing-review', 'by': 'fixture reviewer',
                'source_hashes': {'research/domain/detail.md': h}}}}
        self.save_config()

    def test_topic_selection_is_bounded_and_source_bound(self):
        self.add_topic()
        c = api.make_catalog(self.root)
        pack = api.route(c, 'sample', 'detail')
        self.assertEqual(len(pack['required']), 2)
        self.assertEqual(len(pack['topic_sources']), 1)
        self.write('research/domain/detail.md', '# Changed\n')
        changed = api.make_catalog(self.root)
        with self.assertRaisesRegex(ValueError, 'review'):
            api.route(changed, 'sample', 'detail')

    def test_publish_rejects_changed_source(self):
        self.add_topic()
        bundle = pipe['prepare'](self.root)
        self.write('knowledge/b.md', '---\nname: beta\nloads_with: [alpha]\n---\n# Changed\n')
        with self.assertRaisesRegex(ValueError, 'source'):
            pipe['publish'](self.root, bundle, pipe['plan_digest'](bundle))

    def test_publish_rejects_wrong_digest_and_output_drift(self):
        bundle = pipe['prepare'](self.root)
        with self.assertRaisesRegex(ValueError, 'digest'):
            pipe['publish'](self.root, bundle, 'wrong')
        self.write(pipe['PLAYBOOK'], 'External edit\n')
        with self.assertRaisesRegex(ValueError, 'output'):
            pipe['publish'](self.root, bundle, pipe['plan_digest'](bundle))

    def test_publish_is_deterministic_idempotent_and_never_executes_sources(self):
        self.add_topic()
        self.write('scripts/untrusted.py', "raise RuntimeError('Never run source')\n")
        a = pipe['prepare'](self.root); b = pipe['prepare'](self.root)
        self.assertEqual(a, b)
        result = pipe['publish'](self.root, a, pipe['plan_digest'](a))
        self.assertEqual(result['status'], 'published')
        self.assertEqual(pipe['publish'](self.root, a, pipe['plan_digest'](a)), result)
        self.assertTrue((self.root / pipe['PLAYBOOK']).is_file())
        self.assertEqual(pipe['scan'](self.root)['added'], [])
        api.checked_catalog(self.root)

    def test_nested_boilerplate_is_indexed_without_import(self):
        path = 'scripts/boilerplates/nested/unsafe.py'
        self.write(path, "raise RuntimeError('Do not import')\n")
        c = api.make_catalog(self.root)
        self.assertIn(path, {r['path'] for r in c['records']})
        self.assertIn(path, pipe['scan'](self.root)['added'])

    def test_scan_does_not_report_existing_mirrors_as_deleted(self):
        for prefix in ('.agents', '.claude'):
            self.write(prefix + '/skills/blender-agent-core/SKILL.md', '# Core\n')
        a = pipe['prepare'](self.root)
        pipe['publish'](self.root, a, pipe['plan_digest'](a))
        self.assertEqual(pipe['scan'](self.root)['removed'], [])

    def test_build_alone_does_not_erase_unpublished_change(self):
        a = pipe['prepare'](self.root)
        pipe['publish'](self.root, a, pipe['plan_digest'](a))
        self.write('research/domain/new.md', '# New\n')
        api.build(self.root)
        self.assertIn('research/domain/new.md', pipe['scan'](self.root)['added'])

    def test_scan_reports_removal_even_when_catalog_invalid(self):
        api.build(self.root)
        (self.root / 'knowledge/b.md').unlink()
        scan = pipe['scan'](self.root)
        self.assertIn('knowledge/b.md', scan['removed'])
        self.assertIn('dependency', scan['validation_error'])

    def test_interrupted_publish_can_resume_without_overwriting_external_edit(self):
        from unittest.mock import patch
        a = pipe['prepare'](self.root)
        with patch.dict(pipe['api'], {'build': lambda root: (_ for _ in ()).throw(RuntimeError('interrupted'))}):
            with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                pipe['publish'](self.root, a, pipe['plan_digest'](a))
        self.assertTrue((self.root / pipe['PLAYBOOK']).is_file())
        self.assertFalse((self.root / pipe['RECEIPT']).exists())
        pipe['publish'](self.root, a, pipe['plan_digest'](a))
        self.write(pipe['PLAYBOOK'], 'Externally curated content\n')
        with self.assertRaisesRegex(ValueError, 'output'):
            pipe['publish'](self.root, a, pipe['plan_digest'](a))

    def test_rehashed_fabricated_output_is_not_published(self):
        a = pipe['prepare'](self.root)
        a['content'] = 'Invented unreviewed directions'
        with self.assertRaisesRegex(ValueError, 'compiler'):
            pipe['publish'](self.root, a, pipe['plan_digest'](a))

    def test_scan_reports_deleted_curated_example(self):
        self.write('builds/sample/example.md', '# Example\n')
        self.config['examples'] = ['builds/sample/example.md']; self.save_config()
        api.build(self.root)
        (self.root / 'builds/sample/example.md').unlink()
        result = pipe['scan'](self.root)
        self.assertIn('builds/sample/example.md', result['removed'])
        self.assertIn('Missing source', result['validation_error'])

    def test_catalog_build_cannot_bless_stale_or_missing_playbook(self):
        self.add_topic()
        a = pipe['prepare'](self.root)
        pipe['publish'](self.root, a, pipe['plan_digest'](a))
        self.config['workflows']['sample']['topics']['detail']['gates'] = ['New gate']
        self.save_config(); api.build(self.root)
        with self.assertRaisesRegex(ValueError, 'playbook'):
            api.checked_catalog(self.root)
        self.assertEqual(pipe['scan'](self.root)['playbook_status'], 'stale')
        (self.root / pipe['PLAYBOOK']).unlink();api.build(self.root)
        with self.assertRaisesRegex(ValueError, 'playbook'):
            api.checked_catalog(self.root)

    def test_unrouted_source_requires_current_disposition(self):
        path = 'research/domain/unselected.md'
        self.write(path, '# No matching task yet\n')
        with self.assertRaisesRegex(ValueError, 'unrouted'):
            pipe['prepare'](self.root)
        self.config['routing_exclusions'] = {path: {
            'reason': 'Background only until a task needs it',
            'reviewed_sha256': api.digest((self.root / path).read_bytes())}}
        self.save_config()
        pipe['prepare'](self.root)
        self.write(path, '# Scope changed\n')
        with self.assertRaisesRegex(ValueError, 'unrouted'):
            pipe['prepare'](self.root)

    def test_topic_rejects_archive_missing_or_unreviewed_sources(self):
        self.add_topic()
        flow = self.config['workflows']['sample']['topics']['detail']
        flow['sources'] = ['research/rodin.md'];self.save_config()
        with self.assertRaises(ValueError): api.make_catalog(self.root)
        flow['sources'] = ['absent'];self.save_config()
        with self.assertRaises(ValueError): api.make_catalog(self.root)
        flow['sources'] = ['research/domain/detail.md']; flow.pop('review');self.save_config()
        with self.assertRaises(ValueError): api.make_catalog(self.root)


