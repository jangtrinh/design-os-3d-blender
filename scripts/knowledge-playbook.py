"""Compile curated workflow configuration into a skill-readable Markdown artifact."""
PLAYBOOK = 'knowledge/generated-workflows.md'


def render_playbook(catalog):
    rows = {r['path']: r for r in catalog['records']}
    lines = ['# Generated Blender workflow playbook', '',
             'Generated from catalog-config.json. Edit the config, then prepare/publish again.',
             'Routing reviews are static source assessments, not API, physics or hardware certification.',
             'Read only the workflow and conditional topic relevant to the task. Core owns execution.', '']
    def sources(paths):
        for p in paths:
            r = rows[p]
            lines.append(f"- `{p}` — {r['use']}; SHA256 `{r['sha256']}`")
            if r.get('annotation'):
                lines.append('  Caution: ' + r['annotation']['caution'])
    for name, flow in catalog['workflows'].items():
        lines += ['## ' + name, '', flow['purpose'], '', '### Base reading', '']
        sources(list(dict.fromkeys(catalog['foundations'] + flow['required'])))
        for key in ('steps', 'gates', 'limitations'):
            lines += ['', '### ' + key.capitalize(), ''] + ['- ' + s for s in flow[key]]
        for name, topic in flow.get('topics', {}).items():
            lines += ['', '### Topic: ' + name, '', 'When: ' + topic['when'], '']
            sources(topic['sources'])
            for key in ('steps', 'gates', 'limitations'):
                lines += ['', '**' + key.capitalize() + '**', ''] + ['- ' + s for s in topic[key]]
        lines += ['']
    return '\n'.join(lines) + '\n'


def playbook_status(root, catalog):
    path = root / PLAYBOOK
    if not path.is_file():
        return 'missing' if (root / 'plans/knowledge-updates/last-publication.json').is_file() else 'unpublished'
    return 'current' if path.read_text() == render_playbook(catalog) else 'stale'
