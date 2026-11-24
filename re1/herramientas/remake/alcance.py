"""Dentro de cada sala: desde cada llegada, qué puertas se alcanzan andando sobre la colisión (más los saltos
internos de la propia sala). Lista las puertas inalcanzables, que son los atascos."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/tools'); import pisable
G = json.load(open('/home/claude/re1gc/work/puertas_remake.json'))
def comps_en(P, x0, z0, x1, z1, y=None, tol=1.5):
    out = set()
    for x in np.arange(x0, x1 + 1e-6, 0.125):
        for z in np.arange(z0, z1 + 1e-6, 0.125):
            i, j = int((x - P.lo[0]) / 0.25), int((z - P.lo[1]) / 0.25)
            for l, h in enumerate(P.nodes.get((i, j), [])):
                if y is None or abs(h - y) < tol:
                    c = P.comp.get((i, j, l))
                    if c is not None: out.add(c)
    return out
res = {}
salas = sys.argv[1:] or sorted(G)
for r in salas:
    if r == 'r303': continue
    P = pisable.Pisable(f'/home/claude/re1gc/re4/re_{r}/col/colision.obj')
    llegadas = [(a, d['llegada']) for a in G for d in G[a] if d['dst'] == r]
    puertas = []
    for d in G[r]:
        q = np.array(d['quad'], float).reshape(4, 2) / 1000; lo = q.min(0) - 0.5; hi = q.max(0) + 0.5
        vuelta = [e['llegada'][1] / 1000 for e in G.get(d['dst'], []) if e['dst'] == r]
        y = min(vuelta, key=lambda v: 0) if vuelta else None
        puertas.append((d, comps_en(P, lo[0], lo[1], hi[0], hi[1])))
    # grafo de componentes: saltos internos unen componentes
    union = {}
    def raiz(c):
        while union.get(c, c) != c: c = union[c]
        return c
    for d, cs in puertas:
        if d['dst'] == r:
            x, y, z, _ = d['llegada']; dst = comps_en(P, x / 1000 - .2, z / 1000 - .2, x / 1000 + .2, z / 1000 + .2, y / 1000, 0.5)
            for a in cs:
                for b in dst: union[raiz(a)] = raiz(b)
    lleg = []
    for a, (x, y, z, _) in llegadas:
        cs = comps_en(P, x / 1000 - .2, z / 1000 - .2, x / 1000 + .2, z / 1000 + .2, y / 1000, 0.5)
        lleg.append((a, {raiz(c) for c in cs}))
    problemas = []
    for a, cs in lleg:
        if not cs: problemas.append(f'llegada desde {a} sin suelo'); continue
        for d, pc in puertas:
            if d['dst'] in (r,): continue
            if not ({raiz(c) for c in pc} & cs): problemas.append(f'desde {a} no se llega a la puerta hacia {d["dst"]}')
    if problemas: print(r, '|', '; '.join(sorted(set(problemas))))
