"""Puntos de luz de cada sala a partir de los objetos colocados de UC (rNNN_obj de bgobj):
- llamas: velas, candelabros (candle*, candlestand*, shokudai*) -> puntas de las velas (máximos locales de altura);
  arañas (chandelier) -> anillo de velas (máximos locales lejos del eje, sin la cadena)
- lámparas (light*, lump*) -> luz cálida sin llama en el centro del objeto
Salida: /home/claude/uc/luces.json {sala: {llamas: [[x,y,z] mm RE4], lamparas: [...]}}"""
import json, re, sys, os
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '/home/claude/tools')
import brres, ucbones, objload, re4room
COL = "19.4,0,15.0,-47609,12,7084,-1.253"
def a_re4(P_uc_units): return re4room.place(np.asarray(P_uc_units) * 0.1, COL, 1000.0) * 1000.0

def puntas(W, anillo=False):
    """máximos locales de altura en una rejilla XZ de 2 cm (unidades UC: 0.2)"""
    c = W[:, [0, 2]].mean(0)
    top = W[:, 1].max(); h = np.ptp(W[:, 1])
    cell = 0.25
    k = np.floor((W[:, [0, 2]] - W[:, [0, 2]].min(0)) / cell).astype(int)
    best = {}
    for (i, j), p in zip(map(tuple, k), W):
        if (i, j) not in best or p[1] > best[(i, j)][1]: best[(i, j)] = p
    pts = []
    for (i, j), p in best.items():
        vec = [best.get((i + di, j + dj)) for di in (-2, -1, 0, 1, 2) for dj in (-2, -1, 0, 1, 2) if (di, dj) != (0, 0)]
        if all(v is None or v[1] <= p[1] for v in vec): pts.append(p)
    pts = np.array(pts)
    if anillo:
        r = np.hypot(pts[:, 0] - c[0], pts[:, 2] - c[1])
        pts = pts[(r > 1.5) & (pts[:, 1] < top - 0.15 * h)]
        if not len(pts): return []
        hy = np.median(pts[:, 1]); pts = pts[np.abs(pts[:, 1] - hy) < 0.08 * h + 0.3]
    else:
        pts = pts[pts[:, 1] > top - 0.25 * h - 0.5]
    # juntar puntas a menos de 0.6 u (6 cm)
    out = []
    for p in sorted(pts.tolist(), key=lambda p: -p[1]):
        if all(np.hypot(p[0] - q[0], p[2] - q[2]) > 0.6 for q in out): out.append(p)
    return out

res = {}
for r in sys.argv[1].split(','):
    d = open(f'/home/claude/uc/bgo/{r}/model.brres', 'rb').read(); ms = dict(brres.tree(d)['3DModels(NW4R)'])
    llamas, lamparas = [], []
    if f'{r}_obj' in ms:
        for b in ucbones.bones(d, ms[f'{r}_obj'])[1:]:
            n = b['name']; base = re.sub(r'^r\d+_', '', re.sub(r'_?\d+$', '', n)).lower()
            if not re.match(r'(candle|candlestand|shokudai|chandelier|light|lump)', base): continue
            cand = [n, re.sub(r'_\d+$', '', n), re.sub(r'_?\d+$', '', n), re.sub(r'_?[A-Z]?\d*$', '', n)]
            m = None
            for c in cand:
                p = f'/home/claude/uc/objs/{r}/_m/{c}/{c}.obj'
                if os.path.exists(p): m = p; break
            if not m: continue
            V = objload.load(m)[0]
            if not len(V): continue
            W = V @ b['mtx'][:, :3].T + b['mtx'][:, 3]
            if base.startswith('chandelier'):
                tips = puntas(W, anillo=True)
                if len(tips) > 4: tips = [tips[i] for i in np.linspace(0, len(tips) - 1, 4).astype(int)]
                llamas += [[t[0], t[1] + 0.15, t[2]] for t in tips]
            elif base.startswith(('candle', 'shokudai')):
                tips = puntas(W)[:5]
                llamas += [[t[0], t[1] + 0.15, t[2]] for t in tips]
            else:
                c = W.mean(0); lamparas.append([c[0], c[1], c[2]])
    # agrupar llamas muy juntas (<25 cm) en una: el fuego de RE4 es más grande que una vela
    L = np.array(llamas) if llamas else np.zeros((0, 3))
    agr = []
    for p in L:
        for g in agr:
            if np.linalg.norm(np.mean(g, 0) - p) < 2.5: g.append(p); break
        else: agr.append([p])
    L2 = np.array([np.mean(g, 0) for g in agr]) if agr else np.zeros((0, 3))
    res[r] = dict(llamas=a_re4(L2).tolist() if len(L2) else [], lamparas=a_re4(np.array(lamparas)).tolist() if lamparas else [],
                  velas=len(L))
    print(r, 'velas', len(L), '-> llamas', len(L2), '| lámparas', len(lamparas))
json.dump(res, open('/home/claude/uc/luces.json', 'w'), indent=1)
