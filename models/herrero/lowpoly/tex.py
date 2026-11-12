"""UV atlas (box-projection charts, shelf packed) + baked diffuse texture (procedural detail, AO, soft top light)"""
import numpy as np, pickle, sys, math, cv2
import model, mesh, finish
from model import SKIN, PANTS, BOOT, LEATHER, IRON, WOOD, CHAIN, SOLE, HOT, PLAGA, EYE, CLOTH
FN = {n: fn for n, fn, *_ in model.PARTS}
import model_hi
finish.model = model_hi
def hi_field(P):
    d = np.full(len(P), 1e3, np.float32); m = np.zeros(len(P), np.int32)
    for n2, fn, box, vox, bud in model_hi.PARTS:
        lo, hi = box; ins = np.all((P > lo - 60) & (P < hi + 60), 1)
        if ins.any():
            dd, mm = mesh.ev(fn, P[ins], True); idx = np.nonzero(ins)[0]; b = dd < d[idx]; d[idx[b]] = dd[b]; m[idx[b]] = mm[b]
    return d, m
from finish import vnoise, fbm, allsdf
SZ = 512; PAD = 2
ATLAS = {'body': 0, 'fist': 1, 'claw': 1, 'mask': 1, 'acc': 1, 'weapon': 1, 'legs': 1}
NAT = 2
DENS = {'legs': 1.0, 'body': 1.0, 'fist': 1.1, 'claw': 1.1, 'mask': 1.6, 'acc': 0.9, 'weapon': 0.8}
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
    for at in range(NAT):
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
    cl = (mat == PANTS) | (mat == CLOTH); h[cl] = 0.45 * np.sin(P[cl][:, 1] * 1.6) * np.sin((P[cl][:, 0] + P[cl][:, 2]) * 1.6) + 0.8 * fbm(P[cl], 14.0)
    ir = (mat == IRON) | (mat == CHAIN); h[ir] = 1.4 * vnoise(P[ir], 11.0) + 0.9 * vnoise(P[ir] + 50, 3.5)
    bo = (mat == BOOT) | (mat == SOLE); h[bo] = -1.8 * np.clip(1 - np.abs(fbm(P[bo] + 20, 30.0) - 0.5) * 12, 0, 1) + 0.5 * vnoise(P[bo], 5.0)
    wd = mat == WOOD
    if wd.any():
        q = (P[wd] - model.GRIP) @ model.WB.T
        h[wd] = 1.6 * vnoise(q * np.array([0.05, 1, 1], np.float32), 5.0) - 2.5 * np.clip(1 - np.abs(vnoise(q * np.array([0.03, 1, 1], np.float32) + 9, 22.0) - 0.5) * 30, 0, 1)
    return h
def texcolour(name, fn, P, N):
    dh, _ = hi_field(P); P = P + N * np.clip(1.0 - dh, 0, 45)[:, None]     # out to the detailed surface
    _, mat = hi_field(P - N * 0.8)
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
        c = c * (1 - 0.75 * ln_[:, None]) + np.array([0.33, 0.14, 0.12], np.float32) * 0.75 * ln_[:, None]
    # --- a real person's skin: tanned forearms, flushed joints, body hair, moles, a smith's spark burns
    if sk.any():
        tone = np.ones((len(P), 3), np.float32)
        ax_ = np.abs(P[:, 0])
        tan = np.clip((ax_ - 880) / 250, 0, 1) * 0.22                                    # sun on the forearms / hands
        tone *= (1 - tan)[:, None]
        jr = np.zeros(len(P), np.float32)
        for j_ in (model.JR, model.JL):
            for k_, rr_ in (('el', 130.0), ('wr', 120.0), ('sh', 230.0)):
                jr = np.maximum(jr, np.clip(1 - np.linalg.norm(P - (j_[k_] + (np.array([0, 60, 0], np.float32) if k_ == 'sh' else 0)), axis=1) / rr_, 0, 1))
        tone *= 1 - jr[:, None] * np.array([0.02, 0.20, 0.22], np.float32)                 # redder knuckles / elbows / shoulders
        pale = np.clip((1500 - y) / 300, 0, 1) * (ax_ < 420) * 0.10
        tone += pale[:, None] * np.array([0.9, 1.0, 1.0], np.float32)                      # belly / flanks never see the sun
        hair_zone = np.clip((ax_ - 760) / 120, 0, 1) * np.clip((1290 - ax_) / 60, 0, 1) * (N[:, 1] > -0.2) + 0.7 * ((ax_ < 430) & (P[:, 2] < -150) & (y > 1500)) + 0.6 * ((ax_ < 300) & (P[:, 2] > 200) & (y > 1560))
        hz = np.clip(hair_zone, 0, 1)
        hair = np.clip((vnoise(P * np.array([0.22, 1, 1], np.float32), 2.6) - 0.45) * 3.0, 0, 1) * hz * 0.42
        tone *= (1 - hair)[:, None]
        mole = (vnoise(P + 55, 7.0) > 0.90) & (vnoise(P + 91, 23.0) > 0.55)
        tone[mole] *= np.array([0.45, 0.38, 0.35], np.float32)
        spark = (vnoise(P + 17, 5.0) > 0.86) & (np.linalg.norm(P - model.JR['wr'], axis=1) < 480) | (vnoise(P + 29, 5.0) > 0.88) & (np.linalg.norm(P - model.JL['wr'], axis=1) < 300)
        tone[spark] *= np.array([0.95, 0.42, 0.38], np.float32)
        blot = fbm(P + 700, 28.0)[:, None]                                                 # uneven, blotchy complexion
        tone *= 0.86 + 0.28 * blot * np.array([1.0, 0.8, 0.75], np.float32)
        # an old burn across the right forearm: shiny, pink-white, puckered rim
        bz = np.linalg.norm((P - np.array([-1010, 1700, 110], np.float32)) * np.array([0.55, 1, 1], np.float32), axis=1) / 95 + 0.5 * (fbm(P + 5, 40.0) - 0.5)
        burn2 = np.clip(1.15 - bz, 0, 1); rim2 = np.clip(1 - np.abs(bz - 1.0) * 5, 0, 1)
        tone = tone * (1 - 0.6 * burn2[:, None]) + np.array([1.55, 1.15, 1.10], np.float32) * (0.8 + 0.4 * vnoise(P, 9.0))[:, None] * 0.6 * burn2[:, None]
        tone *= (1 - 0.35 * rim2)[:, None]
        c[sk] *= tone[sk]
    cl_ = mat == CLOTH
    if cl_.any():
        c[cl_] *= (0.7 + 0.5 * vnoise(P[cl_] * np.array([0.3, 1, 1], np.float32), 4.0))[:, None]
        bs = np.clip((fbm(P[cl_] + 64, 55.0) - 0.48) * 6, 0, 1)[:, None]
        c[cl_] = c[cl_] * (1 - 0.8 * bs) + np.array([0.12, 0.02, 0.015], np.float32) * 0.8 * bs
    # --- the infection: spreads from the growths; black veins, grey necrotic skin, an inflamed rim
    G = np.array([c_ for c_, r_ in model.GROWTH], np.float32); GR = np.array([r_ for c_, r_ in model.GROWTH], np.float32)
    dg = np.full(len(P), 1e9, np.float32)
    for c_, r_ in zip(G, GR): dg = np.minimum(dg, np.linalg.norm(P - c_, axis=1) - r_)
    inf = np.clip(1 - dg / 430.0, 0, 1) ** 1.3                                   # 1 on a growth -> 0 at ~45 cm
    inf = np.clip(inf * (0.75 + 0.6 * fbm(P + 222, 120.0)), 0, 1) * sk
    v1 = np.abs(fbm(P + 123, 46.0) - 0.5); v2 = np.abs(fbm(P + 611, 19.0) - 0.5); v3 = np.abs(fbm(P + 37, 95.0) - 0.5)
    wv = 0.012 + 0.05 * inf                                                      # veins thicken towards the source
    veins = np.maximum(np.clip(1 - v1 / wv, 0, 1), np.maximum(0.8 * np.clip(1 - v2 / (wv * 0.7), 0, 1) * (inf > 0.35), np.clip(1 - v3 / (wv * 1.3), 0, 1)))
    veins = veins * np.clip(inf * 2.2, 0, 1)
    nec = np.clip((inf - 0.45) * 2.6, 0, 1) * (0.55 + 0.45 * vnoise(P, 22.0))
    c = c * (1 - nec[:, None]) + np.array([0.075, 0.062, 0.066], np.float32) * (0.7 + 0.6 * vnoise(P + 9, 9.0))[:, None] * nec[:, None]
    rim = np.clip(1 - np.abs(inf - 0.40) * 6, 0, 1)[:, None] * 0.45
    c = c * (1 - rim) + np.array([0.26, 0.085, 0.07], np.float32) * rim
    c = c * (1 - 0.92 * veins[:, None]) + np.array([0.016, 0.006, 0.018], np.float32) * 0.92 * veins[:, None]
    far = np.clip(1 - np.abs(fbm(P + 300, 70.0) - 0.5) * 40, 0, 1)[:, None] * sk[:, None] * 0.30   # faint veins everywhere
    c = c * (1 - far) + np.array([0.06, 0.04, 0.06], np.float32) * far
    pg = mat == PLAGA
    if pg.any():
        ring = 0.55 + 0.45 * np.sin(P[pg][:, 0] * 0.21 + P[pg][:, 1] * 0.17 + P[pg][:, 2] * 0.19)
        c[pg] = np.array([0.17, 0.035, 0.035], np.float32) * (0.45 + 0.75 * ring)[:, None] * (0.8 + 0.4 * vnoise(P[pg], 8.0))[:, None]
    # black ichor run down from the mask's breathing slots onto the bib and the chest
    drip = (np.abs(P[:, 0]) < 125) & (y > 1330) & (y < 1730) & (P[:, 2] > 230) & ((mat == LEATHER) | sk)
    st_ = np.clip((vnoise(P * np.array([1, 0.06, 1], np.float32), 13.0) - 0.42) * 6, 0, 1) * np.clip((y - 1330) / 300, 0, 1) * drip
    c = c * (1 - 0.9 * st_[:, None]) + np.array([0.03, 0.006, 0.008], np.float32) * 0.9 * st_[:, None]
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
    # ---- painted in the game's own way (studied on the disc: em18 / em2b textures): desaturated grey-browns,
    # ---- thin dark crease lines with a light ridge beside them, long painted folds on cloth, dashed stitching
    def aniso(Q, s_fast, s_slow, axis, seed):
        sc = np.full(3, 1.0 / s_slow, np.float32); sc[axis] = 1.0 / s_fast
        W_ = 26.0 * (fbm(Q + seed + 13, 90.0)[:, None] - 0.5)
        return vnoise((Q + W_) * sc * 10.0 + seed, 10.0)
    arm = np.abs(P[:, 0]) > 430
    ax_u = np.where(arm, 0, 1)                                    # creases run round the limbs / across the trunk
    def crease(Q, s_fast, s_slow, seed, wd):
        n0 = np.where(arm, aniso(Q, s_fast, s_slow, 0, seed), aniso(Q, s_fast, s_slow, 1, seed))
        dark = np.clip(1 - np.abs(n0 - 0.50) / wd, 0, 1); lite = np.clip(1 - np.abs(n0 - 0.50 - 2.2 * wd) / wd, 0, 1)
        return dark, lite
    if sk.any():
        d1, l1 = crease(P, 7.0, 75.0, 3.0, 0.035); d2, l2 = crease(P + 40, 3.5, 34.0, 8.0, 0.045)
        jw = np.zeros(len(P), np.float32)                         # deeper wrinkles at the joints and the neck
        for j_ in (model.JR, model.JL):
            for k_ in ('el', 'wr'): jw = np.maximum(jw, np.clip(1 - np.linalg.norm(P - j_[k_], axis=1) / 170.0, 0, 1))
        jw = np.maximum(jw, np.clip(1 - np.linalg.norm(P - np.array([0, 1790, 200], np.float32), axis=1) / 260.0, 0, 1))
        k1 = (0.42 + 0.5 * jw) * d1 + 0.22 * d2
        c[sk] = c[sk] * (1 - np.clip(k1, 0, 0.8)[sk][:, None]) + (0.10 * l1 + 0.05 * l2)[sk][:, None] * np.array([0.9, 0.8, 0.7], np.float32) * 0.25
        hatch = aniso(P + 99, 2.6, 16.0, 2, 5.0)                 # fine cross-grain of the skin
        c[sk] *= (0.88 + 0.24 * hatch[sk])[:, None]
        mott = np.clip((fbm(P + 808, 55.0) - 0.52) * 5, 0, 1)    # dark, dirty patches
        c[sk] *= (1 - 0.38 * mott[sk])[:, None]
        sc_ = np.clip(1 - np.abs(aniso(P + 5, 60.0, 4.0, 1, 21.0) - 0.5) / 0.012, 0, 1) * (vnoise(P + 3, 130.0) > 0.62) * sk   # scars: pink slashes
        c = c * (1 - 0.7 * sc_[:, None]) + np.array([0.30, 0.13, 0.11], np.float32) * 0.7 * sc_[:, None]
    fab = (mat == PANTS) | (mat == CLOTH)
    if fab.any():
        Q = P[fab]
        fold = vnoise((Q + 20.0 * (fbm(Q, 120.0)[:, None] - 0.5)) * np.array([1 / 15.0, 1 / 260.0, 1 / 15.0], np.float32) * 10, 10.0)   # long folds down the leg
        fold2 = vnoise(Q * np.array([1 / 60.0, 1 / 9.0, 1 / 60.0], np.float32) * 10 + 7, 10.0)                                       # bunching across
        bunch = np.clip((Q[:, 1] - 250) / 150, 0, 1) * np.clip((700 - Q[:, 1]) / 250, 0, 1)
        c[fab] *= (0.50 + 0.85 * fold + (0.45 * (fold2 - 0.5)) * bunch)[:, None]
        weave = 0.90 + 0.10 * np.sin(Q[:, 1] * 2.1) * np.sin((Q[:, 0] + Q[:, 2]) * 2.1)
        c[fab] *= weave[:, None]
        # sewn patches with dashed stitching (thigh, shin, seat)
        for (cx, cy, hw, hh, zs) in ((-330, 760, 75, 90, 1), (330, 450, 60, 70, 1), (-150, 900, 85, 70, -1), (270, 880, 70, 80, -1)):
            ins = (np.abs(Q[:, 0] - cx) < hw) & (np.abs(Q[:, 1] - cy) < hh) & (Q[:, 2] * zs > 0)
            edge = np.minimum(hw - np.abs(Q[:, 0] - cx), hh - np.abs(Q[:, 1] - cy))
            st = ins & (np.abs(edge - 9) < 2.6) & (np.sin((Q[:, 0] + Q[:, 1]) * 0.55) > -0.2)
            cc_ = c[fab]; cc_[ins] *= np.array([0.80, 0.78, 0.70], np.float32); cc_[st] = np.array([0.33, 0.30, 0.24], np.float32); c[fab] = cc_
    if le.any():
        Q = P[le]
        crack = np.clip(1 - np.abs(fbm(Q + 70, 26.0) - 0.5) / 0.03, 0, 1) + 0.6 * np.clip(1 - np.abs(fbm(Q + 170, 11.0) - 0.5) / 0.035, 0, 1)
        fold = vnoise(Q * np.array([1 / 22.0, 1 / 300.0, 1 / 22.0], np.float32) * 10 + 3, 10.0)
        hang = np.clip((1250 - Q[:, 1]) / 200, 0, 1)             # the skirt hangs in folds, the bib is stretched
        c[le] *= ((1 - 0.5 * np.clip(crack, 0, 1)) * (1 - hang * 0.45 + hang * 0.8 * fold))[:, None]
        # stitching: bib edges, pocket, hem
        x_ = np.abs(Q[:, 0]); y_ = Q[:, 1]
        wtop = 175 + np.clip((1660 - y_) / 300, 0, 1) * 175
        dash = np.sin((Q[:, 0] + y_) * 0.5) > -0.25
        st = ((np.abs(x_ - (wtop - 16)) < 3) & (y_ > 1270) & (y_ < 1650) & (Q[:, 2] > 150)) | ((np.abs(y_ - 1648) < 3) & (x_ < 160) & (Q[:, 2] > 150))
        st |= ((np.abs(np.maximum(x_ - 150, np.abs(y_ - 880) - 95) + 13) < 3) & (Q[:, 2] > 150))
        st |= (np.abs(y_ - 1128 - 26) < 2.5) | (np.abs(y_ - 1128 + 26) < 2.5)
        cc_ = c[le]; cc_[st & dash] = np.array([0.30, 0.25, 0.17], np.float32); c[le] = cc_
    if ir.any():
        Q = P[ir]
        run = vnoise(Q * np.array([1 / 9.0, 1 / 140.0, 1 / 9.0], np.float32) * 10 + 11, 10.0)                   # rust runs down the plates
        rr = np.clip((run - 0.52) * 4, 0, 1) * np.clip((0.9 - ao[ir]) * 3 + 0.35, 0, 1)
        c[ir] = c[ir] * (1 - 0.75 * rr[:, None]) + np.array([0.16, 0.06, 0.022], np.float32) * 0.75 * rr[:, None]
        scr = np.clip(1 - np.abs(aniso(Q, 45.0, 2.2, 0, 31.0) - 0.5) / 0.012, 0, 1) * (vnoise(Q + 8, 60.0) > 0.55) + np.clip(1 - np.abs(aniso(Q + 9, 50.0, 2.0, 1, 37.0) - 0.5) / 0.010, 0, 1) * (vnoise(Q + 80, 60.0) > 0.6)
        c[ir] += 0.10 * np.clip(scr, 0, 1)[:, None]
        ham = vnoise(Q, 16.0); c[ir] *= (0.72 + 0.5 * ham)[:, None]                                            # hammered, uneven plate
    lum = (c @ np.array([0.30, 0.59, 0.11], np.float32))[:, None]
    keep = ((mat == HOT) | (mat == EYE))[:, None]
    desat = np.where((mat == PLAGA)[:, None], 0.15, 0.38)
    c = np.where(keep, c, c * (1 - desat) + lum * desat * np.array([1.0, 0.96, 0.90], np.float32))
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
    ey = mat == EYE; shade[ey] = 1.6
    shade[pg] *= 1.25
    c[hot] = np.array([0.05, 0.045, 0.04], np.float32)   # B88: no glowing coals on the low-poly (an orange spot on the thigh)
    grime = (0.80 + 0.35 * fbm(P + 400, 45.0))[:, None]
    grime[hot | ey] = 1.0
    return np.clip(c * shade[:, None] * grime * 1.05, 0, 1) ** (1 / 2.2)   # display space
def bake(parts, uvs):
    imgs = [np.zeros((SZ, SZ, 3), np.float32) for _ in range(NAT)]; msk = [np.zeros((SZ, SZ), bool) for _ in range(NAT)]
    for p, uv in zip(parts, uvs):
        name = p['name']; fn = FN[p['fn']]; at = ATLAS[name]; v = p['v']; f = p['f']; cn = p['cn']
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
