"""Recorrido a pie dentro de cada sala (sobre la colisión): desde cada punto de llegada, ¿se alcanzan todas las puertas
de la sala? Rejilla de 0,25 m con varias alturas por celda; paso entre celdas si el desnivel es < 0,45 m y no hay
pared de colisión entre medias (a la altura de las rodillas/pecho de Leon)."""
import glob, os, struct, sys
from collections import deque
import numpy as np
sys.path.insert(0, '/home/claude/tools'); sys.path.insert(0, '/home/claude/re4src/tools')
import drs, re4inject as RI, mundo
from uc_montar2_mapa import MAPA
from hmap import load
B = sys.argv[1]; C = 0.25
col = {}
for rr, ids in MAPA.items():
    for s in ids: col[(1, s & 0xFF)] = ('obj', f'/home/claude/uc/re4/{rr}/col/colision.obj', rr)
for n, (st, rid) in mundo.HUECO.items():
    col[(st, rid)] = ('obj', f'{mundo.dir_sala(n)}/col/colision.obj', n) if mundo.es_malla(n) else ('npz', f'/home/claude/gen/{n}/col.npz', n)
def tris(k):
    t, p, n = col[k]
    if t == 'obj':
        V, F = load(p); T = V[F]
    else:
        z = np.load(p); T = z['T'] / 1000.0
    nn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12
    return T[nn[:, 1] > 0.5], T[np.abs(nn[:, 1]) < 0.3]
salas = {}
for st in (1, 2):
    for p in sorted(glob.glob(f'{B}/St{st}/r*.das')):
        rid = int(os.path.basename(p)[2:4], 16)
        sig, sr, snd, body, c = RI.read_das(p); e, _ = RI.parse_body(body)
        aev = [d for t, d in e if drs.tag_name(t) == 'AEV']; recs = []
        if aev:
            d = aev[0]
            for k in range(struct.unpack('>H', d[6:8])[0]):
                r = d[0x10 + k * 0x9C:0x10 + (k + 1) * 0x9C]
                pts = np.array([struct.unpack('>2f', r[0x14 + 8 * j:0x1C + 8 * j]) for j in range(4)])
                recs.append(dict(c=pts.mean(0) / 1000, floor=struct.unpack('>f', r[8:12])[0] / 1000 + 0.3, pos=np.array(struct.unpack('>3f', r[0x5C:0x68])) / 1000,
                                 dest=(r[0x6C], r[0x6D]), trg=r[0x38], ext=np.ptp(pts, 0).max()))
        salas[(st, rid)] = recs
if len(sys.argv) > 2 and sys.argv[2] == '--gen':        # solo salas generadas, desde gen/*/meta.json
    import json
    salas = {}; llegadas = {}
    for n, k in mundo.HUECO.items():
        if mundo.es_malla(n): continue
        m = json.load(open(f'/home/claude/gen/{n}/meta.json'))
        for d in m['puertas']:
            c = np.array(d['centro'])[[0, 2]]; nn = np.array(d['normal'])
            salas.setdefault(k, []).append(dict(c=c + nn * 0.575, floor=d['centro'][1], pos=None, dest=(9, len(salas.get(k, []))), trg=8, ext=1.0))
            llegadas.setdefault(k, []).append(np.array([c[0] + nn[0] * 1.5, d['centro'][1], c[1] + nn[1] * 1.5]))
if len(sys.argv) > 2 and sys.argv[2] == '--areas':      # salas UC de fuera, puntos de puerta calculados como en montar3
    src = open('/home/claude/tools/montar3.py').read()
    pre = src[:src.index('# 1) mansión')].replace("OUT = sys.argv[1]", "OUT = '/tmp/x'")
    mid = src[src.index('def hit_xz4'):src.index('libres = json.load')]
    ar = src[src.index('import pisable'):src.index('# 3) registros AEV')]
    g = {}; exec(pre + mid + ar, g); EP = g['EP']
    salas = {}; llegadas = {}
    usados = {x for ab in mundo.ENLACES for x in ab}
    for key, e in EP.items():
        if key not in usados: continue
        k = e['slots'][0]; pts = np.array(e['area']['pts']) / 1000
        salas.setdefault(k, []).append(dict(c=pts.mean(0), floor=e['area']['floor'] / 1000 + 0.3, pos=None, dest=(9, len(salas.get(k, []))), trg=8, ext=1.0, key=key))
        llegadas.setdefault(k, []).append(np.array(e['pos']) / 1000)
llegadas = llegadas if len(sys.argv) > 2 and sys.argv[2] in ('--gen', '--areas') else {}
for k, recs in (salas.items() if not llegadas else []):
    for r in recs:
        if r['trg'] == 8: llegadas.setdefault(r['dest'], []).append(r['pos'])
malas = 0
for k in sorted(salas):
    if k not in col or col[k] is None: continue
    puertas = [r for r in salas[k] if r['trg'] == 8 and r['ext'] < 20000]
    starts = llegadas.get(k, [])
    if not puertas or not starts: continue
    FL, WL = tris(k)
    allp = np.concatenate([FL.reshape(-1, 3)] + [np.array([s for s in starts])])
    lo = np.minimum(allp.min(0), np.array([p['c'][0] for p in puertas] + [allp[:, 0].min()]).min()) if False else allp.min(0) - 2
    hi = allp.max(0) + 2
    # recortar a la zona de interés (alrededor de puertas y llegadas, +40 m)
    pts = np.array([[s[0], s[2]] for s in starts] + [list(p['c']) for p in puertas])
    lo2 = np.maximum(lo[[0, 2]], pts.min(0) - 40); hi2 = np.minimum(hi[[0, 2]], pts.max(0) + 40)
    nx, nz = int((hi2[0] - lo2[0]) / C) + 1, int((hi2[1] - lo2[1]) / C) + 1
    cells = {}
    for t in FL:
        x0, z0 = t[:, [0, 2]].min(0); x1, z1 = t[:, [0, 2]].max(0)
        i0, i1 = max(0, int((x0 - lo2[0]) / C)), min(nx - 1, int((x1 - lo2[0]) / C)); j0, j1 = max(0, int((z0 - lo2[1]) / C)), min(nz - 1, int((z1 - lo2[1]) / C))
        if i0 > i1 or j0 > j1: continue
        X, Z = np.meshgrid(lo2[0] + (np.arange(i0, i1 + 1) + .5) * C, lo2[1] + (np.arange(j0, j1 + 1) + .5) * C, indexing='ij')
        a, b, c = t; d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
        if abs(d) < 1e-12: continue
        w0 = ((b[2] - c[2]) * (X - c[0]) + (c[0] - b[0]) * (Z - c[2])) / d; w1 = ((c[2] - a[2]) * (X - c[0]) + (a[0] - c[0]) * (Z - c[2])) / d
        w2 = 1 - w0 - w1; m = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3); Y = w0 * a[1] + w1 * b[1] + w2 * c[1]
        for ii, jj in zip(*np.nonzero(m)): cells.setdefault((ii + i0, jj + j0), []).append(float(Y[ii, jj]))
    nodes = {}
    for key, hs in cells.items():
        hs = sorted(hs); lv = [hs[0]]
        for h in hs[1:]:
            if h - lv[-1] > 0.3: lv.append(h)
            else: lv[-1] = h                      # se pisa la superficie más alta del grupo
        nodes[key] = lv
    # paredes: segmento a ras de suelo de cada triángulo vertical, con su rango de alturas
    bloque = {}
    for t in WL:
        ys = t[:, 1]; ya, yb = ys.min(), ys.max()
        # aristas del triángulo proyectadas
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            L = np.linalg.norm((b - a)[[0, 2]]); n = max(2, int(L / 0.08))
            for s in np.linspace(0, 1, n):
                p = a + (b - a) * s; i, j = int((p[0] - lo2[0]) / C), int((p[2] - lo2[1]) / C)
                if 0 <= i < nx and 0 <= j < nz: bloque.setdefault((i, j), []).append((ya, yb))
    def libre(cell, h):
        for ya, yb in bloque.get(cell, ()):
            if ya < h + 1.2 and yb > h + 0.35: return False
        return True
    def nodo(p, y):
        i, j = int((p[0] - lo2[0]) / C), int((p[1] - lo2[1]) / C); best = None
        for di in range(-2, 3):
            for dj in range(-2, 3):
                for li, h in enumerate(nodes.get((i + di, j + dj), [])):
                    dd = abs(h - y) + 0.2 * (abs(di) + abs(dj))
                    if abs(h - y) < 0.8 and (best is None or dd < best[0]): best = (dd, (i + di, j + dj, li))
        return best[1] if best else None
    def flood(s):
        seen = {s}; q = deque([s])
        while q:
            i, j, l = q.popleft(); h = nodes[(i, j)][l]
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c2 = (i + di, j + dj)
                for l2, h2 in enumerate(nodes.get(c2, [])):
                    if abs(h2 - h) < 0.45 and (c2 + (l2,)) not in seen and libre(c2, h2) and libre((i, j), h):
                        seen.add(c2 + (l2,)); q.append(c2 + (l2,))
        return seen
    res = []; Rs = []
    for si, s in enumerate(starts):
        sn = nodo((s[0], s[2]), s[1])
        if sn is None: res.append(f'llegada ({s[0]:.1f},{s[2]:.1f}) sin suelo'); continue
        Rs.append(flood(sn))
    for p in puertas:
        i0, j0 = int((p['c'][0] - lo2[0]) / C), int((p['c'][1] - lo2[1]) / C)
        def llega(R): return any((i0 + di, j0 + dj, l) in R for di in range(-3, 4) for dj in range(-3, 4)
                                 for l, h in enumerate(nodes.get((i0 + di, j0 + dj), [])) if abs(h - p['floor']) < 0.6)
        estricto = col[k][2] in mundo.HUECO          # salas nuevas y de fuera: todas las puertas conectadas entre sí
        ok = all(llega(R) for R in Rs) if estricto else any(llega(R) for R in Rs)
        if not ok: res.append(f'puerta ->r{p["dest"][0]}{p["dest"][1]:02x} ({p["c"][0]:.1f},{p["c"][1]:.1f}) inalcanzable desde cualquier llegada')
    nm = col[k][2]
    if res: malas += 1; print(f'r{k[0]}{k[1]:02x} ({nm}): ' + ' | '.join(sorted(set(res))[:4]))
    else: print(f'r{k[0]}{k[1]:02x} ({nm}): ok, {len(starts)} llegadas, {len(puertas)} puertas')
print('SALAS CON PROBLEMAS', malas)
