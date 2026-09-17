"""Build a critic packet from frozen targets, native artifacts and actual PNGs."""
from hq_coverage.inputs import InputError, finite, integer, mapping, text

from .evidence import (check_pin, file_pin, load, png_pin, target_contract,
                       value_hash)


def prepare(root, target, candidates, proofs, numeric, author, round_number=1,
            previous=None):
    contract, views, _ = target_contract(root, target)
    text(author, 'author')
    integer(round_number, 'round')
    if round_number > contract['max_rounds']:
        raise InputError('review round exceeds the target budget')
    if not candidates or set(proofs) != views.keys():
        raise InputError('candidate files and all declared proof views are required')
    candidate_pins = {text(k, 'candidate role'): file_pin(root, v)
                      for k, v in candidates.items()}
    target_pin = file_pin(root, target)
    target_files = [v['target'] for v in views.values()]
    forbidden = {target_pin['path'], *(p['path'] for p in target_files)}
    if forbidden & {pin['path'] for pin in candidate_pins.values()}:
        raise InputError('candidate aliases the target or its references')
    proof_pins = {k: png_pin(root, v, views[k]['proof_size'])
                  for k, v in proofs.items()}
    if forbidden & {pin['path'] for pin in proof_pins.values()}:
        raise InputError('candidate proof must be a separate capture file')
    numeric_pin = file_pin(root, numeric)
    numbers = load(root, numeric)
    candidate_digest = value_hash(candidate_pins)
    if numbers.get('candidate_sha256') != candidate_digest:
        raise InputError('numeric receipt is not bound to these candidate files')
    checks = numbers.get('checks')
    if not isinstance(checks, list) or not checks:
        raise InputError('numeric receipt needs actual named checks')
    check_ids = set()
    for check in checks:
        mapping(check, 'numeric check')
        check_id = text(check.get('id'), 'numeric check id')
        if check_id in check_ids:
            raise InputError('duplicate numeric check id')
        check_ids.add(check_id)
        if check.get('status') not in ('pass', 'fail', 'unknown'):
            raise InputError('numeric check status invalid')
        if check['status'] == 'unknown' and check.get('value') is None:
            text(check.get('observation'), 'unknown numeric check observation')
        else:
            finite(check.get('value'), 'numeric check measured value')
    if numbers.get('status') != ('pass' if all(c['status'] == 'pass' for c in checks) else 'fail'):
        raise InputError('numeric receipt status contradicts its checks')
    prior = None
    if previous:
        prior = file_pin(root, previous)
        before = load(root, previous)
        if (before.get('version') != 1 or before.get('target_sha256') != target_pin['sha256']
                or before.get('round') != round_number - 1):
            raise InputError('previous assessment has a different target or round')
        for role in ('packet', 'critique'):
            check_pin(root, before.get(role))
        prior_packet = load(root, before['packet']['path'])
        if prior_packet.get('round') != before['round']:
            raise InputError('previous assessment and packet disagree on round')
    elif round_number != 1:
        raise InputError('later rounds need the preceding assessment')
    return {'version': 1, 'round': round_number, 'author': author,
            'target': target_pin, 'contract': contract,
            'candidates': candidate_pins, 'candidate_sha256': candidate_digest,
            'proofs': proof_pins, 'numeric': numeric_pin, 'previous': prior,
            'limits': ['Bindings validate declared evidence, not image likeness.',
                       'Critic identity/independence is declared, not authenticated.',
                       'Capture context must be verified by the renderer/controller.']}


def validate_packet(root, packet):
    if packet.get('version') != 1:
        raise InputError('packet version must be 1')
    check_pin(root, packet['target'])
    for pin in packet['candidates'].values():
        check_pin(root, pin)
    for pin in packet['proofs'].values():
        check_pin(root, pin)
    check_pin(root, packet['numeric'])
    if packet.get('previous'):
        check_pin(root, packet['previous'])
    expected = prepare(root, packet['target']['path'],
                       {k: p['path'] for k, p in packet['candidates'].items()},
                       {k: p['path'] for k, p in packet['proofs'].items()},
                       packet['numeric']['path'], packet['author'], packet['round'],
                       packet['previous']['path'] if packet.get('previous') else None)
    if expected != packet:
        raise InputError('review packet changed or disagrees with locked inputs')
    return expected


def critique_template(root, packet_path):
    packet = validate_packet(root, load(root, packet_path))
    return {'version': 1, 'packet_sha256': file_pin(root, packet_path)['sha256'],
            'reviewer': 'REPLACE_WITH_INDEPENDENT_REVIEWER',
            'findings': [{'feature': f['id'], 'status': 'unknown',
                          'views': f['views'], 'observation': '', 'action': '',
                          'cause': 'missing-evidence'} for f in packet['contract']['features']]}
