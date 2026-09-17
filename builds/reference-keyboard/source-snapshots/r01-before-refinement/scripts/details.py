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
            size=.0029 if len(text)==1 else .00175
            label(name,text,size,(0,0,.00922),palette['legend'],key)
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
    mat.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
    mat.node_tree.links.new(texture.outputs['Color'],shader.inputs['Emission Color'])


def electronics(palette):
    """Small representative forms, explicitly not a selected PCB/netlist."""
    from studio import material
    board=material('RK_PCB_Mask',(.011,.019,.015),.08,.48)
    g.assign(bpy.data.objects['RK_PCB'],board)
    led=material('RK_Status_LED',(.52,.7,.07),0,.25)
    led.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value=(.5,.7,.07,1)
    led.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.25
    for i in range(3):
        obj=g.slab('RK_STATUS_%d'%i,.001,.0018,.0001,.0151,.01535,(.121+i*.0016,-.021))
        g.assign(obj,led)
        obj['role']='illustrative status LED, no electrical function'
    # Circuit detail stays below the plate, clear of the structural perimeter.
    for i in range(24):
        x=-.110+i*.009
        for side in (-1,1):
            obj=g.slab('RK_COMPONENT_%02d_%d'%(i,side),.0018,.00085,.0001,.0134,.01355,(x,side*.043))
            g.assign(obj,palette['gold'] if i%3 else palette['switch'])
            obj['role']='illustrative electronic package, netlist unqualified'
    hub=g.slab('RK_HUB_COVER',.024,.017,.0015,.0151,.0157,(-.104,.034))
    g.assign(hub,palette['silver'])
    for i,(x,y) in enumerate(((-.113,.028),(-.095,.028),(-.113,.040),(-.095,.040))):
        g.assign(g.cylinder('RK_HUB_FASTENER_%d'%i,.0012,.0157,.017,(x,y)),palette['black'])
    # USB opening already exists in the acrylic. The shell follows that opening.
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
