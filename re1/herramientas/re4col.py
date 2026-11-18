"""Colisión de RE4 GameCube (SAT = escenario por el que se anda, EAT = lo que golpean balas y cámara)
generada a partir del modelo visual de una sala.

Método: rejilla XZ (por defecto 10 cm). En cada celda se buscan las superficies pisables (caras que
miran hacia arriba) y se descartan las que tienen algo encima a la altura del cuerpo. Con eso sale
el suelo (varios niveles: planta baja, balcón, escaleras como rampa) y las paredes se levantan en
el borde de la zona pisable, mirando hacia dentro. Formato según el decomp: include/atari.h,
include/at_sub.h, game/atari.cpp (createSat / createBoxSat como referencia de tablas).

uso: re4col.py sala.obj salida_dir [--celda 0.1] [--escala 1000]
"""
import argparse
import os
import struct
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import objload    # noqa: E402
import decimate   # noqa: E402

STEP = 0.45        # diferencia de altura entre celdas vecinas que se puede subir (los peldaños de UC miden ~30 cm)
BODY_LO = 0.50     # por debajo de esto no estorba (alfombras, zócalos, peldaños)
BODY_HI = 1.70     # altura del cuerpo
WALL_H = 2.5       # altura de las paredes invisibles del SAT
EAT_H = 4.0


def rasterize(V, F, cell, lo, shape):
    """Para cada triángulo: celdas cubiertas y altura del triángulo en el centro de la celda.
    Devuelve listas por celda: superficies (h, ny) y ocupación (hmin, hmax)."""
    nx, nz = shape
    surf = defaultdict(list)
    occ = defaultdict(list)
    P = V[F[:, :3]]
    n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-12
    for t in np.nonzero(ok)[0]:
        a, b, c = P[t]
        ny = n[t, 1] / ln[t]
        xs = np.array([a[0], b[0], c[0]]); zs = np.array([a[2], b[2], c[2]])
        i0 = max(0, int(np.floor((xs.min() - lo[0]) / cell))); i1 = min(nx - 1, int(np.floor((xs.max() - lo[0]) / cell)))
        j0 = max(0, int(np.floor((zs.min() - lo[1]) / cell))); j1 = min(nz - 1, int(np.floor((zs.max() - lo[1]) / cell)))
        if i1 < i0 or j1 < j0:
            continue
        ii, jj = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1), indexing='ij')
        cx = lo[0] + (ii + 0.5) * cell; cz = lo[1] + (jj + 0.5) * cell
        # baricéntricas en XZ
        d = (zs[1] - zs[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (zs[0] - zs[2])
        if abs(d) < 1e-12:
            # cara vertical: ocupa las celdas que toca su segmento en planta
            hmin, hmax = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
            seg = _segment_cells(xs, zs, cell, lo, shape)
            for key in seg:
                occ[key].append((hmin, hmax))
            continue
        w0 = ((zs[1] - zs[2]) * (cx - xs[2]) + (xs[2] - xs[1]) * (cz - zs[2])) / d
        w1 = ((zs[2] - zs[0]) * (cx - xs[2]) + (xs[0] - xs[2]) * (cz - zs[2])) / d
        w2 = 1 - w0 - w1
        e = -0.02 if abs(ny) < 0.5 else 0.0      # paredes inclinadas: margen para no dejar huecos
        inside = (w0 >= e) & (w1 >= e) & (w2 >= e)
        if abs(ny) < 0.5:
            hmin, hmax = min(a[1], b[1], c[1]), max(a[1], b[1], c[1])
            for i, j in zip(ii[inside], jj[inside]):
                occ[(i, j)].append((hmin, hmax))
            for key in _segment_cells(xs, zs, cell, lo, shape):
                occ[key].append((hmin, hmax))
            continue
        h = w0 * a[1] + w1 * b[1] + w2 * c[1]
        for i, j, hh in zip(ii[inside], jj[inside], h[inside]):
            if ny > 0.6:
                surf[(i, j)].append(hh)
            occ[(i, j)].append((hh, hh))
    return surf, occ


def _segment_cells(xs, zs, cell, lo, shape):
    out = set()
    for k in range(3):
        x0, z0, x1, z1 = xs[k], zs[k], xs[(k + 1) % 3], zs[(k + 1) % 3]
        L = max(abs(x1 - x0), abs(z1 - z0)) / cell
        for s in np.linspace(0, 1, int(L * 2) + 2):
            i = int(np.floor((x0 + (x1 - x0) * s - lo[0]) / cell)); j = int(np.floor((z0 + (z1 - z0) * s - lo[1]) / cell))
            if 0 <= i < shape[0] and 0 <= j < shape[1]:
                out.add((i, j))
    return out


def walkable_samples(surf, occ):
    """(i, j, h) de cada superficie libre a la altura del cuerpo."""
    out = []
    for key, hs in surf.items():
        hs = sorted(set(round(h, 3) for h in hs))
        merged = []
        for h in hs:                      # superficies casi a la misma altura (alfombra sobre suelo): la de arriba
            if merged and h - merged[-1] <= STEP: merged[-1] = h
            else: merged.append(h)
        oc = occ.get(key, [])
        for h in merged:
            blocked = any(lo2 < h + BODY_HI and hi2 > h + BODY_LO for lo2, hi2 in oc)
            if not blocked:
                out.append((key[0], key[1], h))
    return out


def build_levels(samples):
    """Une muestras vecinas (diferencia <= STEP) en componentes; descarta islas pequeñas."""
    by_cell = defaultdict(list)
    for k, (i, j, h) in enumerate(samples):
        by_cell[(i, j)].append(k)
    parent = list(range(len(samples)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for k, (i, j, h) in enumerate(samples):
        for di, dj in ((1, 0), (0, 1)):
            for m in by_cell.get((i + di, j + dj), []):
                if abs(samples[m][2] - h) <= STEP:
                    a, b = find(k), find(m)
                    if a != b: parent[a] = b
    comp = defaultdict(list)
    for k in range(len(samples)):
        comp[find(k)].append(k)
    return [v for v in comp.values() if len(v) >= 400], by_cell   # >= 4 m² con celdas de 10 cm


def smooth_heights(samples, comp, by_cell, iters=6):
    """Suaviza alturas dentro de la componente (las escaleras se vuelven rampa; lo plano no cambia)."""
    H = {k: samples[k][2] for k in comp}
    cs = set(comp)
    nb = {}
    for k in comp:
        i, j, h = samples[k]
        nb[k] = [m for di in (-1, 0, 1) for dj in (-1, 0, 1) for m in by_cell.get((i + di, j + dj), [])
                 if m in cs and abs(samples[m][2] - h) <= STEP]
    for _ in range(iters):
        H = {k: (sum(H[m] for m in nb[k]) / len(nb[k])) for k in comp}
    return H


def floor_mesh(samples, comp, by_cell, H, cell, lo):
    """Malla de suelo sobre la rejilla (un vértice por muestra, dos triángulos por cuadrado)."""
    cs = set(comp)
    vid = {}
    P = []
    for k in comp:
        i, j, _ = samples[k]
        vid[k] = len(P); P.append((lo[0] + (i + 0.5) * cell, H[k], lo[1] + (j + 0.5) * cell))
    def get(i, j, h):
        for m in by_cell.get((i, j), []):
            if m in cs and abs(samples[m][2] - h) <= STEP:
                return m
        return None
    T = []
    for k in comp:
        i, j, h = samples[k]
        a = k; b = get(i + 1, j, h); c = get(i + 1, j + 1, h); d = get(i, j + 1, h)
        if b is not None and c is not None and d is not None:
            # CCW visto desde arriba (+Y): (x,z) -> a(0,0) d(0,1) c(1,1) / a c b
            T.append((vid[a], vid[d], vid[c])); T.append((vid[a], vid[c], vid[b]))
    return np.array(P), np.array(T, int)


def boundary_loops(T):
    cnt = defaultdict(int); dirs = {}
    for t in T:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = (min(a, b), max(a, b)); cnt[k] += 1; dirs[k] = (a, b)
    return [dirs[k] for k, c in cnt.items() if c == 1]


def simplify_chain(P, edges, tol):
    """Encadena aristas de borde y simplifica cada cadena (Douglas-Peucker en 3D)."""
    nxt = {}
    for a, b in edges:
        nxt.setdefault(a, []).append(b)
    used = set(); chains = []
    for a, b in edges:
        if (a, b) in used: continue
        chain = [a]; cur = a
        while True:
            cand = [x for x in nxt.get(cur, []) if (cur, x) not in used]
            if not cand: break
            x = cand[0]; used.add((cur, x)); chain.append(x); cur = x
            if cur == a: break
        chains.append(chain)
    out = []
    for ch in chains:
        pts = P[ch]
        keep = _dp(pts, tol)
        out.append([ch[k] for k in keep])
    return out


def _dp(pts, tol):
    n = len(pts)
    if n <= 2: return list(range(n))
    keep = [0, n - 1]; stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1: continue
        a, b = pts[i], pts[j]; ab = b - a; L = np.linalg.norm(ab)
        seg = pts[i + 1:j] - a
        if L < 1e-9: d = np.linalg.norm(seg, axis=1)
        else: d = np.linalg.norm(np.cross(seg, ab / L), axis=1)
        k = int(np.argmax(d))
        if d[k] > tol:
            m = i + 1 + k; keep.append(m); stack += [(i, m), (m, j)]
    return sorted(set(keep))


def walls_from_chains(P, chains, height):
    """Paredes verticales sobre cada tramo de borde, con la cara hacia dentro de la zona pisable.
    El borde va CCW (visto desde arriba) alrededor del suelo, así que el interior queda a la izquierda."""
    tris = []; verts = []
    for ch in chains:
        for a, b in zip(ch[:-1], ch[1:]):
            pa, pb = P[a], P[b]
            if np.linalg.norm((pb - pa)[[0, 2]]) < 1e-4: continue
            base = len(verts)
            verts += [pa, pb, pb + [0, height, 0], pa + [0, height, 0]]
            # normal = cross(e1, e2) debe apuntar al interior (izquierda del borde)
            t1 = (base, base + 3, base + 1); t2 = (base + 1, base + 3, base + 2)
            tris += [t1, t2]
    return np.array(verts, float).reshape(-1, 3), np.array(tris, int).reshape(-1, 3)


def fix_orientation(V, T, want):
    """Da la vuelta a los triángulos cuya normal no va hacia `want(centro)`."""
    out = []
    for t in T:
        a, b, c = V[t]
        n = np.cross(b - a, c - a)
        if np.dot(n, want(t)) < 0: t = (t[0], t[2], t[1])
        out.append(t)
    return np.array(out, int)


# ---------------------------------------------------------------- escritura SAT

def write_sat(V, T, kinds, attrs, block_size):
    """V en mm, T triángulos, kinds 0 suelo / 1 pendiente / 2 pared. Devuelve bytes cSatFile (big-endian)."""
    order = np.argsort(kinds, kind='stable')
    T = T[order]; kinds = kinds[order]; attrs = attrs[order]
    nF = int((kinds == 0).sum()); nS = int((kinds == 1).sum()); nW = int((kinds == 2).sum())
    n = len(T)
    if n > 0x1FFF:
        raise ValueError(f'{n} polígonos (el juego admite 8191)')
    # normales (se comparten las iguales) y aristas
    nrm = []; nkey = {}; edges = []; polys = []
    for t, at in zip(T, attrs):
        a, b, c = V[t]
        nn = np.cross(b - a, c - a); nn = nn / np.linalg.norm(nn)
        k = tuple(np.round(nn, 4))
        if k not in nkey: nkey[k] = len(nrm); nrm.append(nn)
        e0 = len(edges); edges += [b - a, c - b, a - c]
        polys.append((int(t[0]), int(t[1]), int(t[2]), nkey[k], e0, e0 + 1, e0 + 2, int(at)))
    if len(V) > 0xFFFF or len(edges) > 0xFFFF:
        raise ValueError('demasiados vértices / aristas')
    # bloques: rejilla XZ; cada bloque lista sus polígonos ordenados suelo / pendiente / pared
    mn = V.min(0); mx = V.max(0)
    nx = max(1, int(np.ceil((mx[0] - mn[0]) / block_size))); nz = max(1, int(np.ceil((mx[2] - mn[2]) / block_size)))
    blocks = []
    tb_lo = V[T].min(1); tb_hi = V[T].max(1)
    for bi in range(nx):
        for bj in range(nz):
            x0 = mn[0] + bi * block_size - 10; z0 = mn[2] + bj * block_size - 10
            sx = block_size + 20; sz = block_size + 20
            hit = (tb_hi[:, 0] >= x0) & (tb_lo[:, 0] <= x0 + sx) & (tb_hi[:, 2] >= z0) & (tb_lo[:, 2] <= z0 + sz)
            idx = np.nonzero(hit)[0]
            if len(idx) == 0: continue
            k = kinds[idx]
            blocks.append(((x0, 0.0, z0), (sx, 0.0, sz), int((k == 0).sum()), int((k == 1).sum()), int((k == 2).sum()), idx))
    out = bytearray()
    out += struct.pack('>BBHHHHHHHHH', 0x20, 0, len(V), len(nrm), len(edges), 0, n, nF, nS, nW, len(blocks))
    out += b''.join(struct.pack('>3f', *p) for p in V)
    out += b''.join(struct.pack('>3f', *p) for p in nrm)
    out += b''.join(struct.pack('>3f', *p) for p in edges)
    out += b''.join(struct.pack('>3HH3HHI', p[0], p[1], p[2], p[3], p[4], p[5], p[6], 0, p[7]) for p in polys)
    starts = []
    blob = bytearray()
    for b in blocks:
        starts.append(len(blob))
        blob += struct.pack('>3f3fHHHHI', *b[0], *b[1], b[2], b[3], b[4], 0, 0)
        blob += struct.pack(f'>{len(b[5])}H', *[int(x) for x in b[5]])
        blob += b'\0' * ((-len(blob)) % 4)
    # m_pList = offset relativo al bloque siguiente (0 = último)
    for k in range(len(starts) - 1):
        struct.pack_into('>I', blob, starts[k] + 0x20, starts[k + 1] - starts[k])
    out += blob
    out = bytes(out + b'\0' * ((-len(out)) % 32))
    # contenedor como el de las salas: [0x80][nº][ff 79][offset de cada SAT]
    return b'\x80\x01\xff\x79' + struct.pack('>I', 8) + out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('obj'); ap.add_argument('out')
    ap.add_argument('--celda', type=float, default=0.1)
    ap.add_argument('--escala', type=float, default=1000.0)
    ap.add_argument('--colocar', default='')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    V, T, F, M, G, mats = objload.load(a.obj)
    import re4room
    V = re4room.place(V, a.colocar, a.escala)
    lo = (V[:, 0].min() - a.celda, V[:, 2].min() - a.celda)
    shape = (int((V[:, 0].max() - lo[0]) / a.celda) + 2, int((V[:, 2].max() - lo[1]) / a.celda) + 2)
    print('rejilla', shape)
    surf, occ = rasterize(V, F, a.celda, lo, shape)
    samples = walkable_samples(surf, occ)
    comps, by_cell = build_levels(samples)
    comps = sorted(comps, key=len, reverse=True)[:1]    # solo la zona principal (las islas sueltas son tejados/cornisas de fuera)
    print('muestras pisables', len(samples), 'zonas', [len(c) for c in comps])
    allV = []; allT = []; kinds = []; eV = []; eT = []
    for comp in comps:
        H = smooth_heights(samples, comp, by_cell)
        P, Tf = floor_mesh(samples, comp, by_cell, H, a.celda, lo)
        bnd = boundary_loops(Tf)
        chains = simplify_chain(P, bnd, tol=a.celda * 0.75)
        # suelo simplificado (sin UV: solo forma). Los bordes quedan fijos y coinciden con las paredes.
        P2, _, T2 = decimate.decimate(P, np.zeros((len(P), 2)), Tf, 0.01, max_err=None, boundary=True)
        P2s = P2
        # paredes
        Wv, Wt = walls_from_chains(P, chains, WALL_H)
        Ev, Et = walls_from_chains(P, chains, EAT_H)
        for (vv, tt, kd) in ((P2s, T2, None), (Wv, Wt, 2)):
            base = sum(len(x) for x in allV)
            allV.append(vv); allT.append(tt + base)
            if kd is None:
                n = np.cross(vv[tt[:, 1]] - vv[tt[:, 0]], vv[tt[:, 2]] - vv[tt[:, 0]])
                ny = n[:, 1] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
                keep = ny >= 0.5                      # restos del simplificado demasiado inclinados: fuera
                tt = tt[keep]; ny = ny[keep]; allT[-1] = tt + base
                kinds.append(np.where(ny > 0.97, 0, 1))
            else:
                kinds.append(np.full(len(tt), 2))
        nT2 = np.cross(P2s[T2[:, 1]] - P2s[T2[:, 0]], P2s[T2[:, 2]] - P2s[T2[:, 0]])
        T2e = T2[nT2[:, 1] / np.maximum(np.linalg.norm(nT2, axis=1), 1e-12) >= 0.5]
        for (vv, tt) in ((P2s, T2e), (Ev, Et)):
            base = sum(len(x) for x in eV)
            eV.append(vv); eT.append(tt + base)
    SV = np.concatenate(allV) * a.escala; ST = np.concatenate(allT); SK = np.concatenate(kinds)
    good = np.linalg.norm(np.cross(SV[ST[:, 1]] - SV[ST[:, 0]], SV[ST[:, 2]] - SV[ST[:, 0]]), axis=1) > 1.0
    ST, SK = ST[good], SK[good]
    sat = write_sat(SV, ST, SK, np.zeros(len(ST), int), block_size=2000.0)
    EV = np.concatenate(eV) * a.escala; ET = np.concatenate(eT)
    good = np.linalg.norm(np.cross(EV[ET[:, 1]] - EV[ET[:, 0]], EV[ET[:, 2]] - EV[ET[:, 0]]), axis=1) > 1.0
    ET = ET[good]
    en = np.cross(EV[ET[:, 1]] - EV[ET[:, 0]], EV[ET[:, 2]] - EV[ET[:, 0]]); eny = en[:, 1] / np.linalg.norm(en, axis=1)
    EK = np.where(eny > 0.97, 0, np.where(eny >= 0.5, 1, 2))
    eat = write_sat(EV, ET, EK, np.zeros(len(ET), int), block_size=2000.0)
    open(os.path.join(a.out, 'sala.sat'), 'wb').write(sat)
    open(os.path.join(a.out, 'sala.eat'), 'wb').write(eat)
    # OBJ de control
    with open(os.path.join(a.out, 'colision.obj'), 'w') as f:
        f.writelines(f'v {x / a.escala} {y / a.escala} {z / a.escala}\n' for x, y, z in SV)
        for t, k in zip(ST, SK):
            f.write(f'g {"suelo" if k == 0 else "pendiente" if k == 1 else "pared"}\nf {t[0] + 1} {t[1] + 1} {t[2] + 1}\n')
    print(f'SAT: {len(ST)} polígonos (suelo {(SK == 0).sum()}, pendiente {(SK == 1).sum()}, pared {(SK == 2).sum()}), '
          f'{len(sat) / 1024:.0f} KB; EAT: {len(ET)} polígonos, {len(eat) / 1024:.0f} KB')


if __name__ == '__main__':
    main()
