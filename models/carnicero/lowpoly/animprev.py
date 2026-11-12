import sys, pickle, numpy as np, cv2
sys.path.insert(0, '/home/claude/carnicero_lp'); sys.path.insert(0, '/home/claude/re4mod/models/carnicero/anim')
import rig, render
which = sys.argv[1]; frames = [int(x) for x in sys.argv[2].split(',')]; eye = tuple(float(x) for x in sys.argv[3].split(',')); outp = sys.argv[4]
sys.argv = [sys.argv[0]]
import mkcarn
from PIL import Image
parts = pickle.load(open('/home/claude/carnicero_lp/parts.pkl', 'rb'))
for p in parts:
    if 'J' not in p: p['J'], p['W'] = rig.weights(p)
texs = [(cv2.resize(cv2.imread('/home/claude/carnicero_lp/carnicero_tex%d.png' % i), (1024, 1024)).astype(np.float32)[:, :, ::-1] / 255) ** 2.2 for i in (0, 1)]
B = mkcarn.mk.B
def posed(pz):
    P = mkcarn.fk(pz); M = {k: (pz.W[k], P[k] - pz.W[k] @ B[k][1]) for k in B}
    out = []
    for p in parts:
        q = dict(p); q['v'] = rig.skin(p['v'].astype(np.float64), p['J'], p['W'], M).astype(np.float32); f = p['f']; cn = np.zeros_like(p['cn'])
        for k in range(3):
            n = rig.skin(p['cn'][:, k].astype(np.float64), p['J'][f[:, k]], p['W'][f[:, k]], M, normals=True); cn[:, k] = n / (np.linalg.norm(n, axis=1)[:, None] + 1e-9)
        q['cn'] = cn; out.append(q)
    return out
W = Image.new('RGB', (450 * len(frames), 600))
fn = getattr(mkcarn, which)
for i, f in enumerate(frames):
    im = render.render(posed(fn(f)), eye, (0, 600, 300), W=450, H=600, ss=1, texs=texs); W.paste(im, (450 * i, 0))
W.save(outp)
