"""tapas_r103.py: jambas, techo liso de yeso, cornisa y respaldos del pasillo r103 (tapan rendijas y el artesonado de UC con trozos de atlas grises)."""
import math, os
Q = []
def quad(p0, p1, y0, y1, mat, E=1.2): Q.append((mat, [(p0[0], y0, p0[1]), (p1[0], y0, p1[1]), (p1[0], y1, p1[1]), (p0[0], y1, p0[1])], E))
def hz(x0, x1, z0, z1, y, mat, E=1.4): Q.append((mat, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], E, 'h'))
quad((-1.23, 1.25), (-1.23, 1.55), 4.0, 7.25, 'r100_kabe_a'); quad((-2.22, 1.25), (-2.22, 1.55), 4.0, 7.25, 'r100_kabe_a')
quad((-1.26, 1.46), (-0.92, 1.46), 4.0, 7.25, 'r100_kabe_a'); quad((-2.55, 1.46), (-2.19, 1.46), 4.0, 7.25, 'r100_kabe_a')
hz(-9.0, 10.95, 1.3, 2.95, 7.2, 'st_103tenjou_a')
quad((-9.0, 1.47), (10.95, 1.47), 6.3, 7.2, 'r100_kabe_a'); quad((-9.0, 2.79), (10.95, 2.79), 6.3, 7.2, 'r100_kabe_a')
quad((-9.0, 1.49), (10.95, 1.49), 6.95, 7.2, 'st_103wood_a', 0.5); quad((-9.0, 2.77), (10.95, 2.77), 6.95, 7.2, 'st_103wood_a', 0.5)
quad((9.4, 2.8), (10.95, 2.8), 4.0, 6.4, 'r100_kabe_a')
quad((-8.95, 1.35), (-8.95, 2.85), 6.95, 7.5, 'st_103wood_a', 0.6); quad((10.9, 1.35), (10.9, 2.85), 6.95, 7.5, 'st_103wood_a', 0.6)
v = []; vt = []; out = []
for it in Q:
    mat, pts, E = it[:3]; b = len(v)
    if len(it) == 4:
        for p in pts: v.append(p); vt.append((p[0] / E, p[2] / E))
    else:
        L = math.dist((pts[0][0], pts[0][2]), (pts[1][0], pts[1][2]))
        for p, (u, w) in zip(pts, [(0, pts[0][1]), (L, pts[1][1]), (L, pts[2][1]), (0, pts[3][1])]): v.append(p); vt.append((u / E, w / E))
    out.append(f'usemtl {mat}')
    for a, bb, c in [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)]: out.append(f'f {b+a+1}/{b+a+1} {b+bb+1}/{b+bb+1} {b+c+1}/{b+c+1}')
d = '/home/claude/re1gc/modelos/tapas_r103'; os.makedirs(d, exist_ok=True)
open(f'{d}/tapas.obj', 'w').write('\n'.join([f'v {x} {y} {z}' for x, y, z in v] + [f'vt {a} {b}' for a, b in vt] + out) + '\n')
