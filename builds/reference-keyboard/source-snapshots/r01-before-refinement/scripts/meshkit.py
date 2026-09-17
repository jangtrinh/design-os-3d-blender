"""Small Blender-native geometry primitives, in metres and named before linking."""
import math
import bpy
import bmesh


def mesh(name,verts,faces):
    assert name not in bpy.data.objects,name
    data=bpy.data.meshes.new(name)
    data.from_pydata(verts,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def rounded_outline(w,d,r,segments=12):
    out=[]
    for q,(sx,sy) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1))):
        for j in range(segments+1):
            angle=q*math.pi/2+j*math.pi/(2*segments)
            out.append((sx*(w/2-r)+r*math.cos(angle),sy*(d/2-r)+r*math.sin(angle)))
    return out


def prism(name,profile,low,high):
    n=len(profile)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return mesh(name,[(x,y,z) for z in (low,high) for x,y in profile],faces)


def slab(name,w,d,r,low,high,xy=(0,0)):
    obj=prism(name,rounded_outline(w,d,r),low,high)
    obj.location.x,obj.location.y=xy
    return obj


def cylinder(name,r,low,high,xy=(0,0),segments=96):
    profile=[(r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments)) for i in range(segments)]
    obj=prism(name,profile,low,high)
    obj.location.x,obj.location.y=xy
    for polygon in obj.data.polygons:
        polygon.use_smooth=len(polygon.vertices)==4
    return obj


def assign(obj,mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def bevel(obj,width=.00025,segments=3):
    mod=obj.modifiers.new('Manufactured edge','BEVEL')
    mod.width,mod.segments=width,segments
    return obj


def numeric(obj):
    from boilerplates.bp_core import evaluated_mesh
    from agent_verify import world_bbox
    a,b=world_bbox(obj)
    with evaluated_mesh(obj) as (_,me):
        me.calc_loop_triangles()
        bm=bmesh.new()
        try:
            bm.from_mesh(me)
            bm.normal_update()
            value={'name':obj.name,'min_mm':[x*1000 for x in a],
                   'max_mm':[x*1000 for x in b],'dimensions_mm':[(b[i]-a[i])*1000 for i in range(3)],
                   'triangles':len(me.loop_triangles),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),
                   'signed_volume_m3':bm.calc_volume(signed=True)}
        finally:
            bm.free()
    return value
