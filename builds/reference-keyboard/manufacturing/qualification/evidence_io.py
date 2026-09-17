"""Strict project-local evidence identity and numerical interval primitives."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    def reject(value):
        raise ValueError(f'non-finite JSON number: {value}')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), parse_constant=reject, object_pairs_hook=unique)


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'finite number required, got {value!r}')
    return float(value)


def bounded_pin(root, pin):
    path = (root / pin['path']).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file() or sha(path) != pin['sha256']:
        raise ValueError(f'missing, outside-root or changed evidence: {pin.get("path")}')
    return path


def file_pin(root, path):
    path = Path(path).resolve()
    return {'path': path.relative_to(root.resolve()).as_posix(), 'sha256': sha(path)}


def interval_pass(value, uncertainty, minimum, maximum):
    value, uncertainty = number(value), number(uncertainty)
    if uncertainty < 0:
        raise ValueError('negative measurement uncertainty')
    return ((minimum is None or value - uncertainty >= number(minimum))
            and (maximum is None or value + uncertainty <= number(maximum)))


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result > datetime.now(timezone.utc):
        raise ValueError('a non-future timezone-aware timestamp is required')
    return result


def field(value, path):
    for key in path:
        value = value[key]
    return value
