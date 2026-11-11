import numpy as np, pickle, sys, cv2
from PIL import Image
import rig, render
parts = pickle.load(open('parts.pkl', 'rb'))
texs = [(cv2.imread('herrero_tex%d.png' % i)[:, :, ::-1].astype(np.float32) / 255) ** 2.2 for i in (0, 1)]
for p in parts: p['J'], p['W'] = rig.weights(p)
pickle.dump(parts, open('parts.pkl', 'wb'))
def posed(rot):
    M = rig.pose_mats(rot); out = []
    for p in parts:
        q = dict(p); q['v'] = rig.skin(p['v'].astype(np.float64), p['J'], p['W'], M).astype(np.float32)
        f = p['f']; cn = np.zeros_like(p['cn'])
        for k in range(3):
            n = rig.skin(p['cn'][:, k].astype(np.float64), p['J'][f[:, k]], p['W'][f[:, k]], M, normals=True)
            cn[:, k] = n / (np.linalg.norm(n, axis=1)[:, None] + 1e-9)
        q['cn'] = cn; out.append(q)
    return out
P1 = posed(rig.POSE)
allv = np.concatenate([p['v'] for p in P1]); print('posed bbox', allv.min(0).round(), allv.max(0).round())
V = {'front': ((1300, 1450, 4100), (-60, 1000, 0)), 'q2': ((3000, 1300, 2900), (-60, 1000, 0)), 'side': ((-4300, 1300, 500), (-60, 1000, -150)),
     'back': ((-1800, 1700, -3900), (-150, 1000, -100)), 'face': ((650, 1750, 1900), (-30, 1580, 250)), 'anvil': ((-2300, 900, -2300), (-650, 380, -560))}
V['bback'] = ((-1800, 1700, -3900), (-150, 1300, -100))
sel = sys.argv[1:] or list(V)
for k in sel:
    render.render(parts if k == 'bback' else P1, *V[k], texs=texs).save('p_%s.png' % k)
if not sys.argv[1:]:
    render.render(parts, (0, 1500, 6200), (0, 1050, -300), W=1350, H=900, texs=texs).save('p_bind.png')
