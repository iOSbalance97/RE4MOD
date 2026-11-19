import numpy as np
def rays(tri, O, D, tmax):
    """distancia al primer triángulo por rayo (Möller-Trumbore), tmax si no choca"""
    v0, e1, e2 = tri[:, 0], tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
    out = np.full(len(O), tmax)
    for k in range(len(O)):
        p = np.cross(D[k], e2); det = (e1 * p).sum(1)
        ok = np.abs(det) > 1e-9; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        s = O[k] - v0; u = (s * p).sum(1) * inv
        q = np.cross(s, e1); v = (D[k] * q).sum(1) * inv; t = (e2 * q).sum(1) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4) & (t < tmax)
        if hit.any(): out[k] = t[hit].min()
    return out

