import sys, pickle, numpy as np, cv2
sys.path.insert(0, '/home/claude/re4mod/models/herrero/anim')
import rig, render, mkanim
from PIL import Image
parts = pickle.load(open('parts.pkl', 'rb'))
for p in parts:
    if 'J' not in p: p['J'], p['W'] = rig.weights(p)
texs = [(cv2.resize(cv2.imread('herrero_tex%d.png' % i), (1024, 1024)).astype(np.float32)[:, :, ::-1] / 255) ** 2.2 for i in (0, 1)]
def posed(pz):
    P = mkanim.fk(pz); M = {k: (pz.W[k], P[k] - pz.W[k] @ mkanim.B[k][1]) for k in mkanim.B}
    out = []
    for p in parts:
        q = dict(p); q['v'] = rig.skin(p['v'].astype(np.float64), p['J'], p['W'], M).astype(np.float32); f = p['f']; cn = np.zeros_like(p['cn'])
        for k in range(3):
            n = rig.skin(p['cn'][:, k].astype(np.float64), p['J'][f[:, k]], p['W'][f[:, k]], M, normals=True); cn[:, k] = n / (np.linalg.norm(n, axis=1)[:, None] + 1e-9)
        q['cn'] = cn; out.append(q)
    return out
which = sys.argv[1]; frames = [int(x) for x in sys.argv[2].split(',')]; eye = tuple(float(x) for x in sys.argv[3].split(','))
W = Image.new('RGB', (450 * len(frames), 600))
for i, f in enumerate(frames):
    pz = mkanim.walk(f) if which == 'walk' else mkanim.smash(f)
    im = render.render(posed(pz), eye, (-200, 1050, 500), W=450, H=600, ss=1, texs=texs); W.paste(im, (450 * i, 0))
W.save(sys.argv[4])
