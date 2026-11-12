import numpy as np
f32 = np.float32
def V(*a): return np.array(a, dtype=f32)
def nrm(v): v = np.asarray(v, dtype=f32); return v / np.linalg.norm(v)
def ln(p): return np.sqrt((p * p).sum(-1))
def sph(p, c, r): return ln(p - c) - r
def ell(p, c, r):
    q = (p - c) / r; k0 = ln(q); k1 = ln(q / r) + 1e-9
    return k0 * (k0 - 1.0) / k1
def rcone(p, a, b, ra, rb):
    ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return ln(p - a - t[:, None] * ab) - (ra + (rb - ra) * t)
def ccyl(p, a, b, r, rd=0.0):
    ab = b - a; L = np.linalg.norm(ab); u = ab / L
    q = p - a; h = q @ u; rad = ln(q - h[:, None] * u)
    dx = rad - (r - rd); dy = np.abs(h - L / 2) - (L / 2 - rd)
    return np.minimum(np.maximum(dx, dy), 0) + np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2) - rd
def frame(x, yhint):
    x = nrm(x); y = np.asarray(yhint, dtype=f32); y = nrm(y - x * (y @ x)); z = np.cross(x, y)
    return np.stack([x, y, z]).astype(f32)          # rows: local axes
def rbox(p, c, half, r=0.0, R=None):
    q = p - c
    if R is not None: q = q @ R.T
    q = np.abs(q) - (np.asarray(half, dtype=f32) - r)
    return ln(np.maximum(q, 0)) + np.minimum(q.max(-1), 0) - r
def torus(p, c, n, R, r):
    q = p - c; h = q @ n; rad = ln(q - h[:, None] * n)
    return np.sqrt((rad - R) ** 2 + h * h) - r
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b + (a - b) * h - k * h * (1 - h)
def smax(a, b, k): return -smin(-a, -b, k)
def su(k, *ds):
    d = ds[0]
    for e in ds[1:]: d = smin(d, e, k)
    return d
def mn(*ds):
    d = ds[0]
    for e in ds[1:]: d = np.minimum(d, e)
    return d
def shell(d, off, th): return np.abs(d - off) - th
