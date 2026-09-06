"""Build-spec loading and validation (host side, stdlib only).

The JSON Schema file is the single source of truth for shape. This module is a
small interpreter for the subset of JSON Schema used there (type, required,
properties, items, enum, minimum/exclusiveMinimum, minItems/maxItems, $ref,
anyOf), plus the semantic rules the schema cannot express.
Any violation is a CONTRACT error -> the gate exits 2.
"""
from __future__ import annotations

import json
import os

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "specs", "build-spec.schema.json")

_TYPES = {"object": dict, "array": list, "string": str, "integer": int,
          "number": (int, float), "boolean": bool}


class SpecError(Exception):
    """Raised for any contract violation. Callers map this to exit code 2."""


def _resolve(root, node):
    while "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            raise SpecError("unsupported $ref %r" % ref)
        cur = root
        for part in ref[2:].split("/"):
            cur = cur[part]
        node = cur
    return node


def _validate(root, node, value, path, errors):
    node = _resolve(root, node)
    if "anyOf" in node:
        for sub in node["anyOf"]:
            trial = []
            _validate(root, sub, value, path, trial)
            if not trial:
                return
        errors.append("%s: matches none of the allowed forms" % path)
        return
    t = node.get("type")
    if t:
        py = _TYPES[t]
        ok = isinstance(value, py) and not (t != "boolean" and isinstance(value, bool))
        if t == "number" and isinstance(value, bool):
            ok = False
        if not ok:
            errors.append("%s: expected %s, got %s" % (path, t, type(value).__name__))
            return
    if "enum" in node and value not in node["enum"]:
        errors.append("%s: %r not one of %s" % (path, value, node["enum"]))
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in node and value < node["minimum"]:
            errors.append("%s: %s < minimum %s" % (path, value, node["minimum"]))
        if "exclusiveMinimum" in node and value <= node["exclusiveMinimum"]:
            errors.append("%s: %s must be > %s" % (path, value, node["exclusiveMinimum"]))
    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            errors.append("%s: needs at least %d items" % (path, node["minItems"]))
        if "maxItems" in node and len(value) > node["maxItems"]:
            errors.append("%s: allows at most %d items" % (path, node["maxItems"]))
        item = node.get("items")
        if item:
            for i, v in enumerate(value):
                _validate(root, item, v, "%s[%d]" % (path, i), errors)
    if isinstance(value, dict):
        for key in node.get("required", []):
            if key not in value:
                errors.append("%s: missing required field %r" % (path, key))
        props = node.get("properties", {})
        for key, v in value.items():
            if key in props:
                _validate(root, props[key], v, "%s.%s" % (path, key), errors)


def load_schema(path=SCHEMA_PATH):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate(spec, schema=None):
    """Return the spec, or raise SpecError listing every violation found."""
    schema = schema or load_schema()
    errors = []
    if not isinstance(spec, dict):
        raise SpecError("spec root must be a JSON object")
    _validate(schema, schema, spec, "spec", errors)
    ids = set()
    for i, part in enumerate(spec.get("parts", []) if isinstance(spec.get("parts"), list) else []):
        if not isinstance(part, dict):
            continue
        pid = part.get("id")
        if pid in ids:
            errors.append("spec.parts[%d]: duplicate part id %r" % (i, pid))
        ids.add(pid)
        dims = part.get("target_dims_mm")
        if dims is None:
            errors.append("spec.parts[%d] (%s): no target_dims_mm; a part without target "
                          "dimensions cannot be gated" % (i, pid))
        fids = set()
        for j, feat in enumerate(part.get("features", []) or []):
            if not isinstance(feat, dict):
                continue
            fid = feat.get("id") or "f%d" % j
            if fid in fids:
                errors.append("spec.parts[%d].features[%d]: duplicate feature id %r" % (i, j, fid))
            fids.add(fid)
    if errors:
        raise SpecError("; ".join(errors))
    return spec


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        raise SpecError("cannot read spec: %s" % exc)
    try:
        spec = json.loads(raw)
    except ValueError as exc:
        raise SpecError("spec is not valid JSON: %s" % exc)
    return validate(spec)


def select_parts(spec, wanted):
    """wanted: list of part ids or None. Unknown id -> SpecError (exit 2)."""
    parts = spec["parts"]
    if not wanted:
        return parts
    by_id = {p["id"]: p for p in parts}
    missing = [w for w in wanted if w not in by_id]
    if missing:
        raise SpecError("--parts names ids absent from the spec: %s" % ", ".join(missing))
    return [by_id[w] for w in wanted]
