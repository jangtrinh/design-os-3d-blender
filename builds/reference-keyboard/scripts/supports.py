"""Explicit custom guides, board mounts and the USB daughterboard load path."""
import math
import bpy
import meshkit as g
import mechanics as m
from project import interfaces, key_rows


def annulus(name,outer,inner,z0,z1,xy=(0,0),segments=96):
    verts=[]
    for z,r in ((z0,outer),(z1,outer),(z0,inner),(z1,inner)):
        verts.extend((r*math.cos(i*math.tau/segments),r*math.sin(i*math.tau/segments),z)
                     for i in range(segments))
    faces=[]
    n=segments
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,j,n+j,n+i),(2*n+j,2*n+i,3*n+i,3*n+j),
                      (j,i,2*n+i,2*n+j),(n+i,n+j,3*n+j,3*n+i)))
    obj=g.mesh(name,verts,faces)
    obj.location.x,obj.location.y=xy
    m.assert_solid(obj)
    return obj


def spacebar_guides(cap):
    cfg=interfaces()['spacebar']
    guides=[]
    for i,dx in enumerate(cfg['guide_offsets_x']):
        local=(dx/1000,0)
        rod=g.cylinder('GUIDE_PIN_CUTOVER_%d'%i,cfg['pin_diameter']/2000,0,.008,local)
        m.operation(cap,rod,'UNION')
    # Cap remains one manufactured body; fixed sleeves are separate service parts.
    row=next(r for r in key_rows() if r['units']==2)
    for i,dx in enumerate(cfg['guide_offsets_x']):
        xy=((row['xy_mm'][0]+dx)/1000,row['xy_mm'][1]/1000)
        tube=annulus('RK_GUIDE_SLEEVE_%d'%i,.0022,.0011,.0136,.0215,xy)
        flange=annulus('GUIDE_FLANGE_%d'%i,.003,.0011,.0151,.0163,xy)
        m.operation(tube,flange,'UNION')
        tube['design_role']='custom removable spacebar guide; 0.1 mm radial running clearance'
        guides.append(tube)
    return guides


def board_supports():
    cfg=interfaces()['chassis']
    base=bpy.data.objects['RK_BASE']
    for i,p in enumerate(cfg['pcb_support_points']):
        xy=tuple(v/1000 for v in p)
        post=g.cylinder('RK_PCB_SUPPORT_%d'%i,.0015,.002,.01015,xy)
        post['design_role']='chassis-mounted polymer PCB support; presses only masked keepout pad'
        m.hole_set(base,[xy],.00085,-.001,.003,'CUT_BOARD_SUPPORT_%d_'%i)
        m.hole_set(post,[xy],.00065,.001,.006,'CUT_SUPPORT_THREAD_%d_'%i)
        screw=g.cylinder('RK_SUPPORT_SCREW_%d'%i,.0008,-.0008,.005,xy)
        screw['design_role']='M1.6 mounting envelope; thread engagement requires hardware qualification'


def usb_mount():
    cfg=interfaces()['usb']
    xy=tuple(v/1000 for v in cfg['board_center_xy'])
    board=g.slab('RK_USB_BOARD',.016,.010,.001,.0052,.0062,xy)
    mounts=[tuple(v/1000 for v in p) for p in cfg['mount_xy']]
    m.hole_set(board,mounts,.00085,.004,.007,'CUT_USB_MOUNT_')
    base=bpy.data.objects['RK_BASE']
    for i,p in enumerate(mounts):
        post=g.cylinder('RK_USB_SUPPORT_%d'%i,.00145,.002,.0052,p)
        m.hole_set(post,[p],.00065,.001,.006,'CUT_USB_POST_%d_'%i)
        m.hole_set(base,[p],.00085,-.001,.003,'CUT_USB_BASE_%d_'%i)
        head=g.cylinder('RK_USB_MOUNT_SCREW_%d'%i,.0013,.0062,.007,p)
        shaft=g.cylinder('USB_SHAFT_%d'%i,.0008,.0022,.0063,p)
        m.operation(head,shaft,'UNION')
    # Ground tabs represent the connector's mechanical solder attachment to the board.
    for i,dx in enumerate((-.0044,.0044)):
        tab=g.slab('RK_USB_TAB_%d'%i,.001,.003,.0001,.0062,.0067,(.067+dx,.042))
        tab['design_role']='connector shell anchoring-tab envelope; solder joint not simulated'
    board['design_role']='custom USB daughterboard, no fabricated circuit or vendor footprint claim'
    return board


def encoder_bonds():
    """Explicit prototype adhesive joints, not a claim of qualified bond strength."""
    anchors=[o for o in bpy.context.scene.objects if o.type=='MESH' and
             (o.name.startswith('RK_ENCODER_RISER_') or o.name.startswith('RK_ENCODER_BOARD_SUPPORT_'))]
    for index,obj in enumerate(anchors):
        lo=min(v.co.z for v in obj.data.vertices)
        if abs(lo-.002)>1e-6:
            continue
        for vertex in obj.data.vertices:
            if abs(vertex.co.z-lo)<1e-7: vertex.co.z+=.00008
        obj.data.update()
        if obj.name.startswith('RK_ENCODER_RISER_'):
            bond=g.cylinder('RK_ENCODER_BOND_%02d'%index,.00125,.002,.00208,
                            (obj.location.x,obj.location.y))
        else:
            xs=[v.co.x for v in obj.data.vertices]; ys=[v.co.y for v in obj.data.vertices]
            bond=g.slab('RK_ENCODER_BOND_%02d'%index,max(xs)-min(xs),max(ys)-min(ys),.0001,.002,.00208,
                       (obj.location.x+(max(xs)+min(xs))/2,obj.location.y+(max(ys)+min(ys))/2))
        obj['attachment_method']='bonded prototype anchor with explicit 0.08 mm bondline'
        bond['role']='epoxy bondline design envelope; adhesion/creep/torque require physical qualification'
