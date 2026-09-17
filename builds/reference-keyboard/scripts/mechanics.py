"""Declared chassis adaptation with actual holes, layer rebates and native tooling."""
import math
import bpy
import bmesh
from mathutils import Matrix
import meshkit as g
from boilerplates.bp_core import evaluated_mesh
from agent_verify import checkpoint

CHECKPOINTS=None
SEQ=0


def assert_solid(obj):
    with evaluated_mesh(obj) as (_,me):
        bm=bmesh.new()
        try:
            bm.from_mesh(me)
            bm.normal_update()
            assert all(e.is_manifold and e.is_contiguous for e in bm.edges),obj.name
            assert bm.calc_volume(signed=True)>0,obj.name
        finally:
            bm.free()


def combine_cutters(name,objects):
    verts,faces=[],[]
    for obj in objects:
        offset=len(verts)
        verts.extend(tuple(obj.matrix_world @ v.co) for v in obj.data.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in obj.data.polygons)
    out=g.mesh(name,verts,faces)
    for obj in objects:
        data=obj.data
        bpy.data.objects.remove(obj,do_unlink=True)
        if not data.users:bpy.data.meshes.remove(data)
    return out


def operation(obj,cutter,kind='DIFFERENCE'):
    global SEQ
    assert CHECKPOINTS is not None
    assert_solid(obj)
    assert_solid(cutter)
    SEQ+=1
    checkpoint('%03d-%s'%(SEQ,obj.name),str(CHECKPOINTS))
    mod=obj.modifiers.new('EXACT_'+kind,'BOOLEAN')
    mod.operation,mod.solver,mod.object=kind,'EXACT',cutter
    graph=bpy.context.evaluated_depsgraph_get()
    result=bpy.data.meshes.new_from_object(obj.evaluated_get(graph),depsgraph=graph)
    old=obj.data
    obj.modifiers.remove(mod)
    obj.data=result
    if not old.users:bpy.data.meshes.remove(old)
    data=cutter.data
    bpy.data.objects.remove(cutter,do_unlink=True)
    if not data.users:bpy.data.meshes.remove(data)
    # Remove numerical remnants before the later independent STL roundtrip.
    bm=bmesh.new()
    try:
        bm.from_mesh(result)
        bmesh.ops.remove_doubles(bm,verts=bm.verts[:],dist=1e-8)
        bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-8)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
        bm.to_mesh(result)
    finally:
        bm.free()
    result.update()
    assert_solid(obj)
    return obj


def hole_set(obj,locations,radius,lo,hi,name):
    bpy.context.view_layer.update()
    cutters=[g.cylinder(name+str(i),radius,lo,hi,xy) for i,xy in enumerate(locations)]
    bpy.context.view_layer.update()
    operation(obj,combine_cutters(name+'_ALL',cutters))


def chassis(data,keys):
    mount=[tuple(v/1000 for v in xy) for xy in data['fasteners_xy_mm']]
    base=g.slab('RK_BASE',.284,.092,.004,0,.004)
    operation(base,g.slab('CUT_BASE_POCKET',.280,.088,.002,.002,.005))
    for i,xy in enumerate(mount):
        operation(base,g.cylinder('BASE_BOSS_%d'%i,.0035,.001,.004,xy),'UNION')
    hole_set(base,mount,.0017,-.001,.005,'CUT_BASE_M3_')

    acrylic=g.slab('RK_DIFFUSER',.284,.092,.004,.004,.012)
    operation(acrylic,g.slab('CUT_ACRYLIC_VOID',.280,.086,.002,.003,.013))
    for i,xy in enumerate(mount):
        # A 4 mm boss touched the inner side exactly and produced a non-manifold
        # boolean seam. Half a millimetre of real overlap makes the joint solid.
        operation(acrylic,g.cylinder('ACRYLIC_BOSS_%d'%i,.0045,.004,.012,xy),'UNION')
    operation(acrylic,g.slab('CUT_PCB_SEAT',.2804,.0884,.002,.01015,.013))
    hole_set(acrylic,mount,.0029,.003,.013,'CUT_DIFFUSER_SPACER_')
    # Cable location is a declared local design choice, absent from the source photo.
    # Meet the lowered PCB rebate instead of leaving a 0.15 mm internal lip.
    # The remaining outer-wall roof is 1.3 mm above this clearance window.
    usb=g.slab('CUT_USB_WINDOW',.010,.006,.0005,.006,.0107,(.067,.045))
    operation(acrylic,usb)

    pcb=g.slab('RK_PCB',.280,.088,.002,.01015,.01175)
    hole_set(pcb,mount,.0029,.009,.014,'CUT_PCB_SPACER_')
    pins=[]
    for row in keys:
        x,y=[v/1000 for v in row['xy_mm']]
        pins.extend(((x-.0035,y-.0026),(x+.0035,y-.0026)))
    hole_set(pcb,pins,.0005,.009,.014,'CUT_CONTACT_')
    plate=g.slab('RK_MAIN_PLATE',.284,.092,.004,.0136,.0151)
    cut=[]
    for i,row in enumerate(keys):
        xy=tuple(v/1000 for v in row['xy_mm'])
        cut.append(g.slab('CUT_SWITCH_%02d'%i,.014,.014,.00035,.013,.016,xy))
    bpy.context.view_layer.update()
    operation(plate,combine_cutters('CUT_SWITCHES_ALL',cut))
    hole_set(plate,mount,.0017,.013,.016,'CUT_PLATE_M3_')
    knob_xy=[tuple(v/1000 for v in xy) for xy in data['knobs_mm']]
    hole_set(plate,knob_xy,.0082,.013,.016,'CUT_ROTATING_KNOB_')
    # The moving full-diameter knob also crosses the PCB plane. A shaft-sized
    # opening would intersect it even when the encoder's body passed a check.
    for i,xy in enumerate(knob_xy):
        operation(pcb,g.slab('CUT_ENCODER_WINDOW_%d'%i,.0204,.0166,.001,.009,.014,xy))
    operation(pcb,g.slab('CUT_REAR_ENCODER_NOTCH',.0604,.020,.001,.009,.014,(-.062,.0367)))
    from project import interfaces
    wide=next(row for row in keys if row['units']==2)
    guides=[((wide['xy_mm'][0]+dx)/1000,wide['xy_mm'][1]/1000)
            for dx in interfaces()['spacebar']['guide_offsets_x']]
    hole_set(plate,guides,.0023,.013,.016,'CUT_SPACEBAR_GUIDE_')
    # Inspection light pipes align with the three visible status LEDs.
    # A single light-bar opening avoids 0.2 mm webs between separate LED ports;
    # moving below the knob leaves a real ligament around the rotating aperture.
    operation(plate,g.slab('CUT_STATUS_BAR',.0048,.0024,.0003,.013,.016,(.1226,-.025)))
    for obj in (base,acrylic,pcb,plate):
        obj['design_status']='local mechanical adaptation; not vendor-compatible CAD'
    return base,acrylic,pcb,plate


def spacers_and_screws(data):
    results=[]
    for i,point in enumerate(data['fasteners_xy_mm']):
        xy=tuple(v/1000 for v in point)
        spacer=g.cylinder('RK_SPACER_%d'%i,.0027,.002,.0136,xy)
        hole_set(spacer,[xy],.00125,.001,.014,'CUT_SPACER_%d_'%i)
        results.append(spacer)
        spacer['hardware_contract']='custom M3 double-ended tapped standoff; blind insertion regions 2..6 and9.1..13.6 mm'
        spacer['thread_tip_separation_mm']=3.1
        for side in ('TOP','BOTTOM'):
            top=side=='TOP'
            # Recess is modeled; screw thread is an explicitly nominal shank envelope.
            head=g.cylinder('RK_SCREW_%s_%d'%(side,i),.0027,0,.0015)
            recess=g.cylinder('CUT_HEAD_%s_%d'%(side,i),.00135,.0006,.002,segments=6)
            operation(head,recess)
            stem=g.cylinder('SHAFT_%s_%d'%(side,i),.0015,-.006,.0001)
            operation(head,stem,'UNION')
            if not top:
                head.data.transform(Matrix.Rotation(math.pi,4,'X'))
            head.location=(*xy,.0151 if top else 0)
            head['thread']='M3 nominal shank; helical thread and engagement unqualified'
            results.append(head)
    return results
