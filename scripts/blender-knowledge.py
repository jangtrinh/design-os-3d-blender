#!/usr/bin/env python3
"""Local Blender knowledge CLI; stdlib only. JSON output is a retrieval artifact."""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile

MODULES = Path(__file__).resolve().parent
for module in ('knowledge-catalog.py', 'knowledge-query.py'):
    globals().update({k: v for k, v in runpy.run_path(str(MODULES / module)).items()
                      if not k.startswith('__')})
DEFAULT_ROOT = MODULES.parent


def build(root):
    catalog = make_catalog(root)
    target = root / OUTPUT
    with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as handle:
        temporary = handle.name
        json.dump(catalog, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write('\n')
    try:
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return {'status': 'built', 'records': len(catalog['records']), 'counts': catalog['counts'],
            'source_digest': catalog['source_digest'], 'warnings': catalog['warnings']}


def checked_catalog(root):
    target = root / OUTPUT
    if not target.is_file(): raise ValueError('Catalog missing; run build')
    previous = json.loads(target.read_text())
    current = make_catalog(root)
    if current != previous: raise ValueError('Catalog stale; run build after source edits settle')
    compiler = runpy.run_path(str(MODULES / 'knowledge-playbook.py'))
    state = compiler['playbook_status'](root, current)
    if state in ('stale', 'missing'):
        raise ValueError(f'Generated workflow playbook {state}; prepare/review/publish required')
    return current


def positive(value):
    number = int(value)
    if number < 1: raise argparse.ArgumentTypeError('Expected positive integer')
    return number


def bounded(value):
    number = int(value)
    if not 1 <= number <= 200: raise argparse.ArgumentTypeError('Expected 1..200')
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('build', 'check', 'list'): sub.add_parser(name)
    p = sub.add_parser('search'); p.add_argument('query')
    p.add_argument('--scope', choices=('active', 'all'), default='active')
    p.add_argument('--limit', type=bounded, default=5)
    p = sub.add_parser('route'); p.add_argument('workflow'); p.add_argument('--topic')
    p = sub.add_parser('show'); p.add_argument('path')
    p.add_argument('--start', type=positive, default=1)
    p.add_argument('--lines', type=bounded, default=80)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == 'build': return build(root)
    catalog = checked_catalog(root)
    if args.command == 'check':
        return {'status': 'current', 'records': len(catalog['records']),
                'dependency_edges': catalog['dependency_edges'],
                'source_digest': catalog['source_digest'], 'warnings': catalog['warnings']}
    if args.command == 'list':
        return {k: v['purpose'] for k, v in catalog['workflows'].items()}
    if args.command == 'route': return route(catalog, args.workflow, args.topic)
    if args.command == 'search': return search(root, catalog, args.query, args.scope, args.limit)
    return show(root, catalog, args.path, args.start, args.lines)


if __name__ == '__main__':
    try:
        print(json.dumps(main(), ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'error', 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
