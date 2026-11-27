"""visibles.py sala_sin_respaldos.obj respaldos.obj colision.obj [EXCLUIR/SUELO_YMAX por env]
Comprueba cada respaldo: si desde los puntos pisables se ve una parte grande de él (no solo por una rendija),
está mal puesto (queda como una pared suelta). Saca, por respaldo, el % de muestras visibles."""
import sys, os, subprocess, numpy as np
AQ = os.path.dirname(os.path.abspath(__file__))
def load(f):
    V = []; F = []; M = []; cur = None
    for l in open(f):
        if l.startswith('v '): V.append([float(x) for x in l.split()[1:4]])
        elif l.startswith('usemtl'): cur = l.split()[1]
        elif l.startswith('f '): F.append([int(x.split('/')[0]) - 1 for x in l.split()[1:4]]); M.append(cur)
    return np.array(V)[np.array(F)], M
S, _ = load(sys.argv[1]); R, RM = load(sys.argv[2]); C, _ = load(sys.argv[3])
n = np.cross(C[:, 1] - C[:, 0], C[:, 2] - C[:, 0]); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
ym = float(os.environ.get('SUELO_YMAX', 99))
suelo = C[(n[:, 1] > 0.45) & (C[:, :, 1].mean(1) < ym)]
rng = np.random.default_rng(0); pts = []
for t in suelo:
    a = np.linalg.norm(np.cross(t[1] - t[0], t[2] - t[0])) / 2
    for _ in range(max(1, int(a / 1.0))): pts.append(rng.dirichlet([1, 1, 1]) @ t)
pts = np.array(pts)
O = np.concatenate([pts + [0, 1.6, 0], pts + [0, 2.0, 0]]).astype(np.float32)
# cada respaldo son 4 triángulos (2 caras dobles): agrupar de 4 en 4
res = []
for q in range(0, len(R), 4):
    T = R[q]; Q = R[q:q + 2].reshape(-1, 3)
    w = rng.dirichlet([1, 1, 1], 40); P2 = np.concatenate([w @ R[q], w @ R[q + 1]])
    Oa = np.repeat(O, len(P2), 0); Pa = np.tile(P2, (len(O), 1)); D = Pa - Oa; L = np.linalg.norm(D, axis=1); D /= L[:, None]
    S.astype(np.float32).tofile('/tmp/_v_t.bin'); Oa.astype(np.float32).tofile('/tmp/_v_o.bin'); D.astype(np.float32).tofile('/tmp/_v_d.bin')
    subprocess.run([f'{AQ}/rayos', '/tmp/_v_t.bin', '/tmp/_v_o.bin', '/tmp/_v_d.bin', '/tmp/_v_r.bin', 't'], check=True)
    t = np.fromfile('/tmp/_v_r.bin', np.float32); vis = (t < 0) | (t > L - 0.02)
    vis &= L < 25
    fr = vis.reshape(len(O), len(P2)).mean(1)          # por punto de vista: fracción del respaldo que se ve
    res.append((q // 4, RM[q], float(np.round(fr.max() * 100, 1)), float(np.round((fr > 0.05).mean() * 100, 1)), np.round(Q.mean(0), 2).tolist(), float(np.round(np.linalg.norm(Q.max(0) - Q.min(0)), 2)), np.round(O[fr.argmax()], 2).tolist()))
res.sort(key=lambda r: -r[2])
for r in res: print(f'respaldo {r[0]:3d} {r[1]:22s} máx visto {r[2]:5.1f}%  vistas con >5%: {r[3]:5.1f}%  centro {r[4]}  diag {r[5]}  desde {r[6]}')
