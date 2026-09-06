"""Data-API mesh constructors for the native FPV drone build."""
import math

import bpy
from mathutils import Vector


def mesh_object(name, verts, faces, collection, material=None, smooth=True):
    mesh = bpy.data.meshes.new(f"{name}-mesh")
    mesh.from_pydata(verts, [], faces, shade_flat=not smooth)
    assert not mesh.validate(verbose=True), f"invalid mesh: {name}"
    mesh.update()
    if smooth:
        mesh.shade_smooth()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if material:
        mesh.materials.append(material)
    return obj


def add_bevel(obj, width, segments=3, angle_limit=0.52):
    mod = obj.modifiers.new("edge-fillet", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = angle_limit
    mod.harden_normals = True
    return mod


def add_subdivision(obj, levels=2, render_levels=2):
    mod = obj.modifiers.new("surface-subdivision", "SUBSURF")
    mod.levels = levels
    mod.render_levels = render_levels
    mod.use_limit_surface = True
    return mod


def cylinder(name, radius, depth, location, collection, material=None,
             vertices=48, rotation=(0.0, 0.0, 0.0), bevel=0.0):
    verts = []
    for z in (-depth * 0.5, depth * 0.5):
        verts.extend((radius * math.cos(2 * math.pi * i / vertices),
                      radius * math.sin(2 * math.pi * i / vertices), z)
                     for i in range(vertices))
    faces = [tuple(range(vertices - 1, -1, -1)),
             tuple(range(vertices, vertices * 2))]
    for i in range(vertices):
        j = (i + 1) % vertices
        faces.append((i, j, vertices + j, vertices + i))
    obj = mesh_object(name, verts, faces, collection, material)
    obj.location = location
    obj.rotation_euler = rotation
    if bevel:
        add_bevel(obj, bevel, 3)
    return obj


def torus(name, center, major_radius, tube_radius, collection, material=None,
          major_segments=64, minor_segments=10, vertical_scale=0.82):
    cx, cy, cz = center
    verts = []
    for i in range(major_segments):
        u = 2 * math.pi * i / major_segments
        for j in range(minor_segments):
            v = 2 * math.pi * j / minor_segments
            radial = major_radius + tube_radius * math.cos(v)
            verts.append((cx + radial * math.cos(u),
                          cy + radial * math.sin(u),
                          cz + tube_radius * vertical_scale * math.sin(v)))
    faces = []
    for i in range(major_segments):
        ni = (i + 1) % major_segments
        for j in range(minor_segments):
            nj = (j + 1) % minor_segments
            faces.append((i * minor_segments + j,
                          ni * minor_segments + j,
                          ni * minor_segments + nj,
                          i * minor_segments + nj))
    return mesh_object(name, verts, faces, collection, material)


def loft(name, sections, collection, material=None, ring_segments=16):
    verts = []
    exponent = 4.0
    for y, half_width, z_center, half_height in sections:
        for i in range(ring_segments):
            angle = 2 * math.pi * i / ring_segments
            c, s = math.cos(angle), math.sin(angle)
            x = half_width * math.copysign(abs(c) ** (2 / exponent), c)
            z = z_center + half_height * math.copysign(
                abs(s) ** (2 / exponent), s)
            verts.append((x, y, z))
    faces = []
    for r in range(len(sections) - 1):
        a, b = r * ring_segments, (r + 1) * ring_segments
        for i in range(ring_segments):
            j = (i + 1) % ring_segments
            faces.append((a + i, a + j, b + j, b + i))
    faces.append(tuple(range(ring_segments - 1, -1, -1)))
    end = (len(sections) - 1) * ring_segments
    faces.append(tuple(end + i for i in range(ring_segments)))
    obj = mesh_object(name, verts, faces, collection, material)
    add_subdivision(obj, 2, 3)
    return obj


def capsule_prism(name, start, end, width, z_center, height, collection,
                  material=None, arc_segments=8, bevel=0.0015):
    p0, p1 = Vector(start), Vector(end)
    direction = (p1 - p0).normalized()
    normal = Vector((-direction.y, direction.x))
    radius = width * 0.5
    outline = []
    base = math.atan2(direction.y, direction.x)
    for i in range(arc_segments + 1):
        angle = base - math.pi * 0.5 + math.pi * i / arc_segments
        outline.append((p1.x + radius * math.cos(angle),
                        p1.y + radius * math.sin(angle)))
    for i in range(arc_segments + 1):
        angle = base + math.pi * 0.5 + math.pi * i / arc_segments
        outline.append((p0.x + radius * math.cos(angle),
                        p0.y + radius * math.sin(angle)))
    count = len(outline)
    verts = [(x, y, z_center - height * 0.5) for x, y in outline]
    verts += [(x, y, z_center + height * 0.5) for x, y in outline]
    faces = [tuple(range(count - 1, -1, -1)),
             tuple(range(count, count * 2))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, count + j, count + i))
    obj = mesh_object(name, verts, faces, collection, material)
    if bevel:
        add_bevel(obj, bevel, 3)
    return obj


def rounded_box(name, size, location, collection, material=None, bevel=0.003):
    sx, sy, sz = (value * 0.5 for value in size)
    verts = [(x, y, z) for z in (-sz, sz) for y in (-sy, sy)
             for x in (-sx, sx)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    obj = mesh_object(name, verts, faces, collection, material)
    obj.location = location
    if bevel > 0:
        add_bevel(obj, bevel, 5)
    return obj


def blade(name, center, angle, collection, material, z=0.055):
    points = [(0.005, -0.0035), (0.012, -0.0060), (0.022, -0.0080),
              (0.031, -0.0060), (0.035, -0.0020), (0.034, 0.0030),
              (0.028, 0.0080), (0.017, 0.0100), (0.008, 0.0060),
              (0.005, 0.0030)]
    ca, sa = math.cos(angle), math.sin(angle)
    outline = [(center[0] + x * ca - y * sa,
                center[1] + x * sa + y * ca) for x, y in points]
    count, half = len(outline), 0.0011
    verts = [(x, y, z - half) for x, y in outline]
    verts += [(x, y, z + half) for x, y in outline]
    faces = [tuple(range(count - 1, -1, -1)), tuple(range(count, count * 2))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, count + j, count + i))
    obj = mesh_object(name, verts, faces, collection, material)
    add_bevel(obj, 0.00045, 3)
    return obj
