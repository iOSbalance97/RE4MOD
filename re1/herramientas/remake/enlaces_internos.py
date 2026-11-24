"""Saltos internos por sala (escaleras de mano, rejas, desniveles que el REmake resuelve con acciones):
si una llegada o una puerta quedan en zonas pisables separadas, se unen con un par de 'puertas' dentro de la
misma sala (pulsar ABRIR en un lado lleva al otro). Incluye los saltos internos de la tabla del REmake.
Salida: json {sala: [[quad(4x2 mm), llegada(x,y,z,ang mm)], ...]}"""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/tools'); import pisable
G = json.load(open('/home/claude/re1gc/work/puertas_remake.json'))
def nodos_en(P, x0, z0, x1, z1, y=None, tol=0.6):
    out = set()
    for x in np.arange(x0, x1 + 1e-6, 0.125):
        for z in np.arange(z0, z1 + 1e-6, 0.125):
            i, j = int((x - P.lo[0]) / 0.25), int((z - P.lo[1]) / 0.25)
            for l, h in enumerate(P.nodes.get((i, j), [])):
                if y is None or abs(h - y) < tol:
                    c = P.comp.get((i, j, l))
                    if c is not None: out.add(c)
    return out
def salas_validas():
    ok = set(G) - {'r303'}
    return ok
VAL = salas_validas()
salida = {}
for r in sorted(VAL):
    P = pisable.Pisable(f'/home/claude/re1gc/re4/re_{r}/col/colision.obj')
    req = []
    for a in G:
        for d in G[a]:
            if d['dst'] == r and a in VAL and a != r and any(e['dst'] == a for e in G[r]):
                x, y, z, _ = d['llegada']; req.append(nodos_en(P, x / 1e3 - .25, z / 1e3 - .25, x / 1e3 + .25, z / 1e3 + .25, y / 1e3))
    for d in G[r]:
        if d['dst'] in VAL and d['dst'] != r and any(e['dst'] == r for e in G[d['dst']]):
            q = np.array(d['quad'], float).reshape(4, 2) / 1e3; lo = q.min(0) - 0.6; hi = q.max(0) + 0.6
            vy = [e['llegada'][1] / 1e3 for e in G[d['dst']] if e['dst'] == r]
            req.append(nodos_en(P, lo[0], lo[1], hi[0], hi[1], vy[0] if vy else None, 1.0))
    padre = {}
    def raiz(c):
        while padre.get(c, c) != c: c = padre[c]
        return c
    saltos = []
    for d in G[r]:
        if d['dst'] == r:
            saltos.append([d['quad'], d['llegada'], None])
            q = np.array(d['quad'], float).reshape(4, 2) / 1e3; lo = q.min(0) - 0.6; hi = q.max(0) + 0.6
            x, y, z, _ = d['llegada']
            A = nodos_en(P, lo[0], lo[1], hi[0], hi[1]); B = nodos_en(P, x / 1e3 - .25, z / 1e3 - .25, x / 1e3 + .25, z / 1e3 + .25, y / 1e3)
            for a in A:
                for b in B: padre[raiz(a)] = raiz(b)
    grupos = [s for s in req if s]
    comps = sorted({raiz(c) for s in grupos for c in s})
    # cada requisito debe tocar el grupo principal; unir por el par de nodos más cercano
    def nodos_de(k):
        return [s for s, c in P.comp.items() if raiz(c) == k]
    def une(k1, k2):
        A = np.array([P.centro(s) for s in nodos_de(k1)]); B = np.array([P.centro(s) for s in nodos_de(k2)])
        if not len(A) or not len(B): return None
        from scipy.spatial import cKDTree
        t = cKDTree(B[:, [0, 2]]); d, ix = t.query(A[:, [0, 2]])
        dd = d + 0.3 * np.abs(A[:, 1] - B[ix, 1]); i = int(np.argmin(dd))
        return A[i], B[ix[i]], float(dd[i])
    hecho = True
    while True:
        conj = [{raiz(c) for c in s} for s in grupos]
        todos = sorted(set().union(*conj)) if conj else []
        # componente "principal": el que toca más requisitos
        if not todos: break
        cuenta = {k: sum(k in s for s in conj) for k in todos}
        prin = max(todos, key=lambda k: (cuenta[k], P.tam[k] if k < len(P.tam) else 0))
        sueltos = [s for s in conj if prin not in s]
        if not sueltos: break
        mejor = None
        for s in sueltos:
            for k in s:
                u = une(k, prin)
                if u and (mejor is None or u[2] < mejor[3]): mejor = (k, u[0], u[1], u[2])
        if mejor is None: break
        k, pa, pb, dist = mejor
        # puntos seguros (lejos de paredes) en cada lado
        try: pa2, _, da = P.ajustar(pa[0], pa[2], comp=k, margen=0.5)
        except Exception: pa2, da = pa, 0
        try: pb2, _, db = P.ajustar(pb[0], pb[2], comp=prin, margen=0.5)
        except Exception: pb2, db = pb, 0
        if da > 2.5: pa2 = pa
        if db > 2.5: pb2 = pb
        for p1, p2 in ((pa2, pb2), (pb2, pa2)):
            v = p2[[0, 2]] - p1[[0, 2]]; ang = float(np.arctan2(v[0], v[1])) if np.linalg.norm(v) > 1e-3 else 0.0
            h = 0.7; c = p1[[0, 2]] * 1000
            quad = [c[0] - h * 1e3, c[1] - h * 1e3, c[0] + h * 1e3, c[1] - h * 1e3, c[0] + h * 1e3, c[1] + h * 1e3, c[0] - h * 1e3, c[1] + h * 1e3]
            saltos.append([quad, [float(p2[0] * 1e3), float(p2[1] * 1e3), float(p2[2] * 1e3), ang], float(p1[1] * 1e3)])
        padre[raiz(k)] = raiz(prin)
        print(f'{r}: unidas zonas {k} y {prin} (distancia {dist:.1f} m, de {np.round(pa2,1)} a {np.round(pb2,1)})', flush=True)
    if saltos: salida[r] = saltos
json.dump(salida, open('/home/claude/re1gc/work/saltos_internos.json', 'w'), indent=0)
print('salas con saltos internos:', len(salida))
