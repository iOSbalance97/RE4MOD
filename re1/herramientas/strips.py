"""Tiras de triángulos para listas de display GX (opcode 0x98).
Convención GX (meshbin.triangles): triángulo i de la tira = (v[i], v[i+1], v[i+2]) si i es par,
(v[i+1], v[i], v[i+2]) si es impar. Se respeta la orientación original de cada triángulo.
"""
from collections import defaultdict


def _same_orient(t, o):
    a, b, c = o
    return t in ((a, b, c), (b, c, a), (c, a, b))


def stripify(tris):
    tris = [tuple(int(v) for v in t) for t in tris]
    n = len(tris)
    edge = defaultdict(list)
    for i, (a, b, c) in enumerate(tris):
        for e in ((a, b), (b, c), (c, a)):
            edge[frozenset(e)].append(i)
    used = [False] * n

    def neigh_free(i):
        a, b, c = tris[i]
        return sum(1 for e in ((a, b), (b, c), (c, a)) for j in edge[frozenset(e)] if j != i and not used[j])

    def grow(start, rot):
        a, b, c = tris[start]
        s = [(a, b, c), (b, c, a), (c, a, b)][rot]
        s = list(s); taken = [start]; mark = {start}
        while True:
            k = len(s)
            x, y = s[-2], s[-1]
            nxt = None
            for j in edge[frozenset((x, y))]:
                if used[j] or j in mark: continue
                t = tris[j]
                cv = [v for v in t if v != x and v != y]
                if len(cv) != 1: continue
                cv = cv[0]
                cand = (s[k - 2], s[k - 1], cv) if (k - 2) % 2 == 0 else (s[k - 1], s[k - 2], cv)
                if _same_orient(cand, t):
                    nxt = (j, cv); break
            if nxt is None: break
            s.append(nxt[1]); taken.append(nxt[0]); mark.add(nxt[0])
        return s, taken

    order = sorted(range(n), key=neigh_free)
    strips = []; singles = []
    for i in order:
        if used[i]: continue
        best = None
        for rot in range(3):
            s, taken = grow(i, rot)
            if best is None or len(taken) > len(best[1]): best = (s, taken)
        s, taken = best
        for j in taken: used[j] = True
        if len(taken) == 1: singles.append(tris[i])
        else: strips.append(s)
    return strips, singles


def strip_tris(s):
    out = []
    for i in range(len(s) - 2):
        out.append((s[i], s[i + 1], s[i + 2]) if i % 2 == 0 else (s[i + 1], s[i], s[i + 2]))
    return out
