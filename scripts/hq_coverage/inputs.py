"""Typed input pins and safe report destinations for coverage receipts."""
import hashlib
import json
import math
from pathlib import Path


class InputError(ValueError):
    pass


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise InputError('JSON value must contain only finite, canonical values') from exc


def digest(path, cache):
    path = path.resolve()
    if path not in cache:
        try:
            cache[path] = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise InputError('cannot read %s: %s' % (path, exc)) from exc
    return cache[path]


def resolve(base, value, label):
    if not isinstance(value, str) or not value:
        raise InputError('%s.path must be a nonempty string' % label)
    return (Path(value) if Path(value).is_absolute() else base / value).resolve()


def mapping(value, label):
    if not isinstance(value, dict):
        raise InputError('%s must be an object' % label)
    return value


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise InputError('%s must be a nonempty string' % label)
    return value


def integer(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InputError('%s must be a positive integer' % label)
    return value


def coordinate(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InputError('%s must be a nonnegative integer' % label)
    return value


def finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError('%s must be finite number' % label)
    return value


def load_json(path, label):
    if not path.is_file():
        raise InputError('%s missing: %s' % (label, path))
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError('%s malformed JSON: %s' % (label, exc)) from exc


def pinned(base, value, label, cache, issues, paths):
    value = mapping(value, label)
    path = resolve(base, value.get('path'), label)
    expected = text(value.get('sha256'), label + '.sha256')
    if len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
        raise InputError('%s.sha256 must be lowercase SHA-256' % label)
    paths.add(path)
    if not path.is_file():
        raise InputError('%s missing: %s' % (label, path))
    actual = digest(path, cache)
    if actual != expected:
        issues.append({'code': 'stale_hash', 'path': str(path), 'message': '%s hash is stale; update its SHA-256 pin' % label})
    return path, actual


def declared_paths(coverage_path, report_path):
    """Return every path named by the receipt before any output is written."""
    coverage = mapping(load_json(coverage_path, 'coverage'), 'coverage')
    base, paths = coverage_path.parent, {coverage_path}
    for key in ('candidate', 'render_script', 'shot_plan', 'requirements'):
        paths.add(resolve(base, mapping(coverage.get(key), key).get('path'), key))
    reviews = coverage.get('reviews')
    if isinstance(reviews, list):
        for index, review in enumerate(reviews):
            review = mapping(review, 'reviews[%d]' % index)
            for key in ('report', 'proof'):
                paths.add(resolve(base, mapping(review.get(key), 'review.%s' % key).get('path'), 'review.%s' % key))
    requirements = resolve(base, mapping(coverage.get('requirements'), 'requirements').get('path'), 'requirements')
    if requirements.is_file():
        body = mapping(load_json(requirements, 'requirements'), 'requirements JSON')
        features = body.get('features')
        if isinstance(features, list):
            for index, feature in enumerate(features):
                feature = mapping(feature, 'requirements.features[%d]' % index)
                paths.add(resolve(base, mapping(feature.get('reference'), 'feature.reference').get('path'), 'feature.reference'))
    if report_path in paths:
        raise InputError('report path aliases an input/proof/reference path: %s' % report_path)
    return paths


def report_path_is_safe(coverage_path, report_path):
    """Return false on any ambiguity: invalid input should never clobber an input."""
    try:
        declared_paths(coverage_path.resolve(), report_path.resolve())
        return True
    except (InputError, OSError):
        return False


