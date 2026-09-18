"""Per-part report coverage rules, without bpy or new geometric measurements."""
import math
from decimal import Decimal

ZERO_CHECKS = {'non_manifold_edges', 'non_contiguous_edges', 'wire_edges',
               'loose_verts', 'zero_area_faces', 'self_intersection_pairs'}
TOPOLOGY = ZERO_CHECKS | {'shells', 'signed_volume_positive'}
BASE_CHECKS = TOPOLOGY | {'bbox_dims_mm', 'scale_applied', 'scene_unit_system',
                         'scene_scale_length', 'bed_fit_footprint_mm',
                         'bed_fit_height_mm', 'wall_thickness_screen'}
ROUNDTRIP = {'roundtrip_' + name for name in TOPOLOGY | {'bbox_dims_mm', 'import'}}


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('expected a finite number, not a boolean')
    return value


def index_rows(rows, key):
    if not isinstance(rows, list):
        raise ValueError(f'{key} entries must be a list')
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f'{key} entry must be an object')
        name = row[key]
        if not isinstance(name, str) or not name or name in result:
            raise ValueError(f'missing or duplicate {key}: {name!r}')
        result[name] = row
    return result


def feature_checks(part):
    names, identifiers = set(), set()
    for i, feature in enumerate(part.get('features', [])):
        ident = feature.get('id') or f'f{i}'
        if ident in identifiers:
            raise ValueError(f'duplicate feature id: {ident}')
        identifiers.add(ident)
        prefix = f'feature_{ident}_'
        if feature['type'] != 'hole':
            names.add(prefix + 'measured')  # Current gate skips unsupported features.
            continue
        names.update(prefix + suffix for suffix in ('diameter_mm', 'material_around'))
        names.add(prefix + ('depth_mm' if feature.get('depth_mm') is not None else 'bore_clear'))
        if feature.get('keyed_flat_mm') is not None:
            names.add(prefix + 'keyed_flat_mm')
        fastener = feature.get('fastener') or {}
        if fastener:
            names.add(prefix + 'fastener_table')
        if fastener.get('standard') == 'heatset':
            names.add(prefix + 'heatset_depth')
    return names


def inspect_part(part, observed, extra_required):
    """Return concrete missing/failed coverage, never infer a part from summary PASS."""
    if any(not isinstance(observed.get(key), dict) for key in ('allowed', 'measured')):
        raise ValueError('part allowed/measured fields must be objects')
    checks = index_rows(observed['checks'], 'name')
    for row in checks.values():
        if row.get('status') not in ('pass', 'fail', 'skip', 'info'):
            raise ValueError(f'invalid status for {row["name"]}')
    required = BASE_CHECKS | ROUNDTRIP | feature_checks(part) | set(extra_required)
    if part.get('max_overhang_area_pct') is not None:
        required.add('overhang_area_pct')
    problems = [f'{name}: missing or not pass' for name in sorted(required)
                if checks.get(name, {}).get('status') != 'pass']
    problems.extend(f'{name}: failed check' for name, row in checks.items()
                    if row['status'] == 'fail' and name not in required)
    problems.extend(f'feature {f.get("id", i)}: type {f["type"]} is not measured by gate v1'
                    for i, f in enumerate(part.get('features', [])) if f['type'] != 'hole')
    if observed.get('object') != part['object'] or observed.get('status') != 'pass':
        problems.append('part object or status disagrees with the contract')
    try:
        minimum = finite(part['min_wall_mm'])
        if minimum <= 0:
            raise ValueError('an authored positive minimum wall is required')
        allowed = observed['allowed']
        for key in ('tol_mm', 'min_wall_mm', 'expected_shells'):
            finite(allowed[key])
        for value in allowed['target_dims_mm']:
            finite(value)
        expected = {key: part[key] for key in ('target_dims_mm', 'tol_mm', 'min_wall_mm')}
        expected['expected_shells'] = part.get('expected_shells', 1)
        if any(allowed.get(key) != value for key, value in expected.items()):
            raise ValueError('reported allowed values differ from the supplied spec')
        measured = observed['measured']
        samples = measured['wall_ray_samples']
        if type(samples) is not int or samples <= 0:
            raise ValueError('no positive wall sample count')
        if finite(measured['wall_min_mm']) < minimum:
            raise ValueError('measured wall is below the authored minimum')
        wall = checks['wall_thickness_screen']
        if finite(wall['limit']['min_wall_mm']) != minimum:
            raise ValueError('wall check was run against a different limit')
        if type(wall['value']['samples']) is not int or wall['value']['samples'] != samples:
            raise ValueError('wall sample count disagrees between report fields')
        for prefix in ('', 'roundtrip_'):
            for name in ZERO_CHECKS:
                if finite(checks[prefix + name]['value']) != 0:
                    raise ValueError(f'{prefix + name}: nonzero defect count')
            if finite(checks[prefix + 'signed_volume_positive']['value']) <= 0:
                raise ValueError('nonpositive signed volume')
            if finite(checks[prefix + 'shells']['value']) != expected['expected_shells']:
                raise ValueError('shell count disagrees with spec')
            bbox = checks[prefix + 'bbox_dims_mm']
            finite(bbox['limit']['tol'])
            for value in bbox['limit']['target']:
                finite(value)
            if bbox['limit'] != {'target': part['target_dims_mm'], 'tol': part['tol_mm']}:
                raise ValueError('bounding-box check used a different target/tolerance')
            values = bbox['value']
            if len(values) != 3:
                raise ValueError('bounding box must have three components')
            # v1 predicates decide on raw dimensions, then store four-decimal
            # display values. Audit their representable interval, not a new or
            # tighter geometry tolerance. Roundtrip raw bounds are not retained.
            quantum = Decimal('0.00005')
            for value, target in zip(values, part['target_dims_mm']):
                deviation = abs(Decimal(str(finite(value))) - Decimal(str(target)))
                if deviation > Decimal(str(part['tol_mm'])) + quantum:
                    raise ValueError('rounded bounding box contradicts the recorded pass')
        raw = measured['bbox_dims_mm']
        if len(raw) != 3 or any(abs(finite(v) - t) > part['tol_mm']
                               for v, t in zip(raw, part['target_dims_mm'])):
            raise ValueError('raw measured bounding box exceeds the authored tolerance')
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        problems.append(f'incomplete or inconsistent measurements: {exc}')
    return {'id': part['id'], 'object': part['object'], 'required_checks': sorted(required),
            'status': 'fail' if problems else 'pass', 'problems': problems}, checks
