"""Reference-keyboard data, source identity and exclusive output helpers."""
import hashlib
import json
import os
from pathlib import Path
import sys

BUILD = Path(__file__).resolve().parents[1]
ROOT = BUILD.parents[1]
sys.path.insert(0, str(ROOT/'scripts'))


def layout():
    return json.loads((BUILD/'layout.json').read_text())


def interfaces():
    return json.loads((BUILD/'interfaces.json').read_text())


def spec_path():
    return BUILD/'spec-B.json' if layout()['revision'].startswith('B-') else BUILD/'spec.json'


def contract_path():
    return BUILD/'dimensions-contract-B.json' if layout()['revision'].startswith('B-') else BUILD/'dimensions-contract.json'


def key_rows(data=None):
    data = data or layout()
    x0,y0 = data['main_origin_mm']
    keys=[]
    for row,labels in enumerate(data['main_rows']):
        for col,label in enumerate(labels):
            keys.append({'id':'RK_KEY_%02d'%len(keys),'label':label,'units':1,
                         'xy_mm':[x0+col*data['pitch_x_mm'],y0-row*data['pitch_y_mm']],
                         'group':'main','row':row,'column':col})
    for item in data['bottom_row']:
        col=item['column']
        keys.append({'id':'RK_KEY_%02d'%len(keys),'label':item['label'],'units':item['units'],
                     'xy_mm':[x0+col*data['pitch_x_mm'],y0-3*data['pitch_y_mm']],
                     'group':'main','row':3,'column':col})
    macros=data['rear_macros']
    for i in range(macros['count']):
        keys.append({'id':'RK_KEY_%02d'%len(keys),'label':'dot','units':1,
                     'xy_mm':[macros['origin_mm'][0]+i*macros['pitch_mm'],macros['origin_mm'][1]],'group':'loop'})
    for xy in data['left_macros_mm']:
        keys.append({'id':'RK_KEY_%02d'%len(keys),'label':'dot','units':1,'xy_mm':xy,'group':'nano'})
    return keys


def output_context():
    out=Path(os.environ['DESIGN_OS_OUTPUT_DIR']).resolve()
    assert out.is_relative_to(BUILD), out
    assert not any(out.iterdir()), 'refuse mixed attempt output'
    return out,json.loads(os.environ['DESIGN_OS_INPUTS_JSON'])


def write(path,value):
    with Path(path).open('x') as handle:
        json.dump(value,handle,indent=2,allow_nan=False)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
