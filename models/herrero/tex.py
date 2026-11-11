"""UV atlas (box-projection charts, shelf packed) + baked diffuse texture (procedural detail, AO, soft top light)"""
import numpy as np, pickle, sys, math, cv2
import model, mesh, finish
from model import SKIN, PANTS, BOOT, LEATHER, IRON, WOOD, CHAIN, SOLE, HOT
from finish import vnoise, fbm, allsdf
SZ = 1024; PAD = 3
ATLAS = {'body': 0, 'fist': 0, 'claw': 0, 'mask': 1, 'acc': 1, 'weapon': 1}
DENS = {'body': 1.0, 'fist': 1.25, 'claw': 1.25, 'mask': 1.5, 'acc': 1.0, 'weapon': 0.9}
def adjacency(f):
    e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]); e.sort(1)
    fi = np.tile(np.arange(len(f)), 3); o = np.lexsort((e[:, 1], e[:, 0])); e = e[o]; fi = fi[o]
    same = np.all(e[1:] == e[:-1], 1); return fi[:-1][same], fi[1:][same]
def charts(v, f):
    n = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]); n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    A, B = adjacency(f)
    base = np.concatenate([n, -n], 1); lab = base.argmax(1)   # labels +x +y +z -x -y -z
    for _ in range(3):                                      # neighbour vote, only among labels the face tolerates
        cnt = np.zeros((len(f), 6)); np.add.at(cnt, (A, lab[B]), 1.0); np.add.at(cnt, (B, lab[A]), 1.0)
        lab = np.where(base > 0.55, base + 0.3 * cnt, -1e9).argmax(1)
    par = np.arange(len(f))
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for a, b in zip(A, B):
        if lab[a] == lab[b]:
            ra, rb = find(a), find(b)
            if ra != rb: par[ra] = rb
    root = np.array([find(i) for i in range(len(f))])
    return lab, root
def unwrap(parts):
    ch = []                                                 # (part idx, faces, uv local (nf,3,2), w, h)
    for pi, p in enumerate(parts):
        v, f = p['v'], p['f']; lab, root = charts(v, f)
        for r in np.unique(root):
            fs = np.nonzero(root == r)[0]; l = lab[fs[0]]; ax = l % 3; u_, v_ = [(2, 1), (0, 2), (0, 1)][ax]
            uv = v[f[fs]][:, :, [u_, v_]].astype(np.float64) * DENS[p['name']]
            if (l < 3) != (ax == 1): uv[:, :, 0] *= -1       # keep orientation (no mirrored charts)
            uv -= uv.reshape(-1, 2).min(0); wh = uv.reshape(-1, 2).max(0)
            ch.append([pi, fs, uv, wh[0], wh[1]])
    out = [np.zeros((len(p['f']), 3, 2), np.float32) for p in parts]
    scales = {}
    for at in (0, 1):
        cs = [c for c in ch if ATLAS[parts[c[0]]['name']] == at]; cs.sort(key=lambda c: -c[4])
        cs.sort(key=lambda c: -max(c[3], c[4]))
        def pack(s):
            sky = np.zeros(SZ, np.int32); pos = []
            for c in cs:
                w, h = int(math.ceil(c[3] * s)) + PAD, int(math.ceil(c[4] * s)) + PAD
                if w >= SZ - PAD: return False, pos
                win = np.lib.stride_tricks.sliding_window_view(sky, w).max(1)[PAD:SZ - w]
                x = int(win.argmin()) + PAD; y = int(win[x - PAD])
                if y + h > SZ - 1: return False, pos
                y = max(y, PAD); sky[x:x + w] = y + h; pos.append((x, y))
            return True, pos
        lo, hi = 0.01, 2.0
        for _ in range(30):
            mid = (lo + hi) / 2; ok, _p = pack(mid)
            if ok: lo = mid
            else: hi = mid
        ok, pos = pack(lo); scales[at] = lo
        for c, (x, y) in zip(cs, pos): out[c[0]][c[1]] = (c[2] * lo + (x, y)).astype(np.float32)
        print('atlas', at, 'charts', len(cs), 'texel/mm', round(lo, 3)); sys.stdout.flush()
    return out
def height(P, mat):
    """fine relief used for the baked bump / cavity (mm-ish, arbitrary)"""
    h = np.zeros(len(P), np.float32)
    sk = mat == SKIN; h[sk] = 0.8 * fbm(P[sk], 9.0) + 0.5 * np.abs(fbm(P[sk] + 300, 60.0) - 0.5) * -6
    le = mat == LEATHER; h[le] = -2.2 * np.clip(1 - np.abs(fbm(P[le] + 70, 26.0) - 0.5) * 14, 0, 1) + 0.6 * vnoise(P[le], 4.0)
    cl = (mat == PANTS); h[cl] = 0.45 * np.sin(P[cl][:, 1] * 1.6) * np.sin((P[cl][:, 0] + P[cl][:, 2]) * 1.6) + 0.8 * fbm(P[cl], 14.0)
    ir = (mat == IRON) | (mat == CHAIN); h[ir] = 1.4 * vnoise(P[ir], 11.0) + 0.9 * vnoise(P[ir] + 50, 3.5)
    bo = (mat == BOOT) | (mat == SOLE); h[bo] = -1.8 * np.clip(1 - np.abs(fbm(P[bo] + 20, 30.0) - 0.5) * 12, 0, 1) + 0.5 * vnoise(P[bo], 5.0)
    wd = mat == WOOD
    if wd.any():
        q = (P[wd] - model.GRIP) @ model.WB.T
        h[wd] = 1.6 * vnoise(q * np.array([0.05, 1, 1], np.float32), 5.0) - 2.5 * np.clip(1 - np.abs(vnoise(q * np.array([0.03, 1, 1], np.float32) + 9, 22.0) - 0.5) * 30, 0, 1)
    return h
def texcolour(name, fn, P, N):
    _, mat = mesh.ev(fn, P - N * 0.8, True)
    c, ao = finish.colour(name, P, mat, N)                   # base palette + large-scale variation + AO
    c = c / np.maximum(ao[:, None], 1e-3)
    y = P[:, 1]
    sk = mat == SKIN
    # skin: pores, blotches, whip scars on the back, dark veins round the growths
    c[sk] *= (0.90 + 0.20 * vnoise(P[sk], 5.0))[:, None]
    back = sk & (P[:, 2] < -120) & (y > 1150) & (np.abs(P[:, 0]) < 380)
    for k, (a, off) in enumerate(((0.9, 0.0), (0.75, 2.1), (-0.8, 4.0), (1.05, 5.5))):
        t = (P[:, 0] * a + y + 55 * vnoise(P, 140.0)) * 0.016 + off
        ln_ = np.clip(1 - np.abs(np.mod(t, 6.283) - 3.14) * 9, 0, 1) * back * (vnoise(P + k * 31, 200.0) > 0.42)
        c = c * (1 - 0.75 * ln_[:, None]) + np.array([0.40, 0.17, 0.15], np.float32) * 0.75 * ln_[:, None]
    g = np.zeros(len(P), np.float32)
    for cc, r in model.GROWTH: g = np.maximum(g, np.clip(1.9 - np.linalg.norm(P - np.array(cc, np.float32), axis=1) / r, 0, 1))
    g *= sk
    veins = np.clip(1 - np.abs(fbm(P + 123, 34.0) - 0.5) * 16, 0, 1)
    gg = np.clip(g * 1.2, 0, 1) * (0.45 + 0.55 * veins)
    c = c * (1 - gg[:, None]) + np.array([0.16, 0.07, 0.13], np.float32) * (0.6 + 0.8 * vnoise(P, 12.0))[:, None] * gg[:, None]
    # leather: stitching round the apron's edge is too fine for 4 mm texels -> seams as darker bands
    le = mat == LEATHER
    c[le] *= (0.85 + 0.3 * vnoise(P[le], 6.0))[:, None]
    # cloth weave tint
    pa = mat == PANTS
    c[pa] *= (0.86 + 0.28 * vnoise(P[pa] * np.array([1, 0.25, 1], np.float32), 3.0))[:, None]
    ir = (mat == IRON) | (mat == CHAIN)
    # iron: rust gathers in the occluded places, bright scuffs on exposed ones, soot from the forge
    rustc = np.clip((0.75 - ao) * 2.2, 0, 1) * ir * (0.5 + 0.5 * vnoise(P, 20.0))
    c = c * (1 - 0.7 * rustc[:, None]) + np.array([0.21, 0.085, 0.03], np.float32) * 0.7 * rustc[:, None]
    scuff = np.clip((vnoise(P * np.array([1, 0.2, 1], np.float32), 4.0) - 0.72) * 9, 0, 1) * ir * np.clip((ao - 0.7) * 4, 0, 1)
    c = c + np.array([0.07, 0.07, 0.075], np.float32) * scuff[:, None]
    # baked relief: light from above-front
    L = np.array([0.25, 0.9, 0.35], np.float32); L /= np.linalg.norm(L)
    T = L - N * (N @ L)[:, None]                             # light dir projected on the surface
    T /= np.linalg.norm(T, axis=1)[:, None] + 1e-6
    h0 = height(P, mat); h1 = height(P + T * 1.6, mat)
    bump = np.clip(1 + 0.30 * (h1 - h0), 0.45, 1.6)
    cav = np.clip(1 + 0.10 * (h0 - height(P + N * 0 + 3.0, mat)), 0.8, 1.2)
    shade = (0.62 + 0.38 * np.clip(N @ L, -0.3, 1)) * ao ** 1.15 * bump
    hot = mat == HOT
    shade[hot] = 1.0
    c[hot] = np.array([1.0, 0.36, 0.05], np.float32) * (0.8 + 0.5 * vnoise(P[hot], 15.0))[:, None]
    grime = (0.80 + 0.35 * fbm(P + 400, 45.0))[:, None]
    return np.clip(c * shade[:, None] * grime * 1.0, 0, 1) ** (1 / 2.2)   # display space
def bake(parts, uvs):
    imgs = [np.zeros((SZ, SZ, 3), np.float32) for _ in (0, 1)]; msk = [np.zeros((SZ, SZ), bool) for _ in (0, 1)]
    for p, uv, (name, fn, box, vox, bud) in zip(parts, uvs, model.PARTS):
        at = ATLAS[name]; v = p['v']; f = p['f']; cn = p['cn']
        PX = []; PP = []; NN = []
        for i in range(len(f)):
            t = uv[i].astype(np.float64); x0, y0 = t[:, 0], t[:, 1]
            area = (x0[1] - x0[0]) * (y0[2] - y0[0]) - (x0[2] - x0[0]) * (y0[1] - y0[0])
            if abs(area) < 1e-9: continue
            xa, xb = int(np.floor(x0.min() - 1)), int(np.ceil(x0.max() + 1)); ya, yb = int(np.floor(y0.min() - 1)), int(np.ceil(y0.max() + 1))
            xs, ys = np.meshgrid(np.arange(xa, xb + 1), np.arange(ya, yb + 1)); px = xs + 0.5; py = ys + 0.5
            w0 = ((x0[1] - px) * (y0[2] - py) - (x0[2] - px) * (y0[1] - py)) / area
            w1 = ((x0[2] - px) * (y0[0] - py) - (x0[0] - px) * (y0[2] - py)) / area; w2 = 1 - w0 - w1
            e = -0.6 / max(1.0, math.sqrt(abs(area)))        # conservative: a bit beyond the edges
            m = (w0 >= e) & (w1 >= e) & (w2 >= e)
            if not m.any(): continue
            b = np.clip(np.stack([w0[m], w1[m], w2[m]], 1), 0, 1); b /= b.sum(1, keepdims=True)
            PX.append(np.stack([xs[m], ys[m]], 1)); PP.append(b @ v[f[i]]); NN.append(b @ cn[i])
        PX = np.concatenate(PX); PP = np.concatenate(PP).astype(np.float32); NN = np.concatenate(NN).astype(np.float32)
        NN /= np.linalg.norm(NN, axis=1)[:, None] + 1e-9
        ok = (PX[:, 0] >= 0) & (PX[:, 0] < SZ) & (PX[:, 1] >= 0) & (PX[:, 1] < SZ); PX, PP, NN = PX[ok], PP[ok], NN[ok]
        col = np.concatenate([texcolour(name, fn, PP[i:i + 200000], NN[i:i + 200000]) for i in range(0, len(PP), 200000)])
        imgs[at][PX[:, 1], PX[:, 0]] = col; msk[at][PX[:, 1], PX[:, 0]] = True
        print('baked', name, len(PP)); sys.stdout.flush()
    out = []
    for im, m in zip(imgs, msk):
        im8 = (im * 255).astype(np.uint8); mm = m.astype(np.uint8)
        for _ in range(6):                                   # bleed over the chart borders
            d = cv2.dilate(im8, np.ones((3, 3), np.uint8)); dm = cv2.dilate(mm, np.ones((3, 3), np.uint8))
            im8 = np.where(mm[..., None] > 0, im8, d); mm = dm
        im8[mm == 0] = (40, 30, 24); out.append(im8)
    return out
if __name__ == '__main__':
    parts = pickle.load(open('parts.pkl', 'rb'))
    uvs = unwrap(parts)
    texs = bake(parts, uvs)
    for p, uv in zip(parts, uvs): p['uv'] = uv; p['atlas'] = ATLAS[p['name']]
    pickle.dump(parts, open('parts.pkl', 'wb'))
    for i, t in enumerate(texs): cv2.imwrite('herrero_tex%d.png' % i, t[:, :, ::-1])
