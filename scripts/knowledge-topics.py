"""Validate optional curated reading topics; review means routing, not certification."""
import re


def validate_topics(config, records):
    rows = {r['path']: r for r in records}
    warnings = []
    for workflow, flow in config['workflows'].items():
        for name, topic in flow.get('topics', {}).items():
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
                raise ValueError(f'Invalid topic name: {name}')
            if not topic.get('when') or not 1 <= len(topic.get('sources', [])) <= 5:
                raise ValueError(f'Topic needs trigger and 1..5 sources: {workflow}/{name}')
            for field in ('steps', 'gates', 'limitations'):
                if not isinstance(topic.get(field), list) or not 1 <= len(topic[field]) <= 5:
                    raise ValueError(f'Topic needs 1..5 {field}: {name}')
            review = topic.get('review', {})
            if review.get('kind') != 'static-routing-review' or not review.get('by'):
                raise ValueError(f'Topic requires routing review: {name}')
            if set(review.get('source_hashes', {})) != set(topic['sources']):
                raise ValueError(f'Topic review does not cover sources: {name}')
            for path in topic['sources']:
                if path not in rows: raise ValueError(f'Missing topic source: {name}: {path}')
                if rows[path]['use'] == 'archive-only':
                    raise ValueError(f'restricted topic source: {name}: {path}')
                if rows[path]['sha256'] != review['source_hashes'][path]:
                    warnings.append(f'Topic review stale: {workflow}/{name}: {path}')
    return warnings


def topic_current(topic, rows):
    return all(rows[p]['sha256'] == topic['review']['source_hashes'][p] for p in topic['sources'])


def coverage(catalog):
    used = set(catalog['foundations'])
    for flow in catalog['workflows'].values():
        for key in ('required', 'supplemental', 'concepts', 'adapters'): used.update(flow[key])
        for topic in flow.get('topics', {}).values(): used.update(topic['sources'])
    unrouted, deferred = [], []
    for row in catalog['records']:
        path = row['path']
        if row['kind'] not in ('research-synthesis', 'knowledge') or row['use'] == 'archive-only': continue
        if path in used or path in ('knowledge/INDEX.md', 'knowledge/generated-workflows.md'): continue
        decision = catalog.get('routing_exclusions', {}).get(path, {})
        if decision.get('reason') and decision.get('reviewed_sha256') == row['sha256']:
            deferred.append({'path': path, 'reason': decision['reason']})
        else: unrouted.append(path)
    return {'unrouted': unrouted, 'deferred': deferred}
