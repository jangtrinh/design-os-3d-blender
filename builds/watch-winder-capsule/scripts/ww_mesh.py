"""Pure mesh constructors (verts, faces) in METRES. No bpy state, no operators.

All builders return (verts, faces) lists suitable for Mesh.from_pydata. Quad
dominant; poles are triangle fans and documented per builder.
"""
import math

from mathutils import Matrix, Vector


def lathe(profile, segments=64, closed=True):
    """Revolve a (r, z) profile around local Z.

    profile: list of (r, z) in metres. Points with r == 0 become single pole
    vertices (triangle fan). closed=True connects the last profile point back
    to the first (thick, watertight cross-section).
    """
    verts, faces = [], []
    rings = []
    for r, z in profile:
        if abs(r) < 1e-9:
            rings.append([len(verts)])
            verts.append((0.0, 0.0, z))
        else:
            idx = []
            for j in range(segments):
                a = 2.0 * math.pi * j / segments
                idx.append(len(verts))
                verts.append((r * math.cos(a), r * math.sin(a), z))
            rings.append(idx)
    pairs = list(zip(rings, rings[1:]))
    if closed:
        pairs.append((rings[-1], rings[0]))
    for a, b in pairs:
        if len(a) == 1 and len(b) == 1:
            continue
        for j in range(segments):
            k = (j + 1) % segments
            if len(a) == 1:
                faces.append((a[0], b[k], b[j]))  # start-pole fan, same winding as the quads
            elif len(b) == 1:
                faces.append((a[j], a[k], b[0]))
            else:
                faces.append((a[j], a[k], b[k], b[j]))
    if closed:
        verts, faces = orient_outward(verts, faces)
    return verts, faces


def signed_volume(verts, faces):
    """Fan-triangulated signed volume; > 0 means outward-facing normals (closed meshes)."""
    vol = 0.0
    for f in faces:
        p0 = Vector(verts[f[0]])
        for i in range(1, len(f) - 1):
            vol += p0.dot(Vector(verts[f[i]]).cross(Vector(verts[f[i + 1]])))
    return vol / 6.0


def orient_outward(verts, faces):
    """Flip every face when the closed mesh is inside-out (booleans need outward normals)."""
    if signed_volume(verts, faces) < 0:
        faces = [tuple(reversed(f)) for f in faces]
    return verts, faces


def arc(radius, a0, a1, n, z_offset=0.0):
    """(r, z) points on a circle of `radius` from polar angle a0 to a1 (rad from +Z)."""
    pts = []
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        pts.append((radius * math.sin(t), z_offset + radius * math.cos(t)))
    return pts


def dedupe_profile(pts, eps=1e-7):
    out = []
    for p in pts:
        if not out or abs(out[-1][0] - p[0]) > eps or abs(out[-1][1] - p[1]) > eps:
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


def cylinder(radius, z0, z1, segments=48, cap=True):
    prof = [(0.0, z0), (radius, z0), (radius, z1), (0.0, z1)] if cap else [(radius, z0), (radius, z1)]
    return lathe(prof, segments, closed=cap)


def annulus(r_in, r_out, z0, z1, segments=96):
    return lathe([(r_in, z0), (r_out, z0), (r_out, z1), (r_in, z1)], segments, closed=True)


def tapered_tube(p0, p1, r0, r1, segments=24, cap=True):
    """Cone frustum from world point p0 (radius r0) to p1 (radius r1)."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    length = axis.length
    prof = [(0.0, 0.0), (r0, 0.0), (r1, length), (0.0, length)] if cap else [(r0, 0.0), (r1, length)]
    v, f = lathe(prof, segments, closed=cap)
    rot = axis.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    m = Matrix.Translation(p0) @ rot
    return [tuple(m @ Vector(p)) for p in v], f


def rounded_box(sx, sy, sz, radius, corner_segs=4, z_center=0.0):
    """Box with rounded vertical (Z) edges; flat top/bottom, closed."""
    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    r = min(radius, hx, hy)
    ring = []
    centers = [(hx - r, hy - r, 0.0), (-(hx - r), hy - r, math.pi / 2),
               (-(hx - r), -(hy - r), math.pi), (hx - r, -(hy - r), 3 * math.pi / 2)]
    for cx, cy, a0 in centers:
        for i in range(corner_segs + 1):
            a = a0 + (math.pi / 2) * i / corner_segs
            pt = (cx + r * math.cos(a), cy + r * math.sin(a))
            if not ring or math.hypot(ring[-1][0] - pt[0], ring[-1][1] - pt[1]) > 1e-9:
                ring.append(pt)
    if len(ring) > 1 and math.hypot(ring[-1][0] - ring[0][0], ring[-1][1] - ring[0][1]) <= 1e-9:
        ring.pop()  # pills: last corner meets the first
    n = len(ring)
    verts = [(x, y, z_center - hz) for x, y in ring] + [(x, y, z_center + hz) for x, y in ring]
    faces = [(j, (j + 1) % n, n + (j + 1) % n, n + j) for j in range(n)]
    faces.append(tuple(range(n - 1, -1, -1)))
    faces.append(tuple(range(n, 2 * n)))
    return orient_outward(verts, faces)


def pill(length, width, height, segs=8):
    """Stadium-shaped button: long axis X, flat top, closed."""
    return rounded_box(length, width, height, width / 2.0, corner_segs=segs, z_center=height / 2.0)


def uv_sphere(radius, u=48, v=24):
    prof = arc(radius, 0.0, math.pi, v)
    return lathe(prof, u, closed=False)


def d_profile(radius, flat_x, n=32):
    """2D circle of `radius` clipped by the plane x <= flat_x (keyed 'D' cross-section)."""
    pts = []
    a_cut = math.acos(min(1.0, flat_x / radius))
    for i in range(n + 1):
        a = a_cut + (2 * math.pi - 2 * a_cut) * i / n
        pts.append((radius * math.cos(a), radius * math.sin(a)))
    return pts


def prism(poly, z0, z1):
    """Extrude a closed 2D polygon (CCW) from z0 to z1; flat caps as n-gons."""
    n = len(poly)
    verts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    faces = [(j, (j + 1) % n, n + (j + 1) % n, n + j) for j in range(n)]
    faces.append(tuple(range(n - 1, -1, -1)))
    faces.append(tuple(range(n, 2 * n)))
    return orient_outward(verts, faces)


def rotate_verts(verts, matrix):
    return [tuple(matrix @ Vector(v)) for v in verts]


def spherical_cap(r_out, r_in, angular_radius, segments=96, n_arc=12):
    """Thick spherical cap about local +Z, centred on the sphere centre at the origin."""
    prof = arc(r_out, 0.0, angular_radius, n_arc) + arc(r_in, angular_radius, 0.0, n_arc)
    return lathe(dedupe_profile(prof), segments, closed=True)
