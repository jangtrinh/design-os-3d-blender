"""Compute separated fork staging from projected envelopes, preserving final geometry."""
from pathlib import Path
import json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
units=json.loads((ROOT/'reports/units.json').read_text())
right=Vector((1,.55,0)).normalized()

def span(rows):
    result=[]
    for u in rows:
        c=Vector(u['center']);e=Vector(u['extent'])
        result.extend(right.dot(c+Vector((x*e.x,y*e.y,z*e.z)))
                      for x in (-.5,.5) for y in (-.5,.5) for z in (-.5,.5))
    return min(result),max(result)

report={}
for module in ('shoulder','elbow'):
    main=[u for u in units if u['group']==module and u['subassembly']!='fork']
    fork=[u for u in units if u['group']==module and u['subassembly']=='fork']
    distance=span(main)[1]-span(fork)[0]+.035
    delta=right*distance
    for u in units:
        if u['group']!=module:continue
        if u['subassembly']=='fork':u['sub_offset']=list(delta)
        if u['subassembly']=='carrier-left':u['sub_offset']=[0,-.075,0]
        if u['subassembly']=='carrier-right':u['sub_offset']=[0,.075,0]
    report[module]={'fork_offset':list(delta),'projected_gap_mm':35,
                    'carrier_axial_staging_mm':75}
(ROOT/'reports/units.json').write_text(json.dumps(units,indent=2))
(ROOT/'reports/staging-layout.json').write_text(json.dumps(report,indent=2))
print('SEPARATED_STAGING_PASS',report)
