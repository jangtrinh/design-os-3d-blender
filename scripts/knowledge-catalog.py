"""Deterministic inventory. Reads local text only; never imports indexed code."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import runpy

TOPICS = runpy.run_path(str(Path(__file__).with_name("knowledge-topics.py")))

CONFIG = 'knowledge/catalog-config.json'
OUTPUT = 'knowledge/catalog.json'
ARCHIVE = {'00-SYNTHESIS.md', 'hunyuan3d.md', 'marketplaces.md',
           'oss-models.md', 'pipeline-fit.md', 'rodin.md',
           'oss-tooling.md', 'how-image-to-3d-works.md'}
OWNED = {'blender-agent-core', 'blender-image-to-3d', 'blender-knowledge-workbench'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError(f'Unsafe source path: {relative}')
    target = root / p
    if any(parent.is_symlink() for parent in [target, *target.parents] if parent != root.parent):
        raise ValueError(f'symlink source refused: {relative}')
    if not target.is_file():
        raise ValueError(f'Missing source: {relative}')
    return target


def metadata(text):
    if not text.startswith('---\n'):
        return {}
    if '\n---' not in text[4:]:
        raise ValueError('Unclosed frontmatter')
    result = {}
    for line in text.split('\n---', 1)[0].splitlines()[1:]:
        if not line or line.startswith('#'): continue
        if ':' not in line: raise ValueError(f'Unsupported metadata: {line}')
        key, value = line.split(':', 1)
        value = value.strip()
        if key in {'tags', 'loads_with'}:
            if not (value.startswith('[') and value.endswith(']')):
                raise ValueError(f'Expected inline list: {line}')
            result[key] = [v.strip().strip('\"\'') for v in value[1:-1].split(',') if v.strip()]
        else:
            result[key] = value.strip('\"\'')
    return result


def source_paths(root, config):
    paths = {CONFIG, *config['examples']}
    for base, pattern in [('knowledge', '*.md'), ('research', '*.md'),
                          ('.agents/skills', '*.md'), ('.agents/skills', '*.jsonl'),
                          ('docs', '*.md'), ('tests', '*.py'), ('scripts/boilerplates', '*.py')]:
        for p in (root / base).rglob(pattern):
            rel = p.relative_to(root)
            if any(x in rel.parts for x in ('.git', '__pycache__', '.cache', 'node_modules', '.venv')):
                continue
            if rel.parts[:2] == ('research', 'tools'): continue
            paths.add(rel.as_posix())
    for pattern in ('*.py', '*.sh'):
        paths.update(p.relative_to(root).as_posix() for p in (root / 'scripts').glob(pattern))
    paths.update(p for p in ('.project-agent.md', 'AGENTS.md', 'CLAUDE.md') if (root / p).is_file())
    return sorted(paths)


def classify(path, config):
    if path.startswith('.agents/skills/img2threejs/'):
        return 'imported-reference', ('read-adapt' if path in config['portable'] else 'archive-only')
    if path.startswith('research/'):
        archive = len(Path(path).parts) == 2 and Path(path).name in ARCHIVE
        return 'research-synthesis', 'archive-only' if archive else 'read-verify'
    if path.startswith(('builds/', 'tests/blender/')): return 'asset-example', 'inspect-adapt'
    if path.startswith(('scripts/', 'tests/')): return 'execution-source', 'inspect-adapt'
    if path.startswith('knowledge/') and path.endswith('.md'): return 'knowledge', 'read-verify'
    return 'workflow', 'read'


def make_catalog(root):
    root = Path(root).resolve()
    config_bytes = safe_path(root, CONFIG).read_bytes()
    config = json.loads(config_bytes)
    if config.get('version') != 1: raise ValueError('Unsupported config version')
    for skill in sorted(OWNED):
        canonical = root / '.agents/skills' / skill
        mirror = root / '.claude/skills' / skill
        left = {p.relative_to(canonical).as_posix() for p in canonical.rglob('*.md')}
        right = {p.relative_to(mirror).as_posix() for p in mirror.rglob('*.md')}
        if left != right: raise ValueError(f'Owned mirror file-set drift: {skill}')
    records, warnings, hashes, names = [], [], {}, {}
    for path in source_paths(root, config):
        data = safe_path(root, path).read_bytes()
        hashes[path] = digest(data)
        text = data.decode('utf-8')
        meta = metadata(text) if path.startswith('knowledge/') and path.endswith('.md') else {}
        headings = [{'line': i, 'text': line.lstrip('# ').strip()} for i, line in
                    enumerate(text.splitlines(), 1) if re.match(r'^#{1,6} ', line)]
        kind, use = classify(path, config)
        row = {'path': path, 'sha256': hashes[path], 'kind': kind, 'use': use,
               'title': headings[0]['text'] if headings else Path(path).name,
               'lines': len(text.splitlines()), 'headings': headings,
               'name': meta.get('name'), 'tags': meta.get('tags', []),
               'description': meta.get('description', ''),
               'loads_with': meta.get('loads_with', []), 'related': []}
        if row['name']:
            if row['name'] in names: raise ValueError(f'Duplicate knowledge name: {row["name"]}')
            names[row['name']] = path
        note = config['annotations'].get(path)
        if note:
            row['annotation'] = note
            row['annotation_revision'] = ('matched' if note['reviewed_sha256'] == row['sha256']
                                          else 'changed-since-review')
            if row['annotation_revision'] != 'matched': warnings.append(f'Re-review annotation: {path}')
        if path.startswith('.agents/skills/'):
            mirror = path.replace('.agents/', '.claude/', 1)
            if (root / mirror).exists():
                hashes[mirror] = digest(safe_path(root, mirror).read_bytes())
                row['mirror'] = {'path': mirror, 'matches': hashes[mirror] == row['sha256']}
                if not row['mirror']['matches']:
                    if Path(path).parts[2] in OWNED: raise ValueError(f'Owned mirror drift: {path}')
                    warnings.append(f'Imported mirror drift (preserved): {path}')
            elif Path(path).parts[2] in OWNED:
                raise ValueError(f'Missing owned mirror: {mirror}')
        records.append(row)
    if digest(config_bytes) != hashes[CONFIG]: raise ValueError('Config changed during scan; retry')
    by_path = {r['path']: r for r in records}
    for row in records:
        for name in row['loads_with']:
            if name not in names: raise ValueError(f'Missing dependency {name} from {row["path"]}')
            row['related'].append(names[name])
    for path in config['annotations']:
        if path not in by_path: raise ValueError(f'Orphan annotation: {path}')
    for name, flow in config['workflows'].items():
        required = list(dict.fromkeys(config['foundations'] + flow['required']))
        if len(required) > 8: raise ValueError(f'Unbounded workflow required pack: {name}')
        for group in ('required', 'supplemental', 'concepts', 'adapters'):
            for path in (required if group == 'required' else flow[group]):
                if path not in by_path: raise ValueError(f'Missing workflow source: {name}: {path}')
                if by_path[path]['use'] == 'archive-only':
                    raise ValueError(f'restricted source in workflow: {name}: {path}')
    warnings.extend(TOPICS['validate_topics'](config, records))
    # Compare a second census/read to reject a source changed during construction.
    if source_paths(root, config) != sorted(p for p in hashes if not p.startswith('.claude/')):
        raise ValueError('Source census changed during scan; retry')
    if any(digest(safe_path(root, p).read_bytes()) != h for p, h in hashes.items()):
        raise ValueError('Source changed during scan; retry')
    return {'schema': 1, 'source_digest': digest(json.dumps(hashes, sort_keys=True).encode()),
            'counts': dict(sorted(Counter(r['kind'] for r in records).items())),
            'dependency_edges': sum(len(r['related']) for r in records),
            'records': records, 'source_hashes': hashes, 'warnings': warnings,
            'foundations': config['foundations'], 'workflows': config['workflows'],
            'routing_exclusions': config.get('routing_exclusions', {}),
            'boundaries': 'Local text inventory; no execution or technical certification. '
            'research/tools, binaries, caches, generated media and unselected builds excluded. '
            'Imported text retained as provenance; only explicitly portable references route by default.'}
