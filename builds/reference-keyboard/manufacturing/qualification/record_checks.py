"""Physical record consistency; identity checks do not authenticate a laboratory."""
from datetime import date
from evidence_io import bounded_pin, interval_pass, number, timestamp

CONDITION_UNITS = {'load_N': 'N', 'torque_Nm': 'Nm', 'hold_s': 's', 'ambient_degC': 'degC',
                   'soak_minutes': 'min', 'service_cycles': 'count', 'actuation_cycles': 'count',
                   'key_positions': 'count', 'encoders': 'count', 'events_per_control': 'count'}


def calibrated(root, measurement, unit, when, instruments):
    value, error = number(measurement['value']), number(measurement['uncertainty'])
    instrument = instruments[measurement['instrument_id']]
    if instrument['unit'] != unit:
        raise ValueError('instrument unit mismatch')
    if not date.fromisoformat(instrument['valid_from']) <= when.date() <= date.fromisoformat(instrument['valid_until']):
        raise ValueError('calibration not valid at measurement time')
    bounded_pin(root, instrument['calibration_record'])
    if unit == 'count':
        if value != int(value) or value < 0 or error != 0:
            raise ValueError('integer count with zero counting uncertainty required')
    elif error <= 0:
        raise ValueError('positive measurement uncertainty required')
    if not interval_pass(value, error, instrument['range_min'], instrument['range_max']):
        raise ValueError('reading outside calibrated instrument range')
    return value, error


def check_observation(root, row, criterion, instruments, snapshot):
    errors = []
    try:
        for key in ('sample_serial', 'material_lot', 'hardware_mpn', 'operator', 'measured_at', 'instrument_id', 'configuration_id'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f'missing {key}')
        if row.get('unit') != criterion['unit']:
            raise ValueError('metric unit mismatch')
        when = timestamp(row['measured_at'])
        if when < timestamp(snapshot['frozen_at']):
            raise ValueError('measurement predates frozen design')
        config = snapshot['test_configurations'][row['configuration_id']]
        if criterion['id'] not in config['metrics'] or row['hardware_mpn'] != config['hardware_mpn']:
            raise ValueError('specimen hardware or metric does not match frozen configuration')
        bounded_pin(root, config['process_record'])
        bounded_pin(root, row['raw_record'])
        ratio = criterion['id'] == 'post_strip_margin'
        value, error = number(row['value']), number(row['uncertainty'])
        if ratio:
            if row.get('damage_observed') is not True or row.get('failure_mode') not in ('thread_strip', 'screw_fracture', 'base_pull_through', 'post_fracture'):
                raise ValueError('joint-strength test needs an observed limiting failure mode')
            derived = row['derivation']
            failure, uf = calibrated(root, {'value': derived['joint_failure_torque_Nm'],
                'uncertainty': derived['failure_uncertainty_Nm'], 'instrument_id': row['instrument_id']}, 'Nm', when, instruments)
            assembly, ua = calibrated(root, {'value': derived['assembly_torque_Nm'],
                'uncertainty': derived['assembly_uncertainty_Nm'], 'instrument_id': row['instrument_id']}, 'Nm', when, instruments)
            if assembly <= ua or assembly + ua > number(config['manufacturer_screw_torque_max_Nm']):
                raise ValueError('assembly torque is invalid or exceeds selected screw limit')
            low, high = (failure - uf) / (assembly + ua), (failure + uf) / (assembly - ua)
            if abs(value - failure / assembly) > 1e-6 or error + 1e-9 < max(value - low, high - value):
                raise ValueError('joint-margin derivation or uncertainty is inconsistent')
        else:
            if row.get('damage_observed') is not False:
                raise ValueError('functional specimen damage is present or unrecorded')
            value, error = calibrated(root, row, criterion['unit'], when, instruments)
        minimum = criterion['min']
        if minimum == 0 and criterion['unit'] not in ('count', 'degC'):
            minimum = None
        if value < 0 and criterion['unit'] != 'degC':
            raise ValueError('negative magnitude measurement')
        if not interval_pass(value, error, minimum, criterion['max']):
            errors.append('uncertainty interval exceeds metric acceptance limits')
        for key, limits in criterion['conditions'].items():
            measurement = row.get('conditions', {})[key]
            bounded_pin(root, measurement['raw_record'])
            measured, uncertainty = calibrated(root, measurement, CONDITION_UNITS[key], when, instruments)
            if not interval_pass(measured, uncertainty, limits.get('min'), limits.get('max')):
                errors.append(f'calibrated test condition not met: {key}')
    except (ValueError, KeyError, TypeError, OSError) as exc:
        errors.append(str(exc))
    return errors


def cohort_errors(observations, cohorts):
    errors = []
    for cohort in cohorts:
        rows = {metric: {r.get('sample_serial'): r for r in observations if r.get('metric') == metric} for metric in cohort}
        if any(set(rows[m]) != set(rows[cohort[0]]) for m in cohort[1:]):
            errors.append(f'paired sample sets disagree: {cohort}')
            continue
        for serial in rows[cohort[0]]:
            previous = None
            for metric in cohort:
                row = rows[metric][serial]
                identity = tuple(row.get(k) for k in ('hardware_mpn', 'material_lot', 'configuration_id'))
                try:
                    when = timestamp(row['measured_at'])
                except (ValueError, KeyError):
                    continue
                if previous and (identity != previous[0] or when <= previous[1]):
                    errors.append(f'paired specimen identity/order mismatch: {cohort}, {serial}')
                previous = (identity, when)
    return errors
