"""Coverage receipt parsing and fail-closed validation; no Blender dependency."""
import hashlib
import json
import math
from pathlib import Path

from .png import PngError, dimensions


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


def shot_plan(value):
    value = mapping(value, 'shot_plan JSON')
    if not value.get('settings') or not isinstance(value['settings'], dict):
        raise InputError('shot_plan.settings must be a nonempty object')
    shots = value.get('shots')
    if not isinstance(shots, list) or not shots:
        raise InputError('shot_plan.shots must be a nonempty array')
    result = {}
    for index, shot in enumerate(shots):
        shot = mapping(shot, 'shot_plan.shots[%d]' % index)
        ident = text(shot.get('id'), 'shot.id')
        if ident in result: raise InputError('duplicate shot id: %s' % ident)
        size = shot.get('size')
        if not isinstance(size, list) or len(size) != 2: raise InputError('shot %s.size must be [width,height]' % ident)
        integer(size[0], 'shot %s.width' % ident); integer(size[1], 'shot %s.height' % ident)
        camera = mapping(shot.get('camera'), 'shot %s.camera' % ident)
        for key in ('location', 'target'):
            row = camera.get(key)
            if not isinstance(row, list) or len(row) != 3: raise InputError('shot %s.camera.%s must have 3 values' % (ident,key))
            for number in row: finite(number, 'shot %s.camera.%s' % (ident,key))
        if camera.get('projection') not in ('ORTHO','PERSP'): raise InputError('shot %s.camera.projection invalid' % ident)
        start, end = finite(camera.get('clip_start'), 'clip_start'), finite(camera.get('clip_end'), 'clip_end')
        if start <= 0 or end <= start: raise InputError('shot %s camera clip range invalid' % ident)
        visible = shot.get('visibility')
        if not isinstance(visible, list) or not all(isinstance(x,str) and x for x in visible): raise InputError('shot %s.visibility invalid' % ident)
        result[ident] = shot
    return result


def validate(coverage_path, report_path, refuse_existing=True):
    coverage_path, report_path = coverage_path.resolve(), report_path.resolve()
    if refuse_existing and report_path.exists(): raise InputError('report path already exists; choose a new path to avoid clobbering: %s' % report_path)
    coverage = mapping(load_json(coverage_path, 'coverage'), 'coverage')
    declared_paths(coverage_path, report_path)
    base, cache, paths = coverage_path.parent, {}, {coverage_path}
    if coverage.get('version') != 1: raise InputError('coverage.version must be 1')
    if coverage.get('mode') not in ('preflight','retrospective'): raise InputError('coverage.mode must be preflight or retrospective')
    if coverage.get('purpose') != 'render-only': raise InputError('coverage.purpose must be render-only')
    issues, warnings, results = [], [], []
    candidate, _ = pinned(base, coverage.get('candidate'), 'candidate', cache, issues, paths)
    render_script, _ = pinned(base, coverage.get('render_script'), 'render_script', cache, issues, paths)
    plan_path, _ = pinned(base, coverage.get('shot_plan'), 'shot_plan', cache, issues, paths)
    requirements_path, _ = pinned(base, coverage.get('requirements'), 'requirements', cache, issues, paths)
    plan = shot_plan(load_json(plan_path, 'shot_plan'))
    requirements = mapping(load_json(requirements_path, 'requirements'), 'requirements JSON')
    features = requirements.get('features')
    if not isinstance(features, list) or not features: raise InputError('requirements.features must be a nonempty array')
    known = {}
    for index, feature in enumerate(features):
        feature = mapping(feature, 'requirements.features[%d]' % index)
        ident = text(feature.get('id'), 'feature.id')
        if ident in known: raise InputError('duplicate feature id: %s' % ident)
        objects = feature.get('objects')
        if not isinstance(objects, list) or not objects or not all(isinstance(x,str) and x for x in objects): raise InputError('feature %s.objects invalid' % ident)
        if feature.get('shot') not in plan: raise InputError('feature %s references unknown shot %s' % (ident, feature.get('shot')))
        text(feature.get('falsifier'), 'feature %s.falsifier' % ident)
        if not isinstance(feature.get('critical'), bool): raise InputError('feature %s.critical must be bool' % ident)
        reference, _ = pinned(base, feature.get('reference'), 'feature %s.reference' % ident, cache, issues, paths)
        known[ident] = feature | {'_reference_path': str(reference)}
    if not any(f['critical'] for f in known.values()): raise InputError('requirements needs at least one critical feature')
    reviews = coverage.get('reviews')
    if not isinstance(reviews, list): raise InputError('coverage.reviews must be an array')
    by_feature = {}
    for index, review in enumerate(reviews):
        review = mapping(review, 'reviews[%d]' % index); ident = text(review.get('feature'), 'review.feature')
        if ident not in known: raise InputError('review references unknown feature: %s' % ident)
        if ident in by_feature: raise InputError('duplicate review for feature: %s' % ident)
        by_feature[ident] = review
    pins = {key: coverage[key]['sha256'] for key in ('candidate','render_script','shot_plan','requirements')}
    for ident, feature in known.items():
        review = by_feature.get(ident)
        row = {'id': ident, 'critical': feature['critical'], 'reviewed': bool(review)}
        if not review:
            (issues if feature['critical'] else warnings).append({'code':'missing_review','feature':ident,'message':'%s review is missing; add a current native-density review receipt' % ident})
            results.append(row); continue
        text(review.get('reviewer'), 'reviewer'); text(review.get('note'), 'review note')
        verdict = review.get('verdict')
        if verdict not in ('pass','fail','pending'): raise InputError('review %s verdict invalid' % ident)
        row['verdict'] = verdict
        report, _ = pinned(base, review.get('report'), 'review %s.report' % ident, cache, issues, paths)
        proof, _ = pinned(base, review.get('proof'), 'review %s.proof' % ident, cache, issues, paths)
        binding = mapping(review.get('binding'), 'review %s.binding' % ident)
        for key, expected in pins.items():
            if binding.get(key + '_sha256') != expected:
                issues.append({'code':'stale_binding','feature':ident,'message':'%s binding is stale; regenerate review for current %s' % (ident,key)})
        proof_data = mapping(review.get('proof'), 'review %s.proof' % ident)
        if canonical(proof_data.get('shot_snapshot')) != canonical(plan[feature['shot']]): issues.append({'code':'shot_snapshot_mismatch','feature':ident,'message':'%s proof shot snapshot differs from frozen shot plan' % ident})
        region = proof_data.get('region')
        if not isinstance(region,list) or len(region)!=4: raise InputError('review %s proof.region must be [x,y,width,height]' % ident)
        x,y=coordinate(region[0],'review %s proof.region.x' % ident),coordinate(region[1],'review %s proof.region.y' % ident)
        w,h=integer(region[2],'review %s proof.region.width' % ident),integer(region[3],'review %s proof.region.height' % ident)
        target_w,target_h=plan[feature['shot']]['size']
        if x+w>target_w or y+h>target_h: issues.append({'code':'region_out_of_bounds','feature':ident,'message':'%s proof region is outside shot %s' % (ident,feature['shot'])})
        try: actual_w,actual_h=dimensions(proof)
        except PngError as exc: raise InputError('review %s proof PNG invalid: %s' % (ident,exc)) from exc
        if (actual_w,actual_h)!=(w,h): issues.append({'code':'density_mismatch','feature':ident,'message':'%s proof dimensions do not equal declared region' % ident})
        checks = mapping(review.get('checks'), 'review %s.checks' % ident)
        for check in ('framing','near_clip'):
            if checks.get(check) != 'pass': issues.append({'code':'failed_check','feature':ident,'message':'%s %s must be pass' % (ident,check)})
        if verdict != 'pass':
            (issues if feature['critical'] else warnings).append({'code':'review_'+verdict,'feature':ident,'message':'%s review verdict is %s' % (ident,verdict)})
        results.append(row)
    if report_path in paths: raise InputError('report path aliases an input/proof/reference path: %s' % report_path)
    status = 'pass' if not issues else 'fail'
    return {'version':1,'status':status,'mode':coverage['mode'],'purpose':coverage['purpose'],
            'coverage':str(coverage_path),'candidate':str(candidate),'render_script':str(render_script),
            'issues':issues,'warnings':warnings,'features':results,'all_reviews_pass':all(r.get('verdict')=='pass' for r in results if r['reviewed'])}, coverage
