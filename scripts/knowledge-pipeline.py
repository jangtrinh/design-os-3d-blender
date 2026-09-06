#!/usr/bin/env python3
"""Scan -> curate config -> prepare -> review -> publish. Never executes source snippets."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile

HERE = Path(__file__).resolve().parent
api = runpy.run_path(str(HERE / 'blender-knowledge.py'))
compiler = runpy.run_path(str(HERE / 'knowledge-playbook.py'))
PLAYBOOK = compiler['PLAYBOOK']
RECEIPT = 'plans/knowledge-updates/last-publication.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def plan_digest(bundle):
    return sha(json.dumps(bundle, sort_keys=True, ensure_ascii=False).encode())


def read_hash(path):
    if path.is_symlink(): raise ValueError(f'symlink output refused: {path}')
    return sha(path.read_bytes()) if path.is_file() else None


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if any(p.is_symlink() for p in [path, *path.parents]): raise ValueError('symlink output path')
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temp = f.name; f.write(data)
    try: os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def inputs(catalog):
    return {p: h for p, h in catalog['source_hashes'].items() if p != PLAYBOOK}


def scan(root):
    root = Path(root).resolve()
    config = json.loads(api['safe_path'](root, api['CONFIG']).read_text())
    current, read_errors = {}, []
    for path in api['source_paths'](root, config):
        if path == PLAYBOOK: continue
        try: current[path] = sha(api['safe_path'](root, path).read_bytes())
        except (OSError, ValueError) as error: read_errors.append(str(error))
    for path in list(current):
        if path.startswith('.agents/skills/'):
            mirror = path.replace('.agents/', '.claude/', 1)
            if (root / mirror).exists():
                current[mirror] = sha(api['safe_path'](root, mirror).read_bytes())
    receipt = root / RECEIPT
    baseline = json.loads(receipt.read_text())['inputs'] if receipt.is_file() else None
    if baseline is None:
        saved = root / api['OUTPUT']
        baseline = inputs(json.loads(saved.read_text())) if saved.is_file() else {}
    result = {'added': sorted(current.keys() - baseline.keys()),
              'changed': sorted(p for p in current.keys() & baseline.keys() if current[p] != baseline[p]),
              'removed': sorted(baseline.keys() - current.keys()),
              'baseline': RECEIPT if receipt.is_file() else api['OUTPUT']}
    result['source_errors'] = read_errors
    try:
        c = api['make_catalog'](root)
        result.update(api['TOPICS']['coverage'](c))
        result['warnings'] = c['warnings']
        result['records'] = len(c['records'])
        result['playbook_status'] = compiler['playbook_status'](root, c)
    except ValueError as error: result['validation_error'] = str(error)
    return result


def prepare(root):
    root = Path(root).resolve(); c = api['make_catalog'](root)
    if api['TOPICS']['coverage'](c)['unrouted']:
        raise ValueError('unrouted knowledge requires a topic or hash-bound deferral: ' +
                         ', '.join(api['TOPICS']['coverage'](c)['unrouted']))
    if any(w.startswith('Topic review stale:') for w in c['warnings']):
        raise ValueError('Topic source review is stale; re-read before preparing')
    return {'schema': 'blender.knowledge-promotion.v1', 'root': str(root),
            'inputs': inputs(c), 'output': PLAYBOOK,
            'before_sha256': read_hash(root / PLAYBOOK),
            'content': compiler['render_playbook'](c),
            'meaning': 'Curated routing only; no source execution or technical certification.'}


@contextmanager
def publication_lock(root):
    lock = root / 'plans/knowledge-updates/publish.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    if any(p.is_symlink() for p in [lock, *lock.parents]): raise ValueError('symlink lock')
    with lock.open('a') as f:
        try: fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise ValueError('Another publication is running')
        try: yield
        finally: fcntl.flock(f, fcntl.LOCK_UN)


def publish(root, bundle, reviewed_digest):
    root = Path(root).resolve()
    if plan_digest(bundle) != reviewed_digest: raise ValueError('Reviewed plan digest mismatch')
    if bundle['schema'] != 'blender.knowledge-promotion.v1' or bundle['root'] != str(root):
        raise ValueError('Wrong bundle schema/root')
    if bundle['output'] != PLAYBOOK: raise ValueError('Unexpected output path')
    with publication_lock(root):
        fresh = prepare(root)
        if fresh['inputs'] != bundle['inputs']: raise ValueError('Prepared source inputs changed')
        if fresh['content'] != bundle['content']: raise ValueError('Output does not match compiler')
        target = root / PLAYBOOK; wanted = sha(bundle['content'].encode())
        if read_hash(target) not in (bundle['before_sha256'], wanted):
            raise ValueError('Concurrent output edit; prepare again')
        write_atomic(target, bundle['content'].encode())
        api['build'](root)
        c = api['checked_catalog'](root)
        if inputs(c) != bundle['inputs']: raise ValueError('source changed during publication; prepare again')
        result = {'status': 'published', 'plan_sha256': reviewed_digest,
                  'playbook_sha256': wanted, 'catalog_digest': c['source_digest'], 'inputs': inputs(c)}
        write_atomic(root / RECEIPT, (json.dumps(result, indent=2, ensure_ascii=False) + '\n').encode())
        return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=HERE.parent)
    p.add_argument('stage', choices=('scan', 'prepare', 'publish'))
    p.add_argument('--bundle', type=Path)
    p.add_argument('--reviewed-sha256')
    args = p.parse_args(); root = args.root.resolve()
    if args.stage == 'scan': return scan(root)
    if args.stage == 'prepare':
        bundle = prepare(root)
        if not args.bundle: raise ValueError('prepare requires --bundle output')
        dest = args.bundle.resolve()
        if not dest.is_relative_to(root / 'plans/knowledge-updates'):
            raise ValueError('Candidate bundles belong in plans/knowledge-updates/')
        write_atomic(dest, (json.dumps(bundle, indent=2, ensure_ascii=False) + '\n').encode())
        return {'bundle': str(dest), 'review_sha256': plan_digest(bundle), 'inputs': len(bundle['inputs']),
                'output': PLAYBOOK, 'output_sha256': sha(bundle['content'].encode())}
    if not args.bundle or not args.reviewed_sha256: raise ValueError('publish needs bundle and reviewed digest')
    result = publish(root, json.loads(args.bundle.read_text()), args.reviewed_sha256)
    return {k: v for k, v in result.items() if k != 'inputs'}


if __name__ == '__main__':
    try: print(json.dumps(main(), indent=2, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status':'error', 'message':str(error)}), file=sys.stderr);sys.exit(2)
