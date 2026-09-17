#!/usr/bin/env python3
"""Prepare/assess native visual review evidence; no LLM, image generation or network."""
import argparse
import json
from pathlib import Path
import sys

from native_review.decision import assess
from native_review.evidence import write_new
from native_review.packets import critique_template, prepare


def pairs(values):
    result = {}
    for value in values:
        key, separator, path = value.partition('=')
        if not separator or not key or not path or key in result:
            raise ValueError('use unique role=path entries')
        result[key] = path
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--target', required=True)
    prep.add_argument('--candidate', action='append', required=True)
    prep.add_argument('--proof', action='append', required=True)
    prep.add_argument('--numeric', required=True)
    prep.add_argument('--author', required=True)
    prep.add_argument('--round', type=int, default=1)
    prep.add_argument('--previous')
    prep.add_argument('--out', required=True)
    template = commands.add_parser('template')
    template.add_argument('--packet', required=True)
    template.add_argument('--out', required=True)
    review = commands.add_parser('assess')
    review.add_argument('--packet', required=True)
    review.add_argument('--critique', required=True)
    review.add_argument('--out', required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        data = prepare(args.root, args.target, pairs(args.candidate), pairs(args.proof),
                       args.numeric, args.author, args.round, args.previous)
    elif args.command == 'template':
        data = critique_template(args.root, args.packet)
    else:
        data = assess(args.root, args.packet, args.critique)
    path = write_new(args.root, args.out, data)
    print(json.dumps({'output': str(path), 'command': args.command,
                      'verdict': data.get('verdict'), 'accepted': data.get('accepted')}))
    return 1 if args.command == 'assess' and not data['accepted'] else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'error', 'message': str(exc)}), file=sys.stderr)
        sys.exit(2)
