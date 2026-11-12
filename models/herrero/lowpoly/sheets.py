"""B86: which triangles belong to open sheets (apron, pauldron straps...): seen from behind they vanish
(the game culls back faces) and the body shows through -> game.py doubles them, reversed"""
import numpy as np, collections
def open_sheets(v, f):
    key = {}; rep = np.array([key.setdefault(tuple(np.round(p, 2)), i) for i, p in enumerate(v)])
    F = rep[f]; E = collections.defaultdict(list)
    for t, (a, b, c) in enumerate(F):
        for u, w in ((a, b), (b, c), (c, a)): E[(min(u, w), max(u, w))].append(t)
    par = list(range(len(F)))
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for ts in E.values():
        for t in ts[1:]: par[find(t)] = find(ts[0])
    openc = {find(ts[0]) for ts in E.values() if len(ts) == 1}
    return np.array([find(t) in openc for t in range(len(F))])
if __name__ == '__main__':
    import pickle; ps = pickle.load(open('parts.pkl', 'rb'))
    for p in ps:
        o = open_sheets(p['v'], p['f']); print(p['name'], len(p['f']), 'open', o.sum(), np.bincount(p['mat'][p['f'][o,0]], minlength=12))
