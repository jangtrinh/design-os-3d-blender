"""Source-guided switch/stem prototype with a real moving receiver clearance."""
import math
import bpy
import meshkit as g
from project import interfaces
from boilerplates.bp_geonodes import create_geometry_node_tree,assign_geonodes_modifier,set_modifier_input
from agent_verify import world_bbox,tri_count


def ring(name,width,depth,radius,z0,z1,hole_radius,xy=(0,0)):
    # Uniform angular samples preserve the circular bore. Projecting only the
    # rounded rectangle's corner vertices previously created ~78-degree gaps on
    # straight sides and reduced the purported 3.4 mm bore radius to 2.64 mm.
    outer=[]; inner=[]
    for i in range(128):
        angle=math.tau*i/128
        c,s=math.cos(angle),math.sin(angle)
        lo,hi=0.0,math.hypot(width/2,depth/2)
        for _ in range(42):
            distance=(lo+hi)/2
            qx=max(abs(distance*c)-(width/2-radius),0)
            qy=max(abs(distance*s)-(depth/2-radius),0)
            if qx*qx+qy*qy<=radius*radius: lo=distance
            else: hi=distance
        outer.append((lo*c,lo*s))
        inner.append((hole_radius*c,hole_radius*s))
    n=len(outer)
    verts=[(x,y,z) for profile,z in ((outer,z0),(outer,z1),(inner,z0),(inner,z1)) for x,y in profile]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),
                      (j,i,2*n+i,2*n+j),(n+i,n+j,3*n+j,3*n+i)))
    obj=g.mesh(name,verts,faces)
    obj.location.x,obj.location.y=xy
    from mechanics import assert_solid
    assert_solid(obj)
    return obj


def cross_profile(span,horizontal,vertical):
    a,h,v=span/2,horizontal/2,vertical/2
    return [(-v,-a),(v,-a),(v,-h),(a,-h),(a,h),(v,h),
            (v,a),(-v,a),(-v,h),(-a,h),(-a,-h),(-v,-h)]


def build(keys):
    cfg=interfaces()['keycap']
    template=ring('TOOL_SWITCH_RING',.0138,.0138,.0007,0,.00335,.0034)
    template.hide_render=True
    template.hide_set(True)
    points=[(row['xy_mm'][0]/1000,row['xy_mm'][1]/1000,.01175) for row in keys]
    obj=g.mesh('RK_SWITCH_HOUSINGS',points,[])
    tree,inp,out=create_geometry_node_tree('RK_SWITCH_ARRAY')
    width=tree.interface.new_socket(name='Housing width',in_out='INPUT',socket_type='NodeSocketFloat')
    width.default_value,width.min_value,width.max_value=.0138,.013,.014
    info=tree.nodes.new('GeometryNodeObjectInfo')
    info.inputs['Object'].default_value=template
    scale=tree.nodes.new('ShaderNodeMath'); scale.operation='DIVIDE'; scale.inputs[1].default_value=.0138
    tree.links.new(inp.outputs[width.identifier],scale.inputs[0])
    vector=tree.nodes.new('ShaderNodeCombineXYZ'); vector.inputs['Z'].default_value=1
    tree.links.new(scale.outputs[0],vector.inputs['X']); tree.links.new(scale.outputs[0],vector.inputs['Y'])
    instances=tree.nodes.new('GeometryNodeInstanceOnPoints')
    realize=tree.nodes.new('GeometryNodeRealizeInstances')
    tree.links.new(inp.outputs['Geometry'],instances.inputs['Points'])
    tree.links.new(info.outputs['Geometry'],instances.inputs['Instance'])
    tree.links.new(vector.outputs['Vector'],instances.inputs['Scale'])
    tree.links.new(instances.outputs['Instances'],realize.inputs['Geometry'])
    tree.links.new(realize.outputs['Geometry'],out.inputs['Geometry'])
    mod=assign_geonodes_modifier(obj,tree)
    set_modifier_input(mod,width.identifier,.0132); a,b=world_bbox(obj); before=b.x-a.x
    set_modifier_input(mod,width.identifier,.0138); a,b=world_bbox(obj); delta=b.x-a.x-before
    assert abs(delta-.0006)<1e-6,delta
    assert tri_count(obj)==len(keys)*tri_count(template)
    obj['gn_measured_width_change_m']=delta
    obj['role']='custom hollow switch carrier; source-guided actuator, not complete commercial-switch CAD'
    for i,row in enumerate(keys):
        xy=tuple(v/1000 for v in row['xy_mm'])
        flange=ring('RK_SWITCH_FLANGE_%02d'%i,.015,.015,.001,.0151,.0163,.0034,xy)
        flange['switch_index']=i
        top=ring('RK_SWITCH_TOP_%02d'%i,.0126,.0126,.0012,.0163,.02085,.0034,xy)
        top['role']='custom guide cover with measured 6.8 mm boss clearance'
        stem=g.prism('RK_SWITCH_STEM_%02d'%i,cross_profile(.004,.00110,.00128),.01785,.02085)
        stem.location.x,stem.location.y=xy
        stem['role']='source-dimensioned cross actuator; factory switch compatibility remains a separate test'
        for side in (-1,1):
            pin=g.cylinder('RK_CONTACT_%02d_%s'%(i,'L' if side<0 else 'R'),.00035,.00865,.01175,
                           (xy[0]+side*.0035,xy[1]-.0026),segments=64)
            pin['switch_index']=i
    return obj
