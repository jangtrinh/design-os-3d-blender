"""Native task render; preview pass or complete30second film."""
from pathlib import Path
import bpy,os
ROOT=Path(__file__).resolve().parent
sc=bpy.data.scenes['ARM2-Task-demo'];bpy.context.window.scene=sc
sc.render.engine='CYCLES';sc.cycles.samples=6;sc.cycles.use_denoising=True
if os.environ.get('ARM_GPU_DENOISE'):sc.cycles.denoising_use_gpu=True
if os.environ.get('ARM_RENDER_THREADS'):
    sc.render.threads_mode='FIXED';sc.render.threads=int(os.environ['ARM_RENDER_THREADS'])
preview=os.environ.get('ARM_PREVIEW_FRAMES')
if preview:
    for frame in map(int,preview.split(',')):
        sc.frame_set(frame);sc.render.filepath=str(ROOT/f'renders/task-{frame:04d}.png');bpy.ops.render.render(write_still=True)
else:
    folder=ROOT/'videos/task-frames';folder.mkdir(exist_ok=True)
    sc.frame_start=int(os.environ.get('ARM_RENDER_START','1'))
    sc.frame_end=int(os.environ.get('ARM_RENDER_END','720'))
    sc.render.filepath=str(folder/'frame-');bpy.ops.render.render(animation=True)
