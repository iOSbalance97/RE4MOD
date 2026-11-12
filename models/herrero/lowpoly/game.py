"""El Herrero -> the game's own formats: .BIN on a Ganado body as template + CMPR textures into its TPL,
written in place over the donor (same sizes) in the em1x.drs that carry that body."""
import numpy as np, pickle, struct, sys, glob, os, cv2
sys.path.insert(0, '/home/claude/re4mod/models/tools')
import re4bin, tpl, rig
S = 0.95                                  # 16 units / mm in s16: +-2047 mm; the Herrero is 2.06 m tall
DONOR = ('/home/claude/disc/ext1/files/em/em10.drs', 0x3ab040, 32352)
def weights_table(parts):
    rows = {}; out = []
    for p in parts:
        idx = np.zeros(len(p['v']), int)
        for i, (j, w) in enumerate(zip(p['J'], p['W'])):
            w1 = int(round(float(w[0]) * 5)) * 20
            if w1 >= 100 or w[1] <= 0: key = (int(j[0]), 0, 0, 1, 100, 0, 0, 0)
            elif w1 <= 0: key = (int(j[1]), 0, 0, 1, 100, 0, 0, 0)
            else: key = (int(j[0]), int(j[1]), 0, 2, w1, 100 - w1, 0, 0)
            idx[i] = rows.setdefault(key, len(rows))
        out.append(idx)
    return np.array(list(rows.keys()), np.uint8), out
def stripify(tris):
    """tris: (n,3) corner ids, game winding. greedy strips; returns list of vertex-id lists"""
    edge = {}
    for t, (a, b, c) in enumerate(tris):
        edge[(a, b)] = (t, c); edge[(b, c)] = (t, a); edge[(c, a)] = (t, b)
    used = np.zeros(len(tris), bool); strips = []
    def grow(t0, rot, commit):
        a, b, c = np.roll(tris[t0], -rot); s = [a, b, c]; seen = {t0}
        while True:
            k = len(s) - 2                                   # index of the next triangle in the strip
            key = (s[-1], s[-2]) if k % 2 == 1 else (s[-2], s[-1])
            # next tri (index k) must hold the directed edge: odd -> (v[k+1], v[k]), even -> (v[k], v[k+1])
            key = (s[k + 1], s[k]) if k % 2 == 1 else (s[k], s[k + 1])
            nx = edge.get(key)
            if nx is None or used[nx[0]] or nx[0] in seen: break
            seen.add(nx[0]); s.append(nx[1])
        if commit:
            for t in seen: used[t] = True
        return s
    for t0 in range(len(tris)):
        if used[t0]: continue
        best = max(range(3), key=lambda r: len(grow(t0, r, False)))
        strips.append(grow(t0, best, True))
    return strips
def cmpr(img):
    """img (H,W,3) uint8 -> GX CMPR bytes (no mips)"""
    H, W, _ = img.shape; out = bytearray()
    im = img.astype(np.float32)
    def to565(c): return (int(c[0]) >> 3 << 11) | (int(c[1]) >> 2 << 5) | (int(c[2]) >> 3)
    def from565(v): return np.array([(v >> 11 & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31], np.float32)
    for by in range(0, H, 8):
        for bx in range(0, W, 8):
            for sy in (0, 4):
                for sx in (0, 4):
                    b = im[by + sy:by + sy + 4, bx + sx:bx + sx + 4].reshape(16, 3)
                    m = b.mean(0); d = b - m; cov = d.T @ d; ax = np.array([1.0, 1.0, 1.0])
                    for _ in range(4): ax = cov @ ax; ax /= np.linalg.norm(ax) + 1e-9
                    t = d @ ax; c0 = to565(np.clip(m + ax * t.max(), 0, 255)); c1 = to565(np.clip(m + ax * t.min(), 0, 255))
                    if c0 < c1: c0, c1 = c1, c0
                    if c0 == c1:
                        if c0 < 0xFFFF: c0 += 1
                        else: c1 -= 1
                    e0, e1 = from565(c0), from565(c1); pal = np.stack([e0, e1, (2 * e0 + e1) / 3, (e0 + 2 * e1) / 3])
                    ix = ((b[:, None, :] - pal[None]) ** 2).sum(2).argmin(1); bits = 0
                    for i in range(16): bits |= int(ix[i]) << (30 - 2 * i)
                    out += struct.pack('>HHI', c0, c1, bits)
    return bytes(out)
def build(parts):
    d = open(DONOR[0], 'rb').read(); dm = d[DONOR[1]:DONOR[1] + DONOR[2]]; H = list(struct.unpack('>24I', dm[:0x60]))
    nb = dm[0x19]
    # bones: the donor's table with our joints for parts 0-25 (offsets from the parent)
    bones = bytearray(dm[0x60:0x60 + 16 * nb])
    for i in range(nb):
        no, par = bones[16 * i], bones[16 * i + 1]
        if no in rig.B:
            pp = rig.B[no][1] - (rig.B[par][1] if par != 255 else 0)
            if no in (6, 7, 12, 13): pp = rig.B[no][1] - rig.B[par][1]
            bones[16 * i + 4:16 * i + 16] = struct.pack('>3f', *[float(x) * S for x in pp])
    wt, widx = weights_table(parts); assert len(wt) <= 127, len(wt)
    POS = []; NRM = {}; UV = {}; mats = {0: [], 1: []}; base = 0
    for p, wi in zip(parts, widx):
        POS.append(np.concatenate([np.round(p['v'] * 16 * S).astype(np.int64), wi[:, None]], 1))
        f = p['f']
        for t in range(len(f)):
            cor = []
            for k in (2, 1, 0):                              # the game's winding is the other way round
                vi = int(f[t, k]); n = np.clip(np.round(p['cn'][t, k] * 21) * 6, -127, 127).astype(int)
                ni = NRM.setdefault((int(n[0]), int(n[1]), int(n[2]), int(wi[vi])), len(NRM))
                u = np.clip(np.round(p['uv'][t, k] / 2) * 2, 0, 255).astype(int); ui = UV.setdefault((int(u[0]), int(u[1])), len(UV))
                cor.append((base + vi, ni, 0, ui))
            mats[p['atlas']].append(cor)
        base += len(p['v'])
    POS = np.concatenate(POS); assert np.abs(POS[:, :3]).max() < 32767
    blob = bytearray(0x60) + bones
    def pad(n=32):
        while len(blob) % n: blob.append(0)
    pad(); o_pos = len(blob); blob += POS.astype('>i2').tobytes()
    pad(); o_nrm = len(blob); blob += np.array(list(NRM.keys()), np.int8).tobytes()
    pad(); o_col = len(blob); blob += b'\xff' * 16
    pad(); o_uv = len(blob); blob += np.array(list(UV.keys()), '>i2').tobytes()
    pad(); o_wt = len(blob); blob += wt.tobytes()
    pad(); o_mat = len(blob); mh = dm[H[7]:H[7] + 0x20]; ntot = 0; nmat = 0
    for at in (0, 1):
        tr = mats[at]
        if not tr: continue
        ids = {}; T = np.array([[ids.setdefault(c, len(ids)) for c in t] for t in tr]); inv = list(ids.keys())
        dl = bytearray()
        for s in stripify(T):
            dl += bytes([0x98]) + struct.pack('>H', len(s))
            for c in s: dl += struct.pack('>4H', *inv[c])
        while len(dl) % 32: dl.append(0)
        h = bytearray(mh); h[0x0C] = at + 1; h[0x18:0x20] = struct.pack('>II', len(dl), len(tr)); blob += h + dl; ntot += len(tr); nmat += 1
    o_t40 = len(blob); blob += dm[H[16]:H[17]]; o_t44 = len(blob); blob += dm[H[17]:H[17] + 4 + 2 * nb + 64][: (DONOR[2] - H[17])]
    H[3], H[4], H[5], H[7], H[12], H[13], H[16], H[17] = o_col, o_uv, o_wt, o_mat, o_pos, o_nrm, o_t40, o_t44
    blob[:0x60] = struct.pack('>24I', *H)
    blob[0x18] = len(wt); blob[0x19] = nb; blob[0x1a:0x1c] = struct.pack('>H', nmat); blob[0x38:0x3c] = struct.pack('>HH', len(POS), len(NRM))
    print('BIN', len(blob), 'of', DONOR[2], '| pos', len(POS), 'nrm', len(NRM), 'uv', len(UV), 'weights', len(wt), 'tris', ntot)
    return bytes(blob), dm
if __name__ == '__main__':
    parts = pickle.load(open('parts.pkl', 'rb'))
    blob, dm = build(parts)
    # read it back with the same reader used on the game's own models
    r = re4bin.parse(blob); print('read back: tris', sum(len(t['tris']) for t in r['mats']), 'hdr', sum(t['ntri'] for t in r['mats']), 'tex', [t['tex'] for t in r['mats']])
    assert len(blob) <= DONOR[2], 'too big for the donor slot'
    open('herrero.bin', 'wb').write(blob)
    texs = [cmpr(cv2.imread('herrero_tex%d.png' % i)[:, :, ::-1]) for i in (0, 1)]
    for i, t in enumerate(texs): open('herrero_tex%d.cmpr' % i, 'wb').write(t)
    print('textures', [len(t) for t in texs])
