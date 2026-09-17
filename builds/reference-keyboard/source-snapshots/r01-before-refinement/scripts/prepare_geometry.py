"""Generate the fixed dimensional and evidence contracts before detailed execution."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import ROOT,BUILD,layout,key_rows,write
from boilerplates.bp_parametric_contract import normalize_contract
from production_gate.spec import validate

data=layout()
dimension_keys=('width_mm','depth_mm','height_mm','key_top_mm','key_height_mm','switch_width_mm','switch_height_mm','knob_diameter_mm','knob_height_mm')
raw={'units':'mm','parameters':{name:{'value':data[name],'unit':'mm','min':data[name],'max':data[name]} for name in dimension_keys},
     'frames':{'base':{'parent':None,'origin':[0,0,0],'unit':'mm','axes':{'x':[1,0,0],'y':[0,1,0],'z':[0,0,1]}}},
     'datums':{'ground':{'frame':'base','position':[0,0,-2],'unit':'mm'},'plate':{'frame':'base','position':[0,0,13.6],'unit':'mm'}},
     'ports':{'usb':{'frame':'base','kind':'unqualified-USB-C-visual-envelope','roles':['visual']}},
     'roles':{'visual':['RK_BASE','RK_DIFFUSER','RK_PCB','RK_MAIN_PLATE']+[r['id'] for r in key_rows(data)]+['RK_KNOB_%d'%i for i in range(1,6)],
              'physical':['RK_BASE','RK_DIFFUSER','RK_MAIN_PLATE'],'collision':['RK_BASE','RK_DIFFUSER','RK_MAIN_PLATE']}}
write(BUILD/'dimensions-contract.json',raw)
normalize_contract(raw)


def holes(z,diam):
    return [{'id':'mount%d'%i,'type':'hole','axis':'z','center_mm':[x,y,z],
             'diameter_mm':diam,'tol_mm':.05} for i,(x,y) in enumerate(data['fasteners_xy_mm'])]


def part(name,dims,wall,features=()):
    return {'id':name,'object':name,'target_dims_mm':dims,'tol_mm':.05,
            'min_wall_mm':wall,'expected_shells':1,'orientation_up':'+z',
            'features':list(features),'material':'Prototype geometry only; actual material/process remains unqualified',
            'process':'Digital geometry and mesh export screening, no machine selected'}

spec={'schema_version':1,'units':'mm','project':'CK-001 reference reconstruction, digital geometry screening',
      'print_volume_mm':[320,200,100],'brim_margin_mm':5,
      'parts':[part('RK_BASE',[284,92,4],1.2,holes(1,3.4)),
               part('RK_DIFFUSER',[284,92,8],1.2,holes(8,5.8)),
               part('RK_MAIN_PLATE',[284,92,1.5],1.2,holes(14.3,3.4)),
               part('RK_KEY_00',[16.2,16.2,9.5],1.0),part('RK_KEY_41',[35,16.2,9.5],1.0),
               part('RK_KNOB_1',[16,16,18],1.15),part('RK_FOOT_0',[14,5,2],1.2)],
      'required_checks':['non_manifold_edges','non_contiguous_edges','zero_area_faces','bbox_dims_mm','signed_volume_positive','scale_applied','wall_thickness_screen'],
      'load_cases':[{'description':'Representative keyboard housing/controls; no physical load contract qualified'}],
      'physical_evidence':['The 320x200x100 envelope is a required prototype workspace, not a verified available printer.',
                           'Confirm exact switches, keycap retention and shaft D-flat before machining/printing functional controls.',
                           'Confirm PCB/electrical isolation, standoffs, screw engagement and physical assembly.',
                           'No material, load, thermal, optical, electrical or device-function qualification.']}
validate(spec)
write(BUILD/'spec.json',spec)
sources=[BUILD/'layout.json',BUILD/'spec.json',BUILD/'dimensions-contract.json']
sources += [BUILD/'scripts'/n for n in ('project.py','meshkit.py','mechanics.py','switches.py','controls.py')]
sources += list((ROOT/'scripts/agent_verify').glob('*.py'))
sources += list((ROOT/'scripts/production_gate').glob('*.py'))
sources += [ROOT/'specs/build-spec.schema.json',ROOT/'scripts/boilerplates/bp_core.py',ROOT/'scripts/boilerplates/bp_geonodes.py',ROOT/'scripts/boilerplates/bp_parametric_contract.py']
write(BUILD/'geometry-pipeline.json',{'version':1,'pipeline_id':'reference-keyboard-geometry','steps':[{
    'id':'geometry','script':'builds/reference-keyboard/pass-02-geometry.py','depends_on':[],
    'inputs':sorted(set(p.relative_to(ROOT).as_posix() for p in sources)),'artifact_inputs':[],
    'outputs':['model.blend','geometry.json','source-inputs.json','source-evidence.json','contract.json'],
    'required_postconditions':['keys','knobs','mesh_objects','gn_width_change_m'],'timeout_seconds':240},
    {'id':'gate','script':'builds/reference-keyboard/pass-03-gate.py','depends_on':['geometry'],
     'inputs':sorted(set(p.relative_to(ROOT).as_posix() for p in sources)),
     'artifact_inputs':['geometry:model.blend'],
     'outputs':['gate-report.json','stl/manifest.json']+['stl/'+p['id']+'.stl' for p in spec['parts']],
     'required_postconditions':['part_families','failed_parts','stl_files'],'timeout_seconds':240}]})
print('GEOMETRY_CONTRACTS_READY')
