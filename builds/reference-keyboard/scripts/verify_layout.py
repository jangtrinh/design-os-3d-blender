"""Host-side checker for actual keyboard geometry read-back, millimetres."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

COMPONENTS={"RK_BASE","RK_DIFFUSER","RK_PCB","RK_MAIN_PLATE","RK_SWITCH_HOUSINGS"}
POS_TOL=0.25
DIM_TOL=0.05

def _expected(value):
    if isinstance(value,dict): return value
    return json.loads(Path(value).read_text(encoding="utf-8")) if isinstance(value,(str,Path)) else json.loads(value)

def _objects(report):
    raw=report.get("objects")
    rows=[dict(v,name=k) for k,v in raw.items()] if isinstance(raw,dict) else raw
    if not isinstance(rows,list): raise ValueError("scene report must contain objects")
    names=[r.get("name") for r in rows]
    if any(not isinstance(n,str) or not n for n in names) or len(names)!=len(set(names)):
        raise ValueError("object names must be unique non-empty strings")
    return rows

def _bbox(row):
    box=row.get("bbox_mm")
    if isinstance(box,dict): lo,hi=box.get("min"),box.get("max")
    elif isinstance(box,list) and len(box)==2: lo,hi=box
    else: lo,hi=row.get("min_mm"),row.get("max_mm")
    if not (isinstance(lo,list) and isinstance(hi,list) and len(lo)==len(hi)==3):
        raise ValueError(f"{row['name']} missing 3D bbox")
    vals=[float(v) for v in lo+hi]
    if not all(math.isfinite(v) for v in vals) or any(vals[i]>vals[i+3] for i in range(3)):
        raise ValueError(f"{row['name']} invalid bbox")
    return vals[:3],vals[3:]

def _box2(row,field):
    box=row.get(field)
    if not (isinstance(box,list) and len(box)==2 and all(isinstance(v,list) and len(v)==2 for v in box)):
        raise ValueError(f"{row['name']} missing {field}")
    vals=[float(v) for pair in box for v in pair]
    if not all(math.isfinite(v) for v in vals) or vals[0]>vals[2] or vals[1]>vals[3]:
        raise ValueError(f"{row['name']} invalid {field}")
    return vals[:2],vals[2:]

def _center(row):
    lo,hi=_bbox(row); return [(lo[i]+hi[i])/2 for i in range(3)]

def _dims(row):
    lo,hi=_bbox(row); return [hi[i]-lo[i] for i in range(3)]

def _expected_keys(layout):
    ox,oy=map(float,layout["main_origin_mm"]); px,py=float(layout["pitch_x_mm"]),float(layout["pitch_y_mm"])
    pts=[(ox+c*px,oy-r*py) for r,row in enumerate(layout["main_rows"]) for c in range(len(row))]
    pts += [(ox+float(k["column"])*px,oy-3*py) for k in layout["bottom_row"]]
    rx,ry=map(float,layout["rear_macros"]["origin_mm"]); rp=float(layout["rear_macros"]["pitch_mm"])
    pts += [(rx+i*rp,ry) for i in range(int(layout["rear_macros"]["count"]))]
    return pts+[tuple(map(float,p)) for p in layout["left_macros_mm"]]

def _ordered(rows,expected,tol=POS_TOL):
    left=list(rows); out=[]; worst=0.0
    for p in expected:
        if not left: return None,float("inf")
        i,d=min(enumerate(math.hypot(_center(r)[0]-p[0],_center(r)[1]-p[1]) for r in left),key=lambda x:x[1])
        worst=max(worst,d)
        if d>tol: return None,worst
        out.append(left.pop(i))
    return (out,worst) if not left else (None,float("inf"))

def _rect_gap(a,b):
    alo,ahi=_box2(a,"top_bbox_mm"); blo,bhi=_box2(b,"top_bbox_mm")
    return math.hypot(max(alo[0]-bhi[0],blo[0]-ahi[0],0),max(alo[1]-bhi[1],blo[1]-ahi[1],0))

def _circle_rect(c,r,row):
    lo,hi=_bbox(row); dx=max(lo[0]-c[0],0,c[0]-hi[0]); dy=max(lo[1]-c[1],0,c[1]-hi[1])
    return math.hypot(dx,dy)-r

def run(scene_report_dict:dict,expected_layout_json)->dict:
    layout,rows=_expected(expected_layout_json),_objects(scene_report_dict)
    for row in rows: _bbox(row)
    stack=layout.get("stack_mm")
    if not isinstance(stack,dict): raise ValueError("layout.stack_mm is required")
    by={r["name"]:r for r in rows}; checks=[]
    def add(name,ok,actual,expected):
        checks.append({"name":name,"status":"pass" if ok else "fail","actual":actual,"expected":expected})
    def unqualified(name,actual,expected):
        checks.append({"name":name,"status":"unqualified","actual":actual,"expected":expected})

    missing=sorted(COMPONENTS-by.keys())
    add("required_components",not missing,missing,"none missing")
    keys=[r for r in rows if r["name"].startswith("RK_KEY_")]
    switch_tops=[r for r in rows if re.fullmatch(r"RK_SWITCH_TOP_\d{2}",r["name"])]
    switch_stems=[r for r in rows if re.fullmatch(r"RK_SWITCH_STEM_\d{2}",r["name"])]
    housing=by.get("RK_SWITCH_HOUSINGS")
    knobs=[r for r in rows if r["name"].startswith("RK_KNOB_")]
    feet=[r for r in rows if r["name"].startswith("RK_FOOT_")]
    exp=_expected_keys(layout); expected_count=len(exp)
    add("key_count",len(keys)==expected_count,len(keys),expected_count)
    add("switch_count",len(switch_tops)==expected_count,len(switch_tops),expected_count)
    add("switch_stem_count",len(switch_stems)==expected_count,len(switch_stems),expected_count)
    add("knob_count",len(knobs)==len(layout["knobs_mm"]),len(knobs),len(layout["knobs_mm"]))
    add("foot_count",len(feet)==4,len(feet),4)

    layer_specs={
        "RK_BASE":("base_bottom","base_top"),
        "RK_DIFFUSER":("diffuser_bottom","diffuser_top"),
        "RK_PCB":("pcb_bottom","pcb_top"),
        "RK_MAIN_PLATE":("plate_bottom","plate_top"),
    }
    for name,(low_key,high_key) in layer_specs.items():
        if low_key not in stack or high_key not in stack: raise ValueError(f"layout.stack_mm missing {low_key}/{high_key}")
        if name in by:
            lo,hi=_bbox(by[name]); z0,z1=float(stack[low_key]),float(stack[high_key])
            add(name.lower()+"_z",abs(lo[2]-z0)<=DIM_TOL and abs(hi[2]-z1)<=DIM_TOL,
                [round(lo[2],4),round(hi[2],4)],[z0,z1])
    if "RK_BASE" in by:
        lo,hi=_bbox(by["RK_BASE"]); s=_dims(by["RK_BASE"]); target=[float(layout["width_mm"]),float(layout["depth_mm"])]
        add("base_footprint",abs(s[0]-target[0])<=DIM_TOL and abs(s[1]-target[1])<=DIM_TOL,
            [round(s[0],4),round(s[1],4)],target)
        add("base_center_xy",abs((lo[0]+hi[0])/2)<=POS_TOL and abs((lo[1]+hi[1])/2)<=POS_TOL,
            [round((lo[0]+hi[0])/2,4),round((lo[1]+hi[1])/2,4)],[0,0])
    if "RK_MAIN_PLATE" in by:
        d=_dims(by["RK_MAIN_PLATE"]); target=[float(layout["width_mm"]),float(layout["depth_mm"])]
        add("main_plate_footprint",abs(d[0]-target[0])<=DIM_TOL and abs(d[1]-target[1])<=DIM_TOL,
            [round(d[0],4),round(d[1],4)],target)

    foot_z=[float(stack["foot_bottom"]),float(stack["foot_top"])]
    if len(feet)==4:
        fd=[_dims(r) for r in feet]; z=[(_bbox(r)[0][2],_bbox(r)[1][2]) for r in feet]
        add("foot_envelope",all(max(abs(d[i]-[14,5,2][i]) for i in range(3))<=DIM_TOL for d in fd),
            [[round(v,4) for v in d] for d in fd],[14,5,2])
        add("foot_z",all(abs(a-foot_z[0])<=DIM_TOL and abs(b-foot_z[1])<=DIM_TOL for a,b in z),
            [[round(a,4),round(b,4)] for a,b in z],foot_z)

    product=[r for r in rows if r["name"].startswith("RK_")]
    if product:
        minz=min(_bbox(r)[0][2] for r in product); maxz=max(_bbox(r)[1][2] for r in product)
        actual_height=maxz-minz; target_height=float(layout["height_mm"])
        add("overall_height",abs(actual_height-target_height)<=DIM_TOL,
            {"min_z_mm":round(minz,4),"max_z_mm":round(maxz,4),"height_mm":round(actual_height,4)},
            {"height_mm":target_height,"tol_mm":DIM_TOL})

    key_order,key_err=_ordered(keys,exp) if len(keys)==expected_count else (None,float("inf"))
    sw_order,sw_err=_ordered(switch_tops,exp) if len(switch_tops)==expected_count else (None,float("inf"))
    if key_order:
        for r in key_order: _box2(r,"top_bbox_mm")
        add("key_centers",key_err<=POS_TOL,round(key_err,4),{"max_error_mm":POS_TOL})
        h=[_dims(r)[2] for r in key_order]; key_h=float(layout["key_height_mm"])
        add("key_height",all(abs(v-key_h)<=POS_TOL for v in h),[round(min(h),4),round(max(h),4)],key_h)
        key_z=[float(stack["key_bottom"]),float(stack["key_bottom"])+key_h]
        z=[(_bbox(r)[0][2],_bbox(r)[1][2]) for r in key_order]
        add("key_z",all(abs(a-key_z[0])<=DIM_TOL and abs(b-key_z[1])<=DIM_TOL for a,b in z),
            [round(min(a for a,_ in z),4),round(max(b for _,b in z),4)],key_z)
        gaps=[_rect_gap(key_order[i],key_order[j]) for i in range(expected_count) for j in range(i+1,expected_count)]
        add("key_top_spacing",min(gaps)>=1,round(min(gaps),4),{"min_mm":1})
    if sw_order:
        add("switch_centers",sw_err<=POS_TOL,round(sw_err,4),{"max_error_mm":POS_TOL})

    if housing is not None:
        shell_count=housing.get("evaluated_connected_shells")
        if isinstance(shell_count,int) and not isinstance(shell_count,bool):
            add("switch_repeat_count",shell_count==expected_count,shell_count,expected_count)
        else:
            unqualified("switch_repeat_count","evaluated connected-shell count not exported",
                        {"required":"RK_SWITCH_HOUSINGS.evaluated_connected_shells","count":expected_count})
        cells=(scene_report_dict.get('geometry_evidence') or {}).get('switch_assembly_envelope')
        expected_size=[float(layout['switch_width_mm']),float(layout['switch_width_mm']),float(layout['switch_height_mm'])]
        if isinstance(cells,dict) and cells.get('method')=='evaluated_per_cell_union_bbox' and len(cells.get('cells',[]))==expected_count:
            sizes=[]
            indices=[]
            for cell in cells['cells']:
                row={'name':'switch-cell-'+str(cell['index']),'bbox_mm':cell['bbox_mm']}
                sizes.append(_dims(row)); indices.append(cell['index'])
            assert len(set(indices))==expected_count,'duplicate switch-cell evidence'
            errors=[max(abs(size[i]-expected_size[i]) for i in range(3)) for size in sizes]
            add('switch_assembly_envelope',max(errors)<=DIM_TOL,
                {'cells':len(sizes),'max_error_mm':max(errors)},{'nominal_mm':expected_size,'tolerance_mm':DIM_TOL})
        else:
            unqualified('switch_assembly_envelope','missing per-cell evaluated geometry',
                        {'required':'geometry_evidence.switch_assembly_envelope','nominal_mm':expected_size})

    collision=(scene_report_dict.get("geometry_evidence") or {}).get("switch_keycap_overlap")
    if isinstance(collision,dict) and collision.get("method")=="evaluated_mesh_intersection_common_z" and collision.get("pairs_checked")==expected_count:
        n=collision.get("collision_pairs")
        if isinstance(n,int) and not isinstance(n,bool): add("switch_keycap_overlap_collision",n==0,n,0)
        else: unqualified("switch_keycap_overlap_collision",collision,{"collision_pairs":0,"pairs_checked":expected_count})
    else:
        unqualified("switch_keycap_overlap_collision",collision or "missing",
                    {"method":"evaluated_mesh_intersection_common_z","pairs_checked":expected_count,"collision_pairs":0})

    if len(knobs)==len(layout["knobs_mm"]):
        order,err=_ordered(knobs,[tuple(map(float,p)) for p in layout["knobs_mm"]]); add("knob_centers",order is not None,round(err,4),{"max_error_mm":POS_TOL})
        kd=[_dims(r) for r in knobs]; kz=[(_bbox(r)[0][2],_bbox(r)[1][2]) for r in knobs]
        knob_d=float(layout["knob_diameter_mm"]); knob_h=float(layout["knob_height_mm"])
        add("knob_envelope",all(abs(d[0]-knob_d)<=POS_TOL and abs(d[1]-knob_d)<=POS_TOL and abs(d[2]-knob_h)<=POS_TOL for d in kd),
            [[round(v,4) for v in d] for d in kd],[knob_d,knob_d,knob_h])
        knob_z=[float(stack["knob_bottom"]),float(stack["knob_bottom"])+knob_h]
        add("knob_z",all(abs(a-knob_z[0])<=DIM_TOL and abs(b-knob_z[1])<=DIM_TOL for a,b in kz),
            [[round(a,4),round(b,4)] for a,b in kz],knob_z)
        circles=[(_center(r)[:2],max(_dims(r)[0],_dims(r)[1])/2) for r in knobs]
        gaps=[math.hypot(a[0][0]-b[0][0],a[0][1]-b[0][1])-a[1]-b[1] for i,a in enumerate(circles) for b in circles[i+1:]]+[_circle_rect(c,r,k) for c,r in circles for k in keys]
        add("knob_planar_disjoint",min(gaps)>=0,round(min(gaps),4),{"min_margin_mm":0})
        if "RK_BASE" in by:
            blo,bhi=_bbox(by["RK_BASE"]); margins=[min(c[0]-r-blo[0],bhi[0]-c[0]-r,c[1]-r-blo[1],bhi[1]-c[1]-r) for c,r in circles]
            add("knob_base_margin",min(margins)>=0,round(min(margins),4),{"min_mm":0})

    failed=[c["name"] for c in checks if c["status"]=="fail"]
    unqualified_names=[c["name"] for c in checks if c["status"]=="unqualified"]
    return {
        "status":"pass" if not failed else "fail",
        "physical_scope_status":"not_tested",
        "digital_interface_scope":"unqualified" if unqualified_names else "checked",
        "checks":checks,"failed":failed,"unqualified":unqualified_names,
        "limits":[
            "Overall 32 mm is checked as maxZ-minZ across actual RK_* geometry; feet at -2 mm and knob tops at 30 mm therefore span 32 mm.",
            "Switch TOP/STEM object counts establish interpreted layout repetition only. Actual RK_SWITCH_HOUSINGS repeat count requires an evaluated connected-shell count from the Blender producer.",
            "Switch assembly dimensions are checked only when the caller supplies actual per-cell evaluated geometry; array bounds alone are insufficient.",
            "Switch/keycap fit requires evaluated mesh intersection at their common Z range. Full-body XY containment inside a cap cavity is not a valid substitute.",
            "Layout checks do not establish image likeness, switch/socket/PCB compatibility, load, thermal, print success or manufacture qualification."
        ]}

if __name__=="__main__":
    import sys
    print(json.dumps(run(json.loads(Path(sys.argv[1]).read_text()),sys.argv[2]),indent=2,allow_nan=False))
