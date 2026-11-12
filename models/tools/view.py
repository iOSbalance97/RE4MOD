import sys, numpy as np, struct
sys.path.insert(0, '/tmp/sal'); sys.path.insert(0, '/home/claude/brute')
import re4bin, render
from PIL import Image
def as_part(r):
    v = r['pos'][:, :3].astype(np.float32); T = np.concatenate([t['tris'] for t in r['mats'] if len(t['tris'])])
    f = T[:, :, 0].astype(int); cn = (r['nrm'][T[:, :, 1].astype(int), :3] / 127.0).astype(np.float32)
    return dict(name='m', v=v, f=f[:, ::-1].copy(), cn=cn[:, ::-1].copy(), col=np.full((len(v), 3), 0.45, np.float32), mat=np.zeros(len(v), int)), len(T)
def shot(r, W=380, H=520):
    p, nt = as_part(r); v = p['v']; c = (v.min(0) + v.max(0)) / 2; ext = (v.max(0) - v.min(0)).max()
    ims = [render.render([p], c + np.array([ext * 0.9 * s, ext * 0.25, ext * 2.3 * z]), c, W=W, H=H, ss=1) for s, z in ((1, 1), (-1, -1))]
    return ims, nt
if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read(); offs = [int(x, 16) for x in sys.argv[3:]]; sheet = Image.new('RGB', (760 * min(len(offs), 4), 520 * ((len(offs) + 3) // 4)))
    for i, o in enumerate(offs):
        r = re4bin.parse(d[o:]); (a, b), nt = shot(r)
        print(hex(o), 'bones', len(r['bones']), 'pos', len(r['pos']), 'tris', nt, 'hdr tris', sum(t['ntri'] for t in r['mats']), 'mats', len(r['mats']), 'tex', [t['tex'] for t in r['mats']], 'w/vert', np.bincount(r['wt'][:, 3]).tolist())
        sheet.paste(a, (760 * (i % 4), 520 * (i // 4))); sheet.paste(b, (760 * (i % 4) + 380, 520 * (i // 4)))
    sheet.save(sys.argv[2])
