"""96-frame inspectable control/assembly choreography, not physical actuation proof."""
import math
import bpy
from boilerplates.bp_animation import animate_property_keys,add_simple_driver
from project import interfaces


def _group(name,objects):
    obj=bpy.data.objects.new(name,None)
    bpy.context.scene.collection.objects.link(obj)
    for child in objects:
        if child.parent is None: child.parent=obj
    return obj


def setup():
    rest=interfaces()['keycap']['stem_bottom_z']/1000
    stroke=interfaces()['keycap']['travel']/1000
    sc=bpy.context.scene
    sc.frame_start,sc.frame_end,sc.render.fps=1,96,24
    objects=list(sc.objects)
    select=lambda pred:[o for o in objects if pred(o.name)]
    groups={
        'keycaps':_group('ASSEMBLY_KEYCAPS',select(lambda n:n.startswith('RK_KEY_'))),
        'knobs':_group('ASSEMBLY_KNOBS',select(lambda n:n.startswith('RK_KNOB_'))),
        'plate':_group('ASSEMBLY_PLATE',select(lambda n:n=='RK_MAIN_PLATE' or n.startswith(('RK_SILK_','RK_STATUS_','RK_HUB_')))),
        'switches':_group('ASSEMBLY_SWITCHES',select(lambda n:n.startswith(('RK_SWITCH_','RK_CONTACT_','RK_GUIDE_')))),
        'pcb':_group('ASSEMBLY_PCB',select(lambda n:n=='RK_PCB' or n.startswith(('RK_COMPONENT_','RK_RGB_')))),
        'diffuser':_group('ASSEMBLY_DIFFUSER',select(lambda n:n=='RK_DIFFUSER')),
        'top_screws':_group('ASSEMBLY_TOP_SCREWS',select(lambda n:n.startswith('RK_SCREW_TOP_'))),
    }
    keys=sorted(select(lambda n:n.startswith('RK_KEY_')),key=lambda o:o.name)
    for i,key in enumerate(keys):
        start=3+i%10
        animate_property_keys(key,'location',[(1,rest),(start,rest),(start+2,rest-stroke),(start+4,rest),(96,rest)],2,'LINEAR')
        stem=bpy.data.objects['RK_SWITCH_STEM_%02d'%i]
        add_simple_driver(stem,'location',2,key,'location',2,'var - '+repr(rest))
    for i,knob in enumerate(sorted(select(lambda n:n.startswith('RK_KNOB_')),key=lambda o:o.name)):
        animate_property_keys(knob,'rotation_euler',[(1,0),(8,0),(18,.8+i*.1),(24,0),(96,0)],2,'LINEAR')
        shaft=bpy.data.objects['RK_ENCODER_SHAFT_%d'%(i+1)]
        add_simple_driver(shaft,'rotation_euler',2,knob,'rotation_euler',2,'var')
    travel={'keycaps':.055,'knobs':.052,'plate':.029,'switches':.017,'pcb':.008,'diffuser':.003,'top_screws':.075}
    for name,group in groups.items():
        start=25 if name in ('keycaps','knobs','top_screws') else 37
        animate_property_keys(group,'location',[(1,0),(start,0),(58,travel[name]),(66,travel[name]),(90,0),(96,0)],2,'LINEAR')
    sc.frame_set(1)
    return {'frames':[1,96],'fps':24,'keys':len(keys),'drivers':len(keys),'assembly_groups':list(groups),
            'purpose':'exploded product inspection and control demonstration',
            'limits':['Exploded views are choreography, not a validated hardware assembly procedure.',
                      'Press travel is 3 mm; modeled cross receivers and guides are digital prototypes, not measured retention-force evidence.']}


def verify():
    rest=interfaces()['keycap']['stem_bottom_z']/1000
    sc=bpy.context.scene
    original=sc.frame_current
    rows=[]
    try:
        for frame in (1,5,7,12,18,24,40,58,66,90,96):
            sc.frame_set(frame)
            graph=bpy.context.evaluated_depsgraph_get()
            row={'frame':frame,'key_travel_mm':{},'knob_radians':{},'groups_mm':{}}
            for i in range(58):
                key=bpy.data.objects['RK_KEY_%02d'%i].evaluated_get(graph)
                stem=bpy.data.objects['RK_SWITCH_STEM_%02d'%i].evaluated_get(graph)
                travel=(rest-key.location.z)*1000
                assert -.001<=travel<=3.001,(frame,i,travel)
                assert abs(stem.location.z-(key.location.z-rest))<1e-7,(frame,i,'driver')
                row['key_travel_mm'][str(i)]=round(travel,5)
            for i in range(1,6):
                obj=bpy.data.objects['RK_KNOB_%d'%i].evaluated_get(graph)
                shaft=bpy.data.objects['RK_ENCODER_SHAFT_%d'%i].evaluated_get(graph)
                assert abs(shaft.rotation_euler.z-obj.rotation_euler.z)<1e-7,(frame,i,'encoder rotation')
                row['knob_radians'][str(i)]=round(obj.rotation_euler.z,6)
            for obj in sc.objects:
                if obj.name.startswith('ASSEMBLY_'):
                    row['groups_mm'][obj.name]=round(obj.evaluated_get(graph).location.z*1000,5)
            rows.append(row)
        assert abs(rows[0]['groups_mm']['ASSEMBLY_KEYCAPS'])<1e-5
        assert rows[7]['groups_mm']['ASSEMBLY_KEYCAPS']>54.99
        assert abs(rows[-1]['groups_mm']['ASSEMBLY_KEYCAPS'])<1e-5
        assert max(v for row in rows for v in row['key_travel_mm'].values())>2.999
        assert max(v for row in rows for v in row['knob_radians'].values())>=1.19
    finally:
        sc.frame_set(original)
    return {'status':'pass','samples':rows,'sampled_frames':len(rows),'drivers_checked_per_frame':58,
            'limits':['Evaluated transforms and driver response only; no continuous collision proof.']}
