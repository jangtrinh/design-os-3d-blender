"""Validate declared shot coverage without judging visual similarity."""
from .png import PngError, dimensions
from .inputs import (InputError, canonical, coordinate, declared_paths, digest, finite,
                     integer, load_json, mapping, pinned, report_path_is_safe, text)


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


def stable_json(path, expected_hash, label, cache):
    value = load_json(path, label, cache)
    if digest(path, cache) != expected_hash:
        raise InputError('%s changed while validating; retry with a frozen receipt' % label)
    return value


def validate(coverage_path, report_path, refuse_existing=True):
    coverage_path, report_path = coverage_path.resolve(), report_path.resolve()
    if refuse_existing and report_path.exists(): raise InputError('report path already exists; choose a new path to avoid clobbering: %s' % report_path)
    base, cache, paths = coverage_path.parent, {}, {coverage_path}
    coverage = mapping(load_json(coverage_path, 'coverage', cache), 'coverage')
    declared_paths(coverage_path, report_path, coverage)
    if coverage.get('version') != 1: raise InputError('coverage.version must be 1')
    if coverage.get('mode') not in ('preflight','retrospective'): raise InputError('coverage.mode must be preflight or retrospective')
    if coverage.get('purpose') != 'render-only': raise InputError('coverage.purpose must be render-only')
    issues, warnings, results = [], [], []
    coverage_hash = digest(coverage_path, cache)
    candidate, candidate_hash = pinned(base, coverage.get('candidate'), 'candidate', cache, issues, paths)
    render_script, render_script_hash = pinned(base, coverage.get('render_script'), 'render_script', cache, issues, paths)
    plan_path, plan_hash = pinned(base, coverage.get('shot_plan'), 'shot_plan', cache, issues, paths)
    requirements_path, requirements_hash = pinned(base, coverage.get('requirements'), 'requirements', cache, issues, paths)
    plan = shot_plan(stable_json(plan_path, plan_hash, 'shot_plan', cache))
    requirements = mapping(stable_json(requirements_path, requirements_hash, 'requirements JSON', cache), 'requirements JSON')
    features = requirements.get('features')
    if not isinstance(features, list) or not features: raise InputError('requirements.features must be a nonempty array')
    known = {}
    references = []
    for index, feature in enumerate(features):
        feature = mapping(feature, 'requirements.features[%d]' % index)
        ident = text(feature.get('id'), 'feature.id')
        if ident in known: raise InputError('duplicate feature id: %s' % ident)
        objects = feature.get('objects')
        if not isinstance(objects, list) or not objects or not all(isinstance(x,str) and x for x in objects): raise InputError('feature %s.objects invalid' % ident)
        if feature.get('shot') not in plan: raise InputError('feature %s references unknown shot %s' % (ident, feature.get('shot')))
        text(feature.get('falsifier'), 'feature %s.falsifier' % ident)
        if not isinstance(feature.get('critical'), bool): raise InputError('feature %s.critical must be bool' % ident)
        reference, reference_hash = pinned(base, feature.get('reference'), 'feature %s.reference' % ident, cache, issues, paths)
        references.append({'feature':ident, 'path':str(reference), 'sha256':reference_hash})
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
    proofs, review_reports = [], []
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
        report, report_hash = pinned(base, review.get('report'), 'review %s.report' % ident, cache, issues, paths)
        proof, proof_hash = pinned(base, review.get('proof'), 'review %s.proof' % ident, cache, issues, paths)
        review_reports.append({'feature':ident, 'path':str(report), 'sha256':report_hash})
        proofs.append({'feature':ident, 'path':str(proof), 'sha256':proof_hash})
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
    provenance = {'coverage':{'path':str(coverage_path), 'sha256':coverage_hash},
                  'inputs':{'candidate':{'path':str(candidate), 'sha256':candidate_hash},
                            'render_script':{'path':str(render_script), 'sha256':render_script_hash},
                            'shot_plan':{'path':str(plan_path), 'sha256':plan_hash},
                            'requirements':{'path':str(requirements_path), 'sha256':requirements_hash}},
                  'references':references, 'proofs':proofs, 'review_reports':review_reports}
    return {'version':1,'status':status,'mode':coverage['mode'],'purpose':coverage['purpose'],
            'coverage':str(coverage_path),'candidate':str(candidate),'render_script':str(render_script),
            'issues':issues,'warnings':warnings,'features':results,'provenance':provenance,
            'all_reviews_pass':all(r.get('verdict')=='pass' for r in results if r['reviewed'])}, coverage
