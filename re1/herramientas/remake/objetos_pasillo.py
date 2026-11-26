"""objetos al final del pasillo en L de r107: mueble y silla tapados con sábanas y cuadros apoyados en la pared"""
import numpy as np
rng = np.random.default_rng(11)
V = []; T = []; Fs = []
def add(Vp, Tp, Fp, mat):
    b = len(V); V.extend(Vp); T.extend(Tp); Fs.extend([(mat, [b + a for a in f]) for f in Fp])
def tapado(cx, cz, sx, sz, h, giro=0.0, n=14, pliegues=7, amp=0.035):
    """caja tapada con una sábana: lados con pliegues que se abren hacia el bajo, tapa algo hundida"""
    Vp = []; Tp = []; Fp = []
    per = 2 * (sx + sz); c, s = np.cos(giro), np.sin(giro)
    def borde(t):          # t en [0,1) alrededor del rectángulo -> (x, z, normal)
        d = t * per
        for (L, p0, dv, nv) in ((sx, (-sx/2, -sz/2), (1, 0), (0, -1)), (sz, (sx/2, -sz/2), (0, 1), (1, 0)), (sx, (sx/2, sz/2), (-1, 0), (0, 1)), (sz, (-sx/2, sz/2), (0, -1), (-1, 0))):
            if d <= L: return np.array([p0[0] + dv[0] * d, p0[1] + dv[1] * d]), np.array(nv, float)
            d -= L
        return np.array([-sx/2, -sz/2]), np.array([0, -1.0])
    nu = int(per / 0.06); nv = n
    fase = rng.random(pliegues) * 6.28
    for j in range(nv + 1):
        v = j / nv; y = h * (1 - v)          # de arriba (v=0) al suelo (v=1)
        for i in range(nu + 1):
            t = i / nu; p, nn = borde(t % 1.0)
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
            Vp.append([cx + c * x + s * z, h - sag, cz - s * x + c * z]); Tp.append([u * sx / 0.9, v * sz / 0.9])
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
# mueble alto tapado contra la pared del fondo (x = 1.5) y silla tapada al lado
Vp, Tp, Fp = tapado(1.86, -4.05, 0.55, 1.15, 1.72, giro=0.0, amp=0.065); add(Vp, Tp, Fp, 'sabana')
Vp, Tp, Fp = tapado(1.95, -3.05, 0.55, 0.55, 0.98, giro=0.12, pliegues=5, amp=0.07); add(Vp, Tp, Fp, 'sabana2')
# cuadros apilados contra la pared sur (z = -4.78), inclinados hacia la pared
for (x, an, al, inc, lz, dz) in ((2.95, 1.05, 0.80, 0.20, 'cuadro12', 0.0), (2.85, 0.85, 0.66, 0.17, 'cuadro14', 0.07), (3.75, 0.70, 0.56, 0.22, 'cuadro13', 0.0)):
    cuadro(x, -4.76 + 0.03 + dz + al * np.sin(inc), an, al, inc, (0, 1), lz)
# sombreado horneado de las sábanas: 4 tonos según la luz (de arriba y del lado del pasillo)
ld = np.array([0.45, 1.0, 0.35]); ld /= np.linalg.norm(ld)
VV = np.array(V)
for k_, (m, fa) in enumerate(Fs):
    if not m.startswith('sabana'): continue
    p = VV[fa]; n = np.cross(p[1] - p[0], p[2] - p[0]); n /= np.linalg.norm(n) + 1e-12
    c = p.mean(0); cen = np.array([1.86, 0.9, -4.05]) if m == 'sabana' else np.array([1.95, 0.5, -3.05])
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
