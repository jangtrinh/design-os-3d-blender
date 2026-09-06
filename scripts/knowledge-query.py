"""Read-only retrieval and bounded workflow packs over a checked catalog."""
import re
import unicodedata


def normalize(text):
    text = text.lower().replace('đ', 'd')
    return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c))


def compact(row):
    keys = ('path', 'title', 'use', 'sha256', 'annotation', 'annotation_revision')
    return {k: row[k] for k in keys if k in row}


def route(catalog, name, topic=None):
    if name not in catalog['workflows']:
        raise ValueError('Unknown workflow. Available: ' + ', '.join(catalog['workflows']))
    flow = catalog['workflows'][name]
    by_path = {r['path']: r for r in catalog['records']}
    result = {'workflow': name, 'purpose': flow['purpose'], 'source_digest': catalog['source_digest']}
    chosen = set()
    for group in ('required', 'supplemental', 'concepts', 'adapters'):
        paths = catalog['foundations'] + flow[group] if group == 'required' else flow[group]
        result[group] = [compact(by_path[p]) for p in dict.fromkeys(paths)]
        chosen.update(paths)
    related = set()
    # One hop, deduplicated; cycles never recursively expand required reading.
    for p in list(chosen): related.update(by_path[p]['related'])
    result['related'] = sorted(related - chosen)
    topics = flow.get('topics', {})
    result['topics'] = {key: {'when': value['when'], 'sources': len(value['sources']),
        'review_current': all(by_path[p]['sha256'] == value['review']['source_hashes'][p]
                              for p in value['sources'])} for key, value in topics.items()}
    if topic is not None:
        if topic not in topics: raise ValueError(f'Unknown topic for {name}: {topic}')
        selected = topics[topic]
        if not result['topics'][topic]['review_current']:
            raise ValueError(f'Topic source changed; re-review required: {name}/{topic}')
        result['selected_topic'] = {k: selected[k] for k in ('when', 'steps', 'gates', 'limitations')}
        result['topic_sources'] = [compact(by_path[p]) for p in selected['sources']]

    for key in ('steps', 'gates', 'limitations'): result[key] = flow[key]
    return result


def search(root, catalog, query, scope, limit):
    terms = set(re.findall(r'[a-z0-9]+', normalize(query)))
    if not terms: raise ValueError('Search needs a non-empty word')
    results = []
    for row in catalog['records']:
        if scope == 'active' and row['use'] == 'archive-only': continue
        lines = (root / row['path']).read_text().splitlines()
        title = normalize(row['title'] + ' ' + row['path'] + ' ' + ' '.join(row['tags']))
        matching = [(sum(t in normalize(line) for t in terms), i, line)
                    for i, line in enumerate(lines, 1)]
        score, number, snippet = max(matching, default=(0, 0, ''), key=lambda x: x[0])
        boost = sum(t in title for t in terms) * 3
        if score + boost:
            results.append({**compact(row), 'score': score + boost, 'line': number,
                            'snippet': snippet[:300]})
    return sorted(results, key=lambda r: (-r['score'], r['path']))[:limit]


def show(root, catalog, path, start, count):
    row = next((r for r in catalog['records'] if r['path'] == path), None)
    if row is None: raise ValueError('Path is not in the catalog')
    lines = (root / path).read_text().splitlines()
    return {**compact(row), 'headings': row['headings'],
            'excerpt': [{'line': i, 'text': line} for i, line in
                        enumerate(lines, 1) if start <= i < start + count]}
