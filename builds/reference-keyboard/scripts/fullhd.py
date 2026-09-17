"""Full HD native Cycles delivery. No image synthesis, resize or upscaling route."""
import json
import shutil
import struct
import subprocess
import time
from contextlib import contextmanager

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from agent_verify import framing
from boilerplates.bp_core import evaluated_mesh
from project import sha,write
import studio

SIZE=(1920,1080)


def renderer():
    sc=bpy.context.scene
    sc.render.engine='CYCLES'
    sc.render.resolution_x,sc.render.resolution_y=SIZE
    sc.render.resolution_percentage=100
    sc.render.use_border=False
    sc.render.use_persistent_data=False
    sc.cycles.use_denoising=True
    sc.cycles.use_adaptive_sampling=True
    sc.cycles.adaptive_threshold=.02
    prefs=bpy.context.preferences.addons['cycles'].preferences
    devices=[]
    try:
        prefs.compute_device_type='METAL'
        prefs.refresh_devices()
        devices=[d for d in prefs.devices if d.type=='METAL']
    except (TypeError,AttributeError):
        devices=[]
    for device in prefs.devices:
        device.use=device in devices
    sc.cycles.device='GPU' if devices else 'CPU'
    return {'engine':'CYCLES','device':sc.cycles.device,
            'devices':[d.name for d in devices],'resolution':list(SIZE),
            'denoise':True,'adaptive_threshold':.02,'native_render':True}


@contextmanager
def isolated(names,light_target):
    saved={o:o.hide_render for o in bpy.context.scene.objects if o.type=='MESH'}
    data=bpy.data.lights.new('INSPECTION_TEMP','AREA')
    data.energy,data.size=.4,.05
    lamp=bpy.data.objects.new(data.name,data)
    bpy.context.scene.collection.objects.link(lamp)
    lamp.location=Vector(light_target)+Vector((0,-.045,-.05))
    lamp.rotation_euler=(Vector(light_target)-lamp.location).to_track_quat('-Z','Y').to_euler()
    try:
        for obj in saved:
            obj.hide_render=obj.name not in names
        yield
    finally:
        for obj,value in saved.items(): obj.hide_render=value
        bpy.data.objects.remove(lamp,do_unlink=True)
        bpy.data.lights.remove(data)


def fit_subjects(settings, margin=.06):
    """Expand an orthographic detail shot from evaluated projected vertices.

    Keep the authored aim and a six-percent image border. Square-preview scales
    otherwise crop tall controls when the output changes to 16:9.
    """
    result=dict(settings)
    names=result.get('subjects')
    if not names:
        return result
    sc=bpy.context.scene
    studio.aim(**{k:v for k,v in result.items() if k!='subjects'})
    graph=bpy.context.evaluated_depsgraph_get()
    camera=sc.camera.evaluated_get(graph)
    required=0.0
    for name in names:
        obj=bpy.data.objects[name]
        with evaluated_mesh(obj,graph) as (owner,mesh):
            for vertex in mesh.vertices:
                p=world_to_camera_view(sc,camera,owner.matrix_world@vertex.co)
                assert camera.data.clip_start<=p.z<=camera.data.clip_end,(name,'depth clipping')
                required=max(required,abs(2*p.x-1),abs(2*p.y-1))
    result['scale']=sc.camera.data.ortho_scale*max(1.0,required/(1-2*margin))
    return result


def stills(out):
    sc=bpy.context.scene
    sc.cycles.samples=64
    views={}
    def shot(name,**settings):
        start=time.monotonic()
        path=out/('CK-001-'+name+'.png')
        requested=settings.get('scale')
        settings=fit_subjects(settings)
        views[name]=studio.capture(path,**settings)
        views[name]['requested_ortho_scale']=requested
        with path.open('rb') as handle:
            header=handle.read(24)
        assert header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==SIZE,(path,'not native Full HD')
        views[name]['verified_pixel_size']=list(SIZE)
        views[name]['sha256']=sha(path)
        views[name]['render_seconds']=round(time.monotonic()-start,3)
        print('FULLHD_STILL',name,views[name]['render_seconds'],flush=True)
    sc.frame_set(1)
    shot('hero',scale=.365)
    shot('top',location=(0,0,.5),target=(0,0,0),scale=.32)
    shot('knob-detail',subjects=['RK_KNOB_5'],location=(.16,-.10,.11),target=(.125,-.012,.021),scale=.048)
    shot('key-detail',subjects=['RK_KEY_15'],location=(-.067,-.095,.125),target=(-.050,-.001,.023),scale=.060)
    sc.frame_set(60)
    shot('exploded',target=(0,0,.037),scale=.415)
    sc.frame_set(1)
    parts=[o.name for o in sc.objects if o.type=='MESH' and o.name.startswith('RK_')]
    with isolated(parts,(0,0,0)):
        shot('bottom',location=(0,0,-.4),target=(0,0,0),scale=.32)
    for name,object_name,scale in [('receiver','RK_KEY_00',.039),('spacebar-guides','RK_KEY_41',.061),('D-receiver','RK_KNOB_5',.037)]:
        obj=bpy.data.objects[object_name]
        origin=obj.matrix_world.translation.copy()
        target=origin+Vector((0,0,.005))
        camera=origin+Vector((.018,-.025,-.038))
        with isolated([object_name],target):
            shot(name,subjects=[object_name],location=tuple(camera),target=tuple(target),scale=scale)
    index=2
    encoder_names=[o.name for o in sc.objects if o.type=='MESH' and o.get('encoder_index')==index]
    center=(-.082,.035,.012)
    with isolated(encoder_names,center):
        shot('encoder-mount',subjects=encoder_names,location=(-.047,-.011,.057),target=center,scale=.054)
    shot('usb-mount',subjects=['RK_USB_SHELL'],location=(.086,.095,.041),target=(.067,.041,.008),scale=.045)
    return views


def movie(out):
    sc=bpy.context.scene
    sc.cycles.samples=24
    sc.cycles.adaptive_threshold=.035
    sc.render.resolution_x,sc.render.resolution_y=SIZE
    camera=studio.aim(target=(0,0,.037),scale=.415)
    directory=out/'frames'
    directory.mkdir()
    rows=[]; start=time.monotonic()
    for frame in range(1,97):
        sc.frame_set(frame)
        for obj in sc.objects:
            if obj.type=='MESH' and obj.name.startswith('RK_') and not obj.hide_render:
                assert framing(obj)['in_frame'],(frame,obj.name,'clipped')
        path=directory/('frame-%04d.png'%frame)
        assert not path.exists()
        sc.render.filepath=str(path)
        assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
        rows.append({'frame':frame,'file':path.name,'sha256':sha(path)})
        if frame%8==0:
            print('FULLHD_FRAMES',frame,96,'SECONDS',round(time.monotonic()-start,1),flush=True)
    ffmpeg,ffprobe=shutil.which('ffmpeg'),shutil.which('ffprobe')
    assert ffmpeg and ffprobe
    path=out/'CK-001-animation-FullHD.mp4'
    subprocess.run([ffmpeg,'-v','error','-n','-framerate','24','-start_number','1','-i',str(directory/'frame-%04d.png'),
                    '-frames:v','96','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],
                   check=True,capture_output=True,timeout=180)
    result=subprocess.run([ffprobe,'-v','error','-select_streams','v:0','-count_frames','-show_entries',
                           'stream=nb_read_frames,r_frame_rate,width,height,duration','-of','json',str(path)],
                          check=True,capture_output=True,text=True,timeout=60)
    stream=json.loads(result.stdout)['streams'][0]
    assert [stream['width'],stream['height']]==list(SIZE) and int(stream['nb_read_frames'])==96 and stream['r_frame_rate']=='24/1',stream
    subprocess.run([ffmpeg,'-v','error','-i',str(path),'-f','null','-'],check=True,capture_output=True,timeout=120)
    return {'file':path.name,'sha256':sha(path),'probe':stream,'full_decode':'pass','frames':rows,
            'camera':camera,'render_seconds':round(time.monotonic()-start,3)}
