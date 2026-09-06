"""Detail mesh constructors (metres): guilloche height-field annulus, diamond-knurl sleeve,
swept leather ribbon. Closed solids; quad dominant; verified by the passes that use them.
"""
import math

from mathutils import Vector


def _close_grid_solid(top, bottom, n_ring, n_around, periodic=True):
    """Faces for a solid whose top and bottom are (n_ring x n_around) grids sharing the
    same (ring, angle) index layout; walls join first/last rings. `top`/`bottom` are
    vertex index offsets. Returns face list."""
    faces = []
    na = n_around
    step = na if periodic else na - 1
    for i in range(n_ring - 1):
        for j in range(step):
            k = (j + 1) % na
            a, b, c, d = top + i * na + j, top + i * na + k, top + (i + 1) * na + k, top + (i + 1) * na + j
            faces.append((a, b, c, d))
            a, b, c, d = bottom + i * na + j, bottom + i * na + k, bottom + (i + 1) * na + k, bottom + (i + 1) * na + j
            faces.append((d, c, b, a))
    for j in range(step):  # inner wall (ring 0) and outer wall (ring n-1)
        k = (j + 1) % na
        faces.append((top + k, top + j, bottom + j, bottom + k))
        o = (n_ring - 1) * na
        faces.append((top + o + j, top + o + k, bottom + o + k, bottom + o + j))
    return faces


def guilloche_annulus(r_in, r_out, z_base, z_bottom, amplitude, rays=128, twist_rad=0.18,
                      n_ring=40, samples_per_ray=8, flat_border=0.0):
    """Spiral-ray relief: z(r,t) = z_base + a*(0.5+0.5*cos(N*(t - beta*(r-r_in)/(r_out-r_in)))).
    Optional flat polished borders of width `flat_border` at both edges (crisp step)."""
    na = rays * samples_per_ray
    verts = []
    for i in range(n_ring):
        r = r_in + (r_out - r_in) * i / (n_ring - 1)
        u = (r - r_in) / (r_out - r_in)
        in_border = (r - r_in) < flat_border or (r_out - r) < flat_border
        for j in range(na):
            t = 2 * math.pi * j / na
            z = z_base if in_border else z_base + amplitude * (0.5 + 0.5 * math.cos(rays * (t - twist_rad * u)))
            verts.append((r * math.cos(t), r * math.sin(t), z))
    top = 0
    bottom = len(verts)
    verts += [(x, y, z_bottom) for x, y, _ in verts[:bottom]]
    return verts, _close_grid_solid(top, bottom, n_ring, na)


def knurl_sleeve(x0, x1, r_inner, r_base, relief, pitch, samples_per_pitch=8, n_along=None):
    """Diamond knurl as one connected cylindrical height field about local X.
    Two opposite-handed 45-degree ridge families; periodic seam by integer diamond count."""
    circ = 2 * math.pi * r_base
    n_diamonds = max(8, round(circ / pitch))
    na = n_diamonds * samples_per_pitch
    length = x1 - x0
    n_along = n_along or max(4, int(length / pitch * samples_per_pitch))
    verts = []
    for i in range(n_along):
        x = x0 + length * i / (n_along - 1)
        for j in range(na):
            t = 2 * math.pi * j / na
            s = t * r_base
            u1 = 2 * math.pi * (s + x) / pitch  # right-hand helix family
            u2 = 2 * math.pi * (s - x) / pitch  # left-hand helix family
            h = (0.5 + 0.5 * math.cos(u1)) * (0.5 + 0.5 * math.cos(u2))
            r = r_base - relief + relief * h
            verts.append((x, r * math.cos(t), r * math.sin(t)))
    top = 0
    bottom = len(verts)
    verts += [(x, r_inner * math.cos(2 * math.pi * (k % na) / na), r_inner * math.sin(2 * math.pi * (k % na) / na))
              for k, (x, _, _) in enumerate(verts[:bottom])]
    return verts, _close_grid_solid(top, bottom, n_along, na)


def ribbon(path_yz, width_x, thickness, segs_round=0):
    """Closed strap solid swept along a polyline in the (y, z) plane, extruded +-x.
    The profile is a rectangle width_x x thickness; thickness is applied along the path normal."""
    pts = [Vector((0.0, y, z)) for y, z in path_yz]
    n = len(pts)
    normals = []
    for i in range(n):
        p0 = pts[max(i - 1, 0)]
        p1 = pts[min(i + 1, n - 1)]
        tang = (p1 - p0).normalized()
        normals.append(Vector((0.0, -tang.z, tang.y)))  # rotate tangent +90 deg in the yz plane
    hx, ht = width_x / 2.0, thickness / 2.0
    verts = []
    for p, nrm in zip(pts, normals):
        for sx in (-hx, hx):
            for st in (-ht, ht):
                q = p + nrm * st
                verts.append((sx, q.y, q.z))
    # per station: 0:(-x,-t) 1:(-x,+t) 2:(+x,-t) 3:(+x,+t)
    ring = [0, 1, 3, 2]
    faces = []
    for i in range(n - 1):
        a, b = i * 4, (i + 1) * 4
        for k in range(4):
            r0, r1 = ring[k], ring[(k + 1) % 4]
            faces.append((a + r0, a + r1, b + r1, b + r0))
    faces.append(tuple(ring))
    faces.append(tuple(reversed([(n - 1) * 4 + r for r in ring])))
    return verts, faces
