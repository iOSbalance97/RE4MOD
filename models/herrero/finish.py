import numpy as np, struct, json, sys, math
import model, mesh
from model import SKIN, PANTS, BOOT, LEATHER, IRON, WOOD, CHAIN, SOLE, HOT, PLAGA, EYE
rng = np.random.default_rng(7)
NG = rng.random((32, 32, 32)).astype(np.float32)
def vnoise(p, sc):
    q = p / sc; i = np.floor(q).astype(int); f = q - i; f = f * f * (3 - 2 * f)
    def g(dx, dy, dz): return NG[(i[:, 0] + dx) & 31, (i[:, 1] + dy) & 31, (i[:, 2] + dz) & 31]
    x0 = g(0,0,0)*(1-f[:,0]) + g(1,0,0)*f[:,0]; x1 = g(0,1,0)*(1-f[:,0]) + g(1,1,0)*f[:,0]
    x2 = g(0,0,1)*(1-f[:,0]) + g(1,0,1)*f[:,0]; x3 = g(0,1,1)*(1-f[:,0]) + g(1,1,1)*f[:,0]
    return (x0*(1-f[:,1]) + x1*f[:,1])*(1-f[:,2]) + (x2*(1-f[:,1]) + x3*f[:,1])*f[:,2]
def fbm(p, sc): return (vnoise(p, sc) + 0.5 * vnoise(p + 31.7, sc / 2) + 0.25 * vnoise(p + 77.1, sc / 4)) / 1.75
def allsdf(P):
    d = np.full(len(P), 1e3, np.float32)
    for n2, fn, box, vox, bud in model.PARTS:
        lo, hi = box; ins = np.all((P > lo - 200) & (P < hi + 200), 1)
        if ins.any(): d[ins] = np.minimum(d[ins], mesh.ev(fn, P[ins]))
    return d
def corner_normals(v, f, ang=42.0):
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    fa = np.linalg.norm(fn, axis=1) + 1e-12; fu = fn / fa[:, None]
    vf = [[] for _ in range(len(v))]
    for i, t in enumerate(f):
        for k in t: vf[k].append(i)
    cs = math.cos(math.radians(ang)); out = np.zeros((len(f), 3, 3), np.float32)
    for i, t in enumerate(f):
        for k in range(3):
            nb = vf[t[k]]; w = fu[nb] @ fu[i] > cs
            n = (fn[nb][w]).sum(0); out[i, k] = n / (np.linalg.norm(n) + 1e-12)
    return out
BASE = {SKIN: (0.235, 0.16, 0.11), PANTS: (0.085, 0.078, 0.058), BOOT: (0.05, 0.04, 0.032), SOLE: (0.022, 0.022, 0.022), HOT: (1.0, 0.42, 0.06),
        LEATHER: (0.125, 0.075, 0.042), IRON: (0.10, 0.097, 0.095), CHAIN: (0.07, 0.068, 0.07), WOOD: (0.13, 0.09, 0.055),
        PLAGA: (0.20, 0.045, 0.04), EYE: (1.0, 0.07, 0.02)}
def colour(name, v, mat, n):
    c = np.array([BASE[m] for m in mat], np.float32)
    n1 = fbm(v, 90.0); n2 = fbm(v + 500, 30.0); n3 = fbm(v + 900, 220.0)
    y = v[:, 1]
    sk = mat == SKIN
    c[sk] *= (0.82 + 0.36 * n1[sk])[:, None]
    # soot on the forearms / hands, burn scars, bruised veins
    for j in (model.JR, model.JL):
        dist = np.linalg.norm(v - j['wr'], axis=1); soot = np.clip(1 - dist / 420, 0, 1)[:, None] * sk[:, None]
        c = c * (1 - 0.62 * soot) + np.array([0.05, 0.045, 0.04], np.float32) * 0.62 * soot
    burn = np.clip((n3 - 0.56) * 9, 0, 1)[:, None] * sk[:, None]
    c = c * (1 - 0.4 * burn) + np.array([0.24, 0.10, 0.085], np.float32) * (0.75 + 0.5 * n2[:, None]) * 0.4 * burn
    vein = np.clip(1 - np.abs(fbm(v + 300, 60.0) - 0.5) * 22, 0, 1)[:, None] * sk[:, None] * 0.35
    c = c * (1 - vein) + np.array([0.20, 0.16, 0.24], np.float32) * vein
    le = mat == LEATHER
    c[le] *= (0.62 + 0.75 * n1[le])[:, None]
    wear = np.clip((n2 - 0.58) * 6, 0, 1)[:, None] * le[:, None]
    c = c * (1 - 0.5 * wear) + np.array([0.30, 0.20, 0.12], np.float32) * 0.5 * wear            # scuffed
    if name == 'body':
        ap = le & (v[:, 2] > 150) & (y < 1500)
        bl = np.clip((fbm(v + 40, 150.0) - 0.47) * 7, 0, 1) * np.clip((1350 - y) / 500, 0.15, 1) * ap
        c = c * (1 - 0.8 * bl[:, None]) + np.array([0.13, 0.015, 0.012], np.float32) * 0.8 * bl[:, None]   # old blood
    ir = (mat == IRON) | (mat == CHAIN)
    rust = np.clip((n1 - 0.50) * 5, 0, 1)[:, None] * ir[:, None]
    c = c * (1 - 0.6 * rust) + np.array([0.20, 0.09, 0.04], np.float32) * (0.7 + 0.6 * n2[:, None]) * 0.6 * rust
    c[ir] *= (0.8 + 0.4 * n2[ir])[:, None]
    wd = mat == WOOD
    if wd.any():
        q = (v - model.GRIP) @ model.WB.T
        grain = 0.75 + 0.5 * vnoise(q * np.array([0.08, 1, 1], np.float32), 14.0)
        c[wd] *= grain[wd][:, None]
    pa = (mat == PANTS) | (mat == BOOT)
    c[pa] *= (0.7 + 0.6 * n1[pa])[:, None]
    mud = np.clip((330 - y) / 330, 0, 1)[:, None] * pa[:, None] * (0.4 + 0.6 * n2[:, None])
    c = c * (1 - 0.6 * mud) + np.array([0.20, 0.16, 0.11], np.float32) * 0.6 * mud
    # ambient occlusion from the distance field
    ao = np.zeros(len(v), np.float32)
    for h in (12.0, 35.0, 80.0, 170.0): ao += np.clip(allsdf(v + n * h) / h, 0, 1)
    ao = 0.12 + 0.88 * (ao / 4) ** 1.5
    ao[(mat == HOT) | (mat == EYE)] = 1.0
    # cavities: the visor slit
    return np.clip(c * ao[:, None], 0, 1), ao
def load():
    parts = []
    for name, fn, box, vox, bud in model.PARTS:
        z = np.load('dec_%s.npz' % name); v, f, mat = z['v'], z['f'], z['mat']
        v, f2 = mesh.cull(name, v, f, -10.0 if name == 'acc' else -4.0)
        if len(f2) != len(f):
            _, mat = mesh.ev(fn, v, True); f = f2
        # smooth vertex normal for colouring / AO
        fn_ = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); vn = np.zeros_like(v)
        for k in range(3): np.add.at(vn, f[:, k], fn_)
        vn /= (np.linalg.norm(vn, axis=1)[:, None] + 1e-9)
        _, mat = mesh.ev(fn, v - vn * 0.5, True)
        col, ao = colour(name, v, mat, vn)
        cn = corner_normals(v, f)
        parts.append(dict(name=name, v=v, f=f, mat=mat, col=col, cn=cn))
        print(name, len(v), len(f)); sys.stdout.flush()
    return parts
if __name__ == '__main__':
    parts = load()
    import pickle; pickle.dump(parts, open('parts.pkl', 'wb'))
    print('TOTAL tris', sum(len(p['f']) for p in parts), 'verts', sum(len(p['v']) for p in parts))
    allv = np.concatenate([p['v'] for p in parts]); print('bbox', allv.min(0), allv.max(0))
