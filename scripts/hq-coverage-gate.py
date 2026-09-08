#!/usr/bin/env python3
"""Fail-closed receipt gate for the explicit HQ headless render route."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from hq_coverage.core import InputError, report_path_is_safe, validate


def write(path, report):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + '\n')
    except (OSError, TypeError, ValueError) as exc:
        raise InputError('cannot write report %s: %s' % (path, exc)) from exc


def run_headless(command):
    """Keep runner output visible while requiring its payload sentinel."""
    try:
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    except OSError as exc:
        raise InputError('could not start headless render: %s' % exc) from exc
    sentinel = None
    for line in child.stdout:
        sys.stdout.write(line); sys.stdout.flush()
        for kind in ('AGENT_OK', 'AGENT_FAIL'):
            prefix = kind + ' '
            if line.startswith(prefix):
                try:
                    payload = json.loads(line[len(prefix):])
                    sentinel = {'kind':kind, 'payload':payload} if isinstance(payload, dict) else {'kind':'invalid', 'raw':line.rstrip()}
                except json.JSONDecodeError:
                    sentinel = {'kind':'invalid', 'raw':line.rstrip()}
    return child.wait(), sentinel


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--coverage', required=True)
    parser.add_argument('--report', required=True)
    parser.add_argument('--launch', action='store_true')
    args = parser.parse_args(argv)
    report_path = Path(args.report)
    try:
        report, coverage = validate(Path(args.coverage), report_path)
    except (InputError, OSError) as exc:
        failure = {'version':1,'status':'invalid','error':str(exc)}
        try: existing = report_path.exists()
        except OSError: existing = True
        if not existing and report_path_is_safe(Path(args.coverage), report_path):
            try: write(report_path, failure)
            except InputError: pass
        print('AGENT_FAIL ' + json.dumps(failure, sort_keys=True)); return 2
    if args.launch and coverage['mode'] != 'preflight':
        report['status']='fail'; report['issues'].append({'code':'retrospective_launch_refused','message':'--launch requires coverage.mode preflight'})
    if report['status'] != 'pass':
        try: write(report_path, report)
        except InputError as exc:
            print('AGENT_FAIL ' + json.dumps({'status':'invalid','error':str(exc)}, sort_keys=True)); return 2
        print('AGENT_FAIL ' + json.dumps({'status':'fail','issues':len(report['issues'])})); return 1
    if not args.launch:
        try: write(report_path, report)
        except InputError as exc:
            print('AGENT_FAIL ' + json.dumps({'status':'invalid','error':str(exc)}, sort_keys=True)); return 2
        print('AGENT_OK ' + json.dumps({'status':'pass','launch':False})); return 0
    try:
        rechecked, coverage = validate(Path(args.coverage), report_path, refuse_existing=False)
        if coverage['mode'] != 'preflight' or rechecked['status'] != 'pass': raise InputError('bindings or preflight mode changed immediately before launch')
        report['launch']={'attempted':True,'command':['bash',str(ROOT/'scripts/headless-run.sh'),'--blend',rechecked['candidate'],rechecked['render_script']]}
        returncode, sentinel = run_headless(report['launch']['command'])
        report['launch'].update({'returncode':returncode, 'sentinel':sentinel})
        if returncode or not sentinel or sentinel['kind'] != 'AGENT_OK':
            report['status']='launch_failed'
            report['issues'].append({'code':'launch_payload_not_confirmed','message':'headless runner must return zero and end with AGENT_OK'})
            write(report_path, report)
            print('AGENT_FAIL ' + json.dumps({'status':'launch_failed','returncode':returncode})); return returncode or 1
        write(report_path, report)
    except InputError as exc:
        report['status']='fail'; report['issues'].append({'code':'prelaunch_recheck_failed','message':str(exc)})
        try: write(report_path, report)
        except InputError as write_exc:
            print('AGENT_FAIL ' + json.dumps({'status':'invalid','error':str(write_exc)}, sort_keys=True)); return 2
        print('AGENT_FAIL ' + json.dumps({'status':'launch_refused'})); return 1
    print('AGENT_OK ' + json.dumps({'status':'pass','launch':True})); return 0


if __name__ == '__main__':
    raise SystemExit(main())
