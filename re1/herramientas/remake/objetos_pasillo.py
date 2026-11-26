"""objetos al final del pasillo en L de r107: mueble y silla tapados con sábanas y cuadros apoyados en la pared"""
import numpy as np
rng = np.random.default_rng(11)
CENTROS = []
V = []; T = []; Fs = []
def add(Vp, Tp, Fp, mat):
    b = len(V); V.extend(Vp); T.extend(Tp); Fs.extend([(mat, [b + a for a in f]) for f in Fp])
def tapado(cx, cz, sx, sz, h, giro=0.0, n=10, pliegues=7, amp=0.035, hfun=None):
    hf = hfun or (lambda x, z: h)
    CENTROS.append(np.array([cx, h * 0.45, cz]))
    """caja tapada con una sábana: lados con pliegues que se abren hacia el bajo, tapa algo hundida"""
    Vp = []; Tp = []; Fp = []
    per = 2 * (sx + sz); c, s = np.cos(giro), np.sin(giro)
    def borde(t):          # t en [0,1) alrededor del rectángulo -> (x, z, normal)
        d = t * per
        for (L, p0, dv, nv) in ((sx, (-sx/2, -sz/2), (1, 0), (0, -1)), (sz, (sx/2, -sz/2), (0, 1), (1, 0)), (sx, (sx/2, sz/2), (-1, 0), (0, 1)), (sz, (-sx/2, sz/2), (0, -1), (-1, 0))):
            if d <= L: return np.array([p0[0] + dv[0] * d, p0[1] + dv[1] * d]), np.array(nv, float)
            d -= L
        return np.array([-sx/2, -sz/2]), np.array([0, -1.0])
    nu = int(per / 0.09); nv = n
    fase = rng.random(pliegues) * 6.28
    for j in range(nv + 1):
        v = j / nv
        for i in range(nu + 1):
            t = i / nu; p, nn = borde(t % 1.0); y = hf(p[0], p[1]) * (1 - v)
            # pliegues: crecen hacia abajo; el bajo se abre un poco
            w = sum(np.sin(t * per * (3.0 + k * 1.7) + fase[k]) for k in range(3)) / 3
            off = amp * (0.25 + v ** 1.5) * w + 0.06 * v ** 2.5
            # esquinas redondeadas arriba
            q = p + nn * off - nn * 0.05 * (1 - min(1.0, v * 6.0)) ** 2          # canto de arriba redondeado
            Vp.append([cx + c * q[0] + s * q[1], y if v > 0 else y - 0.01, cz - s * q[0] + c * q[1]]); Tp.append([t * per / 0.9, v * h / 0.9 + 0.1])
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i; b = a + 1; c2 = a + nu + 1; d = c2 + 1
            Fp += [[a, c2, b], [b, c2, d]]
    # tapa: rejilla hundida en el centro
    m = 10; b0 = len(Vp)
    for j in range(m + 1):
        for i in range(m + 1):
            u, v = i / m, j / m; x = (u - .5) * sx; z = (v - .5) * sz
            sag = 0.03 * np.sin(np.pi * u) * np.sin(np.pi * v) + 0.01 * rng.standard_normal()
            Vp.append([cx + c * x + s * z, hf(x, z) - sag, cz - s * x + c * z]); Tp.append([u * sx / 0.9, v * sz / 0.9])
    for j in range(m):
        for i in range(m):
            a = b0 + j * (m + 1) + i; Fp += [[a, a + 1, a + m + 1], [a + 1, a + m + 2, a + m + 1]]
    return Vp, Tp, Fp
def cuadro(x0, z0, ancho, alto, inclin, normal, lienzo, grosor=0.05):
    """cuadro apoyado en la pared: pie en (x0,z0) a ras de suelo, se inclina hacia la pared (normal = hacia fuera de la pared)"""
    nrm = np.array([normal[0], 0, normal[1]], float); t = np.array([-normal[1], 0, normal[0]], float)
    up = np.array([0, np.cos(inclin), 0]) - nrm * np.sin(inclin)
    o = np.array([x0, 0.0, z0]) - t * ancho / 2
    P = lambda a, b, c: o + t * a + up * b + nrm * c
    caras = []
    f = [P(0, 0, grosor), P(ancho, 0, grosor), P(ancho, alto, grosor), P(0, alto, grosor)]
    add(f, [[0, 0], [1, 0], [1, 1], [0, 1]], [[0, 1, 2], [0, 2, 3]], lienzo)
    k = [P(0, 0, 0), P(ancho, 0, 0), P(ancho, alto, 0), P(0, alto, 0)]
    add(k, [[0, 0], [ancho, 0], [ancho, alto], [0, alto]], [[0, 2, 1], [0, 3, 2]], 'madera')
    for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
        add([k[a], k[b], f[b], f[a]], [[0, 0], [1, 0], [1, .1], [0, .1]], [[0, 1, 2], [0, 2, 3]], 'madera')
    return

import sys
out = sys.argv[1]
def caja(p0, p1, mat, esc=0.6):
    """caja de p0 a p1 (esquinas), 6 caras con UV planas"""
    x0, y0, z0 = p0; x1, y1, z1 = p1
    P = [[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]]
    for (a, b, c, d), ej in (((0,1,2,3),(0,1)),((5,4,7,6),(0,1)),((4,0,3,7),(2,1)),((1,5,6,2),(2,1)),((3,2,6,7),(0,2)),((4,5,1,0),(0,2))):
        q = [P[a], P[b], P[c], P[d]]
        add(q, [[q_[ej[0]] / esc, q_[ej[1]] / esc] for q_ in q], [[0, 1, 2], [0, 2, 3]], mat)
# armario de madera al fondo (x = 1.5), puertas hacia el pasillo (+x)
X0, X1, Z0, Z1, H = 1.55, 2.1, -4.62, -3.48, 1.95
caja((X0, 0.08, Z0), (X1, H - 0.1, Z1), 'mueble')                          # cuerpo
caja((X0 - 0.01, 0.0, Z0 - 0.02), (X1 + 0.03, 0.1, Z1 + 0.02), 'moldura')    # zócalo
caja((X0 - 0.01, H - 0.12, Z0 - 0.04), (X1 + 0.06, H, Z1 + 0.04), 'moldura')  # cornisa
zm = (Z0 + Z1) / 2
for za, zb in ((Z0 + 0.06, zm - 0.015), (zm + 0.015, Z1 - 0.06)):          # dos puertas con cuarterones
    caja((X1, 0.2, za), (X1 + 0.025, H - 0.22, zb), 'puerta', esc=0.9)
    for ya, yb in ((0.3, 0.95), (1.08, H - 0.32)):
        caja((X1 + 0.025, ya, za + 0.07), (X1 + 0.04, yb, zb - 0.07), 'moldura')
    zt = zb - 0.06 if za < zm else za + 0.06
    caja((X1 + 0.04, 1.0, zt - 0.012), (X1 + 0.075, 1.1, zt + 0.012), 'tirador')
# silla tapada con la sábana: asiento a 0.5 y respaldo hasta 1.0 contra la pared del fondo
def h_silla(x, z): return 1.0 if x < -0.12 else 0.52
Vp, Tp, Fp = tapado(2.42, -3.05, 0.55, 0.55, 1.0, giro=0.0, pliegues=5, amp=0.06, hfun=h_silla); add(Vp, Tp, Fp, 'sabana')
# cuadros apoyados en la pared sur, uno junto a otro (sin cortarse con la pared ni entre ellos)
for (x, an, al, inc, lz) in ((2.95, 1.0, 0.78, 0.16, 'cuadro12'), (4.05, 0.82, 0.64, 0.15, 'cuadro14'), (4.95, 0.68, 0.54, 0.17, 'cuadro13')):
    cuadro(x, -4.62 + al * np.sin(inc), an, al, inc, (0, 1), lz)
# muebles tapados del cuarto de las sábanas (en el sitio de los de UC)
for (x0, x1, z0, z1, h, am) in ((4.18, 4.95, -0.78, -0.06, 1.38, 0.05), (5.26, 6.29, -2.13, -1.66, 2.1, 0.05), (7.2, 8.22, -3.6, -1.6, 1.15, 0.06),
                                (7.7, 8.3, -1.5, -0.08, 2.0, 0.05), (5.12, 6.25, -0.7, -0.06, 1.05, 0.06)):
    Vp, Tp, Fp = tapado((x0 + x1) / 2, (z0 + z1) / 2, x1 - x0, z1 - z0, h, amp=am); add(Vp, Tp, Fp, 'sabana')
# sombreado horneado de las sábanas: 4 tonos según la luz (de arriba y del lado del pasillo)
ld = np.array([0.45, 1.0, 0.35]); ld /= np.linalg.norm(ld)
VV = np.array(V)
for k_, (m, fa) in enumerate(Fs):
    if not m.startswith('sabana'): continue
    p = VV[fa]; n = np.cross(p[1] - p[0], p[2] - p[0]); n /= np.linalg.norm(n) + 1e-12
    c = p.mean(0); cen = min(CENTROS, key=lambda q: np.hypot(*(q - p.mean(0))[[0, 2]]))
    if n @ (c - cen) < 0: n = -n
    t = int(np.clip(3 - np.floor((n @ ld + 0.25) / 1.25 * 4), 0, 3))
    Fs[k_] = (f'{m}_t{t}', fa)
with open(out, 'w') as f:
    for v in V: f.write('v %.4f %.4f %.4f\n' % tuple(v))
    for t in T: f.write('vt %.4f %.4f\n' % tuple(t))
    cur = None
    for m, fa in Fs:
        if m != cur: f.write(f'usemtl {m}\n'); cur = m
        f.write('f ' + ' '.join(f'{a+1}/{a+1}' for a in fa) + '\n')
print(len(V), 'vértices', len(Fs), 'triángulos')
