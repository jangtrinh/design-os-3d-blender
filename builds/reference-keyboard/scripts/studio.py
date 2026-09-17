"""Small native product studio with pinned capture context and no external textures."""
import bpy
import bmesh
import math
from mathutils import Vector
from agent_verify import framing,frame_stats


def finish_control_normals():
    """Smooth curved control faces while preserving sharp manufactured boundaries.

    Only normal/shading flags change. The vertex coordinates and face loops are
    compared before/after; receiver, shaft and slot geometry remain identical.
    """
    seen=set()
    counts={'meshes':0,'smooth_faces':0,'sharp_edges':0}
    for obj in bpy.context.scene.objects:
        if obj.type!='MESH' or not obj.name.startswith(('RK_KEY_','RK_KNOB_')):
            continue
        mesh=obj.data
        if mesh.as_pointer() in seen:
            continue
        seen.add(mesh.as_pointer())
        before=(tuple(tuple(v.co) for v in mesh.vertices),
                tuple(tuple(p.vertices) for p in mesh.polygons))
        bm=bmesh.new()
        try:
            bm.from_mesh(mesh)
            bm.normal_update()
            for face in bm.faces:
                face.smooth=True
            for edge in bm.edges:
                edge.smooth=(len(edge.link_faces)==2 and
                             edge.calc_face_angle() < math.radians(35))
                counts['sharp_edges']+=int(not edge.smooth)
            bm.to_mesh(mesh)
        finally:
            bm.free()
        mesh.update()
        after=(tuple(tuple(v.co) for v in mesh.vertices),
               tuple(tuple(p.vertices) for p in mesh.polygons))
        assert after==before,(obj.name,'normal finish changed geometry')
        counts['meshes']+=1
        counts['smooth_faces']+=sum(p.use_smooth for p in mesh.polygons)
    return counts


def material(name,color,metal=0,rough=.35):
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    shader=mat.node_tree.nodes.get('Principled BSDF')
    assert {'Base Color','Metallic','Roughness'} <= set(shader.inputs.keys())
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Metallic'].default_value=metal
    shader.inputs['Roughness'].default_value=rough
    return mat


def palette():
    result={'black':material('RK_Anodized_black',(.004,.005,.007),.35),
            'key':material('RK_Black_PBT',(.007,.008,.009),0,.46),
            'silver':material('RK_Brushed_aluminum',(.46,.49,.51),.72,.28),
            'legend':material('RK_White_legends',(.77,.80,.82),0,.52),
            'rubber':material('RK_Rubber',(.012,.014,.016),0,.65),
            'gold':material('RK_Brass_contacts',(.53,.28,.08),.8,.25),
            'switch':material('RK_Switch_polymer',(.037,.042,.047),0,.32)}
    result['key'].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.22
    mat=material('RK_RGB_diffuser',(.42,.34,.64),0,.17)
    nodes,links=mat.node_tree.nodes,mat.node_tree.links
    shader=nodes.get('Principled BSDF')
    shader.inputs['Transmission Weight'].default_value=.65
    shader.inputs['IOR'].default_value=1.49
    shader.inputs['Emission Strength'].default_value=.35
    coord=nodes.new('ShaderNodeTexCoord')
    xyz=nodes.new('ShaderNodeSeparateXYZ')
    ramp=nodes.new('ShaderNodeValToRGB')
    colors=[(0,(.07,.04,1,1)),(.20,(.32,.035,1,1)),(.52,(.74,.06,.86,1)),(.72,(.65,.12,.65,1)),(1,(1,.5,.07,1))]
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    first=ramp.color_ramp.elements[0]
    first.position,first.color=colors[0]
    for pos,col in colors[1:]:
        ramp.color_ramp.elements.new(pos).color=col
    links.new(coord.outputs['Generated'],xyz.inputs[0])
    links.new(xyz.outputs['X'],ramp.inputs[0])
    links.new(ramp.outputs['Color'],shader.inputs['Base Color'])
    links.new(ramp.outputs['Color'],shader.inputs['Emission Color'])
    result['diffuser']=mat
    return result


def setup():
    from meshkit import slab,assign
    sc=bpy.context.scene
    sc.render.engine,sc.cycles.device,sc.cycles.samples='CYCLES','CPU',16
    sc.cycles.use_denoising=True
    sc.render.resolution_x,sc.render.resolution_y=512,384
    sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG'
    sc.render.image_settings.color_mode='RGBA'
    sc.world=bpy.data.worlds.new('RK_Studio_world')
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.35,.35,.35,1)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.22
    ground=slab('STUDIO_GROUND',3,3,.01,-.003,-.002)
    assign(ground,material('RK_Background',(.58,.58,.58),0,.72))
    for name,loc,power,size in [('KEY',(.18,-.24,.45),8,.45),('FILL',(-.28,-.1,.25),3,.35),('RIM',(.12,.25,.32),6,.38)]:
        data=bpy.data.lights.new('STUDIO_'+name,'AREA')
        data.energy,data.size=power,size
        obj=bpy.data.objects.new(data.name,data)
        sc.collection.objects.link(obj)
        obj.location=loc
        obj.rotation_euler=(Vector((0,0,.012))-obj.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('RK_CAMERA')
    data.type,data.ortho_scale,data.clip_start,data.clip_end='ORTHO',.39,.001,10
    camera=bpy.data.objects.new(data.name,data)
    sc.collection.objects.link(camera)
    sc.camera=camera


def aim(location=(.30,-.43,.33),target=(0,0,.015),scale=.39):
    sc=bpy.context.scene
    sc.camera.location=location
    sc.camera.rotation_euler=(Vector(target)-sc.camera.location).to_track_quat('-Z','Y').to_euler()
    sc.camera.data.ortho_scale=scale
    bpy.context.view_layer.update()
    return {'camera':sc.camera.name,'projection':'ORTHO','frame':sc.frame_current,
            'resolution':[sc.render.resolution_x,sc.render.resolution_y],
            'location':list(location),'target':list(target),'clip_start':.001,'clip_end':10.,'ortho_scale':scale}


def capture(path,subjects=None,**kwargs):
    assert not path.exists(),path
    context=aim(**kwargs)
    for obj in bpy.context.scene.objects:
        if obj.type=='MESH' and obj.name.startswith('RK_') and not obj.hide_render and (subjects is None or obj.name in subjects):
            assert framing(obj)['in_frame'],('clipped',obj.name)
    bpy.context.scene.render.filepath=str(path)
    assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
    stats=frame_stats(str(path))
    assert stats['stdev']>.01,stats
    return {'capture':context,'statistics':stats,'subjects':subjects or 'all visible product meshes'}
