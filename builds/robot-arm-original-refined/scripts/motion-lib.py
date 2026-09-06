"""Deterministic native movement with explicit held intervals."""
import bpy
from mathutils import Vector
from bpy_extras.anim_utils import action_get_channelbag_for_slot


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t*t*t*(10+t*(-15+6*t))


def empty(sc, name):
    root = bpy.data.objects.new(name, None)
    sc.collection.objects.link(root)
    return root


def move(root, start, end, first, duration):
    start, end = Vector(start), Vector(end)
    root.location = start
    root.keyframe_insert('location', frame=first)
    for frame in range(first+1, first+duration+1):
        root.location = start.lerp(end, smooth((frame-first)/duration))
        root.keyframe_insert('location', frame=frame)


def linear_keys(ob):
    if not ob.animation_data:
        return
    bag = action_get_channelbag_for_slot(ob.animation_data.action, ob.animation_data.action_slot)
    for curve in bag.fcurves:
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'


def bounds(obs):
    pts = [o.matrix_world @ Vector(v) for o in obs for v in o.bound_box]
    low = Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return low, high
