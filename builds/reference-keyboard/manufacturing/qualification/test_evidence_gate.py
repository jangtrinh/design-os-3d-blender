"""Logic tests are synthetic and never written into the physical bench record set."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

import evidence_gate as gate


def snapshot_config(pin, metric):
    return {'frozen_at':'2025-01-01T00:00:00Z', 'test_configurations':{'TEST':{
        'metrics':[metric], 'hardware_mpn':'TEST', 'process_record':pin,
        'manufacturer_screw_torque_max_Nm':.1}}}


class EvidenceTests(unittest.TestCase):
    def test_uncertainty_inside_both_limits(self):
        self.assertTrue(gate.interval_pass(10, .2, 5, 25))
        self.assertFalse(gate.interval_pass(5, .2, 5, 25))
        self.assertFalse(gate.interval_pass(24.9, .2, 5, 25))

    def test_nonfinite_boolean_and_negative_uncertainty_rejected(self):
        for bad in (True, float('nan'), float('inf'), '5'):
            with self.assertRaises(ValueError): gate.interval_pass(bad, 0, 0, 1)
        with self.assertRaises(ValueError): gate.interval_pass(1, -.1, 0, 2)

    def test_stale_or_outside_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);path=root/'test-only.txt';path.write_text('SYNTHETIC UNIT TEST')
            pin={'path':path.name,'sha256':gate.sha(path)}
            self.assertEqual(gate.bounded_pin(root,pin),path.resolve())
            path.write_text('changed synthetic fixture')
            with self.assertRaises(ValueError):gate.bounded_pin(root,pin)
            with self.assertRaises(ValueError):gate.bounded_pin(root,{'path':'../outside.txt','sha256':'0'})

    def test_observation_units_calibration_and_load(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw=root/'SYNTHETIC-NOT-BENCH.txt';raw.write_text('UNIT TEST ONLY')
            pin={'path':raw.name,'sha256':gate.sha(raw)}
            criterion={'id':'knob_axial_slip','unit':'mm','min':0,'max':.2,'conditions':{'load_N':{'min':10}}}
            instrument={'unit':'mm','range_min':-1,'range_max':1,'valid_from':'2020-01-01',
                        'valid_until':'2099-01-01','calibration_record':pin}
            force=dict(instrument,unit='N',range_min=0,range_max=20)
            instruments={'I':instrument,'F':force}
            snapshot=snapshot_config(pin,criterion['id'])
            row={'sample_serial':'UNIT-TEST-ONLY','material_lot':'TEST','hardware_mpn':'TEST',
                 'operator':'TEST','measured_at':'2026-01-01T00:00:00Z','instrument_id':'I',
                 'unit':'mm','value':.1,'uncertainty':.01,'raw_record':pin,'configuration_id':'TEST',
                 'conditions':{'load_N':{'value':10.1,'uncertainty':.01,'instrument_id':'F','raw_record':pin}},'damage_observed':False}
            self.assertEqual(gate.check_observation(root,row,criterion,instruments,snapshot),[])
            for update in ({'unit':'N'},{'uncertainty':0},{'conditions':{'load_N':1}},
                           {'measured_at':'2099-01-01T00:00:00Z'},{'raw_record':{'path':raw.name,'sha256':'0'}},
                           {'damage_observed':True},{'hardware_mpn':'OTHER'},{'configuration_id':'UNKNOWN'},
                           {'measured_at':'2024-01-01T00:00:00Z'}):
                wrong=deepcopy(row);wrong.update(update)
                self.assertTrue(gate.check_observation(root,wrong,criterion,instruments,snapshot))
            instrument['valid_until']='2025-01-01'
            self.assertTrue(gate.check_observation(root,row,criterion,instruments,snapshot))

    def test_blank_or_synthetic_records_never_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            requirements={'metrics':[{'id':'m','unit':'N','min':1,'max':2,'samples':1,'group':'test','conditions':{}}],
                          'same_sample_cohorts':[],'digital_release_prerequisites':['erc'],'limitations':['TEST ONLY']}
            (root/'req.json').write_text(json.dumps(requirements))
            snapshot={'requirements':{'path':'req.json','sha256':gate.sha(root/'req.json')},
                      'design_inputs':[],'digital_prerequisites':{'erc':{'status':'not_run'}}}
            (root/'snapshot.json').write_text(json.dumps(snapshot))
            for origin in ('not_recorded','synthetic','simulation','physical_measurement'):
                record={'origin':origin,'selected_process':'UNIT TEST','instruments':[],'observations':[],
                        'design_snapshot_sha256':gate.sha(root/'snapshot.json')}
                (root/'records.json').write_text(json.dumps(record))
                result=gate.assess(root,root/'snapshot.json',root/'records.json')
                self.assertEqual(result['status'],'INCOMPLETE_MANUFACTURING_EVIDENCE')
                self.assertEqual(result['physical_records'],0)
                self.assertEqual(result['blocked_digital_prerequisites'],['erc'])

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.json';path.write_text('{"value":1,"value":2}')
            with self.assertRaises(ValueError):gate.load(path)

    def test_derived_ratio_uses_calibrated_torque_and_propagated_uncertainty(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw=root/'SYNTHETIC.txt';raw.write_text('UNIT TEST ONLY')
            pin={'path':raw.name,'sha256':gate.sha(raw)}
            criterion={'id':'post_strip_margin','unit':'ratio','min':3,'max':None,'conditions':{}}
            instrument={'unit':'Nm','range_min':0,'range_max':1,'valid_from':'2020-01-01',
                        'valid_until':'2099-01-01','calibration_record':pin}
            row={'sample_serial':'UNIT-TEST','material_lot':'TEST','hardware_mpn':'TEST','operator':'TEST',
                 'measured_at':'2026-01-01T00:00:00Z','instrument_id':'I','unit':'ratio','value':4,
                 'uncertainty':.5,'raw_record':pin,'damage_observed':True,'failure_mode':'thread_strip',
                 'configuration_id':'TEST',
                 'derivation':{'joint_failure_torque_Nm':.08,'assembly_torque_Nm':.02,
                               'failure_uncertainty_Nm':.005,'assembly_uncertainty_Nm':.001}}
            snapshot=snapshot_config(pin,criterion['id'])
            self.assertEqual(gate.check_observation(root,row,criterion,{'I':instrument},snapshot),[])
            row['uncertainty']=.01
            self.assertTrue(gate.check_observation(root,row,criterion,{'I':instrument},snapshot))
            row['uncertainty']=.5
            snapshot['test_configurations']['TEST']['manufacturer_screw_torque_max_Nm']=.01
            self.assertTrue(gate.check_observation(root,row,criterion,{'I':instrument},snapshot))

    def test_cohorts_require_same_hardware_process_and_forward_time(self):
        from record_checks import cohort_errors
        first={'metric':'before','sample_serial':'TEST','hardware_mpn':'TEST','material_lot':'TEST',
               'configuration_id':'TEST','measured_at':'2026-01-01T00:00:00Z'}
        second=dict(first,metric='after',measured_at='2026-01-02T00:00:00Z')
        self.assertFalse(cohort_errors([first,second],[['before','after']]))
        for update in ({'material_lot':'OTHER'},{'hardware_mpn':'OTHER'},{'configuration_id':'OTHER'},
                       {'measured_at':'2025-12-31T00:00:00Z'}):
            self.assertTrue(cohort_errors([first,dict(second,**update)],[['before','after']]))

    def test_digital_pass_requires_actual_source_binding_and_success_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);model=root/'model.test';model.write_text('SYNTHETIC')
            report=root/'report.json';report.write_text(json.dumps({'scene_sha256':gate.sha(model),'failed':[]}))
            snapshot={'design_inputs':[dict(gate.file_pin(root,model),role='model')],
                      'digital_prerequisites':{'geometry':{'status':'pass','evidence':gate.file_pin(root,report),
                      'bindings':[{'field':['scene_sha256'],'input_role':'model'}],
                      'assertions':[{'field':['failed'],'equals':[]}]}}}
            requirements={'digital_release_prerequisites':['geometry']}
            self.assertEqual(gate.digital_checks(root,snapshot,requirements),([],[]))
            for value in ({'scene_sha256':'old','failed':[]},{'scene_sha256':gate.sha(model),'failed':['defect']}):
                report.write_text(json.dumps(value))
                snapshot['digital_prerequisites']['geometry']['evidence']=gate.file_pin(root,report)
                self.assertTrue(gate.digital_checks(root,snapshot,requirements)[1])

    def test_assessment_detects_later_bench_record_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);raw=root/'raw.test';raw.write_text('UNIT TEST ONLY')
            req=root/'req.json';req.write_text(json.dumps({'metrics':[], 'same_sample_cohorts':[],
                'digital_release_prerequisites':[], 'limitations':['TEST ONLY']}))
            snapshot=root/'snapshot.json';snapshot.write_text(json.dumps({'schema_version':1,
                'frozen_at':'2025-01-01T00:00:00Z','requirements':gate.file_pin(root,req),
                'design_inputs':[dict(gate.file_pin(root,raw),role='fixture')],
                'test_configurations':{},'digital_prerequisites':{}}))
            records=root/'records.json';records.write_text(json.dumps({'origin':'synthetic','observations':[]}))
            assessment=gate.assess(root,snapshot,records)
            self.assertTrue(gate.validate_assessment(root,assessment))
            records.write_text(json.dumps({'origin':'changed-synthetic','observations':[]}))
            with self.assertRaises(ValueError):gate.validate_assessment(root,assessment)


if __name__=='__main__':
    unittest.main()
