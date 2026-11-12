import numpy as np, pickle, sys, cv2, math
from PIL import Image
import rig, render, model
from rig import rx, ry, rz
parts = pickle.load(open('parts.pkl', 'rb'))
texs = [(cv2.imread('rastrero_tex%d.png' % i)[:, :, ::-1].astype(np.float32) / 255) ** 2.2 for i in (0, 1, 2)]
for p in parts: p['J'], p['W'] = rig.weights(p)
pickle.dump(parts, open('parts.pkl', 'wb'))
def posed(rot, off=(0, 0, 0)):
    M = rig.pose_mats(rot, off); out = []
    for p in parts:
        q = dict(p); q['v'] = rig.skin(p['v'].astype(np.float64), p['J'], p['W'], M).astype(np.float32)
        f = p['f']; cn = np.zeros_like(p['cn'])
        for k in range(3):
            n = rig.skin(p['cn'][:, k].astype(np.float64), p['J'][f[:, k]], p['W'][f[:, k]], M, normals=True)
            cn[:, k] = n / (np.linalg.norm(n, axis=1)[:, None] + 1e-9)
        q['cn'] = cn; out.append(q)
    lo = min(q['v'][:, 1].min() for q in out)
    for q in out: q['v'][:, 1] -= lo
    return out
d = math.radians
STAND = {7: rz(d(68)) @ ry(d(-6)), 8: ry(d(18)), 13: rz(d(-66)) @ ry(d(-10)), 14: ry(d(-14)),
         1: rx(d(10)), 2: rx(d(10)), 3: rx(d(-8)), 4: rx(d(-6)), 18: ry(d(4)), 22: ry(d(-6))}
CROUCH = {1: rx(d(35)), 2: rx(d(22)), 3: rx(d(-38)), 4: rx(d(-28)),
          18: rx(d(-72)) @ rz(d(-12)), 19: rx(d(98)), 20: rx(d(-22)), 22: rx(d(-35)) @ rz(d(10)), 23: rx(d(80)), 24: rx(d(-40)),
          7: rz(d(25)) @ ry(d(-55)), 8: ry(d(-40)) @ rz(d(-20)), 10: rx(d(-40)),
          13: rz(d(-62)) @ ry(d(-48)), 14: ry(d(-15)), 16: rz(d(-25))}
POSES = {'stand': STAND, 'crouch': CROUCH}
V = {'front': ((900, 1250, 3600), (0, 900, 0)), 'q2': ((2600, 1150, 2500), (0, 900, 0)), 'side': ((-3700, 1100, 300), (0, 900, 0)),
     'back': ((-1300, 1400, -3400), (0, 950, 0)), 'face': ((420, 1650, 1200), (0, 1560, 50)), 'claw': ((2200, 1300, 1500), (700, 1000, 300)),
     'sickle': ((-1500, 1000, 1900), (-560, 650, 250)), 'cq': ((2400, 1100, 2600), (0, 650, 300)), 'cside': ((-3300, 900, 600), (0, 600, 200))}
if __name__ == '__main__':
    for k in sys.argv[1:]:
        pose, view = k.split(':')
        im = render.render(posed(POSES[pose]) if pose != 'bind' else parts, *V[view], texs=texs, W=600, H=800)
        im.save('r_%s_%s.png' % (pose, view))
