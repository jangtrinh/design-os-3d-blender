"""Turn attributed feature findings into bounded, revision-specific next actions."""
from hq_coverage.inputs import InputError, mapping, text

from .evidence import file_pin, load
from .packets import validate_packet


def assess(root, packet_path, critique_path):
    packet = validate_packet(root, load(root, packet_path))
    critique = load(root, critique_path)
    if (critique.get('version') != 1
            or critique.get('packet_sha256') != file_pin(root, packet_path)['sha256']):
        raise InputError('critique is not bound to this review packet')
    reviewer = text(critique.get('reviewer'), 'reviewer')
    if reviewer == packet['author'] or reviewer.startswith('REPLACE_'):
        raise InputError('independent reviewer must be declared')
    features = {f['id']: f for f in packet['contract']['features']}
    findings = {}
    for row in critique.get('findings', []):
        mapping(row, 'finding')
        ident = row.get('feature')
        if ident not in features or ident in findings:
            raise InputError('unknown or duplicate reviewed feature')
        if row.get('status') not in ('pass', 'fail', 'unknown'):
            raise InputError('finding status must be pass, fail or unknown')
        if set(row.get('views', [])) != set(features[ident]['views']):
            raise InputError('finding must account for all required feature views')
        text(row.get('observation'), 'finding observation')
        if row['status'] != 'pass':
            text(row.get('action'), 'actionable next check or correction')
            if row.get('cause') not in ('code', 'spec', 'missing-evidence'):
                raise InputError('failed/unknown finding needs a declared cause')
        findings[ident] = row
    if findings.keys() != features.keys():
        raise InputError('every contracted feature must receive a finding')
    numbers = load(root, packet['numeric']['path'])
    failed = sorted(k for k, r in findings.items() if r['status'] == 'fail')
    unknown = sorted(k for k, r in findings.items() if r['status'] == 'unknown')
    numeric_failures = sorted(c['id'] for c in numbers['checks'] if c['status'] != 'pass')
    accepted = not failed and not unknown and not numeric_failures
    previous = load(root, packet['previous']['path']) if packet.get('previous') else None
    repeated = sorted(set(failed) & set(previous.get('failed_features', []))) if previous else []
    if accepted:
        verdict, action = 'stop', 'Declared numeric and visual criteria passed for this revision.'
    elif unknown:
        verdict, action = 'request-input', 'Obtain the missing evidence named by the critic.'
    elif packet['round'] >= packet['contract']['max_rounds']:
        verdict, action = 'request-input', 'The declared review budget is exhausted; retain unresolved findings.'
    elif any(findings[k].get('cause') == 'spec' for k in failed):
        verdict, action = 'refine-spec', 'Revise the contract with explicit evidence and invalidate old reviews.'
    else:
        verdict = 'refine-code'
        action = ('Change the modeling or capture approach before another attempt.' if repeated
                  else 'Address named failed features and numeric checks, then capture new evidence.')
    return {'version': 1, 'round': packet['round'], 'verdict': verdict,
            'accepted': accepted, 'next_action': action,
            'change_approach': bool(repeated and not accepted),
            'failed_features': failed, 'unknown_features': unknown,
            'numeric_failures': numeric_failures, 'repeated_features': repeated,
            'target_sha256': packet['target']['sha256'],
            'candidate_sha256': packet['candidate_sha256'],
            'packet': file_pin(root, packet_path), 'critique': file_pin(root, critique_path),
            'reviewer': reviewer, 'findings': list(findings.values()),
            'manufacture': 'NOT_REQUESTED' if packet['contract']['purpose'] == 'render-only' else 'BLOCKED',
            'limits': packet['limits'] + ['No physical, export, continuous-motion or load qualification is inferred.']}
