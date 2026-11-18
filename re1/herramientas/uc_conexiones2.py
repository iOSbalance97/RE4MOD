"""Puertas entre las salas de UC (con la colisión real de UC, chit.col) en coordenadas de RE4.
Cada puerta: pareja de salas y punto aproximado (sacado del solape de suelos y de las hojas de puerta del modelo).
Por puerta se calcula:
  u      dirección A->B (suelo solo de A frente a suelo solo de B alrededor de la puerta)
  área   cuadrilátero XZ4 de 1,4 m de ancho, de 1,1 m dentro de la sala hasta 0,3 m pasado el umbral
  llegada en la otra sala a ~1,5 m del umbral, sobre su suelo, lejos de sus otras áreas, mirando hacia dentro
  hueco  si el modelo de la sala no tiene hoja de puerta ahí, se mide el hueco (rayos) para taparlo con una puerta
uso: uc_conexiones2.py salida.json"""
import json, pickle, re, sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/claude/tools')
import objload, re4room

COL = "19.4,0,15.0,-47609,12,7084,-1.253"
PUERTAS = [  # sala A, sala B, punto aproximado (m, coordenadas de RE4)
    ('r102', 'r101', (-42.4, 0.0, -2.4)), ('r102', 'r103', (-39.54, 0.0, 11.72)), ('r101', 'r100', (-43.44, 0.0, -18.85)),
    ('r102', 'r108', (-34.8, 4.0, 9.9)), ('r102', 'r111', (-46.6, 4.5, -0.1)),
    ('r103', 'r104', (-37.83, 0.0, 19.86)), ('r104', 'r105', (-21.39, 0.0, 27.89)), ('r105', 'r106', (-21.95, 0.0, 15.34)),
    ('r106', 'r107', (-21.82, 0.0, 12.14)), ('r107', 'r108', (-23.35, 3.53, 12.61)), ('r108', 'r109', (-27.5, 3.53, 17.73)),
    ('r112', 'r113', (-31.19, 4.02, -25.45)), ('r111', 'r112', (-44.08, 4.03, -22.4)),
    ('r113', 'r114', (-39.61, 4.03, -13.93)), ('r114', 'r115', (-30.82, 4.02, -7.16)),
    ('r101', 'r112', (-44.0, 4.0, -18.7)), ('r101', 'r113', (-42.7, 4.0, -14.9)), ('r101', 'r114', (-40.0, 4.0, -8.9)),
]
SALIDA_PUEBLO = ('r102', (-48.8, 0.0, 7.5))      # puerta principal del vestíbulo -> pueblo

fl = pickle.load(open('/tmp/fl2.pkl', 'rb'))
T3 = {r: cKDTree(P) for r, P in fl.items()}

def suelo_cerca(R, c, rad, dy):
    P = fl[R]; d = np.hypot(P[:, 0] - c[0], P[:, 2] - c[2])
    return np.where((d < rad) & (np.abs(P[:, 1] - c[1]) < dy))[0]

def direccion(A, B, c):
    ia = suelo_cerca(A, c, 3.0, 1.3); ib = suelo_cerca(B, c, 3.0, 1.3)
    pa = fl[A][ia]; pb = fl[B][ib]
    sa = pa[T3[B].query(pa)[0] > 0.35]; sb = pb[T3[A].query(pb)[0] > 0.35]   # solo de A / solo de B
    if len(sa) < 5: sa = pa
    if len(sb) < 5: sb = pb
    u = (sb.mean(0) - sa.mean(0))[[0, 2]]; u /= np.linalg.norm(u)
    return u

def umbral(A, B, c, u):
    """Punto del umbral: donde, avanzando por u, se acaba el suelo solo de A y empieza el de B."""
    best = None
    for s in np.arange(-2.0, 2.01, 0.05):
        p = c.copy(); p[[0, 2]] = c[[0, 2]] + u * s
        ia = suelo_cerca(A, p, 0.25, 1.0); ib = suelo_cerca(B, p, 0.25, 1.0)
        fa = len(ia) > 0; fb = len(ib) > 0
        if best is None and fb and not (fa and s < 0): best = s
    s = best if best is not None else 0.0
    p = c.copy(); p[[0, 2]] = c[[0, 2]] + u * s
    return p

def quad(c, u, floor_y, back=1.1, front=0.3, half=0.7):
    n = np.array([-u[1], u[0]])
    base = c[[0, 2]]
    pts = [base - u * back - n * half, base + u * front - n * half, base + u * front + n * half, base - u * back + n * half]
    pts = [list(map(float, p * 1000)) for p in pts]
    if not hit_xz4(pts, (base - u * back * 0.5) * 1000): pts = pts[::-1]
    assert hit_xz4(pts, (base - u * back * 0.5) * 1000)
    return dict(floor=float(floor_y * 1000 - 300), height=2600.0, pts=pts)

def hit_xz4(p, q):
    x, z = q
    (x0, z0), (x1, z1), (x2, z2), (x3, z3) = p
    if (x3 - x0) * (z - z0) > (z3 - z0) * (x - x0) or (x1 - x0) * (z - z0) < (z1 - z0) * (x - x0): return False
    if (x3 - x2) * (z - z2) < (z3 - z2) * (x - x2) or (x1 - x2) * (z - z2) > (z1 - z2) * (x - x2): return False
    return True

def floor_y(R, p):
    i = suelo_cerca(R, p, 0.6, 1.3)
    if not len(i): i = suelo_cerca(R, p, 1.5, 1.5)
    assert len(i), (R, p)
    P = fl[R][i]; return float(P[np.argmin(np.hypot(P[:, 0] - p[0], P[:, 2] - p[2])), 1])

out = []
for A, B, c0 in PUERTAS:
    c = np.array(c0, float)
    u = direccion(A, B, c)
    t = umbral(A, B, c, u)
    out.append(dict(a=A, b=B, umbral=[float(x) for x in t], u=[float(x) for x in u], ya=floor_y(A, t - np.array([u[0], 0, u[1]]) * 0.5),
                    yb=floor_y(B, t + np.array([u[0], 0, u[1]]) * 0.5)))
# salida al pueblo
c = np.array(SALIDA_PUEBLO[1]); ia = suelo_cerca('r102', c, 4.0, 1.0)
u = c[[0, 2]] - fl['r102'][ia].mean(0)[[0, 2]]; u /= np.linalg.norm(u)
out.append(dict(a='r102', b='PUEBLO', umbral=[float(x) for x in c], u=[float(x) for x in u], ya=floor_y('r102', c - np.array([u[0], 0, u[1]]) * 0.5), yb=None))

# áreas
for q in out:
    t = np.array(q['umbral']); u = np.array(q['u'])
    q['area_a'] = quad(t, u, q['ya'])
    if q['yb'] is not None: q['area_b'] = quad(t, -u, q['yb'])
# llegadas: ~1,5 m dentro, sobre el suelo de la sala, a >0,5 m de cualquier área de esa sala
def areas_de(R):
    res = []
    for q in out:
        if q['a'] == R: res.append(q['area_a'])
        if q['b'] == R: res.append(q['area_b'])
    return res
def dist_area(p, ar):
    pts = np.array(ar['pts']) / 1000
    if hit_xz4(ar['pts'], (p[0] * 1000, p[2] * 1000)): return 0.0
    d = []
    for k in range(4):
        a, b = pts[k], pts[(k + 1) % 4]; ab = b - a; s = np.clip(np.dot(p[[0, 2]] - a, ab) / np.dot(ab, ab), 0, 1)
        d.append(np.linalg.norm(p[[0, 2]] - (a + ab * s)))
    return min(d)
for q in out:
    for lado, R, sg, y in (('b', q['b'], 1, q['yb']), ('a', q['a'], -1, q['ya'])):
        if R == 'PUEBLO': continue
        t = np.array(q['umbral']); u = np.array(q['u']) * sg
        P = fl[R]; d = np.hypot(P[:, 0] - t[0], P[:, 2] - t[2])
        along = (P[:, [0, 2]] - t[[0, 2]]) @ u; lat = np.abs((P[:, [0, 2]] - t[[0, 2]]) @ np.array([-u[1], u[0]]))
        ok = (np.abs(P[:, 1] - y) < 0.6 + 0.7 * np.clip(along, 0, None)) & (along > 0.9) & (along < 3.0)   # escaleras: sube con la distancia
        clear = np.array([min(dist_area(p, ar) for ar in areas_de(R)) for p in P[ok]]) if ok.any() else np.array([])
        cand = np.where(ok)[0][clear > 0.5] if len(clear) else []
        assert len(cand), (q['a'], q['b'], lado)
        j = cand[np.argmin(np.abs(along[cand] - 1.5) + 0.7 * lat[cand])]
        p = P[j]
        q['llegada_' + lado] = dict(pos=[float(x * 1000) for x in p], ang=float(np.arctan2(u[0], u[1])),
                                    libre=float(min(dist_area(p, ar) for ar in areas_de(R))))
json.dump(out, open(sys.argv[1], 'w'), indent=1)
for q in out:
    la = q.get('llegada_a', {}); lb = q.get('llegada_b', {})
    print(f"{q['a']}<->{q['b']}: umbral {np.round(q['umbral'], 2)} u {np.round(q['u'], 2)} suelo {q['ya']:.2f}/{q['yb'] if q['yb'] is None else round(q['yb'], 2)} "
          f"llegadas libres {la.get('libre', 0):.2f}/{lb.get('libre', 0):.2f} m")
