"""Hash exact static-render inputs; never interpolate or drop timeline frames."""
import array, hashlib


def state_key(scene):
    values=[]
    for ob in sorted(scene.objects,key=lambda item:item.name):
        if ob.type not in {'MESH','CURVE','CAMERA','LIGHT','EMPTY'}:
            raise AssertionError(ob.type)
        values.append(float(ob.hide_render))
        values.extend(x for row in ob.matrix_world for x in row)
        if ob.type=='CURVE':
            for spline in ob.data.splines:
                for point in spline.points:values.extend(point.co)
        if ob.type=='CAMERA':values.append(ob.data.ortho_scale)
    return hashlib.sha256(array.array('f',values).tobytes()).hexdigest()


def verify_static_render_domain(scene):
    assert not scene.render.use_motion_blur
    assert not scene.cycles.use_animated_seed
    for ob in scene.objects:
        assert not ob.constraints and not ob.particle_systems,ob.name
        for modifier in ob.modifiers:
            assert modifier.type not in {'NODES','CLOTH','FLUID','PARTICLE_SYSTEM'},ob.name
    for material in {m for ob in scene.objects if ob.type=='MESH' for m in ob.data.materials if m}:
        assert not material.animation_data and not material.node_tree.animation_data,material.name
    assert not scene.world.animation_data and not scene.world.node_tree.animation_data
