"""Native, individually traceable process specimens; no assertion of physical fit."""
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import controls


def circle(radius, n=96):
    return [(radius * math.cos(i * math.tau / n), radius * math.sin(i * math.tau / n)) for i in range(n)]


def tube(name, outer_profile, inner_profile, height):
    verts, faces = [], []
    outer0 = controls._append_ring(verts, outer_profile, 0)
    outer1 = controls._append_ring(verts, outer_profile, height)
    inner0 = controls._append_ring(verts, inner_profile, 0)
    inner1 = controls._append_ring(verts, inner_profile, height)
    controls._join_rings(faces, outer0, outer1)
    controls._join_rings(faces, inner1, inner0)
    controls._planar_annulus(faces, verts, outer0, inner0)
    controls._planar_annulus(faces, verts, outer1, inner1)
    return controls._make_object(name, verts, faces)


def stepped(name, outer, inner=None):
    verts, faces, rings = [], [], []
    for radius, z in outer:
        rings.append(controls._append_ring(verts, circle(radius), z))
    for first, last in zip(rings, rings[1:]):
        controls._join_rings(faces, first, last)
    if inner is None:
        faces.extend([tuple(reversed(rings[0])), tuple(rings[-1])])
    else:
        lo = controls._append_ring(verts, circle(inner), outer[0][1])
        hi = controls._append_ring(verts, circle(inner), outer[-1][1])
        controls._join_rings(faces, hi, lo)
        controls._join_rings(faces, lo, rings[0])
        controls._join_rings(faces, rings[-1], hi)
    return controls._make_object(name, verts, faces)


def build(row, cfg):
    name, kind = row['id'], row['kind']
    if kind == 'keycap':
        obj = controls.keycap(name, receiver_span_m=row['span_mm']/1000,
                              receiver_horizontal_arm_m=row['horizontal_arm_mm']/1000,
                              receiver_vertical_arm_m=row['vertical_arm_mm']/1000,
                              receiver_depth_m=cfg['receiver_depth_mm']/1000)
    elif kind == 'D-gauge':
        radius, flat = row['diameter_mm']/2000, row['flat_offset_mm']/1000
        alpha = math.asin(flat/radius)
        arc = [(radius*math.cos(math.pi-alpha+(math.pi+2*alpha)*i/79),
                radius*math.sin(math.pi-alpha+(math.pi+2*alpha)*i/79)) for i in range(80)]
        # Join the exact circle endpoints by one straight D flat.
        obj = tube(name, circle(.007), arc, .008)
    elif kind == 'guide':
        obj = stepped(name, [(.0022,0),(.0022,.0015),(.003,.0015),
                             (.003,.0027),(.0022,.0027),(.0022,.0079)], row['diameter_mm']/2000)
    elif kind == 'pin':
        obj = stepped(name, [(.004,0),(.004,.002),(.001,.002),(.001,.012)])
    else:
        raise ValueError(kind)
    obj['specimen_id'], obj['specimen_kind'] = name, kind
    obj['physical_status'] = 'UNTESTED_PROCESS_SPECIMEN'
    return obj


def measure(obj, row):
    mesh = obj.data
    mesh.calc_loop_triangles()
    vertices = [v.co.copy() for v in mesh.vertices]
    faces = [tuple(t.vertices) for t in mesh.loop_triangles]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=True)
    def ray(origin, direction):
        hit = tree.ray_cast(Vector(origin), Vector(direction), .1)[0]
        if hit is None:
            raise AssertionError((obj.name, origin, direction, 'measurement ray missed'))
        return hit
    dims = [(max(v[i] for v in vertices)-min(v[i] for v in vertices))*1000 for i in range(3)]
    assert all(abs(a-b)<.03 for a,b in zip(dims,row['dims_mm'])), (obj.name,dims)
    result = {'id':obj.name, 'dimensions_mm':dims, 'triangles':len(faces)}
    if row['kind']=='keycap':
        x=ray((0,0,.0015),(1,0,0)).x*2000
        h=ray((.0015,0,.0015),(0,1,0)).y*2000
        v=ray((0,.0015,.0015),(1,0,0)).x*2000
        depth=ray((0,0,-.001),(0,0,1)).z*1000
        actual=[x,h,v,depth]; expected=[row['span_mm'],row['horizontal_arm_mm'],row['vertical_arm_mm'],3.2]
        assert all(abs(a-b)<.02 for a,b in zip(actual,expected)), (obj.name,actual)
        result['cross_mm']=actual
    elif row['kind']=='D-gauge':
        flat=ray((0,0,.004),(0,1,0)).y*1000
        back=-ray((0,0,.004),(0,-1,0)).y*1000
        assert abs(flat-row['flat_offset_mm'])<.02 and abs(back-row['diameter_mm']/2)<.02
        result['flat_offset_mm'],result['across_flat_mm']=flat,flat+back
    elif row['kind']=='guide':
        diameter=(ray((0,0,.004),(1,0,0))-ray((0,0,.004),(-1,0,0))).length*1000
        assert abs(diameter-row['diameter_mm'])<.02
        result['bore_mm']=diameter
    else:
        diameter=(ray((.01,0,.007),(-1,0,0))-ray((-.01,0,.007),(1,0,0))).length*1000
        assert abs(diameter-2)<.02
        result['pin_mm']=diameter
    return result
