"""Suelo pisable de una sala (colisión): rejilla de 0,25 m con varias alturas por celda, paso si el desnivel < 0,45 m
y no hay pared a la altura de Leon. Componentes conectadas y ajuste de puntos al componente mayor."""
from collections import deque
import numpy as np
from hmap import load

C = 0.25
class Pisable:
    def __init__(self, obj):
        V, F = load(obj); T = V[F]
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        FL = T[n[:, 1] > 0.5]; WL = T[np.abs(n[:, 1]) < 0.3]
        self.lo = FL.reshape(-1, 3).min(0)[[0, 2]] - 1; hi = FL.reshape(-1, 3).max(0)[[0, 2]] + 1
        lo = self.lo; nx, nz = int((hi[0] - lo[0]) / C) + 1, int((hi[1] - lo[1]) / C) + 1
        cells = {}
        for t in FL:
            x0, z0 = t[:, [0, 2]].min(0); x1, z1 = t[:, [0, 2]].max(0)
            i0, i1 = max(0, int((x0 - lo[0]) / C)), min(nx - 1, int((x1 - lo[0]) / C)); j0, j1 = max(0, int((z0 - lo[1]) / C)), min(nz - 1, int((z1 - lo[1]) / C))
            X, Z = np.meshgrid(lo[0] + (np.arange(i0, i1 + 1) + .5) * C, lo[1] + (np.arange(j0, j1 + 1) + .5) * C, indexing='ij')
            a, b, c = t; d = (b[2] - c[2]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[2] - c[2])
            if abs(d) < 1e-12: continue
            w0 = ((b[2] - c[2]) * (X - c[0]) + (c[0] - b[0]) * (Z - c[2])) / d; w1 = ((c[2] - a[2]) * (X - c[0]) + (a[0] - c[0]) * (Z - c[2])) / d
            w2 = 1 - w0 - w1; m = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3); Y = w0 * a[1] + w1 * b[1] + w2 * c[1]
            for ii, jj in zip(*np.nonzero(m)): cells.setdefault((ii + i0, jj + j0), []).append(float(Y[ii, jj]))
        self.nodes = {}
        for key, hs in cells.items():
            hs = sorted(hs); lv = [hs[0]]
            for h in hs[1:]:
                if h - lv[-1] > 0.3: lv.append(h)
                else: lv[-1] = h
            self.nodes[key] = lv
        self.bloque = {}
        for t in WL:
            ya, yb = t[:, 1].min(), t[:, 1].max()
            for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                L = np.linalg.norm((b - a)[[0, 2]]); n_ = max(2, int(L / 0.08))
                for s in np.linspace(0, 1, n_):
                    p = a + (b - a) * s; i, j = int((p[0] - lo[0]) / C), int((p[2] - lo[1]) / C)
                    self.bloque.setdefault((i, j), []).append((ya, yb))
        # componentes
        self.comp = {}; k = 0; self.tam = []
        for cell, lv in self.nodes.items():
            for l in range(len(lv)):
                s = cell + (l,)
                if s in self.comp or not self.libre(cell, lv[l]): continue
                q = deque([s]); self.comp[s] = k; n_ = 1
                while q:
                    i, j, l_ = q.popleft(); h = self.nodes[(i, j)][l_]
                    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        c2 = (i + di, j + dj)
                        for l2, h2 in enumerate(self.nodes.get(c2, [])):
                            s2 = c2 + (l2,)
                            if s2 not in self.comp and abs(h2 - h) < 0.45 and self.libre(c2, h2):
                                self.comp[s2] = k; q.append(s2); n_ += 1
                self.tam.append(n_); k += 1
    def libre(self, cell, h):
        for ya, yb in self.bloque.get(cell, ()):
            if ya < h + 1.2 and yb > h + 0.35: return False
        return True
    def centro(self, s): i, j, l = s; return np.array([self.lo[0] + (i + .5) * C, self.nodes[(i, j)][l], self.lo[1] + (j + .5) * C])
    def ajustar(self, x, z, comp=None, margen=0.6):
        """nodo más cercano a (x,z) del componente dado (por defecto el mayor), lejos de paredes (margen m)"""
        if comp is None: comp = int(np.argmax(self.tam))
        r = int(margen / C); best = None
        for s, k in self.comp.items():
            if k != comp: continue
            i, j, l = s
            if any(not self.libre((i + di, j + dj), self.nodes[(i, j)][l]) or (i + di, j + dj) not in self.nodes
                   for di in range(-r, r + 1) for dj in range(-r, r + 1) if di * di + dj * dj <= r * r): continue
            p = self.centro(s); d = (p[0] - x) ** 2 + (p[2] - z) ** 2
            if best is None or d < best[0]: best = (d, s)
        s = best[1]; p = self.centro(s)
        # hacia dentro: hacia la media del componente en 4 m
        vec = []
        for (i, j, l), k in self.comp.items():
            if k == comp:
                q = self.centro((i, j, l))
                if (q[0] - p[0]) ** 2 + (q[2] - p[2]) ** 2 < 16: vec.append(q[[0, 2]] - p[[0, 2]])
        v = np.mean(vec, 0) if vec else np.array([0.0, 1.0])
        if np.linalg.norm(v) < 1e-3: v = np.array([0.0, 1.0])
        return p, v / np.linalg.norm(v), np.sqrt(best[0])
