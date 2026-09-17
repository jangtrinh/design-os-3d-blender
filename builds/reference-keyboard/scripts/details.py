"""Native legends, plausible electronics envelopes and exportable diffuse color."""
import math
import bpy
import bmesh
from mathutils import Matrix
import meshkit as g


def label(name, body, size, xyz, material, parent=None):
    assert name not in bpy.data.objects
    curve=bpy.data.curves.new(name, 'FONT')
    curve.body,curve.size=body,size
    curve.align_x,curve.align_y='CENTER','CENTER'
    curve.resolution_u=6
    obj=bpy.data.objects.new(name,curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.location=xyz
    if parent is not None: obj.parent=parent
    bpy.context.view_layer.update()
    graph=bpy.context.evaluated_depsgraph_get()
    mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(graph),depsgraph=graph)
    # Object data types differ for FONT/MESH; create the mesh object explicitly.
    bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.curves.remove(curve)
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location=xyz
    if parent is not None: obj.parent=parent
    g.assign(obj,material)
    obj['role']='printed legend, not a manufacturing solid'
    return obj


def orient(obj):
    bm=bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
        bm.to_mesh(obj.data)
    finally:
        bm.free()
    obj.data.update()


def conform_legend(obj,key):
    """Place printed legend vertices on the actual dished cap, 0.015 mm above it."""
    from mathutils import Vector
    bpy.context.view_layer.update()
    matrix=obj.matrix_local.copy()
    inverse=matrix.inverted()
    for vertex in obj.data.vertices:
        point=matrix@vertex.co
        hit,where,_,_=key.ray_cast(Vector((point.x,point.y,.012)),Vector((0,0,-1)))
        assert hit,(obj.name,'legend missed key surface')
        point.z=where.z+.000015
        vertex.co=inverse@point
    obj.data.update()
    obj['printed_surface_offset_mm']=.015


def legends(keys,palette):
    for row in keys:
        key=bpy.data.objects[row['id']]
        text=row['label']
        name='RK_LEGEND_%s'%row['id'].removeprefix('RK_KEY_')
        if text=='dot':
            obj=g.cylinder(name,.0009,.00916,.00919,segments=24)
            obj.parent=key
            obj.location=(0,0,0)
            g.assign(obj,palette['legend'])
        elif text=='space':
            obj=g.slab(name,.006,.0013,.0006,.00915,.00919)
            obj.parent=key
            obj.location=(0,0,0)
            g.assign(obj,palette['legend'])
        elif text in ('left','down','right','enter'):
            angle={'left':math.pi,'down':-math.pi/2,'right':0,'enter':math.pi}[text]
            points=[(-.002,.00015),(.0009,.00015),(.0001,.00095),(.00035,.0012),
                    (.0017,0),(.00035,-.0012),(.0001,-.00095),(.0009,-.00015),(-.002,-.00015)]
            obj=g.prism(name,points,.00917,.00919)
            orient(obj)
            obj.parent=key
            obj.location=(0,0,0)
            obj.rotation_euler.z=angle
            g.assign(obj,palette['legend'])
        else:
            size=.0035 if len(text)==1 else .00205
            obj=label(name,text,size,(0,0,.00924),palette['legend'],key)
        if text not in ('dot','space','left','down','right','enter'):
            conform_legend(obj,key)
    # Product marks are decorative reference labels, no compliance/weight claims.
    for i,(txt,size,xy) in enumerate([('podo',.0036,(-.126,-.025)),
                                    ('CREATE',.00135,(-.126,-.031)),
                                    ('work',.0028,(.123,-.027)),
                                    ('keeb',.0028,(.123,-.0315)),
                                    ('40% +1',.0016,(.123,-.036)),
                                    ('Tools for a brighter tomorrow.',.00125,(0,-.044))]):
        label('RK_SILK_%d'%i,txt,size,(*xy,.01512),palette['legend'])


def rgb_texture(diffuser, palette, out):
    """Bake the declared color gradient to a tiny native texture GLB can embed."""
    image=bpy.data.images.new('RK_RGB_NATIVE_GRADIENT',256,8,alpha=True)
    stops=[(0,(.07,.04,1)),(.2,(.32,.035,1)),(.52,(.74,.06,.86)),
           (.72,(.65,.12,.65)),(1,(1,.5,.07))]
    pixels=[]
    for _ in range(8):
        for x in range(256):
            u=x/255
            lo,hi=next((a,b) for a,b in zip(stops,stops[1:]) if a[0]<=u<=b[0])
            t=(u-lo[0])/(hi[0]-lo[0])
            pixels.extend([lo[1][i]*(1-t)+hi[1][i]*t for i in range(3)]+[1])
    image.pixels.foreach_set(pixels)
    image.filepath_raw=str(out/'rgb-gradient.png')
    image.file_format='PNG'
    image.save()
    image.pack()
    uv=diffuser.data.uv_layers.new(name='RGB_Gradient_UV')
    for polygon in diffuser.data.polygons:
        for index in polygon.loop_indices:
            v=diffuser.data.vertices[diffuser.data.loops[index].vertex_index].co
            uv.data[index].uv=((v.x+.142)/.284,.5)
    mat=palette['diffuser']
    shader=mat.node_tree.nodes.get('Principled BSDF')
    texture=mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image=image
    # PMMA transmits and diffuses actual internal emitter geometry. The color
    # image belongs to the LED rail material rather than making all acrylic glow.
    for name in ('Base Color','Emission Color'):
        for link in list(shader.inputs[name].links): mat.node_tree.links.remove(link)
    shader.inputs['Base Color'].default_value=(.90,.93,.98,1)
    shader.inputs['Emission Strength'].default_value=0
    shader.inputs['Transmission Weight'].default_value=.92
    shader.inputs['Roughness'].default_value=.22
    scatter=mat.node_tree.nodes.new('ShaderNodeVolumeScatter')
    scatter.inputs['Color'].default_value=(.95,.97,1,1)
    scatter.inputs['Density'].default_value=100
    scatter.inputs['Anisotropy'].default_value=.1
    mat.node_tree.links.new(scatter.outputs['Volume'],mat.node_tree.nodes['Material Output'].inputs['Volume'])
    from studio import material
    ledmat=material('RK_RGB_LED_RAIL',(.7,.7,.7),0,.2)
    ledshader=ledmat.node_tree.nodes['Principled BSDF']
    ledtex=ledmat.node_tree.nodes.new('ShaderNodeTexImage'); ledtex.image=image
    ledmat.node_tree.links.new(ledtex.outputs['Color'],ledshader.inputs['Emission Color'])
    ledmat.node_tree.links.new(ledtex.outputs['Color'],ledshader.inputs['Base Color'])
    ledshader.inputs['Emission Strength'].default_value=650
    ledmat['radiance_status']='visual lighting parameter, not calibrated vendor flux or electrical power'
    keymat=ledmat.copy(); keymat.name='RK_RGB_KEY_DIODE'
    keymat.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=8
    from project import key_rows
    for row in key_rows():
        x,y=[v/1000 for v in row['xy_mm']]
        led=g.slab('RK_RGB_KEY_%s'%row['id'].removeprefix('RK_KEY_'),.0016,.0016,.0002,.01175,.01235,(x,y))
        uv=led.data.uv_layers.new(name='EmitterColor')
        for loop in uv.data: loop.uv=((x+.142)/.284,.5)
        g.assign(led,keymat)
        led['role']='per-key RGB emitter envelope on PCB, no routing/power/firmware qualification'
    for i in range(28):
        x=-.132+i*(.264/27)
        for side in (-1,1):
            from project import layout
            y=side*.0418
            if any(abs(x-kx/1000)<.0115 and abs(y-ky/1000)<.009 for kx,ky in layout()['knobs_mm']):
                continue
            led=g.slab('RK_RGB_LED_%02d_%s'%(i,'F' if side<0 else 'R'),.0024,.0014,.0002,.00955,.01015,(x,y))
            uv=led.data.uv_layers.new(name='EmitterColor')
            for loop in uv.data: loop.uv=((x+.142)/.284,.5)
            g.assign(led,ledmat)
            led['role']='generic RGB emitter envelope; circuit selection and optical flux remain unqualified'


def electronics(palette):
    """Small representative forms, explicitly not a selected PCB/netlist."""
    from studio import material
    board=material('RK_PCB_Mask',(.011,.019,.015),.08,.48)
    g.assign(bpy.data.objects['RK_PCB'],board)
    for obj in bpy.context.scene.objects:
        if obj.name=='RK_USB_BOARD' or obj.name.startswith('RK_ENCODER_DAUGHTERBOARD_'): g.assign(obj,board)
    led=material('RK_Status_LED',(.52,.7,.07),0,.25)
    led.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=(.5,.7,.07,1)
    led.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.25
    for i in range(3):
        obj=g.slab('RK_STATUS_%d'%i,.001,.0018,.0001,.0151,.01535,(.121+i*.0016,-.025))
        g.assign(obj,led)
        obj['role']='illustrative status LED, no electrical function'
        pipe=g.slab('RK_STATUS_PIPE_%d'%i,.0012,.002,.00015,.01175,.0151,(.121+i*.0016,-.025))
        g.assign(pipe,palette['diffuser'])
        pipe['role']='clear molded light-pipe envelope joining PCB LED plane to plate aperture'
    # Circuit detail stays below the plate, clear of the structural perimeter.
    for i in range(24):
        x=-.110+i*.009
        for side in (-1,1):
            from project import layout
            if any(abs(x-kx/1000)<.011 and abs(side*.043-ky/1000)<.009 for kx,ky in layout()['knobs_mm']):
                continue
            obj=g.slab('RK_COMPONENT_%02d_%d'%(i,side),.0018,.00085,.0001,.01175,.01255,(x,side*.043))
            g.assign(obj,palette['gold'] if i%3 else palette['switch'])
            obj['role']='illustrative electronic package, netlist unqualified'
    hub=g.slab('RK_HUB_COVER',.024,.017,.0015,.0151,.0157,(-.104,.034))
    g.assign(hub,palette['silver'])
    for i,(x,y) in enumerate(((-.113,.028),(-.095,.028),(-.113,.040),(-.095,.040))):
        g.assign(g.cylinder('RK_HUB_FASTENER_%d'%i,.0012,.0157,.017,(x,y)),palette['black'])
    # The connector is mounted on RK_USB_BOARD/RK_USB_TAB_* fixed to the chassis.
    # The acrylic window is clearance only and moves independently in the exploded view.
    outer=g.rounded_outline(.009,.003,.0008)
    inner=g.rounded_outline(.0082,.0022,.0005)
    n=len(outer); verts=[]
    for profile,y in ((outer,.039),(outer,.046),(inner,.039),(inner,.046)):
        verts.extend((.067+x,y,.008+z) for x,z in profile)
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),
                      (i,2*n+i,2*n+j,j),(n+j,3*n+j,3*n+i,n+i)))
    usb=g.mesh('RK_USB_SHELL',verts,faces)
    orient(usb)
    g.assign(usb,palette['silver'])
    tongue=g.slab('RK_USB_TONGUE',.0062,.004,.0002,.0077,.0083,(.067,.0428))
    g.assign(tongue,palette['switch'])
    usb['role']='USB-C visual envelope; connector model and mating unqualified'
