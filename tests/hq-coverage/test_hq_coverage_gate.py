import contextlib
import hashlib
import importlib.util
import io
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from hq_coverage.core import InputError, validate
import hq_coverage.core as coverage_core

spec = importlib.util.spec_from_file_location('hq_coverage_gate', ROOT / 'scripts/hq-coverage-gate.py')
gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path, value): path.write_text(json.dumps(value, indent=2)); return path
def chunk(kind, data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
def png(path, width, height, corrupt=False, fill=b'\x00\x00\x00\xff'):
    raw=b''.join(b'\0'+fill*width for _ in range(height))
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
    path.write_bytes(data[:-2] if corrupt else data); return path

class CoverageFixture:
    def __init__(self, root):
        self.root=Path(root); self.candidate=self.root/'candidate.blend'; self.script=self.root/'render.py'
        self.reference=self.root/'reference.png'; self.proof=self.root/'proof.png'; self.review=self.root/'review.md'
        for path, data in ((self.candidate,b'blend'),(self.script,b'print(1)'),(self.reference,b'reference'),(self.review,b'review')): path.write_bytes(data)
        png(self.proof,8,6); self.shot={'id':'hero','size':[8,6],'camera':{'location':[0,0,1],'target':[0,0,0],'projection':'ORTHO','clip_start':.001,'clip_end':100},'visibility':['feature']}
        self.plan=self.root/'shots.json'; dump(self.plan,{'settings':{'samples':128},'shots':[self.shot]})
        self.requirements=self.root/'requirements.json'; self.write_requirements()
        self.coverage=self.root/'coverage.json'; self.write_coverage()
    def pin(self, path): return {'path':path.name,'sha256':sha(path)}
    def write_requirements(self, features=None):
        if features is None: features=[{'id':'feature','reference':self.pin(self.reference),'objects':['OBJ'],'shot':'hero','falsifier':'missing silhouette','critical':True}]
        dump(self.requirements,{'features':features})
    def review_data(self, verdict='pass'):
        return {'feature':'feature','reviewer':'reviewer','verdict':verdict,'note':'Compared native proof against assigned source feature.',
                'report':self.pin(self.review),'binding':{},'proof':self.pin(self.proof)|{'shot_snapshot':self.shot,'region':[0,0,8,6]},'checks':{'framing':'pass','near_clip':'pass'}}
    def write_coverage(self, reviews=None, mode='preflight'):
        data={'version':1,'mode':mode,'purpose':'render-only','candidate':self.pin(self.candidate),'render_script':self.pin(self.script),'shot_plan':self.pin(self.plan),'requirements':self.pin(self.requirements),'reviews':reviews if reviews is not None else [self.review_data()]}
        for review in data['reviews']:
            review['binding']={'candidate_sha256':data['candidate']['sha256'],'render_script_sha256':data['render_script']['sha256'],'shot_plan_sha256':data['shot_plan']['sha256'],'requirements_sha256':data['requirements']['sha256']}
        dump(self.coverage,data); return data
    def data(self): return json.loads(self.coverage.read_text())
    def save(self,data): dump(self.coverage,data)


class CoverageGateTests(unittest.TestCase):
    def setUp(self): self.temp=tempfile.TemporaryDirectory(); self.fx=CoverageFixture(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def fresh(self):
        self.temp.cleanup(); self.temp=tempfile.TemporaryDirectory(); self.fx=CoverageFixture(self.temp.name)
    def invoke(self,*extra):
        out=io.StringIO()
        with contextlib.redirect_stdout(out): code=gate.main(['--coverage',str(self.fx.coverage),'--report',str(self.fx.root/'report.json'),*extra])
        return code,out.getvalue(),self.fx.root/'report.json'
    def invoke_at(self, report):
        out=io.StringIO()
        with contextlib.redirect_stdout(out): code=gate.main(['--coverage',str(self.fx.coverage),'--report',str(report)])
        return code, out.getvalue()
    def reroute_proof_hash(self):
        data=self.fx.data(); data['reviews'][0]['proof']['sha256']=sha(self.fx.proof); self.fx.save(data)

    def test_accepted_fixture_passes(self):
        code, text, report=self.invoke(); self.assertEqual(code,0); self.assertIn('AGENT_OK',text); self.assertEqual(json.loads(report.read_text())['status'],'pass')
    def test_missing_critical_review_fails(self):
        self.fx.write_coverage(reviews=[]); code,_,report=self.invoke(); self.assertEqual(code,1); self.assertEqual(json.loads(report.read_text())['issues'][0]['code'],'missing_review')
    def test_duplicate_or_unknown_review_is_invalid(self):
        data=self.fx.data(); data['reviews'].append(data['reviews'][0].copy()); self.fx.save(data); self.assertEqual(self.invoke()[0],2)
        self.fresh(); data=self.fx.data(); data['reviews'][0]['feature']='unknown'; self.fx.save(data); self.assertEqual(self.invoke()[0],2)
    def test_stale_top_level_pins_fail(self):
        for field, attr in [('candidate','candidate'),('render_script','script'),('shot_plan','plan'),('requirements','requirements')]:
            with self.subTest(field=field):
                path=getattr(self.fx, attr)
                if field == 'shot_plan':
                    body=json.loads(path.read_text()); body['settings']['samples']=129; dump(path, body)
                elif field == 'requirements': path.write_text(path.read_text()+' ')
                else: path.write_bytes(path.read_bytes()+b'x')
                code,_,report=self.invoke(); self.assertEqual(code,1); self.assertIn('stale_hash',[x['code'] for x in json.loads(report.read_text())['issues']]); self.fresh()
    def test_stale_reference_report_and_proof_fail(self):
        for attr, update in [('reference',None),('review',None),('proof','proof')]:
            with self.subTest(path=attr):
                path=getattr(self.fx, attr)
                path.write_bytes(path.read_bytes()+b'x') if update is None else png(path,8,6,fill=b'\x01\x00\x00\xff')
                code,_,report=self.invoke(); self.assertEqual(code,1); self.assertIn('stale_hash',[x['code'] for x in json.loads(report.read_text())['issues']]); self.fresh()
    def test_empty_inventory_and_no_critical_are_invalid(self):
        self.fx.write_requirements([]); self.fx.write_coverage(); self.assertEqual(self.invoke()[0],2)
        self.fresh(); self.fx.write_requirements([{'id':'f','reference':self.fx.pin(self.fx.reference),'objects':['x'],'shot':'hero','falsifier':'x','critical':False}]); self.fx.write_coverage(reviews=[]); self.assertEqual(self.invoke()[0],2)
    def test_empty_starter_settings_and_objects_are_invalid_when_pins_are_current(self):
        plan=json.loads(self.fx.plan.read_text()); plan['settings']={}; dump(self.fx.plan,plan); self.fx.write_coverage(); self.assertEqual(self.invoke()[0],2)
        self.fresh(); feature={'id':'feature','reference':self.fx.pin(self.fx.reference),'objects':[],'shot':'hero','falsifier':'missing silhouette','critical':True}
        self.fx.write_requirements([feature]); self.fx.write_coverage(); self.assertEqual(self.invoke()[0],2)
    def test_failed_pending_and_missing_checks_fail(self):
        for verdict in ('fail','pending'):
            self.fx.write_coverage([self.fx.review_data(verdict)]); self.assertEqual(self.invoke()[0],1); self.fresh()
        data=self.fx.data(); del data['reviews'][0]['checks']['near_clip']; self.fx.save(data); self.assertEqual(self.invoke()[0],1)
    def test_density_region_and_snapshot_fail(self):
        png(self.fx.proof,4,4); self.reroute_proof_hash(); self.assertEqual(self.invoke()[0],1); self.fresh()
        data=self.fx.data(); data['reviews'][0]['proof']['region']=[7,0,8,6]; self.fx.save(data); self.assertEqual(self.invoke()[0],1); self.fresh()
        plan=json.loads(self.fx.plan.read_text()); plan['shots'][0]['camera']['clip_end']=101; dump(self.fx.plan,plan); self.fx.write_coverage(); self.assertEqual(self.invoke()[0],1)
    def test_malformed_nonfinite_and_corrupt_png_are_invalid(self):
        plan=json.loads(self.fx.plan.read_text()); plan['shots'][0]['camera']['location'][0]=float('nan'); dump(self.fx.plan,plan); self.fx.write_coverage(); self.assertEqual(self.invoke()[0],2)
        self.fresh(); png(self.fx.proof,8,6,corrupt=True); self.reroute_proof_hash(); self.assertEqual(self.invoke()[0],2)
        self.fresh(); data=bytearray(self.fx.proof.read_bytes()); data[-5]^=1; self.fx.proof.write_bytes(data); self.reroute_proof_hash(); self.assertEqual(self.invoke()[0],2)
    def test_invalid_root_ids_and_missing_input_alias_do_not_escape_or_clobber(self):
        self.fx.coverage.write_text('[]'); self.assertEqual(self.invoke()[0],2)
        self.fresh(); plan=json.loads(self.fx.plan.read_text()); plan['shots'][0]['id']=[]; dump(self.fx.plan,plan); self.fx.write_coverage(); self.assertEqual(self.invoke()[0],2)
        self.fresh(); data=self.fx.data(); data['candidate']['path']='missing.blend'; self.fx.save(data)
        missing=self.fx.root/'missing.blend'; code,_=self.invoke_at(missing)
        self.assertEqual(code,2); self.assertFalse(missing.exists())
    def test_report_clobber_and_alias_are_refused(self):
        report=self.fx.root/'report.json'; report.write_text('old'); self.assertEqual(self.invoke_at(report)[0],2)
        self.assertEqual(self.invoke_at(self.fx.candidate)[0],2)
    def test_recheck_symlink_cannot_clobber_candidate_or_launch(self):
        report=self.fx.root/'launch-report.json'; before=self.fx.candidate.read_bytes(); actual=gate.validate; calls=[0]
        def race(coverage_path, report_path, refuse_existing=True):
            calls[0]+=1
            if calls[0]==2: report.symlink_to(self.fx.candidate)
            return actual(coverage_path, report_path, refuse_existing=refuse_existing)
        with patch.object(gate,'validate',side_effect=race), patch.object(gate.subprocess,'Popen') as popen:
            out=io.StringIO()
            with contextlib.redirect_stdout(out): code=gate.main(['--coverage',str(self.fx.coverage),'--report',str(report),'--launch'])
        self.assertEqual(code, 2); self.assertEqual(calls[0], 2); popen.assert_not_called(); self.assertEqual(self.fx.candidate.read_bytes(), before)
    def test_retrospective_launch_refusal_and_block_before_subprocess(self):
        self.fx.write_coverage(mode='retrospective')
        with patch.object(gate.subprocess,'Popen') as run: self.assertEqual(self.invoke('--launch')[0],1); run.assert_not_called()
        self.fresh(); self.fx.write_coverage(reviews=[])
        with patch.object(gate.subprocess,'Popen') as run: self.assertEqual(self.invoke('--launch')[0],1); run.assert_not_called()
    def test_launcher_uses_argv_and_propagates_failure(self):
        class Child:
            stdout=io.StringIO('AGENT_FAIL {"status":"fail"}\n')
            def wait(self): return 9
        with patch.object(gate.subprocess,'Popen',return_value=Child()) as run:
            code, text, report=self.invoke('--launch')
        self.assertEqual(code,9); self.assertIn('AGENT_FAIL',text); self.assertFalse(run.call_args.kwargs.get('shell',False)); self.assertEqual(run.call_args.args[0][0:3],['bash',str(ROOT/'scripts/headless-run.sh'),'--blend']); self.assertEqual(json.loads(report.read_text())['launch']['returncode'],9)
    def test_launcher_requires_success_sentinel(self):
        class Child:
            stdout=io.StringIO('render returned without payload receipt\n')
            def wait(self): return 0
        with patch.object(gate.subprocess,'Popen',return_value=Child()):
            code,_,report=self.invoke('--launch')
        self.assertEqual(code,1); self.assertEqual(json.loads(report.read_text())['status'],'launch_failed')
        self.fresh()
        class Failed:
            stdout=io.StringIO('AGENT_FAIL {"status":"fail"}\n')
            def wait(self): return 0
        with patch.object(gate.subprocess,'Popen',return_value=Failed()): code,_,report=self.invoke('--launch')
        self.assertEqual(code,1); self.assertEqual(json.loads(report.read_text())['status'],'launch_failed')
        self.fresh()
        class Malformed:
            stdout=io.StringIO('AGENT_OK unstructured\n')
            def wait(self): return 0
        with patch.object(gate.subprocess,'Popen',return_value=Malformed()): code,_,report=self.invoke('--launch')
        self.assertEqual(code,1); self.assertEqual(json.loads(report.read_text())['status'],'launch_failed')
        self.fresh()
        class Good:
            stdout=io.StringIO('AGENT_OK {"stage":"render"}\n')
            def wait(self): return 0
        with patch.object(gate.subprocess,'Popen',return_value=Good()): code,_,report=self.invoke('--launch')
        self.assertEqual(code,0); self.assertEqual(json.loads(report.read_text())['launch']['sentinel']['kind'],'AGENT_OK')
    def test_provenance_records_hashes_from_final_prelaunch_recheck(self):
        actual=gate.validate; calls=[0]
        def recheck(coverage_path, report_path, refuse_existing=True):
            calls[0]+=1
            if calls[0]==2:
                self.fx.candidate.write_bytes(b'changed candidate')
                data=self.fx.data(); data['candidate']['sha256']=sha(self.fx.candidate)
                data['reviews'][0]['binding']['candidate_sha256']=data['candidate']['sha256']; self.fx.save(data)
            return actual(coverage_path, report_path, refuse_existing=refuse_existing)
        class Good:
            stdout=io.StringIO('AGENT_OK {"stage":"render"}\n')
            def wait(self): return 0
        with patch.object(gate,'validate',side_effect=recheck), patch.object(gate.subprocess,'Popen',return_value=Good()):
            code,_,report=self.invoke('--launch')
        data=json.loads(report.read_text()); provenance=data['provenance']
        self.assertEqual(code,0); self.assertEqual(calls[0],2)
        self.assertEqual(provenance['coverage']['sha256'],sha(self.fx.coverage))
        self.assertEqual(provenance['inputs']['candidate']['sha256'],sha(self.fx.candidate))
        self.assertEqual(provenance['inputs']['render_script']['sha256'],sha(self.fx.script))
        self.assertEqual(provenance['inputs']['shot_plan']['sha256'],sha(self.fx.plan))
        self.assertEqual(provenance['inputs']['requirements']['sha256'],sha(self.fx.requirements))
        self.assertEqual(provenance['references'][0]['sha256'],sha(self.fx.reference))
        self.assertEqual(provenance['proofs'][0]['sha256'],sha(self.fx.proof))
        self.assertEqual(provenance['review_reports'][0]['sha256'],sha(self.fx.review))
    def test_changed_shot_plan_between_pin_and_parse_is_invalid(self):
        original=coverage_core.pinned
        def mutate_after_pin(base, value, label, cache, issues, paths):
            result=original(base, value, label, cache, issues, paths)
            if label == 'shot_plan':
                plan=json.loads(self.fx.plan.read_text()); plan['settings']['samples']=129; dump(self.fx.plan,plan)
            return result
        with patch.object(coverage_core, 'pinned', side_effect=mutate_after_pin):
            self.assertEqual(self.invoke()[0], 2)
