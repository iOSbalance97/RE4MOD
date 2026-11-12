import numpy as np, pickle, math, sys
from PIL import Image
from model import IRON, CHAIN, HOT
def look(eye, tgt, up=(0, 1, 0)):
    eye = np.array(eye, float); tgt = np.array(tgt, float)
    f = tgt - eye; f /= np.linalg.norm(f); r = np.cross(f, up); r /= np.linalg.norm(r); u = np.cross(r, f)
    return eye, np.stack([r, u, f])
def render(parts, eye, tgt, fov=32, W=900, H=1200, ss=2, bg=(0.012, 0.012, 0.014), texs=None):
    w, h = W * ss, H * ss
    eye, R = look(eye, tgt); fl = 0.5 * h / math.tan(math.radians(fov) / 2)
    zb = np.full((h, w), 1e9, np.float32); img = np.zeros((h, w, 3), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    g = (yy / h).astype(np.float32)
    img[:] = np.array(bg, np.float32) * (1.35 - 0.7 * g[..., None])
    floor_y = h  # unused
    L1 = np.array([-0.45, 0.75, 0.55]); L1 /= np.linalg.norm(L1)
    L2 = np.array([0.8, 0.2, 0.3]); L2 /= np.linalg.norm(L2)
    L3 = np.array([0.3, 0.5, -0.85]); L3 /= np.linalg.norm(L3)
    for p in parts:
        v = p['v'].astype(float); f = p['f']; cam = (v - eye) @ R.T
        sx = w / 2 + cam[:, 0] * fl / cam[:, 2]; sy = h / 2 - cam[:, 1] * fl / cam[:, 2]
        metal = np.isin(p['mat'], (IRON, CHAIN)).astype(np.float32); hot = (p['mat'] == HOT).astype(np.float32)
        for i, t in enumerate(f):
            z = cam[t, 2]
            if z.min() < 50: continue
            x0, y0 = sx[t], sy[t]
            area = (x0[1] - x0[0]) * (y0[2] - y0[0]) - (x0[2] - x0[0]) * (y0[1] - y0[0])
            gn = np.cross(v[t[1]] - v[t[0]], v[t[2]] - v[t[0]])
            if gn @ (v[t[0]] - eye) >= 0 or area == 0: continue    # back face
            xa, xb = max(int(x0.min()), 0), min(int(x0.max()) + 1, w - 1)
            ya, yb = max(int(y0.min()), 0), min(int(y0.max()) + 1, h - 1)
            if xa > xb or ya > yb: continue
            px = xx[ya:yb + 1, xa:xb + 1] + 0.5; py = yy[ya:yb + 1, xa:xb + 1] + 0.5
            w0 = ((x0[1] - px) * (y0[2] - py) - (x0[2] - px) * (y0[1] - py)) / area
            w1 = ((x0[2] - px) * (y0[0] - py) - (x0[0] - px) * (y0[2] - py)) / area
            w2 = 1 - w0 - w1
            m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not m.any(): continue
            iz = w0 / z[0] + w1 / z[1] + w2 / z[2]; zz = 1 / iz
            sub = zb[ya:yb + 1, xa:xb + 1]; m &= zz < sub
            if not m.any(): continue
            b0 = (w0 / z[0] * zz)[m]; b1 = (w1 / z[1] * zz)[m]; b2 = (w2 / z[2] * zz)[m]
            n = b0[:, None] * p['cn'][i, 0] + b1[:, None] * p['cn'][i, 1] + b2[:, None] * p['cn'][i, 2]
            n /= np.linalg.norm(n, axis=1)[:, None] + 1e-9
            if texs is not None:
                uv = b0[:, None] * p['uv'][i, 0] + b1[:, None] * p['uv'][i, 1] + b2[:, None] * p['uv'][i, 2]
                T = texs[p['atlas']]; ux = np.clip(uv[:, 0] - 0.5, 0, T.shape[1] - 1.001); uy = np.clip(uv[:, 1] - 0.5, 0, T.shape[0] - 1.001)
                xi = ux.astype(int); yi = uy.astype(int); fx = (ux - xi)[:, None]; fy = (uy - yi)[:, None]
                c = (T[yi, xi] * (1 - fx) + T[yi, xi + 1] * fx) * (1 - fy) + (T[yi + 1, xi] * (1 - fx) + T[yi + 1, xi + 1] * fx) * fy
            else:
                c = b0[:, None] * p['col'][t[0]] + b1[:, None] * p['col'][t[1]] + b2[:, None] * p['col'][t[2]]
            me = b0 * metal[t[0]] + b1 * metal[t[1]] + b2 * metal[t[2]]
            pos = b0[:, None] * v[t[0]] + b1[:, None] * v[t[1]] + b2[:, None] * v[t[2]]
            vd = eye - pos; vd /= np.linalg.norm(vd, axis=1)[:, None]
            d1 = np.clip(n @ L1, 0, 1); d2 = np.clip(n @ L2, 0, 1); d3 = np.clip(n @ L3, 0, 1)
            hv = L1 + vd; hv /= np.linalg.norm(hv, axis=1)[:, None]
            sp = np.clip((n * hv).sum(1), 0, 1) ** (18 + 50 * me) * (0.10 + 0.55 * me)
            rim = (1 - np.clip((n * vd).sum(1), 0, 1)) ** 3
            lit = (0.34 if texs is not None else 0.07) + (0.95 if texs is not None else 1.25) * d1[:, None] * np.array([1.0, 0.93, 0.82]) + 0.22 * d2[:, None] * np.array([0.55, 0.65, 0.9]) + 0.75 * d3[:, None] * np.array([0.9, 0.5, 0.3])
            col = c * lit + sp[:, None] * np.array([1.0, 0.95, 0.85]) + (0.22 * rim * (0.3 + d3))[:, None] * np.array([0.9, 0.55, 0.35])
            ho = (b0 * hot[t[0]] + b1 * hot[t[1]] + b2 * hot[t[2]])[:, None]; col = col * (1 - ho) + c * 2.2 * ho
            sub[m] = zz[m]; img[ya:yb + 1, xa:xb + 1][m] = col
    img = np.clip(img, 0, None); img = np.clip(img * 1.9 / (1 + 0.9 * img), 0, 1) ** (1 / 2.2)
    im = Image.fromarray((img * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    return im
if __name__ == '__main__':
    parts = pickle.load(open('parts.pkl', 'rb'))
    views = {'front': ((1500, 1500, 3900), (-80, 1000, 0)), 'side': ((-4200, 1300, 600), (-80, 1000, -100)),
             'back': ((-2200, 1700, -3600), (-150, 1000, -100)), 'q2': ((2900, 1300, 2900), (-80, 1000, 0))}
    views['face'] = ((700, 1750, 1900), (-40, 1560, 250)); views['anvil'] = ((-2300, 900, -2300), (-820, 380, -560))
    sel = sys.argv[1:] or list(views)
    for k in sel:
        e, t = views[k]; render(parts, e, t).save('r_%s.png' % k); print(k)
