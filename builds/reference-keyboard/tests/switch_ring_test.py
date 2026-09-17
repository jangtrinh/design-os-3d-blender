"""Bore geometry and boss-clearance regression on the actual switch constructors."""
from pathlib import Path
import math
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import bpy
from mathutils import Vector
import switches,controls,inspect_fit
from agent_runtime import emit_ok
from production_gate import meshprep,topology

assert bpy.app.background
cover=switches.ring('CHECK_COVER',.0126,.0126,.0012,.0163,.02085,.0034)
flange=switches.ring('CHECK_FLANGE',.015,.015,.001,.0151,.0163,.0034)
cap=controls.keycap('CHECK_CAP'); cap.location.z=.01785
bpy.context.view_layer.update()
minimum=1
for obj,z in ((cover,.018),(flange,.0157)):
    bm=meshprep.evaluated_mm_bmesh(obj)
    try:
        checks,values=topology.evaluate(bm)
        assert not [c for c in checks if c['status']=='fail'],checks
    finally:bm.free()
    for i in range(96):
        angle=math.tau*(i+.37)/96
        hit,location,_,_=obj.ray_cast(Vector((0,0,z)),Vector((math.cos(angle),math.sin(angle),0)))
        assert hit
        radius=math.hypot(location.x,location.y)
        minimum=min(minimum,radius)
        assert .003398<radius<.003401,(obj.name,i,radius)
for travel in (0,.0005,.001,.0015,.002,.0025,.003):
    key=inspect_fit._tri_mesh(cap,-travel)
    for obj in (cover,flange):
        collided,reason=inspect_fit._intersects(key,inspect_fit._tri_mesh(obj))
        assert not collided,(travel,obj.name,reason)
# Moving the cap laterally must still expose interference rather than a weak test.
cap.location.x=.001
bpy.context.view_layer.update()
assert inspect_fit._intersects(inspect_fit._tri_mesh(cap),inspect_fit._tri_mesh(cover))[0]
emit_ok('switch-ring-bore-contract',minimum_measured_bore_radius_mm=minimum*1000,
        rays=192,travel_samples=7,collision_pairs=0,offset_negative_detected=True)
