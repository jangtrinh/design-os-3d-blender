"""Small stdlib-only contract for Blender-native parametric model intent/evidence."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping
SCHEMA_VERSION = 1
_LENGTH_SCALE = {"m": 1.0, "mm": 0.001}
_ROLE_NAMES = frozenset({"visual", "collision", "physical"})

def _object(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{where} must be an object")
    return value

def _closed(value: Mapping[str, Any], allowed: set[str], where: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"{where} has unknown field(s): {', '.join(sorted(unknown))}")

def _name(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{where} must be a non-empty string")
    return value.strip()

def _number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{where} must be a finite number")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{where} must be finite")
    return out

def _unit(value: Any, where: str) -> str:
    unit = _name(value, where)
    if unit not in _LENGTH_SCALE:
        raise ValueError(f"{where} must be one of: {', '.join(sorted(_LENGTH_SCALE))}")
    return unit

def _vec3(value: Any, where: str) -> tuple[float, float, float]:
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{where} must contain three finite numbers")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise TypeError(f"{where} must contain three finite numbers") from exc
    if len(items) != 3:
        raise ValueError(f"{where} must contain exactly three numbers")
    return tuple(_number(item, f"{where}[{index}]") for index, item in enumerate(items))

def _basis(value: Any, where: str) -> dict[str, list[float]]:
    axes = _object(value, where)
    if set(axes) != {"x", "y", "z"}:
        raise ValueError(f"{where} must contain exactly x, y, z")
    out = {}
    for name in ("x", "y", "z"):
        axis = _vec3(axes[name], f"{where}.{name}")
        length = math.sqrt(sum(component * component for component in axis))
        if length <= 1e-12:
            raise ValueError(f"{where}.{name} must not be a zero vector")
        out[name] = [component / length for component in axis]
    dot = lambda a, b: sum(x * y for x, y in zip(a, b, strict=True))
    if any(abs(dot(out[a], out[b])) > 1e-6 for a, b in (("x", "y"), ("x", "z"), ("y", "z"))):
        raise ValueError(f"{where} axes must be orthogonal")
    x, y, z = out["x"], out["y"], out["z"]
    cross_xy = [x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0]]
    if dot(cross_xy, z) < 1.0 - 1e-6:
        raise ValueError(f"{where} axes must form a right-handed basis")
    return out

def normalize_contract(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a fresh JSON-ready contract with all lengths normalized to metres."""
    raw = _object(raw, "contract")
    _closed(raw, {"units", "parameters", "frames", "datums", "ports", "roles"}, "contract")
    source_units = _unit(raw.get("units"), "contract.units")
    parameters = {}
    for key, value in _object(raw.get("parameters", {}), "contract.parameters").items():
        name = _name(key, "parameter name")
        if name in parameters:
            raise ValueError(f"duplicate parameter name after normalization: {name!r}")
        item = _object(value, f"parameter {name!r}")
        if set(item) != {"value", "unit", "min", "max"}:
            raise ValueError(f"parameter {name!r} must contain exactly value, unit, min, max")
        unit = _unit(item["unit"], f"parameter {name!r}.unit")
        scale = _LENGTH_SCALE[unit]
        values = {field: _number(item[field], f"parameter {name!r}.{field}") * scale for field in ("value", "min", "max")}
        if values["min"] > values["max"] or not values["min"] <= values["value"] <= values["max"]:
            raise ValueError(f"parameter {name!r} must satisfy min <= value <= max")
        parameters[name] = {"unit": unit, "values_si": values}
    frames = {}
    for key, value in _object(raw.get("frames", {}), "contract.frames").items():
        name = _name(key, "frame name")
        if name in frames:
            raise ValueError(f"duplicate frame name after normalization: {name!r}")
        item = _object(value, f"frame {name!r}")
        _closed(item, {"parent", "origin", "unit", "axes"}, f"frame {name!r}")
        parent = item.get("parent")
        if parent is not None:
            parent = _name(parent, f"frame {name!r}.parent")
        unit = _unit(item.get("unit"), f"frame {name!r}.unit")
        origin = _vec3(item.get("origin"), f"frame {name!r}.origin")
        frames[name] = {"parent": parent, "origin_m": [v * _LENGTH_SCALE[unit] for v in origin], "axes": _basis(item.get("axes"), f"frame {name!r}.axes")}
    state: dict[str, int] = {}
    def visit(frame: str) -> None:
        if state.get(frame) == 1:
            raise ValueError(f"frame parent cycle includes {frame!r}")
        if state.get(frame) == 2:
            return
        state[frame] = 1
        parent = frames[frame]["parent"]
        if parent is not None:
            if parent not in frames:
                raise ValueError(f"frame {frame!r} references unknown parent {parent!r}")
            visit(parent)
        state[frame] = 2
    for frame_name in frames:
        visit(frame_name)
    datums = {}
    for key, value in _object(raw.get("datums", {}), "contract.datums").items():
        name = _name(key, "datum name")
        if name in datums:
            raise ValueError(f"duplicate datum name after normalization: {name!r}")
        item = _object(value, f"datum {name!r}")
        if set(item) != {"frame", "position", "unit"}:
            raise ValueError(f"datum {name!r} must contain exactly frame, position, unit")
        frame = _name(item["frame"], f"datum {name!r}.frame")
        if frame not in frames:
            raise ValueError(f"datum {name!r} references unknown frame {frame!r}")
        unit = _unit(item["unit"], f"datum {name!r}.unit")
        position = _vec3(item["position"], f"datum {name!r}.position")
        datums[name] = {"frame": frame, "position_m": [v * _LENGTH_SCALE[unit] for v in position]}
    roles = {}
    for role, labels in _object(raw.get("roles", {}), "contract.roles").items():
        role = _name(role, "role name")
        if role in roles:
            raise ValueError(f"duplicate role name after normalization: {role!r}")
        if role not in _ROLE_NAMES:
            raise ValueError(f"unknown role {role!r}; expected visual, collision, or physical")
        if isinstance(labels, (str, bytes)) or not isinstance(labels, (list, tuple)) or not labels:
            raise TypeError(f"role {role!r} must be a non-empty list of labels")
        normalized = [_name(label, f"role {role!r} label") for label in labels]
        if len(set(normalized)) != len(normalized):
            raise ValueError(f"role {role!r} contains duplicate labels")
        roles[role] = normalized
    ports = {}
    for key, value in _object(raw.get("ports", {}), "contract.ports").items():
        name = _name(key, "port name")
        if name in ports:
            raise ValueError(f"duplicate port name after normalization: {name!r}")
        item = _object(value, f"port {name!r}")
        if set(item) != {"frame", "kind", "roles"}:
            raise ValueError(f"port {name!r} must contain exactly frame, kind, roles")
        frame = _name(item["frame"], f"port {name!r}.frame")
        if frame not in frames:
            raise ValueError(f"port {name!r} references unknown frame {frame!r}")
        raw_roles = item["roles"]
        if isinstance(raw_roles, (str, bytes)) or not isinstance(raw_roles, (list, tuple)) or not raw_roles:
            raise TypeError(f"port {name!r}.roles must be a non-empty list of role labels")
        port_roles = [_name(role, f"port {name!r}.roles") for role in raw_roles]
        if len(set(port_roles)) != len(port_roles):
            raise ValueError(f"port {name!r}.roles contains duplicate labels")
        if any(role not in roles for role in port_roles):
            raise ValueError(f"port {name!r} roles must reference declared role labels")
        ports[name] = {"frame": frame, "kind": _name(item["kind"], f"port {name!r}.kind"), "roles": port_roles}
    return {"schema_version": SCHEMA_VERSION, "units": source_units, "parameters": parameters, "frames": frames, "datums": datums, "ports": ports, "roles": roles}

def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
def _file_rows(paths: Iterable[str | Path], root: str | Path, *, include_format: bool = False) -> list[dict[str, str]]:
    root_path = Path(root).expanduser().resolve()
    if not root_path.is_dir():
        raise NotADirectoryError(root_path)
    rows, seen = [], set()
    for raw in paths:
        path = Path(raw).expanduser()
        candidate = path if path.is_absolute() else root_path / path
        if candidate.absolute() != candidate.resolve():
            raise ValueError(f"evidence path must not use symlinks or parent aliases: {candidate}")
        path = candidate.resolve()
        try:
            relative = path.relative_to(root_path).as_posix()
        except ValueError as exc:
            raise ValueError(f"evidence path escapes root: {path}") from exc
        if relative in seen:
            raise ValueError(f"duplicate evidence path: {relative}")
        if not path.is_file():
            raise FileNotFoundError(path)
        seen.add(relative)
        row = {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        if include_format:
            row["format"] = path.suffix.lower().lstrip(".") or "unknown"
        rows.append(row)
    if not rows:
        raise ValueError("at least one evidence file is required")
    return sorted(rows, key=lambda row: row["path"])
def bind_source_evidence(contract: Mapping[str, Any], paths: Iterable[str | Path], root: str | Path) -> dict[str, Any]:
    return {"kind": "source-evidence", "schema_version": SCHEMA_VERSION, "contract_sha256": _digest(contract), "files": _file_rows(paths, root)}
def source_evidence_current(receipt: Mapping[str, Any], root: str | Path, *, contract: Mapping[str, Any] | None = None) -> bool:
    if receipt.get("kind") != "source-evidence" or receipt.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported source evidence receipt")
    if contract is not None and receipt.get("contract_sha256") != _digest(contract):
        return False
    try:
        current = _file_rows((row["path"] for row in receipt["files"]), root)
    except (KeyError, TypeError, OSError, ValueError):
        return False
    return current == receipt["files"]
def bind_export_evidence(contract: Mapping[str, Any], paths: Iterable[str | Path], root: str | Path, *, scene_sha256: str | None = None, spec_sha256: str | None = None) -> dict[str, Any]:
    receipt = {"kind": "export-evidence", "schema_version": SCHEMA_VERSION, "contract_sha256": _digest(contract), "files": _file_rows(paths, root, include_format=True)}
    for key, value in (("scene_sha256", scene_sha256), ("spec_sha256", spec_sha256)):
        if value is not None:
            if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
                raise ValueError(f"{key} must be a 64-character hexadecimal sha256")
            receipt[key] = value.lower()
    return receipt
