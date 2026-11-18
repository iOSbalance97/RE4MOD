"""Simplificación de mallas por colapso de medias aristas con cuádricas (Garland-Heckbert).

La topología se calcula con las posiciones soldadas; las UV van por esquina de triángulo.
Un vértice solo puede desaparecer si no está en un borde abierto ni en una costura de UV,
así las texturas y los contornos no se rompen.

decimate(P, UV, tris, ratio) -> (P2, UV2, tris2)   (tris indexan P/UV juntos, como en OBJ)
"""
import heapq
import numpy as np


def decimate(P, UV, tris, ratio, max_err=None, boundary=False):
    P = np.asarray(P, float); UV = np.asarray(UV, float); tris = np.asarray(tris, int)
    key = np.round(P / 1e-5).astype(np.int64)
    _, first, pid = np.unique(key, axis=0, return_index=True, return_inverse=True)
    pid = pid.ravel()
    X = P[first].copy()
    n = len(X)
    F = [list(pid[t]) for t in tris]
    CUV = [[tuple(UV[v]) for v in t] for t in tris]
    keepf = [len(set(f)) == 3 for f in F]
    F = [f for f, k in zip(F, keepf) if k]; CUV = [c for c, k in zip(CUV, keepf) if k]
    m = len(F); target = int(m * ratio)
    vf = [set() for _ in range(n)]
    for fi, f in enumerate(F):
        for v in f: vf[v].add(fi)
    alive = [True] * m
    ecount = {}
    for f in F:
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            k = (a, b) if a < b else (b, a); ecount[k] = ecount.get(k, 0) + 1
    fixed = np.zeros(n, bool)
    onb = np.zeros(n, bool); bedges = set()
    for (a, b), c in ecount.items():
        if c != 2:
            fixed[a] = fixed[b] = True; onb[a] = onb[b] = True; bedges.add((a, b))
    bcount = np.zeros(n, int)
    for (a, b) in bedges: bcount[a] += 1; bcount[b] += 1
    uvs = [set() for _ in range(n)]
    for f, c in zip(F, CUV):
        for v, u in zip(f, c): uvs[v].add(u)
    T = np.array(F)
    nrm = np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]])
    ln = np.linalg.norm(nrm, axis=1); ok = ln > 1e-14
    nn = np.zeros_like(nrm); nn[ok] = nrm[ok] / ln[ok, None]
    pl = np.c_[nn, -(nn * X[T[:, 0]]).sum(1)]
    Q = np.zeros((n, 4, 4))
    K = pl[:, :, None] * pl[:, None, :] * (ln / 2)[:, None, None]
    for j in range(3): np.add.at(Q, T[:, j], K)
    if boundary:
        # planos perpendiculares en los bordes: conservan el contorno al colapsar por el borde
        fn = {}
        for fi, f in enumerate(F):
            for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
                fn[(min(a, b), max(a, b))] = fi
        for (a, b) in bedges:
            e = X[b] - X[a]; L = np.linalg.norm(e)
            if L < 1e-12: continue
            pn = np.cross(e / L, nn[fn[(a, b)]]); ln2 = np.linalg.norm(pn)
            if ln2 < 1e-12: continue
            pn /= ln2; p = np.r_[pn, -pn @ X[a]]
            Kb = np.outer(p, p) * (L * L * 100.0)
            Q[a] += Kb; Q[b] += Kb
        for v in range(n):
            if onb[v] and bcount[v] == 2 and len(uvs[v]) <= 1: fixed[v] = False
    ver = [0] * n
    heap = []

    def push(drop, keep):
        if fixed[drop]: return
        h = np.r_[X[keep], 1.0]
        c = h @ (Q[drop] + Q[keep]) @ h
        heapq.heappush(heap, (c, drop, keep, ver[drop], ver[keep]))

    for (a, b) in ecount:
        push(a, b); push(b, a)
    nalive = m
    while nalive > target and heap:
        c, drop, keep, vd, vk = heapq.heappop(heap)
        if ver[drop] != vd or ver[keep] != vk or fixed[drop]: continue
        if onb[drop] and (min(drop, keep), max(drop, keep)) not in bedges: continue
        if max_err is not None and c > max_err: break
        shared = vf[drop] & vf[keep]
        if not shared: continue
        nd = {v for fi in vf[drop] for v in F[fi]}; nk = {v for fi in vf[keep] for v in F[fi]}
        if len(nd & nk) - 2 != len(shared): continue
        bad = False
        for fi in vf[drop] - shared:
            f = F[fi]
            pts = [X[keep] if v == drop else X[v] for v in f]
            old = np.cross(X[f[1]] - X[f[0]], X[f[2]] - X[f[0]])
            new = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            if np.dot(old, new) <= 0.2 * np.linalg.norm(old) * np.linalg.norm(new): bad = True; break
        if bad: continue
        # cada clase de UV de 'drop' debe tener una cara compartida que diga qué UV de 'keep' le toca
        uvmap = {}
        for fi in shared:
            uvmap[CUV[fi][F[fi].index(drop)]] = CUV[fi][F[fi].index(keep)]
        if any(CUV[fi][F[fi].index(drop)] not in uvmap for fi in vf[drop]): continue
        for fi in shared:
            alive[fi] = False; nalive -= 1
            for v in F[fi]: vf[v].discard(fi)
        for fi in list(vf[drop]):
            k = F[fi].index(drop); F[fi][k] = keep; CUV[fi][k] = uvmap[CUV[fi][k]]; vf[keep].add(fi)
        vf[drop] = set(); Q[keep] += Q[drop]; ver[drop] += 1; ver[keep] += 1
        if onb[drop]:
            nbe = set()
            for (x, y) in bedges:
                if drop in (x, y):
                    o = y if x == drop else x
                    if o != keep: nbe.add((min(o, keep), max(o, keep)))
                else: nbe.add((x, y))
            bedges = nbe; onb[keep] = True
        for v in {v for fi in vf[keep] for v in F[fi]} - {keep}:
            push(v, keep); push(keep, v)
    outP = []; outUV = []; outT = []; idx = {}
    for fi in range(m):
        if not alive[fi]: continue
        t = []
        for v, u in zip(F[fi], CUV[fi]):
            k = (v, u)
            if k not in idx:
                idx[k] = len(outP); outP.append(X[v]); outUV.append(u)
            t.append(idx[k])
        outT.append(t)
    return np.array(outP), np.array(outUV), np.array(outT, int)
