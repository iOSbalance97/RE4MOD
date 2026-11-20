"""Puertas de las salas UC de la mansión que no están conectadas todavía: centro, normal hacia dentro, ancho, suelo (RE4 mm)."""
import json, re, sys, numpy as np
sys.path.insert(0, '/home/claude/tools'); import objload, re4room
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
from scipy import sparse
from hmap import load, floors, heights
COL = "19.4,0,15.0,-47609,12,7084,-1.253"
conx = json.load(open('/home/claude/uc/re4/conexiones2.json'))
salas = 'r100 r101 r102 r103 r104 r105 r106 r107 r108 r109 r111 r112 r113 r114 r115'.split()
res = {}
for r in salas:
    V, T, F, M, G, mats = objload.load(f'/home/claude/uc/m/{r}/sala.obj')
    P = re4room.place(V, COL, 1000.0) * 1000
    tex = np.array([(mats.get(m) or '') for m in M])
    sel = np.array([bool(re.search('door', t, re.I)) and not re.search('nob|knob|handle|frame|waku|huchi|fuchi|parts', t, re.I) for t in tex])
    idx = np.nonzero(sel)[0]; res[r] = []
    if not len(idx): continue
    C = P[F[idx, :3]].mean(1)
    pairs = cKDTree(C).query_pairs(700, output_type='ndarray')
    g = sparse.coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(len(idx), len(idx)))
    nc, lab = connected_components(g, directed=False)
    Tc = floors(f'/home/claude/uc/re4/{r}/col/colision.obj')
    umb = [np.array(q['umbral']) * 1000 for q in conx if r in (q['a'], q['b'])]
    for k in range(nc):
        pts = P[F[idx[lab == k], :3]].reshape(-1, 3)
        if len(pts) < 12: continue
        lo, hi = pts.min(0), pts.max(0); h = hi[1] - lo[1]
        c = (lo + hi) / 2
        xz = pts[:, [0, 2]] - c[[0, 2]]; w, vec = np.linalg.eigh(xz.T @ xz)
        u = vec[:, 1]; n = vec[:, 0]; ancho = np.ptp(xz @ u); grosor = np.ptp(xz @ n)
        if h < 1700 or h > 4000 or ancho < 600 or ancho > 2600 or grosor > 400: continue
        # ¿hacia qué lado hay suelo pisable a la altura de la puerta?
        lados = []
        for s in (1, -1):
            q = c[[0, 2]] + s * n * 900
            hh = heights(Tc, q[0] / 1000, q[1] / 1000) * 1000
            ok = hh[(hh > lo[1] - 400) & (hh < lo[1] + 400)]
            lados.append(len(ok) > 0)
        if lados[0] == lados[1]: continue       # dentro de la sala por los dos lados (o por ninguno): no es puerta al exterior
        nn = n if lados[0] else -n
        dmin = min([np.linalg.norm(c[[0, 2]] - uu[[0, 2]]) for uu in umb] + [1e9])
        res[r].append(dict(centro=[round(float(c[0])), round(float(lo[1])), round(float(c[2]))], normal=nn.round(3).tolist(), ancho=round(float(ancho)),
                           alto=round(float(h)), conectada=bool(dmin < 1800), tex=sorted(set(tex[idx[lab == k]]))[0]))
    # quitar duplicados (hojas dobles)
    L = []
    for d in res[r]:
        if all(np.linalg.norm(np.subtract(d['centro'], e['centro'])) > 900 for e in L): L.append(d)
    res[r] = L
    print(r, ' '.join(f"{'C' if d['conectada'] else 'LIBRE'}{tuple(d['centro'])}" for d in L))
json.dump(res, open('/home/claude/uc/puertas_libres.json', 'w'), indent=1)
