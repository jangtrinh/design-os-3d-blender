"""Root-bounded, revision-pinned files reused by the native visual review flow."""
import hashlib
import json
from pathlib import Path

from hq_coverage.inputs import InputError, canonical, finite, integer, mapping, text
from hq_coverage.png import dimensions


def path_at(root, value):
    root = Path(root).resolve()
    source = Path(text(str(value), 'path'))
    joined = source if source.is_absolute() else root / source
    if '..' in joined.parts:
        raise InputError('parent traversal is not a review path')
    if any(p.is_symlink() for p in (joined, *joined.parents)):
        raise InputError('symlink review path refused')
    path = joined.resolve()
    if not path.is_relative_to(root):
        raise InputError('review path is outside the project root')
    return path


def file_pin(root, value):
    path = path_at(root, value)
    raw = path.read_bytes()
    if not raw:
        raise InputError('empty evidence file: ' + str(value))
    return {'path': path.relative_to(Path(root).resolve()).as_posix(),
            'sha256': hashlib.sha256(raw).hexdigest()}


def check_pin(root, value):
    pin = mapping(value, 'file pin')
    actual = file_pin(root, pin.get('path', ''))
    if pin.get('sha256') != actual['sha256']:
        raise InputError('stale evidence: ' + actual['path'])
    return path_at(root, actual['path'])


def load(root, value):
    def reject(value):
        raise InputError('nonfinite JSON: ' + value)
    data = json.loads(path_at(root, value).read_text(), parse_constant=reject)
    return mapping(data, 'JSON document')


def value_hash(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def png_pin(root, value, expected_size=None):
    pin = file_pin(root, value)
    size = list(dimensions(check_pin(root, pin)))
    if expected_size is not None and size != expected_size:
        raise InputError('proof dimensions do not match the locked shot size')
    return pin | {'size': size}


def write_new(root, value, data):
    path = path_at(root, value)
    raw = json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        handle.write(raw)
    return path


def capture_contract(value, proof_size):
    capture = mapping(value, 'view.capture')
    text(capture.get('camera'), 'capture.camera')
    if capture.get('projection') not in ('ORTHO', 'PERSP'):
        raise InputError('capture projection must be ORTHO or PERSP')
    if type(capture.get('frame')) is not int:
        raise InputError('capture frame must be an integer')
    if capture.get('resolution') != proof_size:
        raise InputError('capture resolution must match proof_size')
    for key in ('location', 'target'):
        vector = capture.get(key)
        if not isinstance(vector, list) or len(vector) != 3:
            raise InputError('capture ' + key + ' must have three coordinates')
        for component in vector:
            finite(component, 'capture coordinate')
    if capture['location'] == capture['target']:
        raise InputError('capture camera location and target must differ')
    start = finite(capture.get('clip_start'), 'capture.clip_start')
    end = finite(capture.get('clip_end'), 'capture.clip_end')
    if not 0 < start < end:
        raise InputError('capture clip range invalid')
    key = 'ortho_scale' if capture['projection'] == 'ORTHO' else 'lens_mm'
    if finite(capture.get(key), 'capture.' + key) <= 0:
        raise InputError('capture lens/scale must be positive')
    return capture


def target_contract(root, path):
    contract = load(root, path)
    if type(contract.get('version')) is not int or contract['version'] != 1:
        raise InputError('target contract version must be 1')
    text(contract.get('target_revision'), 'target_revision')
    if contract.get('purpose') not in ('render-only', 'print', 'both'):
        raise InputError('target purpose must be explicit')
    maximum = integer(contract.get('max_rounds'), 'max_rounds')
    if maximum > 3:
        raise InputError('review attempts are bounded to at most three')
    views, features = {}, {}
    for view in contract.get('views', []):
        view = mapping(view, 'view')
        ident = text(view.get('id'), 'view.id')
        if ident in views:
            raise InputError('duplicate view id')
        check_pin(root, view.get('target'))
        dimensions(path_at(root, view['target']['path']))
        size = view.get('proof_size')
        if not isinstance(size, list) or len(size) != 2:
            raise InputError('view.proof_size must be [width, height]')
        for n in size:
            integer(n, 'proof size')
        capture_contract(view.get('capture'), size)
        views[ident] = view
    for feature in contract.get('features', []):
        feature = mapping(feature, 'feature')
        ident = text(feature.get('id'), 'feature.id')
        if ident in features:
            raise InputError('duplicate feature id')
        text(feature.get('expectation'), 'feature.expectation')
        text(feature.get('falsifier'), 'feature.falsifier')
        required = feature.get('views')
        if not isinstance(required, list) or not required or not set(required) <= views.keys():
            raise InputError('feature needs known evidence views')
        features[ident] = feature
    if not views or not features:
        raise InputError('target needs nonempty views and features')
    return contract, views, features
