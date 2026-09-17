"""Native repeated switch envelopes; geometry output is tested after GN input changes."""
import bpy
import meshkit as g
from boilerplates.bp_geonodes import create_geometry_node_tree,assign_geonodes_modifier,set_modifier_input
from agent_verify import world_bbox,tri_count


def build(keys):
    points=[(row['xy_mm'][0]/1000,row['xy_mm'][1]/1000,.01425) for row in keys]
    obj=g.mesh('RK_SWITCH_HOUSINGS',points,[])
    tree,inp,out=create_geometry_node_tree('RK_SWITCH_ARRAY')
    width=tree.interface.new_socket(name='Housing width',in_out='INPUT',socket_type='NodeSocketFloat')
    width.default_value,width.min_value,width.max_value=.0138,.013,.014
    size=tree.nodes.new('ShaderNodeCombineXYZ')
    size.inputs['Z'].default_value=.0017
    tree.links.new(inp.outputs[width.identifier],size.inputs['X'])
    tree.links.new(inp.outputs[width.identifier],size.inputs['Y'])
    cube=tree.nodes.new('GeometryNodeMeshCube')
    tree.links.new(size.outputs['Vector'],cube.inputs['Size'])
    instance=tree.nodes.new('GeometryNodeInstanceOnPoints')
    realize=tree.nodes.new('GeometryNodeRealizeInstances')
    tree.links.new(inp.outputs['Geometry'],instance.inputs['Points'])
    tree.links.new(cube.outputs['Mesh'],instance.inputs['Instance'])
    tree.links.new(instance.outputs['Instances'],realize.inputs['Geometry'])
    tree.links.new(realize.outputs['Geometry'],out.inputs['Geometry'])
    mod=assign_geonodes_modifier(obj,tree)
    set_modifier_input(mod,width.identifier,.0132)
    a,b=world_bbox(obj)
    narrow=b.x-a.x
    set_modifier_input(mod,width.identifier,.0138)
    a,b=world_bbox(obj)
    delta=b.x-a.x-narrow
    assert abs(delta-.0006)<1e-6,(delta,narrow,b.x-a.x)
    assert tri_count(obj)==len(keys)*12
    obj['gn_measured_width_change_m']=delta
    obj['role']='representative housing envelopes, not electrically qualified components'
    g.bevel(obj,.00035,3)
    # Smaller switch tops remain in the cap cavity; individual stems can follow presses.
    for i,row in enumerate(keys):
        xy=tuple(v/1000 for v in row['xy_mm'])
        flange=g.slab('RK_SWITCH_FLANGE_%02d'%i,.0156,.0156,.001,.0151,.0157,xy)
        flange['switch_index']=i
        top=g.slab('RK_SWITCH_TOP_%02d'%i,.013,.013,.0012,.0157,.0185,xy)
        top['role']='generic transparent switch cover'
        g.bevel(top,.00015,2)
        stem=g.slab('RK_SWITCH_STEM_%02d'%i,.004,.0012,.00015,.0183,.0195,xy)
        stem['role']='generic switch stem envelope; no fit qualification'
        for side in (-1,1):
            pin=g.cylinder('RK_CONTACT_%02d_%s'%(i,'L' if side<0 else 'R'),.00035,.0085,.0134,
                           (xy[0]+side*.0035,xy[1]-.0026),segments=32)
            pin['switch_index']=i
    return obj
