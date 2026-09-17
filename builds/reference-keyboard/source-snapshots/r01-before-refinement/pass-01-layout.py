"""XY layout blockout only; unresolved final Z is not manufacturing acceptance."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'scripts'))
from project import layout,key_rows,output_context,write
import meshkit as g
import studio
import bpy
from agent_runtime import emit_ok

assert bpy.app.background
out,inputs=output_context()
data=layout()
sc=bpy.data.scenes.new('RK_LAYOUT_BLOCKOUT')
bpy.context.window.scene=sc
sc.unit_settings.system,sc.unit_settings.scale_length='METRIC',1
m=studio.palette()
g.assign(g.slab('RK_BASE',.284,.092,.004,0,.003),m['silver'])
g.assign(g.slab('RK_DIFFUSER',.284,.092,.004,.003,.010),m['diffuser'])
g.assign(g.slab('RK_MAIN_PLATE',.254,.073,.003,.0125,.014,(.015,-.0095)),m['black'])
g.assign(g.slab('RK_LOOP_PLATE',.234,.018,.003,.0125,.014,(.025,.037)),m['black'])
g.assign(g.slab('RK_NANO_PLATE',.030,.092,.003,.0125,.014,(-.126,0)),m['black'])
g.assign(g.slab('RK_HUB_PLATE',.026,.024,.002,.013,.0145,(-.105,.034)),m['silver'])
for row in key_rows(data):
    width=(data['key_base_mm']+(row['units']-1)*data['pitch_x_mm'])/1000
    xy=tuple(v/1000 for v in row['xy_mm'])
    g.assign(g.bevel(g.slab(row['id'],width,.0162,.003,.017,.022,xy),.0004),m['key'])
for i,xy in enumerate(data['knobs_mm']):
    g.assign(g.bevel(g.cylinder('RK_KNOB_%d'%(i+1),.008,.014,.032,tuple(v/1000 for v in xy)),.0004),m['silver'])
for i,(x,y) in enumerate(((-.125,-.034),(.125,-.034),(-.125,.034),(.125,.034))):
    g.assign(g.slab('RK_FOOT_%d'%i,.019,.010,.003,-.003,0,(x,y)),m['rubber'])
studio.setup()
views={'hero':studio.capture(out/'hero.png'),
       'top':studio.capture(out/'top.png',location=(0,0,.50),target=(0,0,0),scale=.32)}
write(out/'views.json',views)
write(out/'layout-measurements.json',{'objects':[g.numeric(o) for o in sc.objects if o.type=='MESH' and o.name.startswith('RK_')],
                                    'scope':'layout blockout, not final-height or manufacture qualification'})
assert bpy.ops.wm.save_as_mainfile(filepath=str(out/'layout.blend'))=={'FINISHED'}
emit_ok('reference-keyboard-layout',keys=len(key_rows(data)),knobs=len(data['knobs_mm']),width_mm=data['width_mm'],depth_mm=data['depth_mm'])
